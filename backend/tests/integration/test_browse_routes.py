"""
Integration tests for browse API routes.

Tests that browse endpoints work with mocked repositories.
For true integration tests with real Supabase, set up test database credentials.
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
import os

# Set test environment variables before importing app
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["ADMIN_API_KEY"] = "test-admin-key"

from app.main import app
from app.models.db.browse import Newspaper, Issue, Page
from app.dependencies import (
    get_issue_repository,
    get_newspaper_repository,
    get_page_repository,
)


# Create test client
client = TestClient(app)


@pytest.fixture
def mock_data():
    """Create mock data for tests."""
    newspaper_id = uuid4()
    issue_id = uuid4()
    page_id = uuid4()

    newspaper = Newspaper(
        id=newspaper_id,
        name="Test Daily News",
        city="San Francisco",
        country="USA",
        start_year=1920,
        end_year=1950,
        description="A test newspaper",
        source_type="upload",
        created_at="2025-01-01T00:00:00Z",
    )

    issue = Issue(
        id=issue_id,
        newspaper_id=newspaper_id,
        issue_date=date(1925, 1, 15),
        num_pages=4,
        source_type="upload",
        created_at="2025-01-01T00:00:00Z",
    )

    page = Page(
        id=page_id,
        issue_id=issue_id,
        page_number=1,
        image_path="/test/path/page1.png",
        ocr_text="Test OCR text from page 1",
        ocr_confidence=0.95,
        ocr_provider="test_ocr",
        ingestion_status="ocr_completed",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )

    return {
        "newspaper": newspaper,
        "issue": issue,
        "page": page,
    }


@pytest.fixture
def mock_repos(mock_data):
    """Create mock repositories with configured responses."""
    # Create mock repositories
    mock_issue_repo = Mock()
    mock_newspaper_repo = Mock()
    mock_page_repo = Mock()

    # Configure mock responses
    mock_issue_repo.list_all.return_value = [mock_data["issue"]]
    mock_issue_repo.list_by_newspaper.return_value = [mock_data["issue"]]
    mock_issue_repo.get_by_id.return_value = mock_data["issue"]

    mock_newspaper_repo.get_by_id.return_value = mock_data["newspaper"]

    mock_page_repo.list_by_issue.return_value = [mock_data["page"]]
    mock_page_repo.get_by_id.return_value = mock_data["page"]

    # Override FastAPI dependencies
    app.dependency_overrides[get_issue_repository] = lambda: mock_issue_repo
    app.dependency_overrides[get_newspaper_repository] = lambda: mock_newspaper_repo
    app.dependency_overrides[get_page_repository] = lambda: mock_page_repo

    yield {
        "issue_repo": mock_issue_repo,
        "newspaper_repo": mock_newspaper_repo,
        "page_repo": mock_page_repo,
    }

    # Clear overrides after test
    app.dependency_overrides.clear()


class TestIssuesEndpoints:
    """Test /api/issues endpoints."""

    def test_list_issues(self, mock_repos, mock_data):
        """Test GET /api/issues returns paginated list."""
        response = client.get("/api/issues")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        assert len(data["items"]) == 1
        assert data["items"][0]["newspaper_id"] == str(mock_data["issue"].newspaper_id)

    def test_list_issues_with_pagination(self, mock_repos):
        """Test GET /api/issues with pagination parameters."""
        response = client.get("/api/issues?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_list_issues_with_newspaper_filter(self, mock_repos, mock_data):
        """Test GET /api/issues filtered by newspaper_id."""
        newspaper_id = mock_data["newspaper"].id

        response = client.get(f"/api/issues?newspaper_id={newspaper_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify the filter was used
        mock_repos["issue_repo"].list_by_newspaper.assert_called_once()

    def test_get_issue_detail(self, mock_repos, mock_data):
        """Test GET /api/issues/{id} returns issue with newspaper and pages."""
        issue_id = mock_data["issue"].id

        response = client.get(f"/api/issues/{issue_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify issue data
        assert data["id"] == str(issue_id)
        assert "newspaper" in data
        assert "pages" in data

        # Verify newspaper included
        assert data["newspaper"]["name"] == "Test Daily News"

        # Verify pages included
        assert len(data["pages"]) == 1
        assert data["pages"][0]["page_number"] == 1

    def test_get_issue_not_found(self):
        """Test GET /api/issues/{id} returns 404 for non-existent issue."""
        fake_id = uuid4()

        # Override issue repo to return None
        mock_issue_repo = Mock()
        mock_issue_repo.get_by_id.return_value = None

        # Also override other repos (though they won't be called if issue is not found)
        mock_newspaper_repo = Mock()
        mock_page_repo = Mock()

        app.dependency_overrides[get_issue_repository] = lambda: mock_issue_repo
        app.dependency_overrides[get_newspaper_repository] = lambda: mock_newspaper_repo
        app.dependency_overrides[get_page_repository] = lambda: mock_page_repo

        response = client.get(f"/api/issues/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        app.dependency_overrides.clear()


class TestPagesEndpoints:
    """Test /api/pages endpoints."""

    def test_get_page_detail(self, mock_repos, mock_data):
        """Test GET /api/pages/{id} returns page details."""
        page_id = mock_data["page"].id

        response = client.get(f"/api/pages/{page_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(page_id)
        assert data["page_number"] == 1
        assert data["ocr_text"] == "Test OCR text from page 1"
        assert data["ocr_confidence"] == 0.95
        assert data["ingestion_status"] == "ocr_completed"

    def test_get_page_not_found(self):
        """Test GET /api/pages/{id} returns 404 for non-existent page."""
        fake_id = uuid4()

        # Override to return None
        mock_repo = Mock()
        mock_repo.get_by_id.return_value = None
        app.dependency_overrides[get_page_repository] = lambda: mock_repo

        response = client.get(f"/api/pages/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self):
        """Test GET / returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "Time Browser API"
        assert data["status"] == "running"
        assert "version" in data

    def test_health_check(self):
        """Test GET /health returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"


class TestBrowseIndependence:
    """
    Acceptance test: Verify browse endpoints work without retrieval tables.

    This test verifies the architectural boundary between browse and retrieval contexts.
    """

    def test_browse_works_without_segments(self, mock_repos, mock_data):
        """
        Browse endpoints should work even if segments table is empty.

        This is a key architectural requirement: browse context is independent
        of retrieval context.
        """
        issue_id = mock_data["issue"].id

        # Get issue detail (should work without any retrieval data)
        response = client.get(f"/api/issues/{issue_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify all browse data is present
        assert "id" in data
        assert "newspaper" in data
        assert "pages" in data

        # Verify no retrieval data is exposed
        assert "segments" not in data
        assert "embeddings" not in data
        assert "chunks" not in data
