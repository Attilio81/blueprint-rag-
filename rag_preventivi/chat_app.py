# chat_app.py
import sys
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

        try:
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

        except Exception as e:
            full_text = full_text or f"_Errore durante la risposta: {e}_"

        placeholder.markdown(full_text or "_Nessuna risposta ricevuta._")  # rimuove cursore

        if sources:
            with st.expander("Fonti"):
                for src in sources:
                    st.markdown(f"- {src}")

    # Salva nella cronologia
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_text or "_Nessuna risposta ricevuta._",
        "sources": sources,
    })
