# MCP Preventivi — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Server MCP Python (FastMCP) che espone 7 tool read-only per cercare articoli, fornitori, clienti e prezzi nel DB IAB, inclusa ricerca semantica via embeddings.

**Architecture:** `search.py` contiene tutta la logica di query sulle viste SQL; `server.py` è solo il wiring FastMCP; `db.py` gestisce la connessione pyodbc. Le viste SQL sono già create nel DB (vedi `mcp_preventivi/views.sql`).

**Tech Stack:** Python 3.10+, FastMCP (`mcp[cli]`), pyodbc, agno (GeminiEmbedder), chromadb, python-dotenv, pytest

---

## File Map

| File | Responsabilità |
|------|---------------|
| `mcp_preventivi/requirements.txt` | Dipendenze del server MCP |
| `mcp_preventivi/.env.example` | Template variabili d'ambiente |
| `mcp_preventivi/db.py` | Connessione pyodbc + helper `query()` |
| `mcp_preventivi/search.py` | Logica di tutti i 7 tool (pura Python, nessuna dipendenza FastMCP) |
| `mcp_preventivi/embeddings.py` | Gestione indice ChromaDB per `cerca_articoli_simili` |
| `mcp_preventivi/server.py` | FastMCP wiring — decora le funzioni di `search.py` |
| `mcp_preventivi/index_articoli.py` | Script one-shot per costruire l'indice embedding |
| `mcp_preventivi/tests/__init__.py` | Package marker |
| `mcp_preventivi/tests/test_search.py` | Unit test con mock su `db.query` |
| `mcp_preventivi/tests/test_embeddings.py` | Unit test con mock su ChromaDB |

---

## Task 1: Setup struttura progetto

**Files:**
- Create: `mcp_preventivi/requirements.txt`
- Create: `mcp_preventivi/.env.example`
- Create: `mcp_preventivi/__init__.py`
- Create: `mcp_preventivi/tests/__init__.py`

- [ ] **Step 1: Crea requirements.txt**

```
# mcp_preventivi/requirements.txt
mcp[cli]>=1.0.0
pyodbc>=5.0.0
python-dotenv>=1.0.0
agno>=1.0.0
chromadb>=0.5.0
google-generativeai>=0.5.0
pytest>=8.0.0
```

- [ ] **Step 2: Crea .env.example**

```
# mcp_preventivi/.env.example
# Stringa di connessione pyodbc al DB IAB
# Formato Windows Auth:
# DRIVER={ODBC Driver 17 for SQL Server};SERVER=nome_server;DATABASE=nome_db;Trusted_Connection=yes
# Formato SQL Auth:
# DRIVER={ODBC Driver 17 for SQL Server};SERVER=nome_server;DATABASE=nome_db;UID=utente;PWD=password
IAB_DB_CONNECTION_STRING=

# Google API key per gli embedding (uguale a quella in rag_preventivi/.env)
GOOGLE_API_KEY=
```

- [ ] **Step 3: Crea __init__.py vuoti**

`mcp_preventivi/__init__.py` — file vuoto
`mcp_preventivi/tests/__init__.py` — file vuoto

- [ ] **Step 4: Installa dipendenze**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/mcp_preventivi"
pip install -r requirements.txt
```

Atteso: nessun errore, `mcp` e `pyodbc` installati.

- [ ] **Step 5: Crea .env copiando .env.example e riempiendo le variabili**

```bash
cp mcp_preventivi/.env.example mcp_preventivi/.env
```

Poi apri `mcp_preventivi/.env` e inserisci:
- `IAB_DB_CONNECTION_STRING` con la stessa stringa di connessione usata dal server MCP dbIAB esistente
- `GOOGLE_API_KEY` copiata da `rag_preventivi/.env`

- [ ] **Step 6: Commit**

```bash
git add mcp_preventivi/requirements.txt mcp_preventivi/.env.example mcp_preventivi/__init__.py mcp_preventivi/tests/__init__.py
git commit -m "feat(mcp-preventivi): setup struttura progetto e dipendenze"
```

---

## Task 2: DB connection helper

**Files:**
- Create: `mcp_preventivi/db.py`
- Create: `mcp_preventivi/tests/test_search.py` (prima sezione)

- [ ] **Step 1: Scrivi il test per db.query**

```python
# mcp_preventivi/tests/test_search.py
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
```

- [ ] **Step 2: Esegui il test — deve fallire**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/mcp_preventivi"
python -m pytest tests/test_search.py::test_query_returns_list_of_dicts -v
```

Atteso: `FAILED` con `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 3: Crea db.py**

```python
# mcp_preventivi/db.py
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def get_connection() -> pyodbc.Connection:
    conn_str = os.environ["IAB_DB_CONNECTION_STRING"]
    return pyodbc.connect(conn_str)


def query(sql: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
```

- [ ] **Step 4: Esegui i test — devono passare**

```bash
python -m pytest tests/test_search.py -v
```

Atteso: `PASSED` su entrambi i test

- [ ] **Step 5: Commit**

```bash
git add mcp_preventivi/db.py mcp_preventivi/tests/test_search.py
git commit -m "feat(mcp-preventivi): db connection helper con query()"
```

---

## Task 3: Tool cerca_articoli

**Files:**
- Create: `mcp_preventivi/search.py`
- Modify: `mcp_preventivi/tests/test_search.py`

- [ ] **Step 1: Aggiungi test per cerca_articoli**

Aggiungi in fondo a `mcp_preventivi/tests/test_search.py`:

```python
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
```

- [ ] **Step 2: Esegui — deve fallire**

```bash
python -m pytest tests/test_search.py::test_cerca_articoli_per_descrizione -v
```

Atteso: `FAILED` con `ModuleNotFoundError: No module named 'search'`

- [ ] **Step 3: Crea search.py con cerca_articoli**

```python
# mcp_preventivi/search.py
import db


def _like_tokens(tokens: list[str], fields: list[str]) -> tuple[str, list]:
    """Costruisce condizioni multi-token LIKE.

    Per ogni token produce: (field1 LIKE ? OR field2 LIKE ? ...)
    I blocchi sono collegati con AND.
    Restituisce (where_clause, params_list).
    """
    blocks = []
    params = []
    for token in tokens:
        like = f"%{token}%"
        field_conditions = " OR ".join(
            f"UPPER({f}) LIKE UPPER(?)" for f in fields
        )
        blocks.append(f"({field_conditions})")
        params.extend([like] * len(fields))
    return " AND ".join(blocks), params


def cerca_articoli(query_text: str) -> list[dict]:
    """Cerca articoli per codice IAB, descrizione o EAN/barcode (multi-token LIKE)."""
    tokens = query_text.strip().split()
    if not tokens:
        return []
    where, params = _like_tokens(tokens, ["codart", "descrizione", "ISNULL(barcodes,'')"])
    sql = f"SELECT TOP 50 * FROM dbo.v_articoli WHERE {where} ORDER BY codart"
    return db.query(sql, tuple(params))
```

- [ ] **Step 4: Esegui test**

```bash
python -m pytest tests/test_search.py -v
```

Atteso: tutti e 4 i test `PASSED`

- [ ] **Step 5: Commit**

```bash
git add mcp_preventivi/search.py mcp_preventivi/tests/test_search.py
git commit -m "feat(mcp-preventivi): search.py con cerca_articoli multi-token LIKE"
```

---

## Task 4: Tool cerca_fornitori e cerca_clienti

**Files:**
- Modify: `mcp_preventivi/search.py`
- Modify: `mcp_preventivi/tests/test_search.py`

- [ ] **Step 1: Aggiungi test**

```python
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


def test_cerca_clienti_vuota():
    with _mock_query([]) as _:
        from search import cerca_clienti
        assert cerca_clienti("") == []
```

- [ ] **Step 2: Esegui — deve fallire**

```bash
python -m pytest tests/test_search.py::test_cerca_fornitori -v
```

Atteso: `FAILED` con `ImportError` su `cerca_fornitori`

- [ ] **Step 3: Aggiungi a search.py**

```python
def cerca_fornitori(query_text: str) -> list[dict]:
    """Cerca fornitori per ragione sociale o P.IVA (multi-token LIKE)."""
    tokens = query_text.strip().split()
    if not tokens:
        return []
    where, params = _like_tokens(
        tokens, ["ragione_sociale", "ISNULL(partita_iva,'')"]
    )
    sql = f"SELECT TOP 50 * FROM dbo.v_fornitori WHERE {where} ORDER BY ragione_sociale"
    return db.query(sql, tuple(params))


def cerca_clienti(query_text: str) -> list[dict]:
    """Cerca clienti per ragione sociale o P.IVA (multi-token LIKE)."""
    tokens = query_text.strip().split()
    if not tokens:
        return []
    where, params = _like_tokens(
        tokens, ["ragione_sociale", "ISNULL(partita_iva,'')"]
    )
    sql = f"SELECT TOP 50 * FROM dbo.v_clienti WHERE {where} ORDER BY ragione_sociale"
    return db.query(sql, tuple(params))
```

- [ ] **Step 4: Esegui test**

```bash
python -m pytest tests/test_search.py -v
```

Atteso: tutti i test `PASSED`

- [ ] **Step 5: Commit**

```bash
git add mcp_preventivi/search.py mcp_preventivi/tests/test_search.py
git commit -m "feat(mcp-preventivi): aggiungi cerca_fornitori e cerca_clienti"
```

---

## Task 5: Tool get_prezzi_fornitore

**Files:**
- Modify: `mcp_preventivi/search.py`
- Modify: `mcp_preventivi/tests/test_search.py`

- [ ] **Step 1: Aggiungi test**

```python
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
```

- [ ] **Step 2: Esegui — deve fallire**

```bash
python -m pytest tests/test_search.py::test_get_prezzi_fornitore -v
```

Atteso: `FAILED` con `ImportError`

- [ ] **Step 3: Aggiungi a search.py**

```python
def get_prezzi_fornitore(codart: str) -> list[dict]:
    """Prezzi d'acquisto validi oggi per un articolo, per tutti i fornitori."""
    sql = """
        SELECT *
        FROM dbo.v_prezzi_acquisto
        WHERE codart = ?
        ORDER BY prezzo
    """
    return db.query(sql, (codart,))
```

- [ ] **Step 4: Esegui test**

```bash
python -m pytest tests/test_search.py -v
```

Atteso: tutti i test `PASSED`

- [ ] **Step 5: Commit**

```bash
git add mcp_preventivi/search.py mcp_preventivi/tests/test_search.py
git commit -m "feat(mcp-preventivi): aggiungi get_prezzi_fornitore"
```

---

## Task 6: Tool cerca_per_codice_fornitore

**Files:**
- Modify: `mcp_preventivi/search.py`
- Modify: `mcp_preventivi/tests/test_search.py`

- [ ] **Step 1: Aggiungi test**

```python
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
```

- [ ] **Step 2: Esegui — deve fallire**

```bash
python -m pytest tests/test_search.py::test_cerca_per_codice_fornitore_senza_filtro -v
```

Atteso: `FAILED`

- [ ] **Step 3: Aggiungi a search.py**

```python
def cerca_per_codice_fornitore(
    codice: str, conto_fornitore: int | None = None
) -> list[dict]:
    """Trova articoli IAB dal codice riportato nel preventivo del fornitore."""
    if conto_fornitore is not None:
        sql = """
            SELECT * FROM dbo.v_codici_fornitore
            WHERE codice_fornitore = ? AND fornitore_conto = ?
            ORDER BY fornitore_nome
        """
        return db.query(sql, (codice, conto_fornitore))
    sql = """
        SELECT * FROM dbo.v_codici_fornitore
        WHERE codice_fornitore = ?
        ORDER BY fornitore_nome
    """
    return db.query(sql, (codice,))
```

- [ ] **Step 4: Esegui test**

```bash
python -m pytest tests/test_search.py -v
```

Atteso: tutti i test `PASSED`

- [ ] **Step 5: Commit**

```bash
git add mcp_preventivi/search.py mcp_preventivi/tests/test_search.py
git commit -m "feat(mcp-preventivi): aggiungi cerca_per_codice_fornitore"
```

---

## Task 7: Tool confronta_fornitori

**Files:**
- Modify: `mcp_preventivi/search.py`
- Modify: `mcp_preventivi/tests/test_search.py`

- [ ] **Step 1: Aggiungi test**

```python
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
```

- [ ] **Step 2: Esegui — deve fallire**

```bash
python -m pytest tests/test_search.py::test_confronta_fornitori -v
```

Atteso: `FAILED`

- [ ] **Step 3: Aggiungi a search.py**

```python
def confronta_fornitori(codart: str) -> list[dict]:
    """Tabella comparativa fornitori: prezzo + codice fornitore per articolo."""
    sql = """
        SELECT
            p.fornitore_nome,
            p.fornitore_conto,
            c.codice_fornitore,
            p.prezzo,
            p.unita_misura,
            p.quantita_da,
            p.quantita_a,
            p.data_scadenza
        FROM dbo.v_prezzi_acquisto p
        LEFT JOIN dbo.v_codici_fornitore c
            ON  p.codart           = c.codart
            AND p.fornitore_conto  = c.fornitore_conto
        WHERE p.codart = ?
        ORDER BY p.prezzo
    """
    return db.query(sql, (codart,))
```

- [ ] **Step 4: Esegui tutti i test**

```bash
python -m pytest tests/test_search.py -v
```

Atteso: tutti i test `PASSED`

- [ ] **Step 5: Commit**

```bash
git add mcp_preventivi/search.py mcp_preventivi/tests/test_search.py
git commit -m "feat(mcp-preventivi): aggiungi confronta_fornitori con LEFT JOIN viste"
```

---

## Task 8: FastMCP server wiring

**Files:**
- Create: `mcp_preventivi/server.py`

- [ ] **Step 1: Crea server.py**

```python
# mcp_preventivi/server.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP
import search

mcp = FastMCP("mcp-preventivi")


@mcp.tool()
def cerca_articoli(query: str) -> list:
    """Cerca articoli nel DB IAB per codice, descrizione o EAN/barcode.
    Usa multi-token LIKE: ogni parola del parametro query deve essere presente.
    Esempio: cerca_articoli('vite m6 zincata')
    """
    return search.cerca_articoli(query)


@mcp.tool()
def cerca_articoli_simili(query: str, n_risultati: int = 10) -> list:
    """Ricerca semantica articoli: trova descrizioni simili anche con parole diverse.
    Esempio: 'vite zincata' trova anche 'vite galvanizzata'.
    Richiede che l'indice sia stato costruito con index_articoli.py.
    """
    return search.cerca_articoli_simili(query, n_risultati)


@mcp.tool()
def cerca_fornitori(query: str) -> list:
    """Cerca fornitori per ragione sociale o P.IVA (multi-token LIKE)."""
    return search.cerca_fornitori(query)


@mcp.tool()
def cerca_clienti(query: str) -> list:
    """Cerca clienti per ragione sociale o P.IVA (multi-token LIKE).
    Restituisce anche il codice listino assegnato al cliente.
    """
    return search.cerca_clienti(query)


@mcp.tool()
def get_prezzi_fornitore(codart: str) -> list:
    """Restituisce tutti i prezzi d'acquisto validi oggi per un articolo.
    Un record per fornitore, ordinati per prezzo crescente.
    """
    return search.get_prezzi_fornitore(codart)


@mcp.tool()
def cerca_per_codice_fornitore(codice: str, conto_fornitore: int = 0) -> list:
    """Trova l'articolo IAB dal codice riportato nel preventivo del fornitore.
    Se conto_fornitore > 0, filtra per quel fornitore specifico.
    """
    cf = conto_fornitore if conto_fornitore > 0 else None
    return search.cerca_per_codice_fornitore(codice, cf)


@mcp.tool()
def confronta_fornitori(codart: str) -> list:
    """Tabella comparativa: tutti i fornitori con prezzo + codice articolo fornitore.
    Usare dopo aver trovato codart con cerca_articoli o cerca_per_codice_fornitore.
    """
    return search.confronta_fornitori(codart)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: Verifica che il server si avvii senza errori**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/mcp_preventivi"
python server.py --help
```

Atteso: nessun errore, output FastMCP con le opzioni disponibili

- [ ] **Step 3: Commit**

```bash
git add mcp_preventivi/server.py
git commit -m "feat(mcp-preventivi): FastMCP server con 7 tool wired"
```

---

## Task 9: Indice embedding (embeddings.py + index_articoli.py)

**Files:**
- Create: `mcp_preventivi/embeddings.py`
- Create: `mcp_preventivi/index_articoli.py`
- Create: `mcp_preventivi/tests/test_embeddings.py`

- [ ] **Step 1: Scrivi test per embeddings.py**

```python
# mcp_preventivi/tests/test_embeddings.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock


def test_cerca_simili_restituisce_lista():
    mock_results = MagicMock()
    mock_results.ids = [["VITE-M6", "DADO-M6"]]
    mock_results.distances = [[0.1, 0.3]]
    mock_results.metadatas = [[
        {"codart": "VITE-M6", "descrizione": "Vite M6x20 zincata", "unita_misura": "PZ", "bloccato": "N", "esaurito": "N"},
        {"codart": "DADO-M6", "descrizione": "Dado M6 zincato", "unita_misura": "PZ", "bloccato": "N", "esaurito": "N"},
    ]]

    mock_collection = MagicMock()
    mock_collection.query.return_value = mock_results

    mock_embedder = MagicMock()
    mock_embedder.get_embedding.return_value = [0.1] * 3072

    with patch("embeddings._get_collection", return_value=mock_collection), \
         patch("embeddings._get_embedder", return_value=mock_embedder):
        from embeddings import cerca_simili
        result = cerca_simili("vite m6", n_risultati=2)

    assert len(result) == 2
    assert result[0]["codart"] == "VITE-M6"
    assert "score" in result[0]
    assert result[0]["score"] < result[1]["score"]  # distanza crescente
```

- [ ] **Step 2: Esegui — deve fallire**

```bash
python -m pytest tests/test_embeddings.py -v
```

Atteso: `FAILED`

- [ ] **Step 3: Crea embeddings.py**

```python
# mcp_preventivi/embeddings.py
import os
import chromadb
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

COLLECTION_NAME = "iab_articoli"
CHROMA_PATH = os.path.join(os.path.dirname(__file__), ".chroma_iab")
EMBEDDING_MODEL = "gemini-embedding-2-preview"
EMBEDDING_DIMENSIONS = 3072


def _get_embedder():
    from agno.knowledge.embedder.google import GeminiEmbedder
    return GeminiEmbedder(id=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)


def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)


def cerca_simili(query_text: str, n_risultati: int = 10) -> list[dict]:
    """Ricerca semantica per descrizione simile usando embedding GeminiEmbedder."""
    embedder = _get_embedder()
    collection = _get_collection()
    query_embedding = embedder.get_embedding(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_risultati,
    )
    output = []
    for i, metadata in enumerate(results["metadatas"][0]):
        output.append({**metadata, "score": results["distances"][0][i]})
    return output


def index_articoli(articoli: list[dict]) -> int:
    """Indicizza una lista di articoli in ChromaDB. Restituisce il numero indicizzato."""
    embedder = _get_embedder()
    collection = _get_collection()
    ids, embeddings, metadatas = [], [], []
    for art in articoli:
        testo = f"{art['codart']} {art['descrizione']}"
        embedding = embedder.get_embedding(testo)
        ids.append(art["codart"])
        embeddings.append(embedding)
        metadatas.append({
            "codart": art["codart"],
            "descrizione": art["descrizione"],
            "unita_misura": art.get("unita_misura", ""),
            "bloccato": art.get("bloccato", "N"),
            "esaurito": art.get("esaurito", "N"),
        })
    collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
    return len(ids)
```

- [ ] **Step 4: Esegui test**

```bash
python -m pytest tests/test_embeddings.py -v
```

Atteso: `PASSED`

- [ ] **Step 5: Crea index_articoli.py**

```python
# mcp_preventivi/index_articoli.py
"""Script standalone per costruire/aggiornare l'indice embedding degli articoli IAB.
Eseguire una volta, poi al bisogno quando il catalogo articoli cambia.

Uso: python index_articoli.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import db
import embeddings


def main():
    print("Carico articoli da v_articoli...")
    articoli = db.query("SELECT codart, descrizione, unita_misura, bloccato, esaurito FROM dbo.v_articoli")
    print(f"Trovati {len(articoli)} articoli.")

    print("Genero embedding e indicizzro in ChromaDB...")
    n = embeddings.index_articoli(articoli)
    print(f"Indicizzati {n} articoli in '{embeddings.CHROMA_PATH}'.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Commit**

```bash
git add mcp_preventivi/embeddings.py mcp_preventivi/index_articoli.py mcp_preventivi/tests/test_embeddings.py
git commit -m "feat(mcp-preventivi): indice embedding articoli con GeminiEmbedder + ChromaDB"
```

---

## Task 10: Tool cerca_articoli_simili

**Files:**
- Modify: `mcp_preventivi/search.py`
- Modify: `mcp_preventivi/tests/test_search.py`

- [ ] **Step 1: Aggiungi test**

```python
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
```

- [ ] **Step 2: Esegui — deve fallire**

```bash
python -m pytest tests/test_search.py::test_cerca_articoli_simili -v
```

Atteso: `FAILED`

- [ ] **Step 3: Aggiungi a search.py** (in cima aggiungere l'import)

All'inizio di `search.py` aggiungi dopo `import db`:
```python
import embeddings
```

Poi in fondo al file aggiungi:
```python
def cerca_articoli_simili(query_text: str, n_risultati: int = 10) -> list[dict]:
    """Ricerca semantica articoli: trova descrizioni simili anche con sinonimi.
    Richiede indice costruito con index_articoli.py.
    """
    return embeddings.cerca_simili(query_text, n_risultati)
```

- [ ] **Step 4: Esegui tutti i test**

```bash
python -m pytest tests/ -v
```

Atteso: tutti i test `PASSED`

- [ ] **Step 5: Commit**

```bash
git add mcp_preventivi/search.py mcp_preventivi/tests/test_search.py
git commit -m "feat(mcp-preventivi): aggiungi cerca_articoli_simili con embedding semantico"
```

---

## Task 11: Registra server MCP in Claude Code

**Files:**
- Modify: `C:/Progetti Pilota/EsploraPreventivi/.claude/settings.local.json`

- [ ] **Step 1: Aggiungi il server MCP alla configurazione**

Apri `.claude/settings.local.json` e aggiungi la sezione `mcpServers` (o aggiungila dentro quella esistente se già presente):

```json
{
  "mcpServers": {
    "mcp-preventivi": {
      "command": "python",
      "args": ["C:/Progetti Pilota/EsploraPreventivi/mcp_preventivi/server.py"],
      "env": {
        "IAB_DB_CONNECTION_STRING": "<incollare qui la stringa di connessione>",
        "GOOGLE_API_KEY": "<incollare qui la API key>"
      }
    }
  },
  "permissions": {
    "allow": [ ... ]
  }
}
```

In alternativa, non mettere le credenziali nel JSON e usare il file `.env` già creato nel Task 1 (il `load_dotenv` in `db.py` lo leggerà automaticamente).

- [ ] **Step 2: Riavvia Claude Code e verifica che il server MCP sia visibile**

Dopo il riavvio, in una nuova sessione Claude Code il server `mcp-preventivi` deve apparire nei tool disponibili. Prova:

```
Usa il tool cerca_fornitori con query="rossi"
```

Atteso: risposta con lista fornitori dal DB IAB

- [ ] **Step 3: Commit finale**

```bash
git add .claude/settings.local.json
git commit -m "feat(mcp-preventivi): registra server MCP in Claude Code settings"
```

---

## Verifica finale

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/mcp_preventivi"
python -m pytest tests/ -v
```

Atteso: tutti i test `PASSED`, zero errori.
