"""Business logic for RAG-augmented chat via llama.cpp."""

from src.core.llama_cpp_client import LlamaCppClient
from src.core.settings import settings
from src.core.vram_scheduler import VRAMScheduler
from src.ingestion.database import VectorDB
from src.ingestion.embedder import LocalEmbedder
from src.schemas.chat import ChatRequest, ChatResponse
from src.schemas.search import SearchRequest
from src.services.search import perform_hybrid_search

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using ONLY the context "
    "provided below. If the answer cannot be found in the context, say so clearly. "
    "Do not make up information."
)


async def generate_chat_response(
    request: ChatRequest,
    embedder: LocalEmbedder,
    db: VectorDB,
    vram_scheduler: VRAMScheduler,
    llama_client: LlamaCppClient,
) -> ChatResponse:
    """Retrieve relevant context, then generate a grounded response via llama.cpp."""
    search_request = SearchRequest(
        query=request.message, limit=settings.default_search_limit
    )

    async with vram_scheduler.schedule_embedding(embedder):
        results = perform_hybrid_search(search_request, embedder, db)

    context_blocks = [f"[{i + 1}] {r.text}" for i, r in enumerate(results)]
    context = "\n\n".join(context_blocks)

    prompt = (
        f"### System\n{_SYSTEM_PROMPT}\n\n"
        f"### Context\n{context}\n\n"
        f"### Question\n{request.message}\n\n"
        f"### Answer\n"
    )

    async with vram_scheduler.schedule_generation():
        data = await llama_client.completion(
            prompt,
            n_predict=request.max_tokens,
            temperature=request.temperature,
            stop=["\n\n\n", "### Question"],
        )

    timings = data.get("timings", {})
    predicted_ms: float | None = None
    if isinstance(timings, dict):
        raw = timings.get("predicted_ms")
        if raw is not None:
            predicted_ms = round(float(str(raw)), 2)

    return ChatResponse(
        response=str(data["content"]),
        model=settings.llama_cpp_model_name,
        total_duration_ms=predicted_ms,
        context_chunks_used=len(results),
    )
