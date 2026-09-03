"""Main entry point for the RAG Ingestion API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import get_vram_scheduler
from src.api.routes import chat, documents, health, ingest, search
from src.core.exceptions import RAGError
from src.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle manager for the FastAPI application."""
    scheduler = get_vram_scheduler()
    await scheduler.start()
    logger.info("Starting RAG API. Embedding models load on demand.")
    yield
    logger.info("Shutting down RAG API...")
    await scheduler.stop()


app = FastAPI(
    title="RAG Ingestion API",
    description="A production-ready RAG API for PDF ingestion and hybrid search.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RAGError)
async def rag_error_handler(request: Request, exc: RAGError) -> JSONResponse:
    """Handle custom RAG errors."""
    logger.error(f"RAG Error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error_type": exc.__class__.__name__},
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(f"Unexpected Error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"detail": "An internal server error occurred."}
    )


app.include_router(health.router, tags=["Health"])
app.include_router(ingest.router, tags=["Ingestion"])
app.include_router(search.router, tags=["Search"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(documents.router, tags=["Documents"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
