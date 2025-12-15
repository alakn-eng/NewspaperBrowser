"""
Retrieval context models: Rebuildable search index.

These models represent the retrieval infrastructure (segments, embeddings)
that can be dropped and rebuilt without affecting browse data.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Segment(BaseModel):
    """A text segment with embedding for semantic search."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    page_id: UUID
    segment_index: int
    segment_text: str
    segment_hash: str
    segmenter_version: str = "v0_fixed_chars_800_100"
    metadata: Optional[dict] = None
    embedding: Optional[List[float]] = None  # Vector embedding
    created_at: datetime


class SegmentCreate(BaseModel):
    """Data required to create a segment."""

    page_id: UUID
    segment_index: int
    segment_text: str
    segment_hash: str
    segmenter_version: str = "v0_fixed_chars_800_100"
    metadata: Optional[dict] = None
    embedding: Optional[List[float]] = None


class IngestJob(BaseModel):
    """A job tracking the ingestion of an issue."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    idempotency_key: str
    issue_id: Optional[UUID] = None
    status: str = "pending"  # pending, processing, completed, failed
    progress: dict = Field(
        default_factory=lambda: {
            "pages_total": 0,
            "pages_processed": 0,
            "pages_succeeded": 0,
            "pages_failed": 0,
            "current_stage": "initializing",
            "errors": [],
        }
    )
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IngestJobCreate(BaseModel):
    """Data required to create an ingest job."""

    idempotency_key: str
    status: str = "pending"


class IngestJobUpdate(BaseModel):
    """Data for updating an ingest job."""

    issue_id: Optional[UUID] = None
    status: Optional[str] = None
    progress: Optional[dict] = None
    error_message: Optional[str] = None
