"""
Dashboard aggregation service.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.match_service import MatchService
from app.services.tender_expiry import active_tender_filter, is_tender_active, refresh_expired_flags


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DashboardService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.tenders = db.get_collection("tenders")
        self.companies = db.get_collection("company_profiles")
        self.searches = db.get_collection("search_history")
        self.jobs = db.get_collection("scrape_logs")
        self.actions = db.get_collection("tender_actions")
        self.match_service = MatchService(db)

    async def get_stats(
        self,
        owner_user_id: str,
        company_id: str | None = None,
        overview_range: str = "7d",
    ) -> Dict[str, Any]:
        now = utcnow()
        await refresh_expired_flags(self.tenders, now)

        profile = None
        if company_id:
            profile = await self.companies.find_one({"company_id": company_id, "owner_user_id": owner_user_id})
        if not profile:
            profile = await self.companies.find_one({"owner_user_id": owner_user_id}, sort=[("updated_at", -1)])

        active_company_id = profile.get("company_id") if profile else None
        company_name = (profile or {}).get("name") or "Company"

        analyzed_filter = active_tender_filter(now)
        analyzed_filter["status.llm_processed"] = True
        tenders_analyzed = await self.tenders.count_documents(analyzed_filter)

        best_tenders_found = 0
        if active_company_id:
            matches = await self.match_service.get_company_matches(
                company_id=active_company_id,
                owner_user_id=owner_user_id,
                q=None,
                time_period="30d",
                sort="best_match",
                min_score=0.8,
                page=1,
                limit=500,
            )
            best_tenders_found = matches.get("total", 0)

        saved_count = 0
        applied_count = 0
        if active_company_id:
            saved_count = await self._count_active_actions(active_company_id, "saved", now)
            applied_count = await self._count_active_actions(active_company_id, "applied", now)

        normalized_range = self._normalize_overview_range(overview_range)
        selected_start = self._overview_start_from_range(normalized_range)
        overview = await self._overview_counts(active_company_id, selected_start, now)

        seven_days_ago = now - timedelta(days=7)
        overview_last_7_days = (
            overview
            if normalized_range == "7d"
            else await self._overview_counts(active_company_id, seven_days_ago, now)
        )

        return {
            "company_id": active_company_id,
            "company_name": company_name,
            "totals": {
                "tenders_analyzed": tenders_analyzed,
                "best_tenders_found": best_tenders_found,
                "tenders_saved": saved_count,
                "tenders_applied": applied_count,
            },
            "overview_range": normalized_range,
            "overview": overview,
            "overview_last_7_days": overview_last_7_days,
        }

    async def get_report(
        self,
        owner_user_id: str,
        company_id: str | None,
        range_key: str,
    ) -> Dict[str, Any]:
        now = utcnow()
        await refresh_expired_flags(self.tenders, now)

        profile = None
        if company_id:
            profile = await self.companies.find_one({"company_id": company_id, "owner_user_id": owner_user_id})
        if not profile:
            profile = await self.companies.find_one({"owner_user_id": owner_user_id}, sort=[("updated_at", -1)])

        company = profile.get("company_id") if profile else None
        labels, bucket_starts = self._build_buckets(range_key)

        gathering_series: List[int] = []
        analyzed_series: List[int] = []
        saved_series: List[int] = []

        for i, start in enumerate(bucket_starts):
            end = bucket_starts[i + 1] if i + 1 < len(bucket_starts) else now + timedelta(seconds=1)

            gathering_filter = active_tender_filter(now)
            gathering_filter["scraped_at"] = {"$gte": start, "$lt": end}
            gathering = await self.tenders.count_documents(gathering_filter)

            analyzed_filter = active_tender_filter(now)
            analyzed_filter["processed_at"] = {"$gte": start, "$lt": end}
            analyzed_filter["status.llm_processed"] = True
            analyzed = await self.tenders.count_documents(analyzed_filter)
            if company:
                saved = await self._count_active_actions(
                    company,
                    "saved",
                    now,
                    {"updated_at": {"$gte": start, "$lt": end}},
                )
            else:
                saved = 0

            gathering_series.append(gathering)
            analyzed_series.append(analyzed)
            saved_series.append(saved)

        return {
            "range": range_key,
            "labels": labels,
            "series": {
                "gathering": gathering_series,
                "analyze": analyzed_series,
                "saved": saved_series,
            },
        }

    async def get_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        activity: List[Dict[str, Any]] = []

        async for tender in self.tenders.find().sort("created_at", -1).limit(limit):
            activity.append(
                {
                    "type": "tender",
                    "message": f"Tender scraped: {tender.get('bid_id')}",
                    "timestamp": tender.get("scraped_at") or tender.get("created_at"),
                    "data": {"bid_id": tender.get("bid_id")},
                }
            )

        async for job in self.jobs.find().sort("started_at", -1).limit(limit):
            activity.append(
                {
                    "type": "job",
                    "message": f"Job {job.get('job_type')} {job.get('status')}",
                    "timestamp": job.get("completed_at") or job.get("started_at"),
                    "data": {"job_id": job.get("job_id")},
                }
            )

        activity = [item for item in activity if item.get("timestamp")]
        activity.sort(key=lambda item: item["timestamp"], reverse=True)
        return activity[:limit]

    async def get_queue(self, limit: int = 20) -> List[Dict[str, Any]]:
        now = utcnow()
        await refresh_expired_flags(self.tenders, now)

        filters = active_tender_filter(now)
        filters["status.llm_processed"] = False
        cursor = self.tenders.find(filters).sort("created_at", -1).limit(limit)
        items: List[Dict[str, Any]] = []
        async for tender in cursor:
            items.append(
                {
                    "bid_id": tender.get("bid_id"),
                    "status": tender.get("status"),
                    "scraped_info": tender.get("scraped_info"),
                    "created_at": tender.get("created_at"),
                }
            )
        return items

    def _build_buckets(self, range_key: str) -> Tuple[List[str], List[datetime]]:
        now = utcnow()
        normalized = (range_key or "12m").lower()

        if normalized == "7d":
            starts = [(now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0) for i in range(6, -1, -1)]
            labels = [start.strftime("%d %b") for start in starts]
            return labels, starts

        if normalized == "10d":
            starts = [(now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0) for i in range(9, -1, -1)]
            labels = [start.strftime("%d %b") for start in starts]
            return labels, starts

        if normalized == "6m":
            starts = []
            labels = []
            for i in range(5, -1, -1):
                month = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                starts.append(month)
                labels.append(month.strftime("%b"))
            return labels, starts

        starts = []
        labels = []
        for i in range(11, -1, -1):
            month = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            starts.append(month)
            labels.append(month.strftime("%b"))
        return labels, starts

    async def _overview_counts(self, company_id: str | None, start: datetime, now: datetime) -> Dict[str, int]:
        gathering_filter = active_tender_filter(now)
        gathering_filter["scraped_at"] = {"$gte": start}
        gathering = await self.tenders.count_documents(gathering_filter)

        analyzed_filter = active_tender_filter(now)
        analyzed_filter["processed_at"] = {"$gte": start}
        analyzed_filter["status.llm_processed"] = True
        analyzed = await self.tenders.count_documents(analyzed_filter)

        saved = await self._count_active_actions(company_id, "saved", now, {"updated_at": {"$gte": start}}) if company_id else 0
        applied = await self._count_active_actions(company_id, "applied", now, {"updated_at": {"$gte": start}}) if company_id else 0
        return {
            "gathering": gathering,
            "analyzed": analyzed,
            "saved": saved,
            "applied": applied,
        }

    def _normalize_overview_range(self, range_key: str | None) -> str:
        normalized = (range_key or "7d").lower()
        return normalized if normalized in {"7d", "10d", "6m", "12m"} else "7d"

    def _overview_start_from_range(self, range_key: str) -> datetime:
        now = utcnow()
        if range_key == "10d":
            return now - timedelta(days=10)
        if range_key == "6m":
            return now - timedelta(days=180)
        if range_key == "12m":
            return now - timedelta(days=365)
        return now - timedelta(days=7)

    async def _count_active_actions(
        self,
        company_id: str,
        action: str,
        now: datetime,
        extra_filters: Dict[str, Any] | None = None,
    ) -> int:
        filters: Dict[str, Any] = {"company_id": company_id, "action": action}
        if extra_filters:
            filters.update(extra_filters)

        count = 0
        async for record in self.actions.find(filters):
            tender = await self._find_tender_by_id(record.get("tender_id"))
            if tender and is_tender_active(tender, now):
                count += 1
        return count

    async def _find_tender_by_id(self, tender_id: Any) -> Dict[str, Any] | None:
        if not tender_id:
            return None

        candidates: List[Any] = []
        if isinstance(tender_id, ObjectId):
            candidates.append(tender_id)
        else:
            try:
                candidates.append(ObjectId(str(tender_id)))
            except Exception:
                pass
            candidates.append(str(tender_id))

        for candidate in candidates:
            tender = await self.tenders.find_one({"_id": candidate})
            if tender:
                return tender
        return None
