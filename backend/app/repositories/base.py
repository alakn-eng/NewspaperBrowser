"""
Base repository with common database access patterns.

Provides shared functionality for all repositories including
connection management and common query patterns.
"""

from typing import TypeVar, Generic, Type, Optional, List, Any
from uuid import UUID
from supabase import Client
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, supabase: Client, table_name: str, model_class: Type[T]):
        """
        Initialize base repository.

        Args:
            supabase: Supabase client instance
            table_name: Name of the database table
            model_class: Pydantic model class for this table
        """
        self.supabase = supabase
        self.table_name = table_name
        self.model_class = model_class

    def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get a single record by ID.

        Args:
            id: Record UUID

        Returns:
            Model instance or None if not found
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("id", str(id))
            .maybe_single()
            .execute()
        )

        if response.data:
            return self.model_class(**response.data)
        return None

    def create(self, data: BaseModel) -> T:
        """
        Create a new record.

        Args:
            data: Pydantic model with data to insert

        Returns:
            Created model instance with generated ID
        """
        # Convert Pydantic model to dict, excluding None values
        insert_data = data.model_dump(exclude_none=True)

        response = (
            self.supabase.table(self.table_name)
            .insert(insert_data)
            .execute()
        )

        if not response.data:
            raise ValueError(f"Failed to create record in {self.table_name}")

        return self.model_class(**response.data[0])

    def update(self, id: UUID, data: dict) -> T:
        """
        Update a record by ID.

        Args:
            id: Record UUID
            data: Dictionary of fields to update

        Returns:
            Updated model instance
        """
        # Remove None values
        update_data = {k: v for k, v in data.items() if v is not None}

        response = (
            self.supabase.table(self.table_name)
            .update(update_data)
            .eq("id", str(id))
            .execute()
        )

        if not response.data:
            raise ValueError(f"Failed to update record {id} in {self.table_name}")

        return self.model_class(**response.data[0])

    def delete(self, id: UUID) -> None:
        """
        Delete a record by ID.

        Args:
            id: Record UUID
        """
        self.supabase.table(self.table_name).delete().eq("id", str(id)).execute()

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        List all records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        response = (
            self.supabase.table(self.table_name)
            .select("*")
            .limit(limit)
            .offset(offset)
            .execute()
        )

        return [self.model_class(**row) for row in response.data]

    def count(self) -> int:
        """
        Count total records in table.

        Returns:
            Total record count
        """
        response = (
            self.supabase.table(self.table_name)
            .select("id", count="exact")
            .execute()
        )

        return response.count or 0

    def _execute_upsert(self, data: dict, on_conflict: str) -> T:
        """
        Execute an upsert operation.

        Args:
            data: Data to insert/update
            on_conflict: Columns to check for conflict (e.g., "newspaper_id,issue_date")

        Returns:
            Model instance (created or existing)
        """
        response = (
            self.supabase.table(self.table_name)
            .upsert(data, on_conflict=on_conflict)
            .execute()
        )

        if not response.data:
            raise ValueError(f"Failed to upsert record in {self.table_name}")

        return self.model_class(**response.data[0])
