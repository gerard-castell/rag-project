"""In-memory store for tracking ingestion task progress."""

import threading
from typing import cast

from src.schemas.ingestion import TaskRecord, TaskStatus


class TaskStore:
    """Thread-safe in-memory store of ingestion task records, keyed by task_id."""

    def __init__(self) -> None:
        self._records: dict[str, TaskRecord] = {}
        self._lock = threading.Lock()

    def create(self, task_id: str) -> None:
        """Register a new task in the queued state."""
        with self._lock:
            self._records[task_id] = TaskRecord()

    def get(self, task_id: str) -> TaskRecord | None:
        """Return a copy of the task record, or None if unknown."""
        with self._lock:
            record = self._records.get(task_id)
            if record is None:
                return None
            return cast("TaskRecord", record.model_copy())

    def update(
        self,
        task_id: str,
        *,
        status: TaskStatus | None = None,
        chunks_indexed: int | None = None,
        total_chunks: int | None = None,
        error: str | None = None,
    ) -> None:
        """Update the fields provided on an existing task record, if present."""
        with self._lock:
            record = self._records.get(task_id)
            if record is None:
                return
            if status is not None:
                record.status = status
            if chunks_indexed is not None:
                record.chunks_indexed = chunks_indexed
            if total_chunks is not None:
                record.total_chunks = total_chunks
            if error is not None:
                record.error = error
