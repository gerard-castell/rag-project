"""Dependency injection providers for FastAPI."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from qdrant_client import QdrantClient

from src.core.settings import settings
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


EmbedderDep = Annotated[LocalEmbedder, Depends(get_embedder)]
VectorDBDep = Annotated[VectorDB, Depends(get_vector_db)]
QdrantClientDep = Annotated[QdrantClient, Depends(lambda: get_vector_db().client)]
