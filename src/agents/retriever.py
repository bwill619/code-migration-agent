import os
from openai import OpenAI
from src.agents.state import MigrationState
from src.database.vector_store import MigrationVectorStore

# Initialize external dependencies
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db_store = MigrationVectorStore()

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    """Helper function to vectorize anti-pattern strings."""
    text = text.replace("\n", " ")
    response = openai_client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def retriever_node(state: MigrationState) -> MigrationState:
    """
    LangGraph Agent Node: Iterates through flagged structural anti-patterns
    and queries Qdrant to retrieve relevant async upgrade documentation.
    """
    print("\n--- [AGENT: RETRIEVER] Querying migration rules vector space ---")
    
    anti_patterns = state.get("detected_anti_patterns", [])
    collected_context = []

    # If the parser found nothing, look for general framework initialization updates
    if not anti_patterns:
        anti_patterns = ["Migrate legacy Flask application instance to FastAPI"]

    for pattern in anti_patterns:
        try:
            print(f"[RETRIEVER] Vectorizing context query for: '{pattern}'")
            query_vector = get_embedding(pattern)
            
            # Retrieve semantic context chunks from local Qdrant
            matched_chunks = db_store.search_migration_rules(query_vector, limit=2)
            collected_context.extend(matched_chunks)
        except Exception as e:
            print(f"[RETRIEVER ERROR] Failed embedding generation/lookup: {e}")

    print(f"[RETRIEVER SUCCESS] Retrieved {len(collected_context)} documentation context blocks.")
    
    return {
        **state,
        "retrieved_docs": collected_context
    }
