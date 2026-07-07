# -*- coding: utf-8 -*-
"""Loop de color iteración 1 (2026-07-06, logos famosos):
1. acc2 fallback ARMÓNICO: mismo matiz profundo apagado (el análogo +25° inventaba
   oliva en amarillos y marrón en rojos).
2. Bicolor 50/50: el matiz más PROFUNDO es la estructura/dominante (Pepsi = azul,
   no rojo); pares con dominante claro de verdad (Interbank) no se voltean.
3. Matices luminosos (amarillo/lima 40–90°): prof/carbon corren el matiz hacia el
   ámbar → marrón dorado rico, no mostaza/oliva sucia."""
import colorsys
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))

from PIL import Image  # noqa: E402


def _hls(c):
    return colorsys.rgb_to_hls(*[x / 255.0 for x in c])


def _dh(h1, h2):
    d = abs(h1 - h2)
    return min(d, 1 - d)


def _logo_bicolor(c1, c2, frac1=0.5):
    """Logo sintético opaco: dos bandas de color (frac1 = proporción de c1)."""
    img = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
    corte = int(100 * frac1)
    img.paste(Image.new("RGBA", (120, corte), c1 + (255,)), (0, 0))
    img.paste(Image.new("RGBA", (120, 100 - corte), c2 + (255,)), (0, corte))
    return img


# --- 1. acc2 armónico ---

def test_acc2_fallback_es_del_mismo_matiz_no_analogo():
    from motor import paleta_roles, dif_matiz
    rojo = (233, 29, 43)                       # Coca-Cola
    roles = paleta_roles(rojo, tuple(int(x * 0.6) for x in rojo))
    h_acc = _hls(roles["acc"])[0]
    h_acc2, _l, s = _hls(roles["acc2"])
    assert dif_matiz(h_acc, h_acc2) < 8 / 360.0     # humo de la marca, no marrón ajeno
    assert 0.15 <= s <= 0.50                        # apagado


def test_acc2_de_amarillo_no_es_verde_oliva():
    from motor import paleta_roles
    amarillo = (255, 204, 0)                   # McDonald's
    roles = paleta_roles(amarillo, (140, 112, 0))
    h = _hls(roles["acc2"])[0] * 360
    assert h < 62, "acc2 %r se fue a verde oliva (h=%.0f)" % (roles["acc2"], h)


# --- 2. bicolor 50/50: el profundo manda ---

def test_bicolor_parity_domina_el_profundo():
    from motor import paleta_del_logo
    rojo, azul = (235, 32, 60), (6, 92, 148)   # Pepsi: rojo apenas más presente
    prim, sec = paleta_del_logo(_logo_bicolor(rojo, azul, frac1=0.58))
    h_p = _hls(prim)[0]
    assert _dh(h_p, _hls(azul)[0]) < 0.06, "Pepsi debe ser AZUL, salió %r" % (prim,)
    assert _dh(_hls(sec)[0], _hls(rojo)[0]) < 0.06   # el rojo sobrevive como acento


def test_bicolor_dominante_claro_legitimo_no_se_voltea():
    from motor import paleta_del_logo
    verde, azul = (0, 165, 80), (0, 96, 169)   # Interbank: L casi iguales
    prim, _sec = paleta_del_logo(_logo_bicolor(verde, azul, frac1=0.60))
    assert _dh(_hls(prim)[0], _hls(verde)[0]) < 0.06, \
        "Interbank debe seguir VERDE, salió %r" % (prim,)


def test_bicolor_secundario_minoritario_no_dispara_parity():
    from motor import paleta_del_logo
    azul, naranja = (0, 65, 146), (249, 106, 83)   # BCP: naranja ~30%
    prim, _sec = paleta_del_logo(_logo_bicolor(azul, naranja, frac1=0.72))
    assert _dh(_hls(prim)[0], _hls(azul)[0]) < 0.06


# --- 3. profundidad de matices luminosos ---

def test_prof_de_amarillo_corre_hacia_ambar():
    from motor import paleta_roles
    amarillo = (255, 204, 0)
    roles = paleta_roles(amarillo, (140, 112, 0))
    h_prof = _hls(roles["prof"])[0] * 360
    h_acc = _hls(roles["acc"])[0] * 360
    assert h_prof < h_acc - 6, "prof %r sigue en mostaza (h=%.0f)" % (roles["prof"], h_prof)
    _h, l, s = _hls(roles["prof"])
    assert 0.20 <= l <= 0.36 and s >= 0.45          # sigue profundo y saturado


def test_prof_de_rojo_no_se_toca():
    from motor import paleta_roles, dif_matiz
    rojo = (233, 29, 43)
    roles = paleta_roles(rojo, tuple(int(x * 0.6) for x in rojo))
    assert dif_matiz(_hls(roles["prof"])[0], _hls(roles["acc"])[0]) < 0.02
