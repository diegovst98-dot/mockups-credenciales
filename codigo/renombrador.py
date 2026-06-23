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


_SUFIJO_SOC = re.compile(r"(S\.?A\.?C|E\.?I\.?R\.?L|S\.?A|S\.?R\.?L)\.?$")


def extraer_cliente(texto: str, plantilla: str) -> str | None:
    nz = [l.strip() for l in texto.splitlines() if l.strip()]
    if plantilla == "A":
        for i, l in enumerate(nz):
            if _norm(l).startswith("FECHA") and i + 1 < len(nz):
                return nz[i + 1]
        return None
    # Plantilla B: primera linea bajo "Señores:" que no sea "Presente.-"
    for i, l in enumerate(nz):
        if _norm(l).rstrip(":") == "SENORES":
            for j in range(i + 1, len(nz)):
                if "PRESENTE" not in _norm(nz[j]):
                    return nz[j]
    return None


def limpiar_cliente(nombre: str) -> str:
    c = nombre.strip()
    # Primero remover SOCIEDAD ANONIMA CERRADA (redundancia con S.A.C.)
    c = re.sub(r"\s+SOCIEDAD ANONIMA CERRADA", "", c, flags=re.I).strip()
    # Luego revisar si hay " - " con sufijo societario en el lado derecho
    if " - " in c:
        parts = c.split(" - ")
        derecho = parts[-1].strip()
        izquierdo = parts[0].strip()
        # Si el lado derecho tiene un sufijo y ambos lados empiezan con las mismas palabras,
        # es redundancia (mismo nombre, dos formas) -> tomar solo el lado derecho
        if _SUFIJO_SOC.search(_norm(derecho)):
            # Extraer las primeras palabras de cada lado para comparar
            palabras_izq = izquierdo.split()[:2]
            palabras_der = derecho.split()[:2]
            if palabras_izq == palabras_der:
                c = derecho
    c = re.sub(r'[\\/:*?"<>|]', "", c)
    if len(c) > 45:
        c = c[:45].strip()
    return c
