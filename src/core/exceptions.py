"""Custom exception hierarchy for the RAG application."""


class RAGError(Exception):
    """Base exception for all RAG related errors."""

    pass


class DocumentParsingError(RAGError):
    """Raised when document parsing fails."""

    pass


class EmbeddingGenerationError(RAGError):
    """Raised when embedding generation fails."""

    pass


class VectorDBError(RAGError):
    """Raised when vector database operations fail."""

    pass
