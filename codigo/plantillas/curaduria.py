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

# Combo de roles de color por modelo (rol_prim, rol_sec) — ver motor.paleta_roles.
# Criterio de diseñador: bandas/áreas GRANDES → tono profundo/neutro + acento vivo
# (no se lavan ni gritan); modelos limpios/minimal → acento + carbon; resto → acc/prof.
COMBOS = {
    # áreas grandes
    "mv1": ("carbon", "acc"),   # Impacto (triángulo grande)
    "mv2": ("carbon", "acc"),   # Orgánica (blobs)
    "mv3": ("prof", "acc"),     # Corporativa (banda superior)
    "mv4": ("carbon", "acc"),   # Doble Banda
    "mh4": ("prof", "acc"),     # Fluida
    "mh2": ("prof", "acc"),     # Dinámica
    "mh7": ("prof", "acc"),     # Círculo (suele ser estrella: que lleve el color del cliente)
    # limpios / minimal (clasica y gafete dibujan hairlines --acc2 → si el logo
    # trae un 2º color real, ese detalle fino lo lleva; si no, cae al oro)
    "mv6": ("acc", "carbon"), "mv7": ("acc", "carbon"), "mv8": ("acc", "carbon"),
    "clasica": ("acc", "acc2"), "mh5": ("acc", "carbon"),
    "premium": ("acc", "carbon"), "gafete": ("acc", "acc2"),
    # resto: el 2º rol alimenta --acc2 (acento fino) — v33 usa el secundario
    # real del logo (o el análogo apagado) en vez del profundo del mismo matiz
    "mv5": ("acc", "acc2"), "mh1": ("acc", "acc2"),
    "mh3": ("acc", "acc2"), "mh6": ("acc", "acc2"),
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

    # desempate variado: dentro de cada grupo de empate se rota por hash del
    # prim, para que la estrella no sea siempre la misma con todas las marcas
    # (determinista: mismo prim = mismo orden).
    # (hash de tupla de ints es determinista entre corridas; el int RGB crudo
    # caía siempre en la misma paridad con % 2)
    sem = hash((int(prim[0]), int(prim[1]), int(prim[2]))) & 0x7FFFFFFF
    grupos = {}
    for c in sorted(ori):
        grupos.setdefault(score(c), []).append(c)
    orden = []
    for s in sorted(grupos, reverse=True):
        emp = grupos[s]
        r = sem % len(emp)
        orden += emp[r:] + emp[:r]
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
