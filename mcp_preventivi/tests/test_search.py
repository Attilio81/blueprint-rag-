import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock


def test_query_returns_list_of_dicts():
    mock_cursor = MagicMock()
    mock_cursor.description = [("codart",), ("descrizione",)]
    mock_cursor.fetchall.return_value = [("ART-001", "Vite M6"), ("ART-002", "Dado M6")]
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor

    with patch("db.get_connection", return_value=mock_conn):
        from db import query
        result = query("SELECT codart, descrizione FROM v_articoli")

    assert result == [
        {"codart": "ART-001", "descrizione": "Vite M6"},
        {"codart": "ART-002", "descrizione": "Dado M6"},
    ]


def test_query_with_params():
    mock_cursor = MagicMock()
    mock_cursor.description = [("codart",)]
    mock_cursor.fetchall.return_value = [("ART-001",)]
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor

    with patch("db.get_connection", return_value=mock_conn):
        from db import query
        result = query("SELECT codart FROM v_articoli WHERE codart = ?", ("ART-001",))

    mock_cursor.execute.assert_called_once_with(
        "SELECT codart FROM v_articoli WHERE codart = ?", ("ART-001",)
    )
    assert result == [{"codart": "ART-001"}]
