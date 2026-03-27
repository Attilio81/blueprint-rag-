"""CatalogoTools — Agno Toolkit per la ricerca nel catalogo interno.

Wrappa le funzioni di mcp_preventivi/search.py come tool Agno nativi,
compatibili con agent.run() sincrono senza necessità di MCPTools async.
"""
import sys
import os
import json

# Aggiunge mcp_preventivi/ al path per importare search.py
_MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "mcp_preventivi")
sys.path.insert(0, os.path.abspath(_MCP_DIR))

from agno.tools import Toolkit
import search


def _fmt(results: list[dict]) -> str:
    """Serializza risultati come JSON compatto (leggibile dal modello)."""
    if not results:
        return "Nessun risultato trovato."
    return json.dumps(results, ensure_ascii=False, indent=2)


class CatalogoTools(Toolkit):
    """Tool per cercare articoli, fornitori e prezzi nel catalogo interno."""

    def __init__(self):
        super().__init__(name="catalogo")
        self.register(self.cerca_articoli_catalogo)
        self.register(self.cerca_per_codice_fornitore)
        self.register(self.confronta_fornitori)
        self.register(self.cerca_fornitori)

    def cerca_articoli_catalogo(self, query: str) -> str:
        """Cerca articoli nel catalogo interno per codice, descrizione o EAN/barcode.
        Usa ricerca multi-token: ogni parola deve essere presente.
        Esempio: cerca_articoli_catalogo('vite m6 zincata') oppure cerca_articoli_catalogo('8001234567890')
        """
        return _fmt(search.cerca_articoli(query))

    def cerca_per_codice_fornitore(self, codice: str, conto_fornitore: int = 0) -> str:
        """Trova un articolo del catalogo partendo dal codice riportato nel preventivo del fornitore.
        Usare quando il preventivo contiene un codice articolo del fornitore (es. 'ROS-VM6-20').
        Se conto_fornitore > 0, filtra per quel fornitore specifico.
        """
        cf = conto_fornitore if conto_fornitore > 0 else None
        return _fmt(search.cerca_per_codice_fornitore(codice, cf))

    def confronta_fornitori(self, codart: str) -> str:
        """Confronta i prezzi di acquisto di un articolo tra tutti i fornitori del catalogo.
        Restituisce prezzo, codice fornitore e scadenza per ogni fornitore.
        Usare dopo aver trovato il codart con cerca_articoli_catalogo o cerca_per_codice_fornitore.
        Esempio: confronta_fornitori('VITE-M6')
        """
        return _fmt(search.confronta_fornitori(codart))

    def cerca_fornitori(self, query: str) -> str:
        """Cerca fornitori nel catalogo per ragione sociale o P.IVA.
        Esempio: cerca_fornitori('Ferramenta Rossi')
        """
        return _fmt(search.cerca_fornitori(query))
