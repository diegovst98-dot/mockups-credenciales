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

_LEGAL = re.compile(r"SOCIEDAD (ANONIMA|COMERCIAL)|RESPONSABILIDAD LIMITADA")


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


# (categoria, palabras clave) en orden de especificidad: la primera que matchea gana el bloque
# ACCESORIOS va antes de FOTOCHECKS porque "FOTOCHECK" es subcadena de "PORTAFOTOCHECK"
CATS = [
    ("MANTENIMIENTO",   ["SERVICIO DE MANTENIMIENTO", "SERV-MANT", "MANTENIMIENTO"]),
    ("KIT DE LIMPIEZA", ["KIT DE LIMPIEZA", "ACL001"]),
    ("IMPRESORAS",      ["IMPRESORA DE CARNETS", "IMPRESORA DE FOTOCHECKS",
                          "IMPRESORA EVOLIS", "ZENIUS", "PRIMACY", "ELYPSO", "BADGY"]),
    ("INSUMOS",         ["RIBBON", "RCT", "YMCKO", "PELICULA", "CINTA DE"]),
    ("ACCESORIOS",      ["PORTAFOTOCHECK", "COLLAR", "GANCHO", "YOYO", "ARNES"]),
    ("FOTOCHECKS",      ["FOTOCHECK"]),
    ("OTROS",           ["GIFT CARD", "TARJETA DE REGALO"]),
]
_MONTO_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\.\d{2}$")
# {1,5} soporta codigos de 1 letra inicial como F400102, P400112
_CODIGO_RE = re.compile(r"^[A-Z]{1,5}[A-Z0-9-]*\d[A-Z0-9-]*-?$")


def _categoria_de(desc: str) -> str | None:
    n = _norm(desc)
    for cat, kws in CATS:
        if any(k in n for k in kws):
            return cat
    return None


def clasificar(texto: str, plantilla: str) -> tuple[str, dict]:
    nz = [l.strip() for l in texto.splitlines() if l.strip()]
    # cortar antes de los totales / condiciones
    cut = len(nz)
    for i, l in enumerate(nz):
        if _norm(l).startswith("SUBTOTAL") or "CONDICIONES COMERCIAL" in _norm(l):
            cut = i
            break
    body = nz[:cut]

    def es_inicio_item(idx: int) -> bool:
        l = body[idx]
        if plantilla == "A":
            return bool(_CODIGO_RE.match(l))
        # Plantilla B: indice 1-2 digitos seguido de linea con texto
        if re.fullmatch(r"\d{1,2}", l):
            return idx + 1 < len(body) and bool(re.search(r"[A-Za-z]", body[idx + 1]))
        return False

    bloques, cur = [], None
    for i, l in enumerate(body):
        if es_inicio_item(i):
            cur = []
            bloques.append(cur)
        if cur is not None:
            cur.append(l)

    sums: dict[str, float] = {}
    for b in bloques:
        cat = _categoria_de(" ".join(b))
        montos = [float(x.replace(",", "")) for x in b if _MONTO_RE.match(x)]
        if cat and montos:
            sums[cat] = sums.get(cat, 0.0) + max(montos)

    ganadora = max(sums, key=sums.get) if sums else "OTROS"
    return ganadora, sums


def limpiar_cliente(nombre: str) -> str:
    c = nombre.strip()
    if " - " in c:
        izq, der = c.split(" - ", 1)
        # Colapsar SOLO la redundancia legal del ERP: "<largo> SOCIEDAD ANONIMA
        # CERRADA - <corto> S.A.C." -> "<corto> S.A.C.". Nunca partir marcas con
        # guion propio (ej. "CUTTING - EDGE PERU SAC") donde la izquierda no es
        # la forma legal larga.
        if _LEGAL.search(_norm(izq)) and _SUFIJO_SOC.search(_norm(der)):
            c = der.strip()
    c = re.sub(r"\s+SOCIEDAD ANONIMA CERRADA", "", c, flags=re.I).strip()
    c = re.sub(r'[\\/:*?"<>|]', "", c)
    if len(c) > 45:
        c = c[:45].strip()
    return c
