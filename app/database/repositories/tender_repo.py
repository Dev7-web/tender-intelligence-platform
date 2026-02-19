"""
Tender repository for CRUD operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class TenderRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.get_collection("tenders")

    async def create(self, tender: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        tender.setdefault("created_at", now)
        tender.setdefault("updated_at", now)
        result = await self.collection.insert_one(tender)
        return str(result.inserted_id)

    async def upsert_by_bid_id(self, bid_id: str, data: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        data = dict(data)
        data.pop("created_at", None)
        data["updated_at"] = now
        result = await self.collection.update_one(
            {"bid_id": bid_id},
            {"$setOnInsert": {"created_at": now}, "$set": data},
            upsert=True,
        )
        if result.upserted_id:
            return str(result.upserted_id)
        existing = await self.collection.find_one({"bid_id": bid_id}, {"_id": 1})
        return str(existing["_id"]) if existing else ""

    async def get_by_id(self, tender_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(tender_id)})

    async def get_by_bid_id(self, bid_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"bid_id": bid_id})

    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        cursor = self.collection.find(filters or {}).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def update(self, tender_id: str, data: Dict[str, Any]) -> bool:
        data["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.update_one({"_id": ObjectId(tender_id)}, {"$set": data})
        return result.modified_count > 0

    async def set_status(self, bid_id: str, status: Dict[str, Any]) -> bool:
        update = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        result = await self.collection.update_one({"bid_id": bid_id}, {"$set": update})
        return result.modified_count > 0

    async def delete(self, tender_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(tender_id)})
        return result.deleted_count > 0
