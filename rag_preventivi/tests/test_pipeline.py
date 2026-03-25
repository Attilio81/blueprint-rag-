# tests/test_pipeline.py
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from ingestion.pipeline import compute_file_hash, load_indexed, save_indexed, is_already_indexed

SAMPLE_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "ONICE.pdf"


def test_compute_file_hash_is_stable():
    h1 = compute_file_hash(str(SAMPLE_PDF))
    h2 = compute_file_hash(str(SAMPLE_PDF))
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_load_indexed_returns_empty_dict_if_missing():
    result = load_indexed("/nonexistent/path.json")
    assert result == {}


def test_save_and_load_indexed(tmp_path):
    index_file = str(tmp_path / "indexed.json")
    data = {"file.pdf": "abc123"}
    save_indexed(data, index_file)
    loaded = load_indexed(index_file)
    assert loaded == data


def test_is_already_indexed_false_for_new_file(tmp_path):
    index_file = str(tmp_path / "indexed.json")
    assert not is_already_indexed(str(SAMPLE_PDF), index_file)


def test_is_already_indexed_true_after_recording(tmp_path):
    index_file = str(tmp_path / "indexed.json")
    h = compute_file_hash(str(SAMPLE_PDF))
    save_indexed({"ONICE.pdf": h}, index_file)
    assert is_already_indexed(str(SAMPLE_PDF), index_file)


@patch("ingestion.pipeline.extract_text_chunks", return_value=[
    {"content": "Testo di test", "source": "ONICE.pdf", "page": 1, "type": "text"}
])
@patch("ingestion.pipeline.extract_vision_chunks", return_value=[
    {"content": "Descrizione visiva", "source": "ONICE.pdf", "page": 1, "type": "vision"}
])
@patch("ingestion.pipeline.ChromaDb")
@patch("ingestion.pipeline.GeminiEmbedder")
def test_run_ingestion_skips_already_indexed(mock_emb, mock_chroma, mock_vision, mock_text, tmp_path):
    """File already indexed with correct hash → no call to extract_*."""
    index_file = str(tmp_path / "indexed.json")
    h = compute_file_hash(str(SAMPLE_PDF))
    save_indexed({"ONICE.pdf": h}, index_file)

    # Patch load_indexed and DOCUMENTS_DIR at module level.
    # Don't patch INDEXED_FILE directly: it's used as default arg
    # (evaluated at definition time, not call time) → won't change anything.
    # Also patch list_pdf_files to return only ONICE.pdf (the Preventivi folder
    # may contain other PDFs that are not relevant to this test).
    with patch("ingestion.pipeline.load_indexed", return_value={"ONICE.pdf": h}), \
         patch("ingestion.pipeline.DOCUMENTS_DIR", str(SAMPLE_PDF.parent)), \
         patch("ingestion.pipeline.list_pdf_files", return_value=[SAMPLE_PDF]):
        from ingestion.pipeline import run_ingestion
        run_ingestion(reindex=False)

    mock_text.assert_not_called()
    mock_vision.assert_not_called()
