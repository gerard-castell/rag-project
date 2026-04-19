"""Dependency injection providers for FastAPI."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from qdrant_client import QdrantClient

from src.core.ollama_client import OllamaClient
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
def get_ollama_client() -> OllamaClient:
    """Singleton-like dependency for OllamaClient."""
    return OllamaClient(base_url=settings.ollama_url)


@lru_cache
def get_vram_scheduler() -> VRAMScheduler:
    """Singleton-like dependency for VRAMScheduler."""
    return VRAMScheduler(ollama_client=get_ollama_client())


EmbedderDep = Annotated[LocalEmbedder, Depends(get_embedder)]
VectorDBDep = Annotated[VectorDB, Depends(get_vector_db)]
QdrantClientDep = Annotated[QdrantClient, Depends(lambda: get_vector_db().client)]
OllamaClientDep = Annotated[OllamaClient, Depends(get_ollama_client)]
VRAMSchedulerDep = Annotated[VRAMScheduler, Depends(get_vram_scheduler)]
