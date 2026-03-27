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
