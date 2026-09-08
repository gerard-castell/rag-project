"""Application configuration using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings configuration using Pydantic BaseSettings."""

    # API Keys
    llama_parse_api_key: str = Field(
        default=..., validation_alias="LLAMA_PARSE_API_KEY"
    )

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "knowledge_base"

    # Directory Paths
    upload_dir: Path = Path("temp_uploads")
    models_cache_dir: Path = Path("models_cache")

    # Max accepted size for a single /ingest upload, in bytes.
    max_upload_size_bytes: int = 50 * 1024 * 1024

    # Text Splitting Configuration
    chunk_size: int = 800
    chunk_overlap: int = 100

    # Embedding Configuration
    dense_model_name: str = "BAAI/bge-m3"
    sparse_model_name: str = "prithivida/Splade_PP_en_v1"
    embedding_batch_size: int = 8

    # Ingestion processes this many chunks per batch to cap peak RAM usage.
    ingestion_batch_size: int = 32

    # Max CPU threads for sparse (ONNX) model.
    sparse_model_threads: int = 4

    # Reranker Configuration
    rerank_model_name: str = "BAAI/bge-reranker-v2-m3"

    # llama.cpp Configuration
    llama_cpp_url: str = "http://localhost:8080"
    llama_cpp_model_name: str = "gemma-4-E4B-it-Q4_K_M"
    llama_container_name: str = "llama-cpp-gpu"
    llama_idle_timeout_seconds: int = 300  # 5 minutes

    # Search Configuration
    default_search_limit: int = 5
    prefetch_multiplier: int = 2

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
