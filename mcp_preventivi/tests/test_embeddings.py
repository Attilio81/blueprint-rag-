# mcp_preventivi/tests/test_embeddings.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock


def test_cerca_simili_restituisce_lista():
    mock_results = {
        "ids": [["VITE-M6", "DADO-M6"]],
        "distances": [[0.1, 0.3]],
        "metadatas": [[
            {"codart": "VITE-M6", "descrizione": "Vite M6x20 zincata", "unita_misura": "PZ", "bloccato": "N", "esaurito": "N"},
            {"codart": "DADO-M6", "descrizione": "Dado M6 zincato", "unita_misura": "PZ", "bloccato": "N", "esaurito": "N"},
        ]],
    }

    mock_collection = MagicMock()
    mock_collection.count.return_value = 10
    mock_collection.query.return_value = mock_results

    mock_embedder = MagicMock()
    mock_embedder.get_embedding.return_value = [0.1] * 3072

    with patch("embeddings._get_collection", return_value=mock_collection), \
         patch("embeddings._get_embedder", return_value=mock_embedder):
        from embeddings import cerca_simili
        result = cerca_simili("vite m6", n_risultati=2)

    assert len(result) == 2
    assert result[0]["codart"] == "VITE-M6"
    assert "score" in result[0]
    assert result[0]["score"] < result[1]["score"]  # distanza crescente
