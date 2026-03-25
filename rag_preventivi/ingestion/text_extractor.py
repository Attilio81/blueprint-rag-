# ingestion/text_extractor.py
import pymupdf
from pathlib import Path
from config import CHUNK_SIZE, CHUNK_OVERLAP, NON_ASCII_THRESHOLD


def is_corrupted_pdf(pdf_path: str) -> bool:
    """Returns True if >30% of extracted characters are non-ASCII."""
    doc = pymupdf.open(pdf_path)
    total_chars = 0
    non_ascii_chars = 0
    for page in doc:
        text = page.get_text()
        total_chars += len(text)
        non_ascii_chars += sum(1 for c in text if ord(c) > 127)
    doc.close()
    if total_chars == 0:
        return True
    return (non_ascii_chars / total_chars) > NON_ASCII_THRESHOLD


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Splits text into chunks with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def extract_text_chunks(pdf_path: str) -> list[dict]:
    """
    Extracts text from a PDF and splits into chunks.
    Returns list of dicts with: content, source, page, type.
    """
    source = Path(pdf_path).name
    doc = pymupdf.open(pdf_path)
    result = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        if not text:
            continue
        for chunk_text in _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP):
            if chunk_text.strip():
                result.append({
                    "content": chunk_text.strip(),
                    "source": source,
                    "page": page_num + 1,
                    "type": "text",
                })
    doc.close()
    return result
