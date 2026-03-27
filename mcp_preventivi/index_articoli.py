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
    if len(articoli) > 500:
        print(f"ATTENZIONE: {len(articoli)} articoli da indicizzare. Stima: ~{len(articoli) // 60 + 1} minuti.")

    print("Genero embedding e indicizzando in ChromaDB...")
    n = embeddings.index_articoli(articoli)
    print(f"Indicizzati {n} articoli in '{embeddings.CHROMA_PATH}'.")


if __name__ == "__main__":
    main()
