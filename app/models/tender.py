"""
Pydantic models for tenders.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TenderScrapedInfo(BaseModel):
    items: Optional[str] = None
    quantity: Optional[int] = None
    department: Optional[str] = None
    department_address: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    bid_type: Optional[str] = None
    bid_value_range: Optional[str] = None


class TenderEligibility(BaseModel):
    min_turnover: Optional[str] = None
    min_experience_years: Optional[int] = None
    required_registrations: List[str] = Field(default_factory=list)


class TenderMetadata(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    sector: Optional[str] = None
    domains: List[str] = Field(default_factory=list)
    required_certifications: List[str] = Field(default_factory=list)
    required_technologies: List[str] = Field(default_factory=list)
    required_experience_years: Optional[int] = None
    estimated_value: Optional[str] = None
    eligibility_criteria: Optional[TenderEligibility] = None
    location: Optional[str] = None
    delivery_period: Optional[str] = None
    emd_amount: Optional[str] = None
    summary: Optional[str] = None


class TenderStatus(BaseModel):
    scrape_status: str = "pending"
    pdf_downloaded: bool = False
    llm_processed: bool = False
    embedding_generated: bool = False
    last_error: Optional[str] = None


class TenderBase(BaseModel):
    bid_id: str
    ra_no: Optional[str] = None
    gem_url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_local_path: Optional[str] = None
    scraped_info: Optional[TenderScrapedInfo] = None
    metadata: Optional[TenderMetadata] = None
    summary_embedding: Optional[List[float]] = None
    status: Optional[TenderStatus] = None
    scraped_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    expired: bool = False


class TenderCreate(TenderBase):
    pass


class TenderResponse(TenderBase):
    id: Optional[str] = None
