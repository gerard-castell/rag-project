"""Ingestion service logic."""

import gc
import os
import uuid

import torch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import models

from src.core.exceptions import DocumentParsingError, RAGError
from src.core.logger import logger
from src.core.settings import settings
from src.ingestion.parser import DocumentParser


def run_ingestion_logic(file_path: str, task_id: str) -> None:
    """Run the ingestion pipeline for a given file."""
    try:
        logger.info(f"[Task {task_id}] Initializing processing of {file_path}")

        parser = DocumentParser()
        from src.api.dependencies import get_embedder, get_vector_db

        embedder = get_embedder()
        db = get_vector_db()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )

        try:
            docs = parser.parse(file_path)
            logger.info(f"[Task {task_id}] Parsed {len(docs)} documents/pages.")
        except Exception as e:
            raise DocumentParsingError(f"Failed to parse document: {e}") from e

        logger.info(f"[Task {task_id}] Splitting documents into chunks...")
        all_chunks = []
        chunk_metadatas = []

        for doc in docs:
            chunks = splitter.split_text(doc.text)
            if not chunks:
                continue

            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadatas.append(
                    {
                        "source": os.path.basename(file_path),
                        "page": doc.metadata.get("page", 0),
                    }
                )

        if not all_chunks:
            logger.warning(f"[Task {task_id}] No text extracted to index.")
            return

        db.setup_hybrid_collection(settings.collection_name)

        logger.info(
            f"[Task {task_id}] Generating embeddings for {len(all_chunks)} chunks..."
        )
        try:
            embedder.load()
            embeddings_batch = embedder.generate(all_chunks)
        except Exception as e:
            logger.error(f"[Task {task_id}] Embedding generation failed: {e}")
            raise e
        finally:
            embedder.unload()
        all_points = []
        logger.info(
            f"[Task {task_id}] Preparing {len(all_chunks)} points for upsert..."
        )
        for chunk, metadata, vector_data in zip(
            all_chunks, chunk_metadatas, embeddings_batch, strict=True
        ):
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense-bge": vector_data["dense"],
                    "sparse-splade": models.SparseVector(
                        indices=vector_data["sparse_indices"],
                        values=vector_data["sparse_values"],
                    ),
                },
                payload={"text": chunk, "metadata": metadata},
            )
            all_points.append(point)

        if all_points:
            logger.info(
                f"[Task {task_id}] Saving {len(all_points)} vectors to Qdrant..."
            )
            db.upsert_points(settings.collection_name, all_points)
            logger.info(f"[Task {task_id}] Pipeline finished successfully.")

    except RAGError as e:
        logger.error(f"[Task {task_id}] Application error: {e}")
    except Exception as e:
        logger.error(f"[Task {task_id}] Unexpected error: {e}")
    finally:
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info(f"[Task {task_id}] CUDA memory freed.")
        elif torch.backends.mps.is_available():
            torch.mps.empty_cache()
            logger.info(f"[Task {task_id}] MPS memory freed.")

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(
                    f"[Task {task_id}] Could not delete temp file {file_path}: {e}"
                )
