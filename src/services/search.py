"""Search service logic."""

from qdrant_client import models

from src.core.exceptions import RAGError, VectorDBError
from src.core.settings import settings
from src.core.vram_scheduler import VRAMScheduler
from src.ingestion.database import VectorDB
from src.ingestion.embedder import LocalEmbedder
from src.schemas.search import SearchRequest, SearchResponse


async def perform_hybrid_search(
    request: SearchRequest,
    embedder: LocalEmbedder,
    db: VectorDB,
    vram_scheduler: VRAMScheduler,
) -> list[SearchResponse]:
    """Do a hybrid search (Dense + Sparse) using RRF.

    Loads the embedder models via the VRAM scheduler for the duration of the
    call, so callers never need to remember to do so themselves.
    """
    try:
        async with vram_scheduler.schedule_embedding(embedder):
            vector_data = embedder.generate([request.query])[0]
    except Exception as e:
        raise RAGError(f"Embedding generation failed: {e}") from e

    prefetch_limit = request.limit * settings.prefetch_multiplier

    prefetch_dense = models.Prefetch(
        query=vector_data["dense"], using="dense-bge", limit=prefetch_limit
    )

    prefetch_sparse = models.Prefetch(
        query=models.SparseVector(
            indices=vector_data["sparse_indices"], values=vector_data["sparse_values"]
        ),
        using="sparse-splade",
        limit=prefetch_limit,
    )

    try:
        results = db.client.query_points(
            collection_name=settings.collection_name,
            prefetch=[prefetch_dense, prefetch_sparse],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=request.limit,
            with_payload=True,
        )
    except Exception as e:
        raise VectorDBError(f"Search failed in VectorDB: {e}") from e

    response = []
    for point in results.points:
        payload = point.payload or {}
        response.append(
            SearchResponse(
                text=payload.get("text", ""),
                score=point.score,
                metadata=payload.get("metadata", {}),
            )
        )

    return response
