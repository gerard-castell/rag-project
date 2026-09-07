"""Pytest configuration and shared fixtures."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_vram_scheduler
from src.core.vram_scheduler import VRAMScheduler
from src.ingestion.embedder import LocalEmbedder
from src.main import app


class NoOpVRAMScheduler(VRAMScheduler):
    """VRAMScheduler stand-in that never touches Docker, for tests."""

    def __init__(self) -> None:
        super().__init__(
            container_name="unused",
            llama_cpp_url="http://localhost:8080",
            idle_timeout_seconds=300,
        )

    async def start(self) -> None:
        """No-op: skip the idle watcher background task."""

    async def stop(self) -> None:
        """No-op: nothing to tear down."""

    @asynccontextmanager
    async def schedule_embedding(
        self, embedder: LocalEmbedder
    ) -> AsyncGenerator[None, None]:
        """Load/unload the embedder without acquiring a real GPU lock."""
        embedder.load()
        try:
            yield
        finally:
            embedder.unload()


@pytest.fixture
def client():
    """Provide a TestClient for FastAPI with a no-op VRAMScheduler."""
    app.dependency_overrides[get_vram_scheduler] = NoOpVRAMScheduler
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_vram_scheduler, None)
