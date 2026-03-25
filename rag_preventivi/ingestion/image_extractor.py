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
    """Sends a PNG image to Gemini Vision and returns the description."""
    model = genai.GenerativeModel(VISION_MODEL)
    image_part = {"mime_type": "image/png", "data": image_bytes}
    response = model.generate_content([VISION_PROMPT, image_part])
    return response.text.strip() if response.text else ""


def extract_vision_chunks(pdf_path: str) -> list[dict]:
    """
    Rasterizes each PDF page in memory and describes it with Gemini Vision.
    Returns list of dicts with: content, source, page, type.
    """
    source = Path(pdf_path).name
    doc = pymupdf.open(pdf_path)
    result = []
    mat = pymupdf.Matrix(PAGE_DPI / 72, PAGE_DPI / 72)  # 150 DPI

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)
            image_bytes = pix.tobytes("png")  # in-memory, no temp files

            description = describe_page_with_vision(image_bytes)
            if description:
                result.append({
                    "content": description,
                    "source": source,
                    "page": page_num + 1,
                    "type": "vision",
                })
            time.sleep(RATE_LIMIT_SECONDS)  # Gemini rate limiting
    finally:
        doc.close()

    return result
