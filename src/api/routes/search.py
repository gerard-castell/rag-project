"""Search endpoint."""

from fastapi import APIRouter, HTTPException

from src.api.dependencies import EmbedderDep, VectorDBDep
from src.schemas.search import SearchRequest, SearchResponse
from src.services.search import perform_hybrid_search

router = APIRouter()


@router.post("/search", response_model=list[SearchResponse])
async def search_endpoint(
    request: SearchRequest, embedder: EmbedderDep, db: VectorDBDep
) -> list[SearchResponse]:
    """Do a hybrid search (Dense + Sparse) using RRF."""
    try:
        return perform_hybrid_search(request, embedder, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
