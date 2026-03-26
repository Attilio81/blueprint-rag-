# admin_tab.py
from pathlib import Path

import streamlit as st

from config import DOCUMENTS_DIR
from ingestion.pipeline import (
    list_pdf_files,
    load_indexed,
    save_indexed,
    compute_file_hash,
    run_ingestion_streaming,
)
from ingestion.text_extractor import is_corrupted_pdf


def get_document_status() -> list[dict]:
    """
    Returns list of {"name": str, "status": str, "path": str} for all PDFs in DOCUMENTS_DIR.
    Status values: "✅ Indicizzato", "⏳ Non indicizzato", "⚠️ Corrotto"
    """
    indexed = load_indexed()
    result = []
    for pdf_path in list_pdf_files():
        name = pdf_path.name
        current_hash = compute_file_hash(str(pdf_path))
        if indexed.get(name) == current_hash:
            status = "✅ Indicizzato"
        else:
            status = "⚠️ Corrotto" if is_corrupted_pdf(str(pdf_path)) else "⏳ Non indicizzato"
        result.append({"name": name, "status": status, "path": str(pdf_path)})
    return result


def render_admin_tab() -> None:
    """Renders the document management tab UI."""
    if msg := st.session_state.pop("delete_msg", None):
        st.warning(msg)
    st.subheader("Gestione Documenti")

    # ── Upload PDF ───────────────────────────────────────────────────────────
    uploaded_files = st.file_uploader(
        "Carica PDF nella cartella Preventivi",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        dest_dir = Path(DOCUMENTS_DIR)
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in uploaded_files:
            (dest_dir / f.name).write_bytes(f.getvalue())
        st.success(f"{len(uploaded_files)} file caricato/i in {DOCUMENTS_DIR}")
        st.rerun()

    # ── Bottoni indicizzazione ───────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Indicizza nuovi", use_container_width=True):
            with st.status("Indicizzazione in corso...", expanded=True) as status:
                for line in run_ingestion_streaming(reindex=False):
                    st.write(line)
                status.update(label="✅ Indicizzazione completata!", state="complete")
            st.rerun()

    with col2:
        if st.button("🔄 Re-indicizza tutto", use_container_width=True):
            with st.status("Re-indicizzazione in corso...", expanded=True) as status:
                for line in run_ingestion_streaming(reindex=True):
                    st.write(line)
                status.update(label="✅ Re-indicizzazione completata!", state="complete")
            st.rerun()

    # ── Lista documenti ──────────────────────────────────────────────────────
    st.divider()
    docs = get_document_status()

    if not docs:
        st.info(f"Nessun PDF trovato in {DOCUMENTS_DIR}")
        return

    st.markdown(f"**📋 Documenti ({len(docs)})**")
    indexed_data = load_indexed()

    for doc in docs:
        col_name, col_status, col_btn = st.columns([3, 1.5, 1])
        with col_name:
            st.markdown(f"📄 `{doc['name']}`")
        with col_status:
            st.markdown(doc["status"])
        with col_btn:
            if st.button("🗑️", key=f"del_{doc['name']}", help=f"Elimina {doc['name']}"):
                try:
                    Path(doc["path"]).unlink()
                    if doc["name"] in indexed_data:
                        del indexed_data[doc["name"]]
                        save_indexed(indexed_data)
                    st.session_state["delete_msg"] = (
                        f"'{doc['name']}' eliminato. "
                        "Ri-indicizza per aggiornare il knowledge base."
                    )
                    st.rerun()
                except OSError as e:
                    st.error(f"Errore eliminazione: {e}")
