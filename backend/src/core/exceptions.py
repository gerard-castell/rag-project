"""Custom exception hierarchy; each subclass carries its own HTTP status/detail."""


class RAGError(Exception):
    """Base exception for all RAG related errors."""

    status_code: int = 500
    detail: str | None = None

    def http_detail(self) -> str:
        """Return the user-facing message: `detail` override, else str(self)."""
        return self.detail if self.detail is not None else str(self)


class DocumentParsingError(RAGError):
    """Raised when document parsing fails."""


class EmbeddingGenerationError(RAGError):
    """Raised when embedding generation fails."""


class VectorDBError(RAGError):
    """Raised when vector database operations fail."""


class DocumentNotFoundError(RAGError):
    """Raised when a requested document does not exist."""

    status_code = 404


class ContainerUnavailableError(RAGError):
    """Raised when the llama.cpp Docker container cannot be found."""

    status_code = 503


class ModelWarmupTimeoutError(RAGError):
    """Raised when llama.cpp does not become ready within the cold-start timeout."""

    status_code = 503
    detail = "Model is warming up, retry shortly."
