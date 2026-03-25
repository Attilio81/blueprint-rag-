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
