"""
Persistent rate limiting for authentication endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(value: str | None) -> str:
    return (value or "").strip().lower() or "<missing>"


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"


class AuthRateLimiter:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.get_collection("auth_rate_limits")

    async def enforce_auth_limit(self, request: Request, action: str, email: str | None = None) -> None:
        await self._enforce(
            scope=f"auth:{action}:ip",
            key=client_ip(request),
            limit=settings.AUTH_RATE_LIMIT_IP_REQUESTS,
            window_seconds=settings.AUTH_RATE_LIMIT_IP_WINDOW_SECONDS,
        )

        if email is not None:
            await self._enforce(
                scope=f"auth:{action}:email",
                key=normalize_email(email),
                limit=settings.AUTH_RATE_LIMIT_EMAIL_REQUESTS,
                window_seconds=settings.AUTH_RATE_LIMIT_EMAIL_WINDOW_SECONDS,
            )

    async def _enforce(self, scope: str, key: str, limit: int, window_seconds: int) -> None:
        now = utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        result = await self.collection.insert_one({"scope": scope, "key": key, "ts": now})
        count = await self.collection.count_documents(
            {
                "scope": scope,
                "key": key,
                "ts": {"$gte": window_start},
            }
        )

        if count > limit:
            await self.collection.delete_one({"_id": result.inserted_id})
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts. Please retry later.",
                headers={"Retry-After": str(window_seconds)},
            )
