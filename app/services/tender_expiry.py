"""
Shared tender expiry helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dateutil import parser as date_parser


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc_datetime(value: Any) -> Optional[datetime]:
    """Normalize datetimes for expiry checks.

    MongoDB returns UTC datetimes as timezone-naive by default, so naive values
    are treated as UTC instead of local server time.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = date_parser.parse(value)
        except Exception:
            return None
    else:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def active_tender_filter(now: Optional[datetime] = None) -> Dict[str, Any]:
    current = ensure_utc_datetime(now) or utcnow()
    return {
        "expired": False,
        "scraped_info.end_date": {"$gte": current},
    }


def analyzed_active_tender_filter(now: Optional[datetime] = None) -> Dict[str, Any]:
    filters = active_tender_filter(now)
    filters["status.llm_processed"] = True
    return filters


def is_tender_active(tender: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    if not tender or tender.get("expired") is True:
        return False

    current = ensure_utc_datetime(now) or utcnow()
    end_date = ensure_utc_datetime((tender.get("scraped_info") or {}).get("end_date"))
    return end_date is not None and end_date >= current


def tender_inactive_reason(tender: Dict[str, Any], now: Optional[datetime] = None) -> Optional[str]:
    if is_tender_active(tender, now):
        return None

    end_date = ensure_utc_datetime((tender.get("scraped_info") or {}).get("end_date"))
    if end_date is None:
        return "missing_deadline"
    return "expired"


async def refresh_expired_flags(tenders_collection: Any, now: Optional[datetime] = None) -> int:
    current = ensure_utc_datetime(now) or utcnow()
    result = await tenders_collection.update_many(
        {
            "expired": False,
            "scraped_info.end_date": {"$lt": current},
        },
        {"$set": {"expired": True}},
    )
    return int(getattr(result, "modified_count", 0) or 0)
