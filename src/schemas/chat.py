"""Pydantic schemas for chat operations."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Model to represent a chat request."""

    message: str
    max_tokens: int = Field(default=256, ge=32, le=1024)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    doc_id: str | None = None


class ChatResponse(BaseModel):
    """Model to represent a chat response."""

    response: str
    model: str
    total_duration_ms: float | None = None
    context_chunks_used: int | None = None
