# tests/test_image_extractor.py
import pytest
from unittest.mock import patch
from pathlib import Path
from ingestion.image_extractor import describe_page_with_vision, extract_vision_chunks

SAMPLE_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "ONICE.pdf"

MOCK_DESCRIPTION = "Scheda prodotto fioriera ONICE. Misure: Ø800mm H480mm 278kg."


def test_extract_vision_chunks_returns_list():
    with patch("ingestion.image_extractor.describe_page_with_vision", return_value=MOCK_DESCRIPTION):
        chunks = extract_vision_chunks(str(SAMPLE_PDF))
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_vision_chunk_has_required_keys():
    with patch("ingestion.image_extractor.describe_page_with_vision", return_value=MOCK_DESCRIPTION):
        chunks = extract_vision_chunks(str(SAMPLE_PDF))
    chunk = chunks[0]
    assert chunk["type"] == "vision"
    assert "content" in chunk
    assert "source" in chunk
    assert "page" in chunk
    assert MOCK_DESCRIPTION in chunk["content"]


def test_empty_vision_description_skipped():
    with patch("ingestion.image_extractor.describe_page_with_vision", return_value=""):
        chunks = extract_vision_chunks(str(SAMPLE_PDF))
    assert len(chunks) == 0
