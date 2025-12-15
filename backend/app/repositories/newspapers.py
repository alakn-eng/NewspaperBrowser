"""
Newspaper repository for managing newspaper publications.
"""

from typing import Optional
from uuid import UUID
from supabase import Client

from app.models.db.browse import Newspaper, NewspaperCreate
from app.repositories.base import BaseRepository


class NewspaperRepository(BaseRepository[Newspaper]):
    """Repository for newspaper CRUD operations."""

    def __init__(self, supabase: Client):
        """Initialize newspaper repository."""
        super().__init__(supabase, "newspapers", Newspaper)

    def get_or_create(self, name: str) -> Newspaper:
        """
        Get existing newspaper by name or create if doesn't exist.

        Args:
            name: Newspaper name

        Returns:
            Newspaper instance (existing or newly created)
        """
        # Try to find existing newspaper by name
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("name", name)
            .maybe_single()
            .execute()
        )

        if response.data:
            return Newspaper(**response.data)

        # Create new newspaper if not found
        new_newspaper = NewspaperCreate(name=name)
        return self.create(new_newspaper)

    def get_by_name(self, name: str) -> Optional[Newspaper]:
        """
        Get newspaper by exact name match.

        Args:
            name: Newspaper name

        Returns:
            Newspaper instance or None if not found
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("name", name)
            .maybe_single()
            .execute()
        )

        if response.data:
            return Newspaper(**response.data)
        return None

    def search_by_name(self, name_query: str, limit: int = 10) -> list[Newspaper]:
        """
        Search newspapers by name (case-insensitive partial match).

        Args:
            name_query: Search query
            limit: Maximum results to return

        Returns:
            List of matching newspapers
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .ilike("name", f"%{name_query}%")
            .limit(limit)
            .execute()
        )

        return [Newspaper(**row) for row in response.data]
