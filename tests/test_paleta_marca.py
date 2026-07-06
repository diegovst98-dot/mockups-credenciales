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
    # ningún gris hardcodeado tipo #999/#9aa0a6/#aaa/#bbb fuera de la paleta
    # (cubre hex de 3 Y de 6 dígitos que empiecen en 9/a/b — el gris real era #9aa0a6)
    import re
    assert not re.search(r"#[9ab][0-9a-f]{2}(?:[0-9a-f]{3})?\b", src, re.I)
