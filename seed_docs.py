import os
import json
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()

from src.utils.embeddings import get_embedding

QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "migration_docs")
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base.json")

if QDRANT_URL == ":memory:":
    qdrant_client = QdrantClient(location=":memory:")
elif QDRANT_URL.startswith("http"):
    qdrant_client = QdrantClient(url=QDRANT_URL)
else:
    qdrant_client = QdrantClient(path=QDRANT_URL)


def load_knowledge_base() -> list:
    with open(KNOWLEDGE_BASE_PATH, "r") as f:
        return json.load(f)

def main():
    print(f"Connecting to Qdrant at: {QDRANT_URL}...")
    knowledge_base = load_knowledge_base()
    print(f"Loaded {len(knowledge_base)} rules from {KNOWLEDGE_BASE_PATH}")

    try:
        print("Generating embeddings...")
        points = []
        vector_size = None
        for block in knowledge_base:
            print(f"Vectorizing Migration Rule #{block['id']}...")
            vector = get_embedding(block["text"])
            if vector_size is None:
                vector_size = len(vector)
            points.append(
                models.PointStruct(
                    id=block["id"],
                    vector=vector,
                    payload={"text": block["text"]}
                )
            )

        existing = qdrant_client.get_collections()
        collection_names = [c.name for c in existing.collections]

        if COLLECTION_NAME in collection_names:
            print(f"Wiping existing collection '{COLLECTION_NAME}' for a clean re-index...")
            qdrant_client.delete_collection(collection_name=COLLECTION_NAME)

        print(f"Creating collection '{COLLECTION_NAME}' ({vector_size} dims, Cosine)...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )

        qdrant_client.upsert(collection_name=COLLECTION_NAME, wait=True, points=points)
        print(f"Success! Upserted {len(points)} migration rules into Qdrant.")

    except Exception as e:
        print(f"Critical failure initializing or seeding database: {e}")
    finally:
        qdrant_client.close()

if __name__ == "__main__":
    main()
