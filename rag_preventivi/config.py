import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "Preventivi"
CHROMA_PATH = str(BASE_DIR / "chroma_db")
INDEXED_FILE = str(BASE_DIR / "indexed.json")

CHROMA_COLLECTION = "preventivi_leonardo_v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 6
PAGE_DPI = 150
EMBEDDING_MODEL = "gemini-embedding-2-preview"
EMBEDDING_DIMENSIONS = 3072
NON_ASCII_THRESHOLD = 0.30

# ── Vision provider ────────────────────────────────────────────────────────
# Scegli il provider per l'analisi visiva delle pagine PDF.
#
# "lmstudio"  — modello locale via LM Studio (OpenAI-compatible, localhost)
#               Nessun costo, privacy totale, richiede GPU/RAM adeguata
#               Modelli consigliati: qwen/qwen3.5-9b, llava-v1.6, minicpm-v
#               Richiede LM Studio in esecuzione su localhost
#
# "gemini"    — Google Gemini Vision API
#               Modelli: gemini-2.5-flash (veloce/economico), gemini-2.5-pro (qualità massima)
#               Richiede GOOGLE_API_KEY in .env
#
# "openai"    — OpenAI GPT-4o Vision API
#               Modelli: gpt-4o-mini (economico), gpt-4o (qualità massima)
#               Richiede OPENAI_API_KEY in .env
#
VISION_PROVIDER = "lmstudio"

# Impostazioni LM Studio (usate se VISION_PROVIDER = "lmstudio")
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
LMSTUDIO_VISION_MODEL = "qwen/qwen3.5-9b"

# Impostazioni Gemini (usate se VISION_PROVIDER = "gemini")
GEMINI_VISION_MODEL = "gemini-2.5-flash"
GEMINI_RATE_LIMIT_SECONDS = 1.0   # rispetta i limiti API gratuiti

# Impostazioni OpenAI (usate se VISION_PROVIDER = "openai")
OPENAI_VISION_MODEL = "gpt-4o-mini"

# Descrizione del progetto — personalizza questi campi per il tuo caso d'uso
PROJECT_CONTEXT = "preventivi edilizi del Centro Commerciale Leonardo di Imola"

VISION_PROMPT = """Analizza questa pagina di documento commerciale.
Restituisci SOLO il contenuto in Markdown strutturato:
- Usa tabelle Markdown per le voci di preventivo (| Codice | Descrizione | Qt | Prezzo |)
- Usa ## per i titoli di sezione
- Riporta tutti i valori visibili: prezzi, codici articolo, quantità, nomi aziende, contatti
Non aggiungere testo che non sia nella pagina. Non spiegare, solo estrarre."""
