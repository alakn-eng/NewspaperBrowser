"""
Issue repository for managing newspaper issues.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID
from supabase import Client

from app.models.db.browse import Issue, IssueCreate
from app.repositories.base import BaseRepository


class IssueRepository(BaseRepository[Issue]):
    """Repository for issue CRUD operations."""

    def __init__(self, supabase: Client):
        """Initialize issue repository."""
        super().__init__(supabase, "issues", Issue)

    def create_or_get(
        self,
        newspaper_id: UUID,
        issue_date: date,
        num_pages: int = 0,
        source_type: str = "upload",
        source_external_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Issue:
        """
        Create new issue or get existing one.

        Uses UNIQUE constraint (newspaper_id, issue_date) for idempotency.
        If issue already exists, returns existing issue without error.

        Args:
            newspaper_id: Parent newspaper UUID
            issue_date: Publication date
            num_pages: Number of pages in issue
            source_type: Source of the issue (upload, loc_batch, etc.)
            source_external_id: External ID if from third-party source
            metadata: Additional metadata (JSONB)

        Returns:
            Issue instance (existing or newly created)
        """
        # Try to find existing issue
        existing = self.get_by_newspaper_and_date(newspaper_id, issue_date)
        if existing:
            return existing

        # Create new issue
        new_issue = IssueCreate(
            newspaper_id=newspaper_id,
            issue_date=issue_date,
            num_pages=num_pages,
            source_type=source_type,
            source_external_id=source_external_id,
            metadata=metadata,
        )

        # Use upsert to handle race conditions
        return self._execute_upsert(
            data=new_issue.model_dump(exclude_none=True),
            on_conflict="newspaper_id,issue_date",
        )

    def get_by_newspaper_and_date(
        self, newspaper_id: UUID, issue_date: date
    ) -> Optional[Issue]:
        """
        Get issue by newspaper ID and date.

        Args:
            newspaper_id: Parent newspaper UUID
            issue_date: Publication date

        Returns:
            Issue instance or None if not found
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("newspaper_id", str(newspaper_id))
            .eq("issue_date", str(issue_date))
            .maybe_single()
            .execute()
        )

        if response.data:
            return Issue(**response.data)
        return None

    def list_by_newspaper(
        self,
        newspaper_id: UUID,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ) -> List[Issue]:
        """
        List issues for a newspaper, ordered by date.

        Args:
            newspaper_id: Parent newspaper UUID
            limit: Maximum number of results
            offset: Number of records to skip
            order_desc: If True, newest first; if False, oldest first

        Returns:
            List of issues
        """
        query = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("newspaper_id", str(newspaper_id))
            .limit(limit)
            .offset(offset)
        )

        if order_desc:
            query = query.order("issue_date", desc=True)
        else:
            query = query.order("issue_date", desc=False)

        response = query.execute()
        return [Issue(**row) for row in response.data]

    def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        newspaper_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[Issue]:
        """
        List issues within a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            newspaper_id: Optional filter by newspaper
            limit: Maximum number of results

        Returns:
            List of issues
        """
        query = (
            self.supabase.table(self.table_name)
            .select("*")
            .gte("issue_date", str(start_date))
            .lte("issue_date", str(end_date))
            .order("issue_date", desc=True)
            .limit(limit)
        )

        if newspaper_id:
            query = query.eq("newspaper_id", str(newspaper_id))

        response = query.execute()
        return [Issue(**row) for row in response.data]
