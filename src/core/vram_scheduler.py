"""GPU coordinator."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from src.ingestion.embedder import LocalEmbedder


class VRAMScheduler:
    """Serializes GPU usage between the fastembed embedder and llama.cpp server."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def schedule_embedding(
        self, embedder: LocalEmbedder
    ) -> AsyncGenerator[None, None]:
        """Acquire GPU lock, load embedder, yield, then unload."""
        async with self._lock:
            embedder.load()
            try:
                yield
            finally:
                embedder.unload()

    @asynccontextmanager
    async def schedule_generation(self) -> AsyncGenerator[None, None]:
        """Acquire GPU lock for llama.cpp inference."""
        async with self._lock:
            yield
