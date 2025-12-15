"""
Browse context models: Canonical newspaper data.

These models represent the core browsing entities and should never
depend on retrieval tables (segments, embeddings).
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Newspaper(BaseModel):
    """A newspaper publication."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None
    source_type: str = "upload"
    created_at: datetime


class Issue(BaseModel):
    """A specific dated issue of a newspaper."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    newspaper_id: UUID
    issue_date: date
    num_pages: int = 0
    source_type: str = "upload"
    source_external_id: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime


class Page(BaseModel):
    """A single page from an issue with OCR data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    issue_id: UUID
    page_number: int
    image_path: str

    # OCR data (canonical storage)
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_provider: Optional[str] = None
    ocr_version: Optional[str] = None
    ocr_meta: Optional[dict] = None

    ingestion_status: str = "pending"
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Create models (for inserts)
# ============================================================================


class NewspaperCreate(BaseModel):
    """Data required to create a newspaper."""

    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None
    source_type: str = "upload"


class IssueCreate(BaseModel):
    """Data required to create an issue."""

    newspaper_id: UUID
    issue_date: date
    num_pages: int = 0
    source_type: str = "upload"
    source_external_id: Optional[str] = None
    metadata: Optional[dict] = None


class PageCreate(BaseModel):
    """Data required to create a page."""

    issue_id: UUID
    page_number: int
    image_path: str
    ingestion_status: str = "pending"


class PageOcrUpdate(BaseModel):
    """OCR data to update on a page."""

    ocr_text: str
    ocr_confidence: Optional[float] = None
    ocr_provider: Optional[str] = None
    ocr_version: Optional[str] = None
    ocr_meta: Optional[dict] = None
    ingestion_status: str = "ocr_completed"
