"""Search endpoint."""

from fastapi import APIRouter

from src.api.dependencies import EmbedderDep, VectorDBDep, VRAMSchedulerDep
from src.schemas.search import SearchRequest, SearchResponse
from src.services.search import perform_hybrid_search

router = APIRouter()


@router.post("/search", response_model=list[SearchResponse])
async def search_endpoint(
    request: SearchRequest,
    embedder: EmbedderDep,
    db: VectorDBDep,
    vram_scheduler: VRAMSchedulerDep,
) -> list[SearchResponse]:
    """Do a hybrid search (Dense + Sparse) using RRF."""
    return await perform_hybrid_search(request, embedder, db, vram_scheduler)
