"""
API response models for browse endpoints.

These models define the shape of data returned from API endpoints.
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class NewspaperResponse(BaseModel):
    """Response model for newspaper data."""

    id: UUID
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None
    source_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    """Response model for page data."""

    id: UUID
    issue_id: UUID
    page_number: int
    image_path: str
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_provider: Optional[str] = None
    ingestion_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class IssueResponse(BaseModel):
    """Response model for issue data with optional page details."""

    id: UUID
    newspaper_id: UUID
    issue_date: date
    num_pages: int
    source_type: str
    source_external_id: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime

    # Optional: Include newspaper details
    newspaper: Optional[NewspaperResponse] = None

    # Optional: Include pages if requested
    pages: Optional[List[PageResponse]] = None

    class Config:
        from_attributes = True


class PaginatedIssuesResponse(BaseModel):
    """Paginated response for issues list."""

    items: List[IssueResponse]
    total: int
    limit: int
    offset: int
    has_more: bool = Field(
        ..., description="Whether there are more results available"
    )


class PaginatedPagesResponse(BaseModel):
    """Paginated response for pages list."""

    items: List[PageResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class IssueDetailResponse(IssueResponse):
    """
    Detailed issue response including newspaper info and pages.

    Extends IssueResponse with guaranteed newspaper and pages data.
    """

    newspaper: NewspaperResponse
    pages: List[PageResponse]
