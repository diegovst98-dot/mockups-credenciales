# -*- coding: utf-8 -*-
import glob
import os
import sys
import tempfile

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
sys.path.insert(0, CODIGO)

LOGO_DISECOD = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


# ---- Task 1: prerequisitos ----

def test_playwright_disponible():
    import playwright  # noqa


def test_fuentes_horneadas_existen():
    for f in ("playfair.ttf", "inter.ttf", "inter-semibold.ttf"):
        assert os.path.exists(os.path.join(CODIGO, "fuentes", f)), f


# ---- Task 2: render ----

def test_render_caras_produce_imagen_del_tamano():
    from render import render_caras
    html = ('<!doctype html><body style="margin:0">'
            '<div class="card" style="width:200px;height:120px;background:#0a7"></div></body>')
    imgs = render_caras([(html, 200, 120)], escala=2)
    assert len(imgs) == 1
    assert imgs[0].size == (400, 240)
    # no es una imagen vacía: algún canal tiene señal (el fondo verde)
    assert any(mx > 0 for (_, mx) in imgs[0].convert("RGB").getextrema())


# ---- Task 3: contexto + css ----

def test_contexto_y_css_base():
    from plantillas import construir_contexto, css_base
    from motor import cargar_logo
    logo = cargar_logo(LOGO_DISECOD)
    ctx = construir_contexto(logo, (0, 164, 80), (0, 90, 44), "Interbank")
    assert ctx["logo_uri"].startswith("data:image/png;base64,")
    assert ctx["foto_uri"].startswith("data:image")
    assert ctx["prim_css"] == "rgb(0,164,80)"
    assert "@font-face" in css_base() and "Playfair" in css_base()


# ---- Task 4: caras ----

def test_cara_devuelve_html_dimensionado():
    from plantillas import cara, construir_contexto
    from motor import cargar_logo
    logo = cargar_logo(LOGO_DISECOD)
    ctx = construir_contexto(logo, (0, 164, 80), (0, 90, 44), "Interbank")
    for estilo in ("aurora", "editorial", "glass"):
        for lado in ("frontal", "reverso"):
            html, w, h = cara(estilo, lado, ctx)
            assert "class='card" in html
            assert ctx["prim_css"] in html
            assert (w, h) in (H_OK := [(1011, 638), (638, 1011)]), (estilo, lado, w, h)


# ---- Task 5: generar end to end ----

def test_generar_produce_brief_y_3_direcciones():
    from motor import generar
    out = tempfile.mkdtemp(prefix="t_gen_")
    carpeta, rutas = generar(LOGO_DISECOD, "Interbank", out)
    base = [os.path.basename(r) for r in rutas]
    assert any("brief" in b for b in base), base
    assert sum(b.startswith("direccion-") for b in base) == 3, base
    diseno = glob.glob(os.path.join(carpeta, "para-diseno", "*.png"))
    assert len(diseno) == 6, diseno


# ---- Task 6: robustez ----

def test_robustez_nombre_largo():
    from motor import generar
    out = tempfile.mkdtemp(prefix="t_rob_")
    carpeta, rutas = generar(LOGO_DISECOD, "Corporación Andina de Seguridad Integral del Perú", out)
    assert len(rutas) >= 4
