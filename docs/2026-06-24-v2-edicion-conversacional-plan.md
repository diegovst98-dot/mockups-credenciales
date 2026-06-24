# Plan de implementación — v2: Edición conversacional (Parte B)

> **For agentic workers:** REQUIRED SUB-SKILL: usa `superpowers:subagent-driven-development` (recomendado)
> o `superpowers:executing-plans` para implementar este plan tarea por tarea. Los pasos usan
> casillas (`- [ ]`) para seguimiento.

**Goal:** Agregar una pestaña "Personalizar" a Mockups DISECOD donde el vendedor retoca **un modelo
elegido** por chat (parser local, gratis) + controles, ve el preview en vivo y exporta el boceto (PDF/PNG).

**Architecture:** Un dict `Ajustes` es la única fuente de verdad de la edición. El chat
(`asistente.interpretar`) y los controles producen `cambios` que se fusionan en `Ajustes`
(`estado.aplicar_cambios`). `motor.render_modelo(logo, cliente, ajustes)` renderiza **un frente** del
modelo con sus ajustes aplicados (reusa `construir_contexto` + `cara` + `render_caras` de la Parte A).
La GUI re-renderiza el preview desde `Ajustes` en un hilo. `color/textos/cambiar-modelo` funcionan para
los 18 modelos sin tocar cada archivo; `campos`/`logo_pos` los declara cada modelo (D7 del spec).

**Tech Stack:** Python 3.12, Pillow (PIL), tkinter (ttk.Notebook + ImageTk), render HTML→PNG vía Edge
headless (`render.py`), pytest. Sin red, sin APIs de pago.

**Spec de referencia:** [docs/2026-06-23-v2-edicion-conversacional-design.md](2026-06-23-v2-edicion-conversacional-design.md)

## Global Constraints

Aplican a **todas** las tareas (verbatim del spec y de `CLAUDE.md`):

- **Español peruano** en toda la UI, mensajes del chat y textos. (`CLAUDE.md`)
- **El logo del cliente NUNCA se recolorea** — prohibido `brightness(0)`/`invert(`/duotono/teñido del
  logo. Los tests verifican que el HTML no contenga `brightness(0)` ni `invert(`. (regla fija del proyecto)
- **Parser 100% offline, determinista, gratis.** Nada de IA con costo; la firma `interpretar(...)` queda
  enchufable a futuro, pero hoy no llama a ninguna red.
- **No romper la Parte A (catálogo).** `construir_contexto(..., ajustes=None)` debe dar un contexto
  **idéntico** al actual. Los tests existentes (`tests/test_plantillas_paquete.py`, `tests/test_folleto.py`,
  `tests/test_motor_html.py`, `tests/test_renombrador.py`) deben seguir verdes.
- **Tests con pytest.** Cada archivo de test agrega `codigo/` al `sys.path` con
  `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))`.
  Logo de prueba: `recursos/logo-disecod-oscuro.png`.
- **Cambio del `.exe`** (esta v2 agrega el forced-import `PIL.ImageTk` al `launcher.py`) →
  **reconstruir el zip COMPLETO** (`dist\FotochecksEditor`/`dist\codigo` entera) en la carpeta `dist\` del
  proyecto, **NO** un update-zip en el Escritorio. (lección de build, `mockups-credenciales.md`)
- **Publicar** = subir `version.txt`, regenerar `manifest.json`, commit + push (`publicar.py`). Los
  archivos planos nuevos de `codigo/` (`estado.py`, `asistente.py`) hay que **agregarlos a `ARCHIVOS`**
  en `publicar.py` (el glob solo cubre `plantillas/**/*.py` y los `fondo-*.jpg`).
- **Render desde hilo**: el preview re-renderiza en un hilo daemon; reusar el `render.py` endurecido de la
  Parte A (stdin redirigido, `CREATE_NO_WINDOW`, 3 reintentos). No tocar `render.py`.

**Capacidades por modelo en v1 (YAGNI):** solo **2 modelos** declaran campos/posiciones de logo —
`clasica` (H) y `mv7` (V). Para el resto, el asistente **sugiere** uno compatible. `color`, `textos` y
`cambiar de modelo` ya funcionan para los 18 tras la Fase 1. Ampliar a más modelos es mecánico (misma
receta) y queda fuera de v1.

---

## Fase 1 — Núcleo (sin GUI)

### Task 1: Estado de edición (`estado.py`)

**Files:**
- Create: `codigo/estado.py`
- Test: `tests/test_estado.py`

**Interfaces:**
- Produces:
  - `CAMPOS_VALIDOS = ("tipo_sangre", "codigo", "web")`
  - `LOGO_POSICIONES = ("default", "izq", "centro", "der")`
  - `ajustes_inicial(modelo_clave: str) -> dict` con llaves `modelo, color, campos, textos, logo_pos`
  - `aplicar_cambios(ajustes: dict, cambios: dict) -> dict` (copia; deep-merge en `campos`/`textos`,
    reemplazo en `modelo`/`color`/`logo_pos`)

- [ ] **Step 1: Escribir el test que falla**

Create `tests/test_estado.py`:

```python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))


def test_ajustes_inicial_tiene_llaves_y_defaults():
    from estado import ajustes_inicial
    a = ajustes_inicial("clasica")
    assert a["modelo"] == "clasica"
    assert a["color"] is None
    assert a["campos"] == {} and a["textos"] == {}
    assert a["logo_pos"] == "default"


def test_aplicar_cambios_no_muta_el_original():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("clasica")
    b = aplicar_cambios(a, {"color": "#1f7a3d"})
    assert a["color"] is None          # original intacto
    assert b["color"] == "#1f7a3d"


def test_aplicar_cambios_fusiona_campos_y_textos():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("clasica")
    a = aplicar_cambios(a, {"campos": {"tipo_sangre": True}})
    a = aplicar_cambios(a, {"campos": {"codigo": True}})
    a = aplicar_cambios(a, {"textos": {"nombre": "Juan Pérez"}})
    assert a["campos"] == {"tipo_sangre": True, "codigo": True}   # fusiona, no reemplaza
    assert a["textos"] == {"nombre": "Juan Pérez"}


def test_aplicar_cambios_vacio_es_idempotente():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("mv7")
    assert aplicar_cambios(a, {}) == a
    assert aplicar_cambios(a, None) == a
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_estado.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estado'`.

- [ ] **Step 3: Implementar `estado.py`**

Create `codigo/estado.py`:

```python
# -*- coding: utf-8 -*-
"""Estado de edición de la pestaña Personalizar (v2). 'Ajustes' es un dict simple,
única fuente de verdad: el chat y los controles lo mutan, y el preview se
re-renderiza desde él. Funciones puras y testeables; sin GUI, sin red."""
from copy import deepcopy

# Campos opcionales que un modelo puede prender/apagar (sus valores demo viven en DATOS).
CAMPOS_VALIDOS = ("tipo_sangre", "codigo", "web")

# Posiciones preset de logo (cada modelo declara cuáles soporta).
LOGO_POSICIONES = ("default", "izq", "centro", "der")


def ajustes_inicial(modelo_clave):
    """Ajustes por defecto para un modelo recién elegido."""
    return {
        "modelo": modelo_clave,
        "color": None,        # None = automático del logo; "#RRGGBB" = manual
        "campos": {},         # {campo: True/False} — solo los que el modelo soporta
        "textos": {},         # overrides de los textos demo (nombre/cargo/id/empresa)
        "logo_pos": "default",
    }


def aplicar_cambios(ajustes, cambios):
    """Devuelve una COPIA de 'ajustes' con 'cambios' fusionados: deep-merge en
    'campos' y 'textos'; reemplazo directo en 'modelo', 'color', 'logo_pos'."""
    nuevo = deepcopy(ajustes)
    for clave, valor in (cambios or {}).items():
        if clave in ("campos", "textos") and isinstance(valor, dict):
            nuevo.setdefault(clave, {}).update(valor)
        else:
            nuevo[clave] = valor
    return nuevo
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `python -m pytest tests/test_estado.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add codigo/estado.py tests/test_estado.py
git commit -m "feat(v2): estado de edicion Ajustes + helpers puros"
```

---

### Task 2: Capacidades por modelo (`registro.py`)

**Files:**
- Modify: `codigo/plantillas/registro.py`
- Test: `tests/test_registro_capacidades.py`

**Interfaces:**
- Consumes: `Modelo`, `registrar`, `catalogo` (Task previa / Parte A).
- Produces:
  - `Modelo` con atributos nuevos `campos_opcionales: tuple`, `logo_posiciones: tuple`
  - `registrar(clave, nombre, orientacion, frontal, reverso=None, campos=(), campos_opcionales=(), logo_posiciones=())`
  - `modelos_con_campo(campo: str) -> list[Modelo]`
  - `modelos_con_logo_pos(pos: str) -> list[Modelo]`

- [ ] **Step 1: Escribir el test que falla**

Create `tests/test_registro_capacidades.py`:

```python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))


def test_modelo_tiene_capacidades_por_defecto_vacias():
    from plantillas.registro import Modelo
    m = Modelo("x", "X", "H", lambda lado, ctx, d: ("", 1, 1))
    assert m.campos_opcionales == ()
    assert m.logo_posiciones == ()


def test_registrar_acepta_capacidades():
    from plantillas import catalogo
    import plantillas  # noqa: F401  (puebla el registro)
    clasica = next(m for m in catalogo() if m.clave == "clasica")
    # se declaran en la Fase 2; aquí solo verificamos el canal (atributos existen)
    assert isinstance(clasica.campos_opcionales, tuple)
    assert isinstance(clasica.logo_posiciones, tuple)


def test_buscar_por_capacidad():
    from plantillas.registro import registrar, modelos_con_campo, modelos_con_logo_pos
    registrar("cap_test", "Cap Test", "H", lambda lado, ctx, d: ("", 1, 1),
              campos_opcionales=("tipo_sangre",), logo_posiciones=("der",))
    assert any(m.clave == "cap_test" for m in modelos_con_campo("tipo_sangre"))
    assert any(m.clave == "cap_test" for m in modelos_con_logo_pos("der"))
    assert all("tipo_sangre" in m.campos_opcionales for m in modelos_con_campo("tipo_sangre"))
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_registro_capacidades.py -v`
Expected: FAIL con `AttributeError: 'Modelo' object has no attribute 'campos_opcionales'`.

- [ ] **Step 3: Modificar `registro.py`**

Replace the entire content of `codigo/plantillas/registro.py` with:

```python
# -*- coding: utf-8 -*-
"""Registro central de modelos de credencial. Cada módulo de plantillas.modelos
llama a registrar() al importarse; motor.py consume catalogo() para iterar el folleto.
v2: cada modelo declara qué campos opcionales y qué posiciones de logo soporta, para
que el editor ofrezca solo lo posible y el asistente sugiera otro modelo cuando no."""


class Modelo:
    def __init__(self, clave, nombre, orientacion, frontal, reverso=None, campos=(),
                 campos_opcionales=(), logo_posiciones=()):
        self.clave = clave
        self.nombre = nombre
        self.orientacion = orientacion      # 'V' (638x1011) o 'H' (1011x638)
        self.frontal = frontal              # fn(lado, ctx, d) -> (html, ancho, alto)
        self.reverso = reverso              # opcional; si None, cara() cae al frontal
        self.campos = tuple(campos)         # datos extra que muestra (legacy, sin uso v1)
        self.campos_opcionales = tuple(campos_opcionales)   # v2: campos que prende/apaga
        self.logo_posiciones = tuple(logo_posiciones)       # v2: presets de logo que soporta


_MODELOS = {}


def registrar(clave, nombre, orientacion, frontal, reverso=None, campos=(),
              campos_opcionales=(), logo_posiciones=()):
    _MODELOS[clave] = Modelo(clave, nombre, orientacion, frontal, reverso, campos,
                             campos_opcionales, logo_posiciones)


def catalogo():
    """Lista de modelos en orden de registro."""
    return list(_MODELOS.values())


def modelos_con_campo(campo):
    """Modelos cuyo 'campos_opcionales' incluye 'campo' (para sugerencias del asistente)."""
    return [m for m in _MODELOS.values() if campo in m.campos_opcionales]


def modelos_con_logo_pos(pos):
    """Modelos cuyo 'logo_posiciones' incluye 'pos' (para sugerencias del asistente)."""
    return [m for m in _MODELOS.values() if pos in m.logo_posiciones]


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto). estilo = clave registrada; lado in {frontal, reverso}."""
    m = _MODELOS[estilo]
    fn = m.frontal if lado == "frontal" else (m.reverso or m.frontal)
    return fn(lado, ctx, ctx["datos"])
```

- [ ] **Step 4: Correr los tests (nuevo + regresión del paquete) y verificar que pasan**

Run: `python -m pytest tests/test_registro_capacidades.py tests/test_plantillas_paquete.py -v`
Expected: PASS (todos). La API pública y los 18 modelos siguen registrándose igual.

- [ ] **Step 5: Commit**

```bash
git add codigo/plantillas/registro.py tests/test_registro_capacidades.py
git commit -m "feat(v2): Modelo declara campos_opcionales/logo_posiciones + busqueda por capacidad"
```

---

### Task 3: `construir_contexto` aplica los ajustes (`base.py`)

**Files:**
- Modify: `codigo/plantillas/base.py:116-141` (función `construir_contexto`)
- Test: `tests/test_contexto_ajustes.py`

**Interfaces:**
- Consumes: `DATOS`, helpers de `motor` (igual que hoy).
- Produces: `construir_contexto(logo, prim, sec, cliente, ajustes=None) -> dict`. El `ctx` ahora **siempre**
  trae `ctx["campos"]` (dict) y `ctx["logo_pos"]` (str). Con `ajustes=None` el contexto es equivalente al
  actual (más esas 2 llaves con default `{}` / `"default"`, que los modelos viejos ignoran). `textos.empresa`
  (si viene) sobreescribe el nombre de empresa mostrado (`ctx["cliente"]`, `web`, `monograma`).

- [ ] **Step 1: Escribir el test que falla**

Create `tests/test_contexto_ajustes.py`:

```python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _logo():
    from motor import cargar_logo
    return cargar_logo(LOGO)


def test_sin_ajustes_es_compatible():
    from plantillas import construir_contexto
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank")
    assert ctx["datos"]["nombre"] == "Carlos González M."   # DATOS demo intacto
    assert ctx["campos"] == {}                              # default v2
    assert ctx["logo_pos"] == "default"
    assert ctx["cliente"] == "Interbank"


def test_textos_override_no_muta_DATOS_global():
    from plantillas import construir_contexto, DATOS
    ajustes = {"textos": {"nombre": "Juan Pérez", "cargo": "Gerente"}}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["datos"]["nombre"] == "Juan Pérez"
    assert ctx["datos"]["cargo"] == "Gerente"
    assert ctx["datos"]["id"] == DATOS["id"]                # lo no override se conserva
    assert DATOS["nombre"] == "Carlos González M."          # el global NO se tocó


def test_empresa_override_cambia_cliente_y_web():
    from plantillas import construir_contexto
    ajustes = {"textos": {"empresa": "Acme SAC"}}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["cliente"] == "Acme SAC"
    assert "acme" in ctx["web"]


def test_campos_y_logo_pos_pasan_al_contexto():
    from plantillas import construir_contexto
    ajustes = {"campos": {"tipo_sangre": True}, "logo_pos": "der"}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["campos"] == {"tipo_sangre": True}
    assert ctx["logo_pos"] == "der"
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_contexto_ajustes.py -v`
Expected: FAIL — `test_campos_y_logo_pos_pasan_al_contexto` y `test_empresa_override...` fallan con
`KeyError: 'campos'` / `assert 'Interbank' == 'Acme SAC'`.

- [ ] **Step 3: Reemplazar `construir_contexto` en `base.py`**

In `codigo/plantillas/base.py`, replace the function `construir_contexto` (lines 116-141) with:

```python
def construir_contexto(logo, prim, sec, cliente, ajustes=None):
    from motor import web_cliente, luminancia, marca_legible, pseudo_qr, distancia, saturacion
    ajustes = ajustes or {}
    textos = ajustes.get("textos", {})
    # 'empresa' override cambia el nombre mostrado (y, por coherencia, web y monograma)
    empresa = (textos.get("empresa") or cliente)
    oscuro = luminancia(prim) < 0.45
    # color secundario de la marca como ACENTO que "puntua" (5-10%): solo si es
    # realmente distinto y con color; si no, cae al oro. Regla: un color manda, otro puntua.
    sec_distinta = distancia(prim, sec) > 70 and saturacion(sec) > 0.18
    acc2 = marca_legible(sec) if sec_distinta else None
    # textos demo con overrides del usuario (copia: NO muta el DATOS global)
    datos = dict(DATOS)
    datos.update({k: v for k, v in textos.items() if v and k in DATOS})
    return {
        "_prim": tuple(int(x) for x in prim[:3]),
        "logo_uri": _b64_img(logo),
        "foto_uri": _foto_uri(prim),
        "qr_uri": _b64_img(pseudo_qr(empresa, 360)),
        "prim_css": _rgb(prim),
        "medio_css": _rgb(_ajustar(prim, 0.58)),
        "oscuro_css": _rgb(_ajustar(prim, 0.22)),
        "claro_css": _rgb(_ajustar(prim, 1.7)),
        "prim_legible": _rgb(marca_legible(prim)),
        "acc2_css": _rgb(acc2) if acc2 else ORO,
        "txt_sobre_prim": "#ffffff" if oscuro else "#1d1f24",
        "logo_oscuro": oscuro,
        "variante": variante_de(empresa),
        "cliente": empresa,
        "monograma": ("".join(w[0] for w in (empresa or "").split()[:2]).upper() or "•"),
        "web": web_cliente(empresa),
        "datos": datos,
        # --- v2: ajustes que cada modelo lee si los soporta ---
        "campos": dict(ajustes.get("campos", {})),
        "logo_pos": ajustes.get("logo_pos", "default"),
    }
```

> Nota: `datos.update(... if k in DATOS)` ignora la llave `empresa` (no está en `DATOS`); la empresa se
> maneja arriba vía `ctx["cliente"]`. Así los modelos siguen leyendo `d["nombre"]/d["cargo"]/d["id"]` y
> `ctx["cliente"]` como hoy.

- [ ] **Step 4: Correr los tests (nuevo + regresión) y verificar que pasan**

Run: `python -m pytest tests/test_contexto_ajustes.py tests/test_plantillas_paquete.py tests/test_motor_html.py -v`
Expected: PASS (todos). La Parte A (catálogo) no cambia de comportamiento.

- [ ] **Step 5: Commit**

```bash
git add codigo/plantillas/base.py tests/test_contexto_ajustes.py
git commit -m "feat(v2): construir_contexto aplica textos/campos/logo_pos (ajustes=None compatible)"
```

---

### Task 4: Parser local de intención (`asistente.py`)

**Files:**
- Create: `codigo/asistente.py`
- Test: `tests/test_asistente.py`

**Interfaces:**
- Consumes: `plantillas.registro.modelos_con_campo`, `modelos_con_logo_pos`, `plantillas.catalogo` (Task 2);
  `Modelo` (objeto del modelo actual, para leer `campos_opcionales`/`logo_posiciones`).
- Produces: `interpretar(texto: str, ajustes: dict, modelo: Modelo) -> (cambios: dict, mensaje: str)`.
  `cambios` se fusiona con `estado.aplicar_cambios`; `{}` si no aplica nada. `mensaje` siempre es texto en
  español para el chat.

- [ ] **Step 1: Escribir el test que falla**

Create `tests/test_asistente.py`:

```python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))


class _ModeloFake:
    def __init__(self, clave="x", nombre="X", campos_opcionales=(), logo_posiciones=()):
        self.clave = clave
        self.nombre = nombre
        self.campos_opcionales = campos_opcionales
        self.logo_posiciones = logo_posiciones


def _aj(modelo="clasica", color=None):
    from estado import ajustes_inicial
    a = ajustes_inicial(modelo)
    a["color"] = color
    return a


def test_color_nombrado():
    from asistente import interpretar
    cambios, msg = interpretar("ponle color azul", _aj(), _ModeloFake())
    assert cambios == {"color": "#1f4ed8"}
    assert "azul" in msg.lower()


def test_color_hex_directo():
    from asistente import interpretar
    cambios, _ = interpretar("usa el color #0a66c2", _aj(), _ModeloFake())
    assert cambios == {"color": "#0a66c2"}


def test_mas_oscuro_requiere_color_base():
    from asistente import interpretar
    cambios, msg = interpretar("hazlo más oscuro", _aj(color=None), _ModeloFake())
    assert cambios == {}
    assert "color" in msg.lower()


def test_mas_oscuro_con_base():
    from asistente import interpretar
    cambios, _ = interpretar("más oscuro", _aj(color="#3366cc"), _ModeloFake())
    assert cambios["color"].startswith("#") and cambios["color"] != "#3366cc"


def test_campo_soportado_se_prende():
    from asistente import interpretar
    m = _ModeloFake(campos_opcionales=("tipo_sangre",))
    cambios, msg = interpretar("agrégale el tipo de sangre", _aj(), m)
    assert cambios == {"campos": {"tipo_sangre": True}}


def test_campo_soportado_se_quita():
    from asistente import interpretar
    m = _ModeloFake(campos_opcionales=("tipo_sangre",))
    cambios, _ = interpretar("quita el tipo de sangre", _aj(), m)
    assert cambios == {"campos": {"tipo_sangre": False}}


def test_campo_no_soportado_sugiere_modelo_real():
    # 'clasica' (catálogo real) soporta tipo_sangre tras la Fase 2; el modelo actual no.
    from asistente import interpretar
    import plantillas  # noqa: F401  (puebla el registro)
    m = _ModeloFake(clave="premium", nombre="Premium", campos_opcionales=())
    cambios, msg = interpretar("ponle tipo de sangre", _aj("premium"), m)
    assert cambios == {}
    assert "modelo" in msg.lower()        # sugiere cambiar de modelo


def test_logo_a_la_derecha_soportado():
    from asistente import interpretar
    m = _ModeloFake(logo_posiciones=("default", "der"))
    cambios, _ = interpretar("el logo ponlo a la derecha", _aj(), m)
    assert cambios == {"logo_pos": "der"}


def test_logo_pos_no_soportada_no_falla():
    from asistente import interpretar
    m = _ModeloFake(logo_posiciones=("default",))
    cambios, msg = interpretar("logo a la izquierda", _aj(), m)
    assert cambios == {}
    assert msg                            # da un mensaje, no revienta


def test_cambiar_modelo_por_nombre():
    from asistente import interpretar
    import plantillas  # noqa: F401
    m = _ModeloFake(clave="premium", nombre="Premium")
    cambios, _ = interpretar("usa el modelo clasica", _aj("premium"), m)
    assert cambios == {"modelo": "clasica"}


def test_no_entiende_da_ayuda():
    from asistente import interpretar
    cambios, msg = interpretar("xyzzy qwerty", _aj(), _ModeloFake())
    assert cambios == {}
    assert "controles" in msg.lower() or "prueba" in msg.lower()


def test_texto_override_cargo():
    from asistente import interpretar
    cambios, _ = interpretar("cambia el cargo a Gerente de Ventas", _aj(), _ModeloFake())
    assert cambios == {"textos": {"cargo": "Gerente De Ventas"}}
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_asistente.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'asistente'`.

- [ ] **Step 3: Implementar `asistente.py`**

Create `codigo/asistente.py`:

```python
# -*- coding: utf-8 -*-
"""Parser local de intención para la pestaña Personalizar (v2). Convierte lo que
escribe el vendedor en 'cambios' para el dict Ajustes. 100% offline, determinista,
gratis. La firma queda lista para, a futuro, delegar el parseo a un LLM detrás de la
misma interfaz, sin tocar el resto del sistema.

interpretar(texto, ajustes, modelo) -> (cambios, mensaje)
  cambios: dict para fusionar en Ajustes (vacío si no aplica nada)
  mensaje: respuesta en español para mostrar en el chat
"""
import re
import unicodedata

# colores nombrados frecuentes -> hex
_COLORES = {
    "azul": "#1f4ed8", "celeste": "#2563eb", "rojo": "#c81e1e", "verde": "#1f7a3d",
    "negro": "#222222", "dorado": "#c9a14a", "naranja": "#d2691e", "morado": "#6b46c1",
    "lila": "#9987f7", "gris": "#4b5563", "rosado": "#db2777", "rosa": "#db2777",
    "amarillo": "#d4a017", "turquesa": "#0d9488", "guinda": "#7a1f3d", "vino": "#7a1f3d",
}

# campo -> frases que lo activan (se buscan dentro del texto normalizado con espacios)
_CAMPOS_SINONIMOS = {
    "tipo_sangre": ("tipo de sangre", "grupo sanguineo", "factor rh"),
    "codigo": ("codigo de empleado", "codigo", "n de empleado", "numero de empleado"),
    "web": ("pagina web", "sitio web", "la web", "url", "dominio"),
}
_CAMPO_LABEL = {"tipo_sangre": "el tipo de sangre", "codigo": "el código", "web": "la web"}

_QUITAR = ("quita", "quitar", "saca", "sacar", " sin ", "elimina", "borra", "no pongas", "remueve")

_POS_SINONIMOS = {
    "der": ("a la derecha", "derecha"),
    "izq": ("a la izquierda", "izquierda"),
    "centro": ("al centro", "centrado", "al medio", "en el centro"),
}
_POS_LABEL = {"der": "a la derecha", "izq": "a la izquierda", "centro": "al centro",
              "default": "a su sitio"}

# textos editables: campo de Ajustes/DATOS -> sinónimos en el habla
_TEXTO_CAMPOS = (
    ("nombre", ("nombre",)),
    ("cargo", ("cargo", "puesto")),
    ("id", ("dni", "documento")),
    ("empresa", ("empresa", "razon social")),
)
_TEXTO_LABEL = {"nombre": "el nombre", "cargo": "el cargo", "id": "el DNI", "empresa": "la empresa"}


def _norm(texto):
    """minúsculas, sin acentos, con un espacio de borde para matchear palabras."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return " " + re.sub(r"\s+", " ", t).strip() + " "


def _ajustar_hex(hexv, factor):
    c = hexv.lstrip("#")
    rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    if factor <= 1:
        rgb = [int(x * factor) for x in rgb]
    else:
        rgb = [int(x + (255 - x) * (factor - 1)) for x in rgb]
    return "#%02x%02x%02x" % tuple(max(0, min(255, x)) for x in rgb)


def _texto_override(t):
    """Captura '<campo> ... <conector> <valor>'. Best-effort; los controles son el respaldo."""
    for campo, syns in _TEXTO_CAMPOS:
        for s in syns:
            m = re.search(r"\b%s\b.*?(?:que diga|sea|es|a|:|=)\s+(.+)$" % re.escape(s), t)
            if m:
                valor = m.group(1).strip().strip(".").strip()
                if valor and len(valor) <= 60:
                    return campo, valor.title()
    return None


def interpretar(texto, ajustes, modelo):
    from plantillas.registro import modelos_con_campo, modelos_con_logo_pos
    t = _norm(texto)
    quitar = any(k in t for k in _QUITAR)
    pos_pedida = next((p for p, syns in _POS_SINONIMOS.items() if any(s in t for s in syns)), None)

    # 1) POSICIÓN DEL LOGO ("el logo a la derecha", "ponlo a la derecha")
    if pos_pedida and ("logo" in t or "ponlo" in t or "muev" in t or " pon " in t):
        if pos_pedida in getattr(modelo, "logo_posiciones", ()):
            return {"logo_pos": pos_pedida}, "Listo, moví el logo %s." % _POS_LABEL[pos_pedida]
        otros = [m for m in modelos_con_logo_pos(pos_pedida) if m.clave != modelo.clave]
        if otros:
            return {}, ("Este modelo no permite mover el logo ahí. El modelo «%s» sí — "
                        "escribe «usa el modelo %s»." % (otros[0].nombre, otros[0].clave))
        return {}, "Este modelo mantiene el logo en su sitio. Puedes probar otro modelo."

    # 2) CAMPO opcional (tipo de sangre / código / web)
    for campo, syns in _CAMPOS_SINONIMOS.items():
        if any(s in t for s in syns):
            encender = not quitar
            if campo in getattr(modelo, "campos_opcionales", ()):
                verbo = "agregué" if encender else "quité"
                return {"campos": {campo: encender}}, "Listo, %s %s." % (verbo, _CAMPO_LABEL[campo])
            if encender:
                otros = [m for m in modelos_con_campo(campo) if m.clave != modelo.clave]
                if otros:
                    return {}, ("Este modelo no tiene espacio para %s. El modelo «%s» sí — "
                                "escribe «usa el modelo %s» para cambiarlo."
                                % (_CAMPO_LABEL[campo], otros[0].nombre, otros[0].clave))
                return {}, "Ningún modelo del catálogo muestra %s en el frente." % _CAMPO_LABEL[campo]
            return {}, "Ese dato no está en este modelo; no hay nada que quitar."

    # 3) COLOR (nombrado, hex, más oscuro/claro)
    m = re.search(r"#([0-9a-f]{6})", t)
    if m:
        return {"color": "#" + m.group(1)}, "Listo, apliqué el color #%s." % m.group(1)
    for nombre, hexv in _COLORES.items():
        if (" " + nombre + " ") in t:
            return {"color": hexv}, "Listo, cambié el color a %s." % nombre
    if "mas oscuro" in t or "oscurece" in t or "mas fuerte" in t:
        base = ajustes.get("color")
        if not base:
            return {}, "Primero dime un color (ej. «azul») y luego lo oscurezco."
        return {"color": _ajustar_hex(base, 0.8)}, "Listo, lo oscurecí un poco."
    if "mas claro" in t or "aclara" in t or "mas suave" in t:
        base = ajustes.get("color")
        if not base:
            return {}, "Primero dime un color (ej. «azul») y luego lo aclaro."
        return {"color": _ajustar_hex(base, 1.25)}, "Listo, lo aclaré un poco."

    # 4) CAMBIAR DE MODELO (por clave o por nombre)
    if "modelo" in t or "diseno" in t or "otro" in t:
        from plantillas import catalogo
        for mdl in catalogo():
            if (" " + mdl.clave + " ") in t or _norm(mdl.nombre).strip() in t:
                return {"modelo": mdl.clave}, "Listo, cambié al modelo «%s»." % mdl.nombre
        if "otro" in t or "modelo" in t:
            return {}, ("Dime cuál: por ejemplo «usa el modelo clasica». "
                        "También puedes elegirlo en el selector de arriba.")

    # 5) TEXTO override (nombre/cargo/DNI/empresa)
    cambio_txt = _texto_override(t)
    if cambio_txt:
        campo_txt, valor = cambio_txt
        return {"textos": {campo_txt: valor}}, "Listo, actualicé %s." % _TEXTO_LABEL[campo_txt]

    # 6) NADA
    return {}, ("No te entendí 🤔. Prueba con: «ponle tipo de sangre», «el logo a la derecha», "
                "«color azul», «cambia el cargo a Gerente» — o usa los controles de la derecha.")
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `python -m pytest tests/test_asistente.py -v`
Expected: PASS (12 tests).

> Si `test_campo_no_soportado_sugiere_modelo_real` o `test_cambiar_modelo_por_nombre` fallan porque
> `clasica` aún no declara `campos_opcionales`, es porque la Fase 2 va después. **Ese test depende de la
> Fase 2.** Para correr Task 4 aislada, esos dos casos pueden quedar `xfail` temporal; se vuelven verdes al
> cerrar Task 6. (Marcar con `@pytest.mark.xfail(reason="depende de Fase 2 Task 6")` y quitar el marcador en
> Task 6.)

- [ ] **Step 5: Commit**

```bash
git add codigo/asistente.py tests/test_asistente.py
git commit -m "feat(v2): parser local de intencion (color/campos/logo/modelo/texto) determinista"
```

---

### Task 5: Render de un modelo con ajustes + export (`motor.py`)

**Files:**
- Modify: `codigo/motor.py` (agregar `render_modelo` y `exportar_personalizado` cerca de `generar`, ~línea 1204)
- Test: `tests/test_render_modelo.py`

**Interfaces:**
- Consumes: `cargar_logo`, `paleta_del_logo`, `_hex_a_rgb`, `slug`, `CARD_W/H`, `V_W/H`, `render.render_caras`,
  `plantillas.construir_contexto`, `plantillas.cara`, `plantillas.catalogo`, `folleto.armar_pdf`.
- Produces:
  - `render_modelo(logo, cliente, ajustes) -> PIL.Image` — `logo` es la imagen YA cargada con
    `cargar_logo()`; devuelve un frente a tamaño CR80 (300 dpi).
  - `exportar_personalizado(logo, cliente, ajustes, carpeta_salida=None, pdf=True, png=True) -> (carpeta, [rutas])`

- [ ] **Step 1: Escribir el test que falla**

Create `tests/test_render_modelo.py`:

```python
# -*- coding: utf-8 -*-
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _hay_navegador():
    from render import _navegador_sistema
    return _navegador_sistema() is not None


requiere_edge = pytest.mark.skipif(not _hay_navegador(), reason="no hay Edge/Chrome para rasterizar")


@requiere_edge
def test_render_modelo_vertical_tamano_cr80():
    from motor import cargar_logo, render_modelo
    from estado import ajustes_inicial
    img = render_modelo(cargar_logo(LOGO), "Interbank", ajustes_inicial("mv7"))
    assert img.size == (638, 1011)        # vertical CR80 300 dpi


@requiere_edge
def test_render_modelo_horizontal_color_manual():
    from motor import cargar_logo, render_modelo
    from estado import ajustes_inicial, aplicar_cambios
    aj = aplicar_cambios(ajustes_inicial("clasica"), {"color": "#1f7a3d"})
    img = render_modelo(cargar_logo(LOGO), "Interbank", aj)
    assert img.size == (1011, 638)


@requiere_edge
def test_exportar_personalizado_crea_png_y_pdf(tmp_path):
    from motor import cargar_logo, exportar_personalizado
    from estado import ajustes_inicial
    carpeta, archivos = exportar_personalizado(
        cargar_logo(LOGO), "Interbank", ajustes_inicial("clasica"),
        carpeta_salida=str(tmp_path))
    assert any(a.endswith(".png") for a in archivos)
    assert any(a.endswith(".pdf") for a in archivos)
    for a in archivos:
        assert os.path.getsize(a) > 0
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_render_modelo.py -v`
Expected: FAIL con `ImportError: cannot import name 'render_modelo' from 'motor'` (o SKIP si la máquina no
tiene Edge — en la PC de desarrollo sí hay).

- [ ] **Step 3: Agregar `render_modelo` y `exportar_personalizado` a `motor.py`**

In `codigo/motor.py`, just **before** `def generar(` (línea ~1204), insert:

```python
def render_modelo(logo, cliente, ajustes):
    """Renderiza UN frente del modelo elegido con los ajustes aplicados y lo devuelve
    como PIL.Image a tamaño CR80 (300 dpi). 'logo' es la imagen YA cargada con
    cargar_logo(); 'ajustes' es el dict de estado.py. Alimenta el preview y el export."""
    from plantillas import cara, construir_contexto
    from render import render_caras
    ajustes = ajustes or {}
    color = ajustes.get("color")
    if color:
        prim = _hex_a_rgb(color)
        sec = tuple(int(x * 0.6) for x in prim)
    else:
        prim, sec = paleta_del_logo(logo)
    ctx = construir_contexto(logo, prim, sec, cliente, ajustes)
    html, w, h = cara(ajustes["modelo"], "frontal", ctx)
    img = render_caras([(html, w, h)])[0]
    destino = (CARD_W, CARD_H) if img.width > img.height else (V_W, V_H)
    return img.resize(destino, Image.LANCZOS)


def exportar_personalizado(logo, cliente, ajustes, carpeta_salida=None, pdf=True, png=True):
    """Renderiza el modelo elegido con sus ajustes y lo exporta como PNG y/o PDF
    (boceto de venta). Devuelve (carpeta, [rutas]). 'logo' ya viene de cargar_logo()."""
    from plantillas import catalogo
    from folleto import armar_pdf
    cliente = (cliente or "Cliente").strip() or "Cliente"
    img = render_modelo(logo, cliente, ajustes)
    modelo = next(m for m in catalogo() if m.clave == ajustes["modelo"])
    if carpeta_salida is None:
        carpeta_salida = os.path.join(RUTA_BASE, "salida", "%s-personalizado" % slug(cliente))
    os.makedirs(carpeta_salida, exist_ok=True)
    archivos = []
    base = "%s-%s" % (modelo.clave, slug(cliente))
    if png:
        rp = os.path.join(carpeta_salida, base + ".png")
        img.convert("RGB").save(rp, optimize=True)
        archivos.append(rp)
    if pdf:
        rpdf = os.path.join(carpeta_salida, "boceto-%s.pdf" % slug(cliente))
        armar_pdf(cliente, logo, [(modelo.nombre, modelo.orientacion, img)], rpdf)
        archivos.append(rpdf)
    return carpeta_salida, archivos
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `python -m pytest tests/test_render_modelo.py -v`
Expected: PASS (3 tests; rasteriza con Edge — tarda unos segundos).

- [ ] **Step 5: Commit**

```bash
git add codigo/motor.py tests/test_render_modelo.py
git commit -m "feat(v2): motor.render_modelo + exportar_personalizado (un frente con ajustes)"
```

---

## Fase 2 — Modelos (declaran capacidades y leen ajustes)

> Solo 2 modelos en v1 (YAGNI): `clasica` (H) y `mv7` (V). El resto sigue igual; el asistente sugiere uno de
> estos dos cuando el modelo actual no soporta un campo/posición.

### Task 6: Parametrizar `clasica` (campos + posición de logo)

**Files:**
- Modify: `codigo/plantillas/modelos/clasica.py` (función `_clasica` frontal + llamada `registrar`)
- Test: `tests/test_modelo_clasica_ajustes.py`

**Interfaces:**
- Consumes: `ctx["campos"]`, `ctx["logo_pos"]`, `d["tipo_sangre"]`, `d["codigo"]` (Task 3 los provee).
- Produces: `clasica` con `campos_opcionales=("tipo_sangre", "codigo")` y
  `logo_posiciones=("default", "izq", "der", "centro")`. Frente muestra/oculta las filas extra y mueve el logo.

- [ ] **Step 1: Escribir el test que falla**

Create `tests/test_modelo_clasica_ajustes.py`:

```python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _ctx(ajustes=None):
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)


def test_clasica_declara_capacidades():
    from plantillas import catalogo
    m = next(x for x in catalogo() if x.clave == "clasica")
    assert "tipo_sangre" in m.campos_opcionales
    assert "codigo" in m.campos_opcionales
    assert "der" in m.logo_posiciones


def test_clasica_sin_campos_no_muestra_extras():
    from plantillas import cara, DATOS
    html, _, _ = cara("clasica", "frontal", _ctx())
    assert DATOS["tipo_sangre"] not in html
    assert "Código" not in html and "Codigo" not in html


def test_clasica_con_tipo_sangre_lo_muestra():
    from plantillas import cara, DATOS
    html, _, _ = cara("clasica", "frontal", _ctx({"campos": {"tipo_sangre": True}}))
    assert DATOS["tipo_sangre"] in html


def test_clasica_con_codigo_lo_muestra():
    from plantillas import cara, DATOS
    html, _, _ = cara("clasica", "frontal", _ctx({"campos": {"codigo": True}}))
    assert DATOS["codigo"] in html


def test_clasica_logo_pos_der_cambia_alineacion():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"logo_pos": "der"}))
    assert "flex-end" in html


def test_clasica_no_recolorea_logo_con_ajustes():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"campos": {"tipo_sangre": True}, "logo_pos": "izq"}))
    assert "brightness(0)" not in html and "invert(" not in html
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_modelo_clasica_ajustes.py -v`
Expected: FAIL (`test_clasica_declara_capacidades` y los de campos/logo fallan).

- [ ] **Step 3: Modificar `clasica.py`**

Replace the function `_clasica` and the final `registrar(...)` call in
`codigo/plantillas/modelos/clasica.py` with:

```python
def _clasica(lado, ctx, d):
    if lado == "frontal":
        # filas base + opcionales según ctx["campos"] (iconos válidos de base._ICON_PATHS)
        filas = [
            ("edificio", "Empresa:", ctx["cliente"]),
            ("persona", "DNI:", d["id"]),
        ]
        if ctx["campos"].get("codigo"):
            filas.append(("maletin", "Código:", d["codigo"]))
        if ctx["campos"].get("tipo_sangre"):
            filas.append(("escudo", "T. Sangre:", d["tipo_sangre"]))
        rows_html = "".join(
            "<div class='row'><span class='ic'>%s</span>"
            "<span><span class='lb'>%s</span> %s</span></div>"
            % (_icono(ic, "#fff", 24), lb, val) for ic, lb, val in filas)
        # posición del logo en la cabecera
        pos = {"izq": "flex-start", "der": "flex-end", "centro": "center"}.get(
            ctx["logo_pos"], "center")
        cuerpo = (
            "<div class='wm'>%s</div>"
            "<div class='safe'>"
            "<div class='logohdr' style='justify-content:%s'><img src='%s'></div>"
            "<img class='foto' src='%s'>"
            "<div class='info'>"
            "<div class='name'>%s</div>"
            "<div class='role'>%s</div>"
            "<div class='rows'>%s</div>"
            "</div></div>"
            % (ctx["monograma"], pos, ctx["logo_uri"], ctx["foto_uri"],
               d["nombre"], d["cargo"], rows_html))
    else:
        cuerpo = (
            "<div class='bsafe'>"
            "<div class='oline'></div>"
            "<div class='scan'>Escanea para validar</div>"
            "<div class='qrbox'><img src='%s'></div>"
            "<div class='oline'></div>"
            "<div class='ptxt'>%s Credencial personal e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "<div class='vig'>%s Vigencia 2026 — 2027</div>"
            "</div>"
            % (ctx["qr_uri"], _icono("escudo", ctx["prim_legible"], 20),
               _icono("globo", ctx["prim_legible"], 20), ctx["web"],
               _icono("calendario", ctx["prim_legible"], 19)))
    return _shell(ctx, "clas", _CSS_CLASICA, cuerpo, *H), H[0], H[1]


registrar("clasica", "Clásica", "H", _clasica,
          campos_opcionales=("tipo_sangre", "codigo"),
          logo_posiciones=("default", "izq", "der", "centro"))
```

- [ ] **Step 4: Correr los tests (nuevo + asistente Fase 1 + paquete) y verificar que pasan**

Run: `python -m pytest tests/test_modelo_clasica_ajustes.py tests/test_asistente.py tests/test_plantillas_paquete.py -v`
Expected: PASS. Si en Task 4 marcaste `xfail` los 2 casos que dependían de `clasica`, **quítalos ahora** y
verifica que pasan en verde.

- [ ] **Step 5: Commit**

```bash
git add codigo/plantillas/modelos/clasica.py tests/test_modelo_clasica_ajustes.py tests/test_asistente.py
git commit -m "feat(v2): clasica declara tipo_sangre/codigo + posicion de logo y los lee del ctx"
```

---

### Task 7: Parametrizar `mv7` (Médico — tipo de sangre)

**Files:**
- Modify: `codigo/plantillas/modelos/mv7_medico.py` (función `_frontal` + `registrar`)
- Test: `tests/test_modelo_mv7_ajustes.py`

**Interfaces:**
- Consumes: `ctx["campos"]`, `d["tipo_sangre"]`.
- Produces: `mv7` con `campos_opcionales=("tipo_sangre",)`, `logo_posiciones=("default",)`. Muestra la línea
  de tipo de sangre cuando se prende.

- [ ] **Step 1: Escribir el test que falla**

Create `tests/test_modelo_mv7_ajustes.py`:

```python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _ctx(ajustes=None):
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)


def test_mv7_declara_tipo_sangre():
    from plantillas import catalogo
    m = next(x for x in catalogo() if x.clave == "mv7")
    assert "tipo_sangre" in m.campos_opcionales


def test_mv7_sin_campo_no_muestra_sangre():
    from plantillas import cara, DATOS
    html, _, _ = cara("mv7", "frontal", _ctx())
    assert DATOS["tipo_sangre"] not in html


def test_mv7_con_campo_muestra_sangre():
    from plantillas import cara, DATOS
    html, _, _ = cara("mv7", "frontal", _ctx({"campos": {"tipo_sangre": True}}))
    assert DATOS["tipo_sangre"] in html
    assert "brightness(0)" not in html and "invert(" not in html
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_modelo_mv7_ajustes.py -v`
Expected: FAIL (`test_mv7_declara_tipo_sangre` y `test_mv7_con_campo_muestra_sangre`).

- [ ] **Step 3: Modificar `mv7_medico.py`**

In `codigo/plantillas/modelos/mv7_medico.py`, replace `_frontal` and the final `registrar(...)` with:

```python
def _frontal(lado, ctx, d):
    extra = ""
    if ctx["campos"].get("tipo_sangre"):
        extra = "<div class='dni'>Tipo de sangre: %s</div>" % d["tipo_sangre"]
    cuerpo = (
        "<div class='topdark'></div><div class='topprim'></div>"
        "<div class='botdark'></div><div class='botprim'></div>"
        "<div class='safe'>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='name'>%s</div>"
        "<div class='dni'>DNI: %s</div>"
        "<div class='cargo'>%s</div>"
        "%s"
        "</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["id"], d["cargo"], extra))
    return _shell(ctx, "mv7", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv7", "Médico (vertical)", "V", _frontal,
          campos_opcionales=("tipo_sangre",),
          logo_posiciones=("default",))
```

- [ ] **Step 4: Correr todos los tests del núcleo y modelos**

Run: `python -m pytest tests/test_estado.py tests/test_registro_capacidades.py tests/test_contexto_ajustes.py tests/test_asistente.py tests/test_modelo_clasica_ajustes.py tests/test_modelo_mv7_ajustes.py tests/test_plantillas_paquete.py -v`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add codigo/plantillas/modelos/mv7_medico.py tests/test_modelo_mv7_ajustes.py
git commit -m "feat(v2): mv7 Medico declara y muestra tipo de sangre opcional"
```

---

## Fase 3 — GUI (pestaña "Personalizar")

> La GUI es **pegamento**: la lógica testeable (`estado`, `asistente`, `render_modelo`) ya está cubierta.
> Aquí se valida con (a) el **smoke** del `launcher` (que ahora debe ver 3 pestañas) y (b) **pasos manuales**
> con resultado esperado. Reglas: re-render en hilo daemon (patrón seguro del build); `ImageTk.PhotoImage`
> necesita una referencia viva para no ser recolectada.

### Task 8: Andamiaje de la pestaña Personalizar (inputs + selector + preview)

**Files:**
- Modify: `codigo/app.py` (agregar 3.ª pestaña al Notebook + método `_construir_personalizar`)
- Modify: `launcher.py:135-164` (`_smoke` ahora exige 3 pestañas incl. "Personalizar")

**Interfaces:**
- Consumes: `motor.render_modelo`, `motor.cargar_logo`, `plantillas.catalogo`, `estado.ajustes_inicial`,
  `PIL.ImageTk`.
- Produces: la pestaña con: elegir logo, nombre cliente, selector de modelo (combobox de los 18), área de
  preview (tk.Label con ImageTk), botón "Actualizar preview". Estado: `self.p_logo` (PIL),
  `self.p_logo_ruta`, `self.p_ajustes`.

- [ ] **Step 1: Agregar la 3.ª pestaña en `__init__` de `App`**

In `codigo/app.py`, after `nb.add(frame_renombrar, text="Renombrar Cotizaciones")` (línea 54), add:

```python
        frame_personalizar = tk.Frame(nb, bg=FONDO)
        nb.add(frame_personalizar, text="Personalizar")
```

And at the end of `__init__`, after `self._construir_renombrar(frame_renombrar)` (línea 103), add:

```python
        self._construir_personalizar(frame_personalizar)
```

- [ ] **Step 2: Importar ImageTk y estado/asistente arriba de `app.py`**

In `codigo/app.py`, after `import motor` (línea 14), add:

```python
import asistente
import estado
from PIL import Image, ImageTk
```

- [ ] **Step 3: Implementar `_construir_personalizar` (andamiaje) en `App`**

Add this method to `class App` in `codigo/app.py` (after `_renom_aplicar`, antes de `def main`):

```python
    # ------------------------------------------------------------------ #
    # Pestaña Personalizar (v2): editar UN modelo por chat + controles
    # ------------------------------------------------------------------ #

    def _construir_personalizar(self, panel):
        self.p_logo = None
        self.p_logo_ruta = None
        self._p_preview_img = None         # referencia viva del ImageTk
        self._p_gen = 0                    # contador de re-render (descarta renders viejos)
        self._modelos = motor_catalogo()   # [(clave, nombre)]
        self.p_ajustes = estado.ajustes_inicial(self._modelos[0][0])

        # --- barra superior: logo + cliente + modelo ---
        top = tk.Frame(panel, bg=FONDO)
        top.pack(fill="x", padx=16, pady=10)
        tk.Button(top, text="Elegir logo…", command=self._p_elegir_logo).pack(side="left")
        self.p_logo_lbl = tk.Label(top, text="(ningún logo)", bg=FONDO, fg="#999")
        self.p_logo_lbl.pack(side="left", padx=8)
        tk.Label(top, text="Empresa:", bg=FONDO, fg=GRIS).pack(side="left", padx=(12, 4))
        self.p_cliente = tk.Entry(top, width=18)
        self.p_cliente.pack(side="left")
        tk.Label(top, text="Modelo:", bg=FONDO, fg=GRIS).pack(side="left", padx=(12, 4))
        self.p_modelo_var = tk.StringVar(value=self._modelos[0][1])
        self.p_modelo_combo = ttk.Combobox(
            top, width=22, state="readonly", textvariable=self.p_modelo_var,
            values=[n for _c, n in self._modelos])
        self.p_modelo_combo.pack(side="left")
        self.p_modelo_combo.bind("<<ComboboxSelected>>", self._p_cambiar_modelo)

        # --- cuerpo: preview (izq) + panel chat/controles (der) ---
        cuerpo = tk.Frame(panel, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        izq = tk.Frame(cuerpo, bg="#F4F4F6", width=420)
        izq.pack(side="left", fill="both", expand=True)
        izq.pack_propagate(False)
        self.p_preview = tk.Label(izq, text="Elige un logo y dale «Actualizar preview».",
                                  bg="#F4F4F6", fg="#888")
        self.p_preview.pack(expand=True)

        der = tk.Frame(cuerpo, bg=FONDO, width=340)
        der.pack(side="right", fill="y")
        der.pack_propagate(False)
        self._p_panel_der = der
        self._p_construir_chat(der)
        self._p_controles = tk.Frame(der, bg=FONDO)
        self._p_controles.pack(fill="x", pady=(8, 0))
        self._p_rebuild_controles()

        # --- pie: actualizar + exportar (export se cablea en Task 10) ---
        pie = tk.Frame(panel, bg=FONDO)
        pie.pack(fill="x", padx=16, pady=(0, 12))
        tk.Button(pie, text="Actualizar preview", command=self._p_rerender,
                  bg=LILA, fg="white", relief="flat", padx=14, pady=6).pack(side="left")
        self.p_estado = tk.Label(pie, text="", bg=FONDO, fg="#555")
        self.p_estado.pack(side="left", padx=10)

    def _p_elegir_logo(self):
        ruta = filedialog.askopenfilename(
            title="Logo del cliente",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos", "*.*")])
        if ruta:
            self.p_logo_ruta = ruta
            self.p_logo = motor.cargar_logo(ruta)
            self.p_logo_lbl.config(text=os.path.basename(ruta), fg=GRIS)

    def _modelo_actual(self):
        from plantillas import catalogo
        clave = self.p_ajustes["modelo"]
        return next(m for m in catalogo() if m.clave == clave)

    def _p_cambiar_modelo(self, _evt=None):
        nombre = self.p_modelo_var.get()
        clave = next(c for c, n in self._modelos if n == nombre)
        # conserva color y textos; resetea campos/logo_pos (son por-modelo)
        nuevo = estado.ajustes_inicial(clave)
        nuevo["color"] = self.p_ajustes["color"]
        nuevo["textos"] = dict(self.p_ajustes["textos"])
        self.p_ajustes = nuevo
        self._p_rebuild_controles()
        self._p_rerender()
```

> `motor_catalogo()` es un helper local (Step 4) que devuelve `[(clave, nombre)]` sin exponer objetos
> `Modelo` a la GUI.

- [ ] **Step 4: Agregar el helper `motor_catalogo` en `app.py`**

In `codigo/app.py`, after the constants (`FONDO = "#FFFFFF"`, línea 19), add:

```python
def motor_catalogo():
    """[(clave, nombre)] de los modelos, para el selector — sin filtrar tipos a la GUI."""
    from plantillas import catalogo
    return [(m.clave, m.nombre) for m in catalogo()]
```

- [ ] **Step 5: Actualizar el smoke del `launcher` para exigir 3 pestañas**

In `launcher.py`, in `_smoke()` (línea ~160), replace the GUI assertion line:

```python
        lineas.append("GUI OK; pestanas=%s" % tabs)
```

with:

```python
        ok3 = "Personalizar" in tabs and len(tabs) == 3
        lineas.append("GUI %s; pestanas=%s" % ("OK" if ok3 else "FAIL(faltan pestanas)", tabs))
```

- [ ] **Step 6: Verificación (smoke + manual)**

The chat/controles/rerender methods land in Task 9 — so this step verifies only that the app **builds** with
3 tabs. First add temporary no-op stubs so `_construir_personalizar` runs (they get real bodies in Task 9):

```python
    def _p_construir_chat(self, panel):
        self.p_chat = tk.Text(panel, height=10, width=40, state="disabled", wrap="word")
        self.p_chat.pack(fill="x")
        self.p_entrada = tk.Entry(panel)
        self.p_entrada.pack(fill="x", pady=(4, 0))

    def _p_rebuild_controles(self):
        for w in self._p_controles.winfo_children():
            w.destroy()

    def _p_rerender(self):
        self.p_estado.config(text="(preview se cablea en la siguiente tarea)")
```

Run (desde la carpeta del proyecto, con el código fuente, NO el exe):

```bash
python -c "import sys; sys.path.insert(0,'codigo'); import app, tkinter as tk; r=tk.Tk(); r.withdraw(); app.App(r); import tkinter.ttk as ttk; nb=[w for w in r.winfo_children() if isinstance(w, ttk.Notebook)][0]; print([nb.tab(t,'text') for t in nb.tabs()]); r.destroy()"
```

Expected output: `['Mockups', 'Renombrar Cotizaciones', 'Personalizar']`

- [ ] **Step 7: Commit**

```bash
git add codigo/app.py launcher.py
git commit -m "feat(v2): andamiaje pestana Personalizar (inputs, selector, preview, smoke 3 pestanas)"
```

---

### Task 9: Cablear chat + controles → ajustes → re-render en vivo

**Files:**
- Modify: `codigo/app.py` (reemplazar los stubs `_p_construir_chat`, `_p_rebuild_controles`, `_p_rerender`
  por las versiones reales + agregar handlers)

**Interfaces:**
- Consumes: `asistente.interpretar`, `estado.aplicar_cambios`, `motor.render_modelo`, `ImageTk`.
- Produces: chat funcional (Enter envía), controles que reflejan/mutan `Ajustes`, preview que se re-renderiza
  en hilo a cada cambio.

- [ ] **Step 1: Reemplazar `_p_construir_chat` por la versión real**

In `codigo/app.py`, replace the stub `_p_construir_chat` with:

```python
    def _p_construir_chat(self, panel):
        tk.Label(panel, text="Pídeme un cambio:", bg=FONDO, fg=GRIS,
                 anchor="w").pack(fill="x")
        self.p_chat = tk.Text(panel, height=9, width=40, state="disabled", wrap="word",
                              bg="#FAFAFC", relief="solid", bd=1)
        self.p_chat.pack(fill="x")
        fila = tk.Frame(panel, bg=FONDO)
        fila.pack(fill="x", pady=(4, 0))
        self.p_entrada = tk.Entry(fila)
        self.p_entrada.pack(side="left", fill="x", expand=True)
        self.p_entrada.bind("<Return>", lambda _e: self._p_enviar())
        tk.Button(fila, text="Enviar", command=self._p_enviar).pack(side="left", padx=(4, 0))
        self._p_log_chat("Asistente",
                         "Hola 👋 Dime cosas como «ponle tipo de sangre», «el logo a la "
                         "derecha» o «color azul». También tienes los controles abajo.")

    def _p_log_chat(self, quien, texto):
        self.p_chat.config(state="normal")
        self.p_chat.insert("end", "%s: %s\n" % (quien, texto))
        self.p_chat.see("end")
        self.p_chat.config(state="disabled")

    def _p_enviar(self):
        texto = self.p_entrada.get().strip()
        if not texto:
            return
        self._p_log_chat("Tú", texto)
        cambios, mensaje = asistente.interpretar(texto, self.p_ajustes, self._modelo_actual())
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, cambios)
        self._p_log_chat("Asistente", mensaje)
        self.p_entrada.delete(0, "end")
        if cambios.get("modelo"):
            self.p_modelo_var.set(self._modelo_actual().nombre)
            self._p_rebuild_controles()
        elif cambios:
            self._p_sync_controles()
        if cambios:
            self._p_rerender()
```

- [ ] **Step 2: Reemplazar `_p_rebuild_controles` por la versión real**

```python
    def _p_rebuild_controles(self):
        for w in self._p_controles.winfo_children():
            w.destroy()
        m = self._modelo_actual()
        cont = self._p_controles

        # campos opcionales que el modelo soporta (checkbuttons)
        self._p_campo_vars = {}
        if m.campos_opcionales:
            tk.Label(cont, text="Campos:", bg=FONDO, fg=GRIS, anchor="w").pack(fill="x", pady=(6, 0))
            etiquetas = {"tipo_sangre": "Tipo de sangre", "codigo": "Código", "web": "Web"}
            for campo in m.campos_opcionales:
                var = tk.BooleanVar(value=bool(self.p_ajustes["campos"].get(campo)))
                self._p_campo_vars[campo] = var
                tk.Checkbutton(cont, text=etiquetas.get(campo, campo), variable=var, bg=FONDO,
                               command=lambda c=campo: self._p_toggle_campo(c)).pack(anchor="w")

        # posición del logo (radios) si el modelo soporta más de "default"
        if len(m.logo_posiciones) > 1:
            tk.Label(cont, text="Logo:", bg=FONDO, fg=GRIS, anchor="w").pack(fill="x", pady=(6, 0))
            self._p_logo_var = tk.StringVar(value=self.p_ajustes["logo_pos"])
            fila = tk.Frame(cont, bg=FONDO)
            fila.pack(anchor="w")
            txt = {"default": "Centro/def.", "izq": "Izquierda", "der": "Derecha", "centro": "Centro"}
            for pos in m.logo_posiciones:
                tk.Radiobutton(fila, text=txt.get(pos, pos), value=pos, variable=self._p_logo_var,
                               bg=FONDO, command=self._p_set_logo_pos).pack(side="left")

        # color
        filc = tk.Frame(cont, bg=FONDO)
        filc.pack(fill="x", pady=(8, 0))
        tk.Button(filc, text="Color…", command=self._p_elegir_color).pack(side="left")
        tk.Button(filc, text="Auto", command=self._p_color_auto).pack(side="left", padx=4)

        # textos
        tk.Label(cont, text="Textos:", bg=FONDO, fg=GRIS, anchor="w").pack(fill="x", pady=(8, 0))
        self._p_texto_entries = {}
        for campo, etiq in (("nombre", "Nombre"), ("cargo", "Cargo"), ("id", "DNI"),
                            ("empresa", "Empresa")):
            f = tk.Frame(cont, bg=FONDO)
            f.pack(fill="x")
            tk.Label(f, text=etiq, width=8, anchor="w", bg=FONDO, fg="#666").pack(side="left")
            e = tk.Entry(f)
            e.insert(0, self.p_ajustes["textos"].get(campo, ""))
            e.pack(side="left", fill="x", expand=True)
            e.bind("<Return>", lambda _e, c=campo: self._p_set_texto(c))
            self._p_texto_entries[campo] = e

    def _p_sync_controles(self):
        # refleja en los checkbuttons el estado actual (cuando el chat los cambió)
        for campo, var in getattr(self, "_p_campo_vars", {}).items():
            var.set(bool(self.p_ajustes["campos"].get(campo)))
        if hasattr(self, "_p_logo_var"):
            self._p_logo_var.set(self.p_ajustes["logo_pos"])

    def _p_toggle_campo(self, campo):
        val = self._p_campo_vars[campo].get()
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"campos": {campo: val}})
        self._p_rerender()

    def _p_set_logo_pos(self):
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"logo_pos": self._p_logo_var.get()})
        self._p_rerender()

    def _p_elegir_color(self):
        res = colorchooser.askcolor(title="Color del modelo", color=self.p_ajustes["color"] or "#1f7a3d")
        if res and res[1]:
            self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"color": res[1]})
            self._p_rerender()

    def _p_color_auto(self):
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"color": None})
        self._p_rerender()

    def _p_set_texto(self, campo):
        valor = self._p_texto_entries[campo].get().strip()
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"textos": {campo: valor}})
        self._p_rerender()
```

- [ ] **Step 3: Reemplazar `_p_rerender` por la versión real (render en hilo)**

```python
    def _p_rerender(self):
        if not self.p_logo:
            self.p_estado.config(text="Primero elige un logo.")
            return
        cliente = self.p_cliente.get().strip() or "Cliente"
        self._p_gen += 1
        gen = self._p_gen
        self.p_estado.config(text="Actualizando…")
        ajustes = estado.aplicar_cambios(self.p_ajustes, {})   # copia inmutable para el hilo

        def trabajo():
            try:
                img = motor.render_modelo(self.p_logo, cliente, ajustes)
                self.raiz.after(0, self._p_mostrar, gen, img)
            except Exception as e:
                self.raiz.after(0, self._p_error, str(e))

        threading.Thread(target=trabajo, daemon=True).start()

    def _p_mostrar(self, gen, img):
        if gen != self._p_gen:
            return                       # llegó un render viejo: descártalo
        disp = img.copy()
        disp.thumbnail((380, 560), Image.LANCZOS)
        self._p_preview_img = ImageTk.PhotoImage(disp)
        self.p_preview.config(image=self._p_preview_img, text="")
        self.p_estado.config(text="Listo ✓")

    def _p_error(self, msg):
        self.p_estado.config(text="")
        messagebox.showerror("No se pudo generar el preview", msg)
```

- [ ] **Step 4: Verificación manual (con código fuente)**

Run: `python codigo/app.py` (o `python -c "import sys; sys.path.insert(0,'codigo'); import app; app.main()"`)

Steps + expected:
1. Ir a la pestaña **Personalizar** → elegir un logo (ej. `recursos/logo-disecod-oscuro.png`), escribir
   "Interbank", dejar modelo "Clásica", **Actualizar preview** → aparece la tarjeta. ✓
2. En el chat escribir `ponle tipo de sangre` → el chat responde "Listo, agregué el tipo de sangre." y el
   preview muestra la fila **T. Sangre: O+**. El checkbutton "Tipo de sangre" queda marcado. ✓
3. Escribir `el logo a la derecha` → el logo se alinea a la derecha en la cabecera. ✓
4. Escribir `color azul` → el diseño cambia a azul (el logo del cliente **NO** cambia de color). ✓
5. Cambiar el selector a **Premium** y escribir `ponle tipo de sangre` → responde que Premium no tiene
   espacio y sugiere «Clásica» (no rompe). ✓

- [ ] **Step 5: Commit**

```bash
git add codigo/app.py
git commit -m "feat(v2): chat + controles cablean Ajustes y re-render en vivo del preview"
```

---

### Task 10: Exportar el modelo personalizado (PDF/PNG)

**Files:**
- Modify: `codigo/app.py` (botones de export en el pie + handler `_p_exportar`)

**Interfaces:**
- Consumes: `motor.exportar_personalizado`.
- Produces: botones "Exportar PDF" y "Exportar PNG" en el pie de la pestaña; abren la carpeta con el archivo.

- [ ] **Step 1: Agregar los botones de export en el pie**

In `_construir_personalizar`, in the `pie` frame (Task 8 Step 3), after the `Actualizar preview` button, add:

```python
        tk.Button(pie, text="Exportar PDF", command=lambda: self._p_exportar("pdf"),
                  bg="#EEEAFE", fg=GRIS, relief="flat", padx=12, pady=6).pack(side="right")
        tk.Button(pie, text="Exportar PNG", command=lambda: self._p_exportar("png"),
                  bg="#EEEAFE", fg=GRIS, relief="flat", padx=12, pady=6).pack(side="right", padx=(0, 6))
```

- [ ] **Step 2: Implementar `_p_exportar` (en hilo)**

Add to `class App`:

```python
    def _p_exportar(self, formato):
        if not self.p_logo:
            messagebox.showwarning("Falta el logo", "Primero elige el logo del cliente.")
            return
        cliente = self.p_cliente.get().strip() or "Cliente"
        ajustes = estado.aplicar_cambios(self.p_ajustes, {})
        self.p_estado.config(text="Exportando…")

        def trabajo():
            try:
                carpeta, _ = motor.exportar_personalizado(
                    self.p_logo, cliente, ajustes,
                    pdf=(formato == "pdf"), png=(formato == "png"))
                self.raiz.after(0, self._p_export_listo, carpeta)
            except Exception as e:
                self.raiz.after(0, self._p_error, str(e))

        threading.Thread(target=trabajo, daemon=True).start()

    def _p_export_listo(self, carpeta):
        self.p_estado.config(text="Exportado ✓")
        os.startfile(carpeta)
```

- [ ] **Step 3: Verificación manual**

Run: `python codigo/app.py` → pestaña Personalizar → logo + "Interbank" + algún ajuste → **Exportar PDF**.
Expected: se abre la carpeta `salida/Interbank-personalizado/` con `boceto-Interbank.pdf` (portada + el
modelo). Repetir con **Exportar PNG** → `clasica-Interbank.png`. Ambos > 0 bytes y se ven bien.

- [ ] **Step 4: Commit**

```bash
git add codigo/app.py
git commit -m "feat(v2): exportar el modelo personalizado a PDF/PNG desde la pestana"
```

---

## Fase 4 — Publicar

### Task 11: Preparar publicación (imports forzados + ARCHIVOS + gates verdes)

**Files:**
- Modify: `launcher.py:116-132` (forced imports: agregar `PIL.ImageTk`)
- Modify: `publicar.py:22-24` (`ARCHIVOS` += `estado.py`, `asistente.py`)
- Modify: `codigo/version.txt` (lo sube `publicar.py`; aquí solo se verifica)

**Interfaces:**
- Produces: el exe (al reconstruirse en Task 12) incluirá `PIL.ImageTk`; el auto-update repartirá
  `estado.py` y `asistente.py`.

- [ ] **Step 1: Forzar `PIL.ImageTk` en el launcher**

In `launcher.py`, in the forced-imports block (after `import PIL.JpegImagePlugin`, línea 123), add:

```python
import PIL.ImageTk        # noqa: F401  (codigo/app.py: preview de la pestaña Personalizar)
```

- [ ] **Step 2: Agregar los archivos planos nuevos a `publicar.py`**

In `publicar.py`, replace the `ARCHIVOS = [...]` list (líneas 22-24) with:

```python
ARCHIVOS = ["app.py", "motor.py", "render.py", "folleto.py", "renombrador.py",
            "estado.py", "asistente.py", "version.txt",
            "fuente-display.ttf", "fuente-display-italic.ttf", "foto-persona.jpg",
            "inter.ttf", "inter-semibold.ttf"]
```

- [ ] **Step 3: Correr TODA la suite + el smoke del launcher**

Run: `python -m pytest tests/ -v`
Expected: PASS (suite completa, incl. los tests nuevos de la v2 y los de la Parte A sin regresión).

Run (smoke con el código fuente, sin exe): from the project root,
```bash
python launcher.py --smoke
```
Then read `smoke_result.txt`.
Expected content (3 pestañas):
```
motor+plantillas OK; modelos=18
renombrador OK
GUI OK; pestanas=['Mockups', 'Renombrar Cotizaciones', 'Personalizar']
```

> Si `GUI` sale `FAIL(faltan pestanas)` o `pestanas` no trae las 3, revisar Task 8 antes de seguir.

- [ ] **Step 4: Commit**

```bash
git add launcher.py publicar.py
git commit -m "chore(v2): forzar PIL.ImageTk + publicar estado.py/asistente.py; suite verde"
```

---

### Task 12: Reconstruir el exe + zip completo + publicar

**Files:**
- Rebuild: `dist\` (exe + `dist\codigo` completo)
- Modify (via `publicar.py`): `codigo/version.txt`, `manifest.json`

**Interfaces:** entrega final para Diego/Mirza. (No hay código nuevo; es build + deploy.)

- [ ] **Step 1: Reconstruir el exe (incluye el nuevo `PIL.ImageTk`)**

Como esta v2 cambió los imports forzados del `launcher.py`, el `.exe` **debe** recompilarse (regla del
build). From the project root:

```bash
python -m PyInstaller MockupsDISECOD.spec --noconfirm
```

Expected: `dist\MockupsDISECOD.exe` regenerado sin errores.

- [ ] **Step 2: Smoke del exe ya construido (3 pestañas, sin consola)**

```bash
dist\MockupsDISECOD.exe --smoke
```
Then read `dist\smoke_result.txt` (o donde el exe lo escriba, junto al .exe).
Expected: las 3 líneas OK con `pestanas=['Mockups', 'Renombrar Cotizaciones', 'Personalizar']`.

- [ ] **Step 3: Copiar el `codigo/` completo a `dist\codigo` y armar el zip COMPLETO**

Reconstruir la carpeta `dist\codigo` entera (con `estado.py`, `asistente.py`, `plantillas/` y los assets) y
el zip del instalador **en la carpeta del proyecto** (NO update-zip en el Escritorio):

```powershell
Remove-Item -Recurse -Force dist\codigo -ErrorAction SilentlyContinue
Copy-Item -Recurse codigo dist\codigo
Compress-Archive -Path dist\MockupsDISECOD.exe, dist\codigo -DestinationPath dist\MockupsDISECOD-instalador.zip -Force
```

Expected: `dist\MockupsDISECOD-instalador.zip` actualizado con el código v2 completo.

- [ ] **Step 4: Publicar el auto-update (sube version + manifest + push)**

```bash
python publicar.py "v2 edicion conversacional: pestana Personalizar"
```

Expected: imprime "Publicado: version N…"; `manifest.json` incluye `estado.py` y `asistente.py` y las rutas
`plantillas/...`; commit + push a `origin/main` OK.

- [ ] **Step 5: Verificación final + handoff a Diego**

- Confirmar que `manifest.json` lista `estado.py`, `asistente.py`, `app.py`, `motor.py`,
  `plantillas/modelos/clasica.py`, `plantillas/modelos/mv7_medico.py`, etc.
- Avisar a Diego: **probar el exe/zip en vivo** (abrir la app → pestaña **Personalizar** → logo de un cliente
  → pedir por chat «ponle tipo de sangre», «el logo a la derecha», «color azul» → exportar PDF), y recién
  después pasarlo a Mirza/el vendedor.
- Pendiente conocido (fuera de v1): ampliar `campos_opcionales`/`logo_posiciones` a más modelos si el vendedor
  lo pide (receta mecánica de Task 6/7); edición del **reverso** queda fuera de v1 (el boceto es el frente).

---

## Self-Review (hecho al escribir el plan)

**1. Cobertura del spec:**
- D1 parser local + controles → Task 4 (parser), Task 9 (controles). ✓
- D2 editar un modelo elegido → `Ajustes.modelo` + selector (Task 8). ✓
- D3 boceto de venta (ajustes acotados) → campos/color/textos/logo_pos, sin arte final. ✓
- D4 qué se edita (campos/textos/color/cambiar modelo/logo preset) → Tasks 3,4,6,7,9. ✓
- D5 logo en posiciones preset, sugerir otro modelo → `logo_posiciones` + asistente (Tasks 2,4,6). ✓
- D6 exportar PDF/PNG → Task 5 (`exportar_personalizado`) + Task 10 (botones). ✓
- D7 cada modelo declara lo que soporta; asistente sugiere → Tasks 2,4,6,7. ✓
- §5.3 `construir_contexto(ajustes)` + §5.3 `render_modelo` → Tasks 3,5. ✓
- §5.4 intenciones SET_COLOR/TOGGLE_CAMPO/SET_TEXTO/SET_LOGO_POS/CAMBIAR_MODELO/NADA → Task 4. ✓
- §5.5 pestaña (preview+chat+controles+export) → Tasks 8-10. ✓
- §8 manejo de errores (parser no entiende; pedido no soportado; render falla) → Task 4 mensajes + Task 9
  `_p_error` reusa render robusto. ✓
- §9 riesgo "romper Parte A" → `ajustes=None` compatible (Task 3) + suite de regresión (Task 11). ✓

**2. Placeholders:** sin "TBD"/"implementar luego"; todo paso de código trae el código. ✓

**3. Consistencia de tipos/nombres:**
- `interpretar(texto, ajustes, modelo) -> (cambios, mensaje)` usado igual en Task 4 y Task 9. ✓
- `aplicar_cambios(ajustes, cambios)` y `ajustes_inicial(clave)` iguales en Tasks 1,9,10. ✓
- `render_modelo(logo, cliente, ajustes)` / `exportar_personalizado(...)` iguales en Tasks 5,9,10. ✓
- `modelos_con_campo`/`modelos_con_logo_pos` definidos en Task 2, usados en Task 4. ✓
- `ctx["campos"]` (dict) / `ctx["logo_pos"]` (str) definidos en Task 3, leídos en Tasks 6,7. ✓

**Dependencia cruzada anotada:** 2 casos de `tests/test_asistente.py` (Task 4) dependen de que `clasica`
declare capacidades (Task 6) → marcados `xfail` en Task 4 y desmarcados en Task 6.
