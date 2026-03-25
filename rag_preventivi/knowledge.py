from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from config import CHROMA_PATH, CHROMA_COLLECTION, EMBEDDING_MODEL, TOP_K_RESULTS


def build_knowledge() -> tuple[Knowledge, ChromaDb]:
    """Costruisce e restituisce il knowledge base Agno + ChromaDb."""
    embedder = GeminiEmbedder(id=EMBEDDING_MODEL)
    vector_db = ChromaDb(
        collection=CHROMA_COLLECTION,
        path=CHROMA_PATH,
        persistent_client=True,
        embedder=embedder,
    )
    knowledge = Knowledge(
        vector_db=vector_db,
        max_results=TOP_K_RESULTS,
    )
    return knowledge, vector_db
