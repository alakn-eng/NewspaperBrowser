"""
Repositories package - Data access layer.

Repositories provide CRUD operations and query methods for database tables.
"""

from app.repositories.base import BaseRepository
from app.repositories.newspapers import NewspaperRepository
from app.repositories.issues import IssueRepository
from app.repositories.pages import PageRepository
from app.repositories.ingest_jobs import IngestJobRepository

__all__ = [
    "BaseRepository",
    "NewspaperRepository",
    "IssueRepository",
    "PageRepository",
    "IngestJobRepository",
]
