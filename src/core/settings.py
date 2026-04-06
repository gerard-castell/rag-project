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

    # Text Splitting Configuration
    chunk_size: int = 800
    chunk_overlap: int = 100

    # Embedding Configuration
    dense_model_name: str = "BAAI/bge-m3"
    sparse_model_name: str = "prithivida/Splade_PP_en_v1"
    embedding_batch_size: int = 16

    # Search Configuration
    default_search_limit: int = 5
    prefetch_multiplier: int = 2

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
