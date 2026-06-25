# Editor visual de "Personalizar" — Plan de implementación (Fase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Probar el corazón del editor visual — un compositor de capas (Pillow) que arma la credencial desde capas movibles, un lienzo tkinter donde se arrastra/estira logo, foto y textos con guías/snap, y export a full-res — usando el mismo compositor para preview y export (WYSIWYG).

**Architecture:** Hoy `motor.render_modelo` hornea todo en HTML y lo rasteriza con Edge. La Fase 1 introduce una capa nueva: el **fondo decorativo** del modelo se rasteriza una vez (Edge, reutilizando las plantillas) y el **logo, la foto y los bloques de texto** se vuelven **capas** con posición/tamaño normalizados (0–1) que un **compositor Pillow** (`lienzo.py`) pega encima. El mismo compositor alimenta el preview en vivo y el export, garantizando que lo que se ve es lo que se manda. El estado de las capas vive en `estado.py` (dict puro, testeable).

**Tech Stack:** Python 3.12, Pillow (PIL), tkinter/ttk, pytest. Sin dependencias nuevas (clave: el .exe del vendedor sigue liviano).

## Global Constraints

- **Sin dependencias nuevas pesadas** — solo Pillow + tkinter (ya en el bundle). NADA de rembg/modelos. Si NO cambian librerías, el .exe NO se recompila.
- 🔒 **El logo del cliente NUNCA se recolorea** — solo mover/escalar/posicionar; tinta real. Prohibido invert/duotono/teñido.
- 🔒 **WYSIWYG** — el preview y el export usan el MISMO compositor con los MISMOS ajustes; nunca dos caminos distintos.
- **Tarjeta CR80** — horizontal `(CARD_W, CARD_H) = (1011, 638)`, vertical `(V_W, V_H) = (638, 1011)` (constantes ya en `motor.py` / `base.py`).
- **Coordenadas normalizadas 0–1** — toda posición/tamaño de capa se guarda como fracción de la tarjeta, para que el mismo ajuste rinda idéntico a cualquier resolución (preview chico = export grande).
- **Render-and-look obligatorio** — cada tarea visual termina con un PNG que se ABRE y se MIRA (tests verdes ≠ experiencia; lección recurrente del proyecto).
- **Entorno de pruebas (Windows)** — correr pytest PELADO, sin pipe: `python -m pytest tests/x.py -q --no-header` (un `| tail` se auto-manda a background y no escribe salida). El cwd del bash en background = `C:\Users\Diego`; usar rutas absolutas o `git -C C:\Users\Diego\mockups-credenciales`.
- **tkinter en tests** — UN solo `tk.Tk()` por proceso; usar `Toplevel` por caso. Con `p_logo=None` el re-render hace early-return (cableado headless testeable).
- **Compat exe viejo** — imports nuevos en `codigo/` que el exe viejo no traiga (ej. `ImageTk`) van DIFERIDOS (try/except con aviso). Cada import nuevo → revisar si hay que forzarlo en `launcher.py`.

---

## File Structure

- **Create** `codigo/lienzo.py` — compositor de capas (puro Pillow) + matemática de cajas y snap. Responsabilidad única: dado un fondo + capas + recursos → imagen final a cualquier resolución. Sin tkinter, sin red.
- **Modify** `codigo/estado.py` — ampliar el dict `Ajustes` con `capas` (posición/tamaño normalizados por capa) + helpers puros (`capas_inicial`, `mover_capa`, `serializar`/`deserializar`).
- **Modify** `codigo/motor.py` — `fondo_de_modelo(...)` (rasteriza el fondo decorativo del modelo, sin elementos editables) y reconectar `render_modelo` / `exportar_personalizado` para componer vía `lienzo.componer`.
- **Modify** `codigo/app.py` — reemplazar el `tk.Label` de preview por un `tk.Canvas` interactivo (arrastrar/estirar capas + guías/snap) en la pestaña Personalizar; preview y export vía el compositor.
- **Create** `tests/test_estado_capas.py` — modelo de datos de capas + serialización (puro).
- **Create** `tests/test_lienzo.py` — matemática de cajas, snap, y composición determinista (puro Pillow, sin Edge).
- **Create** `tests/_ver_compositor.py` — arnés de "render-and-look": arma un caso y guarda un PNG para mirar.

### Capas (IDs fijos de la Fase 1)
`"logo"`, `"foto"`, `"nombre"`, `"cargo"`, `"datos"` (el bloque etiqueta:valor como una unidad). Por capa: `{x, y, w, h}` normalizados 0–1 = caja contenedora (esquina sup-izq + ancho + alto, fracción de la tarjeta).

---

## Task 1: Modelo de datos de capas en estado.py

**Files:**
- Modify: `codigo/estado.py`
- Test: `tests/test_estado_capas.py`

**Interfaces:**
- Produces:
  - `CAPAS_IDS = ("logo", "foto", "nombre", "cargo", "datos")`
  - `capas_inicial(orientacion="H") -> dict` — `{id: {"x":float,"y":float,"w":float,"h":float}}` con posiciones por defecto sensatas.
  - `mover_capa(ajustes, capa_id, x=None, y=None, w=None, h=None) -> dict` — copia con la caja de esa capa actualizada (clamp a 0–1), deja las demás intactas.
  - `ajustes_inicial(modelo_clave)` ahora incluye `"capas": capas_inicial(...)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_estado_capas.py
import estado

def test_ajustes_inicial_trae_capas():
    a = estado.ajustes_inicial("clasica")
    assert set(a["capas"]) == set(estado.CAPAS_IDS)
    for caja in a["capas"].values():
        assert {"x", "y", "w", "h"} <= set(caja)

def test_mover_capa_no_toca_las_otras():
    a = estado.ajustes_inicial("clasica")
    logo0 = dict(a["capas"]["logo"])
    b = estado.mover_capa(a, "foto", x=0.5, y=0.5)
    assert b["capas"]["foto"]["x"] == 0.5 and b["capas"]["foto"]["y"] == 0.5
    assert b["capas"]["logo"] == logo0           # no mutó otras
    assert a["capas"]["foto"] != b["capas"]["foto"]  # no mutó el original (copia)

def test_mover_capa_clampa_a_0_1():
    a = estado.ajustes_inicial("clasica")
    b = estado.mover_capa(a, "logo", x=-0.3, w=2.0)
    assert b["capas"]["logo"]["x"] == 0.0
    assert b["capas"]["logo"]["w"] == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_estado_capas.py -q --no-header`
Expected: FAIL (`AttributeError: module 'estado' has no attribute 'CAPAS_IDS'`).

- [ ] **Step 3: Write minimal implementation**

```python
# añadir a codigo/estado.py
CAPAS_IDS = ("logo", "foto", "nombre", "cargo", "datos")

# Posiciones por defecto (fracción de la tarjeta). Horizontal por defecto; el caller
# puede recolocar según el modelo en fases siguientes. Cajas pensadas para no encimarse.
_CAPAS_H = {
    "logo":   {"x": 0.04, "y": 0.06, "w": 0.30, "h": 0.20},
    "foto":   {"x": 0.72, "y": 0.18, "w": 0.22, "h": 0.62},
    "nombre": {"x": 0.05, "y": 0.40, "w": 0.55, "h": 0.12},
    "cargo":  {"x": 0.05, "y": 0.53, "w": 0.55, "h": 0.08},
    "datos":  {"x": 0.05, "y": 0.64, "w": 0.60, "h": 0.30},
}
_CAPAS_V = {
    "logo":   {"x": 0.18, "y": 0.05, "w": 0.64, "h": 0.16},
    "foto":   {"x": 0.28, "y": 0.24, "w": 0.44, "h": 0.34},
    "nombre": {"x": 0.08, "y": 0.60, "w": 0.84, "h": 0.09},
    "cargo":  {"x": 0.08, "y": 0.69, "w": 0.84, "h": 0.06},
    "datos":  {"x": 0.08, "y": 0.77, "w": 0.84, "h": 0.20},
}

def capas_inicial(orientacion="H"):
    base = _CAPAS_V if orientacion == "V" else _CAPAS_H
    return {k: dict(v) for k, v in base.items()}

def _clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else float(v)

def mover_capa(ajustes, capa_id, x=None, y=None, w=None, h=None):
    nuevo = deepcopy(ajustes)
    caja = nuevo.setdefault("capas", {}).setdefault(capa_id, {"x": 0, "y": 0, "w": 0.2, "h": 0.2})
    for nombre, val in (("x", x), ("y", y), ("w", w), ("h", h)):
        if val is not None:
            caja[nombre] = _clamp01(val)
    return nuevo
```

Y en `ajustes_inicial`, agregar la clave `"capas"`:

```python
    return {
        "modelo": modelo_clave,
        "color": None,
        "logo_pos": "default",
        "textos": {},
        "empresa": "",
        "filas": [dict(f) for f in FILAS_DEFAULT],
        "capas": capas_inicial("H"),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_estado_capas.py -q --no-header`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git -C C:/Users/Diego/mockups-credenciales add codigo/estado.py tests/test_estado_capas.py
git -C C:/Users/Diego/mockups-credenciales commit -m "feat(estado): modelo de capas (posicion/tamano normalizados) para el editor visual"
```

---

## Task 2: Serializar / reabrir ajustes (persistencia de cotización)

**Files:**
- Modify: `codigo/estado.py`
- Test: `tests/test_estado_capas.py`

**Interfaces:**
- Produces:
  - `serializar(ajustes, empresa, logo_ruta, foto_ruta) -> dict` (JSON-safe).
  - `deserializar(data) -> dict` con claves `ajustes, empresa, logo_ruta, foto_ruta`; tolera campos faltantes (cotización vieja) rellenando con defaults.

- [ ] **Step 1: Write the failing test**

```python
import json

def test_serializar_y_volver_es_identico():
    a = estado.ajustes_inicial("clasica")
    a = estado.mover_capa(a, "logo", x=0.1, y=0.2)
    data = estado.serializar(a, "ACME SAC", r"C:\logos\acme.png", None)
    txt = json.dumps(data)                       # debe ser JSON-safe
    vuelto = estado.deserializar(json.loads(txt))
    assert vuelto["ajustes"]["capas"]["logo"]["x"] == 0.1
    assert vuelto["empresa"] == "ACME SAC"
    assert vuelto["logo_ruta"].endswith("acme.png")

def test_deserializar_tolera_cotizacion_vieja():
    vuelto = estado.deserializar({"ajustes": {"modelo": "clasica"}})
    assert "capas" in vuelto["ajustes"]          # rellena capas faltantes
    assert vuelto["empresa"] == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_estado_capas.py -k serializ -q --no-header`
Expected: FAIL (`module 'estado' has no attribute 'serializar'`).

- [ ] **Step 3: Write minimal implementation**

```python
# añadir a codigo/estado.py
def serializar(ajustes, empresa, logo_ruta, foto_ruta):
    return {
        "version": 1,
        "ajustes": deepcopy(ajustes),
        "empresa": empresa or "",
        "logo_ruta": logo_ruta or "",
        "foto_ruta": foto_ruta or "",
    }

def deserializar(data):
    data = data or {}
    ajustes = deepcopy(data.get("ajustes") or {})
    ajustes.setdefault("modelo", "clasica")
    ajustes.setdefault("color", None)
    ajustes.setdefault("logo_pos", "default")
    ajustes.setdefault("textos", {})
    ajustes.setdefault("empresa", "")
    ajustes.setdefault("filas", [dict(f) for f in FILAS_DEFAULT])
    if "capas" not in ajustes:
        ajustes["capas"] = capas_inicial("H")
    return {
        "ajustes": ajustes,
        "empresa": data.get("empresa") or "",
        "logo_ruta": data.get("logo_ruta") or "",
        "foto_ruta": data.get("foto_ruta") or "",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_estado_capas.py -q --no-header`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git -C C:/Users/Diego/mockups-credenciales add codigo/estado.py tests/test_estado_capas.py
git -C C:/Users/Diego/mockups-credenciales commit -m "feat(estado): serializar/deserializar cotizacion (persistencia tolerante)"
```

---

## Task 3: Matemática de cajas y snap en lienzo.py

**Files:**
- Create: `codigo/lienzo.py`
- Test: `tests/test_lienzo.py`

**Interfaces:**
- Produces:
  - `caja_px(caja, W, H) -> (x0, y0, x1, y1)` enteros (normalizado→pixel).
  - `GUIAS = (0.0, 0.5, 1.0)` (bordes + centro).
  - `snap(v, guias=GUIAS, umbral=0.02) -> float` — pega `v` a la guía más cercana dentro de `umbral`, si no, devuelve `v`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lienzo.py
import lienzo

def test_caja_px_convierte_normalizado_a_pixel():
    assert lienzo.caja_px({"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}, 1000, 600) == (0, 0, 500, 300)
    assert lienzo.caja_px({"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5}, 1000, 600) == (500, 300, 1000, 600)

def test_snap_pega_a_guia_cercana():
    assert lienzo.snap(0.49) == 0.5           # cerca del centro -> pega
    assert lienzo.snap(0.012) == 0.0          # cerca del borde -> pega
    assert lienzo.snap(0.30) == 0.30          # lejos -> queda igual
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lienzo.py -q --no-header`
Expected: FAIL (`ModuleNotFoundError: No module named 'lienzo'`).

- [ ] **Step 3: Write minimal implementation**

```python
# codigo/lienzo.py  (encabezado + matemática)
# -*- coding: utf-8 -*-
"""Compositor de capas del editor visual. Dado un fondo + capas (cajas normalizadas)
+ recursos (logo/foto/textos), arma la credencial a cualquier resolucion con Pillow.
El MISMO compositor alimenta preview y export => WYSIWYG. Sin tkinter, sin red."""
from PIL import Image, ImageDraw

GUIAS = (0.0, 0.5, 1.0)

def caja_px(caja, W, H):
    x0 = int(round(caja["x"] * W)); y0 = int(round(caja["y"] * H))
    x1 = int(round((caja["x"] + caja["w"]) * W)); y1 = int(round((caja["y"] + caja["h"]) * H))
    return (x0, y0, x1, y1)

def snap(v, guias=GUIAS, umbral=0.02):
    mejor = min(guias, key=lambda g: abs(g - v))
    return mejor if abs(mejor - v) <= umbral else v
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_lienzo.py -q --no-header`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git -C C:/Users/Diego/mockups-credenciales add codigo/lienzo.py tests/test_lienzo.py
git -C C:/Users/Diego/mockups-credenciales commit -m "feat(lienzo): matematica de cajas normalizadas + snap a guias"
```

---

## Task 4: Compositor de capas (imagen + texto + bloque de datos)

**Files:**
- Modify: `codigo/lienzo.py`
- Test: `tests/test_lienzo.py`

**Interfaces:**
- Consumes: `caja_px` (Task 3); `motor.fuente(peso, tam)` (ya existe, `motor.py:75`).
- Produces:
  - `componer(fondo, capas, recursos, W, H) -> PIL.Image (RGBA)` donde:
    - `fondo`: PIL.Image (se reescala a W×H).
    - `capas`: dict id→caja normalizada.
    - `recursos`: dict id→spec: imagen `{"tipo":"imagen","img":PIL}`; texto `{"tipo":"texto","texto":str,"peso":int,"color":(r,g,b)}`; datos `{"tipo":"datos","filas":[(etq,val)],"color_etq":(r,g,b),"color_val":(r,g,b)}`.
  - `encajar_en(img, w, h) -> PIL.Image` — reescala manteniendo proporción para caber en w×h (logo/foto no se deforman).

- [ ] **Step 1: Write the failing test**

```python
from PIL import Image

def test_componer_devuelve_tamano_pedido():
    fondo = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    out = lienzo.componer(fondo, {}, {}, 1011, 638)
    assert out.size == (1011, 638)

def test_capa_imagen_centrada_cae_al_centro():
    fondo = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    rojo = Image.new("RGBA", (50, 50), (255, 0, 0, 255))
    capas = {"logo": {"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2}}
    recursos = {"logo": {"tipo": "imagen", "img": rojo}}
    out = lienzo.componer(fondo, capas, recursos, 100, 100)
    assert out.getpixel((50, 50))[:3] == (255, 0, 0)   # hay rojo en el centro
    assert out.getpixel((5, 5))[:3] == (255, 255, 255)  # esquina sigue blanca

def test_encajar_mantiene_proporcion():
    img = Image.new("RGBA", (200, 100), (0, 0, 0, 255))   # 2:1
    out = lienzo.encajar_en(img, 50, 50)
    assert out.size == (50, 25)                            # cabe sin deformar
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lienzo.py -q --no-header`
Expected: FAIL (`module 'lienzo' has no attribute 'componer'`).

- [ ] **Step 3: Write minimal implementation**

```python
# añadir a codigo/lienzo.py
def encajar_en(img, w, h):
    w = max(1, int(w)); h = max(1, int(h))
    out = img.copy()
    out.thumbnail((w, h), Image.LANCZOS)
    return out

def _fuente(peso, tam):
    from motor import fuente            # import diferido: evita ciclo lienzo<->motor
    return fuente(peso, max(8, int(tam)))

def _dibujar_texto(base, caja_px_v, spec):
    x0, y0, x1, y1 = caja_px_v
    alto = max(8, y1 - y0)
    fnt = _fuente(spec.get("peso", 700), int(alto * 0.8))
    ImageDraw.Draw(base).text((x0, y0), spec.get("texto", ""), font=fnt,
                              fill=tuple(spec.get("color", (30, 30, 30))))

def _dibujar_datos(base, caja_px_v, spec):
    x0, y0, x1, y1 = caja_px_v
    filas = [(e, v) for e, v in spec.get("filas", []) if e]
    if not filas:
        return
    alto_fila = max(10, (y1 - y0) // max(1, len(filas)))
    fnt = _fuente(700, int(alto_fila * 0.62))
    d = ImageDraw.Draw(base)
    y = y0
    for etq, val in filas:
        d.text((x0, y), etq + "  ", font=fnt, fill=tuple(spec.get("color_etq", (30, 110, 80))))
        wlbl = d.textlength(etq + "   ", font=fnt)
        d.text((x0 + wlbl, y), val, font=fnt, fill=tuple(spec.get("color_val", (40, 40, 40))))
        y += alto_fila

def componer(fondo, capas, recursos, W, H):
    base = fondo.convert("RGBA").resize((W, H), Image.LANCZOS) if fondo else Image.new("RGBA", (W, H), (255, 255, 255, 255))
    orden = ("datos", "nombre", "cargo", "foto", "logo")   # logo y foto encima
    for cid in [c for c in orden if c in capas and c in recursos]:
        spec = recursos[cid]; cpx = caja_px(capas[cid], W, H)
        if spec.get("tipo") == "imagen" and spec.get("img") is not None:
            pieza = encajar_en(spec["img"].convert("RGBA"), cpx[2] - cpx[0], cpx[3] - cpx[1])
            base.alpha_composite(pieza, (cpx[0], cpx[1]))
        elif spec.get("tipo") == "texto":
            _dibujar_texto(base, cpx, spec)
        elif spec.get("tipo") == "datos":
            _dibujar_datos(base, cpx, spec)
    return base
```

- [ ] **Step 3b: Verify it passes**

Run: `python -m pytest tests/test_lienzo.py -q --no-header`
Expected: PASS (5 passed).

- [ ] **Step 4: Render-and-LOOK (obligatorio)**

Crear `tests/_ver_compositor.py`:

```python
# tests/_ver_compositor.py — arma un caso real y guarda un PNG para MIRAR
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))
from PIL import Image
import lienzo, estado

fondo = Image.new("RGBA", (1011, 638), (245, 246, 248, 255))
logo = Image.new("RGBA", (400, 200), (20, 110, 80, 255))      # placeholder
foto = Image.new("RGBA", (300, 380), (200, 200, 205, 255))
a = estado.ajustes_inicial("clasica")
recursos = {
    "logo": {"tipo": "imagen", "img": logo},
    "foto": {"tipo": "imagen", "img": foto},
    "nombre": {"tipo": "texto", "texto": "Nombre Apellido", "peso": 800, "color": (30, 30, 30)},
    "cargo": {"tipo": "texto", "texto": "Cargo del colaborador", "peso": 600, "color": (90, 90, 90)},
    "datos": {"tipo": "datos", "filas": [("Código", "A-102"), ("Área", "Operaciones")],
              "color_etq": (20, 110, 80), "color_val": (40, 40, 40)},
}
out = lienzo.componer(fondo, a["capas"], recursos, 1011, 638)
ruta = os.path.join(os.path.dirname(__file__), "_ver_compositor.png")
out.convert("RGB").save(ruta)
print(ruta)
```

Run: `python C:/Users/Diego/mockups-credenciales/tests/_ver_compositor.py`
Luego ABRIR `tests/_ver_compositor.png` con la herramienta Read y confirmar visualmente: logo arriba-izq, foto a la derecha, nombre/cargo/datos legibles y sin encimarse. Ajustar defaults de `_CAPAS_H` (Task 1) si algo se tapa.

- [ ] **Step 5: Commit**

```bash
git -C C:/Users/Diego/mockups-credenciales add codigo/lienzo.py tests/test_lienzo.py tests/_ver_compositor.py
git -C C:/Users/Diego/mockups-credenciales commit -m "feat(lienzo): compositor de capas (imagen/texto/datos) verificado a la vista"
```

---

## Task 5: Fondo decorativo del modelo (sin elementos editables)

**Files:**
- Modify: `codigo/motor.py`
- Test: `tests/test_lienzo.py` (un smoke que NO use Edge si no hay navegador → skip)

**Interfaces:**
- Consumes: `construir_contexto`, `cara` (plantillas), `render_caras` (render.py), `paleta_del_logo`, `_hex_a_rgb` (motor.py).
- Produces: `fondo_de_modelo(logo, cliente, ajustes) -> PIL.Image` — rasteriza el modelo elegido con logo/foto/datos/héroe EN BLANCO (transparentes/vacíos) → queda solo la decoración. Tamaño CR80 según orientación.

- [ ] **Step 1: Implement**

```python
# añadir a codigo/motor.py (cerca de render_modelo)
_PIXEL_TRANSP = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def fondo_de_modelo(logo, cliente, ajustes):
    """Rasteriza SOLO la decoracion del modelo (sin logo/foto/datos/hero) para usarla
    como fondo del compositor de capas. Reusa las plantillas sin modificarlas: vacia los
    elementos editables en el ctx antes de pintar."""
    from plantillas import cara, construir_contexto
    from render import render_caras
    ajustes = ajustes or {}
    color = ajustes.get("color")
    if color:
        prim = _hex_a_rgb(color); sec = tuple(int(x * 0.6) for x in prim)
    else:
        prim, sec = paleta_del_logo(logo)
    ctx = construir_contexto(logo, prim, sec, cliente, ajustes)
    ctx["logo_uri"] = _PIXEL_TRANSP
    ctx["foto_uri"] = _PIXEL_TRANSP
    ctx["filas"] = []
    ctx["datos"] = dict(ctx["datos"], nombre="", cargo="")
    html, w, h = cara(ajustes["modelo"], "frontal", ctx)
    img = render_caras([(html, w, h)])[0]
    destino = (CARD_W, CARD_H) if img.width > img.height else (V_W, V_H)
    return img.resize(destino, Image.LANCZOS)
```

- [ ] **Step 2: Render-and-LOOK (obligatorio)**

Correr (con un logo real cualquiera de `entrada/` o Downloads), guardar el fondo y MIRARLO: debe verse la decoración del modelo (bandas/formas) SIN logo, SIN foto, SIN datos. Anotar si queda un marco de foto fijo que estorbe (se resuelve por-modelo en Fase 2).

```python
# en una sesión rápida de Python o ampliando _ver_compositor.py:
#   from motor import cargar_logo, fondo_de_modelo
#   import estado
#   logo = cargar_logo(r"RUTA\a\un\logo.png")
#   fondo_de_modelo(logo, "ACME", estado.ajustes_inicial("clasica")).save(r"...\_fondo.png")
```

ABRIR `_fondo.png` con Read y confirmar.

- [ ] **Step 3: Commit**

```bash
git -C C:/Users/Diego/mockups-credenciales add codigo/motor.py
git -C C:/Users/Diego/mockups-credenciales commit -m "feat(motor): fondo_de_modelo (decoracion sin elementos editables) para el compositor"
```

---

## Task 6: Reconectar render_modelo y exportar_personalizado al compositor

**Files:**
- Modify: `codigo/motor.py:1204-1245`
- Test: manual render-and-look (preview == export).

**Interfaces:**
- Consumes: `fondo_de_modelo` (Task 5), `lienzo.componer` (Task 4), `estado`/ctx textos+filas, `_foto_uri`/foto real.
- Produces: `render_modelo(logo, cliente, ajustes, escala=1.0)` ahora compone capas; `exportar_personalizado` usa el MISMO `render_modelo` a full-res (ya lo hace) → WYSIWYG.

- [ ] **Step 1: Implement** — construir `recursos` desde ajustes y componer

```python
def render_modelo(logo, cliente, ajustes, escala=1.0):
    """Compone la credencial a partir del fondo del modelo + capas movibles
    (logo/foto/nombre/cargo/datos). El MISMO camino alimenta preview y export."""
    from plantillas import construir_contexto
    import lienzo, estado
    ajustes = ajustes or {}
    capas = ajustes.get("capas") or estado.capas_inicial("H")
    color = ajustes.get("color")
    if color:
        prim = _hex_a_rgb(color); sec = tuple(int(x * 0.6) for x in prim)
    else:
        prim, sec = paleta_del_logo(logo)
    ctx = construir_contexto(logo, prim, sec, cliente, ajustes)
    fondo = fondo_de_modelo(logo, cliente, ajustes)
    W, H = fondo.size
    W, H = int(W * escala), int(H * escala)
    foto = _foto_pil(ajustes)                     # foto real del cliente o demo (Task: helper abajo)
    acc = _hex_a_rgb(ctx["prim_legible"]) if isinstance(ctx["prim_legible"], str) and ctx["prim_legible"].startswith("#") else (30, 110, 80)
    recursos = {
        "logo": {"tipo": "imagen", "img": logo},
        "foto": {"tipo": "imagen", "img": foto},
        "nombre": {"tipo": "texto", "texto": ctx["datos"].get("nombre", ""), "peso": 800, "color": (30, 30, 30)},
        "cargo": {"tipo": "texto", "texto": ctx["datos"].get("cargo", ""), "peso": 600, "color": (90, 90, 90)},
        "datos": {"tipo": "datos", "filas": ctx["filas"], "color_etq": acc, "color_val": (40, 40, 40)},
    }
    return lienzo.componer(fondo, capas, recursos, W, H)
```

Añadir helper de foto (demo por ahora; subir foto del cliente es Fase 2):

```python
def _foto_pil(ajustes):
    from PIL import Image
    ruta = (ajustes or {}).get("foto_ruta")
    if ruta and os.path.exists(ruta):
        return Image.open(ruta).convert("RGBA")
    from plantillas.base import FOTO_PERSONA
    return Image.open(FOTO_PERSONA).convert("RGBA")
```

`exportar_personalizado` no cambia su firma: ya llama `render_modelo(logo, cliente, ajustes)` → ahora compone. (El PDF sigue vía `armar_pdf`.)

- [ ] **Step 2: Render-and-LOOK (preview == export)** — el corazón del WYSIWYG

Renderizar el MISMO ajuste a dos escalas y confirmar que son la misma imagen escalada:

```python
#   a = estado.ajustes_inicial("clasica"); logo = cargar_logo(RUTA_LOGO)
#   render_modelo(logo, "ACME", a, escala=0.5).save("_preview.png")
#   render_modelo(logo, "ACME", a, escala=1.0).save("_export.png")
```

ABRIR ambos con Read: deben verse idénticos (uno más grande). Confirmar que el logo NO está recoloreado (tinta real) y nada se deforma.

- [ ] **Step 3: Correr toda la suite (no romper lo viejo)**

Run: `python -m pytest C:/Users/Diego/mockups-credenciales/tests -q --no-header`
Expected: la suite existente sigue verde (ajustar tests que asumían el render HTML viejo del personalizado, si los hay; los del catálogo/folleto/renombrador no se tocan).

- [ ] **Step 4: Commit**

```bash
git -C C:/Users/Diego/mockups-credenciales add codigo/motor.py
git -C C:/Users/Diego/mockups-credenciales commit -m "feat(motor): render_modelo compone capas (preview=export, WYSIWYG)"
```

---

## Task 7: Lienzo interactivo en app.py (arrastrar/estirar + guías/snap)

**Files:**
- Modify: `codigo/app.py:300-331` (cuerpo de la pestaña) y métodos `_p_*`.
- Test: smoke headless (construye la GUI sin mainloop) + render-and-look interactivo.

**Interfaces:**
- Consumes: `render_modelo` (Task 6), `estado.mover_capa`, `lienzo.snap/caja_px`.
- Produces: en el panel izquierdo, un `tk.Canvas` que (a) muestra el preview compuesto como fondo, (b) dibuja un rectángulo de selección por capa, (c) permite arrastrar (mover x,y) y estirar desde una esquina (cambiar w,h) actualizando `self.p_ajustes` vía `estado.mover_capa`, (d) muestra guías punteadas y hace snap al soltar, (e) re-renderiza (debounce) tras cada cambio.

- [ ] **Step 1: Reemplazar el Label de preview por un Canvas** (líneas 303-310)

```python
        izq = tk.Frame(cuerpo, bg="#F4F4F6", width=560)
        izq.pack(side="left", fill="both", expand=True)
        izq.pack_propagate(False)
        self._p_izq = izq
        izq.bind("<Configure>", lambda _e: self._p_fit_preview_debounced())
        self.p_canvas = tk.Canvas(izq, bg="#F4F4F6", highlightthickness=0, cursor="hand2")
        self.p_canvas.pack(expand=True, fill="both")
        self.p_canvas.bind("<Button-1>", self._p_canvas_down)
        self.p_canvas.bind("<B1-Motion>", self._p_canvas_drag)
        self.p_canvas.bind("<ButtonRelease-1>", self._p_canvas_up)
        self._p_capa_sel = None          # capa que se está moviendo
        self._p_modo = None              # "mover" | "estirar"
        self._p_canvas_geo = None        # (offx, offy, escala_px) del preview en el canvas
```

- [ ] **Step 2: Dibujar el preview + cajas de capa en el canvas**

Reemplazar `_p_fit_preview` para pintar la imagen compuesta y, encima, los rectángulos de capa (con asas en las esquinas). Guardar `self._p_canvas_geo` (offset + escala) para mapear clics↔normalizado. Código completo del método (incluye mapeo px↔norm):

```python
    def _p_fit_preview(self):
        img = getattr(self, "_p_last_full", None)
        if img is None:
            return
        try:
            from PIL import ImageTk
        except Exception:
            self.p_estado.config(text="Cierra y reabre la app para activar el preview. (Exportar ya funciona.)")
            return
        cw = max(160, self.p_canvas.winfo_width()); ch = max(160, self.p_canvas.winfo_height())
        disp = img.copy(); disp.thumbnail((cw - 16, ch - 16), Image.LANCZOS)
        self._p_preview_img = ImageTk.PhotoImage(disp)
        offx = (cw - disp.width) // 2; offy = (ch - disp.height) // 2
        self._p_canvas_geo = (offx, offy, disp.width, disp.height)
        self.p_canvas.delete("all")
        self.p_canvas.create_image(offx, offy, anchor="nw", image=self._p_preview_img)
        for cid, caja in self.p_ajustes.get("capas", {}).items():
            x0 = offx + caja["x"] * disp.width; y0 = offy + caja["y"] * disp.height
            x1 = offx + (caja["x"] + caja["w"]) * disp.width; y1 = offy + (caja["y"] + caja["h"]) * disp.height
            sel = (cid == self._p_capa_sel)
            self.p_canvas.create_rectangle(x0, y0, x1, y1, outline=("#378ADD" if sel else "#B9B9C9"),
                                           dash=(4, 3), width=(2 if sel else 1), tags=("capa", cid))
            self.p_canvas.create_rectangle(x1 - 5, y1 - 5, x1 + 5, y1 + 5, fill="#fff",
                                           outline="#378ADD", tags=("asa", cid))

    def _p_xy_a_norm(self, ex, ey):
        offx, offy, w, h = self._p_canvas_geo
        return ((ex - offx) / max(1, w), (ey - offy) / max(1, h))
```

- [ ] **Step 3: Manejar clic/arrastre/soltar** (mover y estirar) con hit-test por capa

```python
    def _p_canvas_down(self, e):
        if not self._p_canvas_geo:
            return
        nx, ny = self._p_xy_a_norm(e.x, e.y)
        self._p_capa_sel = None; self._p_modo = None
        for cid, c in self.p_ajustes.get("capas", {}).items():
            cerca_asa = abs(nx - (c["x"] + c["w"])) < 0.03 and abs(ny - (c["y"] + c["h"])) < 0.04
            dentro = c["x"] <= nx <= c["x"] + c["w"] and c["y"] <= ny <= c["y"] + c["h"]
            if cerca_asa:
                self._p_capa_sel = cid; self._p_modo = "estirar"; break
            if dentro:
                self._p_capa_sel = cid; self._p_modo = "mover"
        self._p_drag0 = (nx, ny)
        self._p_fit_preview()

    def _p_canvas_drag(self, e):
        if not (self._p_capa_sel and self._p_canvas_geo):
            return
        nx, ny = self._p_xy_a_norm(e.x, e.y)
        dx = nx - self._p_drag0[0]; dy = ny - self._p_drag0[1]
        c = self.p_ajustes["capas"][self._p_capa_sel]
        if self._p_modo == "mover":
            self.p_ajustes = estado.mover_capa(self.p_ajustes, self._p_capa_sel, x=c["x"] + dx, y=c["y"] + dy)
        else:
            self.p_ajustes = estado.mover_capa(self.p_ajustes, self._p_capa_sel,
                                               w=max(0.05, c["w"] + dx), h=max(0.05, c["h"] + dy))
        self._p_drag0 = (nx, ny)
        self._p_redibujar_cajas()        # mover cajas en vivo, sin re-render pesado

    def _p_canvas_up(self, e):
        if not self._p_capa_sel:
            return
        c = self.p_ajustes["capas"][self._p_capa_sel]
        self.p_ajustes = estado.mover_capa(self.p_ajustes, self._p_capa_sel,
                                           x=lienzo.snap(c["x"]), y=lienzo.snap(c["y"]))
        self._p_modo = None
        self._p_schedule_render(120)     # recompone la imagen con la capa en su nuevo sitio
```

`_p_redibujar_cajas` = volver a dibujar SOLO los rectángulos (rápido) reusando la última imagen; para Fase 1 basta llamar `self._p_fit_preview()`. Añadir `import lienzo` arriba en app.py.

- [ ] **Step 4: Smoke headless** (la GUI se construye sin reventar)

Run: `python C:/Users/Diego/mockups-credenciales/launcher.py --smoke` (ya existe; importa código + construye GUI sin mainloop, escribe `smoke_result.txt`).
Expected: `smoke_result.txt` dice OK (sin excepción al crear el Canvas y bindear).

- [ ] **Step 5: Render-and-LOOK interactivo (Diego en vivo, source)**

Abrir la app desde el código (`python codigo/app.py` o `launcher.py`), elegir un logo, y confirmar: se ve la credencial, cada capa tiene su recuadro, se puede ARRASTRAR el logo/foto/textos y ESTIRAR desde la esquina, las guías/snap funcionan, y al soltar el preview se recompone nítido. Capturar un PNG del resultado y MIRARLO.

- [ ] **Step 6: Commit**

```bash
git -C C:/Users/Diego/mockups-credenciales add codigo/app.py
git -C C:/Users/Diego/mockups-credenciales commit -m "feat(app): lienzo interactivo en Personalizar (arrastrar/estirar + guias/snap)"
```

---

## Self-Review (cobertura del spec, Fase 1)

- Editor de capas (arrastrar/estirar logo, foto, textos): Tasks 1, 4, 7. ✅
- Guías + snap: Tasks 3, 7. ✅
- WYSIWYG (mismo compositor preview/export): Tasks 4, 6 (verificación a dos escalas). ✅
- Full-res sin pixelar: Task 4 (`encajar_en` LANCZOS) + Task 6 (escala). ✅
- Persistencia (guardar/reabrir): Task 2 (modelo) — el botón Guardar/Reabrir en la UI se cablea al inicio de la Fase 3. (Anotado: pendiente UI.)
- Logo nunca recoloreado: el compositor pega el logo tal cual (Task 4/6); verificación visual en Task 6. ✅
- Sin dependencias nuevas: solo PIL+tkinter. ✅

**Lo que NO cubre la Fase 1 (va a fases siguientes, plan aparte):**
- Fase 2: anclas por defecto de los 18 modelos + subir/encuadrar la foto del cliente + caras de muestra.
- Fase 3: botones Guardar/Reabrir cotización (UI), limpieza de datos falsos por defecto, un solo botón "Exportar para WhatsApp" (PNG+PDF) con nombre cliente+fecha, bloquear export con empresa vacía/"Cliente".
- Fase 4: pulido mirando los 18, empaque del .exe (recompilar solo si cambian librerías), zip instalador, prueba de Diego antes que Mirza.

## Riesgo vivo a vigilar durante la ejecución
La fidelidad tipográfica del bloque de datos/textos en Pillow vs. el HTML viejo: el compositor reproduce etiqueta(color marca)+valor con `motor.fuente`. Si en la mirada (Task 4/6) se ve pobre, subir calidad ahí ANTES de escalar a los 18 (Fase 2). Es el punto que el spec marcó como principal riesgo técnico.
