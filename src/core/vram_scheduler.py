"""GPU coordinator with Docker-backed llama.cpp container lifecycle."""

import asyncio
import contextlib
import time
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

import docker
import docker.errors
import httpx

from src.core.exceptions import ContainerUnavailableError, ModelWarmupTimeoutError
from src.core.logger import logger
from src.ingestion.embedder import LocalEmbedder


class VRAMScheduler:
    """Serializes GPU usage and manages llama.cpp container lifecycle.

    Stops the llama-cpp container after idle_timeout_seconds of inactivity
    to free VRAM. Transparently restarts it on the next schedule_generation()
    call and waits for the /health endpoint before proceeding.
    """

    def __init__(
        self, container_name: str, llama_cpp_url: str, idle_timeout_seconds: int
    ) -> None:
        self._lock = asyncio.Lock()
        self._container_name = container_name
        self._llama_cpp_url = llama_cpp_url.rstrip("/")
        self._idle_timeout = idle_timeout_seconds
        self._last_used: float = 0.0
        self._idle_task: asyncio.Task[None] | None = None
        self._docker: docker.DockerClient | None = None
        self._docker_unavailable = False
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def _client(self) -> docker.DockerClient | None:
        """Lazily connect to Docker, warning once and disabling on failure."""
        if self._docker is None and not self._docker_unavailable:
            try:
                self._docker = docker.from_env()
            except docker.errors.DockerException as exc:
                self._docker_unavailable = True
                logger.warning(
                    "Docker daemon unavailable, container lifecycle management "
                    "disabled: %s",
                    exc,
                )
        return self._docker

    async def start(self) -> None:
        """Start background idle watcher. Call once from app lifespan."""
        self._loop = asyncio.get_running_loop()
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
        if self._docker is not None:
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
        client = self._client
        if client is None:
            return
        try:
            container = client.containers.get(self._container_name)
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
        client = self._client
        if client is None:
            return
        try:
            container = client.containers.get(self._container_name)
        except docker.errors.NotFound as exc:
            raise ContainerUnavailableError(
                f"Container '{self._container_name}' does not exist. Create it "
                "(e.g. `docker compose up -d llama-cpp`) before sending chat "
                "requests."
            ) from exc
        if container.status != "running":
            container.start()
            logger.info("Container '%s' started.", self._container_name)

    async def _ensure_running(self) -> None:
        """Start container if not running, then wait for /health."""
        await asyncio.to_thread(self._start_container)
        try:
            await self._wait_until_ready()
        except TimeoutError as exc:
            raise ModelWarmupTimeoutError(str(exc)) from exc

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

    def _container_status(self) -> str:
        """Return the llama-cpp container's Docker status (blocking)."""
        client = self._client
        if client is None:
            return "docker_unavailable"
        try:
            container = client.containers.get(self._container_name)
            return str(container.status)
        except docker.errors.NotFound:
            return "not_found"

    async def get_status(self) -> dict[str, object]:
        """Return observable scheduler state for the /health endpoint."""
        container_status = await asyncio.to_thread(self._container_status)
        seconds_since_last_use = (
            None
            if self._last_used == 0.0
            else round(time.monotonic() - self._last_used, 1)
        )
        return {
            "container_status": container_status,
            "lock_held": self._lock.locked(),
            "seconds_since_last_use": seconds_since_last_use,
        }

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

    @contextmanager
    def schedule_embedding_sync(
        self, embedder: LocalEmbedder
    ) -> Generator[None, None, None]:
        """Provide a synchronous `schedule_embedding` for background-task threads.

        Ingestion runs as a sync function in a worker thread, so it cannot
        `async with` the scheduler's asyncio.Lock directly. This submits lock
        acquire/release to the loop the scheduler started on, letting a whole
        ingestion batch share one load() instead of thrashing per chunk batch.
        """
        if self._loop is None:
            embedder.load()
            try:
                yield
            finally:
                embedder.unload()
            return

        acquire_future = asyncio.run_coroutine_threadsafe(
            self._lock.acquire(), self._loop
        )
        acquire_future.result()
        try:
            embedder.load()
            try:
                yield
            finally:
                embedder.unload()
        finally:
            self._loop.call_soon_threadsafe(self._lock.release)

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
