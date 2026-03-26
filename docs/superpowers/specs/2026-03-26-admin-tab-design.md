# UI Gestione Documenti RAG — Design Spec

**Data:** 2026-03-26
**Stato:** Approvato

## Obiettivo

Aggiungere una tab "Gestione" all'app Streamlit esistente (`chat_app.py`) che permetta di: visualizzare lo stato dei documenti, caricare nuovi PDF, avviare l'indicizzazione con log in tempo reale, ed eliminare documenti.

## Architettura

La tab "Gestione" viene integrata in `chat_app.py` tramite `st.tabs()`. La logica della tab è isolata in un nuovo file `admin_tab.py`. La pipeline di ingestion espone una nuova funzione `run_ingestion_streaming()` che fa yield dei log riga per riga, usata dal thread in background.

```
rag_preventivi/
  chat_app.py              ← aggiunge st.tabs() con "💬 Chat" e "🗂 Gestione"
  admin_tab.py             ← nuovo, contiene render_admin_tab()
  ingestion/pipeline.py    ← aggiunge run_ingestion_streaming()
```

## File map

| File | Azione | Responsabilità |
|------|--------|----------------|
| `rag_preventivi/chat_app.py` | Modifica | Aggiunge `st.tabs()`, delega chat e gestione ai rispettivi moduli |
| `rag_preventivi/admin_tab.py` | Crea | Tutta la UI di gestione: lista, upload, indicizzazione, eliminazione |
| `rag_preventivi/ingestion/pipeline.py` | Modifica | Aggiunge `run_ingestion_streaming()` con yield dei log |

## Funzionalità della tab Gestione

### 1. Lista documenti con stato
- Legge i PDF in `DOCUMENTS_DIR` (via `list_pdf_files()`)
- Per ciascuno mostra: nome file, stato (`✅ Indicizzato` / `⏳ Non indicizzato` / `⚠️ Corrotto`)
- Lo stato è determinato confrontando l'hash del file con `indexed.json` (via `is_already_indexed()`)
- La corruzione è determinata via `is_corrupted_pdf()` (già esistente)

### 2. Upload PDF
- `st.file_uploader(accept_multiple_files=True, type=["pdf"])`
- Ogni file caricato viene salvato in `DOCUMENTS_DIR` con il suo nome originale
- Se il file esiste già, viene sovrascritto
- Dopo l'upload la lista si aggiorna

### 3. Indicizza nuovi
- Bottone che avvia `run_ingestion(reindex=False)` in un `threading.Thread`
- I log vengono catturati tramite una `queue.Queue` e mostrati riga per riga in `st.status()`
- La UI non si blocca durante l'indicizzazione
- Al termine: messaggio di completamento, lista aggiornata

### 4. Re-indicizza tutto
- Bottone che avvia `run_ingestion(reindex=True)` in un `threading.Thread`
- Stesso meccanismo di log del punto 3

### 5. Elimina documento
- Pulsante "🗑️" per ogni riga della lista
- Rimuove il file da `DOCUMENTS_DIR`
- Rimuove l'entry da `indexed.json`
- **Non** rimuove i chunk dal vector DB (troppo complesso senza ID stabili) — dopo eliminazione è necessario re-indicizzare per coerenza. Un avviso lo spiega.

## Meccanismo di streaming log (ingestion/pipeline.py)

```python
def run_ingestion_streaming(reindex: bool = False) -> Generator[str, None, None]:
    """Stesso comportamento di run_ingestion() ma fa yield dei log invece di print()."""
    ...
    yield f"[INGEST] {source}"
    yield f"  -> {len(text_chunks)} text chunks"
    ...
    yield "Ingestion complete."
```

Il thread in background chiama questa funzione e mette i log in una `queue.Queue`. `admin_tab.py` legge dalla queue con polling e aggiorna `st.status()`.

## Gestione errori

- Upload fallito (file non PDF, errore I/O): messaggio `st.error()` inline
- Indicizzazione fallita per un documento: il log mostra l'errore, gli altri documenti continuano
- Eliminazione fallita (permessi): `st.error()` inline
- Indicizzazione già in corso: i bottoni vengono disabilitati tramite `st.session_state`

## Avvio

Nessun cambiamento al comando di avvio:
```bash
streamlit run chat_app.py
```

## Note tecniche

- `st.tabs()` non ricarica l'agente al cambio tab (l'agente è in `st.session_state`)
- Il thread di ingestion usa `st.session_state.ingestion_running` come flag per evitare avvii multipli
- L'eliminazione aggiorna `indexed.json` via `save_indexed()` già esistente
