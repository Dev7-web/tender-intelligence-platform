"""
FastAPI dependencies.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict

from bson import ObjectId
from fastapi import Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.database.mongodb import get_database
from app.services.auth_service import decode_access_token


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
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user = await db.get_collection("users").find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    user["id"] = str(user["_id"])
    user["_id"] = str(user["_id"])
    return user
