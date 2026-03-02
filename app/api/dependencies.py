"""
FastAPI dependencies.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict
from fastapi import Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.services.firebase_admin import verify_firebase_token


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().lower()




async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    db = get_database()
    yield db


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = verify_firebase_token(token)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    uid = claims.get("uid") or claims.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    email = _normalize_email(claims.get("email"))
    if not email:
        raise HTTPException(status_code=401, detail="Email is required for this account")

    name = claims.get("name") or claims.get("display_name")
    is_admin = bool(claims.get("admin") is True)
    now = _utcnow()

    users = db.get_collection("users")
    user = await users.find_one({"provider_user_id": uid})
    update_fields = {
        "provider_user_id": uid,
        "auth_provider": "firebase",
        "is_verified": True,
        "is_admin": is_admin,
        "updated_at": now,
        "last_login_at": now,
    }
    if email:
        update_fields["email"] = email
    if name:
        update_fields["name"] = name

    if user:
        await users.update_one({"_id": user["_id"]}, {"$set": update_fields})
        user.update(update_fields)
    else:
        user_by_email = await users.find_one({"email": email}) if email else None
        if user_by_email:
            await users.update_one({"_id": user_by_email["_id"]}, {"$set": update_fields})
            user = user_by_email
            user.update(update_fields)
        else:
            display_name = name or email.split("@")[0]
            insert = {
                "email": email,
                "name": display_name,
                "auth_provider": "firebase",
                "provider_user_id": uid,
                "is_verified": True,
                "is_admin": is_admin,
                "company_id": None,
                "created_at": now,
                "updated_at": now,
                "last_login_at": now,
            }
            result = await users.insert_one(insert)
            user = {**insert, "_id": result.inserted_id}

    user["id"] = str(user["_id"])
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    return user


async def require_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
