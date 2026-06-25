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

# --- Capa movible del editor (v3.2 — "el modelo manda"): SOLO el logo ---
# Decisión Diego 2026-06-24: mover el LOGO no arruina la imagen, pero mover la FOTO sí
# (sale cuadrada en marcos redondos). Por eso la foto la pinta SIEMPRE el modelo (la
# enmarca perfecto, respeta su forma) y el vendedor solo la SUBE; solo el logo se reubica.
# Caja normalizada 0–1; caja["movido"]=True => el logo se vuelve capa encima del render.
CAPAS_IDS = ("logo",)

_CAPAS_H = {"logo": {"x": 0.05, "y": 0.06, "w": 0.30, "h": 0.18}}
_CAPAS_V = {"logo": {"x": 0.18, "y": 0.05, "w": 0.64, "h": 0.16}}


def capas_inicial(orientacion="H"):
    """Caja genérica del logo (fallback si no hay ancla del modelo)."""
    base = _CAPAS_V if orientacion == "V" else _CAPAS_H
    return {k: dict(v) for k, v in base.items()}


def capas_de_modelo(modelo_clave):
    """Caja NATIVA del logo del modelo (derivada en anclas.py), para que al moverlo
    arranque donde el modelo lo pone. Si no hay ancla, cae a la genérica."""
    try:
        import anclas
        nativas = anclas.ANCLAS.get(modelo_clave)
    except Exception:
        nativas = None
    if nativas and "logo" in nativas:
        return {"logo": dict(nativas["logo"])}
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
        "foto_ruta": None,            # None = foto demo; ruta = foto subida del cliente
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
    caja["movido"] = True          # marca que el vendedor lo reubicó -> se vuelve capa
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
