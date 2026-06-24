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

# Filas de datos por defecto (el vendedor las edita / agrega / quita).
FILAS_DEFAULT = [
    {"etiqueta": "DNI", "valor": "45678123"},
]


def ajustes_inicial(modelo_clave):
    """Ajustes por defecto para un modelo recién elegido."""
    return {
        "modelo": modelo_clave,
        "color": None,
        "logo_pos": "default",
        "textos": {},                 # overrides de nombre/cargo
        "empresa": "",                # "" = usa el cliente que se pasa al render
        "filas": [dict(f) for f in FILAS_DEFAULT],
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
