"""
Background job scheduler.
"""

from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.jobs.scrape_job import run_process_job, run_scrape_job
from app.utils.logger import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    if scheduler.running:
        return

    # Use async functions directly - APScheduler handles them properly
    scheduler.add_job(
        run_scrape_job,
        "interval",
        hours=settings.SCRAPE_INTERVAL_HOURS,
        id="scrape_job",
        replace_existing=True,
    )
    scheduler.add_job(
        run_process_job,
        "interval",
        minutes=settings.PROCESS_INTERVAL_MINUTES,
        id="process_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler.started")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped")
