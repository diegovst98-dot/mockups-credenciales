"""Renombrador de cotizaciones DC: lee, clasifica y renombra PDFs de cotizaciones."""
from __future__ import annotations
from pathlib import Path
import pypdfium2 as pdfium
import re
import unicodedata


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()


_NUM_RE = re.compile(r"\b[A-Z]{2}-\d{2,5}-\d{3,8}\b")


def extraer_texto(path) -> str:
    """Devuelve el texto de la primera página del PDF."""
    pdf = pdfium.PdfDocument(str(path))
    try:
        textpage = pdf[0].get_textpage()
        return textpage.get_text_range()
    finally:
        pdf.close()


def detectar_plantilla(texto: str) -> str:
    return "A" if "PROPUESTA ECON" in _norm(texto) else "B"


def extraer_numero(texto: str) -> str | None:
    m = _NUM_RE.search(texto)
    return m.group(0) if m else None
