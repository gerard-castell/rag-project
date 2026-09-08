"""Chat endpoint backed by llama.cpp with RAG context."""

from fastapi import APIRouter

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
    """Retrieve context via hybrid search, then generate a response via llama.cpp."""
    return await generate_chat_response(
        request, embedder, db, vram_scheduler, llama_client
    )
