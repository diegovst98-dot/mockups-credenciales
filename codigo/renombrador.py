"""Renombrador de cotizaciones DC: lee, clasifica y renombra PDFs de cotizaciones."""
from __future__ import annotations
from pathlib import Path
import pypdfium2 as pdfium
import re
import unicodedata


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()


_NUM_RE = re.compile(r"\b[A-Z]{2}-\d{2,5}-\d{3,8}\b")

_MESES = {
    "ENERO": "01", "FEBRERO": "02", "MARZO": "03", "ABRIL": "04",
    "MAYO": "05", "JUNIO": "06", "JULIO": "07", "AGOSTO": "08",
    "SETIEMBRE": "09", "SEPTIEMBRE": "09", "OCTUBRE": "10",
    "NOVIEMBRE": "11", "DICIEMBRE": "12",
}


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


def extraer_fecha(texto: str, plantilla: str) -> str | None:
    if plantilla == "A":
        m = re.search(r"Fecha:\s*(\d{2})/(\d{2})/\d{4}", texto)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
        return None
    # Plantilla B: "Lima, 11 de Junio del 2026"
    m = re.search(r"Lima,\s*(\d{1,2})\s+de\s+([A-Za-zñÑáéíóú]+)\s+del?\s+\d{4}", texto)
    if m:
        dia = m.group(1).zfill(2)
        mes = _MESES.get(_norm(m.group(2)))
        if mes:
            return f"{dia}-{mes}"
    return None
