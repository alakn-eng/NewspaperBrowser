"""
Unit tests for database models.

Tests that Pydantic models can be instantiated and validated correctly.
"""

from datetime import date, datetime
from uuid import uuid4

import pytest

from app.models.db.browse import (
    Newspaper,
    NewspaperCreate,
    Issue,
    IssueCreate,
    Page,
    PageCreate,
    PageOcrUpdate,
)
from app.models.db.retrieval import (
    Segment,
    SegmentCreate,
    IngestJob,
    IngestJobCreate,
    IngestJobUpdate,
)


class TestBrowseModels:
    """Test browse context models."""

    def test_newspaper_model(self):
        """Test Newspaper model instantiation."""
        newspaper = Newspaper(
            id=uuid4(),
            name="The Daily Test",
            city="San Francisco",
            country="USA",
            start_year=1920,
            end_year=1950,
            description="A test newspaper",
            source_type="upload",
            created_at=datetime.now(),
        )
        assert newspaper.name == "The Daily Test"
        assert newspaper.city == "San Francisco"

    def test_newspaper_create(self):
        """Test NewspaperCreate model."""
        create_data = NewspaperCreate(
            name="Test Paper",
            city="New York",
            country="USA",
        )
        assert create_data.name == "Test Paper"
        assert create_data.source_type == "upload"  # Default

    def test_issue_model(self):
        """Test Issue model instantiation."""
        issue = Issue(
            id=uuid4(),
            newspaper_id=uuid4(),
            issue_date=date(1925, 1, 15),
            num_pages=8,
            source_type="upload",
            created_at=datetime.now(),
        )
        assert issue.issue_date == date(1925, 1, 15)
        assert issue.num_pages == 8

    def test_issue_create(self):
        """Test IssueCreate model."""
        newspaper_id = uuid4()
        create_data = IssueCreate(
            newspaper_id=newspaper_id,
            issue_date=date(1925, 1, 15),
            num_pages=8,
        )
        assert create_data.newspaper_id == newspaper_id
        assert create_data.num_pages == 8

    def test_page_model(self):
        """Test Page model instantiation."""
        page = Page(
            id=uuid4(),
            issue_id=uuid4(),
            page_number=1,
            image_path="/test/path/page1.png",
            ocr_text="Sample OCR text",
            ocr_confidence=0.95,
            ocr_provider="test_ocr_v1",
            ingestion_status="ocr_completed",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert page.page_number == 1
        assert page.ocr_text == "Sample OCR text"
        assert page.ocr_confidence == 0.95

    def test_page_create(self):
        """Test PageCreate model."""
        create_data = PageCreate(
            issue_id=uuid4(),
            page_number=1,
            image_path="/test/path/page1.png",
        )
        assert create_data.page_number == 1
        assert create_data.ingestion_status == "pending"  # Default

    def test_page_ocr_update(self):
        """Test PageOcrUpdate model."""
        update_data = PageOcrUpdate(
            ocr_text="Updated OCR text",
            ocr_confidence=0.92,
            ocr_provider="test_ocr_v2",
        )
        assert update_data.ocr_text == "Updated OCR text"
        assert update_data.ingestion_status == "ocr_completed"  # Default


class TestRetrievalModels:
    """Test retrieval context models."""

    def test_segment_model(self):
        """Test Segment model instantiation."""
        segment = Segment(
            id=uuid4(),
            page_id=uuid4(),
            segment_index=0,
            segment_text="This is a test segment",
            segment_hash="abc123hash",
            segmenter_version="v0_fixed_chars_800_100",
            embedding=[0.1, 0.2, 0.3],  # Simplified for test
            created_at=datetime.now(),
        )
        assert segment.segment_index == 0
        assert segment.segment_text == "This is a test segment"
        assert segment.segment_hash == "abc123hash"

    def test_segment_create(self):
        """Test SegmentCreate model."""
        create_data = SegmentCreate(
            page_id=uuid4(),
            segment_index=0,
            segment_text="Test segment",
            segment_hash="hash123",
        )
        assert create_data.segment_index == 0
        assert create_data.segmenter_version == "v0_fixed_chars_800_100"  # Default

    def test_ingest_job_model(self):
        """Test IngestJob model instantiation."""
        job = IngestJob(
            id=uuid4(),
            idempotency_key="test-key-123",
            status="processing",
            progress={
                "pages_total": 10,
                "pages_processed": 5,
                "pages_succeeded": 4,
                "pages_failed": 1,
                "current_stage": "ocr",
                "errors": ["Error on page 3"],
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert job.idempotency_key == "test-key-123"
        assert job.status == "processing"
        assert job.progress["pages_total"] == 10

    def test_ingest_job_create(self):
        """Test IngestJobCreate model."""
        create_data = IngestJobCreate(idempotency_key="key-456")
        assert create_data.idempotency_key == "key-456"
        assert create_data.status == "pending"  # Default

    def test_ingest_job_update(self):
        """Test IngestJobUpdate model."""
        update_data = IngestJobUpdate(
            status="completed",
            progress={"pages_total": 10, "pages_processed": 10},
        )
        assert update_data.status == "completed"
        assert update_data.progress["pages_processed"] == 10


class TestModelValidation:
    """Test model validation and edge cases."""

    def test_newspaper_minimal_fields(self):
        """Test Newspaper with only required fields."""
        newspaper = Newspaper(
            id=uuid4(),
            name="Minimal Paper",
            created_at=datetime.now(),
        )
        assert newspaper.name == "Minimal Paper"
        assert newspaper.city is None
        assert newspaper.description is None

    def test_page_without_ocr(self):
        """Test Page before OCR processing."""
        page = Page(
            id=uuid4(),
            issue_id=uuid4(),
            page_number=1,
            image_path="/path/to/page.png",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert page.ocr_text is None
        assert page.ocr_confidence is None
        assert page.ingestion_status == "pending"

    def test_segment_without_embedding(self):
        """Test Segment before embedding generation."""
        segment = Segment(
            id=uuid4(),
            page_id=uuid4(),
            segment_index=0,
            segment_text="Text without embedding",
            segment_hash="hash789",
            created_at=datetime.now(),
        )
        assert segment.embedding is None
