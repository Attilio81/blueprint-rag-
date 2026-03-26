"""
Visualizzazione del database vettoriale in 2D/3D.

Estrae gli embedding da ChromaDB, li riduce con UMAP e genera
un grafico interattivo HTML (aperto automaticamente nel browser).

Uso:
    python visualize.py          # vista 3D (default)
    python visualize.py --2d     # vista 2D
    python visualize.py --out mappa.html  # salva in un file specifico
"""

import argparse
import sys
import io
import os
import webbrowser
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

from knowledge import build_knowledge


# ── Palette colori per documento sorgente ──────────────────────────────────
COLORS = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]

# ── Marker per tipo di chunk ────────────────────────────────────────────────
MARKERS = {
    "text":   "circle",
    "vision": "diamond",
}


def load_chunks_from_chroma() -> dict:
    """Estrae embedding, contenuti e metadati da ChromaDB."""
    _, vdb = build_knowledge()
    vdb.create()  # inizializza la connessione alla collection
    col = vdb._collection

    total = col.count()
    if total == 0:
        print("Il database è vuoto. Esegui prima: python main.py --ingest-only")
        sys.exit(1)

    print(f"Carico {total} chunk dal database...")
    data = col.get(
        include=["embeddings", "documents", "metadatas"],
        limit=total,
    )
    return data


def reduce_dimensions(embeddings: np.ndarray, n_components: int) -> np.ndarray:
    """Riduce con UMAP da 3072 → 2 o 3 dimensioni."""
    import umap

    print(f"Riduco {embeddings.shape[0]} vettori da {embeddings.shape[1]}d → {n_components}d con UMAP...")
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=min(15, len(embeddings) - 1),
        min_dist=0.1,
        metric="cosine",
        random_state=42,
    )
    return reducer.fit_transform(embeddings)


def build_hover_text(doc: str, meta: dict) -> str:
    """Costruisce il testo del tooltip al passaggio del mouse."""
    snippet = doc[:120].replace("\n", " ").strip()
    if len(doc) > 120:
        snippet += "…"
    return (
        f"<b>{meta.get('source', '?')}</b><br>"
        f"Pagina {meta.get('page', '?')} · {meta.get('type', '?')}<br>"
        f"<i>{snippet}</i>"
    )


def plot_3d(coords: np.ndarray, data: dict, out_path: str) -> None:
    import plotly.graph_objects as go

    sources = sorted(set(m.get("source", "?") for m in data["metadatas"]))
    color_map = {s: COLORS[i % len(COLORS)] for i, s in enumerate(sources)}

    fig = go.Figure()

    for source in sources:
        indices = [i for i, m in enumerate(data["metadatas"]) if m.get("source") == source]

        for chunk_type, marker_symbol in MARKERS.items():
            sub_idx = [i for i in indices if data["metadatas"][i].get("type") == chunk_type]
            if not sub_idx:
                continue

            x = coords[sub_idx, 0]
            y = coords[sub_idx, 1]
            z = coords[sub_idx, 2]
            hover = [build_hover_text(data["documents"][i], data["metadatas"][i]) for i in sub_idx]
            label = f"{source} [{chunk_type}]"

            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=z,
                mode="markers",
                name=label,
                marker=dict(
                    size=6 if chunk_type == "text" else 9,
                    symbol=marker_symbol,
                    color=color_map[source],
                    opacity=0.85,
                    line=dict(width=0.5, color="white") if chunk_type == "vision" else dict(width=0),
                ),
                text=hover,
                hovertemplate="%{text}<extra></extra>",
            ))

    fig.update_layout(
        title=dict(text="Knowledge Base — Preventivi Leonardo Imola", font=dict(size=18)),
        scene=dict(
            xaxis_title="UMAP 1",
            yaxis_title="UMAP 2",
            zaxis_title="UMAP 3",
            bgcolor="#1a1a2e",
            xaxis=dict(gridcolor="#333366"),
            yaxis=dict(gridcolor="#333366"),
            zaxis=dict(gridcolor="#333366"),
        ),
        paper_bgcolor="#0f0f23",
        plot_bgcolor="#0f0f23",
        font=dict(color="white"),
        legend=dict(
            bgcolor="#1a1a2e",
            bordercolor="#333366",
            font=dict(size=11),
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=750,
    )

    fig.write_html(out_path, auto_open=False)


def plot_2d(coords: np.ndarray, data: dict, out_path: str) -> None:
    import plotly.graph_objects as go

    sources = sorted(set(m.get("source", "?") for m in data["metadatas"]))
    color_map = {s: COLORS[i % len(COLORS)] for i, s in enumerate(sources)}

    fig = go.Figure()

    for source in sources:
        indices = [i for i, m in enumerate(data["metadatas"]) if m.get("source") == source]

        for chunk_type, marker_symbol in MARKERS.items():
            sub_idx = [i for i in indices if data["metadatas"][i].get("type") == chunk_type]
            if not sub_idx:
                continue

            x = coords[sub_idx, 0]
            y = coords[sub_idx, 1]
            hover = [build_hover_text(data["documents"][i], data["metadatas"][i]) for i in sub_idx]
            label = f"{source} [{chunk_type}]"

            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="markers",
                name=label,
                marker=dict(
                    size=9 if chunk_type == "text" else 13,
                    symbol=marker_symbol,
                    color=color_map[source],
                    opacity=0.85,
                    line=dict(width=1.5, color="white") if chunk_type == "vision" else dict(width=0),
                ),
                text=hover,
                hovertemplate="%{text}<extra></extra>",
            ))

    fig.update_layout(
        title=dict(text="Knowledge Base — Preventivi Leonardo Imola (2D)", font=dict(size=18)),
        xaxis_title="UMAP 1",
        yaxis_title="UMAP 2",
        paper_bgcolor="#0f0f23",
        plot_bgcolor="#1a1a2e",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#333366", zerolinecolor="#333366"),
        yaxis=dict(gridcolor="#333366", zerolinecolor="#333366"),
        legend=dict(bgcolor="#1a1a2e", bordercolor="#333366", font=dict(size=11)),
        margin=dict(l=40, r=20, t=60, b=40),
        height=720,
    )

    fig.write_html(out_path, auto_open=False)


def main():
    parser = argparse.ArgumentParser(description="Visualizza il knowledge base in 2D/3D")
    parser.add_argument("--2d", dest="two_d", action="store_true", help="Vista 2D invece di 3D")
    parser.add_argument("--out", default=None, help="Path del file HTML di output")
    args = parser.parse_args()

    n_components = 2 if args.two_d else 3
    default_name = "kb_2d.html" if args.two_d else "kb_3d.html"
    out_path = args.out or str(Path(__file__).parent.parent / default_name)

    data = load_chunks_from_chroma()
    embeddings = np.array(data["embeddings"], dtype=np.float32)

    coords = reduce_dimensions(embeddings, n_components)

    print(f"Genero il grafico {'2D' if args.two_d else '3D'}...")
    if args.two_d:
        plot_2d(coords, data, out_path)
    else:
        plot_3d(coords, data, out_path)

    print(f"Salvato in: {out_path}")
    webbrowser.open(f"file:///{out_path}")


if __name__ == "__main__":
    main()
