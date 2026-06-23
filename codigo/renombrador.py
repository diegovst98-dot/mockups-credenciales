"""Renombrador de cotizaciones DC: lee, clasifica y renombra PDFs de cotizaciones."""
from __future__ import annotations
from pathlib import Path
import pypdfium2 as pdfium


def extraer_texto(path) -> str:
    """Devuelve el texto de la primera página del PDF."""
    pdf = pdfium.PdfDocument(str(path))
    try:
        textpage = pdf[0].get_textpage()
        return textpage.get_text_range()
    finally:
        pdf.close()
