import os
from qdrant_client import QdrantClient
from qdrant_client.http import models

class MigrationVectorStore:
    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = os.getenv("QDRANT_COLLECTION", "migration_docs")
        self.client = QdrantClient(url=self.url)

    def init_collection(self, vector_size: int = 1536):
        """Initializes the migration database tracking collection."""
        existing = self.client.get_collections()
        names = [c.name for c in existing.collections]

        if self.collection_name not in names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def search_migration_rules(self, query_vector: list, limit: int = 2) -> list:
        """Pulls relevant FastAPI syntax payloads matching structural anti-patterns."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return [hit.payload.get("text", "") for hit in results if hit.payload]
