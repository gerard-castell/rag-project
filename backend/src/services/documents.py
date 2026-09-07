"""Business logic for document listing and deletion."""

from qdrant_client import models

from src.core.exceptions import DocumentNotFoundError, VectorDBError
from src.core.settings import settings
from src.ingestion.database import VectorDB
from src.schemas.documents import DeleteDocumentResponse, DocumentSummary


def list_documents(db: VectorDB) -> list[DocumentSummary]:
    """List all documents aggregated from indexed chunk metadata."""
    if not db.client.collection_exists(settings.collection_name):
        return []

    documents: dict[str, DocumentSummary] = {}
    try:
        next_offset = None
        while True:
            points, next_offset = db.client.scroll(
                collection_name=settings.collection_name,
                with_payload=True,
                with_vectors=False,
                limit=256,
                offset=next_offset,
            )
            for point in points:
                payload = point.payload or {}
                metadata = payload.get("metadata", {})
                doc_id = metadata.get("doc_id")
                if not doc_id:
                    continue
                summary = documents.get(doc_id)
                if summary is None:
                    summary = DocumentSummary(
                        doc_id=doc_id,
                        source=metadata.get("source", ""),
                        page_count=metadata.get("page_count", 0),
                        ingested_at=metadata.get("ingested_at", ""),
                        chunk_count=0,
                    )
                    documents[doc_id] = summary
                summary.chunk_count += 1
            if next_offset is None:
                break
    except Exception as e:
        raise VectorDBError(f"Failed to list documents: {e}") from e

    return sorted(documents.values(), key=lambda doc: doc.ingested_at, reverse=True)


def delete_document(db: VectorDB, doc_id: str) -> DeleteDocumentResponse:
    """Delete every chunk belonging to a document, or raise if it isn't found."""
    documents = {doc.doc_id: doc for doc in list_documents(db)}
    summary = documents.get(doc_id)
    if summary is None:
        raise DocumentNotFoundError(f"Document {doc_id} not found")

    db.delete_points(
        settings.collection_name,
        models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.doc_id", match=models.MatchValue(value=doc_id)
                )
            ]
        ),
    )
    return DeleteDocumentResponse(doc_id=doc_id, deleted_chunks=summary.chunk_count)
