"""
Dependency injection for FastAPI routes.

Provides shared instances of services, repositories, and clients.
"""

from functools import lru_cache
from supabase import create_client, Client

from app.config import settings
from app.repositories.newspapers import NewspaperRepository
from app.repositories.issues import IssueRepository
from app.repositories.pages import PageRepository
from app.repositories.ingest_jobs import IngestJobRepository


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client instance (cached).

    Returns:
        Supabase client configured with project credentials
    """
    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key,
    )


def get_newspaper_repository() -> NewspaperRepository:
    """
    Get newspaper repository instance.

    Returns:
        NewspaperRepository with Supabase client
    """
    supabase = get_supabase_client()
    return NewspaperRepository(supabase)


def get_issue_repository() -> IssueRepository:
    """
    Get issue repository instance.

    Returns:
        IssueRepository with Supabase client
    """
    supabase = get_supabase_client()
    return IssueRepository(supabase)


def get_page_repository() -> PageRepository:
    """
    Get page repository instance.

    Returns:
        PageRepository with Supabase client
    """
    supabase = get_supabase_client()
    return PageRepository(supabase)


def get_ingest_job_repository() -> IngestJobRepository:
    """
    Get ingest job repository instance.

    Returns:
        IngestJobRepository with Supabase client
    """
    supabase = get_supabase_client()
    return IngestJobRepository(supabase)
