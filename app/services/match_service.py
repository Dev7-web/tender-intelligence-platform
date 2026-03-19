"""
Company-to-tender matching service with hybrid scoring and actions.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from dateutil import parser as date_parser
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.repositories.company_repo import CompanyRepository
from app.database.repositories.tender_action_repo import TenderActionRepository
from app.database.repositories.tender_repo import TenderRepository
from app.processors.embedder import TextEmbedder
from app.services.matching_utils import calculate_enhanced_match_score


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


STOP_WORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "under",
    "over",
    "are",
    "was",
    "were",
    "you",
    "your",
    "have",
    "has",
    "had",
    "not",
    "all",
    "any",
    "our",
    "their",
    "shall",
    "will",
    "can",
    "bid",
    "tender",
    "project",
    "work",
    "works",
}


SEARCH_FIELDS = [
    "metadata.title",
    "metadata.summary",
    "scraped_info.department",
    "metadata.department",
    "metadata.location",
    "metadata.domains",
    "metadata.required_technologies",
    "bid_id",
]

# Amount range boundaries in INR
AMOUNT_RANGES: Dict[str, Tuple[float, float]] = {
    "under_1L": (0, 1_00_000),
    "1L_10L": (1_00_000, 10_00_000),
    "10L_50L": (10_00_000, 50_00_000),
    "50L_1Cr": (50_00_000, 1_00_00_000),
    "above_1Cr": (1_00_00_000, float("inf")),
}


def _parse_amount_inr(text: str) -> Optional[float]:
    """Try to extract a numeric INR value from a free-form amount string."""
    if not text:
        return None
    cleaned = text.lower().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "").replace("inr", "").strip()

    # Match patterns like "5 crore", "10 lakh", "50000"
    match = re.search(r"([\d.]+)\s*(crore|cr|lakh|lac|l|k)?\b", cleaned)
    if not match:
        return None

    try:
        number = float(match.group(1))
    except ValueError:
        return None

    unit = (match.group(2) or "").strip()
    if unit in ("crore", "cr"):
        return number * 1_00_00_000
    if unit in ("lakh", "lac", "l"):
        return number * 1_00_000
    if unit == "k":
        return number * 1_000
    return number


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
        state: Optional[str] = None,
        city: Optional[str] = None,
        certification: Optional[str] = None,
        portal: Optional[str] = None,
        procurement: Optional[str] = None,
        organisation: Optional[str] = None,
        amount_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        profile = await self.company_repo.get_by_id(company_id)
        if not profile or profile.get("owner_user_id") != owner_user_id:
            raise ValueError("Company profile not found")

        now = utcnow()

        # --- Flush stale expired flags before querying ---
        await self.tender_repo.collection.update_many(
            {
                "expired": False,
                "scraped_info.end_date": {"$lt": now},
            },
            {"$set": {"expired": True}},
        )

        candidate_filter = {
            "is_active": True,
            "expired": False,
            "status.llm_processed": True,
            # Real-time date gate: only tenders whose deadline is still in the future
            "scraped_info.end_date": {"$gte": now},
        }
        period = (time_period or "latest").lower()
        if period == "7d":
            candidate_filter["scraped_at"] = {"$gte": now - timedelta(days=7)}
        elif period == "30d":
            candidate_filter["scraped_at"] = {"$gte": now - timedelta(days=30)}

        if q:
            words = [w.strip() for w in q.split() if w.strip()]
            word_conditions = []
            for word in words:
                escaped = re.escape(word)
                regex = {"$regex": escaped, "$options": "i"}
                word_conditions.append(
                    {"$or": [{field: regex} for field in SEARCH_FIELDS]}
                )
            if word_conditions:
                candidate_filter.setdefault("$and", []).extend(word_conditions)

        if state:
            candidate_filter["metadata.location"] = {"$regex": state, "$options": "i"}

        if city:
            if "metadata.location" in candidate_filter:
                candidate_filter["metadata.location"]["$regex"] = f"(?=.*{re.escape(state)})(?=.*{re.escape(city)})"
            else:
                candidate_filter["metadata.location"] = {"$regex": city, "$options": "i"}

        if certification:
            candidate_filter["metadata.required_certifications"] = {"$regex": certification, "$options": "i"}

        if portal:
            candidate_filter["portal"] = {"$regex": portal, "$options": "i"}

        if procurement:
            proc_regex = {"$regex": re.escape(procurement), "$options": "i"}
            candidate_filter.setdefault("$and", []).append(
                {"$or": [
                    {"scraped_info.bid_type": proc_regex},
                    {"metadata.title": proc_regex},
                    {"metadata.summary": proc_regex},
                ]}
            )

        if organisation:
            org_regex = {"$regex": re.escape(organisation), "$options": "i"}
            candidate_filter.setdefault("$and", []).append(
                {"$or": [
                    {"scraped_info.department": org_regex},
                    {"metadata.department": org_regex},
                ]}
            )

        candidates = await self.tender_repo.list(skip=0, limit=1000, filters=candidate_filter)

        # Exclude tenders the user has discarded
        discarded_ids = await self.action_repo.get_discarded_tender_ids(company_id)
        if discarded_ids:
            candidates = [
                t for t in candidates
                if str(t.get("_id")) not in discarded_ids
            ]

        # Amount range filtering (done in Python because values are free-form strings)
        if amount_range and amount_range in AMOUNT_RANGES:
            min_amt, max_amt = AMOUNT_RANGES[amount_range]
            filtered_candidates = []
            for tender in candidates:
                meta = tender.get("metadata") or {}
                scraped = tender.get("scraped_info") or {}
                amount = (
                    _parse_amount_inr(str(meta.get("estimated_value") or ""))
                    or _parse_amount_inr(str(scraped.get("bid_value_range") or ""))
                )
                if amount is not None and min_amt <= amount < max_amt:
                    filtered_candidates.append(tender)
            candidates = filtered_candidates

        profile_embedding = self._profile_embedding(profile)
        profile_meta = profile.get("metadata") or {}
        profile_text = self._build_profile_text(profile)

        scored: List[Dict[str, Any]] = []
        for tender in candidates:
            tender_meta = tender.get("metadata") or {}
            tender_text = self._build_tender_text(tender)
            tender_embedding = self._tender_embedding(tender, tender_text)
            embedding_similarity = self._cosine_similarity(profile_embedding, tender_embedding)

            structured_score, structured_reasons = calculate_enhanced_match_score(
                tender_meta=tender_meta,
                profile_meta=profile_meta,
                vector_similarity=embedding_similarity,
            )

            overlap_score, overlap_terms = self._profile_tender_overlap_score(profile_text, tender_text)

            boosted_score, boost_reason = self._interest_tag_boost(
                interest_tags=profile.get("interest_tags") or [],
                tender_meta=tender_meta,
            )
            raw_score = min(
                (embedding_similarity * 0.55)
                + (structured_score * 0.35)
                + (overlap_score * 0.10)
                + boosted_score,
                1.0,
            )

            reasons = list(structured_reasons)
            reasons.append(f"Embedding similarity: {int(round(embedding_similarity * 100))}%")
            if overlap_terms:
                reasons.append(f"Profile-data overlap: {', '.join(overlap_terms[:3])}")
            if boost_reason:
                reasons.append(boost_reason)

            scored.append(
                {
                    "tender": tender,
                    "raw_score": raw_score,
                    "score": 0.0,
                    "reasons": reasons,
                }
            )

        if not scored:
            return {
                "items": [],
                "page": page,
                "limit": limit,
                "total": 0,
            }

        self._normalize_scores(scored)

        filtered = [item for item in scored if item["score"] >= min_score]
        if not filtered:
            sorted_candidates = sorted(scored, key=lambda item: item["score"], reverse=True)
            fallback_count = min(len(sorted_candidates), max(limit * 3, 10))
            filtered = sorted_candidates[:fallback_count]
            for item in filtered:
                if "Showing closest available matches" not in item["reasons"]:
                    item["reasons"].insert(0, "Showing closest available matches")

        sort_key = (sort or "best_match").lower()
        if "closing_soon" in sort_key:
            # Urgent-first: tenders closest to their deadline appear first
            filtered.sort(
                key=lambda item: self._timestamp(
                    (item["tender"].get("scraped_info") or {}).get("end_date")
                ),
            )
        elif "latest" in sort_key:
            filtered.sort(
                key=lambda item: self._timestamp(
                    (item["tender"].get("scraped_info") or {}).get("start_date")
                    or item["tender"].get("scraped_at")
                    or item["tender"].get("created_at")
                ),
                reverse=True,
            )
        else:
            filtered.sort(
                key=lambda item: (
                    item["score"],
                    self._timestamp((item["tender"].get("scraped_info") or {}).get("end_date")),
                ),
                reverse=True,
            )

        total = len(filtered)
        start = max(page - 1, 0) * limit
        end = start + limit
        page_items = filtered[start:end]

        action_map = await self.action_repo.get_action_map(
            company_id,
            [str(item["tender"].get("_id")) for item in page_items],
        )

        items = []
        for item in page_items:
            tender = item["tender"]
            serialized = self._serialize_tender(tender)
            tender_id = serialized.get("id")
            items.append(
                {
                    "tender": serialized,
                    "match": {"score": round(item["score"], 4), "reasons": item["reasons"][:5]},
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
        reason: Optional[str] = None,
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
            notes=reason,
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

    def _normalize_scores(self, scored: List[Dict[str, Any]]) -> None:
        raw_scores = [item["raw_score"] for item in scored]
        min_raw = min(raw_scores)
        max_raw = max(raw_scores)
        spread = max_raw - min_raw

        for item in scored:
            raw = item["raw_score"]
            if spread <= 1e-9:
                normalized = raw
            else:
                percentile = (raw - min_raw) / spread
                normalized = 0.55 + (0.45 * percentile)
            item["score"] = min(max(normalized, 0.0), 1.0)

    def _serialize_tender(self, tender: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(tender)
        data["id"] = str(data["_id"])
        data["_id"] = str(data["_id"])
        return data

    def _profile_embedding(self, profile: Dict[str, Any]) -> List[float]:
        embedding = profile.get("summary_embedding") or []
        if embedding:
            return embedding
        fallback_text = self._build_profile_text(profile)
        return self.embedder.embed(fallback_text) if fallback_text else []

    def _tender_embedding(self, tender: Dict[str, Any], tender_text: str) -> List[float]:
        embedding = tender.get("summary_embedding") or []
        if embedding:
            return embedding
        return self.embedder.embed(tender_text) if tender_text else []

    def _build_profile_text(self, profile: Dict[str, Any]) -> str:
        meta = profile.get("metadata") or {}
        chunks: List[str] = [
            str(profile.get("name") or ""),
            str(meta.get("company_name") or ""),
            str(meta.get("summary") or ""),
            " ".join(str(item) for item in (meta.get("domains") or [])),
            " ".join(str(item) for item in (meta.get("technologies") or [])),
            " ".join(str(item) for item in (meta.get("certifications") or [])),
            " ".join(str(item) for item in (meta.get("capabilities") or [])),
            " ".join(str(item) for item in (profile.get("interest_tags") or [])),
            str((profile.get("website_scrape") or {}).get("extracted_text") or "")[:5000],
        ]
        return " ".join(part for part in chunks if part).strip()

    def _build_tender_text(self, tender: Dict[str, Any]) -> str:
        meta = tender.get("metadata") or {}
        scraped = tender.get("scraped_info") or {}
        chunks: List[str] = [
            str(meta.get("title") or ""),
            str(meta.get("summary") or ""),
            str(scraped.get("department") or ""),
            str(meta.get("department") or ""),
            str(meta.get("location") or ""),
            " ".join(str(item) for item in (meta.get("domains") or [])),
            " ".join(str(item) for item in (meta.get("required_technologies") or [])),
            " ".join(str(item) for item in (meta.get("required_certifications") or [])),
            str(scraped.get("items") or ""),
            str(tender.get("bid_id") or ""),
        ]
        return " ".join(part for part in chunks if part).strip()

    def _profile_tender_overlap_score(self, profile_text: str, tender_text: str) -> Tuple[float, List[str]]:
        profile_tokens = self._tokenize(profile_text)
        tender_tokens = self._tokenize(tender_text)
        if not profile_tokens or not tender_tokens:
            return 0.0, []

        overlap = profile_tokens.intersection(tender_tokens)
        if not overlap:
            return 0.0, []

        union = profile_tokens.union(tender_tokens)
        jaccard = len(overlap) / max(len(union), 1)
        profile_coverage = len(overlap) / max(len(profile_tokens), 1)
        score = min((jaccard * 0.5) + (profile_coverage * 0.5), 1.0)
        overlap_terms = sorted(overlap, key=len, reverse=True)[:5]
        return score, overlap_terms

    def _tokenize(self, text: str) -> set[str]:
        normalized = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
        if not normalized:
            return set()
        return {
            token
            for token in normalized.split()
            if len(token) >= 4 and token not in STOP_WORDS and not token.isdigit()
        }

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
        if isinstance(value, str):
            try:
                return date_parser.parse(value).timestamp()
            except Exception:
                return 0.0
        return 0.0
