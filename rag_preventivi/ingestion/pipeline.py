# ingestion/pipeline.py
import hashlib
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.document import Document
from ingestion.text_extractor import extract_text_chunks, is_corrupted_pdf
from ingestion.image_extractor import extract_vision_chunks
from config import (
    DOCUMENTS_DIR, INDEXED_FILE, EMBEDDING_MODEL,
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
        vector_db.upsert(documents=documents)


def list_pdf_files() -> list:
    """Returns a sorted list of PDF paths from the module-level DOCUMENTS_DIR."""
    return sorted(Path(DOCUMENTS_DIR).glob("*.pdf"))


def run_ingestion(reindex: bool = False) -> None:
    """
    Indexes all PDFs in DOCUMENTS_DIR.
    Skips already-indexed files unless reindex=True.
    """
    embedder = GeminiEmbedder(id=EMBEDDING_MODEL)
    vector_db = ChromaDb(
        collection=CHROMA_COLLECTION,
        path=CHROMA_PATH,
        persistent_client=True,
        embedder=embedder,
    )

    pdf_files = list_pdf_files()
    if not pdf_files:
        print(f"No PDFs found in {DOCUMENTS_DIR}")
        return

    indexed = load_indexed()

    for pdf_path in pdf_files:
        source = pdf_path.name
        current_hash = compute_file_hash(str(pdf_path))

        if not reindex and indexed.get(source) == current_hash:
            print(f"[SKIP] {source} already indexed")
            continue

        print(f"\n[INGEST] {source}")
        corrupted = is_corrupted_pdf(str(pdf_path))

        # Pass 1: text (only if not corrupted)
        if not corrupted:
            text_chunks = extract_text_chunks(str(pdf_path))
            print(f"  -> {len(text_chunks)} text chunks")
            _upsert_chunks(vector_db, text_chunks)
        else:
            print(f"  ! Corrupted PDF encoding -- skipping text, vision only")

        # Pass 2: vision (always)
        try:
            vision_chunks = extract_vision_chunks(str(pdf_path))
            print(f"  -> {len(vision_chunks)} vision chunks")
            _upsert_chunks(vector_db, vision_chunks)
        except Exception as e:
            print(f"  x Vision error for {source}: {e}")

        # Update index
        indexed[source] = current_hash
        save_indexed(indexed)
        print(f"  v {source} indexed")

    print("\nIngestion complete.")
