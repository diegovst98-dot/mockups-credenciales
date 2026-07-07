# -*- coding: utf-8 -*-
"""Ojo de diseñador v33: clusters de matiz, marcas neutras sin color inventado,
acc2 (acento secundario) real o análogo, y contraste garantizado."""
import colorsys
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))

ENTRADA = os.path.join(os.path.dirname(__file__), "..", "entrada")


def _hsv(c):
    return colorsys.rgb_to_hsv(*[x / 255.0 for x in c])


def _logo(nombre):
    from motor import cargar_logo
    return cargar_logo(os.path.join(ENTRADA, nombre))


def _logo_solido(color, tam=(200, 120)):
    """Logo sintético monocolor con antialias sucio en el borde (ruido real)."""
    img = Image.new("RGBA", tam, (0, 0, 0, 0))
    px = img.load()
    for x in range(20, tam[0] - 20):
        for y in range(20, tam[1] - 20):
            px[x, y] = color + (255,)
    return img


def test_frutos_dos_clusters_verde_dominante_dorado_secundario():
    from motor import paleta_del_logo
    prim, sec = paleta_del_logo(_logo("logo-prueba-frutos.png"))
    h_p, s_p, _ = _hsv(prim)
    h_s, s_s, _ = _hsv(sec)
    assert 0.20 <= h_p <= 0.45 and s_p >= 0.25      # verde real del logo
    assert 0.05 <= h_s <= 0.16 and s_s >= 0.25      # dorado real del logo
    # y sobrevive a paleta_marca (antes el dorado se pisaba por ser más claro)
    from motor import paleta_marca, dif_matiz
    prim2, sec2 = paleta_marca(prim, sec)
    assert dif_matiz(_hsv(sec2)[0], h_s) < 0.05     # sigue siendo dorado


def test_logo_negro_paleta_neutra_sin_matiz_inventado():
    from motor import paleta_del_logo, paleta_marca, paleta_roles
    prim, sec = paleta_del_logo(_logo("logo-prueba-negro.png"))
    roles = paleta_roles(prim, sec)
    for rol, c in roles.items():
        if rol == "acc2_real":          # iter2: None si no hay 2º color real
            assert c is None
            continue
        assert _hsv(c)[1] < 0.08, "rol %s inventó color: %s" % (rol, c)
    # y paleta_marca tampoco satura el ruido de un gris directo
    for gris in ((30, 30, 30), (56, 56, 58), (120, 120, 122)):
        p, s = paleta_marca(gris, tuple(int(x * 0.6) for x in gris))
        assert _hsv(p)[1] < 0.08 and _hsv(s)[1] < 0.08


def test_logo_monocolor_rojo_acc_rojo_y_acc2_analogo():
    from motor import paleta_del_logo, paleta_roles, dif_matiz
    rojo = (185, 28, 38)
    prim, sec = paleta_del_logo(_logo_solido(rojo))
    assert _hsv(prim)[0] < 0.05 or _hsv(prim)[0] > 0.95   # rojo
    roles = paleta_roles(prim, sec)
    h_acc = _hsv(roles["acc"])[0]
    h_acc2, s_acc2, _ = _hsv(roles["acc2"])
    d = dif_matiz(h_acc, h_acc2)
    assert d <= 30 / 360.0 + 0.02                   # análogo (±25°), no complementario
    assert 0.15 <= s_acc2 <= 0.75                   # apagado, no chillón


def test_contraste_garantizado_en_roles_de_texto():
    from motor import luminancia, paleta_del_logo, paleta_roles
    for nombre in ("logo-prueba-frutos.png", "logo-prueba-negro.png",
                   "logo-prueba-acme.png"):
        roles = paleta_roles(*paleta_del_logo(_logo(nombre)))
        for rol in ("acc", "acc2", "prof", "carbon"):
            assert luminancia(roles[rol]) <= 0.45, \
                "rol %s de %s ilegible sobre claro" % (rol, nombre)
        assert luminancia(roles["claro"]) >= 0.60   # claro sí es claro


def test_secundario_real_llega_al_acc2_del_contexto():
    """El dorado de frutos debe llegar a --acc2 vía construir_contexto."""
    from motor import paleta_del_logo, paleta_marca, dif_matiz
    from plantillas import construir_contexto
    logo = _logo("logo-prueba-frutos.png")
    prim, sec = paleta_marca(*paleta_del_logo(logo))
    ctx = construir_contexto(logo, prim, sec, "Frutos")
    c = ctx["acc2_css"]                             # formato "rgb(r,g,b)"
    assert c.startswith("rgb("), "cayó al oro genérico: %s" % c
    rgb = tuple(int(x) for x in c[4:-1].split(","))
    assert dif_matiz(_hsv(rgb)[0], 0.11) < 0.06     # dorado, no oro genérico ni verde
