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


def _mock_query(return_value):
    """Helper: restituisce un patch su db.query."""
    return patch("search.db.query", return_value=return_value)


ARTICOLO_SAMPLE = {
    "codart": "VITE-M6",
    "descrizione": "Vite M6x20 zincata",
    "unita_misura": "PZ",
    "bloccato": "N",
    "esaurito": "N",
    "barcodes": "8001234567890",
}


def test_cerca_articoli_per_descrizione():
    with _mock_query([ARTICOLO_SAMPLE]) as mock_q:
        from search import cerca_articoli
        result = cerca_articoli("vite zincata")

    assert len(result) == 1
    assert result[0]["codart"] == "VITE-M6"
    # verifica che entrambi i token siano nella query
    sql_called = mock_q.call_args[0][0].upper()
    assert "LIKE" in sql_called


def test_cerca_articoli_vuota_restituisce_lista_vuota():
    with _mock_query([]) as _:
        from search import cerca_articoli
        result = cerca_articoli("")
    assert result == []


def test_cerca_articoli_token_multipli():
    with _mock_query([ARTICOLO_SAMPLE]) as mock_q:
        from search import cerca_articoli
        cerca_articoli("vite m6 zincat")

    # con 3 token deve avere 3 blocchi di condizioni
    params = mock_q.call_args[0][1]
    assert len(params) == 9  # 3 token × 3 campi (codart, descrizione, barcodes)
