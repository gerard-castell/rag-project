"""Document management endpoints."""

from fastapi import APIRouter, HTTPException

from src.api.dependencies import VectorDBDep
from src.core.exceptions import DocumentNotFoundError
from src.schemas.documents import DeleteDocumentResponse, DocumentSummary
from src.services.documents import delete_document, list_documents

router = APIRouter()


@router.get("/documents", response_model=list[DocumentSummary])
async def list_documents_endpoint(db: VectorDBDep) -> list[DocumentSummary]:
    """List all ingested documents."""
    try:
        return list_documents(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/documents/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document_endpoint(
    doc_id: str, db: VectorDBDep
) -> DeleteDocumentResponse:
    """Delete a document and all of its indexed chunks."""
    try:
        return delete_document(db, doc_id)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
