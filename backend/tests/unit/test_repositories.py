"""
Unit tests for repository layer.

Tests all repository CRUD operations using mocked Supabase client.
"""

from datetime import date, datetime
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch

import pytest

from app.models.db.browse import (
    Newspaper,
    NewspaperCreate,
    Issue,
    IssueCreate,
    Page,
    PageCreate,
)
from app.models.db.retrieval import IngestJob, IngestJobCreate
from app.repositories.newspapers import NewspaperRepository
from app.repositories.issues import IssueRepository
from app.repositories.pages import PageRepository
from app.repositories.ingest_jobs import IngestJobRepository


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    return Mock()


@pytest.fixture
def mock_table_response():
    """Helper to create mock table responses."""
    def _create_response(data=None, count=None):
        response = Mock()
        response.data = data
        response.count = count
        return response
    return _create_response


class TestNewspaperRepository:
    """Test newspaper repository operations."""

    def test_get_or_create_existing_newspaper(self, mock_supabase, mock_table_response):
        """Test get_or_create returns existing newspaper."""
        # Setup
        newspaper_id = uuid4()
        existing_data = {
            "id": str(newspaper_id),
            "name": "The Daily Test",
            "city": "San Francisco",
            "country": "USA",
            "start_year": 1920,
            "end_year": 1950,
            "description": "Test newspaper",
            "source_type": "upload",
            "created_at": datetime.now().isoformat(),
        }

        # Mock the query chain
        mock_query = Mock()
        mock_query.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(existing_data)
        )
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = NewspaperRepository(mock_supabase)
        result = repo.get_or_create("The Daily Test")

        # Assert
        assert isinstance(result, Newspaper)
        assert result.name == "The Daily Test"
        assert result.city == "San Francisco"

    def test_get_or_create_new_newspaper(self, mock_supabase, mock_table_response):
        """Test get_or_create creates new newspaper when not found."""
        # Setup - first query returns None (not found)
        newspaper_id = uuid4()
        created_data = {
            "id": str(newspaper_id),
            "name": "New Paper",
            "city": None,
            "country": None,
            "start_year": None,
            "end_year": None,
            "description": None,
            "source_type": "upload",
            "created_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        # First call (select) returns None
        mock_query.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(None)
        )
        # Second call (insert) returns created newspaper
        mock_query.insert.return_value.execute.return_value = mock_table_response([created_data])
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = NewspaperRepository(mock_supabase)
        result = repo.get_or_create("New Paper")

        # Assert
        assert isinstance(result, Newspaper)
        assert result.name == "New Paper"

    def test_get_by_name(self, mock_supabase, mock_table_response):
        """Test get_by_name retrieves newspaper."""
        # Setup
        newspaper_id = uuid4()
        newspaper_data = {
            "id": str(newspaper_id),
            "name": "Test Paper",
            "city": "New York",
            "country": "USA",
            "start_year": None,
            "end_year": None,
            "description": None,
            "source_type": "upload",
            "created_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(newspaper_data)
        )
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = NewspaperRepository(mock_supabase)
        result = repo.get_by_name("Test Paper")

        # Assert
        assert result is not None
        assert result.name == "Test Paper"


class TestIssueRepository:
    """Test issue repository operations."""

    def test_create_or_get_new_issue(self, mock_supabase, mock_table_response):
        """Test create_or_get creates new issue."""
        # Setup
        newspaper_id = uuid4()
        issue_id = uuid4()
        issue_date = date(1925, 1, 15)

        # First query (select) returns None - issue doesn't exist
        # Second call (upsert) returns created issue
        created_data = {
            "id": str(issue_id),
            "newspaper_id": str(newspaper_id),
            "issue_date": str(issue_date),
            "num_pages": 8,
            "source_type": "upload",
            "source_external_id": None,
            "metadata": None,
            "created_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(None)
        )
        mock_query.upsert.return_value.execute.return_value = mock_table_response([created_data])
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = IssueRepository(mock_supabase)
        result = repo.create_or_get(
            newspaper_id=newspaper_id,
            issue_date=issue_date,
            num_pages=8,
        )

        # Assert
        assert isinstance(result, Issue)
        assert result.newspaper_id == newspaper_id
        assert result.num_pages == 8

    def test_get_by_newspaper_and_date(self, mock_supabase, mock_table_response):
        """Test get_by_newspaper_and_date retrieves issue."""
        # Setup
        newspaper_id = uuid4()
        issue_id = uuid4()
        issue_date = date(1925, 1, 15)

        issue_data = {
            "id": str(issue_id),
            "newspaper_id": str(newspaper_id),
            "issue_date": str(issue_date),
            "num_pages": 8,
            "source_type": "upload",
            "source_external_id": None,
            "metadata": None,
            "created_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(issue_data)
        )
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = IssueRepository(mock_supabase)
        result = repo.get_by_newspaper_and_date(newspaper_id, issue_date)

        # Assert
        assert result is not None
        assert result.issue_date == issue_date


class TestPageRepository:
    """Test page repository operations."""

    def test_get_by_issue_and_number(self, mock_supabase, mock_table_response):
        """Test get_by_issue_and_number retrieves page."""
        # Setup
        issue_id = uuid4()
        page_id = uuid4()

        page_data = {
            "id": str(page_id),
            "issue_id": str(issue_id),
            "page_number": 1,
            "image_path": "/test/path/page1.png",
            "ocr_text": None,
            "ocr_confidence": None,
            "ocr_provider": None,
            "ocr_version": None,
            "ocr_meta": None,
            "ingestion_status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(page_data)
        )
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = PageRepository(mock_supabase)
        result = repo.get_by_issue_and_number(issue_id, 1)

        # Assert
        assert result is not None
        assert result.page_number == 1

    def test_create_or_get_new_page(self, mock_supabase, mock_table_response):
        """Test create_or_get creates new page."""
        # Setup
        issue_id = uuid4()
        page_id = uuid4()

        created_data = {
            "id": str(page_id),
            "issue_id": str(issue_id),
            "page_number": 1,
            "image_path": "/test/path/page1.png",
            "ocr_text": None,
            "ocr_confidence": None,
            "ocr_provider": None,
            "ocr_version": None,
            "ocr_meta": None,
            "ingestion_status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        # First call (select) returns None
        mock_query.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(None)
        )
        # Second call (upsert) returns created page
        mock_query.upsert.return_value.execute.return_value = mock_table_response([created_data])
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = PageRepository(mock_supabase)
        result = repo.create_or_get(
            issue_id=issue_id,
            page_number=1,
            image_path="/test/path/page1.png",
        )

        # Assert
        assert isinstance(result, Page)
        assert result.page_number == 1

    def test_update_ocr(self, mock_supabase, mock_table_response):
        """Test update_ocr updates page with OCR results."""
        # Setup
        page_id = uuid4()
        issue_id = uuid4()

        updated_data = {
            "id": str(page_id),
            "issue_id": str(issue_id),
            "page_number": 1,
            "image_path": "/test/path/page1.png",
            "ocr_text": "Sample OCR text",
            "ocr_confidence": 0.95,
            "ocr_provider": "test_ocr",
            "ocr_version": "v1",
            "ocr_meta": None,
            "ingestion_status": "ocr_completed",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.update.return_value.eq.return_value.execute.return_value = mock_table_response([updated_data])
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = PageRepository(mock_supabase)
        result = repo.update_ocr(
            page_id=page_id,
            ocr_text="Sample OCR text",
            ocr_confidence=0.95,
            ocr_provider="test_ocr",
            ocr_version="v1",
        )

        # Assert
        assert result.ocr_text == "Sample OCR text"
        assert result.ocr_confidence == 0.95
        assert result.ingestion_status == "ocr_completed"


class TestIngestJobRepository:
    """Test ingest job repository operations."""

    def test_get_by_key(self, mock_supabase, mock_table_response):
        """Test get_by_key retrieves job by idempotency key."""
        # Setup
        job_id = uuid4()
        job_data = {
            "id": str(job_id),
            "idempotency_key": "test-key-123",
            "issue_id": None,
            "status": "pending",
            "progress": {
                "pages_total": 0,
                "pages_processed": 0,
                "pages_succeeded": 0,
                "pages_failed": 0,
                "current_stage": "initializing",
                "errors": [],
            },
            "error_message": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(job_data)
        )
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = IngestJobRepository(mock_supabase)
        result = repo.get_by_key("test-key-123")

        # Assert
        assert result is not None
        assert result.idempotency_key == "test-key-123"

    def test_create_with_key(self, mock_supabase, mock_table_response):
        """Test create_with_key creates new job."""
        # Setup
        job_id = uuid4()
        created_data = {
            "id": str(job_id),
            "idempotency_key": "new-key-456",
            "issue_id": None,
            "status": "pending",
            "progress": {
                "pages_total": 0,
                "pages_processed": 0,
                "pages_succeeded": 0,
                "pages_failed": 0,
                "current_stage": "initializing",
                "errors": [],
            },
            "error_message": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.insert.return_value.execute.return_value = mock_table_response([created_data])
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = IngestJobRepository(mock_supabase)
        result = repo.create_with_key("new-key-456")

        # Assert
        assert isinstance(result, IngestJob)
        assert result.idempotency_key == "new-key-456"
        assert result.status == "pending"

    def test_update_job(self, mock_supabase, mock_table_response):
        """Test update_job updates job fields."""
        # Setup
        job_id = uuid4()
        issue_id = uuid4()

        updated_data = {
            "id": str(job_id),
            "idempotency_key": "test-key-123",
            "issue_id": str(issue_id),
            "status": "processing",
            "progress": {
                "pages_total": 10,
                "pages_processed": 5,
                "pages_succeeded": 5,
                "pages_failed": 0,
                "current_stage": "ocr",
                "errors": [],
            },
            "error_message": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.update.return_value.eq.return_value.execute.return_value = mock_table_response([updated_data])
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = IngestJobRepository(mock_supabase)
        result = repo.update_job(
            job_id=job_id,
            issue_id=issue_id,
            status="processing",
        )

        # Assert
        assert result.issue_id == issue_id
        assert result.status == "processing"

    def test_increment_progress(self, mock_supabase, mock_table_response):
        """Test increment_progress updates job progress."""
        # Setup
        job_id = uuid4()

        # Mock get_by_id to return existing job
        existing_job_data = {
            "id": str(job_id),
            "idempotency_key": "test-key-123",
            "issue_id": None,
            "status": "processing",
            "progress": {
                "pages_total": 10,
                "pages_processed": 4,
                "pages_succeeded": 4,
                "pages_failed": 0,
                "current_stage": "ocr",
                "errors": [],
            },
            "error_message": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        updated_job_data = {
            **existing_job_data,
            "progress": {
                "pages_total": 10,
                "pages_processed": 5,
                "pages_succeeded": 5,
                "pages_failed": 0,
                "current_stage": "ocr",
                "errors": [],
            },
        }

        mock_query = Mock()
        # First call (get_by_id via select)
        mock_query.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(existing_job_data)
        )
        # Second call (update)
        mock_query.update.return_value.eq.return_value.execute.return_value = mock_table_response([updated_job_data])
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = IngestJobRepository(mock_supabase)
        result = repo.increment_progress(
            job_id=job_id,
            pages_processed=5,
            pages_total=10,
            current_stage="ocr",
        )

        # Assert
        assert result.progress["pages_processed"] == 5
        assert result.progress["pages_succeeded"] == 5


class TestBaseRepository:
    """Test base repository operations."""

    def test_get_by_id(self, mock_supabase, mock_table_response):
        """Test get_by_id retrieves record."""
        # Setup
        newspaper_id = uuid4()
        newspaper_data = {
            "id": str(newspaper_id),
            "name": "Test Paper",
            "city": None,
            "country": None,
            "start_year": None,
            "end_year": None,
            "description": None,
            "source_type": "upload",
            "created_at": datetime.now().isoformat(),
        }

        mock_query = Mock()
        mock_query.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_table_response(newspaper_data)
        )
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = NewspaperRepository(mock_supabase)
        result = repo.get_by_id(newspaper_id)

        # Assert
        assert result is not None
        assert result.id == newspaper_id

    def test_list_all(self, mock_supabase, mock_table_response):
        """Test list_all returns multiple records."""
        # Setup
        newspapers_data = [
            {
                "id": str(uuid4()),
                "name": "Paper 1",
                "city": None,
                "country": None,
                "start_year": None,
                "end_year": None,
                "description": None,
                "source_type": "upload",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid4()),
                "name": "Paper 2",
                "city": None,
                "country": None,
                "start_year": None,
                "end_year": None,
                "description": None,
                "source_type": "upload",
                "created_at": datetime.now().isoformat(),
            },
        ]

        mock_query = Mock()
        mock_query.select.return_value.limit.return_value.offset.return_value.execute.return_value = (
            mock_table_response(newspapers_data)
        )
        mock_supabase.table.return_value = mock_query

        # Execute
        repo = NewspaperRepository(mock_supabase)
        result = repo.list_all(limit=10, offset=0)

        # Assert
        assert len(result) == 2
        assert result[0].name == "Paper 1"
        assert result[1].name == "Paper 2"
