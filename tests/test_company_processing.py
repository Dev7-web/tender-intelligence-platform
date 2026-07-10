import pytest

from app.config import settings
from app.services.company_service import CompanyService


class DummyLLM:
    def extract_company(self, _text: str):
        return {
            "company_name": "Demo InfraTech",
            "domains": ["Infrastructure"],
            "summary": "Demo summary",
        }


@pytest.mark.asyncio
async def test_company_processing_pipeline_updates_ready_status(fake_db, monkeypatch):
    monkeypatch.setattr(settings, "AUTO_COMPANY_TENDER_SCRAPE", False)
    service = CompanyService(fake_db)

    profile = {
        "company_id": "company-1",
        "owner_user_id": "user-1",
        "name": "Demo InfraTech",
        "company_url": "https://example.com",
        "experience_years": 8,
        "interest_tags": ["Infrastructure"],
        "website_scrape": {"extracted_text": "Infrastructure expertise"},
        "uploaded_files": [
            {
                "original_name": "profile.txt",
                "extract_status": "extracted",
                "extracted_text": "Road and energy projects",
            }
        ],
        "status": {
            "processing_status": "processing",
            "files_processed": 0,
            "total_files": 1,
            "last_error": None,
        },
    }

    updated_payload = {}

    async def fake_get_owned_profile(company_id: str, owner_user_id: str):
        assert company_id == "company-1"
        assert owner_user_id == "user-1"
        return profile

    async def fake_update(company_id: str, data):
        updated_payload.update(data)
        return True

    async def fake_broadcast(**_kwargs):
        return None

    monkeypatch.setattr(service, "_get_owned_profile", fake_get_owned_profile)
    monkeypatch.setattr(service.repo, "update", fake_update)
    monkeypatch.setattr(service, "_broadcast_progress", fake_broadcast)
    monkeypatch.setattr(service, "_get_llm", lambda: DummyLLM())
    monkeypatch.setattr(service.embedder, "embed", lambda _text: [0.1, 0.2, 0.3])

    await service._process_company_profile(company_id="company-1", owner_user_id="user-1", job_id="job-1")

    assert updated_payload["status"]["processing_status"] == "ready"
    assert updated_payload["metadata"]["company_name"] == "Demo InfraTech"
    assert updated_payload["summary_embedding"] == [0.1, 0.2, 0.3]
