"""Custom exception hierarchy for the RAG application."""


class RAGError(Exception):
    """Base exception for all RAG related errors."""


class DocumentParsingError(RAGError):
    """Raised when document parsing fails."""


class EmbeddingGenerationError(RAGError):
    """Raised when embedding generation fails."""


class VectorDBError(RAGError):
    """Raised when vector database operations fail."""


class DocumentNotFoundError(RAGError):
    """Raised when a requested document does not exist."""


class ContainerUnavailableError(RAGError):
    """Raised when the llama.cpp Docker container cannot be found."""


class ModelWarmupTimeoutError(RAGError):
    """Raised when llama.cpp does not become ready within the cold-start timeout."""
