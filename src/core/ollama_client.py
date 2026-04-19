"""VRAM-aware Ollama HTTP wrapper."""

import httpx

from src.core.logger import logger
from src.core.settings import settings


class OllamaClient:
    """HTTP client for Ollama with VRAM-aware keep_alive management."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    async def get_loaded_models(self) -> list[str]:
        """Return names of models currently loaded in Ollama in VRAM."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/ps")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Ollama failed to get loaded models: {e}")
            return []

    async def force_unload(self, model: str) -> None:
        """Force Ollama to evict a model from VRAM immediately."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{self._base_url}/api/generate",
                    json={"model": model, "prompt": "", "keep_alive": 0},
                )
            logger.info(f"Unloaded Ollama model '{model}' from VRAM.")
        except Exception as e:
            logger.warning(f"Failed to unload Ollama model '{model}': {e}")

    async def generate(self, payload: dict[str, object]) -> dict[str, object]:
        """Send a generation request, injecting keep_alive on every call."""
        payload = {**payload, "keep_alive": settings.ollama_keep_alive_seconds}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._base_url}/api/generate", json=payload)
            resp.raise_for_status()
            result: dict[str, object] = resp.json()
            return result
