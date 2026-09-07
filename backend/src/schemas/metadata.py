"""Shared metadata schema for indexed chunks."""

from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    """Metadata attached to a single indexed text chunk."""

    source: str
    page: int
    doc_id: str
    page_count: int
    ingested_at: str
