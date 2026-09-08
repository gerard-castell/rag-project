"""Unit tests for the run_ingestion_logic background pipeline."""

from contextlib import ExitStack, contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from src.schemas.ingestion import TaskStatus
from src.services.ingestion import run_ingestion_logic
from src.services.task_store import TaskStore


@contextmanager
def _stubbed_pipeline(*, parsed_docs: list[Any], embedder: MagicMock, db: MagicMock):
    """Patch every dependency run_ingestion_logic resolves, yielding its TaskStore."""
    task_store = TaskStore()
    parser = MagicMock()
    parser.parse.return_value = parsed_docs

    vram_scheduler = MagicMock()
    vram_scheduler.schedule_embedding_sync.return_value.__enter__ = MagicMock()
    vram_scheduler.schedule_embedding_sync.return_value.__exit__ = MagicMock(
        return_value=False
    )

    with ExitStack() as stack:
        stack.enter_context(
            patch("src.services.ingestion.DocumentParser", return_value=parser)
        )
        stack.enter_context(
            patch("src.api.dependencies.get_embedder", return_value=embedder)
        )
        stack.enter_context(
            patch("src.api.dependencies.get_vector_db", return_value=db)
        )
        stack.enter_context(
            patch(
                "src.api.dependencies.get_vram_scheduler", return_value=vram_scheduler
            )
        )
        stack.enter_context(
            patch("src.api.dependencies.get_task_store", return_value=task_store)
        )
        stack.enter_context(patch("os.path.exists", return_value=False))
        yield task_store


def test_run_ingestion_logic_marks_task_done_on_success() -> None:
    """A successful parse/embed/upsert pipeline leaves the task DONE."""
    doc = SimpleNamespace(text="hello world " * 50, metadata={"page": 1})
    embedder = MagicMock()
    embedder.generate.side_effect = lambda texts: [
        {"dense": [0.1], "sparse_indices": [0], "sparse_values": [0.5]} for _ in texts
    ]
    db = MagicMock()

    with _stubbed_pipeline(parsed_docs=[doc], embedder=embedder, db=db) as task_store:
        task_store.create("task-1")
        run_ingestion_logic("fake_path.pdf", "task-1", "fake.pdf")

    record = task_store.get("task-1")
    assert record is not None
    assert record.status == TaskStatus.DONE
    assert record.chunks_indexed == record.total_chunks
    assert record.total_chunks > 0
    db.setup_hybrid_collection.assert_called_once()
    db.upsert_points.assert_called()


def test_run_ingestion_logic_marks_task_failed_when_parsing_raises() -> None:
    """A parser failure is caught, wrapped, and recorded as a FAILED task."""
    embedder = MagicMock()
    db = MagicMock()

    with _stubbed_pipeline(parsed_docs=[], embedder=embedder, db=db) as task_store:
        task_store.create("task-2")
        with patch(
            "src.services.ingestion.DocumentParser",
            return_value=MagicMock(parse=MagicMock(side_effect=RuntimeError("boom"))),
        ):
            run_ingestion_logic("fake_path.pdf", "task-2", "fake.pdf")

    record = task_store.get("task-2")
    assert record is not None
    assert record.status == TaskStatus.FAILED
    assert record.error is not None and "boom" in record.error


def test_run_ingestion_logic_marks_task_failed_when_no_text_extracted() -> None:
    """A document that yields no chunks fails the task with a clear message."""
    doc = SimpleNamespace(text="", metadata={"page": 1})
    embedder = MagicMock()
    db = MagicMock()

    with _stubbed_pipeline(parsed_docs=[doc], embedder=embedder, db=db) as task_store:
        task_store.create("task-3")
        run_ingestion_logic("fake_path.pdf", "task-3", "fake.pdf")

    record = task_store.get("task-3")
    assert record is not None
    assert record.status == TaskStatus.FAILED
    assert record.error == "No text could be extracted from the document."
    embedder.generate.assert_not_called()


def test_run_ingestion_logic_marks_task_failed_when_embedding_raises() -> None:
    """An embedding failure mid-pipeline unloads the embedder and fails the task."""
    doc = SimpleNamespace(text="hello world " * 50, metadata={"page": 1})
    embedder = MagicMock()
    embedder.generate.side_effect = RuntimeError("cuda out of memory")
    db = MagicMock()

    with _stubbed_pipeline(parsed_docs=[doc], embedder=embedder, db=db) as task_store:
        task_store.create("task-4")
        run_ingestion_logic("fake_path.pdf", "task-4", "fake.pdf")

    record = task_store.get("task-4")
    assert record is not None
    assert record.status == TaskStatus.FAILED
    assert record.error is not None and "cuda out of memory" in record.error
    db.upsert_points.assert_not_called()
