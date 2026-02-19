"""
Pydantic models for company profiles.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UploadedFile(BaseModel):
    file_hash: str
    original_name: str
    local_path: str
    uploaded_at: datetime


class CompanyMetadata(BaseModel):
    company_name: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    past_clients: List[str] = Field(default_factory=list)
    government_experience: Optional[bool] = None
    years_in_business: Optional[int] = None
    employee_count: Optional[str] = None
    annual_turnover: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    registrations: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class CompanyStatus(BaseModel):
    processing_status: str = "pending"
    files_processed: int = 0
    total_files: int = 0
    last_error: Optional[str] = None


class CompanyProfile(BaseModel):
    company_id: str
    name: Optional[str] = None
    uploaded_files: List[UploadedFile] = Field(default_factory=list)
    metadata: Optional[CompanyMetadata] = None
    summary_embedding: Optional[List[float]] = None
    status: CompanyStatus = Field(default_factory=CompanyStatus)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_search_at: Optional[datetime] = None


class CompanyResponse(CompanyProfile):
    id: Optional[str] = None
