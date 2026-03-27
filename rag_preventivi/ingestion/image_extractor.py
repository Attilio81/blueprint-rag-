# ingestion/image_extractor.py
import base64
import time
import pymupdf
from pathlib import Path
from config import (
    PAGE_DPI, CHUNK_SIZE, CHUNK_OVERLAP, VISION_PROMPT, VISION_PROVIDER,
    LMSTUDIO_BASE_URL, LMSTUDIO_VISION_MODEL,
    GEMINI_VISION_MODEL, GEMINI_RATE_LIMIT_SECONDS,
    OPENAI_VISION_MODEL,
)
from ingestion.text_extractor import _chunk_text


def _describe_with_lmstudio(image_bytes: bytes) -> str:
    from openai import OpenAI
    client = OpenAI(base_url=LMSTUDIO_BASE_URL, api_key="lm-studio")
    b64 = base64.b64encode(image_bytes).decode()
    response = client.chat.completions.create(
        model=LMSTUDIO_VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
        extra_body={"chat_template_kwargs": {"thinking": False}},
    )
    text = response.choices[0].message.content or ""
    if "</think>" in text:
        text = text.split("</think>", 1)[-1]
    return text.strip()


def _describe_with_gemini(image_bytes: bytes) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
    response = client.models.generate_content(
        model=GEMINI_VISION_MODEL,
        contents=[VISION_PROMPT, image_part],
    )
    time.sleep(GEMINI_RATE_LIMIT_SECONDS)
    return response.text.strip() if response.text else ""


def _describe_with_openai(image_bytes: bytes) -> str:
    from openai import OpenAI
    client = OpenAI()  # legge OPENAI_API_KEY da .env
    b64 = base64.b64encode(image_bytes).decode()
    response = client.chat.completions.create(
        model=OPENAI_VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )
    return response.choices[0].message.content.strip()


_PROVIDERS = {
    "lmstudio": _describe_with_lmstudio,
    "gemini":   _describe_with_gemini,
    "openai":   _describe_with_openai,
}


def describe_page_with_vision(image_bytes: bytes) -> str:
    """Dispatches to the configured vision provider (VISION_PROVIDER in config.py)."""
    fn = _PROVIDERS.get(VISION_PROVIDER)
    if fn is None:
        raise ValueError(f"VISION_PROVIDER '{VISION_PROVIDER}' non valido. Scegli: {list(_PROVIDERS)}")
    return fn(image_bytes)


def extract_vision_chunks(pdf_path: str) -> list[dict]:
    """
    Rasterizes each PDF page in memory and describes it with the configured vision provider.
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
            image_bytes = pix.tobytes("png")
            del pix

            description = describe_page_with_vision(image_bytes)
            for chunk in _chunk_text(description, CHUNK_SIZE, CHUNK_OVERLAP):
                result.append({
                    "content": chunk,
                    "source": source,
                    "page": page_num + 1,
                    "type": "vision",
                })
    finally:
        doc.close()

    return result
