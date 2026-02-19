"""
Pydantic models for search requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    domains: List[str] = Field(default_factory=list)
    required_certifications: List[str] = Field(default_factory=list)
    min_value: Optional[str] = None
    max_value: Optional[str] = None


class SearchRequest(BaseModel):
    company_id: str
    query: Optional[str] = None
    filters: Optional[SearchFilters] = None
    limit: int = 20


class SearchResult(BaseModel):
    tender_id: str
    bid_id: str
    score: float
    match_reasons: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    company_id: str
    results: List[SearchResult]
    total: int
    generated_at: datetime
    query: Optional[str] = None
    filters_applied: Optional[Dict[str, Any]] = None
