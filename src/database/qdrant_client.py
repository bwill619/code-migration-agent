import os 
from qdrant_client import QdrantClient
from qdrant_client.http import models

class MigrationVectorStore:
    # Fallback to local host if docker-compose network environment variables aren't set
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = os.getenv("QDRANT_PORT", 6333)
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = "migration_docs"


    def init_collection(self, vector_size: int = 1536):
        """
        Creates a Qdrant collection if it does not exist.
        Default 1536 corresponds to OpenAI text-embedding-3-small dimensions.
        """

        existing_collections = self.client.get_collections()
        collection_names = [c.name for c in existing_collections]

        if self.collection_name not in collection_names:
            print(f"[DB INFO] Creating Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
        else:
            print(f"[DB INFO] Collection '{self.collection_name}' already exists.")
    
    
    def upsert_documentation(self, ids: list, vectors: list, payloads: list):
        """Indexes doc chunks into collection with text payloads"""
        self.client.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                ids=ids,
                vectors=vectors,
                payloads=payloads,
            )
        )

    def search_docs(self, query_vector: list, limit: int = 3):
        """Executes a dense vector semantic lookup against migration rules."""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
