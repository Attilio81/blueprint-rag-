# ingestion/pipeline.py
import hashlib
import json
import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.document import Document
from ingestion.text_extractor import extract_text_chunks, is_corrupted_pdf
from ingestion.image_extractor import extract_vision_chunks
from config import (
    DOCUMENTS_DIR, INDEXED_FILE, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS,
    CHROMA_PATH, CHROMA_COLLECTION,
)

load_dotenv()


def compute_file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_indexed(index_file: str = INDEXED_FILE) -> dict:
    if not os.path.exists(index_file):
        return {}
    try:
        with open(index_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"Warning: Could not read {index_file}, starting fresh")
        return {}


def save_indexed(data: dict, index_file: str = INDEXED_FILE) -> None:
    parent = os.path.dirname(index_file)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(index_file, "w") as f:
        json.dump(data, f, indent=2)


def is_already_indexed(pdf_path: str, index_file: str = INDEXED_FILE) -> bool:
    indexed = load_indexed(index_file)
    source = Path(pdf_path).name
    current_hash = compute_file_hash(pdf_path)
    return indexed.get(source) == current_hash


def _upsert_chunks(vector_db: ChromaDb, chunks: list[dict]) -> None:
    """Inserts chunks into the vector DB as Agno Document objects."""
    documents = [
        Document(
            content=c["content"],
            meta_data={"source": c["source"], "page": c["page"], "type": c["type"]},
        )
        for c in chunks
        if c.get("content", "").strip()
    ]
    if documents:
        # Build a deterministic content hash from all chunk contents
        combined = "".join(c["content"] for c in chunks if c.get("content", "").strip())
        content_hash = hashlib.sha256(combined.encode()).hexdigest()
        vector_db.upsert(content_hash, documents)


def list_pdf_files() -> list:
    """Returns a sorted list of PDF paths from the module-level DOCUMENTS_DIR."""
    return sorted(Path(DOCUMENTS_DIR).glob("*.pdf"))


def run_ingestion_streaming(reindex: bool = False) -> Generator[str, None, None]:
    """
    Stesso comportamento di run_ingestion() ma fa yield dei log invece di stamparli.
    Usata dalla UI Streamlit per mostrare il progresso in tempo reale.
    """
    embedder = GeminiEmbedder(id=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)
    vector_db = ChromaDb(
        collection=CHROMA_COLLECTION,
        path=CHROMA_PATH,
        persistent_client=True,
        embedder=embedder,
    )
    if not vector_db.exists():
        vector_db.create()

    pdf_files = list_pdf_files()
    if not pdf_files:
        yield f"Nessun PDF trovato in {DOCUMENTS_DIR}"
        return

    indexed = load_indexed()

    for pdf_path in pdf_files:
        source = pdf_path.name
        current_hash = compute_file_hash(str(pdf_path))

        if not reindex and indexed.get(source) == current_hash:
            yield f"[SKIP] {source} già indicizzato"
            continue

        yield f"[INGEST] {source}"
        corrupted = is_corrupted_pdf(str(pdf_path))

        if not corrupted:
            text_chunks = extract_text_chunks(str(pdf_path))
            yield f"  → {len(text_chunks)} chunk testo"
            _upsert_chunks(vector_db, text_chunks)
        else:
            yield "  ⚠ PDF corrotto — solo visione"

        try:
            vision_chunks = extract_vision_chunks(str(pdf_path))
            yield f"  → {len(vision_chunks)} chunk visione"
            _upsert_chunks(vector_db, vision_chunks)
        except Exception as e:
            yield f"  ✗ Errore visione: {e}"

        indexed[source] = current_hash
        save_indexed(indexed)
        yield f"  ✓ {source} indicizzato"

    yield "Indicizzazione completata."


def run_ingestion(reindex: bool = False) -> None:
    """Indexes all PDFs in DOCUMENTS_DIR. Skips already-indexed files unless reindex=True."""
    for line in run_ingestion_streaming(reindex=reindex):
        print(line)
