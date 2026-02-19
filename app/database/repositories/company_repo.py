"""
Company repository for CRUD operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class CompanyRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.get_collection("company_profiles")

    async def create(self, profile: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        profile.setdefault("created_at", now)
        profile.setdefault("updated_at", now)
        result = await self.collection.insert_one(profile)
        return str(result.inserted_id)

    async def get_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"company_id": company_id})

    async def get_by_object_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(profile_id)})

    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        cursor = self.collection.find(filters or {}).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def update(self, company_id: str, data: Dict[str, Any]) -> bool:
        data["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.update_one({"company_id": company_id}, {"$set": data})
        return result.modified_count > 0

    async def delete(self, company_id: str) -> bool:
        result = await self.collection.delete_one({"company_id": company_id})
        return result.deleted_count > 0
