from datetime import datetime, timedelta, timezone

import pytest

from app.jobs import scrape_job
from app.scraper.gem_scraper import ScrapeResult
from app.services.tender_service import TenderService


class FakeGemScraper:
    instances = []

    def __init__(self):
        self.scrape_kwargs = None
        FakeGemScraper.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def scrape_bids(self, **kwargs):
        self.scrape_kwargs = kwargs
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
