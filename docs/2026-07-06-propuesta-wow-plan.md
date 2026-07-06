# Propuesta Wow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir el PDF catálogo de 18 modelos en una propuesta de agencia curada (portada de marca + 1 estrella + 5 alternativas + CTA) que asombre al cliente.

**Architecture:** Módulo nuevo `plantillas/curaduria.py` (scoring por afinidad de color + nombres comerciales, sin dependencias circulares). `folleto.py` gana `armar_propuesta()` (portada v2 con la marca del cliente, página estrella, alternativas con aire, CTA) sin romper `armar_pdf()` legacy. `motor.paleta_marca()` aplica la regla anti-lavado antes de construir el contexto; `generar()` orquesta la curaduría.

**Tech Stack:** Python 3 + Pillow (composición PDF), HTML/CSS→Edge (render de tarjetas, sin cambios), pytest.

## Global Constraints

- 🔒 EL LOGO DEL CLIENTE NUNCA SE RECOLOREA (test existente `test_logo_cliente_no_se_recolorea` debe seguir verde).
- 🔒 Colores PLANOS (sin degradados saturados ni fondos oscuros grandes — bandean en Evolis).
- 🔒 Nunca placas/cajas detrás del logo; el logo flota en zona clara.
- Los 18 modelos y sus claves NO cambian; Personalizar y `para-diseno\` intactos.
- cwd de todos los comandos: `C:\Users\Diego\mockups-credenciales`. pytest PELADO (`python -m pytest <archivo> -q --no-header`, sin pipes — el pipe manda el proceso a background en esta máquina).
- Cada import nuevo en `codigo\` → revisar si hay que forzarlo en `launcher.py` (aquí no hay librerías nuevas: solo stdlib `colorsys`, ya disponible).
- NO correr `publicar.py` hasta el OK visual de Diego (Task 7).

---

### Task 1: Curaduría — `plantillas/curaduria.py`

**Files:**
- Create: `codigo/plantillas/curaduria.py`
- Test: `tests/test_curaduria.py`

**Interfaces:**
- Produces: `elegir_top(prim, n=6) -> list[str]` (claves ordenadas por score desc; `[0]` = estrella; garantiza ≥2 'V' y ≥2 'H'), `nombre_comercial(clave) -> str`, `AFINIDAD: dict`, `NOMBRES: dict`.
- Consumes: `plantillas.registro.catalogo()` (para orientación de cada clave).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_curaduria.py
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))

LAVANDA = (169, 161, 216)   # tinta clara (caso DISECOD)
ROJO = (180, 30, 40)        # tinta saturada oscura


def test_top6_devuelve_6_claves_validas():
    from plantillas.curaduria import elegir_top
    from plantillas.registro import catalogo
    import plantillas  # noqa: F401  (importa y registra los 18 modelos)
    claves = {m.clave for m in catalogo()}
    top = elegir_top(LAVANDA)
    assert len(top) == 6 and len(set(top)) == 6
    assert set(top) <= claves


def test_top6_balancea_orientaciones():
    from plantillas.curaduria import elegir_top
    from plantillas.registro import catalogo
    import plantillas  # noqa: F401
    ori = {m.clave: m.orientacion for m in catalogo()}
    for tinta in (LAVANDA, ROJO):
        top = elegir_top(tinta)
        vs = sum(1 for c in top if ori[c] == "V")
        hs = sum(1 for c in top if ori[c] == "H")
        assert vs >= 2 and hs >= 2


def test_pastel_castiga_modelos_que_necesitan_oscuro():
    from plantillas.curaduria import elegir_top
    import plantillas  # noqa: F401
    top_pastel = elegir_top(LAVANDA)
    # mv1 (Acción) y mv2 (Böka) necesitan acento oscuro: con lavanda NO deben entrar
    assert "mv1" not in top_pastel and "mv2" not in top_pastel


def test_nombres_comerciales_cubren_todo_el_catalogo():
    from plantillas.curaduria import nombre_comercial, NOMBRES
    from plantillas.registro import catalogo
    import plantillas  # noqa: F401
    for m in catalogo():
        n = nombre_comercial(m.clave)
        assert n and "(" not in n          # sin "(vertical)"/"(horizontal)"
        assert n == NOMBRES.get(m.clave, n)
    # los nombres internos raros no se filtran al cliente
    prohibidos = {"Böka", "Rosestore", "Vegetata", "Gaio"}
    assert not (set(NOMBRES.values()) & prohibidos)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_curaduria.py -q --no-header`
Expected: FAIL con `ModuleNotFoundError: No module named 'plantillas.curaduria'`

- [ ] **Step 3: Write minimal implementation**

```python
# codigo/plantillas/curaduria.py
# -*- coding: utf-8 -*-
"""Curaduría del folleto: elige los TOP-6 modelos según la tinta del cliente y
da nombres comerciales (cliente-facing). Sin dependencias de motor.py (helpers
de color locales) para evitar import circular."""
import colorsys

from .registro import catalogo

# score base (calidad visual medida mirando renders) + afinidades de color
# necesita_oscuro: con tintas pastel/claras el modelo queda lavado → castigar.
AFINIDAD = {
    "premium": {"base": 9, "necesita_oscuro": False},
    "mh7":     {"base": 9, "necesita_oscuro": False},   # círculo navy
    "mh2":     {"base": 8, "necesita_oscuro": False},
    "mv6":     {"base": 8, "necesita_oscuro": False},
    "mh1":     {"base": 8, "necesita_oscuro": False},
    "clasica": {"base": 7, "necesita_oscuro": False},
    "mv8":     {"base": 7, "necesita_oscuro": False},
    "gafete":  {"base": 7, "necesita_oscuro": False},
    "mh6":     {"base": 6, "necesita_oscuro": False},
    "mv3":     {"base": 6, "necesita_oscuro": True},    # banda superior grande
    "mv7":     {"base": 6, "necesita_oscuro": False},
    "mh5":     {"base": 6, "necesita_oscuro": False},
    "mv5":     {"base": 5, "necesita_oscuro": False},
    "mv4":     {"base": 5, "necesita_oscuro": True},    # doble banda
    "mh3":     {"base": 5, "necesita_oscuro": False},
    "mh4":     {"base": 4, "necesita_oscuro": True},
    "mv1":     {"base": 4, "necesita_oscuro": True},    # triángulo grande
    "mv2":     {"base": 4, "necesita_oscuro": True},    # blobs grandes
}

NOMBRES = {
    "clasica": "Clásica", "gafete": "Gafete Ejecutivo", "premium": "Premium",
    "mv1": "Impacto", "mv2": "Orgánica", "mv3": "Corporativa",
    "mv4": "Doble Banda", "mv5": "Tecnológica", "mv6": "Minimalista",
    "mv7": "Salud", "mv8": "Ondas",
    "mh1": "Ejecutiva", "mh2": "Dinámica", "mh3": "Industrial",
    "mh4": "Fluida", "mh5": "Estudio", "mh6": "Urbana", "mh7": "Círculo",
}


def _hls(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hls(r, g, b)   # (h, l, s)


def es_pastel(prim):
    """Tinta clara o desaturada: los modelos de bandas grandes quedan lavados."""
    _h, l, s = _hls(prim)
    return l > 0.60 or s < 0.30


def nombre_comercial(clave):
    return NOMBRES.get(clave, clave.capitalize())


def elegir_top(prim, n=6):
    """Claves de los n mejores modelos para esta tinta; [0] = estrella.
    Garantiza ≥2 verticales y ≥2 horizontales."""
    pastel = es_pastel(prim)
    ori = {m.clave: m.orientacion for m in catalogo()}

    def score(clave):
        a = AFINIDAD.get(clave, {"base": 5, "necesita_oscuro": False})
        s = a["base"]
        if pastel and a["necesita_oscuro"]:
            s -= 4
        return s

    orden = sorted(ori, key=lambda c: (-score(c), c))
    top = orden[:n]
    # balance de orientaciones: mete el mejor de la orientación faltante
    for necesita in ("V", "H"):
        while sum(1 for c in top if ori[c] == necesita) < 2:
            candidato = next(c for c in orden if c not in top and ori[c] == necesita)
            # saca el peor de la orientación sobrante
            sobrante = max((c for c in top if ori[c] != necesita),
                           key=lambda c: orden.index(c))
            top[top.index(sobrante)] = candidato
    return top
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_curaduria.py -q --no-header`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git -C "C:\Users\Diego\mockups-credenciales" add codigo/plantillas/curaduria.py tests/test_curaduria.py docs/2026-07-06-propuesta-wow-design.md docs/2026-07-06-propuesta-wow-plan.md
git -C "C:\Users\Diego\mockups-credenciales" commit -m "feat: curaduria top-6 por tinta + nombres comerciales (propuesta wow)"
```

---

### Task 2: Color 2.0 — `paleta_marca()` anti-lavado + fix gris de mh4

**Files:**
- Modify: `codigo/motor.py` (agregar `paleta_marca` cerca de `paleta_del_logo`, ~línea 246; usarla en `generar()` ~línea 1361 y `_prim_sec()` ~línea 1218)
- Modify: `codigo/plantillas/modelos/mh4_gaio.py` (reemplazar el gris hardcodeado)
- Test: `tests/test_paleta_marca.py`

**Interfaces:**
- Produces: `motor.paleta_marca(prim, sec) -> ((r,g,b), (r,g,b))` — prim profundizado si es pastel (L≤0.50 y S≥0.45), intacto si ya es fuerte; sec siempre más oscuro que prim.
- Consumes: nada nuevo (usa `colorsys` stdlib).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_paleta_marca.py
# -*- coding: utf-8 -*-
import sys, os, colorsys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))


def _hls(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hls(r, g, b)


def test_pastel_se_profundiza():
    from motor import paleta_marca
    lavanda = (169, 161, 216)
    prim, sec = paleta_marca(lavanda, tuple(int(x * 0.6) for x in lavanda))
    h0, _l0, _s0 = _hls(lavanda)
    h1, l1, s1 = _hls(prim)
    assert l1 <= 0.50 and s1 >= 0.45          # ya no está lavado
    assert abs(h1 - h0) < 0.05                # mismo matiz (sigue siendo SU marca)


def test_tinta_fuerte_no_se_toca():
    from motor import paleta_marca
    rojo = (180, 30, 40)
    prim, _sec = paleta_marca(rojo, (90, 15, 20))
    assert prim == rojo


def test_sec_siempre_mas_oscuro():
    from motor import paleta_marca, luminancia
    for tinta in ((169, 161, 216), (180, 30, 40), (30, 30, 30)):
        prim, sec = paleta_marca(tinta, tuple(int(x * 0.6) for x in tinta))
        assert luminancia(sec) < luminancia(prim) or prim == sec


def test_mh4_sin_gris_huerfano():
    src = open(os.path.join(os.path.dirname(__file__), "..", "codigo",
               "plantillas", "modelos", "mh4_gaio.py"), encoding="utf-8").read()
    # ningún gris hardcodeado tipo #999/#aaa/#bbb/rgb(1xx,1xx,1xx) fuera de la paleta
    import re
    assert not re.search(r"#(9[0-9a-f]{2}|a[0-9a-f]{2}|b[0-9a-f]{2})\b", src, re.I)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_paleta_marca.py -q --no-header`
Expected: FAIL con `ImportError: cannot import name 'paleta_marca'`

- [ ] **Step 3: Write minimal implementation**

En `codigo/motor.py`, después de `oro_del_logo` (~línea 264):

```python
def paleta_marca(prim, sec):
    """Regla anti-lavado (propuesta wow 2026-07-06): si la tinta del cliente es
    pastel (clara o desaturada), las bandas usan una versión PROFUNDA del mismo
    matiz (L<=0.50, S>=0.45); una tinta ya fuerte no se toca. sec se deriva
    del prim final para mantener el par coherente."""
    import colorsys
    r, g, b = [x / 255.0 for x in prim]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l > 0.60 or s < 0.30:
        l, s = min(l, 0.50), max(s, 0.45)
        prim = tuple(int(round(x * 255)) for x in colorsys.hls_to_rgb(h, l, s))
        sec = tuple(int(x * 0.55) for x in prim)
    if luminancia(sec) >= luminancia(prim):
        sec = tuple(int(x * 0.55) for x in prim)
    return prim, sec
```

En `generar()` (~línea 1361), después de obtener `prim, sec`:

```python
    prim, sec = paleta_marca(prim, sec)
```

En `_prim_sec()` (~línea 1218), aplicar lo mismo a su `return` (leer la función
primero; envolver el par que ya devuelve con `paleta_marca(prim, sec)`).

En `mh4_gaio.py`: localizar el color gris hardcodeado (buscar `#9`/`#a`/`#b`/`gray`)
y reemplazarlo por `var(--sec)` (o el tono de la paleta que ya use el modelo).

- [ ] **Step 4: Run tests (nuevos + regresión)**

Run: `python -m pytest tests/test_paleta_marca.py tests/test_motor_html.py tests/test_plantillas_paquete.py -q --no-header`
Expected: todos passed (la regresión confirma que el cambio de paleta no rompe contexto/render)

- [ ] **Step 5: Commit**

```bash
git -C "C:\Users\Diego\mockups-credenciales" add codigo/motor.py codigo/plantillas/modelos/mh4_gaio.py tests/test_paleta_marca.py
git -C "C:\Users\Diego\mockups-credenciales" commit -m "feat: paleta_marca anti-lavado + fix gris huerfano mh4"
```

---

### Task 3: Folleto v2 — portada de agencia con la marca del cliente

**Files:**
- Modify: `codigo/folleto.py` (nueva `_portada_v2(cliente, logo_img, marca)`; conservar `_portada` legacy)
- Test: `tests/test_folleto.py` (agregar tests, no tocar los existentes)

**Interfaces:**
- Produces: `_portada_v2(cliente, logo_img, marca) -> PIL.Image` con `marca=(prim, sec)`.
- Consumes: fuentes ya presentes en `codigo\` (`fuente-display.ttf` para el título, `inter*.ttf` para el resto).

- [ ] **Step 1: Write the failing test**

```python
# agregar a tests/test_folleto.py
def test_portada_v2_usa_la_marca_del_cliente():
    import folleto
    from PIL import Image
    marca = ((90, 70, 190), (40, 30, 90))
    logo = Image.new("RGBA", (400, 160), (10, 10, 10, 255))
    pag = folleto._portada_v2("ACME SAC", logo, marca)
    assert pag.size == folleto.PAG
    px = pag.convert("RGB")
    colores = px.getcolors(pag.size[0] * pag.size[1])
    planos = {c for _n, c in colores}
    assert marca[0] in planos or marca[1] in planos   # la marca está en la portada
    assert (0, 120, 200) not in planos                # adiós azul hardcodeado
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_folleto.py -q --no-header`
Expected: FAIL con `AttributeError: ... '_portada_v2'`

- [ ] **Step 3: Write implementation**

En `codigo/folleto.py`:

```python
def _fuente_display(tam):
    try:
        return ImageFont.truetype(os.path.join(RUTA, "fuente-display.ttf"), tam)
    except Exception:
        return _fuente(tam, True)


def _portada_v2(cliente, logo_img, marca):
    """Portada de agencia: bandas planas con la marca del cliente, logo intacto
    en zona clara, título display. marca=(prim, sec)."""
    prim, sec = marca
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    # banda superior delgada + bloque de color al pie (planos, sin degradados)
    d.rectangle([0, 0, PAG[0], 26], fill=prim)
    d.rectangle([0, PAG[1] - 210, PAG[0], PAG[1]], fill=sec)
    d.rectangle([0, PAG[1] - 224, PAG[0], PAG[1] - 210], fill=prim)
    # zona clara: logo del cliente intacto, grande y centrado
    if logo_img is not None:
        lg = logo_img.convert("RGBA")
        lg.thumbnail((640, 360))
        pag.paste(lg, ((PAG[0] - lg.width) // 2, 300), lg)
    _centrar_texto(d, "Propuesta de credenciales", _fuente_display(72), 760, sec)
    _centrar_texto(d, cliente.upper(), _fuente(44, True), 875, prim)
    _centrar_texto(d, "Diseños seleccionados para tu marca — listos para producir",
                   _fuente(28), 960, TINTA)
    from datetime import date
    _centrar_texto(d, date.today().strftime("Lima, %d/%m/%Y"), _fuente(24), 1020, GRIS)
    _centrar_texto(d, "DISECOD · fotochecks.pe", _fuente(26, True),
                   PAG[1] - 130, (255, 255, 255))
    return pag
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_folleto.py -q --no-header`
Expected: todos passed (nuevos + legacy)

- [ ] **Step 5: Commit**

```bash
git -C "C:\Users\Diego\mockups-credenciales" add codigo/folleto.py tests/test_folleto.py
git -C "C:\Users\Diego\mockups-credenciales" commit -m "feat: portada v2 de agencia con la marca del cliente"
```

---

### Task 4: Folleto v2 — página estrella, alternativas con aire y CTA

**Files:**
- Modify: `codigo/folleto.py` (nuevas `_pagina_estrella`, `_pagina_cta`, `armar_propuesta`; `_grid` gana tamaño de caption)
- Test: `tests/test_folleto.py`

**Interfaces:**
- Produces: `armar_propuesta(cliente, logo_img, estrella, alternativas, ruta_pdf, marca) -> int (páginas)`.
  `estrella` y cada item de `alternativas` = `(nombre_comercial, orientacion, PIL.Image)`.
- Consumes: `_portada_v2` (Task 3). `armar_pdf` legacy queda intacto.

- [ ] **Step 1: Write the failing test**

```python
# agregar a tests/test_folleto.py
def _item(nombre, ori):
    from PIL import Image
    w, h = (638, 1011) if ori == "V" else (1011, 638)
    return (nombre, ori, Image.new("RGB", (w, h), (200, 200, 210)))


def test_armar_propuesta_estructura(tmp_path):
    import folleto
    from PIL import Image
    marca = ((90, 70, 190), (40, 30, 90))
    logo = Image.new("RGBA", (400, 160), (10, 10, 10, 255))
    alts = [_item("Ejecutiva", "H"), _item("Minimalista", "V"),
            _item("Círculo", "H"), _item("Clásica", "H"), _item("Ondas", "V")]
    ruta = str(tmp_path / "propuesta.pdf")
    n = folleto.armar_propuesta("ACME SAC", logo, _item("Premium", "V"), alts, ruta, marca)
    assert os.path.exists(ruta)
    # portada + estrella + alternativas (5 con aire → ≥2 páginas) + CTA
    assert n >= 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_folleto.py -q --no-header`
Expected: FAIL con `AttributeError: ... 'armar_propuesta'`

- [ ] **Step 3: Write implementation**

```python
def _pagina_estrella(item, marca):
    """'Nuestra recomendación': un solo modelo, grande y con aire."""
    prim, sec = marca
    nombre, ori, img = item
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    d.rectangle([0, 0, PAG[0], 16], fill=prim)
    d.text((MARGEN, MARGEN), "Nuestra recomendación", font=_fuente_display(54), fill=sec)
    d.text((MARGEN, MARGEN + 78), "El modelo que mejor le calza a tu marca",
           font=_fuente(26), fill=GRIS)
    th = img.convert("RGB").copy()
    lado = 920 if ori == "H" else 760
    th.thumbnail((lado, 1150))
    pag.paste(th, ((PAG[0] - th.width) // 2, 320))
    y_cap = 320 + th.height + 34
    f_cap = _fuente(34, True)
    w = d.textlength(nombre, font=f_cap)
    d.text(((PAG[0] - w) // 2, y_cap), nombre, font=f_cap, fill=TINTA)
    return pag


def _pagina_cta(cliente, marca):
    prim, sec = marca
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    d.rectangle([0, PAG[1] // 2 - 200, PAG[0], PAG[1] // 2 + 200], fill=sec)
    _centrar_texto(d, "¿Cuál le gustó?", _fuente_display(64), PAG[1] // 2 - 130,
                   (255, 255, 255))
    _centrar_texto(d, "Se lo preparamos con los datos de su equipo — sin costo.",
                   _fuente(30), PAG[1] // 2 - 20, (255, 255, 255))
    _centrar_texto(d, "Responda este WhatsApp con el nombre del modelo elegido.",
                   _fuente(26), PAG[1] // 2 + 50, (230, 230, 235))
    d.rectangle([0, PAG[1] // 2 + 200, PAG[0], PAG[1] // 2 + 214], fill=prim)
    _centrar_texto(d, "DISECOD · fotochecks.pe · Lince, Lima", _fuente(24),
                   PAG[1] - 120, GRIS)
    return pag


def armar_propuesta(cliente, logo_img, estrella, alternativas, ruta_pdf, marca):
    """Propuesta de agencia: portada v2 + estrella + alternativas (2 por página
    con aire, caption 30px con nombre comercial) + CTA. Devuelve nº de páginas."""
    paginas = [_portada_v2(cliente, logo_img, marca), _pagina_estrella(estrella, marca)]
    vs = [it for it in alternativas if it[1] == "V"]
    hs = [it for it in alternativas if it[1] == "H"]
    paginas += _grid(vs, 2, "Alternativas — verticales")
    paginas += _grid(hs, 2, "Alternativas — horizontales")
    paginas.append(_pagina_cta(cliente, marca))
    carpeta = os.path.dirname(os.path.abspath(ruta_pdf))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    paginas[0].save(ruta_pdf, "PDF", save_all=True, append_images=paginas[1:],
                    resolution=150.0, quality=95)
    return len(paginas)
```

Y en `_grid`, subir la fuente de caption de 22 a 30 (`f_l = _fuente(30)`) y el aire
de celda (`th.thumbnail((cw - 60, cell_h - 40))`).

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_folleto.py -q --no-header`
Expected: todos passed

- [ ] **Step 5: Commit**

```bash
git -C "C:\Users\Diego\mockups-credenciales" add codigo/folleto.py tests/test_folleto.py
git -C "C:\Users\Diego\mockups-credenciales" commit -m "feat: armar_propuesta (estrella + alternativas con aire + CTA)"
```

---

### Task 5: Integración — `generar()` produce la propuesta curada

**Files:**
- Modify: `codigo/motor.py::generar` (~líneas 1352-1412)
- Test: `tests/test_motor_html.py` (agregar test de integración con render stubbeado si ya existe patrón; si no, test sobre la selección)

**Interfaces:**
- Consumes: `curaduria.elegir_top(prim)`, `curaduria.nombre_comercial(clave)`, `folleto.armar_propuesta(...)`.
- Produces: `generar()` mantiene su firma y su salida (`catalogo-<cliente>.pdf` + `para-diseno\` con los 18) — el PDF ahora es la propuesta de 6.

- [ ] **Step 1: Write the failing test**

```python
# agregar a tests/test_motor_html.py
def test_generar_cura_top6_y_para_diseno_conserva_18(monkeypatch, tmp_path):
    import motor
    from plantillas.curaduria import elegir_top
    llamadas = {}

    def fake_armar_propuesta(cliente, logo, estrella, alts, ruta, marca):
        llamadas["estrella"] = estrella[0]
        llamadas["n_alts"] = len(alts)
        open(ruta, "wb").write(b"%PDF-1.4 fake")
        return 4
    import folleto
    monkeypatch.setattr(folleto, "armar_propuesta", fake_armar_propuesta)
    # render_caras es caro (Edge): sustituir por imágenes sintéticas
    from PIL import Image
    import render
    monkeypatch.setattr(render, "render_caras",
        lambda items: [Image.new("RGB", (a, b), (220, 220, 225)) for _h, a, b in items])
    motor.generar(None, "ACME SAC", carpeta_salida=str(tmp_path))
    assert llamadas["n_alts"] == 5
    diseno = os.listdir(os.path.join(str(tmp_path), "para-diseno"))
    assert len([f for f in diseno if f.endswith(".png")]) == 18
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_html.py -q --no-header`
Expected: FAIL (generar aún llama `armar_pdf` con los 18)

- [ ] **Step 3: Write implementation**

En `generar()`, tras construir `modelos`/`frentes` (mantener `para-diseno` con los 18),
reemplazar la llamada a `armar_pdf` por:

```python
    from plantillas.curaduria import elegir_top, nombre_comercial
    from folleto import armar_propuesta
    top = elegir_top(prim)
    por_clave = {m.clave: (m, fr) for m, fr in zip(modelos, frentes)}
    def item(clave):
        m, fr = por_clave[clave]
        return (nombre_comercial(clave), m.orientacion, fr)
    ruta_pdf = os.path.join(carpeta_salida, f"catalogo-{slug(cliente)}.pdf")
    paginas = armar_propuesta(cliente, logo, item(top[0]),
                              [item(c) for c in top[1:]], ruta_pdf, (prim, sec))
```

(Ojo: conservar las variables/nombres de salida que la GUI ya espera — revisar el
final actual de `generar()` y mantener su `return`.)

- [ ] **Step 4: Run tests (integración + regresión completa)**

Run: `python -m pytest -q --no-header`
Expected: suite completa verde (118+ tests previos + nuevos)

- [ ] **Step 5: Commit**

```bash
git -C "C:\Users\Diego\mockups-credenciales" add codigo/motor.py tests/test_motor_html.py
git -C "C:\Users\Diego\mockups-credenciales" commit -m "feat: generar() entrega propuesta curada top-6 (para-diseno sigue con 18)"
```

---

### Task 6: Validación visual real (regla de oro) — 3 logos, mirar y afinar

**Files:**
- Create: `tools/_render_propuestas.py` (script de prueba con 3 logos)
- Posibles ajustes finos en `folleto.py` / `curaduria.py` / modelos según lo visto

- [ ] **Step 1: Script de render con 3 tintas distintas**

```python
# tools/_render_propuestas.py — corre generar() con 3 logos de tintas distintas
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))
import motor

CASOS = [
    (r"C:\Users\Diego\mockups-credenciales\docs\referencias-modelos\..", "PENDIENTE"),
]
# Usar: logo real de DISECOD (lavanda/pastel) + 1 logo rojo saturado + 1 logo oscuro.
# Buscar logos reales en Downloads\descargasfotochecksmodelos\ o salida\ previa;
# si no hay, generar 2 logos sintéticos de prueba con Pillow (texto plano de color).
for ruta_logo, nombre in CASOS:
    motor.generar(ruta_logo, nombre,
                  carpeta_salida=os.path.join("salida", "_wow_" + nombre))
    print("OK", nombre)
```

- [ ] **Step 2: Ejecutar y MIRAR (no afirmar sin ver)**

Run: `python tools/_render_propuestas.py`
Luego abrir cada PDF con Read (visual) y revisar contra el checklist:
portada con el color correcto y logo intacto · estrella bien elegida · las 6 se ven
bien con ESA tinta · captions con nombres comerciales y tildes perfectas ("Clásica",
no "Citüsica") · CTA legible · nada lavado, ningún gris huérfano.

- [ ] **Step 3: Ajustes finos según lo visto** (scores de curaduría, tamaños,
colores de banda) — cambios chicos, re-render, volver a mirar.

- [ ] **Step 4: Mostrar los PDFs a Diego para su OK (gate humano)**

- [ ] **Step 5: Commit**

```bash
git -C "C:\Users\Diego\mockups-credenciales" add tools/_render_propuestas.py codigo tests
git -C "C:\Users\Diego\mockups-credenciales" commit -m "chore: validacion visual propuesta wow (3 tintas) + ajustes finos"
```

---

### Task 7: Publicar (SOLO con OK de Diego sobre los renders)

**Files:**
- Modify: `publicar.py` (confirmar que ARCHIVOS incluye `plantillas/curaduria.py` — el patrón `plantillas/**.py` ya podría cubrirlo: verificar)
- Modify: `codigo/version.txt` (lo sube publicar.py)

- [ ] **Step 1: Verificar ARCHIVOS de publicar.py cubre curaduria.py**
- [ ] **Step 2: Correr suite completa una última vez** — `python -m pytest -q --no-header` → verde
- [ ] **Step 3: `python publicar.py`** (sube versión, regenera manifest, push; sin recompilar exe — no hay librerías nuevas)
- [ ] **Step 4: Verificar auto-update** (abrir la app instalada tras ~5 min de CDN, generar un catálogo y confirmar propuesta v2)
- [ ] **Step 5: Actualizar `claude-cerebro\mockups-credenciales.md`** (estado + versión nueva) — vía skill `/cierre` de la sesión

## Self-Review

- **Cobertura del spec:** portada de marca (T3), curaduría top-6 (T1, T5), jerarquía estrella/alternativas/CTA (T4), color anti-lavado + gris mh4 (T2), nombres comerciales (T1, usados en T5), captions/encoding verificado visualmente (T4 sube tamaño, T6 lo mira), validación 3 logos (T6), publicación gated (T7). ✅
- **Placeholders:** el script de T6 tiene CASOS por completar a propósito (los logos se eligen en ejecución con los archivos reales disponibles) — es una decisión de runtime, no un TODO de código. Resto sin placeholders. ✅
- **Consistencia de tipos:** `elegir_top(prim)->list[str]`, items `(nombre, ori, PIL.Image)` iguales en T4/T5; `marca=(prim,sec)` en `_portada_v2`/`_pagina_estrella`/`_pagina_cta`/`armar_propuesta`. ✅
