# mcp_preventivi/search.py
import db
import embeddings


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

    blocks = []
    params = []
    for token in tokens:
        like = f"%{token}%"
        # OR: codart LIKE ? OR descrizione LIKE ? OR barcode subquery
        blocks.append(
            "(UPPER(codart) LIKE UPPER(?)"
            " OR UPPER(descrizione) LIKE UPPER(?)"
            " OR EXISTS (SELECT 1 FROM dbo.barcode"
            " WHERE codditt = 'IAB' AND bc_codart = codart AND UPPER(bc_code) LIKE UPPER(?)))"
        )
        params.extend([like, like, like])  # 3 params per token

    where = " AND ".join(blocks)
    sql = f"SELECT TOP 50 * FROM dbo.v_articoli WHERE {where} ORDER BY codart"
    return db.query(sql, tuple(params))


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


def get_prezzi_fornitore(codart: str) -> list[dict]:
    """Prezzi d'acquisto validi oggi per un articolo, per tutti i fornitori."""
    sql = """
        SELECT *
        FROM dbo.v_prezzi_acquisto
        WHERE codart = ?
        ORDER BY prezzo
    """
    return db.query(sql, (codart,))


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


def cerca_articoli_simili(query_text: str, n_risultati: int = 10) -> list[dict]:
    """Ricerca semantica articoli: trova descrizioni simili anche con sinonimi.
    Richiede indice costruito con index_articoli.py.
    """
    return embeddings.cerca_simili(query_text, n_risultati)
