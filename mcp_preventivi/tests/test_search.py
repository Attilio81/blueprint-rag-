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


FORNITORE_SAMPLE = {
    "conto": 9010001,
    "ragione_sociale": "Ferramenta Rossi SRL",
    "partita_iva": "01234567890",
    "email": "info@rossi.it",
    "telefono": "051123456",
    "citta": "Bologna",
}

CLIENTE_SAMPLE = {
    "conto": 5010001,
    "ragione_sociale": "Edilizia Bianchi SPA",
    "partita_iva": "09876543210",
    "email": "acquisti@bianchi.it",
    "codice_listino": 1,
    "nome_listino": "Listino Base",
}


def test_cerca_fornitori():
    with _mock_query([FORNITORE_SAMPLE]) as mock_q:
        from search import cerca_fornitori
        result = cerca_fornitori("rossi")

    assert result[0]["ragione_sociale"] == "Ferramenta Rossi SRL"
    assert "LIKE" in mock_q.call_args[0][0].upper()
    assert "v_fornitori" in mock_q.call_args[0][0].lower()


def test_cerca_fornitori_per_piva():
    with _mock_query([FORNITORE_SAMPLE]) as mock_q:
        from search import cerca_fornitori
        cerca_fornitori("01234567890")

    params = mock_q.call_args[0][1]
    assert "%01234567890%" in params


def test_cerca_clienti():
    with _mock_query([CLIENTE_SAMPLE]) as mock_q:
        from search import cerca_clienti
        result = cerca_clienti("bianchi")

    assert result[0]["nome_listino"] == "Listino Base"
    assert "v_clienti" in mock_q.call_args[0][0].lower()


def test_cerca_clienti_vuota():
    with _mock_query([]) as _:
        from search import cerca_clienti
        assert cerca_clienti("") == []


PREZZO_SAMPLE = {
    "codart": "VITE-M6",
    "descrizione_articolo": "Vite M6x20 zincata",
    "fornitore_conto": 9010001,
    "fornitore_nome": "Ferramenta Rossi SRL",
    "fornitore_piva": "01234567890",
    "prezzo": 0.25,
    "codice_listino": 1,
    "nome_listino": "Listino Base",
    "unita_misura": "PZ",
    "quantita_da": 0.0,
    "quantita_a": 9999999999.0,
    "prezzo_netto": "N",
    "data_inizio": "2024-01-01",
    "data_scadenza": "2099-12-31",
}


def test_get_prezzi_fornitore():
    with _mock_query([PREZZO_SAMPLE]) as mock_q:
        from search import get_prezzi_fornitore
        result = get_prezzi_fornitore("VITE-M6")

    assert result[0]["prezzo"] == 0.25
    assert result[0]["fornitore_nome"] == "Ferramenta Rossi SRL"
    sql = mock_q.call_args[0][0]
    assert "v_prezzi_acquisto" in sql
    assert mock_q.call_args[0][1] == ("VITE-M6",)


def test_get_prezzi_fornitore_nessun_risultato():
    with _mock_query([]) as _:
        from search import get_prezzi_fornitore
        assert get_prezzi_fornitore("INESISTENTE") == []


CODICE_FORNITORE_SAMPLE = {
    "codart": "VITE-M6",
    "descrizione_articolo": "Vite M6x20 zincata",
    "fornitore_conto": 9010001,
    "fornitore_nome": "Ferramenta Rossi SRL",
    "fornitore_piva": "01234567890",
    "codice_fornitore": "ROS-VM6-20",
    "note": "",
}


def test_cerca_per_codice_fornitore_senza_filtro():
    with _mock_query([CODICE_FORNITORE_SAMPLE]) as mock_q:
        from search import cerca_per_codice_fornitore
        result = cerca_per_codice_fornitore("ROS-VM6-20")

    assert result[0]["codart"] == "VITE-M6"
    params = mock_q.call_args[0][1]
    assert "ROS-VM6-20" in params
    assert 9010001 not in params  # nessun filtro fornitore


def test_cerca_per_codice_fornitore_con_filtro_fornitore():
    with _mock_query([CODICE_FORNITORE_SAMPLE]) as mock_q:
        from search import cerca_per_codice_fornitore
        result = cerca_per_codice_fornitore("ROS-VM6-20", conto_fornitore=9010001)

    params = mock_q.call_args[0][1]
    assert 9010001 in params


CONFRONTO_SAMPLE = [
    {
        "fornitore_nome": "Ferramenta Rossi SRL",
        "fornitore_conto": 9010001,
        "codice_fornitore": "ROS-VM6-20",
        "prezzo": 0.25,
        "unita_misura": "PZ",
        "quantita_da": 0.0,
        "quantita_a": 9999999999.0,
        "data_scadenza": "2099-12-31",
    },
    {
        "fornitore_nome": "Bulloneria Verdi SNC",
        "fornitore_conto": 9020001,
        "codice_fornitore": None,
        "prezzo": 0.22,
        "unita_misura": "PZ",
        "quantita_da": 0.0,
        "quantita_a": 9999999999.0,
        "data_scadenza": "2099-12-31",
    },
]


def test_confronta_fornitori():
    with _mock_query(CONFRONTO_SAMPLE) as mock_q:
        from search import confronta_fornitori
        result = confronta_fornitori("VITE-M6")

    assert len(result) == 2
    assert result[0]["prezzo"] == 0.25
    sql = mock_q.call_args[0][0]
    assert "v_prezzi_acquisto" in sql
    assert "v_codici_fornitore" in sql
    assert mock_q.call_args[0][1] == ("VITE-M6",)


def test_confronta_fornitori_nessun_fornitore():
    with _mock_query([]) as _:
        from search import confronta_fornitori
        assert confronta_fornitori("INESISTENTE") == []


def test_cerca_articoli_simili():
    sample = [
        {"codart": "VITE-M6", "descrizione": "Vite M6x20 zincata",
         "unita_misura": "PZ", "bloccato": "N", "esaurito": "N", "score": 0.1},
    ]
    with patch("search.embeddings.cerca_simili", return_value=sample) as mock_emb:
        from search import cerca_articoli_simili
        result = cerca_articoli_simili("vite zincata", n_risultati=5)

    assert result[0]["score"] == 0.1
    mock_emb.assert_called_once_with("vite zincata", 5)
