"""Visualizzazione interattiva degli embedding degli articoli IAB.

Legge gli embedding da ChromaDB, riduce a 2D con UMAP e mostra
uno scatter plot interattivo (HTML) con descrizione articolo al hover.

Uso: python visualizza_embeddings.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import chromadb
import plotly.graph_objects as go
import umap

import embeddings as emb


def main():
    print("Carico embedding da ChromaDB...")
    client = chromadb.PersistentClient(path=emb.CHROMA_PATH)
    collection = client.get_or_create_collection(emb.COLLECTION_NAME)
    count = collection.count()
    if count == 0:
        print("Nessun articolo indicizzato. Eseguire prima index_articoli.py.")
        return

    result = collection.get(include=["embeddings", "metadatas"])
    vectors = np.array(result["embeddings"])
    metadatas = result["metadatas"]
    print(f"Articoli caricati: {len(vectors)} (dimensioni embedding: {vectors.shape[1]})")

    print("Riduzione dimensionale con UMAP (2D)...")
    reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, len(vectors) - 1))
    coords = reducer.fit_transform(vectors)

    codart = [m.get("codart", "") for m in metadatas]
    descrizioni = [m.get("descrizione", "") for m in metadatas]
    labels = [f"<b>{c}</b><br>{d}" for c, d in zip(codart, descrizioni)]

    fig = go.Figure(go.Scatter(
        x=coords[:, 0],
        y=coords[:, 1],
        mode="markers",
        marker=dict(size=8, opacity=0.75, colorscale="Viridis",
                    color=list(range(len(coords)))),
        text=labels,
        hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Spazio semantico articoli IAB — {len(vectors)} articoli (UMAP 2D)",
        xaxis_title="UMAP 1",
        yaxis_title="UMAP 2",
        width=1100,
        height=750,
        template="plotly_white",
    )

    out_path = os.path.join(os.path.dirname(__file__), "embeddings_map.html")
    fig.write_html(out_path)
    print(f"Mappa salvata in: {out_path}")

    import webbrowser
    webbrowser.open(f"file:///{out_path}")


if __name__ == "__main__":
    main()
