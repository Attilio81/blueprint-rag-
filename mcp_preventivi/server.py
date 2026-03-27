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
