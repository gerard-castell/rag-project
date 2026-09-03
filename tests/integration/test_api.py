"""Integration tests for the RAG API."""

from typing import Any
from unittest.mock import MagicMock

from src.api.dependencies import get_embedder, get_vector_db
from src.main import app


def test_health_check(client: Any) -> None:
    """Verifies that the health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


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

    stub_point = MagicMock()
    stub_point.payload = {"text": "hello world", "metadata": {}}
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
    assert body == [{"text": "hello world", "score": 0.9, "metadata": {}}]
    stub_embedder.load.assert_called_once()
    stub_embedder.unload.assert_called_once()


def test_ingest_validation(client: Any) -> None:
    """Verifies that ingestion only accepts PDF."""
    response = client.post(
        "/ingest", files={"file": ("test.txt", b"content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Solo soportamos PDF" in response.json()["detail"]
