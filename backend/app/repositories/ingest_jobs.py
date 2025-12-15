"""
Ingest job repository for tracking async ingestion operations.
"""

from typing import Optional, List
from uuid import UUID
from supabase import Client

from app.models.db.retrieval import IngestJob, IngestJobCreate, IngestJobUpdate
from app.repositories.base import BaseRepository


class IngestJobRepository(BaseRepository[IngestJob]):
    """Repository for ingest job CRUD operations."""

    def __init__(self, supabase: Client):
        """Initialize ingest job repository."""
        super().__init__(supabase, "ingest_jobs", IngestJob)

    def get_by_key(self, idempotency_key: str) -> Optional[IngestJob]:
        """
        Get ingest job by idempotency key.

        Args:
            idempotency_key: Unique idempotency key

        Returns:
            IngestJob instance or None if not found
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("idempotency_key", idempotency_key)
            .maybe_single()
            .execute()
        )

        if response.data:
            return IngestJob(**response.data)
        return None

    def create_with_key(self, idempotency_key: str, status: str = "pending") -> IngestJob:
        """
        Create a new ingest job with idempotency key.

        Args:
            idempotency_key: Unique idempotency key
            status: Initial status (default: pending)

        Returns:
            Created IngestJob instance
        """
        new_job = IngestJobCreate(
            idempotency_key=idempotency_key,
            status=status,
        )
        return self.create(new_job)

    def update_job(
        self,
        job_id: UUID,
        issue_id: Optional[UUID] = None,
        status: Optional[str] = None,
        progress: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> IngestJob:
        """
        Update ingest job fields.

        Args:
            job_id: Job UUID
            issue_id: Issue UUID (once created)
            status: Job status (pending, processing, completed, failed)
            progress: Progress tracking object
            error_message: Error message if failed

        Returns:
            Updated IngestJob instance
        """
        update_data = {}

        if issue_id is not None:
            update_data["issue_id"] = str(issue_id)
        if status is not None:
            update_data["status"] = status
        if progress is not None:
            update_data["progress"] = progress
        if error_message is not None:
            update_data["error_message"] = error_message

        return self.update(job_id, update_data)

    def increment_progress(
        self,
        job_id: UUID,
        pages_processed: int,
        pages_total: int,
        current_stage: str = "processing",
        error: Optional[str] = None,
    ) -> IngestJob:
        """
        Increment job progress.

        Args:
            job_id: Job UUID
            pages_processed: Number of pages processed so far
            pages_total: Total pages in job
            current_stage: Current processing stage
            error: Error message to append (if any)

        Returns:
            Updated IngestJob instance
        """
        # Get current job to update progress
        job = self.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update progress object
        progress = job.progress or {
            "pages_total": pages_total,
            "pages_processed": 0,
            "pages_succeeded": 0,
            "pages_failed": 0,
            "current_stage": "initializing",
            "errors": [],
        }

        progress["pages_processed"] = pages_processed
        progress["pages_total"] = pages_total
        progress["current_stage"] = current_stage

        if error:
            progress["pages_failed"] = progress.get("pages_failed", 0) + 1
            errors = progress.get("errors", [])
            errors.append(error)
            # Keep only last 10 errors to avoid bloat
            progress["errors"] = errors[-10:]
        else:
            progress["pages_succeeded"] = progress.get("pages_succeeded", 0) + 1

        return self.update_job(job_id, progress=progress)

    def list_by_status(
        self, status: str, limit: int = 100, offset: int = 0
    ) -> List[IngestJob]:
        """
        List jobs by status.

        Args:
            status: Job status to filter by
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of jobs with matching status
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("status", status)
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        return [IngestJob(**row) for row in response.data]

    def list_recent(self, limit: int = 50) -> List[IngestJob]:
        """
        List most recent jobs.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent jobs ordered by created_at desc
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return [IngestJob(**row) for row in response.data]
