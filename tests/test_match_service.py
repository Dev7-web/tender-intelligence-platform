from datetime import datetime, timedelta, timezone

import pytest

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


async def _link_candidate(
    fake_db,
    *,
    company_id: str,
    tender_id: str,
    bid_id: str,
    qualified: bool = True,
    match_score: float = 0.8,
):
    now = datetime.now(timezone.utc)
    await fake_db.get_collection("company_tender_candidates").insert_one(
        {
            "company_id": company_id,
            "tender_id": tender_id,
            "bid_id": bid_id,
            "search_keyword": "infrastructure",
            "raw_score": match_score,
            "match_score": match_score,
            "match_reasons": ["Domain match: infrastructure"],
            "qualified": qualified,
            "relevance_status": "accepted",
            "relevance_score": 1.0,
            "relevance_reasons": ["Matched core profile terms: civil"],
            "matched_core_terms": ["civil"],
            "discovered_at": now,
            "last_scored_at": now,
            "updated_at": now,
        }
    )


@pytest.mark.asyncio
async def test_matches_hide_weak_candidates_when_min_score_too_high(fake_db):
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
    await _link_candidate(fake_db, company_id="cmp-1", tender_id="t-1", bid_id="GEM/2026/B/1001")
    await _link_candidate(fake_db, company_id="cmp-1", tender_id="t-2", bid_id="GEM/2026/B/1002", qualified=False)

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

    assert result["total"] == 0
    assert result["items"] == []


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
            embedding=[0.75, 0.25, 0.0],
            title="Infrastructure maintenance tender",
            summary="Public infrastructure maintenance with civil works support",
        )
    )
    await _link_candidate(fake_db, company_id="cmp-2", tender_id="t-3", bid_id="GEM/2026/B/2001")
    await _link_candidate(fake_db, company_id="cmp-2", tender_id="t-4", bid_id="GEM/2026/B/2002")

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
async def test_company_matches_only_show_company_candidate_tenders(fake_db):
    service = MatchService(fake_db)
    companies = fake_db.get_collection("company_profiles")
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)

    base_profile = {
        "name": "Infra Tech",
        "metadata": {
            "summary": "Infrastructure civil works",
            "domains": ["Infrastructure"],
            "capabilities": ["Civil Works"],
        },
        "summary_embedding": [1.0, 0.0, 0.0],
        "created_at": now,
        "updated_at": now,
    }
    await companies.insert_one({"_id": "profile-a", "company_id": "cmp-a", "owner_user_id": "user-a", **base_profile})
    await companies.insert_one({"_id": "profile-b", "company_id": "cmp-b", "owner_user_id": "user-b", **base_profile})
    await tenders.insert_one(
        _tender_doc(
            tender_id="shared-tender",
            bid_id="GEM/2026/B/3001",
            embedding=[0.98, 0.01, 0.0],
            title="Civil infrastructure tender",
            summary="Public infrastructure civil works execution",
        )
    )
    await _link_candidate(fake_db, company_id="cmp-a", tender_id="shared-tender", bid_id="GEM/2026/B/3001")

    company_a = await service.get_company_matches(
        company_id="cmp-a",
        owner_user_id="user-a",
        q=None,
        time_period="latest",
        sort="best_match",
        min_score=0.0,
        page=1,
        limit=10,
    )
    company_b = await service.get_company_matches(
        company_id="cmp-b",
        owner_user_id="user-b",
        q=None,
        time_period="latest",
        sort="best_match",
        min_score=0.0,
        page=1,
        limit=10,
    )

    assert company_a["total"] == 1
    assert company_b["total"] == 0


@pytest.mark.asyncio
async def test_company_matches_accept_naive_future_deadline(fake_db):
    service = MatchService(fake_db)
    companies = fake_db.get_collection("company_profiles")
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)

    await companies.insert_one(
        {
            "_id": "profile-naive",
            "company_id": "cmp-naive",
            "owner_user_id": "user-naive",
            "name": "Infra Tech",
            "interest_tags": [],
            "metadata": {
                "summary": "Infrastructure civil works",
                "domains": ["Infrastructure"],
                "capabilities": ["Civil Works"],
            },
            "summary_embedding": [1.0, 0.0, 0.0],
            "created_at": now,
            "updated_at": now,
        }
    )

    tender = _tender_doc(
        tender_id="naive-tender",
        bid_id="GEM/2026/B/3501",
        embedding=[0.98, 0.01, 0.0],
        title="Civil infrastructure tender",
        summary="Public infrastructure civil works execution",
    )
    tender["scraped_info"]["end_date"] = (now + timedelta(days=10)).replace(tzinfo=None)
    await tenders.insert_one(tender)
    await _link_candidate(fake_db, company_id="cmp-naive", tender_id="naive-tender", bid_id="GEM/2026/B/3501")

    result = await service.get_company_matches(
        company_id="cmp-naive",
        owner_user_id="user-naive",
        q=None,
        time_period="latest",
        sort="best_match",
        min_score=0.0,
        page=1,
        limit=10,
    )

    assert result["total"] == 1
    assert result["items"][0]["tender"]["bid_id"] == "GEM/2026/B/3501"


@pytest.mark.asyncio
async def test_high_vector_similarity_without_meaningful_match_is_not_qualified(fake_db):
    service = MatchService(fake_db)
    companies = fake_db.get_collection("company_profiles")
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)

    await companies.insert_one(
        {
            "_id": "profile-ai",
            "company_id": "cmp-ai",
            "owner_user_id": "user-ai",
            "name": "AI Automation Co",
            "interest_tags": ["AI"],
            "metadata": {
                "summary": "AI automation NLP and predictive analytics",
                "domains": ["Artificial Intelligence"],
                "technologies": ["Machine Learning"],
                "capabilities": ["Predictive Analytics"],
            },
            "summary_embedding": [1.0, 0.0, 0.0],
            "created_at": now,
            "updated_at": now,
        }
    )

    good_tender = _tender_doc(
        tender_id="ai-tender",
        bid_id="GEM/2026/B/4001",
        embedding=[1.0, 0.0, 0.0],
        title="AI automation platform",
        summary="Artificial intelligence and machine learning analytics platform",
    )
    good_tender["metadata"].update(
        {
            "domains": ["Artificial Intelligence"],
            "required_technologies": ["Machine Learning"],
            "summary": "Artificial intelligence and machine learning analytics platform",
        }
    )
    weak_tender = _tender_doc(
        tender_id="weak-tender",
        bid_id="GEM/2026/B/4002",
        embedding=[1.0, 0.0, 0.0],
        title="Office furniture procurement",
        summary="Chairs, desks, and filing cabinets",
    )
    weak_tender["metadata"].update(
        {
            "domains": ["Furniture"],
            "required_technologies": ["Office Chairs"],
            "summary": "Chairs, desks, and filing cabinets",
        }
    )
    await tenders.insert_one(good_tender)
    await tenders.insert_one(weak_tender)
    await _link_candidate(fake_db, company_id="cmp-ai", tender_id="ai-tender", bid_id="GEM/2026/B/4001")
    await _link_candidate(fake_db, company_id="cmp-ai", tender_id="weak-tender", bid_id="GEM/2026/B/4002")

    result = await service.get_company_matches(
        company_id="cmp-ai",
        owner_user_id="user-ai",
        q=None,
        time_period="latest",
        sort="best_match",
        min_score=0.35,
        page=1,
        limit=10,
    )

    bid_ids = [item["tender"]["bid_id"] for item in result["items"]]
    assert "GEM/2026/B/4001" in bid_ids
    assert "GEM/2026/B/4002" not in bid_ids
