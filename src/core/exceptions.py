"""Custom exception hierarchy for the RAG application."""


class RAGError(Exception):
    """Base exception for all RAG related errors."""


class DocumentParsingError(RAGError):
    """Raised when document parsing fails."""


class EmbeddingGenerationError(RAGError):
    """Raised when embedding generation fails."""


class VectorDBError(RAGError):
    """Raised when vector database operations fail."""
