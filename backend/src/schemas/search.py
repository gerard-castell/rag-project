"""Pydantic schemas for search operations."""

from pydantic import BaseModel, Field

from src.schemas.metadata import ChunkMetadata


class SearchRequest(BaseModel):
    """Model to represent a search request."""

    query: str
    limit: int = Field(default=5, ge=1, le=50)
    doc_id: str | None = None


class SearchResponse(BaseModel):
    """Model to represent a search response."""

    text: str
    score: float
    metadata: ChunkMetadata
