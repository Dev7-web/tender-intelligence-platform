"""
Authentication service for email/password and JWT handling.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PASSWORD_REQUIRES_LETTER = re.compile(r"[A-Za-z]")
PASSWORD_REQUIRES_DIGIT = re.compile(r"[0-9]")
PASSWORD_MIN_LENGTH = 8
PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 390000


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def validate_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def validate_password(password: str) -> None:
    value = password or ""
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError("Password must be at least 8 characters")
    if not PASSWORD_REQUIRES_LETTER.search(value):
        raise ValueError("Password must include at least one letter")
    if not PASSWORD_REQUIRES_DIGIT.search(value):
        raise ValueError("Password must include at least one number")


def hash_password(password: str) -> str:
    validate_password(password)
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return (
        f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}${base64.b64encode(derived).decode('ascii')}"
    )


def verify_password_hash(password: str, password_hash: str) -> bool:
    try:
        algorithm, iteration_str, salt_b64, derived_b64 = (password_hash or "").split("$", 3)
        if algorithm != PBKDF2_ALGORITHM:
            return False
        iterations = int(iteration_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(derived_b64.encode("ascii"))
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


def create_access_token(user_id: str) -> str:
    jwt_secret = settings.require_jwt_secret()
    expires_at = now_utc() + timedelta(minutes=settings.JWT_EXPIRES_MIN)
    payload = {
        "sub": user_id,
        "exp": expires_at,
        "iat": now_utc(),
        "type": "access",
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.require_jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.users = db.get_collection("users")
        self.otps = db.get_collection("auth_otps")

    async def signup_with_password(self, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        normalized = (email or "").strip().lower()
        if not validate_email(normalized):
            raise ValueError("Invalid email address")

        password_hash = hash_password(password)
        display_name = (name or "").strip() or normalized.split("@")[0]
        existing = await self.users.find_one({"email": normalized})
        now = now_utc()

        if existing:
            provider = str(existing.get("auth_provider") or "").lower()
            if provider == "google" or existing.get("provider_user_id"):
                raise ValueError("This email is linked to Google sign-in. Continue with Google.")
            if existing.get("password_hash"):
                raise ValueError("Email already registered. Please sign in.")

            await self.users.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "name": display_name,
                        "password_hash": password_hash,
                        "auth_provider": "email_password",
                        "provider_user_id": None,
                        "is_verified": True,
                        "updated_at": now,
                        "last_login_at": now,
                    }
                },
            )
            existing.update(
                {
                    "name": display_name,
                    "password_hash": password_hash,
                    "auth_provider": "email_password",
                    "provider_user_id": None,
                    "is_verified": True,
                    "updated_at": now,
                    "last_login_at": now,
                }
            )
            user = existing
        else:
            insert = {
                "email": normalized,
                "name": display_name,
                "password_hash": password_hash,
                "auth_provider": "email_password",
                "provider_user_id": None,
                "is_verified": True,
                "company_id": None,
                "created_at": now,
                "updated_at": now,
                "last_login_at": now,
            }
            result = await self.users.insert_one(insert)
            user = {**insert, "_id": result.inserted_id}

        token = create_access_token(str(user["_id"]))
        return {"token": token, "user": self._serialize_user(user)}

    async def signin_with_password(self, email: str, password: str) -> Dict[str, Any]:
        normalized = (email or "").strip().lower()
        if not validate_email(normalized):
            raise ValueError("Invalid email address")
        if not password:
            raise ValueError("Password is required")

        user = await self.users.find_one({"email": normalized})
        if not user:
            raise ValueError("Invalid email or password")

        password_hash = user.get("password_hash")
        if not password_hash:
            provider = str(user.get("auth_provider") or "").lower()
            if provider == "google" or user.get("provider_user_id"):
                raise ValueError("This email is linked to Google sign-in. Continue with Google.")
            raise ValueError("This account has no password set. Please sign up first.")

        if not verify_password_hash(password, str(password_hash)):
            raise ValueError("Invalid email or password")

        now = now_utc()
        await self.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "is_verified": True,
                    "updated_at": now,
                    "last_login_at": now,
                }
            },
        )
        user.update({"is_verified": True, "updated_at": now, "last_login_at": now})

        token = create_access_token(str(user["_id"]))
        return {"token": token, "user": self._serialize_user(user)}

    async def start_email_auth(self, email: str) -> Dict[str, Any]:
        normalized = (email or "").strip().lower()
        if not validate_email(normalized):
            raise ValueError("Invalid email address")

        otp_code = settings.DEV_OTP_CODE
        expires_at = now_utc() + timedelta(minutes=settings.OTP_EXPIRES_MIN)

        await self.otps.insert_one(
            {
                "email": normalized,
                "otp": otp_code,
                "created_at": now_utc(),
                "expires_at": expires_at,
            }
        )

        logger.info("auth.otp_generated", email=normalized, otp=otp_code)
        payload: Dict[str, Any] = {"otp_sent": True}
        if settings.DEBUG:
            payload["dev_otp"] = otp_code
        return payload

    async def verify_email_auth(self, email: str, otp: str) -> Dict[str, Any]:
        normalized = (email or "").strip().lower()
        if not validate_email(normalized):
            raise ValueError("Invalid email address")

        code = (otp or "").strip()
        if not code:
            raise ValueError("OTP is required")

        otp_doc = await self.otps.find_one(
            {"email": normalized},
            sort=[("created_at", -1)],
        )
        if not otp_doc:
            raise ValueError("OTP not found")

        expires_at = otp_doc.get("expires_at")
        if isinstance(expires_at, datetime) and ensure_utc(expires_at) < now_utc():
            raise ValueError("OTP expired")

        expected_otp = str(otp_doc.get("otp") or "")
        if code != expected_otp:
            raise ValueError("Invalid OTP")

        user = await self.users.find_one({"email": normalized})
        now = now_utc()
        if not user:
            insert = {
                "email": normalized,
                "name": normalized.split("@")[0],
                "auth_provider": "email_otp",
                "provider_user_id": None,
                "is_verified": True,
                "company_id": None,
                "created_at": now,
                "updated_at": now,
                "last_login_at": now,
            }
            result = await self.users.insert_one(insert)
            user = {**insert, "_id": result.inserted_id}
        else:
            if user.get("password_hash"):
                raise ValueError("This account uses email and password. Please sign in with password.")
            if str(user.get("auth_provider") or "").lower() == "google":
                raise ValueError("This email is linked to Google sign-in. Continue with Google.")
            await self.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "is_verified": True,
                        "updated_at": now,
                        "last_login_at": now,
                    }
                },
            )
            user.update({"is_verified": True, "updated_at": now, "last_login_at": now})

        token = create_access_token(str(user["_id"]))
        return {
            "token": token,
            "user": self._serialize_user(user),
        }

    async def me(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = await self.users.find_one(self._user_lookup_query(user_id))
        return self._serialize_user(user) if user else None

    async def set_user_company(self, user_id: str, company_id: str) -> None:
        await self.users.update_one(
            self._user_lookup_query(user_id),
            {"$set": {"company_id": company_id, "updated_at": now_utc()}},
        )

    def _user_lookup_query(self, user_id: str) -> Dict[str, Any]:
        try:
            return {"$or": [{"_id": ObjectId(user_id)}, {"_id": user_id}]}
        except Exception:
            return {"_id": user_id}

    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {"name", "username", "phone", "profession", "location", "about_me"}
        clean = {k: (v or "").strip() for k, v in updates.items() if k in allowed}
        if not clean:
            raise ValueError("No valid fields to update")

        clean["updated_at"] = now_utc()
        await self.users.update_one(self._user_lookup_query(user_id), {"$set": clean})
        user = await self.users.find_one(self._user_lookup_query(user_id))
        return self._serialize_user(user)

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> Dict[str, Any]:
        user = await self.users.find_one(self._user_lookup_query(user_id))
        if not user:
            raise ValueError("User not found")

        existing_hash = user.get("password_hash")
        if not existing_hash:
            raise ValueError("This account does not use password authentication")

        if not verify_password_hash(current_password, str(existing_hash)):
            raise ValueError("Current password is incorrect")

        new_hash = hash_password(new_password)
        await self.users.update_one(
            self._user_lookup_query(user_id),
            {"$set": {"password_hash": new_hash, "updated_at": now_utc()}},
        )
        return {"updated": True}

    async def update_notifications(self, user_id: str, preferences: Dict[str, bool]) -> Dict[str, Any]:
        allowed = {"tender_updates", "matching_tenders", "expiring_tenders"}
        clean = {k: bool(v) for k, v in preferences.items() if k in allowed}
        await self.users.update_one(
            self._user_lookup_query(user_id),
            {"$set": {"notification_preferences": clean, "updated_at": now_utc()}},
        )
        return {"updated": True, "notification_preferences": clean}

    async def delete_account(self, user_id: str) -> Dict[str, Any]:
        user = await self.users.find_one(self._user_lookup_query(user_id))
        if not user:
            raise ValueError("User not found")
        await self.users.delete_one({"_id": user["_id"]})
        return {"deleted": True}

    def _serialize_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        if not user:
            return user
        user_data = dict(user)
        user_data["id"] = str(user_data["_id"])
        user_data["_id"] = str(user_data["_id"])
        user_data.pop("password_hash", None)
        return user_data
