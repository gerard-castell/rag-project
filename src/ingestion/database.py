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
