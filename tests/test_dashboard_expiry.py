from datetime import datetime, timedelta, timezone

import pytest

from app.services.dashboard_service import DashboardService


def _tender(tender_id: str, *, end_date, llm_processed: bool, expired: bool = False):
    now = datetime.now(timezone.utc)
    return {
        "_id": tender_id,
        "bid_id": tender_id,
        "expired": expired,
        "is_active": True,
        "scraped_at": now,
        "processed_at": now if llm_processed else None,
        "created_at": now,
        "updated_at": now,
        "status": {"llm_processed": llm_processed},
        "scraped_info": {"end_date": end_date},
    }


async def _candidate(fake_db, *, company_id: str, tender_id: str, qualified: bool):
    now = datetime.now(timezone.utc)
    await fake_db.get_collection("company_tender_candidates").insert_one(
        {
            "company_id": company_id,
            "tender_id": tender_id,
            "bid_id": tender_id,
            "search_keyword": "demo",
            "raw_score": 0.7,
            "match_score": 0.7,
            "match_reasons": ["Domain match: demo"],
            "qualified": qualified,
            "relevance_status": "accepted",
            "relevance_score": 1.0,
            "relevance_reasons": ["Matched core profile terms: demo"],
            "matched_core_terms": ["demo"],
            "discovered_at": now,
            "last_scored_at": now,
            "updated_at": now,
        }
    )


@pytest.mark.asyncio
async def test_dashboard_stats_count_only_active_tenders_and_actions(fake_db, monkeypatch):
    now = datetime.now(timezone.utc)
    tenders = fake_db.get_collection("tenders")
    companies = fake_db.get_collection("company_profiles")
    actions = fake_db.get_collection("tender_actions")

    await companies.insert_one(
        {
            "_id": "profile-1",
            "company_id": "company-1",
            "owner_user_id": "user-1",
            "name": "Demo Company",
            "updated_at": now,
        }
    )
    await tenders.insert_one(_tender("active-saved", end_date=now + timedelta(days=5), llm_processed=True))
    await tenders.insert_one(_tender("active-applied", end_date=now + timedelta(days=5), llm_processed=True))
    await tenders.insert_one(_tender("active-naive", end_date=(now + timedelta(days=5)).replace(tzinfo=None), llm_processed=True))
    await tenders.insert_one(_tender("expired-analyzed", end_date=now - timedelta(days=5), llm_processed=True))
    await tenders.insert_one(_tender("active-pending", end_date=now + timedelta(days=5), llm_processed=False))
    await tenders.insert_one(_tender("missing-deadline", end_date=None, llm_processed=True))
    await _candidate(fake_db, company_id="company-1", tender_id="active-saved", qualified=True)
    await _candidate(fake_db, company_id="company-1", tender_id="active-applied", qualified=True)
    await _candidate(fake_db, company_id="company-1", tender_id="active-naive", qualified=True)
    await _candidate(fake_db, company_id="company-1", tender_id="expired-analyzed", qualified=True)

    await actions.insert_one({"company_id": "company-1", "tender_id": "active-saved", "action": "saved", "updated_at": now})
    await actions.insert_one({"company_id": "company-1", "tender_id": "expired-analyzed", "action": "saved", "updated_at": now})
    await actions.insert_one({"company_id": "company-1", "tender_id": "active-applied", "action": "applied", "updated_at": now})

    service = DashboardService(fake_db)

    async def fake_matches(**_kwargs):
        return {"total": 0}

    monkeypatch.setattr(service.match_service, "get_company_matches", fake_matches)

    stats = await service.get_stats(owner_user_id="user-1", company_id="company-1", overview_range="7d")

    assert stats["totals"]["tenders_analyzed"] == 3
    assert stats["totals"]["tenders_saved"] == 1
    assert stats["totals"]["tenders_applied"] == 1
    assert stats["overview"]["gathering"] == 3
    assert stats["overview"]["analyzed"] == 3
    assert stats["overview"]["saved"] == 1
    assert stats["overview"]["applied"] == 1
    assert (await tenders.find_one({"_id": "expired-analyzed"}))["expired"] is True


@pytest.mark.asyncio
async def test_dashboard_report_and_queue_exclude_expired_and_missing_deadline(fake_db):
    now = datetime.now(timezone.utc)
    tenders = fake_db.get_collection("tenders")
    companies = fake_db.get_collection("company_profiles")
    actions = fake_db.get_collection("tender_actions")

    await companies.insert_one(
        {
            "_id": "profile-1",
            "company_id": "company-1",
            "owner_user_id": "user-1",
            "name": "Demo Company",
            "updated_at": now,
        }
    )
    await tenders.insert_one(_tender("active-analyzed", end_date=now + timedelta(days=5), llm_processed=True))
    await tenders.insert_one(_tender("active-unqualified", end_date=now + timedelta(days=5), llm_processed=True))
    await tenders.insert_one(_tender("active-pending", end_date=now + timedelta(days=5), llm_processed=False))
    await tenders.insert_one(_tender("expired-analyzed", end_date=now - timedelta(days=5), llm_processed=True))
    await tenders.insert_one(_tender("missing-pending", end_date=None, llm_processed=False))
    await _candidate(fake_db, company_id="company-1", tender_id="active-analyzed", qualified=True)
    await _candidate(fake_db, company_id="company-1", tender_id="active-unqualified", qualified=False)
    await _candidate(fake_db, company_id="company-1", tender_id="expired-analyzed", qualified=True)
    await actions.insert_one({"company_id": "company-1", "tender_id": "active-analyzed", "action": "saved", "updated_at": now})
    await actions.insert_one({"company_id": "company-1", "tender_id": "expired-analyzed", "action": "saved", "updated_at": now})

    service = DashboardService(fake_db)

    report = await service.get_report(owner_user_id="user-1", company_id="company-1", range_key="7d")
    queue = await service.get_queue(limit=10)

    assert sum(report["series"]["gathering"]) == 2
    assert sum(report["series"]["analyze"]) == 1
    assert sum(report["series"]["saved"]) == 1
    assert [item["bid_id"] for item in queue] == ["active-pending"]
