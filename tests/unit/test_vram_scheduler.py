"""Unit tests for VRAMScheduler container lifecycle."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

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
def scheduler(mock_docker_client):
    """Return a VRAMScheduler with a mocked Docker client."""
    docker_client, _ = mock_docker_client
    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        s = VRAMScheduler(
            container_name="llama-cpp-gpu",
            llama_cpp_url="http://localhost:8080",
            idle_timeout_seconds=300,
        )
    return s


async def test_schedule_generation_starts_stopped_container(mock_docker_client):
    """Start container when status is exited before yielding."""
    docker_client, container = mock_docker_client
    container.status = "exited"

    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        s = VRAMScheduler(
            container_name="llama-cpp-gpu",
            llama_cpp_url="http://localhost:8080",
            idle_timeout_seconds=300,
        )

    with patch.object(s, "_wait_until_ready", new_callable=AsyncMock):
        async with s.schedule_generation():
            pass

    container.start.assert_called_once()


async def test_schedule_generation_skips_start_when_already_running(mock_docker_client):
    """Skip container.start() when status is already running."""
    docker_client, container = mock_docker_client
    container.status = "running"

    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        s = VRAMScheduler(
            container_name="llama-cpp-gpu",
            llama_cpp_url="http://localhost:8080",
            idle_timeout_seconds=300,
        )

    with patch.object(s, "_wait_until_ready", new_callable=AsyncMock):
        async with s.schedule_generation():
            pass

    container.start.assert_not_called()


async def test_check_and_stop_if_idle_stops_container(mock_docker_client):
    """Stop running container and reset _last_used when idle timeout exceeded."""
    docker_client, container = mock_docker_client
    container.status = "running"

    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        s = VRAMScheduler(
            container_name="llama-cpp-gpu",
            llama_cpp_url="http://localhost:8080",
            idle_timeout_seconds=1,
        )

    s._last_used = time.monotonic() - 2  # 2 s ago, timeout is 1 s
    await s._check_and_stop_if_idle()

    container.stop.assert_called_once_with(timeout=10)
    assert s._last_used == 0.0


async def test_check_and_stop_if_idle_does_nothing_when_not_idle(mock_docker_client):
    """Leave container running when idle timeout has not elapsed."""
    docker_client, container = mock_docker_client

    with patch("src.core.vram_scheduler.docker.from_env", return_value=docker_client):
        s = VRAMScheduler(
            container_name="llama-cpp-gpu",
            llama_cpp_url="http://localhost:8080",
            idle_timeout_seconds=300,
        )

    s._last_used = time.monotonic()  # just used
    await s._check_and_stop_if_idle()

    container.stop.assert_not_called()


async def test_check_and_stop_if_idle_does_nothing_when_never_used(scheduler):
    """Leave container alone when _last_used is 0.0 (llama.cpp never called)."""
    scheduler._last_used = 0.0
    await scheduler._check_and_stop_if_idle()
    scheduler._docker.containers.get.assert_not_called()
