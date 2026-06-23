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
    # Plantilla A tiene "PROPUESTA ECONÓMICA" como línea título independiente.
    # Plantilla B también la menciona en una frase ("nuestra propuesta económica:"),
    # por eso verificamos que alguna línea sea sustancialmente solo esa frase.
    for l in texto.splitlines():
        n = _norm(l.strip())
        if n.startswith("PROPUESTA ECON") and len(n) < 30:
            return "A"
    return "B"


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
VOCABULARIO = [
    "FOTOCHECKS", "ACCESORIOS", "INSUMOS", "KIT DE LIMPIEZA", "MANTENIMIENTO",
    "IMPRESORAS", "OTROS", "PVC", "PVC ADHESIVO", "TARJETAS IMPRESAS",
    "GIFT CARD", "ZENIUS 2 CLASSIC", "PRIMACY 2 DUPLEX",
]

_MONTO_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\.\d{2}$")
# Código de producto = primera palabra de la línea de ítem (plantilla A): empieza con
# mayúscula y contiene al menos un dígito o un guion. Cubre F400102, ACL001, RCT223NAAA,
# COLLARCOLL-SUB1.8, SERV-MANT-IMPR-EVO, YF-SINLOGO. NO matchea palabras de descripción
# (COLLAR, FOTOCHECK, PORTAFOTOCHECK, SERVICIO, SUBLIMADO...) que no tienen dígito ni guion.
_CODIGO_RE = re.compile(r"^[A-Z][A-Z0-9.\-]*[-0-9][A-Z0-9.\-]*$")


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
        n = _norm(l)
        # Cortar en la línea del total final: "(SUB)TOTAL <moneda> <monto>" — exige la
        # moneda para NO cortar en una cabecera de columna suelta ("Subtotal", "Total Inc
        # Igv") que en algunas plantillas B aparece ANTES de los ítems.
        is_total = (bool(re.match(r"(SUB)?TOTAL\s+(US\$|USD|S/)", n))
                    or "CONDICIONES" in n)
        if is_total:
            cut = i
            break
    body = nz[:cut]

    def es_inicio_item(idx: int) -> bool:
        l = body[idx]
        if plantilla == "A":
            # Rechazar números de propuesta (ej. DC-001-00000062) que no son códigos de item
            if _NUM_RE.search(l):
                return False
            # Limpiar caracteres no-ASCII que pueden romper el parsing (ej. ￾P)
            l_limpio = "".join(c for c in l if ord(c) < 128)
            # Match solo la primera palabra (código de producto)
            primer_palabra = l_limpio.split()[0] if l_limpio.split() else ""
            return bool(_CODIGO_RE.match(primer_palabra))
        # Plantilla B: un ítem empieza con un índice de 1-2 dígitos seguido de DESCRIPCIÓN.
        # "01 IMPRESORA DE CARNETS" (índice + texto en la misma línea) es item solo si el
        # resto tiene letras — así NO confunde la fila de precios "01 762.71 762.71 900.00"
        # (resto sin letras) con un ítem nuevo.
        m = re.match(r"^\d{1,2}\s+(\S.*)$", l)
        if m:
            return bool(re.search(r"[A-Za-z]", m.group(1)))
        # "01" solo en su línea (descripción en la línea siguiente).
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
        # Buscar montos dentro de los tokens de todas las líneas del bloque
        montos = []
        for linea in b:
            for token in linea.split():
                if _MONTO_RE.match(token):
                    montos.append(float(token.replace(",", "")))
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


_GENERICOS = {"CLIENTES VARIOS", "CLIENTE VARIOS", "VARIOS"}


def nombre_destino(categoria: str, cliente: str, fecha: str | None) -> str:
    base = f"DC {categoria} - {cliente}"
    if fecha:
        base += f" {fecha}"
    return base + ".pdf"


def analizar_texto(texto: str) -> dict:
    plantilla = detectar_plantilla(texto)
    numero = extraer_numero(texto)
    fecha = extraer_fecha(texto, plantilla)
    cliente_crudo = extraer_cliente(texto, plantilla)
    cliente = limpiar_cliente(cliente_crudo) if cliente_crudo else ""
    categoria, montos = clasificar(texto, plantilla)

    revisar = (
        not numero
        or not cliente
        or len(cliente) < 3
        or _norm(cliente) in _GENERICOS
        or categoria == "OTROS"
        or not montos
    )
    return {
        "plantilla": plantilla,
        "numero": numero,
        "fecha": fecha,
        "cliente": cliente,
        "categoria": categoria,
        "montos": montos,
        "confianza": "revisar" if revisar else "alta",
        "sugerido": nombre_destino(categoria, cliente or "SIN CLIENTE", fecha),
    }


def analizar_pdf(path) -> dict:
    d = analizar_texto(extraer_texto(path))
    d["archivo"] = str(path)
    return d


def planificar_carpeta(carpeta) -> list[dict]:
    """Escanea una carpeta de PDFs, analiza cada uno, devuelve lista de items.

    Si un PDF está dañado, lo agrega como revisar sin tumbar el lote.
    """
    carpeta = Path(carpeta)
    items = []
    for pdf in sorted(carpeta.glob("*.pdf")):
        try:
            items.append(analizar_pdf(pdf))
        except Exception as e:  # PDF dañado no debe tumbar el lote
            items.append({
                "archivo": str(pdf),
                "cliente": "",
                "categoria": "OTROS",
                "fecha": None,
                "confianza": "revisar",
                "error": str(e),
                "sugerido": pdf.name
            })
    return items


def _destino_unico(carpeta, nombre: str, ocupados: set) -> str:
    """Anti-colisión: si nombre ya existe, agrega (2), (3), etc.

    Chequea tanto el set de ocupados como el FS.
    """
    carpeta = Path(carpeta)
    if nombre not in ocupados and not (carpeta / nombre).exists():
        return nombre
    raiz, ext = (nombre[:-4], ".pdf") if nombre.lower().endswith(".pdf") else (nombre, "")
    i = 2
    while True:
        cand = f"{raiz} ({i}){ext}"
        if cand not in ocupados and not (carpeta / cand).exists():
            return cand
        i += 1


def aplicar(items: list[dict], carpeta) -> dict:
    """Renombra archivos IN PLACE basado en item["nombre_final"] o item["sugerido"].

    Devuelve {"renombrados": N, "revisar": M, "errores": [...]}
    """
    carpeta = Path(carpeta)
    ocupados: set = set()
    renombrados, revisar, errores = 0, 0, []

    for it in items:
        # PDF ilegible/dañado: dejarlo INTACTO (conservar su nombre original es la acción
        # segura) y solo marcarlo para revisar. Nunca renombrar lo que no se pudo leer.
        if it.get("error"):
            revisar += 1
            continue

        nombre = it.get("nombre_final") or it.get("sugerido")
        origen = Path(it["archivo"])

        if not nombre or not origen.exists():
            errores.append(origen.name)
            continue

        if nombre == origen.name:  # ya tiene el nombre destino: no-op (no duplicar a " (2)")
            ocupados.add(nombre)
            if it.get("confianza") == "revisar":
                revisar += 1
            continue

        destino_nombre = _destino_unico(carpeta, nombre, ocupados)
        try:
            origen.rename(carpeta / destino_nombre)
            ocupados.add(destino_nombre)
            renombrados += 1
        except OSError as e:
            errores.append(f"{origen.name}: {e}")

        if it.get("confianza") == "revisar":
            revisar += 1

    return {"renombrados": renombrados, "revisar": revisar, "errores": errores}
