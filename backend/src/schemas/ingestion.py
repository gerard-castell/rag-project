"""Pydantic schemas for ingestion task tracking."""

from enum import StrEnum

from pydantic import BaseModel


class TaskStatus(StrEnum):
    """Lifecycle states for an ingestion task."""

    QUEUED = "queued"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    DONE = "done"
    FAILED = "failed"


class TaskRecord(BaseModel):
    """Progress and outcome of a single ingestion task."""

    status: TaskStatus = TaskStatus.QUEUED
    chunks_indexed: int = 0
    total_chunks: int = 0
    error: str | None = None


class IngestResponse(BaseModel):
    """Response returned when a document is queued for ingestion."""

    status: str
    task_id: str
    info: str
