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
