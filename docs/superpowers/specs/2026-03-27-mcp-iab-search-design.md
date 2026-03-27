# MCP IAB Search — Design Spec
_Data: 2026-03-27_

## Obiettivo

Server MCP per la ricerca di articoli, fornitori e prezzi nel database IAB. Usato dall'agente RAG per analizzare preventivi ricevuti e trovare fornitori alternativi con prezzi comparativi.

**Caso d'uso principale:** l'agente legge un preventivo PDF, identifica gli articoli (per codice fornitore, barcode o descrizione), e confronta i prezzi con altri fornitori presenti in IAB.

---

## Architettura

```
PDF Preventivo
     │
     ▼
RAG Agent (Agno)
     │  chiama tool MCP
     ▼
MCP Server "iab-search"   ←── Python / FastMCP
     │  SELECT su viste
     ▼
SQL Views (IAB DB)         ←── logica di join incapsulata
     │
     ▼
artico · anagra · listini · codarfo · barcode · tablist
```

Il server MCP è **read-only** e **agnostico allo schema fisico**: tutta la logica di join vive nelle viste SQL. Se cambiano le tabelle, si aggiorna solo la vista.

---

## Struttura file

```
mcp_iab/
  server.py          # FastMCP server — 7 tool
  db.py              # connessione pyodbc (config da config.py esistente)
  embeddings.py      # gestione indice ChromaDB per ricerca semantica
  index_articoli.py  # script one-shot per costruire/aggiornare indice embedding
  views.sql          # DDL per creare le 5 viste nel DB IAB
  requirements.txt
```

---

## Viste SQL (views.sql)

| Vista | Tabelle sorgente | Descrizione |
|-------|-----------------|-------------|
| `v_articoli` | `artico` + `barcode` | Articoli con barcodes aggregati |
| `v_fornitori` | `anagra` (an_tipo='F') | Anagrafica fornitori |
| `v_clienti` | `anagra` (an_tipo='C') + `tablist` | Anagrafica clienti con listino assegnato |
| `v_prezzi_acquisto` | `listini` + `anagra` + `artico` + `tablist` | Prezzi fornitore validi oggi (`lc_datagg <= oggi <= lc_datscad`, `lc_conto > 0`) |
| `v_codici_fornitore` | `codarfo` + `anagra` + `artico` | Mapping codice IAB ↔ codice articolo fornitore |

---

## Tool MCP

### 1. `cerca_articoli(query: str) → list`
Ricerca articoli per codice IAB, descrizione o EAN/barcode.
Strategia: **multi-token LIKE** — split della query in token, condizione OR tra `codart`, `descrizione` e subquery su `barcode.bc_code` (la colonna `barcodes` aggregata non è ricercabile con LIKE).
Vista: `v_articoli` + subquery su `barcode` per la ricerca EAN.
Campi restituiti: `codart`, `descrizione`, `unita_misura`, `bloccato`, `esaurito`, `barcodes`.

### 2. `cerca_articoli_simili(query: str, n_risultati: int = 10) → list`
Ricerca semantica per descrizione simile (es. "vite zincata" trova "vite galvanizzata").
Strategia: **embedding similarity** — query embeddata con GeminiEmbedder, ricerca su collezione ChromaDB `iab_articoli`.
Richiede che l'indice sia stato costruito con `index_articoli.py`.
Campi restituiti: stessi di `cerca_articoli` + `score` di similarità.

### 3. `cerca_fornitori(query: str) → list`
Ricerca fornitori per ragione sociale o P.IVA. Multi-token LIKE.
Vista: `v_fornitori`.
Campi restituiti: `conto`, `ragione_sociale`, `partita_iva`, `email`, `telefono`, `citta`.

### 4. `cerca_clienti(query: str) → list`
Ricerca clienti per ragione sociale o P.IVA. Multi-token LIKE.
Vista: `v_clienti`.
Campi restituiti: `conto`, `ragione_sociale`, `partita_iva`, `email`, `codice_listino`, `nome_listino`.

### 5. `get_prezzi_fornitore(codart: str) → list`
Restituisce tutti i prezzi d'acquisto validi oggi per un articolo, uno per fornitore.
Vista: `v_prezzi_acquisto`.
Campi restituiti: `fornitore_conto`, `fornitore_nome`, `prezzo`, `unita_misura`, `quantita_da`, `quantita_a`, `data_scadenza`, `nome_listino`.

### 6. `cerca_per_codice_fornitore(codice: str, conto_fornitore: int | None = None) → list`
Trova articoli IAB dal codice riportato nel preventivo del fornitore.
Ricerca esatta su `codice_fornitore`, opzionalmente filtrata per fornitore.
Vista: `v_codici_fornitore`.
Campi restituiti: `codart`, `descrizione_articolo`, `fornitore_conto`, `fornitore_nome`, `codice_fornitore`, `note`.

### 7. `confronta_fornitori(codart: str) → list`
Tabella comparativa: per ogni fornitore dell'articolo restituisce prezzo + codice fornitore.
Join in Python tra risultati di `v_prezzi_acquisto` e `v_codici_fornitore`.
Campi restituiti: `fornitore_nome`, `codice_fornitore`, `prezzo`, `quantita_da`, `quantita_a`, `data_scadenza`.

---

## Flusso tipico agente RAG

```
1. Legge preventivo PDF → trova "cod. fornitore XYZ, desc. 'vite m6 zinc.', €10"
2. cerca_per_codice_fornitore("XYZ")  →  ar_codart = "ART-001"
   oppure
   cerca_articoli_simili("vite m6 zincata")  →  ar_codart = "ART-001"
3. confronta_fornitori("ART-001")
   →  Fornitore A: €10.00 | cod. XYZ
       Fornitore B: €8.50  | cod. B-0042
       Fornitore C: €9.20  | cod. —
4. Risponde: "Fornitore B offre lo stesso articolo a €8.50 (-15%)"
```

---

## Indicizzazione semantica

`index_articoli.py` è uno script standalone (non un tool MCP) che:
1. Legge tutti gli articoli da `v_articoli`
2. Genera embedding di `descrizione` con GeminiEmbedder (già in uso nel progetto)
3. Salva in una collezione ChromaDB `iab_articoli` (separata da quella dei preventivi)

Da eseguire manualmente una volta, poi al bisogno quando gli articoli cambiano significativamente.

---

## Tecnologia

| Componente | Scelta | Motivazione |
|-----------|--------|-------------|
| Framework MCP | FastMCP | Decoratori semplici, compatibile Python |
| DB connection | pyodbc | Già usato dal progetto |
| Embedding | GeminiEmbedder | Già configurato nel progetto |
| Vector store | ChromaDB | Già usato dal progetto |
| Ricerca testuale | Multi-token LIKE | Zero dipendenze, efficace per lookup |

---

## Fuori scope (fase 1)

- Scrittura / aggiornamento dati
- Sconti (`sconti` table) — da aggiungere in fase 2 come tool `get_sconti_fornitore`
- SQL Server Full-Text Search — alternativa futura a multi-token LIKE se le performance degradano
- Prezzi di vendita clienti
