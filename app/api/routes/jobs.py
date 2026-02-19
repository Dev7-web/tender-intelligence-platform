"""
Job API routes.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user, get_db
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=Dict[str, Any])
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    job_type: str | None = None,
    status: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = JobService(db)
    return await service.list_jobs(skip=skip, limit=limit, job_type=job_type, status=status)


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job(
    job_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = JobService(db)
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/scrape/trigger", response_model=Dict[str, Any])
async def trigger_scrape(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = JobService(db)
    return await service.trigger_scrape()


@router.post("/process/trigger", response_model=Dict[str, Any])
async def trigger_process(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = JobService(db)
    return await service.trigger_process()


@router.get("/scheduler/status", response_model=Dict[str, Any])
async def scheduler_status(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = JobService(db)
    return service.scheduler_status()
