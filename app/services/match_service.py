"""
Company-to-tender matching service with hybrid scoring and actions.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.repositories.company_repo import CompanyRepository
from app.database.repositories.tender_action_repo import TenderActionRepository
from app.database.repositories.tender_repo import TenderRepository
from app.processors.embedder import TextEmbedder
from app.services.matching_utils import calculate_enhanced_match_score


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MatchService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.tender_repo = TenderRepository(db)
        self.action_repo = TenderActionRepository(db)
        self.embedder = TextEmbedder()

    async def get_company_matches(
        self,
        company_id: str,
        owner_user_id: str,
        q: Optional[str],
        time_period: str,
        sort: str,
        min_score: float,
        page: int,
        limit: int,
    ) -> Dict[str, Any]:
        profile = await self.company_repo.get_by_id(company_id)
        if not profile or profile.get("owner_user_id") != owner_user_id:
            raise ValueError("Company profile not found")

        candidate_filter = {
            "is_active": True,
            "expired": False,
            "status.llm_processed": True,
        }

        now = utcnow()
        period = (time_period or "latest").lower()
        if period == "7d":
            candidate_filter["scraped_at"] = {"$gte": now - timedelta(days=7)}
        elif period == "30d":
            candidate_filter["scraped_at"] = {"$gte": now - timedelta(days=30)}

        if q:
            regex = {"$regex": q, "$options": "i"}
            candidate_filter["$or"] = [
                {"metadata.title": regex},
                {"metadata.summary": regex},
                {"scraped_info.department": regex},
                {"metadata.department": regex},
                {"bid_id": regex},
            ]

        candidates = await self.tender_repo.list(skip=0, limit=1000, filters=candidate_filter)
        profile_embedding = profile.get("summary_embedding") or []
        if not profile_embedding:
            profile_summary = (profile.get("metadata") or {}).get("summary") or ""
            profile_embedding = self.embedder.embed(profile_summary)

        scored: List[Tuple[Dict[str, Any], float, List[str]]] = []
        for tender in candidates:
            tender_embedding = tender.get("summary_embedding") or []
            vector_similarity = self._cosine_similarity(profile_embedding, tender_embedding)

            tender_meta = tender.get("metadata") or {}
            profile_meta = profile.get("metadata") or {}
            score, reasons = calculate_enhanced_match_score(tender_meta, profile_meta, vector_similarity)

            boosted_score, boost_reason = self._interest_tag_boost(
                interest_tags=profile.get("interest_tags") or [],
                tender_meta=tender_meta,
            )
            score = min(score + boosted_score, 1.0)
            if boost_reason:
                reasons.append(boost_reason)

            if score >= min_score:
                scored.append((tender, score, reasons))

        sort_key = (sort or "best_match").lower()
        if "latest" in sort_key:
            scored.sort(key=lambda item: self._timestamp(item[0].get("scraped_at")), reverse=True)
        else:
            scored.sort(
                key=lambda item: (
                    item[1],
                    self._timestamp((item[0].get("scraped_info") or {}).get("end_date")),
                ),
                reverse=True,
            )

        total = len(scored)
        start = max(page - 1, 0) * limit
        end = start + limit
        page_items = scored[start:end]

        action_map = await self.action_repo.get_action_map(
            company_id,
            [str(item[0].get("_id")) for item in page_items],
        )

        items = []
        for tender, score, reasons in page_items:
            serialized = self._serialize_tender(tender)
            tender_id = serialized.get("id")
            items.append(
                {
                    "tender": serialized,
                    "match": {"score": round(score, 4), "reasons": reasons[:5]},
                    "action": action_map.get(tender_id),
                }
            )

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
        }

    async def update_action(
        self,
        company_id: str,
        user_id: str,
        tender_id: str,
        action: Optional[str],
    ) -> Dict[str, Any]:
        if action not in {"saved", "applied", "discarded", None}:
            raise ValueError("Invalid action")

        tender = await self.tender_repo.get_by_id(tender_id)
        if not tender:
            raise ValueError("Tender not found")

        await self.action_repo.set_action(
            company_id=company_id,
            user_id=user_id,
            tender_id=tender_id,
            action=action,
        )
        return {"updated": True, "action": action}

    async def get_my_list(
        self,
        company_id: str,
        tab: Optional[str],
        page: int,
        limit: int,
    ) -> Dict[str, Any]:
        action = tab if tab in {"saved", "applied", "discarded"} else None
        skip = max(page - 1, 0) * limit
        total = await self.action_repo.count_by_company(company_id=company_id, action=action)
        records = await self.action_repo.list_by_company(company_id=company_id, action=action, skip=skip, limit=limit)

        tender_ids = [record.get("tender_id") for record in records if record.get("tender_id")]
        tender_map: Dict[str, Dict[str, Any]] = {}
        for tender_id in tender_ids:
            tender = await self.tender_repo.get_by_id(tender_id)
            if tender:
                tender_map[tender_id] = self._serialize_tender(tender)

        items = []
        for record in records:
            tender_id = record.get("tender_id")
            items.append(
                {
                    "action": record.get("action"),
                    "updated_at": record.get("updated_at"),
                    "tender": tender_map.get(tender_id),
                }
            )

        return {"items": items, "page": page, "limit": limit, "total": total}

    def _interest_tag_boost(self, interest_tags: List[str], tender_meta: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        if not interest_tags:
            return 0.0, None

        normalized_tags = {tag.strip().lower() for tag in interest_tags if tag and tag.strip()}
        tender_terms = set()

        for key in ["domains", "required_technologies"]:
            for value in tender_meta.get(key, []) or []:
                if value:
                    tender_terms.add(str(value).strip().lower())

        summary = (tender_meta.get("summary") or "").lower()
        overlap = set()
        for tag in normalized_tags:
            if tag in tender_terms or tag in summary:
                overlap.add(tag)

        if not overlap:
            return 0.0, None

        boost = min(0.1, len(overlap) * 0.03)
        reason = f"Interest tag boost: {', '.join(sorted(overlap)[:3])}"
        return boost, reason

    def _serialize_tender(self, tender: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(tender)
        data["id"] = str(data["_id"])
        data["_id"] = str(data["_id"])
        return data

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        vec_a = np.array(a, dtype=float)
        vec_b = np.array(b, dtype=float)
        denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
        if denom == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / denom)

    def _timestamp(self, value: Any) -> float:
        if isinstance(value, datetime):
            return value.timestamp()
        return 0.0
