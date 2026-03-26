# Web Search — Design Spec

**Data:** 2026-03-26
**Stato:** Approvato

## Obiettivo

Aggiungere la capacità di ricerca web all'agente RAG della chat Streamlit, in modo che possa rispondere a richieste esplicite come "cercami un fornitore", "trova alternative online", "qual è il prezzo di mercato di questo articolo".

## Architettura

La ricerca web viene esposta come **tool nativo Agno** (`WebSearchTools`) aggiunto al solo `build_chat_agent()` in `agent.py`. Usa la libreria `ddgs` (meta-search multi-backend) con backend DuckDuckGo — nessuna API key richiesta. L'agente usa il tool solo su richiesta esplicita dell'utente grazie a un'istruzione dedicata. La UI in `chat_app.py` cattura l'evento di completamento del tool e mostra gli URL estratti in una sezione separata "🌐 Fonti web".

```
rag_preventivi/
  agent.py         ← aggiunge WebSearchTools + istruzione a build_chat_agent()
  chat_app.py      ← cattura RunEvent.tool_call_completed, mostra 🌐 Fonti web
  requirements.txt ← aggiunge ddgs
```

## File map

| File | Azione | Responsabilità |
|------|--------|----------------|
| `rag_preventivi/agent.py` | Modifica | Aggiunge `tools=[WebSearchTools(backend="duckduckgo")]` e istruzione a `build_chat_agent()` |
| `rag_preventivi/chat_app.py` | Modifica | Cattura `RunEvent.tool_call_completed`, estrae URL, mostra `🌐 Fonti web` |
| `rag_preventivi/requirements.txt` | Modifica | Aggiunge `ddgs` |

## Modifiche a agent.py

`build_chat_agent()` riceve:
- `tools=[WebSearchTools(backend="duckduckgo")]` — import: `from agno.tools.websearch import WebSearchTools`
- Una nuova istruzione (aggiunta alla lista esistente):
  > "Usa lo strumento di ricerca web SOLO se l'utente chiede esplicitamente di cercare online, trovare fornitori, cercare alternative sul mercato, o usa parole come 'cerca sul web', 'trova online', 'fornitori alternativi'. Per qualsiasi domanda sui preventivi usa sempre e solo il knowledge base."

`build_agent()` (CLI) **non** riceve il tool — la ricerca web è solo per la chat interattiva.

## Modifiche a chat_app.py

Nel loop di streaming si aggiunge la gestione di `RunEvent.tool_call_completed`. La funzione esposta da `WebSearchTools` si chiama `web_search`. Il risultato è una stringa JSON con campi `title`, `href`, `body` per ciascun risultato.

```python
web_sources = []  # inizializzato insieme a sources e full_text

elif chunk.event == RunEvent.tool_call_completed:
    tool = getattr(chunk, "tool", None)
    if tool and "search" in (getattr(tool, "tool_name", "") or "").lower():
        content = getattr(tool, "content", "") or ""
        urls = re.findall(r'https?://[^\s"\'<>\)]+', content)
        for url in urls:
            if url not in web_sources:
                web_sources.append(url)
```

Import aggiunto in testa al file: `import re`

Dopo la risposta, visualizzazione delle fonti web:

```python
if web_sources:
    with st.expander("🌐 Fonti web"):
        for url in web_sources:
            st.markdown(f"- {url}")
```

I `web_sources` vengono salvati in `st.session_state.messages` accanto ai `sources` esistenti:

```python
st.session_state.messages.append({
    "role": "assistant",
    "content": ...,
    "sources": sources,
    "web_sources": web_sources,
})
```

La visualizzazione dello storico mostra entrambe le sezioni se presenti. Nel loop che mostra i messaggi salvati, si aggiunge dopo l'expander "Fonti" già esistente:

```python
if msg.get("web_sources"):
    with st.expander("🌐 Fonti web"):
        for url in msg["web_sources"]:
            st.markdown(f"- {url}")
```

## Dipendenza

`ddgs` — libreria Python che astrae DuckDuckGo, Google, Bing e altri backend. Nessuna API key richiesta per il backend DuckDuckGo.

## Gestione errori

- Se la ricerca non restituisce risultati: l'agente lo comunica nel testo della risposta, nessun expander "🌐 Fonti web" appare.
- Se il parsing degli URL fallisce: `web_sources` rimane vuota, nessun crash.
- Se il backend è temporaneamente non raggiungibile: l'eccezione viene catturata dal `try/except` esistente in `chat_app.py` e mostrata come `_Errore durante la risposta: ..._`.

## Avvio

Nessun cambiamento al comando di avvio:
```bash
streamlit run chat_app.py
```

## Esempi di query che attivano la ricerca web

- "Trovami fornitori alternativi per questo tipo di infissi"
- "Cerca sul web il prezzo medio del calcestruzzo C25/30"
- "Ma quello stesso articolo, riesci a trovarmi un'alternativa online?"
- "Quali aziende vendono pannelli fotovoltaici simili?"
