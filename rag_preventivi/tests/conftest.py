# tests/conftest.py
import sys
from pathlib import Path

# Adds rag_preventivi/ to sys.path so bare imports work (config, ingestion, ...)
sys.path.insert(0, str(Path(__file__).parent.parent))
