"""
Scrape and process jobs for GeM portal.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.config import settings
from app.database.mongodb import get_database
from app.scraper.gem_scraper import GemScraper
from app.services.tender_expiry import refresh_expired_flags, tender_inactive_reason
from app.services.tender_service import TenderService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def run_scrape_job() -> None:
    db = get_database()
    service = TenderService(db)
    job_id = str(uuid.uuid4())
    scrape_logs = db.get_collection("scrape_logs")

    log_entry = {
        "job_id": job_id,
        "job_type": "scrape",
        "started_at": utcnow(),
        "status": "running",
        "stats": {
            "pages_scraped": 0,
            "tenders_found": 0,
            "new_tenders": 0,
            "known_tenders_skipped": 0,
            "pdfs_downloaded": 0,
            "llm_processed": 0,
            "skipped_expired": 0,
            "skipped_missing_deadline": 0,
            "sort_applied": False,
            "errors": 0,
        },
        "errors": [],
    }
    await scrape_logs.insert_one(log_entry)
    await _broadcast_progress(
        job="SCRAPE_TENDERS",
        job_id=job_id,
        status="started",
        current=0,
        total=1,
        message="Scrape job started",
    )

    stats = log_entry["stats"]
    errors: List[Dict[str, Any]] = []

    try:
        known_bid_ids = await _load_known_bid_ids(service.repo.collection)
        async with GemScraper() as scraper:
            scrape_result = await scraper.scrape_bids(
                known_bid_ids=known_bid_ids,
                stop_after_known=settings.SCRAPE_STOP_AFTER_KNOWN_BIDS,
            )
            bids = scrape_result.bids
            stats["pages_scraped"] = scrape_result.pages_scraped
            stats["known_tenders_skipped"] = scrape_result.known_tenders_skipped
            stats["sort_applied"] = scrape_result.sort_applied
            stats["tenders_found"] = len(bids) + scrape_result.known_tenders_skipped

            total_bids = max(len(bids), 1)
            for index, bid in enumerate(bids, start=1):
                bid_id = bid.get("bid_id")
                try:
                    await service.create_or_update_from_scrape(bid)
                    stats["new_tenders"] += 1

                    tender = await service.repo.get_by_bid_id(bid_id) if bid_id else None
                    inactive_reason = tender_inactive_reason(tender or {})
                    if inactive_reason == "expired":
                        stats["skipped_expired"] += 1
                    elif inactive_reason == "missing_deadline":
                        stats["skipped_missing_deadline"] += 1
                    elif await service.process_tender(bid_id):
                        stats["pdfs_downloaded"] += 1
                        stats["llm_processed"] += 1
                    else:
                        tender = await service.repo.get_by_bid_id(bid_id) if bid_id else None
                        inactive_reason = tender_inactive_reason(tender or {})
                        if inactive_reason == "expired":
                            stats["skipped_expired"] += 1
                        elif inactive_reason == "missing_deadline":
                            stats["skipped_missing_deadline"] += 1
                        else:
                            stats["errors"] += 1
                            last_error = ((tender or {}).get("status") or {}).get("last_error") or "Tender processing failed"
                            errors.append(
                                {
                                    "bid_id": bid_id,
                                    "error": last_error,
                                    "timestamp": utcnow(),
                                }
                            )
                except Exception as exc:
                    stats["errors"] += 1
                    errors.append(
                        {
                            "bid_id": bid_id,
                            "error": str(exc),
                            "timestamp": utcnow(),
                        }
                    )

                await _broadcast_progress(
                    job="PROCESS_TENDERS",
                    job_id=job_id,
                    status="progress",
                    current=index,
                    total=total_bids,
                    message=f"Processed {index}/{total_bids} tenders",
                )

        # Mark any tenders whose deadline has passed as expired
        await refresh_expired_flags(service.repo.collection, utcnow())

        await scrape_logs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "completed_at": utcnow(),
                    "status": "completed",
                    "stats": stats,
                    "errors": errors,
                }
            },
        )
        await _broadcast_progress(
            job="PROCESS_TENDERS",
            job_id=job_id,
            status="completed",
            current=stats["llm_processed"],
            total=max(stats["tenders_found"], 1),
            message="Scrape and analysis completed",
        )
    except Exception as exc:
        import traceback

        error_msg = str(exc) or repr(exc) or type(exc).__name__
        error_detail = {
            "error": error_msg,
            "type": type(exc).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": utcnow(),
        }
        await scrape_logs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "completed_at": utcnow(),
                    "status": "failed",
                    "stats": stats,
                    "errors": errors + [error_detail],
                }
            },
        )
        await _broadcast_progress(
            job="PROCESS_TENDERS",
            job_id=job_id,
            status="failed",
            current=0,
            total=max(stats["tenders_found"], 1),
            message=error_msg,
        )
        logger.error("scrape.job_failed", error=error_msg, error_type=type(exc).__name__, exc_info=True)


def run_scrape_job_sync() -> None:
    asyncio.run(run_scrape_job())


async def _load_known_bid_ids(tenders_collection) -> set[str]:
    cursor = tenders_collection.find({}, {"bid_id": 1})
    return {doc.get("bid_id") async for doc in cursor if doc.get("bid_id")}


async def run_process_job() -> None:
    db = get_database()
    service = TenderService(db)
    job_id = str(uuid.uuid4())
    scrape_logs = db.get_collection("scrape_logs")
    log_entry = {
        "job_id": job_id,
        "job_type": "process",
        "started_at": utcnow(),
        "status": "running",
        "stats": {"processed": 0, "errors": 0},
        "errors": [],
    }
    await scrape_logs.insert_one(log_entry)
    await _broadcast_progress(
        job="PROCESS_TENDERS",
        job_id=job_id,
        status="started",
        current=0,
        total=settings.PROCESS_BATCH_LIMIT,
        message="Process job started",
    )

    try:
        processed = await service.process_pending_tenders(limit=settings.PROCESS_BATCH_LIMIT)
        stats = {"processed": processed, "errors": 0}
        await scrape_logs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "completed_at": utcnow(),
                    "status": "completed",
                    "stats": stats,
                    "errors": [],
                }
            },
        )
        await _broadcast_progress(
            job="PROCESS_TENDERS",
            job_id=job_id,
            status="completed",
            current=processed,
            total=max(processed, 1),
            message="Pending tender processing completed",
        )
        logger.info("process.job_completed", processed=processed)
    except Exception as exc:
        await scrape_logs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "completed_at": utcnow(),
                    "status": "failed",
                    "stats": {"processed": 0, "errors": 1},
                    "errors": [{"error": str(exc), "timestamp": utcnow()}],
                }
            },
        )
        await _broadcast_progress(
            job="PROCESS_TENDERS",
            job_id=job_id,
            status="failed",
            current=0,
            total=settings.PROCESS_BATCH_LIMIT,
            message=str(exc),
        )
        logger.info("process.job_failed", error=str(exc))


def run_process_job_sync() -> None:
    asyncio.run(run_process_job())


async def _broadcast_progress(
    job: str,
    job_id: str,
    status: str,
    current: int,
    total: int,
    message: str,
) -> None:
    try:
        from app.services.socket_manager import manager

        payload = {
            "type": "JOB_PROGRESS",
            "job": job,
            "job_id": job_id,
            "status": status,
            "progress": {
                "current": current,
                "total": total,
                "percent": round((current / total), 4) if total else 0,
            },
            "message": message,
            "ts": utcnow().isoformat(),
        }
        await manager.broadcast(payload)
    except Exception:
        return
