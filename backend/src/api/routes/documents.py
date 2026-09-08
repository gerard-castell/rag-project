"""Document management endpoints."""

from fastapi import APIRouter

from src.api.dependencies import VectorDBDep
from src.schemas.documents import DeleteDocumentResponse, DocumentSummary
from src.services.documents import delete_document, list_documents

router = APIRouter()


@router.get("/documents", response_model=list[DocumentSummary])
async def list_documents_endpoint(db: VectorDBDep) -> list[DocumentSummary]:
    """List all ingested documents."""
    return list_documents(db)


@router.delete("/documents/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document_endpoint(
    doc_id: str, db: VectorDBDep
) -> DeleteDocumentResponse:
    """Delete a document and all of its indexed chunks."""
    return delete_document(db, doc_id)
