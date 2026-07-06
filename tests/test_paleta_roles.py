# -*- coding: utf-8 -*-
"""Paleta de ROLES por credencial (propuesta wow 2026-07-06): en vez de pintar
los 18 modelos con el mismo par prim/sec, cada modelo elige un combo de roles."""
import colorsys
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))

LAVANDA = (169, 161, 216)   # tinta clara (caso DISECOD)
ROJO = (180, 30, 40)        # tinta saturada oscura


def _hls(c):
    return colorsys.rgb_to_hls(*[x / 255.0 for x in c])


def _dh(h1, h2):
    d = abs(h1 - h2)
    return min(d, 1 - d)


def test_paleta_roles_tiene_los_4_roles():
    from motor import paleta_roles
    roles = paleta_roles(LAVANDA, (90, 80, 140))
    assert set(roles) >= {"acc", "prof", "carbon", "claro"}
    for c in roles.values():
        assert len(c) == 3 and all(0 <= x <= 255 for x in c)


def test_roles_luminancias_en_rango():
    from motor import paleta_roles
    for prim in (LAVANDA, ROJO, (240, 150, 40), (30, 90, 180)):
        roles = paleta_roles(prim, tuple(int(x * 0.6) for x in prim))
        _h, l, s = _hls(roles["prof"])
        assert 0.20 <= l <= 0.36 and s >= 0.45      # profundo, mismo matiz
        _h, l, s = _hls(roles["carbon"])
        assert 0.10 <= l <= 0.22 and s <= 0.25      # casi neutro ("navy" de marca)
        _h, l, s = _hls(roles["claro"])
        assert 0.84 <= l <= 0.94                    # tinte suave


def test_roles_conservan_el_matiz_de_la_marca():
    from motor import paleta_roles
    roles = paleta_roles(ROJO, (90, 10, 20))
    ha = _hls(roles["acc"])[0]
    for rol in ("prof", "carbon", "claro"):
        assert _dh(_hls(roles[rol])[0], ha) < 0.06


def test_acc_es_el_prim_anti_lavado():
    from motor import paleta_marca, paleta_roles
    prim, _sec = paleta_marca(LAVANDA, (90, 80, 140))
    assert paleta_roles(LAVANDA, (90, 80, 140))["acc"] == prim


def test_combos_cubren_catalogo_con_roles_validos():
    from plantillas.curaduria import COMBOS
    from plantillas.registro import catalogo
    import plantillas  # noqa: F401
    roles = {"acc", "prof", "carbon", "claro"}
    for m in catalogo():
        c1, c2 = COMBOS.get(m.clave, ("acc", "prof"))
        assert c1 in roles and c2 in roles and c1 != c2
    # modelos de bandas/áreas grandes: área en tono profundo/neutro + acento vivo
    for k in ("mv1", "mv2", "mv3", "mv4", "mh4", "mh2", "mh7"):
        assert COMBOS[k][0] in ("carbon", "prof") and COMBOS[k][1] == "acc"


def test_desempate_estrella_determinista_y_variado():
    from plantillas.curaduria import elegir_top
    import plantillas  # noqa: F401
    assert elegir_top(ROJO) == elegir_top(ROJO)      # mismo prim = mismo top
    prims = [ROJO, (30, 90, 180), (20, 140, 60), (240, 120, 20), (120, 40, 160)]
    estrellas = {elegir_top(p)[0] for p in prims}
    assert len(estrellas) >= 2                       # la estrella rota entre marcas
