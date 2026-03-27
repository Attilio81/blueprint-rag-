# mcp_preventivi/embeddings.py
import os
import chromadb
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

COLLECTION_NAME = "iab_articoli"
CHROMA_PATH = os.path.join(os.path.dirname(__file__), ".chroma_iab")
EMBEDDING_MODEL = "gemini-embedding-2-preview"
EMBEDDING_DIMENSIONS = 3072


def _get_embedder():
    from agno.knowledge.embedder.google import GeminiEmbedder
    return GeminiEmbedder(id=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)


_chroma_client = None  # type: chromadb.ClientAPI | None  # lazy singleton


def _get_collection():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client.get_or_create_collection(COLLECTION_NAME)


def cerca_simili(query_text: str, n_risultati: int = 10) -> list[dict]:
    """Ricerca semantica per descrizione simile usando embedding GeminiEmbedder."""
    embedder = _get_embedder()
    collection = _get_collection()
    query_embedding = embedder.get_embedding(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_risultati,
    )
    output = []
    for i, metadata in enumerate(results["metadatas"][0]):
        output.append({**metadata, "score": results["distances"][0][i]})
    return output


def index_articoli(articoli: list[dict]) -> int:
    """Indicizza una lista di articoli in ChromaDB. Restituisce il numero indicizzato.

    NOTA PRESTAZIONI: genera un embedding per articolo (una chiamata API per volta).
    Per cataloghi grandi (>1000 articoli) l'operazione può richiedere diversi minuti
    e potrebbe superare le quote API. Considerare di eseguire in orari off-peak.
    """
    embedder = _get_embedder()
    collection = _get_collection()
    ids, embeddings, metadatas = [], [], []
    for art in articoli:
        testo = f"{art['codart']} {art['descrizione']}"
        embedding = embedder.get_embedding(testo)
        ids.append(art["codart"])
        embeddings.append(embedding)
        metadatas.append({
            "codart": art["codart"],
            "descrizione": art["descrizione"],
            "unita_misura": art.get("unita_misura", ""),
            "bloccato": art.get("bloccato", "N"),
            "esaurito": art.get("esaurito", "N"),
        })
    collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
    return len(ids)
