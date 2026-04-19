"""llama.cpp HTTP server client."""

import httpx

from src.core.logger import logger


class LlamaCppClient:
    """HTTP client for the llama.cpp server (/completion endpoint)."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def health(self) -> bool:
        """Return True if the llama.cpp server responds with HTTP 200 on /health."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                resp = await client.get(f"{self._base_url}/health")
                return bool(resp.status_code == 200)
        except httpx.RequestError:
            return False

    async def completion(
        self,
        prompt: str,
        *,
        n_predict: int = 256,
        temperature: float = 0.7,
        stop: list[str] | None = None,
    ) -> dict[str, object]:
        """Send a completion request to the llama.cpp server."""
        payload: dict[str, object] = {
            "prompt": prompt,
            "n_predict": n_predict,
            "temperature": temperature,
            "stream": False,
        }
        if stop:
            payload["stop"] = stop

        # Generous timeout: cold model load from disk can exceed 2 minutes.
        timeout = httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self._base_url}/completion", json=payload)
            if resp.status_code != 200:
                logger.error(
                    f"llama.cpp /completion returned {resp.status_code}: {resp.text}"
                )
            resp.raise_for_status()
            result: dict[str, object] = resp.json()
            return result
