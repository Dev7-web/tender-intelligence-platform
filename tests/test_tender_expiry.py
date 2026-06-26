from datetime import datetime, timedelta, timezone

import pytest

from app.services.tender_expiry import (
    active_tender_filter,
    ensure_utc_datetime,
    is_tender_active,
    refresh_expired_flags,
    tender_inactive_reason,
)


def _tender(end_date, expired=False):
    return {
        "expired": expired,
        "scraped_info": {"end_date": end_date},
    }


def test_is_tender_active_requires_future_deadline():
    now = datetime(2026, 6, 26, 10, 0, tzinfo=timezone.utc)

    assert is_tender_active(_tender(now + timedelta(minutes=1)), now)
    assert not is_tender_active(_tender(now - timedelta(minutes=1)), now)
    assert not is_tender_active(_tender(None), now)
    assert not is_tender_active(_tender(now + timedelta(minutes=1), expired=True), now)

    assert tender_inactive_reason(_tender(None), now) == "missing_deadline"
    assert tender_inactive_reason(_tender(now - timedelta(minutes=1)), now) == "expired"


def test_naive_datetimes_are_treated_as_utc():
    value = datetime(2026, 6, 26, 10, 0)

    assert ensure_utc_datetime(value) == datetime(2026, 6, 26, 10, 0, tzinfo=timezone.utc)


def test_active_tender_filter_excludes_missing_deadline():
    now = datetime(2026, 6, 26, 10, 0, tzinfo=timezone.utc)

    assert active_tender_filter(now) == {
        "expired": False,
        "scraped_info.end_date": {"$gte": now},
    }


@pytest.mark.asyncio
async def test_refresh_expired_flags_marks_only_past_deadlines(fake_db):
    tenders = fake_db.get_collection("tenders")
    now = datetime(2026, 6, 26, 10, 0, tzinfo=timezone.utc)

    await tenders.insert_one({"_id": "past", "expired": False, "scraped_info": {"end_date": now - timedelta(days=1)}})
    await tenders.insert_one({"_id": "future", "expired": False, "scraped_info": {"end_date": now + timedelta(days=1)}})
    await tenders.insert_one({"_id": "missing", "expired": False, "scraped_info": {}})

    assert await refresh_expired_flags(tenders, now) == 1

    assert (await tenders.find_one({"_id": "past"}))["expired"] is True
    assert (await tenders.find_one({"_id": "future"}))["expired"] is False
    assert (await tenders.find_one({"_id": "missing"}))["expired"] is False
