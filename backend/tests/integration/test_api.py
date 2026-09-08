"""Integration tests for the RAG API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.dependencies import (
    get_embedder,
    get_llama_client,
    get_vector_db,
    get_vram_scheduler,
)
from src.core.exceptions import ModelWarmupTimeoutError
from src.core.settings import settings
from src.main import app
from tests.conftest import NoOpVRAMScheduler


def test_health_check(client: Any) -> None:
    """Verifies that the health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_gpu_reports_observability_fields(client: Any) -> None:
    """/health/gpu surfaces llama.cpp reachability, container state, and lock."""
    response = client.get("/health/gpu")
    assert response.status_code == 200
    body = response.json()
    assert "llama_cpp_reachable" in body
    assert "container_status" in body
    assert "lock_held" in body
    assert "seconds_since_last_use" in body


def test_search_validation(client: Any) -> None:
    """Verifies that search validation works (missing body)."""
    response = client.post("/search", json={})
    assert response.status_code == 422


def test_search_returns_200_with_stubbed_embedder(client: Any) -> None:
    """Regression test: /search loads the embedder via VRAMScheduler and returns 200."""
    stub_embedder = MagicMock()
    stub_embedder.generate.return_value = [
        {"dense": [0.1, 0.2], "sparse_indices": [0], "sparse_values": [0.5]}
    ]

    stub_metadata = {
        "source": "report.pdf",
        "page": 1,
        "doc_id": "task-1",
        "page_count": 3,
        "ingested_at": "2026-01-01T00:00:00+00:00",
    }
    stub_point = MagicMock()
    stub_point.payload = {"text": "hello world", "metadata": stub_metadata}
    stub_point.score = 0.9

    stub_db = MagicMock()
    stub_db.client.query_points.return_value = MagicMock(points=[stub_point])

    app.dependency_overrides[get_embedder] = lambda: stub_embedder
    app.dependency_overrides[get_vector_db] = lambda: stub_db
    try:
        response = client.post("/search", json={"query": "hello", "limit": 5})
    finally:
        app.dependency_overrides.pop(get_embedder, None)
        app.dependency_overrides.pop(get_vector_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body == [{"text": "hello world", "score": 0.9, "metadata": stub_metadata}]
    stub_embedder.load.assert_called_once()
    stub_embedder.unload.assert_called_once()


def test_ingest_validation(client: Any) -> None:
    """Verifies that ingestion only accepts PDF."""
    response = client.post(
        "/ingest", files={"file": ("test.txt", b"content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are supported." in response.json()["detail"]


def test_ingest_sanitizes_path_traversal_filename(client: Any) -> None:
    """A filename with traversal segments is reduced to its basename, not escaped."""
    with patch("src.api.routes.ingest.run_ingestion_logic") as mock_run:
        response = client.post(
            "/ingest",
            files={"file": ("../../../etc/evil.pdf", b"%PDF-1.4", "application/pdf")},
        )
    assert response.status_code == 202
    stored_filename = mock_run.call_args.args[2]
    assert stored_filename == "evil.pdf"
    assert ".." not in stored_filename and "/" not in stored_filename


def test_ingest_rejects_non_pdf_content(client: Any) -> None:
    """A file named `.pdf` whose content isn't a PDF is rejected on magic bytes."""
    response = client.post(
        "/ingest", files={"file": ("fake.pdf", b"not a real pdf", "application/pdf")}
    )
    assert response.status_code == 400
    assert "not a valid PDF" in response.json()["detail"]


def test_ingest_rejects_upload_over_max_size(client: Any) -> None:
    """Uploads larger than the configured limit are rejected with 413."""
    oversized = b"%PDF-1.4" + b"0" * settings.max_upload_size_bytes
    response = client.post(
        "/ingest", files={"file": ("big.pdf", oversized, "application/pdf")}
    )
    assert response.status_code == 413
    assert "exceeds maximum upload size" in response.json()["detail"]


def test_list_documents_aggregates_chunks_by_doc_id(client: Any) -> None:
    """Verifies that /documents groups chunk points into per-document summaries."""
    points = [
        MagicMock(
            payload={
                "text": "a",
                "metadata": {
                    "source": "report.pdf",
                    "page": 1,
                    "doc_id": "doc-1",
                    "page_count": 2,
                    "ingested_at": "2026-01-01T00:00:00+00:00",
                },
            }
        ),
        MagicMock(
            payload={
                "text": "b",
                "metadata": {
                    "source": "report.pdf",
                    "page": 2,
                    "doc_id": "doc-1",
                    "page_count": 2,
                    "ingested_at": "2026-01-01T00:00:00+00:00",
                },
            }
        ),
    ]
    stub_db = MagicMock()
    stub_db.client.collection_exists.return_value = True
    stub_db.client.scroll.return_value = (points, None)

    app.dependency_overrides[get_vector_db] = lambda: stub_db
    try:
        response = client.get("/documents")
    finally:
        app.dependency_overrides.pop(get_vector_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body == [
        {
            "doc_id": "doc-1",
            "source": "report.pdf",
            "page_count": 2,
            "ingested_at": "2026-01-01T00:00:00+00:00",
            "chunk_count": 2,
        }
    ]


def test_delete_document_not_found_returns_404(client: Any) -> None:
    """Verifies that deleting an unknown doc_id returns 404."""
    stub_db = MagicMock()
    stub_db.client.collection_exists.return_value = True
    stub_db.client.scroll.return_value = ([], None)

    app.dependency_overrides[get_vector_db] = lambda: stub_db
    try:
        response = client.delete("/documents/missing-doc")
    finally:
        app.dependency_overrides.pop(get_vector_db, None)

    assert response.status_code == 404


def test_chat_returns_503_when_model_is_warming_up(client: Any) -> None:
    """A cold-start timeout surfaces as a 503 with a retry-shortly message."""

    class TimingOutScheduler(NoOpVRAMScheduler):
        """Scheduler stand-in whose generation slot always times out."""

        @asynccontextmanager
        async def schedule_generation(self) -> AsyncGenerator[None, None]:
            raise ModelWarmupTimeoutError("llama.cpp did not become ready")
            yield  # pragma: no cover - unreachable, satisfies generator typing

    stub_embedder = MagicMock()
    stub_embedder.generate.return_value = [
        {"dense": [0.1, 0.2], "sparse_indices": [0], "sparse_values": [0.5]}
    ]
    stub_db = MagicMock()
    stub_db.client.query_points.return_value = MagicMock(points=[])

    app.dependency_overrides[get_embedder] = lambda: stub_embedder
    app.dependency_overrides[get_vector_db] = lambda: stub_db
    app.dependency_overrides[get_vram_scheduler] = TimingOutScheduler
    try:
        response = client.post("/chat", json={"message": "hello"})
    finally:
        app.dependency_overrides.pop(get_embedder, None)
        app.dependency_overrides.pop(get_vector_db, None)
        app.dependency_overrides[get_vram_scheduler] = NoOpVRAMScheduler

    assert response.status_code == 503
    assert "warming up" in response.json()["detail"]


def test_ingest_status_unknown_task_returns_404(client: Any) -> None:
    """Verifies that checking an unknown task_id returns 404."""
    response = client.get("/ingest/does-not-exist")
    assert response.status_code == 404


def test_search_failure_returns_500_via_global_ragerror_handler(client: Any) -> None:
    """A VectorDB failure in the service layer surfaces as a typed 500, not a crash."""
    stub_embedder = MagicMock()
    stub_embedder.generate.return_value = [
        {"dense": [0.1, 0.2], "sparse_indices": [0], "sparse_values": [0.5]}
    ]
    stub_db = MagicMock()
    stub_db.client.query_points.side_effect = RuntimeError("qdrant unreachable")

    app.dependency_overrides[get_embedder] = lambda: stub_embedder
    app.dependency_overrides[get_vector_db] = lambda: stub_db
    try:
        response = client.post("/search", json={"query": "hello", "limit": 5})
    finally:
        app.dependency_overrides.pop(get_embedder, None)
        app.dependency_overrides.pop(get_vector_db, None)

    assert response.status_code == 500
    body = response.json()
    assert body["error_type"] == "VectorDBError"
    assert "qdrant unreachable" in body["detail"]


class _GenerationNoOpScheduler(NoOpVRAMScheduler):
    """Scheduler stand-in whose generation slot skips the container/GPU lock."""

    @asynccontextmanager
    async def schedule_generation(self) -> AsyncGenerator[None, None]:
        """Yield immediately without touching Docker or a real GPU lock."""
        yield


def test_chat_returns_200_with_generated_response(client: Any) -> None:
    """The full retrieve-then-generate chat path returns a grounded response."""
    stub_embedder = MagicMock()
    stub_embedder.generate.return_value = [
        {"dense": [0.1, 0.2], "sparse_indices": [0], "sparse_values": [0.5]}
    ]
    stub_point = MagicMock()
    stub_point.payload = {
        "text": "the sky is blue",
        "metadata": {
            "source": "sky.pdf",
            "page": 1,
            "doc_id": "doc-1",
            "page_count": 1,
            "ingested_at": "2026-01-01T00:00:00+00:00",
        },
    }
    stub_point.score = 0.9
    stub_db = MagicMock()
    stub_db.client.query_points.return_value = MagicMock(points=[stub_point])

    stub_llama_client = MagicMock()
    stub_llama_client.completion = AsyncMock(
        return_value={"content": "It's blue.", "timings": {"predicted_ms": 42.0}}
    )

    app.dependency_overrides[get_embedder] = lambda: stub_embedder
    app.dependency_overrides[get_vector_db] = lambda: stub_db
    app.dependency_overrides[get_llama_client] = lambda: stub_llama_client
    app.dependency_overrides[get_vram_scheduler] = _GenerationNoOpScheduler
    try:
        response = client.post("/chat", json={"message": "What color is the sky?"})
    finally:
        app.dependency_overrides.pop(get_embedder, None)
        app.dependency_overrides.pop(get_vector_db, None)
        app.dependency_overrides.pop(get_llama_client, None)
        app.dependency_overrides[get_vram_scheduler] = NoOpVRAMScheduler

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == "It's blue."
    assert body["context_chunks_used"] == 1
    assert body["total_duration_ms"] == 42.0


def test_delete_document_returns_200_and_deleted_chunk_count(client: Any) -> None:
    """Deleting a known doc_id removes its chunks and reports how many."""
    points = [
        MagicMock(
            payload={
                "text": "a",
                "metadata": {
                    "source": "report.pdf",
                    "page": 1,
                    "doc_id": "doc-1",
                    "page_count": 1,
                    "ingested_at": "2026-01-01T00:00:00+00:00",
                },
            }
        )
    ]
    stub_db = MagicMock()
    stub_db.client.collection_exists.return_value = True
    stub_db.client.scroll.return_value = (points, None)

    app.dependency_overrides[get_vector_db] = lambda: stub_db
    try:
        response = client.delete("/documents/doc-1")
    finally:
        app.dependency_overrides.pop(get_vector_db, None)

    assert response.status_code == 200
    assert response.json() == {"doc_id": "doc-1", "deleted_chunks": 1}
    stub_db.delete_points.assert_called_once()


def test_ingest_creates_queued_task_status(client: Any) -> None:
    """Verifies that uploading a PDF immediately registers a queued task."""
    with patch("src.api.routes.ingest.run_ingestion_logic") as mock_run:
        response = client.post(
            "/ingest", files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")}
        )
    assert response.status_code == 202
    mock_run.assert_called_once()
    task_id = response.json()["task_id"]

    status_response = client.get(f"/ingest/{task_id}")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "queued"
    assert body["chunks_indexed"] == 0
    assert body["total_chunks"] == 0
    assert body["error"] is None
