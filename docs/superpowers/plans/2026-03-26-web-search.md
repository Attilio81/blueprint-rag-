# Web Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere ricerca web (DuckDuckGo via `ddgs`) all'agente chat, attivabile solo su richiesta esplicita dell'utente, con visualizzazione URL in un expander "🌐 Fonti web" separato dalle fonti RAG.

**Architecture:** `WebSearchTools(backend="duckduckgo")` viene aggiunto a `build_chat_agent()` in `agent.py` insieme a un'istruzione che limita l'uso del tool alle richieste esplicite. In `chat_app.py` si intercetta l'evento `RunEvent.tool_call_completed` per estrarre gli URL restituiti e mostrarli in un expander dedicato, sia in tempo reale che nello storico.

**Tech Stack:** Python 3.11+, Agno (`agno.tools.websearch.WebSearchTools`), `ddgs`, Streamlit

---

## File map

| File | Azione | Responsabilità |
|------|--------|----------------|
| `rag_preventivi/requirements.txt` | Modifica | Aggiunge `ddgs` |
| `rag_preventivi/agent.py` | Modifica | Aggiunge `WebSearchTools` + istruzione a `build_chat_agent()` |
| `rag_preventivi/tests/test_agent.py` | Modifica | Aggiunge test per verifica tool in `build_chat_agent()` |
| `rag_preventivi/chat_app.py` | Modifica | Intercetta tool call, mostra `🌐 Fonti web` in tempo reale e nello storico |

---

### Task 1: Aggiungi dipendenza ddgs

**Files:**
- Modify: `rag_preventivi/requirements.txt`

- [ ] **Step 1: Aggiungi ddgs a requirements.txt**

Il file attuale è:
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

Aggiungi `ddgs` in fondo:
```
agno
chromadb
pymupdf
google-generativeai
python-dotenv
Pillow
pytest
streamlit
ddgs
```

- [ ] **Step 2: Installa la dipendenza**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
pip install ddgs
```

Expected: `Successfully installed ddgs-...` (o `Requirement already satisfied`)

- [ ] **Step 3: Verifica che l'import Agno funzioni**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python -c "from agno.tools.websearch import WebSearchTools; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi"
git add rag_preventivi/requirements.txt
git commit -m "chore: add ddgs dependency for web search"
```

---

### Task 2: Aggiungi WebSearchTools a build_chat_agent() con TDD

**Files:**
- Modify: `rag_preventivi/tests/test_agent.py`
- Modify: `rag_preventivi/agent.py`

- [ ] **Step 1: Scrivi il test fallente in test_agent.py**

Apri `rag_preventivi/tests/test_agent.py` e aggiungi in fondo:

```python
def test_build_chat_agent_has_web_search_tool():
    """build_chat_agent deve avere almeno un tool configurato (WebSearchTools)."""
    mock_knowledge = MagicMock()
    mock_vector_db = MagicMock()
    with patch("agent.build_knowledge", return_value=(mock_knowledge, mock_vector_db)):
        from agent import build_chat_agent
        agent_instance = build_chat_agent()
    assert agent_instance.tools is not None
    assert len(agent_instance.tools) >= 1
```

- [ ] **Step 2: Esegui il test per verificare che fallisca**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python -m pytest tests/test_agent.py::test_build_chat_agent_has_web_search_tool -v
```

Expected: `FAILED` — `AssertionError` perché `agent_instance.tools` è `None` o vuota.

- [ ] **Step 3: Implementa la modifica in agent.py**

Apri `rag_preventivi/agent.py`. Sostituisci l'intero file con:

```python
# agent.py
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.db.in_memory import InMemoryDb
from agno.tools.websearch import WebSearchTools
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
    """Agente con memoria di sessione in-memory per chat multi-turno e ricerca web su richiesta."""
    knowledge, _ = build_knowledge()
    return Agent(
        model=DeepSeek(id="deepseek-chat"),
        knowledge=knowledge,
        search_knowledge=True,
        db=InMemoryDb(),
        add_history_to_context=True,
        tools=[WebSearchTools(backend="duckduckgo")],
        instructions=[
            "Sei un assistente specializzato nell'analisi di preventivi edilizi.",
            f"Il progetto è {PROJECT_CONTEXT}.",
            "Cita sempre il documento sorgente nella risposta.",
            "Se un'informazione proviene dall'analisi visiva di una pagina, indicalo con '(da analisi immagine)'.",
            "Per gli importi specifica sempre se IVA inclusa o esclusa.",
            "Se non trovi l'informazione nel knowledge base, dillo chiaramente.",
            "Rispondi sempre in italiano.",
            "Usa lo strumento di ricerca web SOLO se l'utente chiede esplicitamente di cercare online, trovare fornitori, cercare alternative sul mercato, o usa parole come 'cerca sul web', 'trova online', 'fornitori alternativi'. Per qualsiasi domanda sui preventivi usa sempre e solo il knowledge base.",
        ],
        markdown=True,
    )
```

- [ ] **Step 4: Esegui tutti i test per verificare che passino**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python -m pytest -v 2>&1 | tail -30
```

Expected: tutti PASSED — erano 22, ora 23.

- [ ] **Step 5: Commit**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi"
git add rag_preventivi/agent.py rag_preventivi/tests/test_agent.py
git commit -m "feat: add WebSearchTools to build_chat_agent for explicit web search"
```

---

### Task 3: Aggiorna chat_app.py per mostrare fonti web

**Files:**
- Modify: `rag_preventivi/chat_app.py`

- [ ] **Step 1: Sostituisci chat_app.py con la versione aggiornata**

Scrivi `rag_preventivi/chat_app.py` con il seguente contenuto completo:

```python
# chat_app.py
import re
import sys
from pathlib import Path

# Aggiunge rag_preventivi/ al path per gli import bare (config, agent, ...)
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from agno.agent import RunEvent
from agent import build_chat_agent
from admin_tab import render_admin_tab
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
    st.session_state.messages = []  # list of {"role", "content", "sources", "web_sources"}


# ── Tabs ────────────────────────────────────────────────────────────────────
tab_chat, tab_admin = st.tabs(["💬 Chat", "🗂 Gestione"])

with tab_chat:
    # Mostra storico conversazione
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📄 Fonti documenti"):
                    for src in msg["sources"]:
                        st.markdown(f"- {src}")
            if msg.get("web_sources"):
                with st.expander("🌐 Fonti web"):
                    for url in msg["web_sources"]:
                        st.markdown(f"- {url}")

    # Input utente
    prompt = st.chat_input("Fai una domanda sui preventivi...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt, "sources": [], "web_sources": []})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_text = ""
            sources = []
            web_sources = []

            try:
                stream = st.session_state.agent.run(prompt, stream=True, stream_events=True)

                for chunk in stream:
                    if chunk.event == RunEvent.run_content and chunk.content:
                        full_text += chunk.content
                        placeholder.markdown(full_text + "▌")  # cursore animato
                    elif chunk.event == RunEvent.run_completed:
                        refs = getattr(chunk, "references", None)
                        if refs:
                            for ref in refs:
                                docs = getattr(ref, "documents", [])
                                for doc in docs:
                                    name = getattr(doc, "name", None) or str(doc)
                                    if name not in sources:
                                        sources.append(name)
                    elif chunk.event == RunEvent.tool_call_completed:
                        tool = getattr(chunk, "tool", None)
                        if tool and "search" in (getattr(tool, "tool_name", "") or "").lower():
                            content = getattr(tool, "content", "") or ""
                            urls = re.findall(r'https?://[^\s"\'<>\)]+', content)
                            for url in urls:
                                if url not in web_sources:
                                    web_sources.append(url)

            except Exception as e:
                full_text = full_text or f"_Errore durante la risposta: {e}_"

            placeholder.markdown(full_text or "_Nessuna risposta ricevuta._")

            if sources:
                with st.expander("📄 Fonti documenti"):
                    for src in sources:
                        st.markdown(f"- {src}")

            if web_sources:
                with st.expander("🌐 Fonti web"):
                    for url in web_sources:
                        st.markdown(f"- {url}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_text or "_Nessuna risposta ricevuta._",
            "sources": sources,
            "web_sources": web_sources,
        })

with tab_admin:
    render_admin_tab()
```

- [ ] **Step 2: Verifica sintassi**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python -c "import ast; ast.parse(open('chat_app.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 3: Esegui tutta la suite per verificare nessuna regressione**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python -m pytest -v 2>&1 | tail -10
```

Expected: 23 PASSED, 0 failed.

- [ ] **Step 4: Commit**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi"
git add rag_preventivi/chat_app.py
git commit -m "feat: show web search URLs in 🌐 Fonti web expander"
```

---

### Task 4: Test manuale end-to-end

- [ ] **Step 1: Avvia l'app**

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
streamlit run chat_app.py
```

Apri `http://localhost:8501` nel browser.

- [ ] **Step 2: Testa che le domande normali NON attivano la ricerca web**

Scrivi nella chat: `Qual è il totale del preventivo?`

Expected: risposta basata sui PDF, nessun expander "🌐 Fonti web".

- [ ] **Step 3: Testa la ricerca web esplicita**

Scrivi nella chat: `Cercami sul web dei fornitori di serramenti in PVC`

Expected:
- L'agente risponde con risultati dal web
- Compare l'expander "🌐 Fonti web" con uno o più URL
- L'expander "📄 Fonti documenti" non appare (nessun documento RAG coinvolto)

- [ ] **Step 4: Testa la combinazione RAG + web**

Scrivi nella chat: `Nel preventivo c'è un articolo X — riesci a trovarmi alternative online?`

Expected: l'agente risponde con info dal PDF E cerca sul web, mostrando entrambi gli expander.
