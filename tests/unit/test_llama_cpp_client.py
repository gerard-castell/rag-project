"""Tests for LlamaCppClient health check."""

import httpx
import pytest
import respx

from src.core.llama_cpp_client import LlamaCppClient


@pytest.mark.asyncio
async def test_health_returns_true_when_server_ok():
    """Return True when /health responds 200."""
    with respx.mock:
        respx.get("http://localhost:8080/health").mock(
            return_value=httpx.Response(200)
        )
        client = LlamaCppClient(base_url="http://localhost:8080")
        assert await client.health() is True


@pytest.mark.asyncio
async def test_health_returns_false_when_server_down():
    """Return False when /health connection is refused."""
    with respx.mock:
        respx.get("http://localhost:8080/health").mock(
            side_effect=httpx.ConnectError("refused")
        )
        client = LlamaCppClient(base_url="http://localhost:8080")
        assert await client.health() is False
