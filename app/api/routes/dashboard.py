"""
Dashboard API routes.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user, get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    company_id: str | None = None,
    overview_range: str = "7d",
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = DashboardService(db)
    return await service.get_stats(
        owner_user_id=current_user["id"],
        company_id=company_id,
        overview_range=overview_range,
    )


@router.get("/report", response_model=Dict[str, Any])
async def get_dashboard_report(
    range: str = "12m",
    company_id: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = DashboardService(db)
    return await service.get_report(owner_user_id=current_user["id"], company_id=company_id, range_key=range)


@router.get("/activity", response_model=List[Dict[str, Any]])
async def get_recent_activity(
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = DashboardService(db)
    return await service.get_activity(limit=limit)


@router.get("/queue", response_model=List[Dict[str, Any]])
async def get_processing_queue(
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = DashboardService(db)
    return await service.get_queue(limit=limit)
