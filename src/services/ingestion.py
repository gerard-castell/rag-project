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
from src.schemas.ingestion import TaskStatus
from src.schemas.metadata import ChunkMetadata


def run_ingestion_logic(file_path: str, task_id: str) -> None:
    """Run the ingestion pipeline for a given file."""
    from src.api.dependencies import (
        get_embedder,
        get_task_store,
        get_vector_db,
        get_vram_scheduler,
    )

    task_store = get_task_store()
    try:
        logger.info(f"[Task {task_id}] Initializing processing of {file_path}")
        task_store.update(task_id, status=TaskStatus.PARSING)

        parser = DocumentParser()
        embedder = get_embedder()
        db = get_vector_db()
        vram_scheduler = get_vram_scheduler()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )

        try:
            docs = parser.parse(file_path)
            logger.info(f"[Task {task_id}] Parsed {len(docs)} documents/pages.")
        except Exception as e:
            raise DocumentParsingError(f"Failed to parse document: {e}") from e

        logger.info(f"[Task {task_id}] Splitting documents into chunks...")
        all_chunks: list[str] = []
        chunk_metadatas: list[ChunkMetadata] = []

        for doc in docs:
            chunks = splitter.split_text(doc.text)
            if not chunks:
                continue

            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadatas.append(
                    ChunkMetadata(
                        source=os.path.basename(file_path),
                        page=doc.metadata.get("page", 0),
                        doc_id=task_id,
                    )
                )

        if not all_chunks:
            logger.warning(f"[Task {task_id}] No text extracted to index.")
            task_store.update(
                task_id,
                status=TaskStatus.FAILED,
                error="No text could be extracted from the document.",
            )
            return

        total_chunks = len(all_chunks)
        task_store.update(
            task_id, status=TaskStatus.EMBEDDING, total_chunks=total_chunks
        )

        db.setup_hybrid_collection(settings.collection_name)

        logger.info(
            f"[Task {task_id}] Generating embeddings for {total_chunks} chunks..."
        )
        try:
            with vram_scheduler.schedule_embedding_sync(embedder):
                embeddings_batch = embedder.generate(all_chunks)
        except Exception as e:
            logger.error(f"[Task {task_id}] Embedding generation failed: {e}")
            raise
        all_points = []
        logger.info(f"[Task {task_id}] Preparing {total_chunks} points for upsert...")
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
                payload={"text": chunk, "metadata": metadata.model_dump()},
            )
            all_points.append(point)

        batch_size = settings.ingestion_batch_size
        chunks_indexed = 0
        for start in range(0, len(all_points), batch_size):
            batch = all_points[start : start + batch_size]
            db.upsert_points(settings.collection_name, batch)
            chunks_indexed += len(batch)
            logger.info(
                f"[Task {task_id}] Upserted {chunks_indexed}/{total_chunks} chunks"
            )
            task_store.update(task_id, chunks_indexed=chunks_indexed)

        logger.info(f"[Task {task_id}] Pipeline finished successfully.")
        task_store.update(task_id, status=TaskStatus.DONE)

    except RAGError as e:
        logger.error(f"[Task {task_id}] Application error: {e}")
        task_store.update(task_id, status=TaskStatus.FAILED, error=str(e))
    except Exception as e:  # noqa: BLE001 - background task must not raise
        logger.error(f"[Task {task_id}] Unexpected error: {e}")
        task_store.update(task_id, status=TaskStatus.FAILED, error=str(e))
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
            except Exception as e:  # noqa: BLE001 - best-effort cleanup
                logger.warning(
                    f"[Task {task_id}] Could not delete temp file {file_path}: {e}"
                )
