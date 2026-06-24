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
