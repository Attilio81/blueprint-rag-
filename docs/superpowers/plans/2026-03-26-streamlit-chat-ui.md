# Streamlit Chat UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere un'interfaccia web Streamlit con streaming e visualizzazione fonti per l'agente RAG Preventivi.

**Architecture:** Un file `chat_app.py` importa `build_chat_agent()` da `agent.py`. L'agente usa `InMemoryDb` per il multi-turno e `stream_events=True` per lo streaming. Le fonti vengono estratte dagli eventi `RunCompleted`.

**Tech Stack:** Python 3.11+, Streamlit, Agno (`agno.agent.RunEvent`, `agno.db.in_memory.InMemoryDb`), DeepSeek, ChromaDB

---

## File map

| File | Azione | Responsabilità |
|------|--------|----------------|
| `rag_preventivi/requirements.txt` | Modifica | Aggiunge `streamlit` |
| `rag_preventivi/agent.py` | Modifica | Aggiunge `build_chat_agent()` con InMemoryDb e history |
| `rag_preventivi/tests/test_agent.py` | Crea | Test per `build_chat_agent()` |
| `rag_preventivi/chat_app.py` | Crea | App Streamlit completa |

---

### Task 1: Aggiungi dipendenza Streamlit

**Files:**
- Modify: `rag_preventivi/requirements.txt`

- [ ] **Step 1: Aggiungi streamlit a requirements.txt**

Il file attuale è:
```
agno
chromadb
pymupdf
google-generativeai
python-dotenv
Pillow
pytest
```

Aggiungi `streamlit` alla fine:
```
agno
chromadb
pymupdf
google-generativeai
python-dotenv
Pillow
pytest
streamlit
```

- [ ] **Step 2: Installa la dipendenza**

```bash
cd rag_preventivi
pip install streamlit
```

Expected: `Successfully installed streamlit-...`

- [ ] **Step 3: Commit**

```bash
git add rag_preventivi/requirements.txt
git commit -m "chore: add streamlit dependency"
```

---

### Task 2: TDD per build_chat_agent()

**Files:**
- Create: `rag_preventivi/tests/test_agent.py`
- Modify: `rag_preventivi/agent.py`

- [ ] **Step 1: Scrivi il test fallente**

Crea `rag_preventivi/tests/test_agent.py`:

```python
# tests/test_agent.py
from unittest.mock import patch, MagicMock


def test_build_chat_agent_has_history_and_db():
    """build_chat_agent deve configurare multi-turno con InMemoryDb."""
    mock_knowledge = MagicMock()
    mock_vector_db = MagicMock()
    with patch("agent.build_knowledge", return_value=(mock_knowledge, mock_vector_db)):
        from agent import build_chat_agent
        agent = build_chat_agent()
    assert agent.add_history_to_context is True
    assert agent.db is not None
```

- [ ] **Step 2: Esegui il test per verificare che fallisca**

```bash
cd rag_preventivi
python -m pytest tests/test_agent.py::test_build_chat_agent_has_history_and_db -v
```

Expected: `FAILED` con `ImportError: cannot import name 'build_chat_agent' from 'agent'`

- [ ] **Step 3: Implementa build_chat_agent() in agent.py**

Apri `rag_preventivi/agent.py` e aggiungilo dopo `build_agent()`:

```python
# agent.py
from dotenv import load_dotenv
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.deepseek import DeepSeek
from knowledge import build_knowledge
from config import PROJECT_CONTEXT

load_dotenv()


def build_agent() -> Agent:
    knowledge, _ = build_knowledge()
    return Agent(
        model=DeepSeek(id="deepseek-chat"),
        knowledge=knowledge,
        search_knowledge=True,
        instructions=[
            "Sei un assistente specializzato nell'analisi di preventivi edilizi.",
            f"Il progetto è {PROJECT_CONTEXT}.",
            "Cita sempre il documento sorgente nella risposta.",
            "Se un'informazione proviene dall'analisi visiva di una pagina, indicalo con '(da analisi immagine)'.",
            "Per gli importi specifica sempre se IVA inclusa o esclusa.",
            "Se non trovi l'informazione nel knowledge base, dillo chiaramente.",
            "Rispondi sempre in italiano.",
        ],
        markdown=True,
    )


def build_chat_agent() -> Agent:
    """Agente con memoria di sessione in-memory per chat multi-turno."""
    knowledge, _ = build_knowledge()
    return Agent(
        model=DeepSeek(id="deepseek-chat"),
        knowledge=knowledge,
        search_knowledge=True,
        db=InMemoryDb(),
        add_history_to_context=True,
        instructions=[
            "Sei un assistente specializzato nell'analisi di preventivi edilizi.",
            f"Il progetto è {PROJECT_CONTEXT}.",
            "Cita sempre il documento sorgente nella risposta.",
            "Se un'informazione proviene dall'analisi visiva di una pagina, indicalo con '(da analisi immagine)'.",
            "Per gli importi specifica sempre se IVA inclusa o esclusa.",
            "Se non trovi l'informazione nel knowledge base, dillo chiaramente.",
            "Rispondi sempre in italiano.",
        ],
        markdown=True,
    )
```

- [ ] **Step 4: Esegui il test per verificare che passi**

```bash
cd rag_preventivi
python -m pytest tests/test_agent.py::test_build_chat_agent_has_history_and_db -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add rag_preventivi/agent.py rag_preventivi/tests/test_agent.py
git commit -m "feat: add build_chat_agent with InMemoryDb for multi-turn chat"
```

---

### Task 3: Implementa chat_app.py

**Files:**
- Create: `rag_preventivi/chat_app.py`

- [ ] **Step 1: Crea chat_app.py**

Crea `rag_preventivi/chat_app.py` con il contenuto seguente:

```python
# chat_app.py
import sys
import io

# Fix encoding su Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
from pathlib import Path

# Aggiunge rag_preventivi/ al path per gli import bare (config, agent, ...)
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from agno.agent import RunEvent
from agent import build_chat_agent
from config import PROJECT_CONTEXT


# ── Configurazione pagina ───────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Preventivi",
    page_icon="📄",
    layout="centered",
)
st.title("📄 RAG Preventivi")
st.caption(f"Progetto: {PROJECT_CONTEXT}")


# ── Inizializzazione sessione ───────────────────────────────────────────────
if "agent" not in st.session_state:
    with st.spinner("Carico il knowledge base..."):
        st.session_state.agent = build_chat_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role", "content", "sources"}


# ── Mostra storico conversazione ────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Fonti"):
                for src in msg["sources"]:
                    st.markdown(f"- {src}")


# ── Input utente ────────────────────────────────────────────────────────────
prompt = st.chat_input("Fai una domanda sui preventivi...")

if prompt:
    # Mostra messaggio utente
    st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Streaming risposta agente
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        sources = []

        stream = st.session_state.agent.run(prompt, stream=True, stream_events=True)

        for chunk in stream:
            # Accumula i chunk di testo
            if chunk.event == RunEvent.run_content and chunk.content:
                full_text += chunk.content
                placeholder.markdown(full_text + "▌")  # cursore animato

            # Estrai fonti dall'evento finale
            elif chunk.event == RunEvent.run_completed:
                refs = getattr(chunk, "references", None)
                if refs:
                    for ref in refs:
                        docs = getattr(ref, "documents", [])
                        for doc in docs:
                            name = getattr(doc, "name", None) or str(doc)
                            if name not in sources:
                                sources.append(name)

        placeholder.markdown(full_text)  # rimuove cursore

        if sources:
            with st.expander("Fonti"):
                for src in sources:
                    st.markdown(f"- {src}")

    # Salva nella cronologia
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_text,
        "sources": sources,
    })
```

- [ ] **Step 2: Verifica che Streamlit carichi senza errori di import**

```bash
cd rag_preventivi
python -c "import streamlit; import agno; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add rag_preventivi/chat_app.py
git commit -m "feat: add Streamlit chat UI with streaming and sources"
```

---

### Task 4: Test manuale end-to-end

- [ ] **Step 1: Avvia l'app**

```bash
cd rag_preventivi
streamlit run chat_app.py
```

Expected: il browser si apre su `http://localhost:8501` con il titolo "RAG Preventivi" e lo spinner "Carico il knowledge base...". Dopo qualche secondo lo spinner sparisce.

- [ ] **Step 2: Testa una domanda semplice**

Scrivi nel campo input:
```
Ciao, cosa puoi fare?
```

Expected: risposta streaming con testo che appare progressivamente. Nessun expander "Fonti" (domanda generica, nessun documento citato).

- [ ] **Step 3: Testa una domanda specifica sui preventivi**

Scrivi:
```
Quali sono i preventivi disponibili?
```

Expected: risposta streaming con lista di documenti, expander "Fonti" con almeno un nome di documento.

- [ ] **Step 4: Testa il multi-turno**

Dopo la risposta precedente, scrivi:
```
Puoi dirmi di più sul primo che hai citato?
```

Expected: l'agente risponde in modo coerente con la conversazione precedente (usa il contesto del turno precedente).

- [ ] **Step 5: Commit finale**

```bash
git add -A
git commit -m "chore: finalize streamlit chat UI implementation"
```

---

## Note di esecuzione

- Avviare sempre da dentro `rag_preventivi/` o con path completo, per via degli import bare (`from agent import ...`)
- Il `chroma_db/` deve essere già popolato (eseguire `python main.py --ingest-only` se non lo è)
- Le variabili d'ambiente (`.env`) devono essere presenti nella root del progetto
