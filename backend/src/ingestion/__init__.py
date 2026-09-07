"""Ingestion package."""

from src.ingestion.embedder import LocalEmbedder
from src.ingestion.parser import DocumentParser

__all__ = ["DocumentParser", "LocalEmbedder"]
