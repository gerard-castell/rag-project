"""Dependency injection providers for FastAPI."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from qdrant_client import QdrantClient

from src.core.llama_cpp_client import LlamaCppClient
from src.core.settings import settings
from src.core.vram_scheduler import VRAMScheduler
from src.ingestion.database import VectorDB
from src.ingestion.embedder import LocalEmbedder


@lru_cache
def get_embedder() -> LocalEmbedder:
    """Singleton-like dependency for the embedder."""
    return LocalEmbedder()


@lru_cache
def get_vector_db() -> VectorDB:
    """Singleton-like dependency for VectorDB."""
    return VectorDB(url=settings.qdrant_url)


@lru_cache
def get_llama_client() -> LlamaCppClient:
    """Singleton-like dependency for LlamaCppClient."""
    return LlamaCppClient(base_url=settings.llama_cpp_url)


@lru_cache
def get_vram_scheduler() -> VRAMScheduler:
    """Singleton-like dependency for VRAMScheduler."""
    return VRAMScheduler(
        container_name=settings.llama_container_name,
        llama_cpp_url=settings.llama_cpp_url,
        idle_timeout_seconds=settings.llama_idle_timeout_seconds,
    )


EmbedderDep = Annotated[LocalEmbedder, Depends(get_embedder)]
VectorDBDep = Annotated[VectorDB, Depends(get_vector_db)]
QdrantClientDep = Annotated[QdrantClient, Depends(lambda: get_vector_db().client)]
LlamaCppClientDep = Annotated[LlamaCppClient, Depends(get_llama_client)]
VRAMSchedulerDep = Annotated[VRAMScheduler, Depends(get_vram_scheduler)]
