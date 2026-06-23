# Catálogo de modelos personalizable — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que la app genere un PDF folleto personalizado con los modelos reales del folleto de muestras, pintados con la marca del cliente (logo en su tinta + color del logo), con opción de cambiar el color.

**Architecture:** Cada modelo se reconstruye como plantilla HTML/CSS (Camino 1). Se refactoriza `codigo/plantillas.py` en un paquete `codigo/plantillas/` con un archivo por modelo y un registro central. `motor.generar` itera el registro (solo frentes para el folleto), rasteriza con Edge (`render.py`) y arma el PDF con un módulo nuevo `codigo/folleto.py`. La GUI gana un selector de color.

**Tech Stack:** Python 3.12, Pillow (PIL), HTML/CSS render vía Edge/Chrome headless, tkinter (GUI), pytest.

## Global Constraints

- **El logo del cliente NUNCA se recolorea** — tinta real siempre; prohibido `brightness(0)`, `invert(`, duotono, teñido. (Test `test_logo_cliente_no_se_recolorea` debe seguir verde y cubrir los modelos nuevos.)
- **Fondos claros** en todos los modelos (blanco/crema) → imprimen sin bandeo en Evolis y el logo a color se lee.
- **Compatibilidad de imports:** `from plantillas import cara, construir_contexto, css_base, variante_de` debe seguir funcionando tras el refactor (lo usan los tests y `motor.py`).
- **Render del vendedor = Edge del sistema** (sin empaquetar navegador). No introducir dependencias nuevas en el `.exe`.
- **Datos de muestra fijos** (nombre/cargo/DNI/foto); el catálogo es un boceto de presentación.
- **Solo frentes** en el folleto.
- **Auto-update:** archivos nuevos en `codigo/` deben registrarse en `ARCHIVOS` de `publicar.py` o el vendedor no los recibe.
- **Sin costo por uso:** generación 100% determinista (sin API).
- Tests se corren con: `python -m pytest tests/ -v` desde la raíz del repo.

---

## File Structure

```
codigo/
  plantillas/                 # NUEVO paquete (reemplaza plantillas.py)
    __init__.py               # re-exporta API + registro + catalogo()
    base.py                   # css_base, construir_contexto, _shell, _root, iconos, utils color, variante_de
    registro.py               # registrar(), _MODELOS, catalogo(), cara()
    modelos/
      __init__.py
      clasica.py              # las 3 actuales, movidas tal cual
      gafete.py
      premium.py
      mv1_<nombre>.py ...      # modelos verticales del folleto
      mh1_<nombre>.py ...      # modelos horizontales del folleto
  folleto.py                  # NUEVO: arma el PDF folleto personalizado
  motor.py                    # MODIFICAR: generar() itera el registro + color manual + PDF
  app.py                      # MODIFICAR: selector de color + "Generar catálogo"
docs/referencias-modelos/     # NUEVO: imágenes de referencia versionadas + INDICE.md
tests/
  test_plantillas_paquete.py  # NUEVO: registro, catalogo, render por modelo, no-recoloreo
  test_folleto.py             # NUEVO: armado del PDF
  test_motor_html.py          # MODIFICAR: ajustar a la nueva salida (catálogo + PDF)
```

---

## Task 1: Versionar referencias y catalogar el set exacto

**Files:**
- Create: `docs/referencias-modelos/` (copiar las 16 imágenes del folleto + el PDF)
- Create: `docs/referencias-modelos/INDICE.md`

**Interfaces:**
- Produces: nombres de archivo estables `v1.jpeg..v9.jpeg`, `h1.jpeg..h7.jpeg` y un mapeo clave→archivo→descripción que consumen las tareas de reproducción y el jurado de fidelidad.

- [ ] **Step 1: Copiar las referencias al repo**

Copiar desde `C:\Users\Diego\Desktop\mockups modelos\` al repo, renombrando con el mapeo del contact sheet (V1..V9, H1..H7) a `docs/referencias-modelos/v1.jpeg`..`v9.jpeg`, `h1.jpeg`..`h7.jpeg`, y el PDF como `folleto-muestras.pdf`.

```bash
# (ejecutar con rutas reales; renombrar según el mapeo V#/H# ya conocido)
mkdir -p docs/referencias-modelos
```

- [ ] **Step 2: Escribir el índice con el set exacto**

Crear `docs/referencias-modelos/INDICE.md` con una fila por modelo: `clave | archivo | orientación (V/H) | gesto gráfico | campos extra (sangre/codigo/web) | ¿es reverso?`. Marcar V9 (reverso Medical) como NO-modelo. Resultado: lista definitiva de claves de modelos frontales a reproducir (~15) + las 3 existentes.

- [ ] **Step 3: Commit**

```bash
git add docs/referencias-modelos/
git commit -m "docs: referencias de modelos + índice del catálogo"
```

---

## Task 2: Refactor `plantillas.py` → paquete `plantillas/` (sin cambiar comportamiento)

**Files:**
- Create: `codigo/plantillas/__init__.py`, `codigo/plantillas/base.py`, `codigo/plantillas/registro.py`, `codigo/plantillas/modelos/__init__.py`, `codigo/plantillas/modelos/{clasica,gafete,premium}.py`
- Delete: `codigo/plantillas.py` (su contenido se reparte)
- Test: `tests/test_plantillas_paquete.py`

**Interfaces:**
- Produces:
  - `base.py`: `css_base() -> str`, `construir_contexto(logo, prim, sec, cliente) -> dict`, `_shell(ctx, clase, css, cuerpo, ancho, alto) -> str`, `_root(ctx) -> str`, `_icono(nombre, color, tam, sw) -> str`, `variante_de(cliente, n=3) -> int`, utilidades `_b64_img/_b64_file/_rgb/_ajustar/_nombre2`, constantes `H=(1011,638)`, `V=(638,1011)`, `MG=60`, `ORO`, `DATOS`.
  - `registro.py`: `registrar(clave, nombre, orientacion, frontal, reverso=None, campos=()) -> None`; `_MODELOS: dict[str, Modelo]` (orden de inserción); `catalogo() -> list[Modelo]`; `cara(estilo, lado, ctx) -> (html, ancho, alto)`. `Modelo` es un objeto simple con atributos `.clave, .nombre, .orientacion ('V'|'H'), .frontal, .reverso, .campos`.
  - `__init__.py` re-exporta: `cara, construir_contexto, css_base, variante_de, catalogo, registrar`.
- Consumes: `motor.py` funciones `web_cliente, luminancia, marca_legible, pseudo_qr, distancia, saturacion` (igual que hoy, import diferido dentro de `construir_contexto`).

- [ ] **Step 1: Escribir el test del paquete (falla primero)**

```python
# tests/test_plantillas_paquete.py
import os, sys
CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
sys.path.insert(0, CODIGO)
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")

def _ctx():
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank")

def test_api_publica_se_conserva():
    import plantillas
    for nombre in ("cara", "construir_contexto", "css_base", "variante_de", "catalogo"):
        assert hasattr(plantillas, nombre), nombre

def test_tres_estilos_originales_registrados():
    from plantillas import catalogo
    claves = {m.clave for m in catalogo()}
    assert {"clasica", "gafete", "premium"} <= claves

def test_cara_originales_dimensionadas():
    from plantillas import cara
    ctx = _ctx()
    for estilo in ("clasica", "gafete", "premium"):
        for lado in ("frontal", "reverso"):
            html, w, h = cara(estilo, lado, ctx)
            assert "class='card" in html and ctx["prim_css"] in html
            assert (w, h) in [(1011, 638), (638, 1011)]
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_plantillas_paquete.py -v`
Expected: FAIL (paquete `plantillas` aún no existe / no expone `catalogo`).

- [ ] **Step 3: Crear `base.py`** moviendo de `plantillas.py` TAL CUAL: imports, constantes (`DATOS, ORO, H, V, MG`), `variante_de`, utilidades de imagen/color, iconos (`_ICON_PATHS, _icono`), foto demo (`_silueta_uri, _foto_uri`), `construir_contexto`, `css_base`, `_root`, `_shell`. Sin cambios de lógica.

- [ ] **Step 4: Crear `registro.py`**

```python
# codigo/plantillas/registro.py
class Modelo:
    def __init__(self, clave, nombre, orientacion, frontal, reverso=None, campos=()):
        self.clave, self.nombre, self.orientacion = clave, nombre, orientacion
        self.frontal, self.reverso, self.campos = frontal, reverso, campos

_MODELOS = {}

def registrar(clave, nombre, orientacion, frontal, reverso=None, campos=()):
    _MODELOS[clave] = Modelo(clave, nombre, orientacion, frontal, reverso, campos)

def catalogo():
    return list(_MODELOS.values())

def cara(estilo, lado, ctx):
    m = _MODELOS[estilo]
    fn = m.frontal if lado == "frontal" else (m.reverso or m.frontal)
    return fn(lado, ctx, ctx["datos"])
```

- [ ] **Step 5: Crear `modelos/clasica.py`, `gafete.py`, `premium.py`** con el CSS y la función de cada uno (movidos de `plantillas.py` tal cual), y al final de cada módulo `registrar(...)`. Ejemplo de cierre:

```python
# al final de modelos/clasica.py
from plantillas.registro import registrar
registrar("clasica", "Clásica", "H", _clasica)
```

- [ ] **Step 6: Crear `modelos/__init__.py`** que importe los 3 módulos para poblar el registro:

```python
from . import clasica, gafete, premium  # noqa: F401
```

- [ ] **Step 7: Crear `plantillas/__init__.py`**

```python
from plantillas.base import (construir_contexto, css_base, variante_de,
                             DATOS, ORO, H, V, MG)
from plantillas.registro import registrar, catalogo, cara
from plantillas import modelos  # noqa: F401  (puebla el registro al importar)
```

- [ ] **Step 8: Borrar `codigo/plantillas.py`**

- [ ] **Step 9: Correr toda la suite**

Run: `python -m pytest tests/ -v`
Expected: PASS — `test_plantillas_paquete.py` verde y `test_motor_html.py` SIGUE verde (no se rompió la API).

- [ ] **Step 10: Commit**

```bash
git add codigo/plantillas tests/test_plantillas_paquete.py
git rm codigo/plantillas.py
git commit -m "refactor: plantillas.py -> paquete plantillas/ con registro central"
```

---

## Task 3: Extender datos de muestra con campos extra

**Files:**
- Modify: `codigo/plantillas/base.py` (constante `DATOS`)
- Test: `tests/test_plantillas_paquete.py`

**Interfaces:**
- Produces: `DATOS` con claves nuevas `tipo_sangre` ("O+"), `codigo` ("10052"). `web` se sigue tomando de `ctx["web"]` (ya existe vía `web_cliente`). Los modelos leen estos campos solo si los usan.

- [ ] **Step 1: Test (falla primero)**

```python
def test_datos_demo_tienen_campos_extra():
    from plantillas import DATOS
    assert DATOS["tipo_sangre"] == "O+"
    assert DATOS["codigo"] == "10052"
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_plantillas_paquete.py::test_datos_demo_tienen_campos_extra -v`
Expected: FAIL (KeyError).

- [ ] **Step 3: Implementar** — en `base.py`:

```python
DATOS = {"nombre": "Carlos González M.", "cargo": "Supervisor de Operaciones",
         "id": "45678123", "tipo_sangre": "O+", "codigo": "10052"}
```

- [ ] **Step 4: Correr y verificar PASS**

Run: `python -m pytest tests/test_plantillas_paquete.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add codigo/plantillas/base.py tests/test_plantillas_paquete.py
git commit -m "feat: datos demo con tipo de sangre y codigo"
```

---

## Task 4: Reproducir el PRIMER modelo (patrón de referencia) + validación visual

> **Naturaleza de las tareas de modelo:** el CSS final se produce mirando la imagen de
> referencia e iterando (render → mirar → ajustar) hasta lograr fidelidad. El plan fija el
> ANDAMIAJE concreto (módulo, registro, tests estructurales) que es idéntico para todos los
> modelos; la fidelidad gráfica se valida con el gate visual + jurado, no con un assert.

**Files:**
- Create: `codigo/plantillas/modelos/mv1_<nombre>.py` (modelo vertical, gesto "esquinas diagonales", referencia `docs/referencias-modelos/v4.jpeg` estilo Action)
- Modify: `codigo/plantillas/modelos/__init__.py` (importar el nuevo módulo)
- Test: `tests/test_plantillas_paquete.py`

**Interfaces:**
- Consumes: `base._shell, _root, css_base, _icono, construir_contexto`, `registro.registrar`.
- Produces: modelo registrado con `clave="mv1"`, `orientacion="V"`, función `frontal(lado, ctx, d)` que devuelve `(_shell(...), V[0], V[1])`.

- [ ] **Step 1: Test estructural del modelo (falla primero)**

```python
def test_mv1_registrado_y_render():
    from plantillas import cara, catalogo
    ctx = _ctx()
    assert any(m.clave == "mv1" for m in catalogo())
    html, w, h = cara("mv1", "frontal", ctx)
    assert (w, h) == (638, 1011)              # vertical CR80
    assert ctx["logo_uri"] in html            # logo del cliente presente
    assert ctx["prim_css"] in html            # color de marca aplicado
    assert "brightness(0)" not in html and "invert(" not in html  # regla fija
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_plantillas_paquete.py::test_mv1_registrado_y_render -v`
Expected: FAIL (clave `mv1` no existe).

- [ ] **Step 3: Crear el módulo del modelo** con este andamiaje (el CSS interno se llena reproduciendo la referencia):

```python
# codigo/plantillas/modelos/mv1_accion.py
from plantillas.base import _shell, _icono, V
from plantillas.registro import registrar

_CSS = """
.mv1{background:#fff}
/* … reproducir el gesto de la referencia v4: esquinas diagonales --oscuro arriba/abajo,
   logo arriba, foto 4:5 con borde --acc, nombre, cargo, banda inferior de cargo … */
"""

def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='safe'>"
        "<div class='logohdr'><img src='%s'></div>"
        "<img class='foto' src='%s'>"
        "<div class='name'>%s</div>"
        "<div class='role'>%s</div>"
        "<div class='dni'><span class='lb'>DNI:</span> %s</div>"
        "</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"], d["id"]))
    return _shell(ctx, "mv1", _CSS, cuerpo, *V), V[0], V[1]

registrar("mv1", "Acción (vertical)", "V", _frontal)
```

- [ ] **Step 4: Importarlo en `modelos/__init__.py`**

```python
from . import clasica, gafete, premium, mv1_accion  # noqa: F401
```

- [ ] **Step 5: Correr el test estructural**

Run: `python -m pytest tests/test_plantillas_paquete.py::test_mv1_registrado_y_render -v`
Expected: PASS.

- [ ] **Step 6: GATE VISUAL — renderizar y MIRAR vs la referencia**

Renderizar el frente con un logo real y comparar lado a lado con `docs/referencias-modelos/v4.jpeg`:

```bash
python -c "import sys; sys.path.insert(0,'codigo'); from motor import cargar_logo; from plantillas import cara, construir_contexto; from render import render_caras; l=cargar_logo('recursos/logo-disecod-oscuro.png'); ctx=construir_contexto(l,(20,80,160),(0,40,90),'Acme'); html,w,h=cara('mv1','frontal',ctx); render_caras([(html,w,h)])[0].save('salida/_proto/mv1.png')"
```

Mirar `salida/_proto/mv1.png`. Iterar CSS (Step 3) hasta que el gesto, proporciones y jerarquía coincidan con la referencia. Un jurado (subagente fresco) puntúa fidelidad 0-10 vs `v4.jpeg`; objetivo ≥ 8.

- [ ] **Step 7: Commit**

```bash
git add codigo/plantillas/modelos/mv1_accion.py codigo/plantillas/modelos/__init__.py tests/test_plantillas_paquete.py
git commit -m "feat: modelo mv1 (Accion vertical) reproducido"
```

---

## Task 5: Reproducir 2 modelos más → set de validación Fase 1 (GATE con Diego)

**Files:**
- Create: `codigo/plantillas/modelos/mh1_<nombre>.py` (horizontal con banda de cargo, ref `h1.jpeg` Digital World)
- Create: `codigo/plantillas/modelos/mh2_<nombre>.py` (horizontal con CAMPO EXTRA tipo de sangre, ref `h2.jpeg` Heartfit)
- Modify: `codigo/plantillas/modelos/__init__.py`
- Test: `tests/test_plantillas_paquete.py`

**Interfaces:**
- Produces: modelos `mh1` (orientacion "H", `(1011,638)`) y `mh2` (orientacion "H", `campos=("tipo_sangre",)`).

- [ ] **Step 1: Tests estructurales (fallan primero)**

```python
def test_mh1_y_mh2_horizontales():
    from plantillas import cara, catalogo
    ctx = _ctx()
    claves = {m.clave for m in catalogo()}
    assert {"mh1", "mh2"} <= claves
    for clave in ("mh1", "mh2"):
        html, w, h = cara(clave, "frontal", ctx)
        assert (w, h) == (1011, 638)
        assert ctx["logo_uri"] in html and ctx["prim_css"] in html

def test_mh2_muestra_tipo_de_sangre():
    from plantillas import cara, DATOS
    ctx = _ctx()
    html, _, _ = cara("mh2", "frontal", ctx)
    assert DATOS["tipo_sangre"] in html
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `python -m pytest tests/test_plantillas_paquete.py -k "mh1 or mh2" -v`
Expected: FAIL.

- [ ] **Step 3: Crear `mh1_*.py` y `mh2_*.py`** con el mismo andamiaje del Task 4 (CSS `.mh1{...}` / `.mh2{...}` reproduciendo `h1.jpeg` y `h2.jpeg`; `mh2` incluye un bloque que muestra `d["tipo_sangre"]` con label "G.S."). Registrar con `orientacion="H"`; `mh2` con `campos=("tipo_sangre",)`. Importarlos en `modelos/__init__.py`.

- [ ] **Step 4: Correr tests**

Run: `python -m pytest tests/test_plantillas_paquete.py -k "mh1 or mh2" -v`
Expected: PASS.

- [ ] **Step 5: GATE VISUAL + APROBACIÓN DE DIEGO**

Renderizar `mv1`, `mh1`, `mh2` con 2-3 logos reales (incluido el logo del cliente que mandó el vendedor) y componer una hoja comparativa contra las referencias. Mostrar a Diego. **No avanzar a Task 6 hasta que Diego apruebe la fidelidad del método.** Si pide ajustes, iterar el CSS de estos 3 modelos primero.

- [ ] **Step 6: Commit**

```bash
git add codigo/plantillas/modelos/mh1_*.py codigo/plantillas/modelos/mh2_*.py codigo/plantillas/modelos/__init__.py tests/test_plantillas_paquete.py
git commit -m "feat: modelos mh1, mh2 (set de validacion Fase 1)"
```

---

## Task 6: Reproducir los modelos restantes del folleto

**Files:**
- Create: un módulo por modelo restante en `codigo/plantillas/modelos/` (claves provisionales; confirmar set en Task 1):
  - Verticales: `mv2` (banda sup + foto circular, ref v2), `mv3` (banda azul nombre, ref v3), `mv4` (onda inferior colorida, ref v5/Tech), `mv5` (banda marrón minimalista, ref v6/Rosmino), `mv6` (marco rojo médico, ref v7), `mv7` (ondas naranja/celeste, ref v8/Infinitecon), `mv8` (esquinas amarillo/celeste, ref v1/Böka)
  - Horizontales: `mh3` (barras diag + código de barras + CÓDIGO, ref h3/Digitalist), `mh4` (onda azul + foto circular, ref h4/Gaio), `mh5` (banda naranja + DNI pill, ref h5/Podcast), `mh6` (foto derecha grande + esquina roja/negra, ref h6/Rosestore), `mh7` (esquina negra circular, ref h7/Vegetata)
- Modify: `codigo/plantillas/modelos/__init__.py`
- Test: `tests/test_plantillas_paquete.py`

**Interfaces:**
- Produces: ~12 modelos más registrados. `mh3` usa `campos=("codigo",)`.

- [ ] **Step 1: Test paramétrico de catálogo (falla primero)**

```python
ESPERADOS = ["clasica","gafete","premium",
             "mv1","mv2","mv3","mv4","mv5","mv6","mv7","mv8",
             "mh1","mh2","mh3","mh4","mh5","mh6","mh7"]

def test_catalogo_completo_render_y_dimensiones():
    from plantillas import cara, catalogo
    ctx = _ctx()
    claves = [m.clave for m in catalogo()]
    for c in ESPERADOS:
        assert c in claves, c
    for m in catalogo():
        html, w, h = cara(m.clave, "frontal", ctx)
        esperado = (1011, 638) if m.orientacion == "H" else (638, 1011)
        assert (w, h) == esperado, (m.clave, w, h)
        assert ctx["logo_uri"] in html
        assert "brightness(0)" not in html and "invert(" not in html
```

> Ajustar `ESPERADOS` al set real confirmado en Task 1 (puede ser ±1 modelo).

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_plantillas_paquete.py::test_catalogo_completo_render_y_dimensiones -v`
Expected: FAIL (faltan claves).

- [ ] **Step 3: Crear cada módulo restante** siguiendo el andamiaje del Task 4 (CSS reproduciendo su referencia; registrar con su orientación; `mh3` con `campos=("codigo",)`). Importar todos en `modelos/__init__.py`.

> Recomendado para escalar con calidad: dispatch en paralelo (subagent-driven o Workflow), un agente por modelo, cada uno con su referencia, que itera render→mirar y un jurado puntúa fidelidad ≥ 8 vs la referencia. Cada modelo es self-contained (su propio archivo) → sin conflictos.

- [ ] **Step 4: Correr el test de catálogo + suite completa**

Run: `python -m pytest tests/ -v`
Expected: PASS (todas las claves presentes, dimensiones correctas, regla fija respetada).

- [ ] **Step 5: GATE VISUAL** — hoja de contacto de los ~18 frentes con un logo real; mirar que ninguno esté roto/feo. Iterar los que flojeen.

- [ ] **Step 6: Commit**

```bash
git add codigo/plantillas/modelos/ tests/test_plantillas_paquete.py
git commit -m "feat: catalogo completo de modelos del folleto reproducidos"
```

---

## Task 7: Módulo `folleto.py` — armado del PDF personalizado

**Files:**
- Create: `codigo/folleto.py`
- Test: `tests/test_folleto.py`

**Interfaces:**
- Consumes: PIL.Image de cada frente ya renderizado + metadata del catálogo.
- Produces: `armar_pdf(cliente: str, logo_img: PIL.Image, items: list[tuple[str, str, PIL.Image]], ruta_pdf: str) -> int` donde cada item es `(nombre_modelo, orientacion 'V'|'H', imagen_frente)`. Compone portada + páginas de verticales + páginas de horizontales + pie, guarda PDF multipágina y **devuelve el número de páginas**.

- [ ] **Step 1: Test (falla primero)**

```python
# tests/test_folleto.py
import os, sys, tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
from PIL import Image

def test_armar_pdf_genera_archivo_y_paginas():
    from folleto import armar_pdf
    logo = Image.new("RGBA", (300, 120), (0, 120, 200, 255))
    items = ([("Modelo V%d" % i, "V", Image.new("RGB", (638, 1011), (240, 240, 240))) for i in range(4)] +
             [("Modelo H%d" % i, "H", Image.new("RGB", (1011, 638), (235, 235, 235))) for i in range(3)])
    pdf = os.path.join(tempfile.mkdtemp(prefix="t_foll_"), "cat.pdf")
    n = armar_pdf("Acme S.A.C.", logo, items, pdf)
    assert os.path.exists(pdf) and os.path.getsize(pdf) > 1000
    assert n >= 3  # portada + verticales + horizontales (al menos)
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_folleto.py -v`
Expected: FAIL (módulo `folleto` no existe).

- [ ] **Step 3: Implementar `folleto.py`** — componer páginas como imágenes RGB (lienzo ~1240×1754, "A4" a 150 dpi) y guardar PDF multipágina con PIL:

```python
# codigo/folleto.py
import os
from PIL import Image, ImageDraw, ImageFont

RUTA = os.path.dirname(os.path.abspath(__file__))
PAG = (1240, 1754)            # A4 vertical a ~150 dpi
MARGEN = 70
TINTA = (40, 40, 40)

def _fuente(tam, bold=False):
    nombre = "inter-semibold.ttf" if bold else "inter.ttf"
    try:
        return ImageFont.truetype(os.path.join(RUTA, nombre), tam)
    except Exception:
        return ImageFont.load_default()

def _portada(cliente, logo_img):
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    d.rectangle([30, 30, PAG[0]-30, PAG[1]-30], outline=(0, 120, 200), width=4)
    # logo del cliente centrado arriba
    lg = logo_img.convert("RGBA"); lg.thumbnail((520, 300))
    pag.paste(lg, ((PAG[0]-lg.width)//2, 240), lg)
    titulo = "Propuesta de credenciales"
    sub = "para %s" % cliente
    f1, f2, f3 = _fuente(56, True), _fuente(40), _fuente(28)
    for txt, f, y in ((titulo, f1, 620), (sub, f2, 700)):
        w = d.textlength(txt, font=f); d.text(((PAG[0]-w)//2, y), txt, font=f, fill=TINTA)
    pie = "DISECOD · www.fotochecks.pe"
    w = d.textlength(pie, font=f3); d.text(((PAG[0]-w)//2, PAG[1]-110), pie, font=f3, fill=(120,120,120))
    return pag

def _grid(items, cols, titulo):
    paginas = []
    f_t, f_l = _fuente(34, True), _fuente(22)
    # área útil
    ax, ay = MARGEN, MARGEN + 70
    cw = (PAG[0] - 2*MARGEN) // cols
    # alto de celda según primera orientación
    cell_h = int(cw * 0.92) if items and items[0][1] == "H" else int(cw * 1.45)
    rows = max(1, (PAG[1] - ay - MARGEN) // (cell_h + 50))
    por_pag = cols * rows
    for p in range(0, len(items), por_pag):
        pag = Image.new("RGB", PAG, "white"); d = ImageDraw.Draw(pag)
        d.text((MARGEN, MARGEN), titulo, font=f_t, fill=TINTA)
        for i, (nombre, _o, img) in enumerate(items[p:p+por_pag]):
            r, c = divmod(i, cols)
            x = ax + c*cw; y = ay + r*(cell_h+50)
            th = img.copy(); th.thumbnail((cw-30, cell_h-30))
            pag.paste(th, (x + (cw-th.width)//2, y))
            lw = d.textlength(nombre, font=f_l)
            d.text((x + (cw-lw)//2, y + cell_h - 16), nombre, font=f_l, fill=(90,90,90))
        paginas.append(pag)
    return paginas

def armar_pdf(cliente, logo_img, items, ruta_pdf):
    verticales = [it for it in items if it[1] == "V"]
    horizontales = [it for it in items if it[1] == "H"]
    paginas = [_portada(cliente, logo_img)]
    paginas += _grid(verticales, 3, "Modelos verticales")
    paginas += _grid(horizontales, 2, "Modelos horizontales")
    os.makedirs(os.path.dirname(ruta_pdf), exist_ok=True)
    paginas[0].save(ruta_pdf, save_all=True, append_images=paginas[1:], resolution=150.0)
    return len(paginas)
```

- [ ] **Step 4: Correr y verificar PASS**

Run: `python -m pytest tests/test_folleto.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add codigo/folleto.py tests/test_folleto.py
git commit -m "feat: armado del PDF folleto personalizado"
```

---

## Task 8: Cablear `motor.generar` al catálogo + color manual + PDF

**Files:**
- Modify: `codigo/motor.py` (`generar`, ~líneas 1196-1256)
- Test: `tests/test_motor_html.py`

**Interfaces:**
- Produces: `generar(ruta_logo, cliente, carpeta_salida=None, color=None) -> (carpeta, rutas)`. Con `color` (hex `"#RRGGBB"` o tupla RGB) se usa como `prim` en vez de `paleta_del_logo`; `sec` se deriva (`_ajustar(prim, 0.6)`). Genera el PDF `catalogo-<cliente>.pdf` (1ª ruta) e itera SOLO frentes del catálogo para `para-diseno/`.

- [ ] **Step 1: Reescribir los tests end-to-end (fallan primero)** — reemplazar `test_generar_produce_brief_y_3_direcciones` y `test_robustez_nombre_largo`:

```python
def test_generar_produce_pdf_catalogo():
    from motor import generar
    out = tempfile.mkdtemp(prefix="t_gen_")
    carpeta, rutas = generar(LOGO_DISECOD, "Interbank", out)
    assert any(r.lower().endswith(".pdf") for r in rutas), rutas
    pdf = [r for r in rutas if r.lower().endswith(".pdf")][0]
    assert os.path.getsize(pdf) > 1000
    # para-diseno tiene al menos un frente por modelo del catálogo
    from plantillas import catalogo
    diseno = glob.glob(os.path.join(carpeta, "para-diseno", "*.png"))
    assert len(diseno) >= len(catalogo())

def test_color_manual_se_respeta():
    from motor import generar
    out = tempfile.mkdtemp(prefix="t_col_")
    carpeta, rutas = generar(LOGO_DISECOD, "Acme", out, color="#cc2222")
    assert any(r.lower().endswith(".pdf") for r in rutas)
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `python -m pytest tests/test_motor_html.py -k "pdf or color_manual" -v`
Expected: FAIL.

- [ ] **Step 3: Implementar** — en `generar`:
  1. Añadir parámetro `color=None`. Si viene, `prim = _hex_a_rgb(color)` (helper nuevo en motor) o la tupla; `sec = tuple(int(x*0.6) for x in prim)`. Si no, `prim, sec = paleta_del_logo(logo)` (como hoy).
  2. Construir `ctx` igual.
  3. Iterar `from plantillas import catalogo, cara`; para cada `m in catalogo()` armar `cara(m.clave, "frontal", ctx)` → `items_render`.
  4. `caras = render_caras(items_render)`; bajar a CR80 por orientación.
  5. Guardar cada frente limpio en `para-diseno/` (`<clave>-frontal.png`).
  6. Construir `items_folleto = [(m.nombre, m.orientacion, frente_cr80) ...]` y `from folleto import armar_pdf`; `pdf = os.path.join(carpeta_salida, f"catalogo-{slug(cliente)}.pdf")`; `armar_pdf(cliente, logo, items_folleto, pdf)`.
  7. `rutas = [pdf] + rutas_para_diseno`.

```python
def _hex_a_rgb(c):
    if isinstance(c, (tuple, list)): return tuple(int(x) for x in c[:3])
    c = c.lstrip("#"); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
```

- [ ] **Step 4: Correr la suite completa**

Run: `python -m pytest tests/ -v`
Expected: PASS (incluye `test_logo_cliente_no_se_recolorea`, `test_color_se_adapta_al_logo`).

- [ ] **Step 5: GATE VISUAL** — `python codigo/motor.py recursos/logo-disecod-oscuro.png "Acme S.A.C."`; abrir el PDF y revisar portada + grids.

- [ ] **Step 6: Commit**

```bash
git add codigo/motor.py tests/test_motor_html.py
git commit -m "feat: generar() arma el catalogo completo en PDF + color manual"
```

---

## Task 9: GUI — selector de color + "Generar catálogo"

**Files:**
- Modify: `codigo/app.py`

**Interfaces:**
- Consumes: `motor.generar(ruta_logo, cliente, color=None)`.
- Produces: GUI con botón "Cambiar color…" (`tkinter.colorchooser.askcolor`) que guarda `self.color` (hex o None) y lo pasa a `generar`. Botón principal "Generar catálogo".

- [ ] **Step 1: Implementar en `app.py`:**
  1. `from tkinter import colorchooser`.
  2. Estado `self.color = None`. Fila nueva: botón "Cambiar color…" + muestra del color (un `tk.Label` con `bg`). `elegir_color()` llama `colorchooser.askcolor(title="Elige el color")`; si devuelve, `self.color = hex; actualizar muestra`. Texto auxiliar: "Por defecto usa el color del logo".
  3. Cambiar textos: botón "Generar catálogo", subtítulo "Logo del cliente → catálogo de modelos con su marca".
  4. En `_trabajo`: `motor.generar(self.ruta_logo, cliente, color=self.color)`.
  5. `_listo`: "¡Listo! Se abrió la carpeta con el catálogo. ✓".

> Sin test unitario (tkinter es GUI). Validación: lanzar la app, generar con color del logo y con color manual.

- [ ] **Step 2: GATE VISUAL** — `python codigo/app.py`: probar logo + nombre + color automático y luego "Cambiar color…"; confirmar que el PDF cambia de color.

- [ ] **Step 3: Commit**

```bash
git add codigo/app.py
git commit -m "feat: GUI con selector de color y catalogo"
```

---

## Task 10: Publicar (auto-update del vendedor)

**Files:**
- Modify: `codigo/version.txt`, `publicar.py` (lista `ARCHIVOS`), `manifest.json` (lo regenera `publicar.py`)

**Interfaces:**
- Produces: nuevo `version.txt` + `manifest.json` con TODOS los archivos nuevos del paquete `plantillas/` y `folleto.py`, publicados a GitHub raw.

- [ ] **Step 1: Verificar que `publicar.py` lista archivos nuevos** — `ARCHIVOS` debe incluir `folleto.py` y los archivos del paquete `plantillas/` (rutas planas o con subcarpeta, según cómo el launcher reparte). Si el launcher solo soporta nombres planos, adaptar `ARCHIVOS`/launcher para subcarpetas del paquete, o empaquetar `plantillas/` en el manifest con sus rutas relativas.

> **Verificación previa obligatoria:** revisar `launcher.py` y `publicar.py` para confirmar si el auto-update soporta subcarpetas (`plantillas/...`). Si NO, esta tarea incluye extender el launcher para crear subdirectorios al descargar. Esto es un riesgo conocido (el sistema actual usa "nombres planos").

- [ ] **Step 2: Correr la suite completa una última vez**

Run: `python -m pytest tests/ -v`
Expected: PASS (todo verde).

- [ ] **Step 3: Subir versión y publicar** (cuando Diego apruebe y pida publicar):

```bash
python publicar.py
```

- [ ] **Step 4: Commit** (lo hace `publicar.py`, o):

```bash
git add codigo/version.txt manifest.json publicar.py
git commit -m "release: catalogo de modelos personalizable"
```

---

## Self-Review

**Spec coverage:** D1 (Parte A, Parte B fuera)→alcance del plan; D2 (catálogo completo)→Task 8; D3 (color auto+manual)→Task 8/9; D4 (validar 2-3)→Task 4/5 gate; D5 (Camino 1 HTML/CSS)→Task 4-6; D6 (PDF)→Task 7/8; D7 (solo frentes)→Task 8 (itera "frontal"); D8 (mantener 3 viejas)→Task 2; D9 (datos demo + extra)→Task 3; D10 (portada personalizada)→Task 7 `_portada`. Reglas fijas→Global Constraints + tests no-recoloreo en Task 4/6. Auto-update→Task 10. Referencias→Task 1.

**Placeholder scan:** El CSS de cada modelo se completa reproduciendo su referencia (naturaleza visual declarada explícitamente en Task 4); el andamiaje, tests y comandos son concretos. `ESPERADOS`/claves se ajustan al set real de Task 1 (nota incluida). Sin TBD/TODO sueltos.

**Type consistency:** `cara(estilo, lado, ctx)`, `catalogo() -> [Modelo(.clave,.nombre,.orientacion,.frontal,.reverso,.campos)]`, `registrar(clave,nombre,orientacion,frontal,reverso,campos)`, `construir_contexto(logo,prim,sec,cliente)`, `armar_pdf(cliente,logo_img,items,ruta_pdf)->int`, `generar(ruta_logo,cliente,carpeta_salida=None,color=None)` — usados consistentemente entre tareas. Orientaciones 'V'/'H' y dimensiones (1011,638)=H / (638,1011)=V coherentes en Tasks 4-8.
