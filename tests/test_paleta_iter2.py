# -*- coding: utf-8 -*-
"""Loop de color iteración 2 (2026-07-06, logos famosos):
1. acc2 REAL vs acc2 HUMO: el 2º color real del logo puede pintar ÁREA MEDIA
   (banda del cargo mh1, banda b2 de mv6 vía --acc2m); el humo derivado se queda
   en hairlines. paleta_roles expone "acc2_real" (None si no existe).
2. Estrella para marcas vivas: con tinta saturada la estrella es color-forward
   (mh7/mh2/mv6), nunca Premium crema (caso McDonald's).
3. Tope anti-neón: acentos muy saturados Y luminosos (Spotify) bajan a un verde
   rico imprimible; los saturados oscuros (Coca-Cola, Pepsi) no se tocan.
4. marca_legible con matices luminosos (40–90°): más profundidad + corrimiento
   ámbar para que el TEXTO no quede mostaza débil sobre crema (Premium McD)."""
import colorsys
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))

SPOTIFY = ((30, 216, 96), (16, 118, 52))     # verde neón, sec mismo matiz
PEPSI = ((6, 92, 148), (235, 32, 60))        # azul dominante + rojo REAL
COCA = ((237, 28, 36), (130, 15, 20))        # rojo vivo, sec mismo matiz
MCD = ((255, 199, 44), (218, 41, 28))        # amarillo + rojo REAL


def _hls(c):
    return colorsys.rgb_to_hls(*[x / 255.0 for x in c])


def _dh(h1, h2):
    d = abs(h1 - h2)
    return min(d, 1 - d)


# ---------- 1. acc2 real vs humo ----------

def test_paleta_roles_expone_acc2_real():
    from motor import paleta_roles
    roles = paleta_roles(*PEPSI)
    assert roles["acc2_real"] is not None
    # el acc2 real conserva el matiz rojo del logo (no es humo azul)
    h_real = _hls(roles["acc2_real"])[0]
    assert _dh(h_real, _hls(PEPSI[1])[0]) < 20 / 360.0


def test_paleta_roles_acc2_real_none_si_monocolor():
    from motor import paleta_roles
    roles = paleta_roles(*COCA)          # sec = mismo matiz oscuro → no hay 2º color
    assert roles["acc2_real"] is None


def test_paleta_roles_acc2_real_none_si_neutra():
    from motor import paleta_roles
    roles = paleta_roles((40, 40, 40), (20, 20, 20))
    assert roles["acc2_real"] is None


def test_contexto_acc2m_pinta_con_el_segundo_color_real():
    from plantillas.base import construir_contexto
    from motor import paleta_roles
    from PIL import Image
    logo = Image.new("RGBA", (80, 80), (10, 90, 150, 255))
    roles = paleta_roles(*PEPSI)
    ctx = construir_contexto(logo, roles["acc"], roles["acc2"], "Pepsi")
    # sec de matiz distinto → --acc2m es el color real (≠ prim) y texto blanco
    assert ctx["acc2m_css"] != ctx["prim_css"]
    assert ctx["txt_acc2m"] == "#ffffff"


def test_contexto_acc2m_cae_al_prim_si_es_humo():
    from plantillas.base import construir_contexto
    from motor import paleta_roles
    from PIL import Image
    logo = Image.new("RGBA", (80, 80), (200, 30, 40, 255))
    roles = paleta_roles(*COCA)
    ctx = construir_contexto(logo, roles["acc"], roles["acc2"], "Coca")
    # humo (mismo matiz) NO pinta área media: fallback exacto al prim
    assert ctx["acc2m_css"] == ctx["prim_css"]
    assert ctx["txt_acc2m"] == ctx["txt_sobre_prim"]


def test_root_emite_variables_acc2m():
    from plantillas.base import construir_contexto, _root
    from motor import paleta_roles
    from PIL import Image
    logo = Image.new("RGBA", (80, 80), (10, 90, 150, 255))
    roles = paleta_roles(*PEPSI)
    css = _root(construir_contexto(logo, roles["acc"], roles["acc2"], "Pepsi"))
    assert "--acc2m:" in css and "--txtacc2m:" in css


def test_mh1_y_mv6_usan_acc2m_en_area_media():
    import plantillas  # noqa: F401
    from plantillas.modelos import mh1_digitalworld, mv6_minimal
    assert "var(--acc2m)" in mh1_digitalworld._CSS   # banda del cargo
    assert "var(--acc2m)" in mv6_minimal._CSS        # banda b2


def test_combo_mv6_alimenta_acc2():
    from plantillas.curaduria import COMBOS
    assert COMBOS["mv6"] == ("acc", "acc2")


# ---------- 2. estrella color-forward para marcas vivas ----------

def test_estrella_marca_viva_no_es_premium():
    from plantillas.curaduria import elegir_top
    import plantillas  # noqa: F401
    for prim in [(237, 28, 36), (255, 199, 44), (30, 216, 96), (0, 74, 134)]:
        top = elegir_top(prim)
        assert top[0] in {"mh7", "mh2", "mv6"}, (prim, top)


def test_marca_sobria_conserva_desempate_libre():
    from plantillas.curaduria import elegir_top
    import plantillas  # noqa: F401
    # gris azulado desaturado: NO es viva → premium puede seguir siendo estrella
    top = elegir_top((70, 80, 95))
    assert len(top) == 6   # sin exigir estrella específica: solo que no rompa


# ---------- 3. tope anti-neón en el acento ----------

def test_acc_neon_baja_a_verde_rico():
    from motor import paleta_roles, luminancia, saturacion
    roles = paleta_roles(*SPOTIFY)
    _h, l, s = _hls(roles["acc"])
    assert s <= 0.72 + 1e-6
    assert luminancia(roles["acc"]) < 0.45          # deja de ser chillón
    # sigue siendo verde Spotify (matiz intacto)
    assert _dh(_hls(roles["acc"])[0], _hls(SPOTIFY[0])[0]) < 8 / 360.0
    assert saturacion(roles["acc"]) > 0.5           # no se apaga


def test_acc_amarillo_iconico_no_se_apaga():
    from motor import paleta_roles
    # el amarillo McDonald's ES la marca: el anti-neón NO lo vuelve ocre
    # (la legibilidad la da el texto oscuro, no apagar la banda)
    assert paleta_roles((255, 204, 0), (140, 112, 0))["acc"] == (255, 204, 0)


def test_acc_saturado_oscuro_no_se_toca():
    from motor import paleta_roles
    assert paleta_roles(*COCA)["acc"] == COCA[0]      # rojo vivo intacto
    assert paleta_roles(*PEPSI)["acc"] == PEPSI[0]    # azul intacto


# ---------- 4. marca_legible con matices luminosos ----------

def test_marca_legible_amarillo_gana_profundidad_ambar():
    from motor import marca_legible, luminancia
    res = marca_legible((255, 199, 44))              # amarillo McDonald's
    assert luminancia(res) <= 0.21                   # más profundo que el tope 0.32
    h = _hls(res)[0] * 360
    assert h < 42                                    # corrió hacia el ámbar
    assert res[0] > res[1] > res[2]                  # marrón dorado, no verde oliva


def test_marca_legible_no_luminoso_sin_cambio():
    from motor import marca_legible, luminancia
    azul = marca_legible((0, 74, 134))
    assert azul == (0, 74, 134)                      # ya legible: intacto
    assert luminancia(marca_legible((120, 190, 250))) <= 0.32
