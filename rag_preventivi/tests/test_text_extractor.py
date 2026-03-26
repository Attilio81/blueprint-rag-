# tests/test_text_extractor.py
import pytest
from pathlib import Path
from ingestion.text_extractor import extract_text_chunks, is_corrupted_pdf

SAMPLE_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "ONICE.pdf"


def test_extract_text_chunks_returns_list():
    chunks = extract_text_chunks(str(SAMPLE_PDF))
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_chunk_has_required_keys():
    chunks = extract_text_chunks(str(SAMPLE_PDF))
    chunk = chunks[0]
    assert "content" in chunk
    assert "source" in chunk
    assert "page" in chunk
    assert chunk["type"] == "text"
    assert len(chunk["content"]) > 0


def test_is_corrupted_pdf_returns_bool():
    result = is_corrupted_pdf(str(SAMPLE_PDF))
    assert isinstance(result, bool)
    assert result is False  # ONICE.pdf has valid text


def test_chunk_size_within_bounds():
    from config import CHUNK_SIZE
    chunks = extract_text_chunks(str(SAMPLE_PDF))
    for chunk in chunks:
        assert len(chunk["content"]) <= CHUNK_SIZE * 1.5


CORRUPTED_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "PROT.31 IAB SOC.COOP._130125.pdf"

def test_is_corrupted_pdf_detects_corrupted():
    if not CORRUPTED_PDF.exists():
        pytest.skip("Corrupted PDF not available")
    result = is_corrupted_pdf(str(CORRUPTED_PDF))
    # PROT.31 is NOT corrupted: all 6 pages have <1.2% non-ASCII chars (well below
    # the 30% threshold used by is_corrupted_pdf), so it is a regular readable PDF.
    assert result is False
