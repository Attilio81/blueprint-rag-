# Streamlit Chat UI per RAG Agent Preventivi

**Data:** 2026-03-26
**Stato:** Approvato

## Obiettivo

Aggiungere un'interfaccia web Streamlit per chattare con l'agente RAG Preventivi, con streaming delle risposte e visualizzazione delle fonti citate.

## Architettura

Un solo file nuovo: `rag_preventivi/chat_app.py`.
Modifica minima a `rag_preventivi/agent.py`: aggiunta di `build_chat_agent()`.

```
rag_preventivi/
  agent.py          ← aggiunge build_chat_agent()
  chat_app.py       ← nuovo, entry point Streamlit
  main.py           ← invariato
```

Avvio: `streamlit run rag_preventivi/chat_app.py`

## Agent setup multi-turno (agent.py)

Nuova funzione `build_chat_agent()` che estende la configurazione base con:
- `db=InMemoryDb()` — storage sessione in-memory (persiste per tutta la sessione browser)
- `add_history_to_context=True` — inietta la cronologia in ogni richiesta per il multi-turno

Alla chiusura o refresh del browser la conversazione riparte da zero (comportamento atteso per uso locale).

## UI Components (chat_app.py)

- **Header**: titolo + descrizione del progetto
- **Area messaggi**: `st.chat_message()` per ogni turno (user + assistant)
- **Fonti**: expander collassato `"Fonti"` sotto ogni risposta dell'agente
- **Input**: `st.chat_input()` fisso in fondo alla pagina

### Stato Streamlit

```python
st.session_state.agent   # istanza Agent (creata una volta, riusata)
st.session_state.messages  # lista {"role": ..., "content": ..., "sources": [...]}
```

## Streaming e Fonti

Usa `agent.run(prompt, stream=True, stream_events=True)` e processa gli eventi Agno:

```python
for chunk in stream:
    if chunk.event == RunEvent.run_content and chunk.content:
        full_text += chunk.content
        placeholder.markdown(full_text + "▌")   # cursore animato
    elif chunk.event == RunEvent.run_completed:
        if chunk.references:
            sources = chunk.references

placeholder.markdown(full_text)  # rimuove cursore
```

Dopo lo streaming, se `sources` è popolato, appare un expander "Fonti" con i riferimenti ai documenti del knowledge base.

## File da creare/modificare

| File | Azione |
|------|--------|
| `rag_preventivi/agent.py` | Aggiunge `build_chat_agent()` |
| `rag_preventivi/chat_app.py` | Nuovo file Streamlit |

## Dipendenze

- `streamlit` (da aggiungere a requirements se non presente)
- `agno`, `deepseek`, `python-dotenv` (già presenti)
