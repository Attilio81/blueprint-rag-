# tests/test_admin_tab.py
from pathlib import Path
from unittest.mock import patch


def test_get_document_status_indexed():
    """Un PDF il cui hash coincide con indexed.json è ✅ Indicizzato."""
    mock_pdf = Path("/fake/doc.pdf")
    with patch("admin_tab.list_pdf_files", return_value=[mock_pdf]), \
         patch("admin_tab.compute_file_hash", return_value="hash1"), \
         patch("admin_tab.load_indexed", return_value={"doc.pdf": "hash1"}):
        from admin_tab import get_document_status
        result = get_document_status()
    assert len(result) == 1
    assert result[0]["name"] == "doc.pdf"
    assert "✅" in result[0]["status"]


def test_get_document_status_not_indexed():
    """Un PDF non in indexed.json e non corrotto è ⏳ Non indicizzato."""
    mock_pdf = Path("/fake/new.pdf")
    with patch("admin_tab.list_pdf_files", return_value=[mock_pdf]), \
         patch("admin_tab.compute_file_hash", return_value="newHash"), \
         patch("admin_tab.load_indexed", return_value={}), \
         patch("admin_tab.is_corrupted_pdf", return_value=False):
        from admin_tab import get_document_status
        result = get_document_status()
    assert "⏳" in result[0]["status"]


def test_get_document_status_corrupted():
    """Un PDF non indicizzato e corrotto è ⚠️ Corrotto."""
    mock_pdf = Path("/fake/bad.pdf")
    with patch("admin_tab.list_pdf_files", return_value=[mock_pdf]), \
         patch("admin_tab.compute_file_hash", return_value="badHash"), \
         patch("admin_tab.load_indexed", return_value={}), \
         patch("admin_tab.is_corrupted_pdf", return_value=True):
        from admin_tab import get_document_status
        result = get_document_status()
    assert "⚠️" in result[0]["status"]


def test_get_document_status_empty():
    """Nessun PDF → lista vuota."""
    with patch("admin_tab.list_pdf_files", return_value=[]):
        from admin_tab import get_document_status
        result = get_document_status()
    assert result == []
