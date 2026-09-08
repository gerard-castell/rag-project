"""Unit tests for VRAMScheduler container lifecycle."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import docker.errors
import pytest

from src.core.exceptions import ContainerUnavailableError, ModelWarmupTimeoutError
from src.core.vram_scheduler import VRAMScheduler


@pytest.fixture
def mock_docker_client():
    """Return a mock Docker client and container."""
    container = MagicMock()
    container.status = "running"
    docker_client = MagicMock()
    docker_client.containers.get.return_value = container
    return docker_client, container


@pytest.fixture
def scheduler():
    """Return a VRAMScheduler with no Docker client resolved yet."""
    return VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=300,
    )


async def test_schedule_generation_starts_stopped_container(mock_docker_client):
    """Start container when status is exited before yielding."""
    docker_client, container = mock_docker_client
    container.status = "exited"

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=300,
    )

    with (
        patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client),
        patch.object(s, "_wait_until_ready", new_callable=AsyncMock),
    ):
        async with s.schedule_generation():
            pass

    container.start.assert_called_once()


async def test_schedule_generation_skips_start_when_already_running(mock_docker_client):
    """Skip container.start() when status is already running."""
    docker_client, container = mock_docker_client
    container.status = "running"

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=300,
    )

    with (
        patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client),
        patch.object(s, "_wait_until_ready", new_callable=AsyncMock),
    ):
        async with s.schedule_generation():
            pass

    container.start.assert_not_called()


async def test_check_and_stop_if_idle_stops_container(mock_docker_client):
    """Stop running container and reset _last_used when idle timeout exceeded."""
    docker_client, container = mock_docker_client
    container.status = "running"

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=1,
    )

    s._last_used = time.monotonic() - 2  # 2 s ago, timeout is 1 s
    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        await s._check_and_stop_if_idle()

    container.stop.assert_called_once_with(timeout=10)
    assert s._last_used == 0.0


async def test_check_and_stop_if_idle_does_nothing_when_not_idle(mock_docker_client):
    """Leave container running when idle timeout has not elapsed."""
    docker_client, container = mock_docker_client

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=300,
    )

    s._last_used = time.monotonic()  # just used
    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        await s._check_and_stop_if_idle()

    container.stop.assert_not_called()


async def test_check_and_stop_if_idle_does_nothing_when_never_used(scheduler):
    """Leave container alone when _last_used is 0.0 (llama.cpp never called)."""
    scheduler._last_used = 0.0
    with patch("src.core.vram_scheduler.docker.from_env") as mock_from_env:
        await scheduler._check_and_stop_if_idle()

    mock_from_env.assert_not_called()


async def test_construction_does_not_touch_docker():
    """Constructing a scheduler must not open a Docker connection."""
    with patch("src.core.vram_scheduler.docker.from_env") as mock_from_env:
        VRAMScheduler(
            container_name="llama-cpp-gpu",
            llama_cpp_url="http://localhost:8080",
            idle_timeout_seconds=300,
        )

    mock_from_env.assert_not_called()


def test_client_property_returns_none_when_docker_unavailable(scheduler):
    """Missing Docker daemon disables container lifecycle management gracefully."""
    with patch(
        "src.core.vram_scheduler.docker.from_env",
        side_effect=docker.errors.DockerException("no daemon"),
    ) as mock_from_env:
        assert scheduler._client is None
        assert scheduler._client is None

    mock_from_env.assert_called_once()


async def test_idle_watcher_loop_polls_check_and_stop_if_idle(scheduler):
    """The background idle watcher polls `_check_and_stop_if_idle` on each tick."""
    call_count = 0

    async def _check() -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            raise asyncio.CancelledError

    with (
        patch.object(scheduler, "_check_and_stop_if_idle", side_effect=_check),
        patch("src.core.vram_scheduler.asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(asyncio.CancelledError),
    ):
        await scheduler._idle_watcher()

    assert call_count == 3


def test_start_container_raises_container_unavailable_error_when_not_found(scheduler):
    """A missing llama.cpp container surfaces as a typed, actionable RAGError."""
    docker_client = MagicMock()
    docker_client.containers.get.side_effect = docker.errors.NotFound("missing")

    with (
        patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client),
        pytest.raises(ContainerUnavailableError, match="llama-cpp-gpu"),
    ):
        scheduler._start_container()


async def test_ensure_running_maps_timeout_error_to_model_warmup_error(
    mock_docker_client,
):
    """A cold-start timeout is mapped to a typed error, not a bare TimeoutError."""
    docker_client, container = mock_docker_client
    container.status = "running"

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=300,
    )

    with (
        patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client),
        patch.object(s, "_wait_until_ready", side_effect=TimeoutError("not ready")),
        pytest.raises(ModelWarmupTimeoutError),
    ):
        await s._ensure_running()


async def test_get_status_reports_container_lock_and_idle_state(mock_docker_client):
    """/health/gpu surface: container status, lock state, seconds-since-last-use."""
    docker_client, container = mock_docker_client
    container.status = "running"

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=300,
    )

    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        status = await s.get_status()

    assert status["container_status"] == "running"
    assert status["lock_held"] is False
    assert status["seconds_since_last_use"] is None

    s._last_used = time.monotonic() - 5
    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        status = await s.get_status()

    assert status["seconds_since_last_use"] >= 5


async def test_get_status_reports_not_found_container(scheduler):
    """A container that does not exist is reported as 'not_found', not an error."""
    docker_client = MagicMock()
    docker_client.containers.get.side_effect = docker.errors.NotFound("missing")

    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        status = await scheduler.get_status()

    assert status["container_status"] == "not_found"


def test_schedule_embedding_sync_loads_once_around_whole_block(scheduler):
    """Without a running loop captured, the sync facade still load/unloads once."""
    embedder = MagicMock()
    calls = []

    with scheduler.schedule_embedding_sync(embedder):
        calls.append("inside")

    embedder.load.assert_called_once()
    embedder.unload.assert_called_once()
    assert calls == ["inside"]


async def test_schedule_embedding_unloads_even_when_body_raises(scheduler):
    """A caller that raises inside the block must not leak a loaded embedder."""
    embedder = MagicMock()

    with pytest.raises(ValueError, match="boom"):
        async with scheduler.schedule_embedding(embedder):
            raise ValueError("boom")

    embedder.load.assert_called_once()
    embedder.unload.assert_called_once()
    assert not scheduler._lock.locked()


def test_schedule_embedding_sync_unloads_even_when_body_raises(scheduler):
    """The sync facade must also unload on exception, not just on success."""
    embedder = MagicMock()

    with (
        pytest.raises(ValueError, match="boom"),
        scheduler.schedule_embedding_sync(embedder),
    ):
        raise ValueError("boom")

    embedder.load.assert_called_once()
    embedder.unload.assert_called_once()
    assert not scheduler._lock.locked()


async def test_schedule_generation_releases_lock_when_ensure_running_raises(scheduler):
    """A cold-start failure must release the GPU lock, not deadlock it."""
    with (
        patch.object(
            scheduler,
            "_ensure_running",
            side_effect=ModelWarmupTimeoutError("not ready"),
        ),
        pytest.raises(ModelWarmupTimeoutError),
    ):
        async with scheduler.schedule_generation():
            pass  # pragma: no cover - unreachable, ensure_running raises first

    assert not scheduler._lock.locked()


async def test_lock_serializes_embedding_and_generation(mock_docker_client):
    """Concurrent embed + generate calls never run on the GPU at the same time."""
    docker_client, container = mock_docker_client
    container.status = "running"

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=300,
    )

    active = 0
    max_concurrent = 0
    embedder = MagicMock()

    async def _do_embedding() -> None:
        nonlocal active, max_concurrent
        async with s.schedule_embedding(embedder):
            active += 1
            max_concurrent = max(max_concurrent, active)
            await asyncio.sleep(0.01)
            active -= 1

    async def _do_generation() -> None:
        nonlocal active, max_concurrent
        async with s.schedule_generation():
            active += 1
            max_concurrent = max(max_concurrent, active)
            await asyncio.sleep(0.01)
            active -= 1

    with (
        patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client),
        patch.object(s, "_wait_until_ready", new_callable=AsyncMock),
    ):
        await asyncio.gather(
            _do_embedding(), _do_generation(), _do_embedding(), _do_generation()
        )

    assert max_concurrent == 1


async def test_container_restarts_cleanly_after_idle_stop(mock_docker_client):
    """A container stopped by the idle watcher starts again on the next request."""
    docker_client, container = mock_docker_client
    container.status = "running"

    s = VRAMScheduler(
        container_name="llama-cpp-gpu",
        llama_cpp_url="http://localhost:8080",
        idle_timeout_seconds=1,
    )

    def _stop(**_kwargs: object) -> None:
        container.status = "exited"

    container.stop.side_effect = _stop
    s._last_used = time.monotonic() - 2  # exceeds the 1 s idle timeout

    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        await s._check_and_stop_if_idle()
        container.stop.assert_called_once()

        with patch.object(s, "_wait_until_ready", new_callable=AsyncMock):
            async with s.schedule_generation():
                pass

    container.start.assert_called_once()
