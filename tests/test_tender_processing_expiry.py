from datetime import datetime, timedelta, timezone

import pytest

from app.services.tender_service import TenderService


def _pending_tender(bid_id: str, end_date):
    now = datetime.now(timezone.utc)
    return {
        "_id": bid_id,
        "bid_id": bid_id,
        "pdf_url": "https://example.com/tender.pdf",
        "expired": False,
        "scraped_at": now,
        "created_at": now,
        "updated_at": now,
        "status": {
            "scrape_status": "completed",
            "pdf_downloaded": False,
            "llm_processed": False,
            "embedding_generated": False,
            "last_error": None,
        },
        "scraped_info": {"end_date": end_date},
    }


@pytest.mark.asyncio
async def test_process_tender_skips_expired_without_llm_or_download(fake_db, monkeypatch):
    service = TenderService(fake_db)
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)
    await tenders.insert_one(_pending_tender("expired-bid", now - timedelta(days=1)))

    async def fail_download(*_args, **_kwargs):
        raise AssertionError("download should not be called for expired tenders")

    monkeypatch.setattr("app.services.tender_service.download_with_retry", fail_download)
    monkeypatch.setattr(service.pdf_extractor, "extract_text", lambda _path: (_ for _ in ()).throw(AssertionError("PDF extraction should not run")))
    monkeypatch.setattr(service, "_get_llm", lambda: (_ for _ in ()).throw(AssertionError("LLM should not run")))
    monkeypatch.setattr(service.embedder, "embed", lambda _text: (_ for _ in ()).throw(AssertionError("embedding should not run")))

    assert await service.process_tender("expired-bid") is False
    assert (await tenders.find_one({"bid_id": "expired-bid"}))["expired"] is True


@pytest.mark.asyncio
async def test_process_tender_skips_missing_deadline_without_llm_or_download(fake_db, monkeypatch):
    service = TenderService(fake_db)
    tenders = fake_db.get_collection("tenders")
    await tenders.insert_one(_pending_tender("missing-deadline-bid", None))

    async def fail_download(*_args, **_kwargs):
        raise AssertionError("download should not be called without a deadline")

    monkeypatch.setattr("app.services.tender_service.download_with_retry", fail_download)
    monkeypatch.setattr(service, "_get_llm", lambda: (_ for _ in ()).throw(AssertionError("LLM should not run")))

    assert await service.process_tender("missing-deadline-bid") is False
    assert (await tenders.find_one({"bid_id": "missing-deadline-bid"}))["expired"] is False


@pytest.mark.asyncio
async def test_process_pending_tenders_selects_only_active_pending_tenders(fake_db, monkeypatch):
    service = TenderService(fake_db)
    tenders = fake_db.get_collection("tenders")
    now = datetime.now(timezone.utc)

    await tenders.insert_one(_pending_tender("active-bid", now + timedelta(days=2)))
    await tenders.insert_one(_pending_tender("expired-bid", now - timedelta(days=2)))
    await tenders.insert_one(_pending_tender("missing-deadline-bid", None))

    processed_bid_ids = []

    async def fake_process(bid_id: str):
        processed_bid_ids.append(bid_id)
        return True

    monkeypatch.setattr(service, "process_tender", fake_process)

    assert await service.process_pending_tenders(limit=10) == 1
    assert processed_bid_ids == ["active-bid"]
    assert (await tenders.find_one({"bid_id": "expired-bid"}))["expired"] is True
