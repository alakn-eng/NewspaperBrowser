"""
Page repository for managing newspaper pages with OCR data.
"""

from typing import Optional, List
from uuid import UUID
from supabase import Client

from app.models.db.browse import Page, PageCreate, PageOcrUpdate
from app.repositories.base import BaseRepository


class PageRepository(BaseRepository[Page]):
    """Repository for page CRUD operations."""

    def __init__(self, supabase: Client):
        """Initialize page repository."""
        super().__init__(supabase, "pages", Page)

    def get_by_issue_and_number(
        self, issue_id: UUID, page_number: int
    ) -> Optional[Page]:
        """
        Get page by issue ID and page number.

        Args:
            issue_id: Parent issue UUID
            page_number: Page number within issue

        Returns:
            Page instance or None if not found
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("issue_id", str(issue_id))
            .eq("page_number", page_number)
            .maybe_single()
            .execute()
        )

        if response.data:
            return Page(**response.data)
        return None

    def create_or_get(
        self,
        issue_id: UUID,
        page_number: int,
        image_path: str,
        ingestion_status: str = "pending",
    ) -> Page:
        """
        Create new page or get existing one.

        Uses UNIQUE constraint (issue_id, page_number) for idempotency.

        Args:
            issue_id: Parent issue UUID
            page_number: Page number within issue
            image_path: Path to image in storage
            ingestion_status: Current ingestion status

        Returns:
            Page instance (existing or newly created)
        """
        # Try to find existing page
        existing = self.get_by_issue_and_number(issue_id, page_number)
        if existing:
            return existing

        # Create new page
        new_page = PageCreate(
            issue_id=issue_id,
            page_number=page_number,
            image_path=image_path,
            ingestion_status=ingestion_status,
        )

        # Use upsert to handle race conditions
        return self._execute_upsert(
            data=new_page.model_dump(exclude_none=True),
            on_conflict="issue_id,page_number",
        )

    def update_ocr(
        self,
        page_id: UUID,
        ocr_text: str,
        ocr_confidence: Optional[float] = None,
        ocr_provider: Optional[str] = None,
        ocr_version: Optional[str] = None,
        ocr_meta: Optional[dict] = None,
        ingestion_status: str = "ocr_completed",
    ) -> Page:
        """
        Update page with OCR results.

        Args:
            page_id: Page UUID
            ocr_text: Extracted text from OCR
            ocr_confidence: OCR confidence score (0-1)
            ocr_provider: OCR provider name
            ocr_version: OCR provider version
            ocr_meta: Additional OCR metadata
            ingestion_status: Status to set (default: ocr_completed)

        Returns:
            Updated page instance
        """
        update_data = {
            "ocr_text": ocr_text,
            "ocr_confidence": ocr_confidence,
            "ocr_provider": ocr_provider,
            "ocr_version": ocr_version,
            "ocr_meta": ocr_meta,
            "ingestion_status": ingestion_status,
        }

        return self.update(page_id, update_data)

    def update_status(self, page_id: UUID, status: str) -> Page:
        """
        Update page ingestion status.

        Args:
            page_id: Page UUID
            status: New status (pending, ocr_pending, ocr_completed, ocr_failed, indexed)

        Returns:
            Updated page instance
        """
        return self.update(page_id, {"ingestion_status": status})

    def list_by_issue(
        self, issue_id: UUID, order_by_page_number: bool = True
    ) -> List[Page]:
        """
        List all pages for an issue.

        Args:
            issue_id: Parent issue UUID
            order_by_page_number: If True, order by page number ascending

        Returns:
            List of pages
        """
        query = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("issue_id", str(issue_id))
        )

        if order_by_page_number:
            query = query.order("page_number", desc=False)

        response = query.execute()
        return [Page(**row) for row in response.data]

    def list_by_status(
        self, status: str, limit: int = 100, offset: int = 0
    ) -> List[Page]:
        """
        List pages by ingestion status.

        Useful for finding pages that need processing.

        Args:
            status: Ingestion status to filter by
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of pages with matching status
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("ingestion_status", status)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        return [Page(**row) for row in response.data]
