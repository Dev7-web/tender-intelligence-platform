"""
Company profile and onboarding API routes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user, get_db
from app.services.company_service import CompanyService
from app.services.match_service import MatchService

router = APIRouter(prefix="/companies", tags=["companies"])


class CreateCompanyRequest(BaseModel):
    name: str = Field(min_length=1)
    company_url: str = Field(min_length=1)
    experience_years: int = Field(ge=0, le=100)


class InterestsRequest(BaseModel):
    interest_tags: List[str] = Field(default_factory=list)


@router.get("/", response_model=Dict[str, Any])
async def list_companies(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    return await service.list_companies(
        skip=skip,
        limit=limit,
        status=status,
        search=search,
        owner_user_id=current_user["id"],
    )


@router.post("", response_model=Dict[str, Any])
async def create_company_profile(
    payload: CreateCompanyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    try:
        profile = await service.create_company(
            owner_user_id=current_user["id"],
            name=payload.name,
            company_url=payload.company_url,
            experience_years=payload.experience_years,
        )
        return {"company_id": profile["company_id"], "status": "pending", "company": profile}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{company_id}/scrape-website", response_model=Dict[str, Any])
async def scrape_company_website(
    company_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    try:
        result = await service.scrape_website(company_id=company_id, owner_user_id=current_user["id"])
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{company_id}/documents", response_model=Dict[str, Any])
async def upload_company_documents(
    company_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    try:
        return await service.upload_documents(company_id=company_id, owner_user_id=current_user["id"], files=files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{company_id}/documents/{file_hash}", response_model=Dict[str, Any])
async def delete_company_document(
    company_id: str,
    file_hash: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    try:
        deleted = await service.remove_document(company_id=company_id, owner_user_id=current_user["id"], file_hash=file_hash)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"deleted": True}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{company_id}/interests", response_model=Dict[str, Any])
async def set_company_interests(
    company_id: str,
    payload: InterestsRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    try:
        company = await service.set_interests(
            company_id=company_id,
            owner_user_id=current_user["id"],
            interest_tags=payload.interest_tags,
        )
        return {"company_id": company_id, "interest_tags": company.get("interest_tags", [])}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{company_id}/process", response_model=Dict[str, Any])
async def process_company(
    company_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    try:
        return await service.start_processing(company_id=company_id, owner_user_id=current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{company_id}", response_model=Dict[str, Any])
async def get_company_profile(
    company_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    profile = await service.get_profile(company_id, owner_user_id=current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return profile


@router.get("/{company_id}/search-history", response_model=List[Dict[str, Any]])
async def get_company_search_history(
    company_id: str,
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    profile = await service.get_profile(company_id, owner_user_id=current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return await service.get_search_history(company_id=company_id, limit=limit)


@router.get("/{company_id}/matches", response_model=Dict[str, Any])
async def get_company_matches(
    company_id: str,
    q: Optional[str] = None,
    time_period: str = "latest",
    sort: str = "best_match",
    min_score: float = 0.8,
    page: int = 1,
    limit: int = 10,
    state: Optional[str] = None,
    city: Optional[str] = None,
    certification: Optional[str] = None,
    portal: Optional[str] = None,
    procurement: Optional[str] = None,
    organisation: Optional[str] = None,
    amount_range: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = MatchService(db)
    try:
        return await service.get_company_matches(
            company_id=company_id,
            owner_user_id=current_user["id"],
            q=q,
            time_period=time_period,
            sort=sort,
            min_score=min_score,
            page=page,
            limit=limit,
            state=state,
            city=city,
            certification=certification,
            portal=portal,
            procurement=procurement,
            organisation=organisation,
            amount_range=amount_range,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{company_id}/my-list", response_model=Dict[str, Any])
async def get_my_list(
    company_id: str,
    tab: str = "saved",
    page: int = 1,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    profile = await db.get_collection("company_profiles").find_one(
        {"company_id": company_id, "owner_user_id": current_user["id"]}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")

    service = MatchService(db)
    return await service.get_my_list(company_id=company_id, tab=tab, page=page, limit=limit)


@router.delete("/{company_id}", response_model=Dict[str, Any])
async def delete_company_profile(
    company_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = CompanyService(db)
    deleted = await service.delete_profile(company_id, owner_user_id=current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return {"deleted": True}


@router.post("/upload", response_model=Dict[str, Any])
async def legacy_upload_company_profile(
    files: List[UploadFile] = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = CompanyService(db)
    return await service.create_profile(files=files)
