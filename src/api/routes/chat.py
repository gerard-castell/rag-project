"""Chat endpoint backed by Ollama with RAG context (Sprint 3)."""

from fastapi import APIRouter, HTTPException

from src.api.dependencies import EmbedderDep, VectorDBDep
from src.schemas.chat import ChatRequest, ChatResponse
from src.services.chat import generate_chat_response

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, embedder: EmbedderDep, db: VectorDBDep
) -> ChatResponse:
    """Hybrid search → rerank → generate a grounded response via Ollama."""
    try:
        return await generate_chat_response(request, embedder, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
