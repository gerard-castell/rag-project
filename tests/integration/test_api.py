"""Integration tests for the RAG API."""

from typing import Any
from unittest.mock import MagicMock

from src.api.dependencies import get_embedder, get_vector_db
from src.main import app


def test_health_check(client: Any) -> None:
    """Verifies that the health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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
