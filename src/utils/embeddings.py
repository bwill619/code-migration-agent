import os

_local_model = None

def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        print("[EMBEDDINGS] Loading local sentence-transformers model (all-MiniLM-L6-v2)...")
        _local_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _local_model

def get_embedding(text: str) -> list:
    """Tries OpenAI text-embedding-3-small first; falls back to local all-MiniLM-L6-v2 (384 dims)."""
    text = text.replace("\n", " ")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            response = OpenAI(api_key=api_key).embeddings.create(
                input=[text], model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            if any(code in str(e) for code in ("insufficient_quota", "invalid_api_key", "429", "401")):
                print("[EMBEDDINGS] OpenAI key unavailable, falling back to local model.")
            else:
                raise

    return _get_local_model().encode(text).tolist()
