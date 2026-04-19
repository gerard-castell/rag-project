"""GPU coordinator with Docker-backed llama.cpp container lifecycle."""

import asyncio
import contextlib
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import docker
import docker.errors
import httpx

from src.core.logger import logger
from src.ingestion.embedder import LocalEmbedder


class VRAMScheduler:
    """Serializes GPU usage and manages llama.cpp container lifecycle.

    Stops the llama-cpp container after idle_timeout_seconds of inactivity
    to free VRAM. Transparently restarts it on the next schedule_generation()
    call and waits for the /health endpoint before proceeding.
    """

    def __init__(
        self,
        container_name: str,
        llama_cpp_url: str,
        idle_timeout_seconds: int,
    ) -> None:
        self._lock = asyncio.Lock()
        self._container_name = container_name
        self._llama_cpp_url = llama_cpp_url.rstrip("/")
        self._idle_timeout = idle_timeout_seconds
        self._last_used: float = 0.0
        self._idle_task: asyncio.Task[None] | None = None
        self._docker = docker.from_env()

    async def start(self) -> None:
        """Start background idle watcher. Call once from app lifespan."""
        self._idle_task = asyncio.create_task(self._idle_watcher())
        logger.info(
            "VRAMScheduler idle watcher started (timeout=%ds).", self._idle_timeout
        )

    async def stop(self) -> None:
        """Cancel idle watcher and close Docker client. Call from app lifespan."""
        if self._idle_task:
            self._idle_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._idle_task
        self._docker.close()
        logger.info("VRAMScheduler stopped.")

    async def _idle_watcher(self) -> None:
        """Poll every 30 s and stop container if idle timeout exceeded."""
        while True:
            await asyncio.sleep(30)
            await self._check_and_stop_if_idle()

    async def _check_and_stop_if_idle(self) -> None:
        """Stop the llama-cpp container if it has been idle too long."""
        if self._last_used == 0.0:
            return
        if time.monotonic() - self._last_used > self._idle_timeout:
            async with self._lock:
                if time.monotonic() - self._last_used > self._idle_timeout:
                    await asyncio.to_thread(self._stop_container)
                    self._last_used = 0.0

    def _stop_container(self) -> None:
        """Stop the llama-cpp Docker container (blocking, run via to_thread)."""
        try:
            container = self._docker.containers.get(self._container_name)
            if container.status == "running":
                container.stop(timeout=10)
                logger.info(
                    "Container '%s' stopped — VRAM freed.", self._container_name
                )
        except docker.errors.NotFound:
            logger.warning(
                "Container '%s' not found, nothing to stop.", self._container_name
            )

    def _start_container(self) -> None:
        """Start the llama-cpp Docker container (blocking, run via to_thread)."""
        container = self._docker.containers.get(self._container_name)
        if container.status != "running":
            container.start()
            logger.info("Container '%s' started.", self._container_name)

    async def _ensure_running(self) -> None:
        """Start container if not running, then wait for /health."""
        await asyncio.to_thread(self._start_container)
        await self._wait_until_ready()

    async def _wait_until_ready(self, timeout: float = 120.0) -> None:
        """Poll /health every 2 s until llama.cpp responds 200 or timeout."""
        deadline = time.monotonic() + timeout
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            while time.monotonic() < deadline:
                try:
                    resp = await client.get(f"{self._llama_cpp_url}/health")
                    if resp.status_code == 200:
                        logger.info("llama.cpp server is ready.")
                        return
                except httpx.RequestError:
                    pass
                await asyncio.sleep(2.0)
        raise TimeoutError(
            f"llama.cpp at {self._llama_cpp_url} did not become ready within {timeout}s"
        )

    @asynccontextmanager
    async def schedule_embedding(
        self, embedder: LocalEmbedder
    ) -> AsyncGenerator[None, None]:
        """Acquire GPU lock, load embedder models, yield, then unload."""
        async with self._lock:
            embedder.load()
            try:
                yield
            finally:
                embedder.unload()

    @asynccontextmanager
    async def schedule_generation(self) -> AsyncGenerator[None, None]:
        """Ensure llama.cpp container is running, acquire GPU lock, yield."""
        async with self._lock:
            await self._ensure_running()
            self._last_used = time.monotonic()
            try:
                yield
            finally:
                self._last_used = time.monotonic()
