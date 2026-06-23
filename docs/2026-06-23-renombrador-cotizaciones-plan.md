# Renombrador de Cotizaciones DC — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar una pestaña "Renombrar Cotizaciones" a la app de Mockups que lee cotizaciones PDF de una carpeta, las clasifica por mayor monto y las renombra a `DC CATEGORÍA - CLIENTE DD-MM.pdf`.

**Architecture:** Lógica pura sin GUI en `codigo/renombrador.py` (funciones que reciben texto y devuelven datos, unit-testeables con cadenas sintéticas). La lectura de PDF (`pypdfium2`) y la GUI (`ttk.Notebook` en `app.py`) son capas delgadas encima. Renombra en el sitio con confirmación humana en una tabla.

**Tech Stack:** Python 3.12, Tkinter/ttk (ya en el bundle), `pypdfium2` (nueva, para texto de PDF), PyInstaller (`MockupsDISECOD.spec`).

**Spec:** `docs/2026-06-23-renombrador-cotizaciones-design.md`

## Global Constraints

- **Librería PDF = `pypdfium2`** (licencia permisiva). **PROHIBIDO PyMuPDF/fitz** (AGPL): el repo es público.
- **7 categorías automáticas:** `FOTOCHECKS · ACCESORIOS · INSUMOS · KIT DE LIMPIEZA · MANTENIMIENTO · IMPRESORAS · OTROS`. El desplegable de la GUI ofrece además `PVC`, `PVC ADHESIVO`, `TARJETAS IMPRESAS`, `GIFT CARD` y modelos de impresora.
- **Formato de nombre:** `DC {CATEGORÍA} - {CLIENTE} {DD-MM}.pdf` (sin fecha si no se halló). Colisión → ` (2)`, ` (3)`. Nunca sobrescribir.
- **Renombrar en el sitio** (sin copiar/mover/borrar).
- **No conectar al ERP.** Todo dato sale del texto del PDF.
- **Datos reales NO se commitean** (razón social/RUC/precios). Los unit tests usan cadenas sintéticas (clientes ficticios). La prueba de integración apunta a rutas locales y se salta (`skip`) si no existen.
- **Plataforma:** Windows. Nombres de archivo sin `\ / : * ? " < > |`.

---

## File Structure

- **Create `codigo/renombrador.py`** — lógica pura + I/O de lectura. Responsable de: extraer texto, detectar plantilla, extraer número/fecha/cliente, limpiar cliente, clasificar por monto, armar nombre destino, planificar carpeta, aplicar renombrado.
- **Create `tests/test_renombrador.py`** — unit tests con fixtures sintéticos + 1 test de integración skippable.
- **Modify `codigo/app.py`** — agregar `ttk.Notebook`, mover el flujo Mockups a un frame, agregar el frame "Renombrar Cotizaciones".
- **Modify `publicar.py`** — `ARCHIVOS += ["renombrador.py"]`.
- **Modify `MockupsDISECOD.spec`** — bundle `pypdfium2`.
- **Modify `requirements.txt`** — agregar `pypdfium2`.

---

### Task 1: Dependencia pypdfium2 + extracción de texto (validación de orden)

Esta tarea de-riesga lo más importante: confirmar el **orden real** del texto que da `pypdfium2` sobre los PDFs reales, antes de construir las anclas.

**Files:**
- Create: `codigo/renombrador.py`
- Modify: `requirements.txt`
- Test: `tests/test_renombrador.py`

**Interfaces:**
- Produces: `extraer_texto(path: str | Path) -> str` — texto de la página 1.

- [ ] **Step 1: Instalar la librería en el dev**

Run: `pip install pypdfium2`
Expected: instala sin error. (Licencia: PdfiumViewer / Apache-BSD, OK para repo público.)

- [ ] **Step 2: Agregar a requirements.txt**

Agregar al final de `requirements.txt`:
```
pypdfium2
```

- [ ] **Step 3: Escribir `extraer_texto` en renombrador.py**

Crear `codigo/renombrador.py` con:
```python
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
```

- [ ] **Step 4: Validar el orden real sobre un PDF real (gate de la tarea)**

Run (en una PC con un PDF real, p.ej. `Desktop\cotizaciones para renombrar\pdf 5.pdf`):
```bash
python -c "import sys; sys.path.insert(0,'codigo'); import renombrador as r; print(r.extraer_texto(r'C:/Users/Diego/Desktop/cotizaciones para renombrar/pdf 5.pdf'))"
```
Expected: imprime el texto con la cabecera en este orden (Plantilla A): `PROPUESTA ECONÓMICA` → `DC-001-...` → `Fecha: ...` → `<CLIENTE>` → `R.U.C. : ...`. **Si el orden difiere** (p.ej. columnas entremezcladas), anotarlo y ajustar las anclas de las Tasks 3-5 a ese orden real antes de seguir. Confirmar también un PDF Plantilla B (`pdf 1.pdf`): `DC-...` → `Lima, ...` → `Señores:` → `<CLIENTE>` → `Presente.-`.

- [ ] **Step 5: Commit**

```bash
git add codigo/renombrador.py requirements.txt
git commit -m "feat(renombrador): extraccion de texto con pypdfium2"
```

---

### Task 2: Detectar plantilla + extraer número de documento

**Files:**
- Modify: `codigo/renombrador.py`
- Test: `tests/test_renombrador.py`

**Interfaces:**
- Produces:
  - `detectar_plantilla(texto: str) -> str` — retorna `"A"` (ERP) o `"B"` (carta).
  - `extraer_numero(texto: str) -> str | None` — p.ej. `"DC-001-00000070"`, `"DJ-12845-2026"`, o `None`.

- [ ] **Step 1: Escribir los tests fallidos**

Crear `tests/test_renombrador.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))
import renombrador as r

TEXTO_A = """PROPUESTA ECONÓMICA
DC-001-00000070
Fecha: 23/06/2026
ACME PERU S.A.C.
R.U.C. : 20123456789
Señores:
Por medio de la presente nos es grato hacerle llegar nuestras propuesta económica:
CÓDIGO
DESCRIPCIÓN
CANT.
P. TOTAL
P. UNIT
RCT223NAAA
RIBBON NEGRO RINDE 2000 CARAS
2
86.44
172.88
SUBTOTAL
S/
172.88
"""

TEXTO_B = """DJ-12845-2026
Lima, 11 de Junio del 2026
Señores:
DEMO IMPORT E.I.R.L.
JUAN CONTACTO
Presente.-
Item
Descripción
Cant
Precio Unit
01
IMPRESORA DE CARNETS PRIMACY 2 DUPLEX
01
762.71
900.00
"""

def test_detectar_plantilla_A():
    assert r.detectar_plantilla(TEXTO_A) == "A"

def test_detectar_plantilla_B():
    assert r.detectar_plantilla(TEXTO_B) == "B"

def test_numero_plantilla_A():
    assert r.extraer_numero(TEXTO_A) == "DC-001-00000070"

def test_numero_plantilla_B_acepta_DJ():
    assert r.extraer_numero(TEXTO_B) == "DJ-12845-2026"

def test_numero_ausente():
    assert r.extraer_numero("sin numero aqui") is None
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/test_renombrador.py -v`
Expected: FAIL (`AttributeError: module 'renombrador' has no attribute 'detectar_plantilla'`).

- [ ] **Step 3: Implementar**

Agregar a `renombrador.py`:
```python
import re
import unicodedata

def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()

_NUM_RE = re.compile(r"\b[A-Z]{2}-\d{2,5}-\d{3,8}\b")

def detectar_plantilla(texto: str) -> str:
    return "A" if "PROPUESTA ECON" in _norm(texto) else "B"

def extraer_numero(texto: str) -> str | None:
    m = _NUM_RE.search(texto)
    return m.group(0) if m else None
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/test_renombrador.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/renombrador.py tests/test_renombrador.py
git commit -m "feat(renombrador): detectar plantilla y numero de documento"
```

---

### Task 3: Extraer fecha de emisión → DD-MM

**Files:**
- Modify: `codigo/renombrador.py`
- Test: `tests/test_renombrador.py`

**Interfaces:**
- Produces: `extraer_fecha(texto: str, plantilla: str) -> str | None` — `"23-06"` o `None`.

- [ ] **Step 1: Escribir los tests fallidos**

Agregar a `tests/test_renombrador.py`:
```python
def test_fecha_plantilla_A():
    assert r.extraer_fecha(TEXTO_A, "A") == "23-06"

def test_fecha_plantilla_B():
    assert r.extraer_fecha(TEXTO_B, "B") == "11-06"

def test_fecha_ausente():
    assert r.extraer_fecha("sin fecha", "A") is None
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/test_renombrador.py -k fecha -v`
Expected: FAIL.

- [ ] **Step 3: Implementar**

Agregar a `renombrador.py`:
```python
_MESES = {
    "ENERO": "01", "FEBRERO": "02", "MARZO": "03", "ABRIL": "04",
    "MAYO": "05", "JUNIO": "06", "JULIO": "07", "AGOSTO": "08",
    "SETIEMBRE": "09", "SEPTIEMBRE": "09", "OCTUBRE": "10",
    "NOVIEMBRE": "11", "DICIEMBRE": "12",
}

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
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/test_renombrador.py -k fecha -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/renombrador.py tests/test_renombrador.py
git commit -m "feat(renombrador): extraer fecha de emision en ambas plantillas"
```

---

### Task 4: Extraer y limpiar el nombre del cliente

**Files:**
- Modify: `codigo/renombrador.py`
- Test: `tests/test_renombrador.py`

**Interfaces:**
- Produces:
  - `extraer_cliente(texto: str, plantilla: str) -> str | None`
  - `limpiar_cliente(nombre: str) -> str`

- [ ] **Step 1: Escribir los tests fallidos**

Agregar a `tests/test_renombrador.py`:
```python
TEXTO_A_DNI = """PROPUESTA ECONÓMICA
DC-001-00000028
Fecha: 08/06/2026
CLIENTES VARIOS
D.N.I. :
Señores:
Por medio de la presente nos es grato hacerle llegar nuestras propuesta económica:
"""

def test_cliente_plantilla_A():
    assert r.extraer_cliente(TEXTO_A, "A") == "ACME PERU S.A.C."

def test_cliente_plantilla_A_con_dni():
    # ancla = linea bajo "Fecha:", funciona sin R.U.C.
    assert r.extraer_cliente(TEXTO_A_DNI, "A") == "CLIENTES VARIOS"

def test_cliente_plantilla_B_toma_empresa_no_contacto():
    assert r.extraer_cliente(TEXTO_B, "B") == "DEMO IMPORT E.I.R.L."

def test_limpiar_nombre_societario_largo():
    crudo = "SNIPER TECH SOCIEDAD ANONIMA CERRADA - SNIPER TECH S.A.C."
    assert r.limpiar_cliente(crudo) == "SNIPER TECH S.A.C."

def test_limpiar_conserva_guion_en_razon_social():
    # el cliente tiene guion propio y NO termina en sufijo societario en el lado derecho
    assert r.limpiar_cliente("CUTTING - EDGE PERU SAC") == "CUTTING - EDGE PERU SAC"

def test_limpiar_quita_caracteres_prohibidos():
    assert r.limpiar_cliente('A/B:C*?"<>|') == "ABC"
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/test_renombrador.py -k cliente -v`
Expected: FAIL.

- [ ] **Step 3: Implementar**

Agregar a `renombrador.py`:
```python
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
    if " - " in c:
        derecho = c.split(" - ")[-1].strip()
        if _SUFIJO_SOC.search(_norm(derecho)):
            c = derecho
    c = re.sub(r"\s+SOCIEDAD ANONIMA CERRADA", "", c, flags=re.I).strip()
    c = re.sub(r'[\\/:*?"<>|]', "", c)
    if len(c) > 45:
        c = c[:45].strip()
    return c
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/test_renombrador.py -k "cliente or limpiar" -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/renombrador.py tests/test_renombrador.py
git commit -m "feat(renombrador): extraer y limpiar nombre del cliente"
```

---

### Task 5: Clasificar por mayor monto

El corazón del sistema. Segmenta en bloques de ítem (según plantilla), clasifica cada bloque por la palabra clave más específica, suma el mayor monto de cada bloque por categoría, y gana la de mayor suma.

**Files:**
- Modify: `codigo/renombrador.py`
- Test: `tests/test_renombrador.py`

**Interfaces:**
- Produces: `clasificar(texto: str, plantilla: str) -> tuple[str, dict[str, float]]` — `(categoria_ganadora, montos_por_categoria)`.

- [ ] **Step 1: Escribir los tests fallidos**

Agregar a `tests/test_renombrador.py`:
```python
# Plantilla A: kit de limpieza unico
TEXTO_A_KIT = """PROPUESTA ECONÓMICA
DC-001-00000062
Fecha: 22/06/2026
DEMO HOLDING S.A.C.
R.U.C. : 20111111111
Señores:
CÓDIGO
DESCRIPCIÓN
CANT.
P. TOTAL
P. UNIT
ACL001
KIT DE LIMPIEZA - ACL001
1
90.00
90.00
SUBTOTAL
S/
90.00
"""

# Plantilla A: mezcla fotocheck (grande) + accesorios (chico) -> gana FOTOCHECKS
TEXTO_A_MIX = """PROPUESTA ECONÓMICA
DC-001-00000078
Fecha: 23/06/2026
DEMO MIX S.A.C.
R.U.C. : 20222222222
Señores:
CÓDIGO
DESCRIPCIÓN
CANT.
P. TOTAL
P. UNIT
TOTAL INC IGV
F400102
FOTOCHECK EN PVC AMBAS CARAS A COLOR
100
7.00
700.00
826.00
P400112
PORTAFOTOCHECK ACRILICO VERTICAL TRANSPARENTE
100
1.00
100.00
118.00
SUBTOTAL
S/
800.00
"""

# Plantilla B: impresora combo que menciona "incluye cinta/kit/tarjetas" -> gana IMPRESORAS
TEXTO_B_IMPR = """DC-12942-2026
Lima, 08 de Junio del 2026
Señores:
DEMO PRINT S.A.C.
Presente.-
Item
Descripción
01
IMPRESORA DE CARNETS ZENIUS 2 CLASSIC
Promoción incluye:
- 01 Cinta de color de 200 impresiones
- 100 tarjetas blancas PVC
- 01 tarjeta y 01 hisopo de limpieza
01
762.71
900.00
02
Tarjetas PVC Blanco
01
20.00
23.60
"""

def test_clasifica_kit_unico():
    cat, montos = r.clasificar(TEXTO_A_KIT, "A")
    assert cat == "KIT DE LIMPIEZA"

def test_clasifica_mezcla_gana_mayor_monto():
    cat, montos = r.clasificar(TEXTO_A_MIX, "A")
    assert cat == "FOTOCHECKS"
    assert montos["FOTOCHECKS"] > montos["ACCESORIOS"]

def test_clasifica_impresora_ignora_regalos_del_combo():
    cat, montos = r.clasificar(TEXTO_B_IMPR, "B")
    assert cat == "IMPRESORAS"

def test_clasifica_sin_match_es_otros():
    cat, montos = r.clasificar("PROPUESTA ECONÓMICA\nalgo raro\n5.00\nSUBTOTAL", "A")
    assert cat == "OTROS"
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/test_renombrador.py -k clasifica -v`
Expected: FAIL.

- [ ] **Step 3: Implementar**

Agregar a `renombrador.py`:
```python
# (categoria, palabras clave) en orden de especificidad: la primera que matchea gana el bloque
CATS = [
    ("MANTENIMIENTO",   ["SERVICIO DE MANTENIMIENTO", "SERV-MANT", "MANTENIMIENTO"]),
    ("KIT DE LIMPIEZA", ["KIT DE LIMPIEZA", "ACL001"]),
    ("IMPRESORAS",      ["IMPRESORA DE CARNETS", "IMPRESORA DE FOTOCHECKS",
                          "IMPRESORA EVOLIS", "ZENIUS", "PRIMACY", "ELYPSO", "BADGY"]),
    ("INSUMOS",         ["RIBBON", "RCT", "YMCKO", "PELICULA", "CINTA DE"]),
    ("FOTOCHECKS",      ["FOTOCHECK"]),
    ("ACCESORIOS",      ["PORTAFOTOCHECK", "COLLAR", "GANCHO", "YOYO", "ARNES"]),
    ("OTROS",           ["GIFT CARD", "TARJETA DE REGALO"]),
]
_MONTO_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\.\d{2}$")
_CODIGO_RE = re.compile(r"^[A-Z]{2,5}[A-Z0-9-]*\d[A-Z0-9-]*-?$")

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
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/test_renombrador.py -k clasifica -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/renombrador.py tests/test_renombrador.py
git commit -m "feat(renombrador): clasificacion por mayor monto con segmentacion por plantilla"
```

---

### Task 6: Orquestación — analizar_pdf, nombre destino y confianza

**Files:**
- Modify: `codigo/renombrador.py`
- Test: `tests/test_renombrador.py`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces:
  - `nombre_destino(categoria: str, cliente: str, fecha: str | None) -> str`
  - `analizar_texto(texto: str) -> dict` — claves: `numero, fecha, cliente, categoria, montos, plantilla, confianza, sugerido` (`sugerido` = nombre propuesto). `confianza` es `"alta"` o `"revisar"`.
  - `analizar_pdf(path) -> dict` — igual pero leyendo el PDF (agrega `archivo`).

- [ ] **Step 1: Escribir los tests fallidos**

Agregar a `tests/test_renombrador.py`:
```python
def test_nombre_destino_con_fecha():
    assert r.nombre_destino("FOTOCHECKS", "ACME PERU S.A.C.", "23-06") == "DC FOTOCHECKS - ACME PERU S.A.C. 23-06.pdf"

def test_nombre_destino_sin_fecha():
    assert r.nombre_destino("INSUMOS", "ACME", None) == "DC INSUMOS - ACME.pdf"

def test_analizar_texto_ok_confianza_alta():
    d = r.analizar_texto(TEXTO_A_MIX)
    assert d["categoria"] == "FOTOCHECKS"
    assert d["cliente"] == "DEMO MIX S.A.C."
    assert d["confianza"] == "alta"
    assert d["sugerido"] == "DC FOTOCHECKS - DEMO MIX S.A.C. 23-06.pdf"

def test_analizar_texto_clientes_varios_marca_revisar():
    d = r.analizar_texto(TEXTO_A_DNI + "ACL001\nKIT DE LIMPIEZA - ACL001\n1\n90.00\nSUBTOTAL")
    assert d["cliente"] == "CLIENTES VARIOS"
    assert d["confianza"] == "revisar"

def test_analizar_texto_otros_marca_revisar():
    d = r.analizar_texto("PROPUESTA ECONÓMICA\nDC-001-00000001\nFecha: 01-06\nX S.A.C.\nblah\nSUBTOTAL")
    assert d["confianza"] == "revisar"
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/test_renombrador.py -k "nombre_destino or analizar" -v`
Expected: FAIL.

- [ ] **Step 3: Implementar**

Agregar a `renombrador.py`:
```python
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
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/test_renombrador.py -k "nombre_destino or analizar" -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/renombrador.py tests/test_renombrador.py
git commit -m "feat(renombrador): orquestacion analizar_pdf, nombre destino y confianza"
```

---

### Task 7: Planificar carpeta y aplicar renombrado (en el sitio, anti-colisión)

**Files:**
- Modify: `codigo/renombrador.py`
- Test: `tests/test_renombrador.py`

**Interfaces:**
- Produces:
  - `planificar_carpeta(carpeta) -> list[dict]` — un dict por PDF (de `analizar_pdf` + `archivo`).
  - `aplicar(items: list[dict], carpeta) -> dict` — renombra en el sitio usando `item["sugerido"]` (o `item["nombre_final"]` si la GUI lo editó); devuelve `{"renombrados": N, "revisar": M, "errores": [...]}`. Anti-colisión con ` (2)`.
  - `_destino_unico(carpeta, nombre, ocupados: set) -> str`

- [ ] **Step 1: Escribir los tests fallidos (con archivos temporales)**

Agregar a `tests/test_renombrador.py`:
```python
def test_destino_unico_agrega_contador(tmp_path):
    (tmp_path / "DC FOTOCHECKS - ACME 23-06.pdf").write_text("x")
    ocupados = {"DC FOTOCHECKS - ACME 23-06.pdf"}
    nuevo = r._destino_unico(tmp_path, "DC FOTOCHECKS - ACME 23-06.pdf", ocupados)
    assert nuevo == "DC FOTOCHECKS - ACME 23-06 (2).pdf"

def test_aplicar_renombra_en_el_sitio(tmp_path):
    orig = tmp_path / "pdf 5.pdf"
    orig.write_text("contenido")
    items = [{"archivo": str(orig), "sugerido": "DC INSUMOS - ACME 23-06.pdf", "confianza": "alta"}]
    res = r.aplicar(items, tmp_path)
    assert res["renombrados"] == 1
    assert (tmp_path / "DC INSUMOS - ACME 23-06.pdf").exists()
    assert not orig.exists()
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/test_renombrador.py -k "destino_unico or aplicar" -v`
Expected: FAIL.

- [ ] **Step 3: Implementar**

Agregar a `renombrador.py`:
```python
def planificar_carpeta(carpeta) -> list[dict]:
    carpeta = Path(carpeta)
    items = []
    for pdf in sorted(carpeta.glob("*.pdf")):
        try:
            items.append(analizar_pdf(pdf))
        except Exception as e:  # PDF dañado no debe tumbar el lote
            items.append({"archivo": str(pdf), "cliente": "", "categoria": "OTROS",
                          "fecha": None, "confianza": "revisar", "error": str(e),
                          "sugerido": pdf.name})
    return items

def _destino_unico(carpeta, nombre: str, ocupados: set) -> str:
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
    carpeta = Path(carpeta)
    ocupados: set = set()
    renombrados, revisar, errores = 0, 0, []
    for it in items:
        nombre = it.get("nombre_final") or it.get("sugerido")
        origen = Path(it["archivo"])
        if not nombre or not origen.exists():
            errores.append(origen.name)
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
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/test_renombrador.py -v`
Expected: PASS (todos: ~25 tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/renombrador.py tests/test_renombrador.py
git commit -m "feat(renombrador): planificar carpeta y aplicar renombrado anti-colision"
```

---

### Task 8: Prueba de integración sobre PDFs reales (skippable)

Valida la cadena completa contra los PDFs reales locales, sin commitearlos.

**Files:**
- Test: `tests/test_renombrador.py`

- [ ] **Step 1: Agregar el test de integración**

Agregar a `tests/test_renombrador.py`:
```python
import pytest
from pathlib import Path

FIXT = Path(r"C:/Users/Diego/Desktop/cotizaciones para renombrar")

@pytest.mark.skipif(not FIXT.exists(), reason="PDFs reales no presentes (no se commitean)")
def test_integracion_5_reales():
    items = r.planificar_carpeta(FIXT)
    by_file = {Path(it["archivo"]).name: it for it in items}
    # 4/5 verificados en diseño:
    assert by_file["pdf 3.pdf"]["categoria"] == "KIT DE LIMPIEZA"
    assert by_file["pdf 4.pdf"]["categoria"] == "MANTENIMIENTO"
    assert by_file["pdf 5.pdf"]["categoria"] == "INSUMOS"
    assert by_file["pdf2.pdf"]["categoria"] == "FOTOCHECKS"
    assert by_file["pdf 1.pdf"]["categoria"] == "FOTOCHECKS"  # mayor monto
```

- [ ] **Step 2: Correr en la PC de Diego (con los PDFs)**

Run: `pytest tests/test_renombrador.py::test_integracion_5_reales -v`
Expected: PASS. Si alguno falla, el orden de `pypdfium2` difiere del de la prueba de diseño → ajustar anclas/segmentación (Tasks 3-5) y re-correr. **Este es el gate real de que la lógica funciona end-to-end con pypdfium2.**

- [ ] **Step 3: Commit**

```bash
git add tests/test_renombrador.py
git commit -m "test(renombrador): integracion skippable sobre PDFs reales"
```

---

### Task 9: Pestaña "Renombrar Cotizaciones" en la GUI

Convierte `app.py` (ventana única) en `ttk.Notebook` con 2 pestañas y agrega la tabla de revisión.

**Files:**
- Modify: `codigo/app.py`
- Test: manual (GUI).

**Interfaces:**
- Consumes: `renombrador.planificar_carpeta`, `renombrador.aplicar`, `renombrador.CATS`.

- [ ] **Step 1: Definir el vocabulario completo del desplegable en renombrador.py**

Agregar a `renombrador.py`:
```python
VOCABULARIO = [
    "FOTOCHECKS", "ACCESORIOS", "INSUMOS", "KIT DE LIMPIEZA", "MANTENIMIENTO",
    "IMPRESORAS", "OTROS", "PVC", "PVC ADHESIVO", "TARJETAS IMPRESAS",
    "GIFT CARD", "ZENIUS 2 CLASSIC", "PRIMACY 2 DUPLEX",
]
```

- [ ] **Step 2: Refactor a Notebook + pestaña Mockups intacta**

En `codigo/app.py`, dentro de `App.__init__`, reemplazar el armado directo de widgets por un `ttk.Notebook` con dos frames. Mover **todo** el contenido actual (label título, entrada cliente, botón logo, botón generar, estado) a un `frame_mockups`; los métodos existentes (`elegir_logo`, `generar`, `_trabajo`, `_listo`, `_error`) no cambian, solo se reparentean al `frame_mockups`. Ampliar `raiz.geometry("820x560")`.

```python
from tkinter import ttk
# ...
nb = ttk.Notebook(raiz)
nb.pack(fill="both", expand=True)
frame_mockups = tk.Frame(nb, bg=FONDO)
frame_renombrar = tk.Frame(nb, bg=FONDO)
nb.add(frame_mockups, text="Mockups")
nb.add(frame_renombrar, text="Renombrar Cotizaciones")
# (los widgets de Mockups que hoy van sobre `raiz` ahora van sobre `frame_mockups`)
self._construir_renombrar(frame_renombrar)
```

- [ ] **Step 3: Construir la pestaña de renombrado**

Agregar a la clase `App` en `app.py`:
```python
def _construir_renombrar(self, panel):
    import renombrador
    self._renom = renombrador
    self._items = []
    barra = tk.Frame(panel, bg=FONDO); barra.pack(fill="x", padx=16, pady=12)
    tk.Button(barra, text="Elegir carpeta…", command=self._renom_elegir).pack(side="left")
    self._renom_ruta = tk.Label(barra, text="(ninguna)", bg=FONDO, fg="#777")
    self._renom_ruta.pack(side="left", padx=10)

    cols = ("archivo", "categoria", "cliente", "fecha", "numero")
    self._tabla = ttk.Treeview(panel, columns=cols, show="headings", height=12)
    for c, txt, w in [("archivo","Archivo",240),("categoria","Categoría",150),
                       ("cliente","Cliente",230),("fecha","Fecha",60),("numero","N° (ref)",120)]:
        self._tabla.heading(c, text=txt); self._tabla.column(c, width=w)
    self._tabla.tag_configure("revisar", background="#FFF3CD")  # ambar
    self._tabla.tag_configure("alta", background="#E6F4EA")      # verde
    self._tabla.pack(fill="both", expand=True, padx=16)
    self._tabla.bind("<Double-1>", self._renom_editar_celda)

    pie = tk.Frame(panel, bg=FONDO); pie.pack(fill="x", padx=16, pady=12)
    self._renom_estado = tk.Label(pie, text="", bg=FONDO, fg="#555")
    self._renom_estado.pack(side="left")
    tk.Button(pie, text="Renombrar todo", command=self._renom_aplicar).pack(side="right")

def _renom_elegir(self):
    from tkinter import filedialog
    carpeta = filedialog.askdirectory(title="Carpeta con cotizaciones PDF")
    if not carpeta:
        return
    self._renom_carpeta = carpeta
    self._renom_ruta.config(text=carpeta)
    self._items = self._renom.planificar_carpeta(carpeta)
    self._tabla.delete(*self._tabla.get_children())
    for it in self._items:
        from pathlib import Path
        iid = self._tabla.insert("", "end", tags=(it["confianza"],), values=(
            Path(it["archivo"]).name, it["categoria"], it.get("cliente",""),
            it.get("fecha") or "", it.get("numero") or ""))
        it["_iid"] = iid
    self._renom_estado.config(text=f"{len(self._items)} cotizaciones leídas.")

def _renom_editar_celda(self, event):
    from tkinter import simpledialog, ttk as _ttk
    iid = self._tabla.focus()
    col = self._tabla.identify_column(event.x)
    if not iid:
        return
    idx = {"#1":"archivo","#2":"categoria","#3":"cliente","#4":"fecha","#5":"numero"}.get(col)
    it = next((x for x in self._items if x.get("_iid")==iid), None)
    if it is None or idx in (None,"archivo","numero"):
        return
    if idx == "categoria":
        # menu con vocabulario completo
        top = tk.Toplevel(self._tabla); top.title("Categoría")
        var = tk.StringVar(value=it["categoria"])
        combo = _ttk.Combobox(top, values=self._renom.VOCABULARIO, textvariable=var, state="readonly")
        combo.pack(padx=12, pady=12)
        def ok():
            it["categoria"] = var.get()
            self._tabla.set(iid, "categoria", var.get()); top.destroy()
        tk.Button(top, text="OK", command=ok).pack(pady=(0,12))
    else:
        actual = it.get(idx) or ""
        nuevo = simpledialog.askstring("Editar", idx, initialvalue=actual, parent=self._tabla)
        if nuevo is not None:
            it[idx] = nuevo
            self._tabla.set(iid, idx, nuevo)

def _renom_aplicar(self):
    from tkinter import messagebox
    for it in self._items:  # recomputar nombre con lo editado
        it["nombre_final"] = self._renom.nombre_destino(
            it["categoria"], it.get("cliente") or "SIN CLIENTE", it.get("fecha"))
    res = self._renom.aplicar(self._items, self._renom_carpeta)
    messagebox.showinfo("Listo",
        f"{res['renombrados']} renombrados · {res['revisar']} marcados para revisar."
        + (f"\nErrores: {len(res['errores'])}" if res['errores'] else ""))
    self._renom_elegir_recargar()

def _renom_elegir_recargar(self):
    if getattr(self, "_renom_carpeta", None):
        self._items = self._renom.planificar_carpeta(self._renom_carpeta)
        self._tabla.delete(*self._tabla.get_children())
        for it in self._items:
            from pathlib import Path
            iid = self._tabla.insert("", "end", tags=(it["confianza"],), values=(
                Path(it["archivo"]).name, it["categoria"], it.get("cliente",""),
                it.get("fecha") or "", it.get("numero") or ""))
            it["_iid"] = iid
```

- [ ] **Step 4: Probar la GUI manualmente**

Run: `python codigo/app.py` (o el launcher en dev).
Expected: abre con 2 pestañas. En "Renombrar Cotizaciones": elegir `Desktop\cotizaciones para renombrar`, ver 5 filas con categoría/cliente/fecha, verdes/ámbar correctos; doble clic en Categoría abre el desplegable con el vocabulario completo; "Renombrar todo" renombra y muestra el resumen. Verificar que la pestaña "Mockups" sigue funcionando igual.

- [ ] **Step 5: Commit**

```bash
git add codigo/app.py codigo/renombrador.py
git commit -m "feat(app): pestaña Renombrar Cotizaciones con tabla de revision"
```

---

### Task 10: Empaquetado — bundle pypdfium2, publicar.py, recompile

**Files:**
- Modify: `MockupsDISECOD.spec`, `publicar.py`
- Test: manual (build + smoke test del exe).

- [ ] **Step 1: Agregar renombrador.py al auto-update**

En `publicar.py`, agregar `"renombrador.py"` a la lista `ARCHIVOS`:
```python
ARCHIVOS = ["app.py", "motor.py", "plantillas.py", "render.py", "renombrador.py", "version.txt",
            "fuente-display.ttf", "fuente-display-italic.ttf", "foto-persona.jpg",
            "inter.ttf", "inter-semibold.ttf"]
```

- [ ] **Step 2: Bundle pypdfium2 en el .spec**

En `MockupsDISECOD.spec`, asegurar que PyInstaller incluya pypdfium2 (binario pdfium). En la sección de imports/analysis:
```python
from PyInstaller.utils.hooks import collect_all
pdfium_datas, pdfium_binaries, pdfium_hidden = collect_all("pypdfium2_raw")
# y sumar a Analysis: datas += pdfium_datas ; binaries += pdfium_binaries ;
# hiddenimports += pdfium_hidden + ["pypdfium2"]
```
(Si el editor de fotos ya resolvió pypdfium2 en su `.spec`, copiar ese patrón verbatim — ver `fotochecks-editor/FotochecksEditor.spec`.)

- [ ] **Step 3: Recompilar el exe (con el exe cerrado)**

Run: `pyinstaller MockupsDISECOD.spec` (o el comando que use el proyecto).
Expected: build sin error; genera `dist\MockupsDISECOD...`.

- [ ] **Step 4: Smoke test del exe**

Abrir el exe recién compilado en una PC limpia (o carpeta de prueba). Verificar: abre, pestaña Mockups genera una lámina OK, pestaña Renombrar lee una carpeta de PDFs y renombra. Esto confirma que pdfium viaja dentro del exe (el punto de riesgo del empaquetado).

- [ ] **Step 5: Commit**

```bash
git add MockupsDISECOD.spec publicar.py
git commit -m "build: bundle pypdfium2 en el exe + renombrador.py al auto-update"
```

---

## Cierre

Tras la Task 10, **no publicar ni instalar todavía**: dejar que Diego pruebe el exe con la carpeta `Desktop\cotizaciones para renombrar` y apruebe. Recién ahí: `publicar.py` (sube versión + manifest + push) e instalar el exe al vendedor (trae Mockups + Renombrar en una sola entrega). Actualizar `claude-cerebro\mockups-credenciales.md` con el estado.

---

## Self-Review

**Cobertura del spec:**
- §2 decisiones → Tasks 5 (mayor monto), 6 (nombre/fecha), 7 (en el sitio + colisión), 9 (vocabulario desplegable). ✓
- §3 dos plantillas → Tasks 2-5 (detección + anclas por plantilla). ✓
- §4 extracción (texto, plantilla, número, fecha, cliente, clasificación, confianza) → Tasks 1-6. ✓
- §5 nombre + colisiones → Tasks 6-7. ✓
- §6 GUI pestaña/tabla/semáforo/desplegable → Task 9. ✓
- §7 empaquetado (pypdfium2, publicar.py, .spec, requirements) → Tasks 1, 10. ✓
- §8 casos borde (DJ, DNI, contacto, guion, combo impresora, gift card) → tests en Tasks 2,4,5,6 + integración Task 8. ✓
- §10 pruebas (fixtures locales no commiteadas) → Task 8. ✓
- §4.1 riesgo de orden pypdfium2 → Tasks 1 (gate inicial) y 8 (gate end-to-end). ✓

**Sin placeholders:** todo paso tiene código/comando real. ✓
**Consistencia de tipos:** `analizar_pdf`/`analizar_texto` devuelven el dict con claves usadas por `aplicar` (`archivo`, `sugerido`, `nombre_final`, `confianza`) y por la GUI (`categoria`, `cliente`, `fecha`, `numero`, `confianza`). `clasificar` devuelve `(str, dict)` consumido por `analizar_texto`. ✓
