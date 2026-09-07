from qdrant_client import QdrantClient, models
from qdrant_client.conversions.common_types import Points

from src.core.exceptions import VectorDBError


class VectorDB:
    """Class to manage Qdrant storage."""

    def __init__(self, url: str) -> None:
        self.client = QdrantClient(url=url)

    def setup_hybrid_collection(self, name: str) -> None:
        """Set up a collection with hybrid vectors (dense + sparse)."""
        try:
            if not self.client.collection_exists(name):
                self.client.create_collection(
                    collection_name=name,
                    vectors_config={
                        "dense-bge": models.VectorParams(
                            size=1024, distance=models.Distance.COSINE
                        )
                    },
                    sparse_vectors_config={
                        "sparse-splade": models.SparseVectorParams(
                            modifier=models.Modifier.IDF
                        )
                    },
                )
            self.client.create_payload_index(
                collection_name=name,
                field_name="metadata.doc_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except Exception as e:
            raise VectorDBError(f"Failed to setup collection {name}: {e}") from e

    def upsert_points(self, collection_name: str, points: Points) -> None:
        """Upsert points into the specified collection."""
        try:
            self.client.upsert(collection_name=collection_name, points=points)
        except Exception as e:
            raise VectorDBError(
                f"Failed to upsert points to {collection_name}: {e}"
            ) from e

    def delete_points(self, collection_name: str, points_filter: models.Filter) -> None:
        """Delete all points matching a filter from the specified collection."""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(filter=points_filter),
            )
        except Exception as e:
            raise VectorDBError(
                f"Failed to delete points from {collection_name}: {e}"
            ) from e
