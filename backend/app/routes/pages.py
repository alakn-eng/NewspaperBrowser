"""
Browse API routes for newspaper pages.

Read-only endpoints for browsing individual pages. Does not touch retrieval tables.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_page_repository
from app.repositories.pages import PageRepository
from app.models.api.responses import PageResponse


router = APIRouter(prefix="/api/pages", tags=["pages"])


@router.get("/{page_id}", response_model=PageResponse)
def get_page_detail(
    page_id: UUID,
    page_repo: PageRepository = Depends(get_page_repository),
):
    """
    Get single page details.

    Returns:
    - Page metadata (page number, image path)
    - OCR text (if available)
    - OCR metadata (confidence, provider, status)

    This endpoint only queries the pages table (browse context).
    No retrieval tables are touched.
    """
    page = page_repo.get_by_id(page_id)

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return PageResponse.model_validate(page)
