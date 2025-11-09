"""
Pagination utilities for API endpoints.
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel
from math import ceil


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response with metadata.

    Type Parameters:
        T: The type of items in the paginated response

    Attributes:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_previous: Whether there is a previous page
    """
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "items": [{"id": 1, "name": "Example"}],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False
            }
        }


class Paginator:
    """Utility class for creating paginated responses."""

    @staticmethod
    def create_paginated_response(
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> PaginatedResponse[T]:
        """
        Create a paginated response with metadata.

        Args:
            items: List of items for the current page
            total: Total number of items across all pages
            page: Current page number (1-indexed)
            page_size: Number of items per page

        Returns:
            PaginatedResponse with items and pagination metadata
        """
        total_pages = ceil(total / page_size) if total > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )


class PaginationParams(BaseModel):
    """
    Pagination parameters for FastAPI dependency injection.

    Usage in FastAPI endpoint:
        @router.get("/items")
        async def list_items(
            pagination: PaginationParams = Depends(PaginationParams.as_query)
        ):
            ...
    """
    page: int = 1
    page_size: int = 20

    @classmethod
    def as_query(
        cls,
        page: int = 1,
        page_size: int = 20
    ) -> "PaginationParams":
        """Create PaginationParams from query parameters."""
        return cls(page=max(1, page), page_size=min(max(1, page_size), 100))

    @property
    def skip(self) -> int:
        """Calculate number of items to skip (for offset-based pagination)."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit (same as page_size)."""
        return self.page_size
