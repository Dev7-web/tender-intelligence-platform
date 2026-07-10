"""
Company-to-tender matching service with hybrid scoring and actions.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from bson import ObjectId
from dateutil import parser as date_parser
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.database.repositories.company_tender_candidate_repo import CompanyTenderCandidateRepository
from app.database.repositories.company_repo import CompanyRepository
from app.database.repositories.tender_action_repo import TenderActionRepository
from app.database.repositories.tender_repo import TenderRepository
from app.processors.embedder import TextEmbedder
from app.services.matching_utils import calculate_enhanced_match_score
from app.services.tender_relevance import assess_tender_relevance
from app.services.tender_expiry import is_tender_active, refresh_expired_flags


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
        self.candidate_repo = CompanyTenderCandidateRepository(db)
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

        await refresh_expired_flags(self.tender_repo.collection, now)

        period = (time_period or "latest").lower()
        discovered_since = None
        if period == "7d":
            discovered_since = now - timedelta(days=7)
        elif period == "30d":
            discovered_since = now - timedelta(days=30)

        candidate_docs = await self.candidate_repo.list_for_company(
            company_id,
            qualified=True,
            discovered_since=discovered_since,
        )

        candidate_pairs = []
        for candidate_doc in candidate_docs:
            tender = await self._find_tender_by_id(candidate_doc.get("tender_id"))
            if not tender:
                continue
            if not is_tender_active(tender, now):
                continue
            if tender.get("is_active") is not True:
                continue
            if (tender.get("status") or {}).get("llm_processed") is not True:
                continue
            if not self._tender_matches_request_filters(
                tender=tender,
                q=q,
                state=state,
                city=city,
                certification=certification,
                portal=portal,
                procurement=procurement,
                organisation=organisation,
            ):
                continue
            candidate_pairs.append((candidate_doc, tender))

        # Exclude tenders the user has discarded
        discarded_ids = await self.action_repo.get_discarded_tender_ids(company_id)
        if discarded_ids:
            candidate_pairs = [
                pair for pair in candidate_pairs
                if str(pair[1].get("_id")) not in discarded_ids
            ]

        # Amount range filtering (done in Python because values are free-form strings)
        if amount_range and amount_range in AMOUNT_RANGES:
            min_amt, max_amt = AMOUNT_RANGES[amount_range]
            filtered_candidates = []
            for candidate_doc, tender in candidate_pairs:
                meta = tender.get("metadata") or {}
                scraped = tender.get("scraped_info") or {}
                amount = (
                    _parse_amount_inr(str(meta.get("estimated_value") or ""))
                    or _parse_amount_inr(str(scraped.get("bid_value_range") or ""))
                )
                if amount is not None and min_amt <= amount < max_amt:
                    filtered_candidates.append((candidate_doc, tender))
            candidate_pairs = filtered_candidates

        profile_embedding = self._profile_embedding(profile)
        profile_text = self._build_profile_text(profile)

        scored: List[Dict[str, Any]] = []
        for candidate_doc, tender in candidate_pairs:
            score_data = self.score_tender_for_profile(
                profile=profile,
                tender=tender,
                profile_embedding=profile_embedding,
                profile_text=profile_text,
            )
            scored.append(
                {
                    "tender": tender,
                    "raw_score": score_data["raw_score"],
                    "score": score_data["match_score"],
                    "qualified": score_data["qualified"],
                    "reasons": score_data["match_reasons"],
                    "candidate": candidate_doc,
                }
            )

        if not scored:
            return {
                "items": [],
                "page": page,
                "limit": limit,
                "total": 0,
            }

        filtered = [item for item in scored if item["qualified"] and item["score"] >= min_score]
        if not filtered:
            return {
                "items": [],
                "page": page,
                "limit": limit,
                "total": 0,
            }

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

        if not await self.candidate_repo.exists(company_id=company_id, tender_id=str(tender.get("_id"))):
            raise ValueError("Tender is not available for this company profile")

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
        all_records = await self.action_repo.list_by_company(company_id=company_id, action=action, skip=0, limit=5000)
        scoped_records = []
        for record in all_records:
            if await self.candidate_repo.exists(company_id=company_id, tender_id=str(record.get("tender_id") or "")):
                scoped_records.append(record)
        total = len(scoped_records)
        records = scoped_records[skip:skip + limit]

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

    def score_tender_for_profile(
        self,
        *,
        profile: Dict[str, Any],
        tender: Dict[str, Any],
        profile_embedding: Optional[List[float]] = None,
        profile_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        profile_embedding = profile_embedding if profile_embedding is not None else self._profile_embedding(profile)
        profile_text = profile_text if profile_text is not None else self._build_profile_text(profile)
        profile_meta = profile.get("metadata") or {}

        tender_meta = tender.get("metadata") or {}
        tender_text = self._build_tender_text(tender)
        tender_embedding = self._tender_embedding(tender, tender_text)
        embedding_similarity = max(0.0, self._cosine_similarity(profile_embedding, tender_embedding))
        relevance = assess_tender_relevance(profile=profile, tender=tender)

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

        reasons = list(relevance["relevance_reasons"]) + list(structured_reasons)
        reasons.append(f"Embedding similarity: {int(round(embedding_similarity * 100))}%")
        if overlap_terms:
            reasons.append(f"Profile-data overlap: {', '.join(overlap_terms[:3])}")
        if boost_reason:
            reasons.append(boost_reason)

        qualified = relevance["accepted"] and raw_score >= settings.MATCH_MIN_QUALIFIED_SCORE
        return {
            "raw_score": raw_score,
            "match_score": raw_score,
            "match_reasons": reasons,
            "qualified": qualified,
            "relevance_status": relevance["relevance_status"],
            "relevance_score": relevance["relevance_score"],
            "relevance_reasons": relevance["relevance_reasons"],
            "matched_core_terms": relevance["matched_core_terms"],
        }

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
            phrase_pattern = rf"(?<![a-z0-9]){re.escape(tag)}(?![a-z0-9])"
            if tag in tender_terms or re.search(phrase_pattern, summary):
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

    async def _find_tender_by_id(self, tender_id: Any) -> Optional[Dict[str, Any]]:
        if not tender_id:
            return None

        candidates: List[Any] = []
        try:
            candidates.append(ObjectId(str(tender_id)))
        except Exception:
            pass
        candidates.append(str(tender_id))

        for candidate in candidates:
            tender = await self.tender_repo.collection.find_one({"_id": candidate})
            if tender:
                return tender
        return None

    def _tender_matches_request_filters(
        self,
        *,
        tender: Dict[str, Any],
        q: Optional[str],
        state: Optional[str],
        city: Optional[str],
        certification: Optional[str],
        portal: Optional[str],
        procurement: Optional[str],
        organisation: Optional[str],
    ) -> bool:
        blob = self._search_blob(tender)

        if q:
            words = [word.strip().lower() for word in q.split() if word.strip()]
            if any(word not in blob for word in words):
                return False

        for value in self._split_filter_values(state):
            if value not in blob:
                return False
        for value in self._split_filter_values(city):
            if value not in blob:
                return False
        for value in self._split_filter_values(certification):
            if value not in self._metadata_list_blob(tender, "required_certifications"):
                return False
        if portal and portal.strip().lower() not in str(tender.get("portal") or "").lower():
            return False
        if procurement:
            procurement_text = " ".join(
                str(part or "")
                for part in [
                    (tender.get("scraped_info") or {}).get("bid_type"),
                    (tender.get("metadata") or {}).get("title"),
                    (tender.get("metadata") or {}).get("summary"),
                ]
            ).lower()
            if procurement.strip().lower() not in procurement_text:
                return False
        for value in self._split_filter_values(organisation):
            org_blob = " ".join(
                str(part or "")
                for part in [
                    (tender.get("scraped_info") or {}).get("department"),
                    (tender.get("metadata") or {}).get("department"),
                ]
            ).lower()
            if value not in org_blob:
                return False

        return True

    def _search_blob(self, tender: Dict[str, Any]) -> str:
        return " ".join(
            str(self._nested_get(tender, field) or "")
            for field in SEARCH_FIELDS
        ).lower()

    def _metadata_list_blob(self, tender: Dict[str, Any], key: str) -> str:
        values = (tender.get("metadata") or {}).get(key) or []
        if not isinstance(values, list):
            values = [values]
        return " ".join(str(value or "") for value in values).lower()

    @staticmethod
    def _nested_get(doc: Dict[str, Any], path: str) -> Any:
        current: Any = doc
        for key in path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    @staticmethod
    def _split_filter_values(value: Optional[str]) -> List[str]:
        if not value:
            return []
        return [item.strip().lower() for item in value.split(",") if item.strip()]

    @staticmethod
    def _has_meaningful_match(reasons: List[str]) -> bool:
        meaningful_prefixes = (
            "Domain match:",
            "Technology match:",
            "Capability match:",
            "Cross match:",
        )
        return any(reason.startswith(meaningful_prefixes) for reason in reasons)

    def _timestamp(self, value: Any) -> float:
        if isinstance(value, datetime):
            return value.timestamp()
        if isinstance(value, str):
            try:
                return date_parser.parse(value).timestamp()
            except Exception:
                return 0.0
        return 0.0
