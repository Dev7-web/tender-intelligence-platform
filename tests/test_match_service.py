from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

from app.services.match_service import MatchService


def _tender_doc(
    tender_id: str,
    bid_id: str,
    embedding: list[float],
    title: str,
    summary: str,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "_id": tender_id,
        "bid_id": bid_id,
        "created_at": now,
        "updated_at": now,
        "is_active": True,
        "expired": False,
        "scraped_at": now,
        "status": {"llm_processed": True},
        "summary_embedding": embedding,
        "scraped_info": {
            "department": "Public Works",
            "start_date": now - timedelta(days=2),
            "end_date": now + timedelta(days=10),
            "bid_value_range": "12 L",
            "items": title,
        },
        "metadata": {
            "title": title,
            "summary": summary,
            "domains": ["Infrastructure", "Civil"],
            "required_technologies": ["Survey"],
            "required_certifications": ["ISO 9001"],
            "location": "Jaipur, Rajasthan",
            "sector": "government",
        },
    }


@pytest.mark.asyncio
async def test_matches_fallback_to_closest_when_min_score_too_high(fake_db):
    service = MatchService(fake_db)
    companies = fake_db.get_collection("company_profiles")
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)

    await companies.insert_one(
        {
            "_id": "company-1",
            "company_id": "cmp-1",
            "owner_user_id": "user-1",
            "name": "Pan India",
            "interest_tags": ["Civil Works"],
            "metadata": {
                "summary": "Civil infrastructure works and maintenance for public projects",
                "domains": ["Infrastructure"],
                "capabilities": ["Civil Works", "Maintenance"],
                "government_experience": True,
            },
            "summary_embedding": [1.0, 0.0, 0.0],
            "created_at": now,
            "updated_at": now,
        }
    )

    await tenders.insert_one(
        _tender_doc(
            tender_id="t-1",
            bid_id="GEM/2026/B/1001",
            embedding=[0.98, 0.01, 0.01],
            title="Road restoration work",
            summary="Civil road restoration and related infrastructure maintenance",
        )
    )
    await tenders.insert_one(
        _tender_doc(
            tender_id="t-2",
            bid_id="GEM/2026/B/1002",
            embedding=[0.12, 0.88, 0.0],
            title="Medical equipment procurement",
            summary="Hospital equipment and consumables purchase",
        )
    )

    result = await service.get_company_matches(
        company_id="cmp-1",
        owner_user_id="user-1",
        q=None,
        time_period="latest",
        sort="best_match",
        min_score=1.2,
        page=1,
        limit=10,
    )

    assert result["total"] > 0
    assert result["items"]
    assert any(
        "closest available matches" in reason.lower()
        for reason in result["items"][0]["match"]["reasons"]
    )
    assert all(0.0 <= item["match"]["score"] <= 1.0 for item in result["items"])


@pytest.mark.asyncio
async def test_matches_rank_higher_embedding_similarity_first(fake_db):
    service = MatchService(fake_db)
    companies = fake_db.get_collection("company_profiles")
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)

    await companies.insert_one(
        {
            "_id": "company-2",
            "company_id": "cmp-2",
            "owner_user_id": "user-2",
            "name": "Infra Tech",
            "interest_tags": [],
            "metadata": {
                "summary": "Infrastructure technology provider",
                "domains": ["Infrastructure"],
                "capabilities": ["Civil Works"],
                "government_experience": True,
            },
            "summary_embedding": [1.0, 0.0, 0.0],
            "created_at": now,
            "updated_at": now,
        }
    )

    await tenders.insert_one(
        _tender_doc(
            tender_id="t-3",
            bid_id="GEM/2026/B/2001",
            embedding=[0.99, 0.01, 0.0],
            title="Civil infrastructure tender",
            summary="Public infrastructure civil works execution",
        )
    )
    await tenders.insert_one(
        _tender_doc(
            tender_id="t-4",
            bid_id="GEM/2026/B/2002",
            embedding=[0.05, 0.95, 0.0],
            title="Unrelated healthcare supply",
            summary="Healthcare supplies and diagnostic kits",
        )
    )

    result = await service.get_company_matches(
        company_id="cmp-2",
        owner_user_id="user-2",
        q=None,
        time_period="latest",
        sort="best_match",
        min_score=0.0,
        page=1,
        limit=10,
    )

    assert result["items"][0]["tender"]["bid_id"] == "GEM/2026/B/2001"
    assert result["items"][0]["match"]["score"] >= result["items"][1]["match"]["score"]


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["saved", "applied"])
async def test_update_action_rejects_saved_and_applied_for_expired_tender(fake_db, action):
    service = MatchService(fake_db)
    tender_id = ObjectId()
    await fake_db.get_collection("tenders").insert_one(
        {
            "_id": tender_id,
            "expired": True,
            "is_active": True,
        }
    )

    with pytest.raises(ValueError, match="expired"):
        await service.update_action(
            company_id="company-1",
            user_id="user-1",
            tender_id=str(tender_id),
            action=action,
        )

    stored_action = await fake_db.get_collection("tender_actions").find_one(
        {"company_id": "company-1", "tender_id": str(tender_id)}
    )
    assert stored_action is None


@pytest.mark.asyncio
async def test_update_action_allows_discard_cleanup_for_expired_tender(fake_db):
    service = MatchService(fake_db)
    tender_id = ObjectId()
    await fake_db.get_collection("tenders").insert_one(
        {
            "_id": tender_id,
            "expired": True,
            "is_active": True,
        }
    )
    await fake_db.get_collection("tender_actions").insert_one(
        {
            "company_id": "company-1",
            "user_id": "user-1",
            "tender_id": str(tender_id),
            "action": "discarded",
            "updated_at": datetime.now(timezone.utc),
        }
    )

    discard_result = await service.update_action(
        company_id="company-1",
        user_id="user-1",
        tender_id=str(tender_id),
        action="discarded",
    )
    clear_result = await service.update_action(
        company_id="company-1",
        user_id="user-1",
        tender_id=str(tender_id),
        action=None,
    )

    assert discard_result == {"updated": True, "action": "discarded"}
    assert clear_result == {"updated": True, "action": None}
    stored_action = await fake_db.get_collection("tender_actions").find_one(
        {"company_id": "company-1", "tender_id": str(tender_id)}
    )
    assert stored_action is None
