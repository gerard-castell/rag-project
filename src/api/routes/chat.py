"""Chat endpoint backed by llama.cpp with RAG context."""

from fastapi import APIRouter, HTTPException

from src.api.dependencies import (
    EmbedderDep,
    LlamaCppClientDep,
    VectorDBDep,
    VRAMSchedulerDep,
)
from src.schemas.chat import ChatRequest, ChatResponse
from src.services.chat import generate_chat_response

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    embedder: EmbedderDep,
    db: VectorDBDep,
    vram_scheduler: VRAMSchedulerDep,
    llama_client: LlamaCppClientDep,
) -> ChatResponse:
    """Hybrid search and rerank, then generate response via llama.cpp."""
    try:
        return await generate_chat_response(
            request, embedder, db, vram_scheduler, llama_client
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
