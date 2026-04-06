"""Pydantic schemas for search operations."""

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Model to represent a search request."""

    query: str
    limit: int = Field(default=5, ge=1, le=50)


class SearchResponse(BaseModel):
    """Model to represent a search response."""

    text: str
    score: float
    metadata: dict[str, Any] = {}
