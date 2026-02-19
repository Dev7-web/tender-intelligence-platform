"""
Tender action repository for saved/applied/discarded states.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TenderActionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.get_collection("tender_actions")

    async def set_action(
        self,
        company_id: str,
        user_id: str,
        tender_id: str,
        action: Optional[str],
        notes: Optional[str] = None,
    ) -> bool:
        if action is None:
            result = await self.collection.delete_one({"company_id": company_id, "tender_id": tender_id})
            return result.deleted_count > 0

        update: Dict[str, Any] = {
            "company_id": company_id,
            "user_id": user_id,
            "tender_id": tender_id,
            "action": action,
            "notes": notes,
            "updated_at": utcnow(),
        }
        await self.collection.update_one(
            {"company_id": company_id, "tender_id": tender_id},
            {
                "$set": update,
                "$setOnInsert": {"created_at": utcnow()},
            },
            upsert=True,
        )
        return True

    async def get_action_map(self, company_id: str, tender_ids: List[str]) -> Dict[str, str]:
        if not tender_ids:
            return {}
        cursor = self.collection.find({"company_id": company_id, "tender_id": {"$in": tender_ids}})
        result: Dict[str, str] = {}
        async for item in cursor:
            result[item.get("tender_id")] = item.get("action")
        return result

    async def list_by_company(
        self,
        company_id: str,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {"company_id": company_id}
        if action:
            filters["action"] = action
        cursor = self.collection.find(filters).sort("updated_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_by_company_action(self, company_id: str, action: str) -> int:
        return await self.collection.count_documents({"company_id": company_id, "action": action})

    async def count_by_company(self, company_id: str, action: Optional[str] = None) -> int:
        filters: Dict[str, Any] = {"company_id": company_id}
        if action:
            filters["action"] = action
        return await self.collection.count_documents(filters)
