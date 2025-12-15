"""
Browse API routes for newspaper issues.

Read-only endpoints for browsing issues. Does not touch retrieval tables.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import (
    get_issue_repository,
    get_newspaper_repository,
    get_page_repository,
)
from app.repositories.issues import IssueRepository
from app.repositories.newspapers import NewspaperRepository
from app.repositories.pages import PageRepository
from app.models.api.responses import (
    IssueResponse,
    IssueDetailResponse,
    PaginatedIssuesResponse,
    NewspaperResponse,
    PageResponse,
)


router = APIRouter(prefix="/api/issues", tags=["issues"])


@router.get("", response_model=PaginatedIssuesResponse)
def list_issues(
    limit: int = Query(default=50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    newspaper_id: Optional[UUID] = Query(default=None, description="Filter by newspaper ID"),
    issue_repo: IssueRepository = Depends(get_issue_repository),
):
    """
    List issues with pagination.

    Query Parameters:
    - limit: Number of results (1-100, default 50)
    - offset: Number to skip for pagination
    - newspaper_id: Optional filter by newspaper

    Returns paginated list of issues ordered by date descending.
    """
    if newspaper_id:
        # Filter by newspaper
        issues = issue_repo.list_by_newspaper(
            newspaper_id=newspaper_id,
            limit=limit + 1,  # Fetch one extra to check if there are more
            offset=offset,
            order_desc=True,
        )
    else:
        # Get all issues
        issues = issue_repo.list_all(limit=limit + 1, offset=offset)

    # Check if there are more results
    has_more = len(issues) > limit
    items = issues[:limit]  # Return only requested limit

    # Count total (approximation for now - could be optimized with COUNT query)
    total = offset + len(items) + (1 if has_more else 0)

    return PaginatedIssuesResponse(
        items=[IssueResponse.model_validate(issue) for issue in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )


@router.get("/{issue_id}", response_model=IssueDetailResponse)
def get_issue_detail(
    issue_id: UUID,
    issue_repo: IssueRepository = Depends(get_issue_repository),
    newspaper_repo: NewspaperRepository = Depends(get_newspaper_repository),
    page_repo: PageRepository = Depends(get_page_repository),
):
    """
    Get detailed issue information.

    Includes:
    - Issue metadata
    - Newspaper information
    - All pages for this issue

    This endpoint only queries browse tables (newspapers, issues, pages).
    No retrieval tables are touched.
    """
    # Get issue
    issue = issue_repo.get_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Get newspaper
    newspaper = newspaper_repo.get_by_id(issue.newspaper_id)
    if not newspaper:
        raise HTTPException(
            status_code=500, detail="Associated newspaper not found"
        )

    # Get pages for this issue
    pages = page_repo.list_by_issue(issue_id, order_by_page_number=True)

    return IssueDetailResponse(
        **issue.model_dump(),
        newspaper=NewspaperResponse.model_validate(newspaper),
        pages=[PageResponse.model_validate(page) for page in pages],
    )
