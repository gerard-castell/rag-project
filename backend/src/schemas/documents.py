"""Pydantic schemas for document management."""

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    """Aggregated metadata for one ingested document."""

    doc_id: str
    source: str
    page_count: int
    ingested_at: str
    chunk_count: int


class DeleteDocumentResponse(BaseModel):
    """Response returned after deleting a document."""

    doc_id: str
    deleted_chunks: int
