# ingestion/text_extractor.py
import pymupdf
from pathlib import Path
from config import CHUNK_SIZE, CHUNK_OVERLAP, NON_ASCII_THRESHOLD


def is_corrupted_pdf(pdf_path: str) -> bool:
    """Returns True if >30% of extracted characters are non-ASCII."""
    doc = pymupdf.open(pdf_path)
    try:
        total_chars = 0
        non_ascii_chars = 0
        for page in doc:
            text = page.get_text()
            total_chars += len(text)
            non_ascii_chars += sum(1 for c in text if ord(c) > 127)
        if total_chars == 0:
            return True
        return (non_ascii_chars / total_chars) > NON_ASCII_THRESHOLD
    finally:
        doc.close()


_SEPARATORS = ["\n\n", "\n", " ", ""]


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Splits text on the coarsest boundary that fits: paragraph, line, word, character."""
    for sep in _SEPARATORS:
        if sep == "":
            chunks, start = [], 0
            while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end].strip())
                start += chunk_size - overlap
            return [c for c in chunks if c]

        parts = [p for p in text.split(sep) if p.strip()]
        if len(parts) <= 1:
            continue

        chunks, current, current_len = [], [], 0
        for part in parts:
            add_len = len(part) + (len(sep) if current else 0)
            if current_len + add_len > chunk_size and current:
                chunks.append(sep.join(current).strip())
                tail, tail_len = [], 0
                for p in reversed(current):
                    extra = len(p) + (len(sep) if tail else 0)
                    if tail_len + extra <= overlap:
                        tail.insert(0, p)
                        tail_len += extra
                    else:
                        break
                current, current_len = tail, tail_len
            current.append(part)
            current_len += len(part) + (len(sep) if len(current) > 1 else 0)

        if current:
            chunks.append(sep.join(current).strip())
        return [c for c in chunks if c]

    return [text] if text.strip() else []


def extract_text_chunks(pdf_path: str) -> list[dict]:
    """
    Extracts text from a PDF and splits into chunks.
    Returns list of dicts with: content, source, page, type.
    """
    source = Path(pdf_path).name
    doc = pymupdf.open(pdf_path)
    result = []
    try:
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
    finally:
        doc.close()
    return result
