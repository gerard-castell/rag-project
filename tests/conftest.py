"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():  # noqa: ANN201
    """Provide a TestClient for FastAPI."""
    with TestClient(app) as c:
        yield c
