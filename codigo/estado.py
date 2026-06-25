# -*- coding: utf-8 -*-
"""Estado de edición de la pestaña Personalizar (v2). 'Ajustes' es un dict simple,
única fuente de verdad: los controles lo mutan y el preview se re-renderiza desde él.

Modelo de datos (v2.2 — editor de campos, sin chat):
  modelo   : clave del modelo elegido
  color    : None (auto del logo) | "#RRGGBB"
  logo_pos : "default" | "izq" | "der" | "centro" (según el modelo)
  textos   : overrides del texto HÉROE -> {nombre, cargo}
  empresa  : nombre de la empresa (marca el web/monograma del modelo)
  filas    : LISTA ORDENADA de campos de datos [{etiqueta, valor}, ...] que el vendedor
             agrega/edita/quita libremente; se dibujan en la zona de datos del modelo.
Funciones puras y testeables; sin GUI, sin red."""
from copy import deepcopy

# Texto héroe (nombre grande + cargo): se edita en cajas dedicadas, no en la lista de filas.
TEXTO_HERO = ("nombre", "cargo")

# Filas de datos por defecto: VACÍO a propósito (sin datos falsos tipo "DNI 45678123"
# que delatan plantilla). El vendedor agrega los campos reales con "+ Agregar campo".
FILAS_DEFAULT = []

# --- Capas del editor visual (v3): logo/foto/textos como objetos movibles ---
# Cada capa guarda su CAJA en coordenadas normalizadas 0–1 (fracción de la tarjeta):
# {x, y} = esquina sup-izq, {w, h} = ancho/alto. El mismo ajuste rinde idéntico a
# cualquier resolución (preview chico = export grande) -> base del WYSIWYG.
CAPAS_IDS = ("logo", "foto", "nombre", "cargo", "datos")

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
    """Cajas genéricas de las capas (fallback). 'V' = vertical, resto = horizontal."""
    base = _CAPAS_V if orientacion == "V" else _CAPAS_H
    return {k: dict(v) for k, v in base.items()}


def _acomodar_texto(capas):
    """Conserva logo/foto (se derivan bien) y RE-APILA nombre/cargo/datos en una columna
    ordenada (sin solaparse) ubicada según dónde esté la foto: a su izquierda si la foto va
    a la derecha (horizontales), o debajo de ella si está centrada (verticales)."""
    c = {k: dict(v) for k, v in capas.items()}
    lo = c.get("logo", {"x": 0.05, "y": 0.05, "w": 0.30, "h": 0.18})
    fo = c.get("foto", {"x": 0.70, "y": 0.20, "w": 0.22, "h": 0.60})
    mx = 0.06
    if fo["x"] > 0.5:                       # foto a la derecha (horizontal) -> texto a la izquierda
        col_x = mx
        col_w = max(0.30, fo["x"] - 0.02 - mx)
        col_top = max(lo["y"] + lo["h"] + 0.05, 0.42)
        col_bot = 0.95
    else:                                   # foto centrada/izq (vertical) -> texto debajo de la foto
        col_x = mx
        col_w = 1 - 2 * mx
        col_top = min(0.92, max(fo["y"] + fo["h"] + 0.05, lo["y"] + lo["h"] + 0.05))
        col_bot = 0.97
    colh = max(0.18, col_bot - col_top)
    c["nombre"] = {"x": col_x, "y": col_top, "w": col_w, "h": colh * 0.22}
    c["cargo"] = {"x": col_x, "y": col_top + colh * 0.24, "w": col_w, "h": colh * 0.13}
    c["datos"] = {"x": col_x, "y": col_top + colh * 0.40, "w": col_w, "h": colh * 0.58}
    return c


def capas_de_modelo(modelo_clave):
    """Cajas del modelo: logo/foto NATIVOS (derivados) + texto re-apilado en columna
    ordenada. Si no hay anclas, cae a las genéricas. Cada modelo arranca ORDENADO."""
    try:
        import anclas
        nativas = anclas.ANCLAS.get(modelo_clave)
    except Exception:
        nativas = None
    if nativas and set(CAPAS_IDS) <= set(nativas):
        return _acomodar_texto(nativas)
    return capas_inicial("H")


def ajustes_inicial(modelo_clave):
    """Ajustes por defecto para un modelo recién elegido."""
    return {
        "modelo": modelo_clave,
        "color": None,
        "logo_pos": "default",
        "textos": {},                 # overrides de nombre/cargo
        "empresa": "",                # "" = usa el cliente que se pasa al render
        "filas": [dict(f) for f in FILAS_DEFAULT],
        "capas": capas_de_modelo(modelo_clave),
    }


def aplicar_cambios(ajustes, cambios):
    """Devuelve una COPIA de 'ajustes' con 'cambios' fusionados: 'textos' hace deep-merge;
    'filas' y el resto (modelo/color/logo_pos/empresa) se REEMPLAZAN."""
    nuevo = deepcopy(ajustes)
    for clave, valor in (cambios or {}).items():
        if clave == "textos" and isinstance(valor, dict):
            nuevo.setdefault("textos", {}).update(valor)
        else:
            nuevo[clave] = deepcopy(valor)
    return nuevo


def filas_validas(filas):
    """Limpia la lista: descarta filas sin etiqueta; recorta espacios."""
    out = []
    for f in filas or []:
        etq = (f.get("etiqueta") or "").strip()
        if etq:
            out.append({"etiqueta": etq, "valor": (f.get("valor") or "").strip()})
    return out


def _clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else float(v)


def mover_capa(ajustes, capa_id, x=None, y=None, w=None, h=None):
    """Devuelve una COPIA con la caja de 'capa_id' actualizada (valores clamp a 0–1);
    deja las demás capas intactas. Solo cambia los componentes que se pasan."""
    nuevo = deepcopy(ajustes)
    caja = nuevo.setdefault("capas", {}).setdefault(capa_id, {"x": 0.0, "y": 0.0, "w": 0.2, "h": 0.2})
    for nombre, val in (("x", x), ("y", y), ("w", w), ("h", h)):
        if val is not None:
            caja[nombre] = _clamp01(val)
    return nuevo


# --- Persistencia de cotización (guardar/reabrir): JSON-safe y tolerante a versiones viejas ---

def serializar(ajustes, empresa, logo_ruta, foto_ruta):
    """Empaqueta el estado de una cotización para guardarlo como JSON local."""
    return {
        "version": 1,
        "ajustes": deepcopy(ajustes),
        "empresa": empresa or "",
        "logo_ruta": logo_ruta or "",
        "foto_ruta": foto_ruta or "",
    }


def deserializar(data):
    """Reconstruye una cotización guardada; rellena lo que falte (cotización vieja)."""
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
