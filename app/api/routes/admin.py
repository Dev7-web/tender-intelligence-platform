"""
Admin API routes — for Firebase-authenticated admin panel only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_db
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _require_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


def _serialize_user(user: Dict) -> Dict:
    user = dict(user)
    user["id"] = str(user.pop("_id", ""))
    user.pop("password_hash", None)
    for key in ("created_at", "updated_at", "last_login_at"):
        val = user.get(key)
        if val and isinstance(val, datetime):
            user[key] = val.isoformat()
    return user


def _build_buckets(period: str):
    now = utcnow()
    if period == "7d":
        starts = [
            (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            for i in range(6, -1, -1)
        ]
        labels = [s.strftime("%d %b") for s in starts]
    elif period == "10d":
        starts = [
            (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            for i in range(9, -1, -1)
        ]
        labels = [s.strftime("%d %b") for s in starts]
    elif period == "6m":
        starts, labels = [], []
        for i in range(5, -1, -1):
            m = (now.replace(day=1) - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            starts.append(m)
            labels.append(m.strftime("%b"))
    else:  # 12m
        starts, labels = [], []
        for i in range(11, -1, -1):
            m = (now.replace(day=1) - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            starts.append(m)
            labels.append(m.strftime("%b"))
    return labels, starts


@router.get("/stats", dependencies=[Depends(_require_admin_key)])
async def admin_stats(db: AsyncIOMotorDatabase = Depends(get_db)) -> Dict[str, Any]:
    users_coll = db.get_collection("users")
    actions_coll = db.get_collection("tender_actions")

    thirty_days_ago = utcnow() - timedelta(days=30)

    total_users = await users_coll.count_documents({})
    active_users = await users_coll.count_documents(
        {"last_login_at": {"$gte": thirty_days_ago}}
    )
    applied_tenders = await actions_coll.count_documents({"action": "applied"})
    discarded_tenders = await actions_coll.count_documents({"action": "discarded"})

    return {
        "total_users": total_users,
        "active_users": active_users,
        "applied_tenders": applied_tenders,
        "discarded_tenders": discarded_tenders,
    }


@router.get("/tender-stats", dependencies=[Depends(_require_admin_key)])
async def admin_tender_stats(
    period: str = Query("7d"),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    if period not in ("7d", "10d", "6m", "12m"):
        raise HTTPException(status_code=400, detail="Invalid period")

    actions_coll = db.get_collection("tender_actions")
    now = utcnow()
    labels, starts = _build_buckets(period)

    applied_series: List[int] = []
    discarded_series: List[int] = []

    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else now + timedelta(seconds=1)
        applied = await actions_coll.count_documents(
            {"action": "applied", "updated_at": {"$gte": start, "$lt": end}}
        )
        discarded = await actions_coll.count_documents(
            {"action": "discarded", "updated_at": {"$gte": start, "$lt": end}}
        )
        applied_series.append(applied)
        discarded_series.append(discarded)

    return {"period": period, "labels": labels, "applied": applied_series, "discarded": discarded_series}


@router.get("/users", dependencies=[Depends(_require_admin_key)])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(""),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    users_coll = db.get_collection("users")

    query: Dict[str, Any] = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
        ]

    total = await users_coll.count_documents(query)
    cursor = users_coll.find(query, {"password_hash": 0}).skip(skip).limit(limit).sort("created_at", -1)
    users = [_serialize_user(u) async for u in cursor]

    return {"total": total, "users": users}


@router.get("/users/{user_id}", dependencies=[Depends(_require_admin_key)])
async def get_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> Dict[str, Any]:
    users_coll = db.get_collection("users")
    actions_coll = db.get_collection("tender_actions")

    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await users_coll.find_one({"_id": oid}, {"password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user = _serialize_user(user)
    company_id = user.get("company_id")

    applied = saved = discarded = 0
    if company_id:
        applied = await actions_coll.count_documents({"company_id": company_id, "action": "applied"})
        saved = await actions_coll.count_documents({"company_id": company_id, "action": "saved"})
        discarded = await actions_coll.count_documents({"company_id": company_id, "action": "discarded"})

    user["tender_stats"] = {"applied": applied, "saved": saved, "discarded": discarded, "won": 0}
    return user


@router.put("/users/{user_id}/inactivate", dependencies=[Depends(_require_admin_key)])
async def toggle_user_status(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> Dict[str, Any]:
    users_coll = db.get_collection("users")

    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await users_coll.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_status = not user.get("is_active", True)
    await users_coll.update_one(
        {"_id": oid}, {"$set": {"is_active": new_status, "updated_at": utcnow()}}
    )
    return {"is_active": new_status}


@router.delete("/users/{user_id}", dependencies=[Depends(_require_admin_key)])
async def delete_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> Dict[str, Any]:
    users_coll = db.get_collection("users")

    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    result = await users_coll.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True}
