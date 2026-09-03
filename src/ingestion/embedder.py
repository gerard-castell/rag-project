"""Local embedder for generating dense and sparse embeddings on GPU."""

from typing import Any

import onnxruntime as ort
import torch
from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer

from src.core.logger import logger
from src.core.settings import settings


class LocalEmbedder:
    """Generates dense/sparse embeddings; requires `load()` before `generate()`."""

    def __init__(self) -> None:
        self.device = "cpu"
        self.sparse_providers = ["CPUExecutionProvider"]
        self.dense_model: SentenceTransformer | None = None
        self.sparse_model: SparseTextEmbedding | None = None

        if torch.cuda.is_available():
            self.device = "cuda"
            logger.info(f"CUDA detected: {torch.cuda.get_device_name(0)}")

            available_providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in available_providers:
                self.sparse_providers = ["CUDAExecutionProvider"]
                logger.info("Sparse Model: CUDA Execution Provider enabled.")
            else:
                logger.critical(
                    "CUDA is available for Torch, but ONNX Runtime cannot find 'CUDAExecutionProvider'. "
                    "Sparse model will fallback to CPU. "
                    "ACTION: Ensure 'onnxruntime-gpu' is installed and 'onnxruntime' is uninstalled."
                )
        elif torch.backends.mps.is_available():
            self.device = "mps"
            logger.info("MPS detected. Loading models on Apple Silicon.")
        else:
            logger.info("Using CPU for all models.")

    def load(self) -> None:
        """Load the dense and sparse models onto the target device, if not already loaded."""
        if self.dense_model is not None and self.sparse_model is not None:
            return

        logger.info(
            f"Loading Dense Model: {settings.dense_model_name} on {self.device}"
        )
        self.dense_model = SentenceTransformer(
            settings.dense_model_name,
            device=self.device,
            cache_folder=str(settings.models_cache_dir),
        )

        logger.info(
            f"Loading Sparse Model: {settings.sparse_model_name} "
            f"with {self.sparse_providers[0]}"
        )
        self.sparse_model = SparseTextEmbedding(
            model_name=settings.sparse_model_name,
            providers=self.sparse_providers,
            cache_dir=str(settings.models_cache_dir),
            threads=None,
        )

    def unload(self) -> None:
        """Release the dense and sparse models to free GPU/CPU memory."""
        self.dense_model = None
        self.sparse_model = None
        if self.device == "cuda":
            torch.cuda.empty_cache()

    def _require_models(self) -> tuple[SentenceTransformer, SparseTextEmbedding]:
        """Return the loaded models, raising if `load()` was never called."""
        if self.dense_model is None or self.sparse_model is None:
            raise RuntimeError(
                "Embedder models are not loaded. "
                "Use within schedule_embedding() context."
            )
        return self.dense_model, self.sparse_model

    def generate(self, texts: list[str]) -> list[dict[str, Any]]:
        """Generate both Dense (Semantic) and Sparse (Keyword) embeddings."""
        dense_model, sparse_model = self._require_models()

        with torch.no_grad():
            dense_embeddings = dense_model.encode(
                texts,
                batch_size=settings.embedding_batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        sparse_embeddings_gen = sparse_model.embed(
            texts, batch_size=settings.embedding_batch_size
        )

        results = []
        for dense, sparse in zip(dense_embeddings, sparse_embeddings_gen, strict=True):
            results.append(
                {
                    "dense": dense.tolist(),
                    "sparse_indices": sparse.indices.tolist(),
                    "sparse_values": sparse.values.tolist(),
                }
            )

        return results
