import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()

from src.utils.embeddings import get_embedding

QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "migration_docs")

if QDRANT_URL == ":memory:":
    qdrant_client = QdrantClient(location=":memory:")
elif QDRANT_URL.startswith("http"):
    qdrant_client = QdrantClient(url=QDRANT_URL)
else:
    qdrant_client = QdrantClient(path=QDRANT_URL)


MIGRATION_KNOWLEDGE_BASE = [
    {
        "id": 1,
        "text": "Flask apps use 'from flask import Flask' and 'app = Flask(__name__)'. FastAPI applications must migrate to 'from fastapi import FastAPI' and use 'app = FastAPI()'. Routing changes from '@app.route(\"/path\", methods=[\"GET\"])' to direct async methods like '@app.get(\"/path\") async def endpoint():'."
    },
    {
        "id": 2,
        "text": "Legacy blocking operations like 'time.sleep(seconds)' halt the global application execution flow in sync systems. For modern high-concurrency FastAPI setups, migrate all instances of 'time.sleep(n)' to 'import asyncio' and use 'await asyncio.sleep(n)'. Ensure the surrounding function is declared with 'async def'."
    },
    {
        "id": 3,
        "text": "Flask returning strings or dictionaries implicitly sets the status code to 200. In FastAPI, structural responses are optimized using standard Pydantic schemas or type-hints. Synchronous requests functions (like requests.get) should be moved to an async client library like httpx."
    }
]

def main():
    print(f"Connecting to Qdrant at: {QDRANT_URL}...")

    try:
        # Embed all docs first so vector size is known before collection creation
        print("Generating embeddings...")
        points = []
        vector_size = None
        for block in MIGRATION_KNOWLEDGE_BASE:
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
