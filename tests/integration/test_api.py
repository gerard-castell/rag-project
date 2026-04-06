"""Integration tests for the RAG API."""

from typing import Any


def test_health_check(client: Any) -> None:
    """Verifies that the health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_search_validation(client: Any) -> None:
    """Verifies that search validation works (missing body)."""
    response = client.post("/search", json={})
    assert response.status_code == 422


def test_ingest_validation(client: Any) -> None:
    """Verifies that ingestion only accepts PDF."""
    response = client.post(
        "/ingest", files={"file": ("test.txt", b"content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Solo soportamos PDF" in response.json()["detail"]
