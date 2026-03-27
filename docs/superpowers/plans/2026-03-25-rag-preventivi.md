# RAG Preventivi Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Costruire un agente conversazionale CLI che risponde a domande sui preventivi edilizi in linguaggio naturale, aggregando informazioni da testo E immagini di PDF multipli.

**Architecture:** Pipeline di ingestion custom a due passaggi (testo via pymupdf + vision via Gemini 2.0 Flash). I chunk vengono embeddati con GeminiEmbedder e salvati in ChromaDB locale. L'agente Agno usa DeepSeek come LLM e cerca nel knowledge base tramite `search_knowledge=True`.

**Tech Stack:** Python 3.11+, Agno, DeepSeek API, Gemini API (embedding + vision), ChromaDB, pymupdf, python-dotenv, Pillow

---

## File Structure

```
C:\Progetti Pilota\EsploraPreventivi\
├── rag_preventivi/
│   ├── config.py                 # Costanti, path, nomi modelli
│   ├── knowledge.py              # Costruisce ChromaDb + Knowledge per Agno
│   ├── agent.py                  # Definizione Agent Agno con DeepSeek
│   ├── main.py                   # Entry point CLI (loop interattivo)
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── text_extractor.py     # Estrazione testo + chunking via pymupdf
│   │   ├── image_extractor.py    # Rasterizzazione pagine + Gemini Vision
│   │   └── pipeline.py           # Orchestrazione ingestion + deduplicazione
│   └── tests/
│       ├── __init__.py
│       ├── test_text_extractor.py
│       ├── test_image_extractor.py
│       └── test_pipeline.py
├── Preventivi/                   # PDF sorgente (già presenti)
├── chroma_db/                    # Auto-creata al primo run
├── indexed.json                  # Traccia file già indicizzati (auto-creato)
├── requirements.txt
└── .env                          # GOOGLE_API_KEY, DEEPSEEK_API_KEY
```

**Import paths Agno verificati dalla documentazione:**
- `from agno.knowledge.embedder.google import GeminiEmbedder`
- `from agno.knowledge.knowledge import Knowledge`
- `from agno.vectordb.chroma import ChromaDb`
- `from agno.models.deepseek import DeepSeek`
- `from agno.agent import Agent`

> **Deviazioni intenzionali dal PRD:**
> - I PDF stanno in `Preventivi/` (radice progetto) non in `rag_preventivi/documents/` — già presenti su disco
> - `indexed.json` è in radice progetto per co-locazione con `Preventivi/`
> - Il PRD usa `agno.embedder.google` per GeminiEmbedder — **errato**: il path corretto è `agno.knowledge.embedder.google` (verificato da docs ufficiali Agno)
> - Il file PROT_31 si chiama `PROT.31 IAB SOC.COOP._130125.pdf` (con punti e spazi) — il PRD usa underscore: **il piano usa il nome reale su disco**

---

## Task 1: Setup Progetto

**Files:**
- Create: `rag_preventivi/requirements.txt`
- Create: `rag_preventivi/.env.example`
- Create: `rag_preventivi/config.py`
- Create: `rag_preventivi/tests/conftest.py`

- [ ] **Step 1: Crea requirements.txt**

```
agno
chromadb
pymupdf
google-generativeai
python-dotenv
Pillow
pytest
```

- [ ] **Step 2: Crea .env.example**

```
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

- [ ] **Step 3: Crea config.py**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "Preventivi"
CHROMA_PATH = str(BASE_DIR / "chroma_db")
INDEXED_FILE = str(BASE_DIR / "indexed.json")

CHROMA_COLLECTION = "preventivi_leonardo"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 6
PAGE_DPI = 150
VISION_MODEL = "gemini-2.0-flash"
EMBEDDING_MODEL = "gemini-embedding-exp-03-07"
RATE_LIMIT_SECONDS = 1.0
NON_ASCII_THRESHOLD = 0.30
```

- [ ] **Step 4: Crea tests/conftest.py (fix sys.path per pytest)**

```python
# tests/conftest.py
import sys
from pathlib import Path

# Aggiunge rag_preventivi/ al sys.path per permettere import bare (config, ingestion, ...)
sys.path.insert(0, str(Path(__file__).parent.parent))
```

- [ ] **Step 5: Installa dipendenze**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi"
pip install -r rag_preventivi/requirements.txt
```

- [ ] **Step 6: Crea .env reale con le API key vere**

Copia `.env.example` in `.env` e inserisci le chiavi reali.

---

## Task 2: Knowledge Base Setup

**Files:**
- Create: `rag_preventivi/knowledge.py`

- [ ] **Step 1: Crea knowledge.py**

```python
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from config import CHROMA_PATH, CHROMA_COLLECTION, EMBEDDING_MODEL, TOP_K_RESULTS


def build_knowledge() -> tuple[Knowledge, ChromaDb]:
    """Costruisce e restituisce il knowledge base Agno + ChromaDb."""
    embedder = GeminiEmbedder(id=EMBEDDING_MODEL)
    vector_db = ChromaDb(
        collection=CHROMA_COLLECTION,
        path=CHROMA_PATH,
        persistent_client=True,
        embedder=embedder,
    )
    knowledge = Knowledge(
        vector_db=vector_db,
        max_results=TOP_K_RESULTS,
    )
    return knowledge, vector_db
```

- [ ] **Step 2: Verifica import path `Document` di Agno (OBBLIGATORIO prima di Task 5)**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -c "from agno.document import Document; print('Document OK:', Document)"
```

Se fallisce, prova in ordine:
```bash
python -c "from agno.knowledge.document import Document; print('OK')"
python -c "from agno.models.document import Document; print('OK')"
```

Usa il path che funziona in `pipeline.py`. **Non procedere a Task 5 senza aver risolto questo.**

- [ ] **Step 3: Test smoke — verifica ChromaDb si inizializza senza errori**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -c "from knowledge import build_knowledge; kb, vdb = build_knowledge(); print('OK:', kb)"
```

Expected: stampa `OK:` senza eccezioni.

---

## Task 3: Text Extractor

**Files:**
- Create: `rag_preventivi/ingestion/__init__.py`
- Create: `rag_preventivi/ingestion/text_extractor.py`
- Create: `rag_preventivi/tests/__init__.py`
- Create: `rag_preventivi/tests/test_text_extractor.py`

- [ ] **Step 1: Scrivi il test**

```python
# tests/test_text_extractor.py
import pytest
from pathlib import Path
from ingestion.text_extractor import extract_text_chunks, is_corrupted_pdf

SAMPLE_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "ONICE.pdf"


def test_extract_text_chunks_returns_list():
    chunks = extract_text_chunks(str(SAMPLE_PDF))
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_chunk_has_required_keys():
    chunks = extract_text_chunks(str(SAMPLE_PDF))
    chunk = chunks[0]
    assert "content" in chunk
    assert "source" in chunk
    assert "page" in chunk
    assert chunk["type"] == "text"
    assert len(chunk["content"]) > 0


def test_is_corrupted_pdf_returns_bool():
    result = is_corrupted_pdf(str(SAMPLE_PDF))
    assert isinstance(result, bool)
    assert result is False  # ONICE.pdf ha testo valido


def test_chunk_size_within_bounds():
    from config import CHUNK_SIZE
    chunks = extract_text_chunks(str(SAMPLE_PDF))
    for chunk in chunks:
        assert len(chunk["content"]) <= CHUNK_SIZE * 1.5  # tolleranza per overlap
```

- [ ] **Step 2: Esegui i test — devono FALLIRE**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -m pytest tests/test_text_extractor.py -v
```

Expected: `ModuleNotFoundError: No module named 'ingestion'` o simile.

- [ ] **Step 3: Implementa text_extractor.py**

```python
# ingestion/text_extractor.py
import pymupdf
from pathlib import Path
from config import CHUNK_SIZE, CHUNK_OVERLAP, NON_ASCII_THRESHOLD


def is_corrupted_pdf(pdf_path: str) -> bool:
    """Restituisce True se >30% dei caratteri estratti sono non-ASCII."""
    doc = pymupdf.open(pdf_path)
    total_chars = 0
    non_ascii_chars = 0
    for page in doc:
        text = page.get_text()
        total_chars += len(text)
        non_ascii_chars += sum(1 for c in text if ord(c) > 127)
    doc.close()
    if total_chars == 0:
        return True
    return (non_ascii_chars / total_chars) > NON_ASCII_THRESHOLD


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide il testo in chunk con overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def extract_text_chunks(pdf_path: str) -> list[dict]:
    """
    Estrae testo da un PDF e lo divide in chunk.
    Restituisce lista di dict con: content, source, page, type.
    """
    source = Path(pdf_path).name
    doc = pymupdf.open(pdf_path)
    result = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        if not text:
            continue
        for chunk_text in _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP):
            if chunk_text.strip():
                result.append({
                    "content": chunk_text.strip(),
                    "source": source,
                    "page": page_num + 1,
                    "type": "text",
                })
    doc.close()
    return result
```

- [ ] **Step 4: Esegui i test — devono PASSARE**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -m pytest tests/test_text_extractor.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi"
git add rag_preventivi/
git commit -m "feat: add text extractor with chunking and corrupted PDF detection"
```

---

## Task 4: Image Extractor (Vision Pipeline)

**Files:**
- Create: `rag_preventivi/ingestion/image_extractor.py`
- Create: `rag_preventivi/tests/test_image_extractor.py`

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_image_extractor.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from ingestion.image_extractor import describe_page_with_vision, extract_vision_chunks

SAMPLE_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "ONICE.pdf"

MOCK_DESCRIPTION = "Scheda prodotto fioriera ONICE. Misure: Ø800mm H480mm 278kg."


def test_extract_vision_chunks_returns_list():
    with patch("ingestion.image_extractor.describe_page_with_vision", return_value=MOCK_DESCRIPTION):
        chunks = extract_vision_chunks(str(SAMPLE_PDF))
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_vision_chunk_has_required_keys():
    with patch("ingestion.image_extractor.describe_page_with_vision", return_value=MOCK_DESCRIPTION):
        chunks = extract_vision_chunks(str(SAMPLE_PDF))
    chunk = chunks[0]
    assert chunk["type"] == "vision"
    assert "content" in chunk
    assert "source" in chunk
    assert "page" in chunk
    assert MOCK_DESCRIPTION in chunk["content"]


def test_empty_vision_description_skipped():
    with patch("ingestion.image_extractor.describe_page_with_vision", return_value=""):
        chunks = extract_vision_chunks(str(SAMPLE_PDF))
    assert len(chunks) == 0
```

- [ ] **Step 2: Esegui i test — devono FALLIRE**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -m pytest tests/test_image_extractor.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implementa image_extractor.py**

```python
# ingestion/image_extractor.py
import time
import pymupdf
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from config import PAGE_DPI, VISION_MODEL, RATE_LIMIT_SECONDS

load_dotenv()

VISION_PROMPT = """Sei un assistente tecnico che analizza documenti edilizi e preventivi.
Descrivi in italiano tutto ciò che vedi in questa pagina:
- Prodotti con dimensioni, materiali, codici articolo
- Prezzi, importi, totali
- Nomi di aziende, fornitori, contatti
- Elementi grafici rilevanti (insegne, prospetti, schemi tecnici)
- Qualsiasi dato tecnico visibile
Sii preciso e strutturato. Non inventare dati non visibili."""


def describe_page_with_vision(image_bytes: bytes) -> str:
    """Invia un'immagine PNG a Gemini Vision e restituisce la descrizione."""
    model = genai.GenerativeModel(VISION_MODEL)
    image_part = {"mime_type": "image/png", "data": image_bytes}
    response = model.generate_content([VISION_PROMPT, image_part])
    return response.text.strip() if response.text else ""


def extract_vision_chunks(pdf_path: str) -> list[dict]:
    """
    Rasterizza ogni pagina del PDF in memoria e la descrive con Gemini Vision.
    Restituisce lista di dict con: content, source, page, type.
    """
    source = Path(pdf_path).name
    doc = pymupdf.open(pdf_path)
    result = []
    mat = pymupdf.Matrix(PAGE_DPI / 72, PAGE_DPI / 72)  # 150 DPI

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        image_bytes = pix.tobytes("png")  # in memoria, no file

        description = describe_page_with_vision(image_bytes)
        if description:
            result.append({
                "content": description,
                "source": source,
                "page": page_num + 1,
                "type": "vision",
            })
        time.sleep(RATE_LIMIT_SECONDS)  # rate limiting Gemini

    doc.close()
    return result
```

- [ ] **Step 4: Esegui i test — devono PASSARE (con mock)**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -m pytest tests/test_image_extractor.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add rag_preventivi/ingestion/image_extractor.py rag_preventivi/tests/test_image_extractor.py
git commit -m "feat: add vision extractor using Gemini 2.0 Flash page-as-image"
```

---

## Task 5: Ingestion Pipeline + Deduplicazione

**Files:**
- Create: `rag_preventivi/ingestion/pipeline.py`
- Create: `rag_preventivi/tests/test_pipeline.py`

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_pipeline.py
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from ingestion.pipeline import compute_file_hash, load_indexed, save_indexed, is_already_indexed

SAMPLE_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "ONICE.pdf"


def test_compute_file_hash_is_stable():
    h1 = compute_file_hash(str(SAMPLE_PDF))
    h2 = compute_file_hash(str(SAMPLE_PDF))
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_load_indexed_returns_empty_dict_if_missing():
    result = load_indexed("/nonexistent/path.json")
    assert result == {}


def test_save_and_load_indexed(tmp_path):
    index_file = str(tmp_path / "indexed.json")
    data = {"file.pdf": "abc123"}
    save_indexed(data, index_file)
    loaded = load_indexed(index_file)
    assert loaded == data


def test_is_already_indexed_false_for_new_file(tmp_path):
    index_file = str(tmp_path / "indexed.json")
    assert not is_already_indexed(str(SAMPLE_PDF), index_file)


def test_is_already_indexed_true_after_recording(tmp_path):
    index_file = str(tmp_path / "indexed.json")
    h = compute_file_hash(str(SAMPLE_PDF))
    save_indexed({"ONICE.pdf": h}, index_file)
    assert is_already_indexed(str(SAMPLE_PDF), index_file)


@patch("ingestion.pipeline.extract_text_chunks", return_value=[
    {"content": "Testo di test", "source": "ONICE.pdf", "page": 1, "type": "text"}
])
@patch("ingestion.pipeline.extract_vision_chunks", return_value=[
    {"content": "Descrizione visiva", "source": "ONICE.pdf", "page": 1, "type": "vision"}
])
@patch("ingestion.pipeline.ChromaDb")
@patch("ingestion.pipeline.GeminiEmbedder")
def test_run_ingestion_skips_already_indexed(mock_emb, mock_chroma, mock_vision, mock_text, tmp_path):
    """File già indicizzato con hash corretto → nessuna chiamata a extract_*."""
    index_file = str(tmp_path / "indexed.json")
    h = compute_file_hash(str(SAMPLE_PDF))
    save_indexed({"ONICE.pdf": h}, index_file)

    # Patcha load_indexed e DOCUMENTS_DIR a livello modulo.
    # Non patchare INDEXED_FILE direttamente: è usato come default arg
    # (valutato a definizione, non a call time) → non cambierebbe nulla.
    with patch("ingestion.pipeline.load_indexed", return_value={"ONICE.pdf": h}), \
         patch("ingestion.pipeline.DOCUMENTS_DIR", str(SAMPLE_PDF.parent)):
        from ingestion.pipeline import run_ingestion
        run_ingestion(reindex=False)

    mock_text.assert_not_called()
    mock_vision.assert_not_called()
```

- [ ] **Step 2: Esegui i test — devono FALLIRE**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -m pytest tests/test_pipeline.py -v
```

- [ ] **Step 3: Implementa pipeline.py**

```python
# ingestion/pipeline.py
import hashlib
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.vectordb.chroma import ChromaDb
from ingestion.text_extractor import extract_text_chunks, is_corrupted_pdf
from ingestion.image_extractor import extract_vision_chunks
from config import (
    DOCUMENTS_DIR, INDEXED_FILE, EMBEDDING_MODEL,
    CHROMA_PATH, CHROMA_COLLECTION,
)

load_dotenv()


def compute_file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_indexed(index_file: str = INDEXED_FILE) -> dict:
    if not os.path.exists(index_file):
        return {}
    with open(index_file, "r") as f:
        return json.load(f)


def save_indexed(data: dict, index_file: str = INDEXED_FILE) -> None:
    with open(index_file, "w") as f:
        json.dump(data, f, indent=2)


def is_already_indexed(pdf_path: str, index_file: str = INDEXED_FILE) -> bool:
    indexed = load_indexed(index_file)
    source = Path(pdf_path).name
    current_hash = compute_file_hash(pdf_path)
    return indexed.get(source) == current_hash


def _upsert_chunks(vector_db: ChromaDb, chunks: list[dict]) -> None:
    """Inserisce chunk nel vector DB come documenti Agno."""
    from agno.document import Document  # import lazy per flessibilità versione
    documents = [
        Document(
            content=c["content"],
            meta_data={"source": c["source"], "page": c["page"], "type": c["type"]},
        )
        for c in chunks
        if c.get("content", "").strip()
    ]
    if documents:
        vector_db.upsert(documents=documents)


def run_ingestion(reindex: bool = False) -> None:
    """
    Indicizza tutti i PDF in DOCUMENTS_DIR.
    Salta i file già indicizzati salvo --reindex.
    """
    embedder = GeminiEmbedder(id=EMBEDDING_MODEL)
    vector_db = ChromaDb(
        collection=CHROMA_COLLECTION,
        path=CHROMA_PATH,
        persistent_client=True,
        embedder=embedder,
    )

    pdf_files = list(Path(DOCUMENTS_DIR).glob("*.pdf"))
    if not pdf_files:
        print(f"Nessun PDF trovato in {DOCUMENTS_DIR}")
        return

    indexed = load_indexed()

    for pdf_path in pdf_files:
        source = pdf_path.name
        current_hash = compute_file_hash(str(pdf_path))

        if not reindex and indexed.get(source) == current_hash:
            print(f"[SKIP] {source} già indicizzato")
            continue

        print(f"\n[INGEST] {source}")
        corrupted = is_corrupted_pdf(str(pdf_path))

        # Passaggio 1: testo (solo se non corrotto)
        if not corrupted:
            text_chunks = extract_text_chunks(str(pdf_path))
            print(f"  → {len(text_chunks)} chunk testo")
            _upsert_chunks(vector_db, text_chunks)
        else:
            print(f"  ⚠ PDF con encoding corrotto — skip testo, solo vision")

        # Passaggio 2: vision (sempre)
        try:
            vision_chunks = extract_vision_chunks(str(pdf_path))
            print(f"  → {len(vision_chunks)} chunk vision")
            _upsert_chunks(vector_db, vision_chunks)
        except Exception as e:
            print(f"  ✗ Errore vision {source}: {e}")

        # Aggiorna indice
        indexed[source] = current_hash
        save_indexed(indexed)
        print(f"  ✓ {source} indicizzato")

    print("\nIngestion completata.")
```

- [ ] **Step 4: Esegui i test — devono PASSARE**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -m pytest tests/test_pipeline.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add rag_preventivi/ingestion/pipeline.py rag_preventivi/tests/test_pipeline.py
git commit -m "feat: add ingestion pipeline with SHA-256 deduplication"
```

---

## Task 6: Agent Agno + CLI

**Files:**
- Create: `rag_preventivi/agent.py`
- Create: `rag_preventivi/main.py`

- [ ] **Step 1: Crea agent.py**

```python
# agent.py
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from knowledge import build_knowledge

load_dotenv()


def build_agent() -> Agent:
    knowledge, _ = build_knowledge()
    return Agent(
        model=DeepSeek(id="deepseek-chat"),
        knowledge=knowledge,
        search_knowledge=True,
        instructions=[
            "Sei un assistente specializzato nell'analisi di preventivi edilizi.",
            "Il progetto è il Centro Commerciale Leonardo di Imola (BO), cliente IABGroup.",
            "Cita sempre il documento sorgente nella risposta.",
            "Se un'informazione proviene dall'analisi visiva di una pagina, indicalo con '(da analisi immagine)'.",
            "Per gli importi specifica sempre se IVA inclusa o esclusa.",
            "Se non trovi l'informazione nel knowledge base, dillo chiaramente.",
            "Rispondi sempre in italiano.",
        ],
        show_tool_calls=True,
        markdown=True,
    )
```

- [ ] **Step 2: Crea main.py**

```python
# main.py
import argparse
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="RAG Agent Preventivi")
    parser.add_argument("--reindex", action="store_true", help="Forza re-indicizzazione di tutti i PDF")
    parser.add_argument("--ingest-only", action="store_true", help="Solo indicizzazione, non avvia chat")
    args = parser.parse_args()

    if args.reindex or args.ingest_only:
        from ingestion.pipeline import run_ingestion
        run_ingestion(reindex=args.reindex)
        if args.ingest_only:
            return

    from agent import build_agent
    agent = build_agent()

    print("\n=== Agente RAG Preventivi Leonardo ===")
    print("Digita 'exit' per uscire.\n")

    while True:
        try:
            user_input = input("Tu: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            break
        agent.print_response(user_input, stream=True)
        print()

    print("Arrivederci!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Test smoke — verifica che l'agente si costruisca**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -c "from agent import build_agent; a = build_agent(); print('Agent OK:', a.model.id)"
```

Expected: `Agent OK: deepseek-chat`

- [ ] **Step 4: Commit**

```bash
git add rag_preventivi/agent.py rag_preventivi/main.py
git commit -m "feat: add Agno agent with DeepSeek and interactive CLI"
```

---

## Task 7: Prima Esecuzione e Test T1-T3

- [ ] **Step 1: Esegui l'ingestion testo-only (prima dell'aggiunta vision)**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python main.py --ingest-only
```

Osserva l'output: ogni PDF deve essere processato senza eccezioni.

- [ ] **Step 2: Test T1 — Prezzo fioriera ONICE Ø1200**

```bash
python main.py
```

Query: `Qual è il prezzo della fioriera ONICE Ø1200?`
Expected: risposta contenente `746` o `746,20` con riferimento a `ONICE.pdf`

- [ ] **Step 3: Test T2 — Totale insegne Prospetto Nord**

Query: `Totale insegne Prospetto Nord?`
Expected: `31.350` diurno / `32.755` notturno da `LEONARDO_IMOLA Prospetto NORD.pdf`

- [ ] **Step 4: Test T3 — Elenco fornitori**

Query: `Elenca tutti i fornitori`
Expected: Metalco, Adriatica Neon, Metro Infissi, Adria System

- [ ] **Step 5: Documenta risultati T1-T3 in un file di log**

```bash
# Salva l'output in un file per riferimento
python main.py 2>&1 | tee test_results_fase1.txt
```

---

## Task 8: Re-index --reindex e Test Completo

- [ ] **Step 1: Esegui reindex completo (testo + vision)**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python main.py --reindex --ingest-only
```

Attendi: ~45 chiamate Gemini Vision, ~1/sec. Stima: ~1-2 minuti.

- [ ] **Step 2: Verifica che indexed.json contenga tutti i 9 PDF**

```bash
python -c "import json; d=json.load(open('../indexed.json')); print(f'{len(d)} files:', list(d.keys()))"
```

Expected: 9 file elencati

- [ ] **Step 3: Test T4 — Prospetto Nord (vision)**

```bash
python main.py
```

Query: `Descrivi il prospetto Nord del Centro Commerciale Leonardo`
Expected: descrizione da chunk vision con riferimento alla facciata, insegne, pensilina

- [ ] **Step 4: Test T5 — Dimensioni fioriera ONICE (vision)**

Query: `Dimensioni fioriera ONICE dalla scheda tecnica`
Expected: `Ø800mm H480mm 278kg`, `Ø1200mm H620mm 753kg` con `(da analisi immagine)`

- [ ] **Step 5: Test T6 — Offerte con validità scaduta**

Query: `Offerte con validità scaduta al 25/03/2026`
Expected: menzione Metro Infissi con validità 10gg da 16/01/2025

---

## Task 9: Gestione PDF Corrotto

**Files:**
- Modify: `rag_preventivi/tests/test_text_extractor.py`

- [ ] **Step 1: Aggiungi test per PDF corrotto**

Aggiungi a `test_text_extractor.py`:

```python
CORRUPTED_PDF = Path(__file__).parent.parent.parent / "Preventivi" / "PROT.31 IAB SOC.COOP._130125.pdf"

def test_is_corrupted_pdf_detects_corrupted():
    if not CORRUPTED_PDF.exists():
        pytest.skip("PDF corrotto non disponibile")
    result = is_corrupted_pdf(str(CORRUPTED_PDF))
    assert result is True  # PROT_31 ha encoding corrotto
```

- [ ] **Step 2: Esegui il test**

```bash
cd "C:/Progetti Pilota/EsploraPreventivi/rag_preventivi"
python -m pytest tests/test_text_extractor.py::test_is_corrupted_pdf_detects_corrupted -v
```

- [ ] **Step 3: Se il test fallisce, aggiusta la soglia in config.py**

Se `PROT_31` non supera la soglia del 30%, abbassa `NON_ASCII_THRESHOLD` a `0.10` o usa
un approccio alternativo: conta caratteri di rimpiazzo unicode `\ufffd` o verifica se il testo
estratto è < 50 caratteri per pagina (PDF scansionato).

- [ ] **Step 4: Commit finale**

```bash
git add .
git commit -m "feat: complete RAG preventivi agent - Fase 1+2 all tests passing"
```

---

## Note Operative

### Import path da verificare a runtime

Il path `from agno.document import Document` potrebbe variare con la versione di agno.
Se fallisce, prova queste alternative in ordine:
```python
from agno.document import Document
from agno.knowledge.document import Document
from agno.models.document import Document
```

### Struttura ChromaDb con GeminiEmbedder

Il modello va passato come parametro `id` o `model`:
```python
GeminiEmbedder(id="gemini-embedding-exp-03-07")
# oppure se non accettato:
GeminiEmbedder(model="gemini-embedding-exp-03-07")
```

### Rate Limiting Gemini Embedding

Il rate limiting (`time.sleep(RATE_LIMIT_SECONDS)`) è applicato solo alle chiamate Vision. Per l'embedding, `GeminiEmbedder` fa chiamate dirette alla Gemini API durante `vector_db.upsert()`. Se si riceve un errore `429 Resource Exhausted` durante l'ingestion, aggiungere un `time.sleep(1)` tra le chiamate `_upsert_chunks` nel loop di `run_ingestion()`, oppure ridurre la dimensione del batch. Per il free tier (1500 RPM per `gemini-embedding-exp`) con 9 PDF da ~5 pagine e chunk da 1000 token, il limite non dovrebbe essere raggiunto normalmente.

### Esecuzione comandi

```bash
# Ingestion sola
python main.py --ingest-only

# Re-indicizzazione completa
python main.py --reindex --ingest-only

# Chat interattiva
python main.py

# Solo test
python -m pytest tests/ -v
```

### Variabili .env necessarie

```
GOOGLE_API_KEY=...    # per GeminiEmbedder + Gemini Vision
DEEPSEEK_API_KEY=...  # per DeepSeek chat
```
