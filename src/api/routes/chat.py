"""Chat endpoint backed by Ollama with RAG context."""

from fastapi import APIRouter, HTTPException

from src.api.dependencies import (
    EmbedderDep,
    OllamaClientDep,
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
    ollama_client: OllamaClientDep,
) -> ChatResponse:
    """Hybrid search and rerank to generate response via Ollama."""
    try:
        return await generate_chat_response(
            request, embedder, db, vram_scheduler, ollama_client
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
