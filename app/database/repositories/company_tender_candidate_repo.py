"""
Company-scoped tender candidate repository.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CompanyTenderCandidateRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.get_collection("company_tender_candidates")

    async def upsert_candidate(
        self,
        *,
        company_id: str,
        tender_id: str,
        bid_id: str,
        search_keyword: Optional[str],
        raw_score: float,
        match_score: float,
        match_reasons: List[str],
        qualified: bool,
        relevance_status: str = "accepted",
        relevance_score: float = 0.0,
        relevance_reasons: Optional[List[str]] = None,
        matched_core_terms: Optional[List[str]] = None,
    ) -> None:
        now = utcnow()
        await self.collection.update_one(
            {"company_id": company_id, "tender_id": tender_id},
            {
                "$setOnInsert": {
                    "company_id": company_id,
                    "tender_id": tender_id,
                    "bid_id": bid_id,
                    "discovered_at": now,
                },
                "$set": {
                    "search_keyword": search_keyword,
                    "raw_score": raw_score,
                    "match_score": match_score,
                    "match_reasons": match_reasons,
                    "qualified": qualified,
                    "relevance_status": relevance_status,
                    "relevance_score": relevance_score,
                    "relevance_reasons": relevance_reasons or [],
                    "matched_core_terms": matched_core_terms or [],
                    "last_scored_at": now,
                    "updated_at": now,
                },
            },
            upsert=True,
        )

    async def upsert_rejected(
        self,
        *,
        company_id: str,
        tender_id: str,
        bid_id: str,
        search_keyword: Optional[str],
        relevance_score: float,
        relevance_reasons: List[str],
        matched_core_terms: Optional[List[str]] = None,
    ) -> None:
        await self.upsert_candidate(
            company_id=company_id,
            tender_id=tender_id,
            bid_id=bid_id,
            search_keyword=search_keyword,
            raw_score=0.0,
            match_score=0.0,
            match_reasons=relevance_reasons,
            qualified=False,
            relevance_status="rejected",
            relevance_score=relevance_score,
            relevance_reasons=relevance_reasons,
            matched_core_terms=matched_core_terms or [],
        )

    async def get_company_bid_ids(self, company_id: str) -> set[str]:
        cursor = self.collection.find({"company_id": company_id}, {"bid_id": 1})
        return {doc.get("bid_id") async for doc in cursor if doc.get("bid_id")}

    async def list_for_company(
        self,
        company_id: str,
        *,
        qualified: Optional[bool] = None,
        discovered_since: Optional[datetime] = None,
        relevance_status: Optional[str] = "accepted",
    ) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {"company_id": company_id}
        if qualified is not None:
            filters["qualified"] = qualified
        if discovered_since:
            filters["discovered_at"] = {"$gte": discovered_since}
        if relevance_status is not None:
            filters["relevance_status"] = relevance_status
        cursor = self.collection.find(filters).sort("match_score", -1)
        return await cursor.to_list(length=2000)

    async def count_distinct_company_tenders(
        self,
        company_id: str,
        *,
        qualified: Optional[bool] = None,
        discovered_since: Optional[datetime] = None,
        relevance_status: Optional[str] = "accepted",
    ) -> int:
        filters: Dict[str, Any] = {"company_id": company_id}
        if qualified is not None:
            filters["qualified"] = qualified
        if discovered_since:
            filters["discovered_at"] = {"$gte": discovered_since}
        if relevance_status is not None:
            filters["relevance_status"] = relevance_status
        seen = set()
        async for doc in self.collection.find(filters, {"tender_id": 1}):
            if doc.get("tender_id"):
                seen.add(doc["tender_id"])
        return len(seen)

    async def exists(self, company_id: str, tender_id: str) -> bool:
        return bool(
            await self.collection.find_one(
                {"company_id": company_id, "tender_id": tender_id, "relevance_status": "accepted"},
                {"_id": 1},
            )
        )

    async def delete_for_company(self, company_id: str) -> None:
        await self.collection.delete_many({"company_id": company_id})
