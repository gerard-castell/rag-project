"""GPU coordinator."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import torch

from src.core.logger import logger
from src.core.ollama_client import OllamaClient
from src.core.settings import settings


def _free_vram_mb() -> float:
    """Return free VRAM in MB. Returns inf when CUDA is unavailable."""
    if not torch.cuda.is_available():
        return float("inf")
    free_bytes, _ = torch.cuda.mem_get_info()
    return free_bytes / (1024 * 1024)


class VRAMScheduler:
    """Singleton coordinator for GPU time-sharing between embedder and Ollama."""

    def __init__(self, ollama_client: OllamaClient) -> None:
        self._lock = asyncio.Lock()
        self._ollama = ollama_client

    @asynccontextmanager
    async def schedule_embedding(self) -> AsyncGenerator[None, None]:
        """Acquire GPU lock for embedding, evicting Ollama only if VRAM is tight."""
        free_mb = _free_vram_mb()
        logger.debug(f"VRAMScheduler: free VRAM = {free_mb:.0f} MB")

        if free_mb < settings.embedder_vram_budget_mb:
            loaded = await self._ollama.get_loaded_models()
            if loaded:
                logger.info(
                    f"VRAMScheduler: free VRAM {free_mb:.0f}MB < "
                    f"{settings.embedder_vram_budget_mb}MB — evicting {loaded}"
                )
                for model in loaded:
                    await self._ollama.force_unload(model)
            else:
                logger.warning(
                    "VRAMScheduler: could not list loaded models evicting as fallback."
                )
        else:
            logger.debug("VRAMScheduler: enough free VRAM, Ollama stays warm.")

        async with self._lock:
            yield

    async def force_evict_ollama(self) -> None:
        """Evict all loaded Ollama models, regardless of free VRAM."""
        loaded = await self._ollama.get_loaded_models()
        if loaded:
            logger.info(f"VRAMScheduler: force-evicting {loaded} for ingestion.")
            for model in loaded:
                await self._ollama.force_unload(model)
        else:
            logger.debug("VRAMScheduler: no Ollama models loaded, nothing to evict.")
