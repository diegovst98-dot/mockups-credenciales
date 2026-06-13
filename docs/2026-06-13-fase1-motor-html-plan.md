# Fase 1 — Motor HTML/CSS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar la capa de dibujo Pillow por caras de credencial maquetadas en HTML/CSS y renderizadas con Playwright, con 3 direcciones de arte (Aurora/Editorial/Glass), conservando la orquestación, la composición del brief y el auto-update que ya funcionan.

**Architecture:** Las CARAS (frontal/reverso de cada dirección) se generan como HTML/CSS autocontenido (logo y foto embebidos en base64, fuentes horneadas vía @font-face) y se rasterizan con Playwright (Chromium headless, device_scale_factor=2) a `PIL.Image`. La COMPOSICIÓN (PNG por dirección + brief con cabecera DISECOD + carpeta `para-diseno/`) reutiliza las funciones Pillow existentes (`png_estilo`, `lamina`, `con_sombra`), ahora alimentadas con caras HTML en vez de caras Pillow. `cargar_logo`, `paleta_del_logo`, `slug`, `web_cliente` y `generar()` (misma firma) se conservan.

**Tech Stack:** Python 3.12, Playwright (Chromium), Pillow (solo composición), HTML/CSS, tkinter (GUI sin cambios), PyInstaller (empaquetado).

---

## File Structure

- `codigo/render.py` — **Crear.** `render_caras(items, escala=2) -> list[PIL.Image]`: rasteriza una lista de HTMLs reusando un solo navegador. Único punto que toca Playwright.
- `codigo/plantillas.py` — **Crear.** Construye el HTML/CSS de cada cara: `cara(estilo, lado, ctx) -> (html, ancho, alto)`. Incluye utilidades de data-URI y `@font-face` horneadas. CSS base de las 3 direcciones tomado del prototipo validado `salida/_proto/proto_html.py` (`.s1/.s2/.s3`), parametrizado.
- `codigo/motor.py` — **Modificar.** Reemplazar el bloque de generación (funciones `estiloN_frontal/reverso` + `ESTILOS` Pillow) por: armar contexto → `plantillas.cara` → `render.render_caras` → composición existente. Conservar utilidades de color/logo, `web_cliente`, `slug`, `png_estilo`, `lamina`, `con_sombra`, `generar()`.
- `codigo/fuentes/` — **Crear.** Horneadas: `playfair.ttf` (ya existe como `codigo/fuente-display.ttf`, copiar) + `inter.ttf` (descargar OFL). Para `@font-face` por base64.
- `tests/test_motor_html.py` — **Crear.** Tests funcionales (estructura de salida, color de marca, no-desborde, robustez por tipo de logo).
- `codigo/app.py` — **Modificar.** Texto de estado "9 estilos" → "3 propuestas".
- `publicar.py` — **Modificar.** Agregar `plantillas.py`, `render.py`, fuentes y fondos a `ARCHIVOS` (auto-update).

> **Decisión de tamaño/empaquetado del Chromium (~170 MB):** fuera del alcance de las
> tareas de código; se resuelve en la tarea final de empaquetado (Tarea 9).

---

## Task 1: Dependencias y fuentes horneadas

**Files:**
- Create: `codigo/fuentes/playfair.ttf` (copia de `codigo/fuente-display.ttf`)
- Create: `codigo/fuentes/inter.ttf` (Inter Regular/SemiBold OFL)
- Modify: `requirements.txt` (o crear si no existe)
- Test: `tests/test_motor_html.py`

- [ ] **Step 1: Escribir test de prerequisitos**

```python
# tests/test_motor_html.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))
CODIGO = os.path.join(os.path.dirname(__file__), "..", "codigo")

def test_playwright_disponible():
    import playwright  # noqa

def test_fuentes_horneadas_existen():
    assert os.path.exists(os.path.join(CODIGO, "fuentes", "playfair.ttf"))
    assert os.path.exists(os.path.join(CODIGO, "fuentes", "inter.ttf"))
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_motor_html.py -v`
Expected: FAIL (faltan las fuentes en `codigo/fuentes/`).

- [ ] **Step 3: Crear fuentes y requirements**

```bash
mkdir -p codigo/fuentes
cp codigo/fuente-display.ttf codigo/fuentes/playfair.ttf
# Inter OFL (ejemplo de fuente confiable; ajustar URL a un mirror OFL vigente):
curl -L -o codigo/fuentes/inter.ttf "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.ttf"
```

Agregar a `requirements.txt`:
```
pillow
playwright
```

- [ ] **Step 4: Instalar Chromium de Playwright (si no está) y correr test**

Run: `python -m playwright install chromium && python -m pytest tests/test_motor_html.py -v`
Expected: PASS (ambos tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/fuentes/playfair.ttf codigo/fuentes/inter.ttf requirements.txt tests/test_motor_html.py
git commit -m "fase1: fuentes horneadas + deps (playwright) + test de prerequisitos"
```

---

## Task 2: render.py — rasterizar HTML a PIL.Image

**Files:**
- Create: `codigo/render.py`
- Test: `tests/test_motor_html.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_render_caras_produce_imagen_del_tamano():
    sys.path.insert(0, CODIGO)
    from render import render_caras
    html = ('<!doctype html><body style="margin:0">'
            '<div class="card" style="width:200px;height:120px;background:#0a7"></div></body>')
    imgs = render_caras([(html, 200, 120)], escala=2)
    assert len(imgs) == 1
    w, h = imgs[0].size
    assert (w, h) == (400, 240)  # device_scale_factor=2
    # no es una imagen vacía/transparente
    assert imgs[0].convert("RGB").getextrema()[0] != (0, 0)
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_motor_html.py::test_render_caras_produce_imagen_del_tamano -v`
Expected: FAIL ("No module named 'render'").

- [ ] **Step 3: Implementar render.py**

```python
# -*- coding: utf-8 -*-
"""Rasteriza caras HTML a PIL.Image con Playwright (Chromium headless).
Reusa un solo navegador para todas las caras de una corrida (rapido)."""
import io
from PIL import Image
from playwright.sync_api import sync_playwright


def render_caras(items, escala=2):
    """items: list[(html, ancho, alto)]. Devuelve list[PIL.Image] (RGBA).
    Toma screenshot del elemento .card (sin sombras ni rotulos: full-bleed)."""
    imgs = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--force-color-profile=srgb"])
        for html, ancho, alto in items:
            pg = b.new_page(device_scale_factor=escala,
                            viewport={"width": ancho, "height": alto})
            pg.set_content(html, wait_until="load")
            try:
                pg.evaluate("document.fonts.ready")
            except Exception:
                pass
            pg.wait_for_timeout(120)
            el = pg.query_selector(".card") or pg
            data = el.screenshot()
            pg.close()
            imgs.append(Image.open(io.BytesIO(data)).convert("RGBA"))
        b.close()
    return imgs
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_motor_html.py::test_render_caras_produce_imagen_del_tamano -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add codigo/render.py tests/test_motor_html.py
git commit -m "fase1: render.py - HTML a PIL.Image via Playwright"
```

---

## Task 3: plantillas.py — utilidades (data-URI, fuentes, contexto)

**Files:**
- Create: `codigo/plantillas.py`
- Test: `tests/test_motor_html.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_contexto_y_css_base():
    sys.path.insert(0, CODIGO)
    from plantillas import construir_contexto, css_base
    from motor import cargar_logo
    logo = cargar_logo(os.path.join(CODIGO, "..", "recursos", "logo-disecod-oscuro.png"))
    ctx = construir_contexto(logo, (0, 164, 80), (0, 90, 44), "Interbank")
    assert ctx["logo_uri"].startswith("data:image/png;base64,")
    assert ctx["foto_uri"].startswith("data:image")
    assert ctx["prim_css"] == "rgb(0,164,80)"
    assert "@font-face" in css_base()
    assert "Playfair" in css_base()
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_motor_html.py::test_contexto_y_css_base -v`
Expected: FAIL ("No module named 'plantillas'").

- [ ] **Step 3: Implementar utilidades en plantillas.py**

```python
# -*- coding: utf-8 -*-
"""Construye el HTML/CSS de cada cara de credencial. Autocontenido:
logo/foto en base64, fuentes horneadas via @font-face. El CSS de las 3
direcciones (Aurora/Editorial/Glass) se basa en el prototipo validado
salida/_proto/proto_html.py (.s1/.s2/.s3)."""
import base64
import io
import os

RUTA = os.path.dirname(os.path.abspath(__file__))
FOTO_PERSONA = os.path.join(RUTA, "foto-persona.jpg")
F_PLAYFAIR = os.path.join(RUTA, "fuentes", "playfair.ttf")
F_INTER = os.path.join(RUTA, "fuentes", "inter.ttf")

DATOS = {"nombre": "Carlos González M.", "cargo": "Supervisor de Operaciones",
         "id": "45678123"}


def _b64_img(img, fmt="PNG"):
    buf = io.BytesIO(); img.save(buf, fmt)
    return "data:image/%s;base64,%s" % (fmt.lower(), base64.b64encode(buf.getvalue()).decode())


def _b64_file(path, mime):
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


def _rgb(c):
    return "rgb(%d,%d,%d)" % tuple(c[:3])


def _ajustar(c, f):
    if f <= 1:
        return tuple(int(x * f) for x in c[:3])
    return tuple(int(x + (255 - x) * (f - 1)) for x in c[:3])


def construir_contexto(logo, prim, sec, cliente):
    from motor import web_cliente
    return {
        "logo_uri": _b64_img(logo),
        "foto_uri": _b64_file(FOTO_PERSONA, "image/jpeg"),
        "prim_css": _rgb(prim),
        "medio_css": _rgb(_ajustar(prim, 0.55)),
        "oscuro_css": _rgb(_ajustar(prim, 0.20)),
        "cliente": cliente,
        "web": web_cliente(cliente),
        "datos": DATOS,
    }


def css_base():
    pf = _b64_file(F_PLAYFAIR, "font/ttf")
    inter = _b64_file(F_INTER, "font/ttf")
    return ("@font-face{font-family:'Playfair';src:url(%s) format('truetype');}"
            "@font-face{font-family:'Inter';src:url(%s) format('truetype');}"
            "*{margin:0;padding:0;box-sizing:border-box}"
            "body{margin:0;font-family:'Inter',sans-serif}"
            % (pf, inter))
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_motor_html.py::test_contexto_y_css_base -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add codigo/plantillas.py tests/test_motor_html.py
git commit -m "fase1: plantillas.py - utilidades de contexto, data-URI y fuentes horneadas"
```

---

## Task 4: plantillas.py — las 3 direcciones (frontal + reverso)

**Files:**
- Modify: `codigo/plantillas.py`
- Reference: `salida/_proto/proto_html.py` (CSS `.s1` Aurora, `.s2` Editorial, `.s3` Glass — ya validado visualmente)
- Test: `tests/test_motor_html.py`

> **Nota de diseño:** Aurora y Editorial son horizontales (1011×638); Glass es vertical
> (638×1011). Tomar el CSS de los frontales del prototipo. **Corregir** en Editorial el
> solapamiento nombre/cargo (separar `top` del cargo bajo el nombre). Los reversos son
> nuevos: cada uno repite el gesto del frontal + QR (placa blanca) + "personal e
> intransferible" + `web`. El logo en fondo oscuro usa `filter:brightness(0) invert(1)`
> solo si el logo es oscuro; preferir la silueta cuando aplique (cubierto por la capa
> de composición que ya maneja logos claros/oscuros vía `pegar_logo`; en HTML, usar
> `filter` segun `luminancia(prim)`).

- [ ] **Step 1: Escribir el test que falla**

```python
def test_cara_devuelve_html_dimensionado():
    sys.path.insert(0, CODIGO)
    from plantillas import cara, construir_contexto
    from motor import cargar_logo
    logo = cargar_logo(os.path.join(CODIGO, "..", "recursos", "logo-disecod-oscuro.png"))
    ctx = construir_contexto(logo, (0, 164, 80), (0, 90, 44), "Interbank")
    for estilo in ("aurora", "editorial", "glass"):
        for lado in ("frontal", "reverso"):
            html, w, h = cara(estilo, lado, ctx)
            assert "<div class=\"card\"" in html
            assert ctx["prim_css"] in html       # usa el color de marca
            assert (w, h) in [(1011, 638), (638, 1011)]
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_motor_html.py::test_cara_devuelve_html_dimensionado -v`
Expected: FAIL ("cannot import name 'cara'").

- [ ] **Step 3: Implementar `cara()` y las 3 plantillas**

Agregar a `codigo/plantillas.py`:

```python
H, V = (1011, 638), (638, 1011)
ORO = "#c9a14a"


def _shell(css_estilo, cuerpo, ancho, alto, prim, oscuro):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>%s"
            ".card{width:%dpx;height:%dpx;position:relative;overflow:hidden}"
            ".lab{font-size:18px;letter-spacing:3px;text-transform:uppercase;font-weight:600}"
            ".val{font-size:30px;font-weight:600;margin-top:2px}"
            "%s</style></head><body>"
            "<div class='card'>%s</div></body></html>"
            % (css_base(), ancho, alto, css_estilo, cuerpo))


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto) para la cara pedida.
    estilo in {aurora, editorial, glass}; lado in {frontal, reverso}."""
    d = ctx["datos"]
    fn = {"aurora": _aurora, "editorial": _editorial, "glass": _glass}[estilo]
    return fn(lado, ctx, d)
```

Luego implementar `_aurora`, `_editorial`, `_glass`. Para los **frontales**, portar
el CSS de `.s1/.s2/.s3` del prototipo `salida/_proto/proto_html.py` (variables
`--prim/--medio/--oscuro` → `ctx["prim_css"]` etc.), corrigiendo el solapamiento de
Editorial (`.cargo{top:300px}` separado de `.nombre`). Para los **reversos**, usar este
patrón (ejemplo Aurora; replicar el fondo de cada estilo y cambiar el cuerpo):

```python
def _qr_svg(prim):
    # QR decorativo simple sobre placa blanca (no escaneable)
    return ("<div style=\"position:absolute;left:50%;top:46%;transform:translate(-50%,-50%);"
            "width:190px;height:190px;background:#fff;border-radius:16px;\"></div>")


def _reverso_comun(fondo_css, ctx, claro_txt):
    col = "#fff" if not claro_txt else "#1d1f24"
    return _shell(
        fondo_css,
        ("<img src='%s' style='position:absolute;top:48px;left:50%%;transform:translateX(-50%%);"
         "height:60px;%s'>"
         "%s"
         "<div style='position:absolute;left:0;right:0;bottom:70px;text-align:center;color:%s'>"
         "<div style='font-size:24px;font-weight:600'>Personal e intransferible</div>"
         "<div style='font-size:22px;opacity:.8;margin-top:8px'>%s</div></div>"
         % (ctx["logo_uri"],
            "filter:brightness(0) invert(1)" if col == "#fff" else "",
            _qr_svg(ctx["prim_css"]), col, ctx["web"])),
        *H, ctx["prim_css"], ctx["oscuro_css"])
```

> El ejecutor implementa los 3 frontales (CSS del prototipo, parametrizado) y los 3
> reversos (un fondo por estilo + `_reverso_comun` o equivalente). Cada función devuelve
> `(_shell(...), ancho, alto)` con `H` para aurora/editorial y `V` para glass.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_motor_html.py::test_cara_devuelve_html_dimensionado -v`
Expected: PASS.

- [ ] **Step 5: Render visual de control (checkpoint humano)**

```python
# script de control: codigo/../salida/_proto/control_fase1.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "codigo"))
from motor import cargar_logo, paleta_del_logo
from plantillas import cara, construir_contexto
from render import render_caras
logo = cargar_logo(r"C:\Users\Diego\Downloads\Interbank_logo.svg.png")
prim, sec = paleta_del_logo(logo)
ctx = construir_contexto(logo, prim, sec, "Interbank")
items = [cara(e, l, ctx) for e in ("aurora","editorial","glass") for l in ("frontal","reverso")]
for (html, w, h), nombre in zip(items, ["a-f","a-r","e-f","e-r","g-f","g-r"]):
    render_caras([(html,w,h)])[0].save(rf"C:\Users\Diego\mockups-credenciales\salida\_proto\fase1-{nombre}.png")
```
Run: `python salida/_proto/control_fase1.py` y revisar los 6 PNG con Diego.
Expected: las 6 caras se ven bien; Editorial sin solapamiento.

- [ ] **Step 6: Commit**

```bash
git add codigo/plantillas.py tests/test_motor_html.py
git commit -m "fase1: 3 direcciones (Aurora/Editorial/Glass) frontal+reverso en HTML/CSS"
```

---

## Task 5: Integrar en motor.generar() conservando composición y para-diseno

**Files:**
- Modify: `codigo/motor.py` (reemplazar bloque de generación; conservar `png_estilo`, `lamina`, `con_sombra`, `cargar_logo`, `paleta_del_logo`, `slug`, `web_cliente`, `oro_del_logo`, firma de `generar`)
- Test: `tests/test_motor_html.py`

- [ ] **Step 1: Escribir el test que falla**

```python
import tempfile, glob

def test_generar_produce_brief_y_3_direcciones():
    sys.path.insert(0, CODIGO)
    from motor import generar
    logo = os.path.join(CODIGO, "..", "recursos", "logo-disecod-oscuro.png")
    out = tempfile.mkdtemp(prefix="t_gen_")
    carpeta, rutas = generar(logo, "Interbank", out)
    base = [os.path.basename(r) for r in rutas]
    assert any("brief" in b or "lamina" in b for b in base)         # brief de presentacion
    assert sum(b.startswith("direccion-") or b.startswith("estilo-") for b in base) == 3
    diseno = glob.glob(os.path.join(carpeta, "para-diseno", "*.png"))
    assert len(diseno) == 6   # 3 direcciones x 2 caras, full-bleed
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_motor_html.py::test_generar_produce_brief_y_3_direcciones -v`
Expected: FAIL (generar aún usa el pipeline Pillow / nombres viejos).

- [ ] **Step 3: Reemplazar el pipeline de generación en `generar()`**

En `codigo/motor.py`, dentro de `generar()`, reemplazar el armado de `piezas` (que hoy
llama a `ESTILOS` Pillow) por:

```python
    from plantillas import cara, construir_contexto
    from render import render_caras
    ctx = construir_contexto(logo, prim, sec, cliente)
    DIRECCIONES = [("aurora", "Dirección 1 — Aurora"),
                   ("editorial", "Dirección 2 — Editorial"),
                   ("glass", "Dirección 3 — Glass")]
    items, meta = [], []
    for clave, titulo in DIRECCIONES:
        for lado in ("frontal", "reverso"):
            html, w, h = cara(clave, lado, ctx)
            items.append((html, w, h)); meta.append((titulo, lado))
    caras = render_caras(items)  # 6 PIL.Image, full-bleed CR80
    piezas = []
    for i, (clave, titulo) in enumerate(DIRECCIONES):
        fr, rv = caras[i * 2], caras[i * 2 + 1]
        piezas.append((titulo, fr, rv))
```

Mantener intacto el resto de `generar()` (la parte que escribe `para-diseno/`, llama a
`png_estilo` y `lamina`). Renombrar la salida `estilo-` → `direccion-` y
`lamina-presentacion.png` → `brief-presentacion.png` (insertar al frente de `rutas`).

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_motor_html.py::test_generar_produce_brief_y_3_direcciones -v`
Expected: PASS.

- [ ] **Step 5: Render real + checkpoint humano**

Run: `python codigo/motor.py "C:\Users\Diego\Downloads\Interbank_logo.svg.png" "Interbank"`
Abrir `salida/Interbank-<fecha>/brief-presentacion.png` y revisar con Diego.
Expected: brief con cabecera DISECOD + 3 direcciones HTML; calidad muy superior a v7.

- [ ] **Step 6: Commit**

```bash
git add codigo/motor.py tests/test_motor_html.py
git commit -m "fase1: generar() usa caras HTML, conserva composicion (brief + para-diseno)"
```

---

## Task 6: Robustez (razón social larga, logo pálido / oscuro / monocromo)

**Files:**
- Modify: `codigo/plantillas.py` (clamp de texto si hace falta)
- Test: `tests/test_motor_html.py`

- [ ] **Step 1: Escribir el test que falla**

```python
import tempfile

def test_robustez_logos_y_nombre_largo():
    sys.path.insert(0, CODIGO)
    from motor import generar
    casos = [
        (os.path.join(CODIGO, "..", "recursos", "logo-disecod-oscuro.png"),
         "Corporación Andina de Seguridad Integral del Perú"),
    ]
    for logo, cliente in casos:
        out = tempfile.mkdtemp(prefix="t_rob_")
        carpeta, rutas = generar(logo, cliente, out)
        assert len(rutas) >= 4  # brief + 3 direcciones, sin excepción
```

- [ ] **Step 2: Correr y verificar que falla (o pasa si ya es robusto)**

Run: `python -m pytest tests/test_motor_html.py::test_robustez_logos_y_nombre_largo -v`
Expected: si desborda visualmente o lanza, FAIL; si no, PASS (igual seguir al Step 3 para el clamp CSS).

- [ ] **Step 3: Asegurar no-desborde en CSS**

En las plantillas, a los contenedores de `cliente`/nombre largo agregarles:
```css
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:CALC_DEL_CONTENEDOR;
```
o reducir `font-size` con `clamp()`. (CSS hace esto nativo; no requiere medir como en Pillow.)

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_motor_html.py::test_robustez_logos_y_nombre_largo -v`
Expected: PASS.

- [ ] **Step 5: Render de estrés + checkpoint**

Generar con: Interbank (color), `LOGO GV (1).png` (navy), un logo pálido y uno monocromo.
Revisar las 4 láminas con Diego.

- [ ] **Step 6: Commit**

```bash
git add codigo/plantillas.py tests/test_motor_html.py
git commit -m "fase1: robustez de nombres largos y logos extremos (clamp CSS)"
```

---

## Task 7: Limpieza del motor (quitar Pillow muerto) y textos de GUI

**Files:**
- Modify: `codigo/motor.py` (eliminar `estilo1..10_*`, `_cabecera_arco`, `ESTILOS`, helpers de dibujo solo usados por esas funciones; conservar utilidades de color/logo, `con_sombra`, `png_estilo`, `lamina`, `mascara_redondeada` si la usa la composición)
- Modify: `codigo/app.py` ("9 estilos" → "3 propuestas")
- Test: `tests/test_motor_html.py` (la suite completa sigue verde)

- [ ] **Step 1: Identificar funciones muertas**

Run: `python -c "import ast,sys; src=open('codigo/motor.py',encoding='utf-8').read(); print([n.name for n in ast.walk(ast.parse(src)) if isinstance(n,ast.FunctionDef)])"`
Marcar las `estiloN_*`, `_cabecera_arco`, y helpers de dibujo (`capa_onda`, `icono`, `foto_hexagonal`, `contorno_hexagonal`, etc.) que ya nadie llama.

- [ ] **Step 2: Eliminar lo muerto y correr toda la suite**

Borrar esas funciones. Run: `python -m pytest tests/test_motor_html.py -v`
Expected: PASS (toda la suite). Si algo se rompe, esa función no era muerta → restaurar.

- [ ] **Step 3: Actualizar GUI**

En `codigo/app.py`: `text="Creando las 3 propuestas, dame unos segundos…"`.

- [ ] **Step 4: Correr suite + smoke de la GUI por import**

Run: `python -c "import sys; sys.path.insert(0,'codigo'); import app; print('app OK')"`
Expected: "app OK" sin excepción.

- [ ] **Step 5: Commit**

```bash
git add codigo/motor.py codigo/app.py tests/test_motor_html.py
git commit -m "fase1: limpieza de dibujo Pillow muerto + textos GUI a 3 propuestas"
```

---

## Task 8: Documentación (LEEME/GUIA) a 3 propuestas

**Files:**
- Modify: `LEEME.txt`, `GUIA.md`

- [ ] **Step 1: Actualizar textos**

Reemplazar "9 propuestas"/"estilo-1 al estilo-9" por "3 propuestas"/"direccion-1 a direccion-3" y `lamina-presentacion.png` → `brief-presentacion.png` en ambos archivos.

- [ ] **Step 2: Commit**

```bash
git add LEEME.txt GUIA.md
git commit -m "fase1: LEEME/GUIA a 3 propuestas y brief-presentacion"
```

---

## Task 9: Empaquetado y auto-update (decisión del Chromium)

**Files:**
- Modify: `publicar.py` (`ARCHIVOS` += `plantillas.py`, `render.py`, `fuentes/playfair.ttf`, `fuentes/inter.ttf`)
- Modify: `MockupsDISECOD.spec` / `launcher.py` si se hornea Chromium
- Decisión: hornear Chromium en el exe (instalador más pesado, ~+170 MB) **vs** que `instalar.bat` corra `playwright install chromium` una vez.

> **Recomendación:** que `instalar.bat` ejecute `playwright install chromium` la primera
> vez (mantiene el exe liviano y el auto-update intacto; el navegador se baja una sola
> vez en la PC del vendedor). Confirmar con Diego antes de ejecutar esta tarea.

- [ ] **Step 1: Agregar archivos nuevos al manifest de auto-update**

En `publicar.py`, `ARCHIVOS`:
```python
ARCHIVOS = ["app.py", "motor.py", "plantillas.py", "render.py", "version.txt",
            "fuentes/playfair.ttf", "fuentes/inter.ttf",
            "fuente-display.ttf", "fuente-display-italic.ttf", "foto-persona.jpg"]
```
> **Nota:** verificar que `launcher.py` cree subcarpetas al descargar (`fuentes/`).
> Si no, ajustar `buscar_actualizacion()` para `(CODIGO/nombre).parent.mkdir(...)`.

- [ ] **Step 2: Ajustar launcher para rutas con subcarpeta**

En `launcher.py`, antes de `write_bytes`/`copy`, asegurar:
```python
destino = (tmp / nombre); destino.parent.mkdir(parents=True, exist_ok=True)
```
(y lo mismo para `CODIGO / nombre`).

- [ ] **Step 3: Probar auto-update en sandbox (como se hizo con v7)**

Copiar `dist/codigo` a sandbox, bajar `version.txt`, correr `buscar_actualizacion()`
apuntado al sandbox; verificar retorno True, sin archivos faltantes, `plantillas.py` y
`fuentes/` presentes.
Expected: actualización íntegra.

- [ ] **Step 4: Decisión de empaquetado con Diego**

Checkpoint: confirmar hornear vs instalar Chromium. Implementar la opción elegida.

- [ ] **Step 5: Commit (sin publicar)**

```bash
git add publicar.py launcher.py MockupsDISECOD.spec
git commit -m "fase1: empaquetado - archivos nuevos al auto-update + manejo de Chromium"
```

> **NO** correr `publicar.py` hasta OK explícito de Diego (regla del proyecto).

---

## Self-Review (cobertura del spec)

- HTML/CSS reemplaza Pillow → Tareas 2–5. ✓
- 3 direcciones Aurora/Editorial/Glass, frontal+reverso → Tarea 4. ✓
- Brief con cabecera DISECOD + para-diseno → Tarea 5 (reusa `lamina`/`png_estilo`). ✓
- Color/variación según el logo → `construir_contexto` (Tarea 3), validado en 4/5/6. ✓
- Robustez (pálido/oscuro/monocromo/nombre largo) → Tarea 6. ✓
- Auto-update + empaquetado, Chromium → Tarea 9. ✓
- Foto 1x1 → **fuera de Fase 1** (módulo separado, plan aparte de Fase 2). Documentado en el design doc.
- Banco de fondos IA → **Fase 2** (plan aparte). ✓ (no en este plan, por diseño).

Sin placeholders de implementación: cada paso de código trae código real o referencia a
un archivo fuente concreto y existente (`salida/_proto/proto_html.py`). Las firmas
(`render_caras`, `cara`, `construir_contexto`, `css_base`, `generar`) son consistentes
entre tareas.
