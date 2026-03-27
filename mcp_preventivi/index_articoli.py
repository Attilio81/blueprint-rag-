# mcp_preventivi/index_articoli.py
"""Script standalone per costruire/aggiornare l'indice embedding degli articoli IAB.
Eseguire una volta, poi al bisogno quando il catalogo articoli cambia.

Uso: python index_articoli.py [--limit N]
  --limit N   indicizza solo i primi N articoli (utile per test)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import db
import embeddings


def main(limit: int | None = None):
    top = f"TOP {limit} " if limit else ""
    print("Carico articoli da v_articoli...")
    articoli = db.query(f"SELECT {top}codart, descrizione, unita_misura, bloccato, esaurito FROM dbo.v_articoli")
    print(f"Trovati {len(articoli)} articoli.")
    if len(articoli) > 500:
        print(f"ATTENZIONE: {len(articoli)} articoli da indicizzare. Stima: ~{len(articoli) // 60 + 1} minuti.")

    print("Genero embedding e indicizzando in ChromaDB...")
    n = embeddings.index_articoli(articoli)
    print(f"Indicizzati {n} articoli in '{embeddings.CHROMA_PATH}'.")


if __name__ == "__main__":
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])
    main(limit)
