from datetime import datetime, timedelta, timezone

import pytest

from app.jobs import scrape_job
from app.scraper.gem_scraper import ScrapeResult
from app.services.tender_service import TenderService


class FakeGemScraper:
    instances = []

    def __init__(self):
        self.scrape_kwargs = None
        self.scrape_calls = []
        FakeGemScraper.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def scrape_bids(self, **kwargs):
        self.scrape_kwargs = kwargs
        self.scrape_calls.append(kwargs)
        now = datetime.now(timezone.utc)
        return ScrapeResult(
            bids=[
                {
                    "bid_id": "GEM/2026/B/NEW001",
                    "pdf_url": "https://example.com/new.pdf",
                    "gem_url": "https://example.com/new.pdf",
                    "items": "Latest tender",
                    "start_date": now,
                    "end_date": now + timedelta(days=5),
                }
            ],
            pages_scraped=1,
            known_tenders_skipped=1,
            sort_applied=True,
        )


@pytest.mark.asyncio
async def test_scrape_job_passes_known_ids_and_processes_only_new_scraped_bids(fake_db, monkeypatch):
    FakeGemScraper.instances = []
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)
    await tenders.insert_one(
        {
            "_id": "existing",
            "bid_id": "GEM/2026/B/KNOWN001",
            "expired": False,
            "scraped_info": {"end_date": now + timedelta(days=5)},
            "status": {"llm_processed": True},
        }
    )

    processed_bid_ids = []

    async def fake_process(self, bid_id):
        processed_bid_ids.append(bid_id)
        return True

    async def fake_broadcast(*_args, **_kwargs):
        return None

    monkeypatch.setattr(scrape_job, "get_database", lambda: fake_db)
    monkeypatch.setattr(scrape_job, "GemScraper", FakeGemScraper)
    monkeypatch.setattr(TenderService, "process_tender", fake_process)
    monkeypatch.setattr(scrape_job, "_broadcast_progress", fake_broadcast)

    await scrape_job.run_scrape_job()

    scraper = FakeGemScraper.instances[0]
    assert "GEM/2026/B/KNOWN001" in scraper.scrape_kwargs["known_bid_ids"]
    assert scraper.scrape_kwargs["stop_after_known"] == scrape_job.settings.SCRAPE_STOP_AFTER_KNOWN_BIDS
    assert processed_bid_ids == ["GEM/2026/B/NEW001"]

    log = await fake_db.get_collection("scrape_logs").find_one({"job_type": "scrape"})
    assert log["status"] == "completed"
    assert log["stats"]["pages_scraped"] == 1
    assert log["stats"]["known_tenders_skipped"] == 1
    assert log["stats"]["sort_applied"] is True
    assert log["stats"]["new_tenders"] == 1
    assert log["stats"]["llm_processed"] == 1


@pytest.mark.asyncio
async def test_company_scrape_uses_keywords_and_links_existing_tender(fake_db, monkeypatch):
    FakeGemScraper.instances = []
    now = datetime.now(timezone.utc)
    companies = fake_db.get_collection("company_profiles")
    tenders = fake_db.get_collection("tenders")

    await companies.insert_one(
        {
            "_id": "company-profile",
            "company_id": "company-1",
            "owner_user_id": "user-1",
            "name": "AI Automation Co",
            "tender_search_keywords": ["ai automation"],
            "metadata": {
                "summary": "AI automation and predictive analytics",
                "domains": ["Artificial Intelligence"],
                "technologies": ["Machine Learning"],
                "capabilities": ["Predictive Analytics"],
            },
            "summary_embedding": [1.0, 0.0, 0.0],
            "created_at": now,
            "updated_at": now,
        }
    )
    await tenders.insert_one(
        {
            "_id": "existing-tender",
            "bid_id": "GEM/2026/B/NEW001",
            "is_active": True,
            "expired": False,
            "pdf_url": "https://example.com/new.pdf",
            "scraped_at": now,
            "created_at": now,
            "updated_at": now,
            "scraped_info": {
                "items": "AI automation platform",
                "start_date": now - timedelta(days=1),
                "end_date": now + timedelta(days=5),
            },
            "status": {"llm_processed": True, "pdf_downloaded": True, "embedding_generated": True},
            "metadata": {
                "title": "AI automation platform",
                "summary": "Artificial intelligence and machine learning analytics platform",
                "domains": ["Artificial Intelligence"],
                "required_technologies": ["Machine Learning"],
            },
            "summary_embedding": [1.0, 0.0, 0.0],
        }
    )

    processed_bid_ids = []

    async def fake_process(self, bid_id):
        processed_bid_ids.append(bid_id)
        return True

    async def fake_broadcast(*_args, **_kwargs):
        return None

    def fake_score(self, **_kwargs):
        return {
            "raw_score": 0.82,
            "match_score": 0.82,
            "match_reasons": ["Domain match: artificial intelligence"],
            "qualified": True,
            "relevance_status": "accepted",
            "relevance_score": 1.0,
            "relevance_reasons": ["Matched core profile terms: artificial intelligence"],
            "matched_core_terms": ["artificial intelligence"],
        }

    monkeypatch.setattr(scrape_job, "get_database", lambda: fake_db)
    monkeypatch.setattr(scrape_job, "GemScraper", FakeGemScraper)
    monkeypatch.setattr(TenderService, "process_tender", fake_process)
    monkeypatch.setattr(scrape_job.MatchService, "score_tender_for_profile", fake_score)
    monkeypatch.setattr(scrape_job, "_broadcast_progress", fake_broadcast)

    await scrape_job.run_company_scrape_job(company_id="company-1", owner_user_id="user-1")

    scraper = FakeGemScraper.instances[0]
    assert scraper.scrape_calls[0]["search_query"] == "ai automation"
    assert processed_bid_ids == []
    assert await tenders.count_documents({"bid_id": "GEM/2026/B/NEW001"}) == 1

    candidate = await fake_db.get_collection("company_tender_candidates").find_one(
        {"company_id": "company-1", "bid_id": "GEM/2026/B/NEW001"}
    )
    assert candidate["tender_id"] == "existing-tender"
    assert candidate["qualified"] is True
    assert candidate["relevance_status"] == "accepted"
    assert candidate["matched_core_terms"] == ["artificial intelligence"]
    assert candidate["search_keyword"] == "ai automation"

    log = await fake_db.get_collection("scrape_logs").find_one({"job_type": "company_scrape"})
    assert log["status"] == "completed"
    assert log["company_id"] == "company-1"
    assert log["keywords"] == ["ai automation"]
    assert log["stats"]["candidates_linked"] == 1
    assert log["stats"]["qualified"] == 1
    assert log["stats"]["accepted_relevant"] == 1
    assert log["stats"]["rejected_irrelevant"] == 0


@pytest.mark.asyncio
async def test_company_scrape_rejects_irrelevant_keyword_results(fake_db, monkeypatch):
    FakeGemScraper.instances = []
    now = datetime.now(timezone.utc)
    companies = fake_db.get_collection("company_profiles")
    tenders = fake_db.get_collection("tenders")

    await companies.insert_one(
        {
            "_id": "company-profile",
            "company_id": "company-ai",
            "owner_user_id": "user-ai",
            "name": "AI Automation Co",
            "tender_search_keywords": ["machine learning"],
            "metadata": {
                "summary": "AI automation, NLP, machine learning, cloud, and analytics systems",
                "domains": ["Artificial Intelligence"],
                "technologies": ["Machine Learning"],
                "capabilities": ["Natural Language Processing", "Predictive Analytics"],
            },
            "summary_embedding": [1.0, 0.0, 0.0],
            "created_at": now,
            "updated_at": now,
        }
    )
    await tenders.insert_one(
        {
            "_id": "construction-tender",
            "bid_id": "GEM/2026/B/NEW001",
            "is_active": True,
            "expired": False,
            "pdf_url": "https://example.com/new.pdf",
            "scraped_at": now,
            "created_at": now,
            "updated_at": now,
            "scraped_info": {
                "items": "Pre engineered bunker civil construction",
                "start_date": now - timedelta(days=1),
                "end_date": now + timedelta(days=5),
            },
            "status": {"llm_processed": True, "pdf_downloaded": True, "embedding_generated": True},
            "metadata": {
                "title": "Pre engineered bunker",
                "summary": "Civil construction and structural building work",
                "domains": ["Construction"],
                "required_technologies": ["RCC"],
            },
            "summary_embedding": [0.2, 0.8, 0.0],
        }
    )

    async def fake_broadcast(*_args, **_kwargs):
        return None

    def fake_score(self, **_kwargs):
        raise AssertionError("irrelevant tenders must be rejected before scoring")

    monkeypatch.setattr(scrape_job, "get_database", lambda: fake_db)
    monkeypatch.setattr(scrape_job, "GemScraper", FakeGemScraper)
    monkeypatch.setattr(scrape_job.MatchService, "score_tender_for_profile", fake_score)
    monkeypatch.setattr(scrape_job, "_broadcast_progress", fake_broadcast)

    await scrape_job.run_company_scrape_job(company_id="company-ai", owner_user_id="user-ai")

    candidate = await fake_db.get_collection("company_tender_candidates").find_one(
        {"company_id": "company-ai", "bid_id": "GEM/2026/B/NEW001"}
    )
    assert candidate["qualified"] is False
    assert candidate["relevance_status"] == "rejected"
    assert candidate["matched_core_terms"] == []
    assert "No core profile terms found" in candidate["relevance_reasons"][0]

    log = await fake_db.get_collection("scrape_logs").find_one({"job_type": "company_scrape"})
    assert log["status"] == "completed"
    assert log["stats"]["candidates_linked"] == 0
    assert log["stats"]["accepted_relevant"] == 0
    assert log["stats"]["rejected_irrelevant"] == 1
    assert log["stats"]["rejection_samples"]


@pytest.mark.asyncio
async def test_company_scrape_records_search_apply_failure_without_generic_scrape(fake_db, monkeypatch):
    class FailingSearchScraper:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        async def scrape_bids(self, **_kwargs):
            raise RuntimeError("Unable to apply GeM search query: machine learning")

    now = datetime.now(timezone.utc)
    await fake_db.get_collection("company_profiles").insert_one(
        {
            "_id": "company-profile",
            "company_id": "company-ai",
            "owner_user_id": "user-ai",
            "name": "AI Automation Co",
            "tender_search_keywords": ["machine learning"],
            "metadata": {
                "summary": "AI automation and machine learning",
                "capabilities": ["Machine Learning"],
            },
            "created_at": now,
            "updated_at": now,
        }
    )

    async def fake_broadcast(*_args, **_kwargs):
        return None

    monkeypatch.setattr(scrape_job, "get_database", lambda: fake_db)
    monkeypatch.setattr(scrape_job, "GemScraper", FailingSearchScraper)
    monkeypatch.setattr(scrape_job, "_broadcast_progress", fake_broadcast)

    await scrape_job.run_company_scrape_job(company_id="company-ai", owner_user_id="user-ai")

    log = await fake_db.get_collection("scrape_logs").find_one({"job_type": "company_scrape"})
    assert log["status"] == "completed"
    assert log["stats"]["errors"] == 1
    assert log["stats"]["tenders_found"] == 0
    assert await fake_db.get_collection("company_tender_candidates").count_documents({}) == 0
