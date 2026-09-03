"""Unit tests for VRAMScheduler container lifecycle."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import docker.errors
import pytest

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
