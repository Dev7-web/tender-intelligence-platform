import io
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.services.company_service import CompanyService
from app.services.match_service import MatchService


class DummyUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self._buffer = io.BytesIO(content)
        self.content_type = content_type

    async def read(self, size: int = -1):
        return self._buffer.read(size)


class DummyLLM:
    def extract_company(self, _text: str):
        return {
            "company_name": "Demo InfraTech",
            "domains": ["Infrastructure", "Energy"],
            "technologies": ["Solar PV"],
            "certifications": ["ISO 9001"],
            "capabilities": ["Road construction", "Solar installation"],
            "government_experience": True,
            "summary": "Infrastructure and energy delivery partner",
        }


@pytest.mark.asyncio
async def test_integration_company_upload_process_and_match(fake_db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "PROFILE_UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "AUTO_COMPANY_TENDER_SCRAPE", False)

    company_service = CompanyService(fake_db)
    match_service = MatchService(fake_db)

    company = await company_service.create_company(
        owner_user_id="user-1",
        name="Demo InfraTech",
        company_url="https://example.com",
        experience_years=8,
    )
    company_id = company["company_id"]

    upload_file = DummyUploadFile(
        filename="profile.txt",
        content=b"We deliver infrastructure and solar projects across government departments.",
    )

    await company_service.upload_documents(company_id=company_id, owner_user_id="user-1", files=[upload_file])
    await company_service.set_interests(company_id=company_id, owner_user_id="user-1", interest_tags=["Energy"])

    async def fake_broadcast(**_kwargs):
        return None

    monkeypatch.setattr(company_service, "_broadcast_progress", fake_broadcast)
    monkeypatch.setattr(company_service, "_get_llm", lambda: DummyLLM())
    monkeypatch.setattr(company_service.embedder, "embed", lambda _text: [0.2, 0.2, 0.2])

    await company_service._process_company_profile(company_id=company_id, owner_user_id="user-1", job_id="job-1")

    tenders = fake_db.get_collection("tenders")
    await tenders.insert_one(
        {
            "_id": "tender-1",
            "bid_id": "GEM/2026/B/200001",
            "is_active": True,
            "expired": False,
            "scraped_at": datetime.now(timezone.utc),
            "status": {"llm_processed": True},
            "summary_embedding": [0.2, 0.2, 0.2],
            "scraped_info": {
                "department": "Public Works",
                "start_date": datetime.now(timezone.utc) - timedelta(days=2),
                "end_date": datetime.now(timezone.utc) + timedelta(days=15),
                "bid_value_range": "₹25 L",
                "items": "Road and solar works",
            },
            "metadata": {
                "title": "Road and solar works",
                "department": "Public Works",
                "domains": ["Infrastructure", "Energy"],
                "required_technologies": ["Solar PV"],
                "required_certifications": ["ISO 9001"],
                "summary": "Infrastructure and solar delivery project",
                "location": "Jaipur",
            },
        }
    )
    now = datetime.now(timezone.utc)
    await fake_db.get_collection("company_tender_candidates").insert_one(
        {
            "company_id": company_id,
            "tender_id": "tender-1",
            "bid_id": "GEM/2026/B/200001",
            "search_keyword": "solar",
            "raw_score": 0.8,
            "match_score": 0.8,
            "match_reasons": ["Domain match: energy"],
            "qualified": True,
            "relevance_status": "accepted",
            "relevance_score": 1.0,
            "relevance_reasons": ["Matched core profile terms: solar"],
            "matched_core_terms": ["solar"],
            "discovered_at": now,
            "last_scored_at": now,
            "updated_at": now,
        }
    )

    matches = await match_service.get_company_matches(
        company_id=company_id,
        owner_user_id="user-1",
        q=None,
        time_period="latest",
        sort="best_match",
        min_score=0.1,
        page=1,
        limit=10,
    )

    assert matches["total"] >= 1
    assert matches["items"][0]["tender"]["bid_id"] == "GEM/2026/B/200001"
    assert matches["items"][0]["match"]["score"] >= 0.1
