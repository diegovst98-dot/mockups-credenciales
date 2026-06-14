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
    for f in ("fuente-display.ttf", "inter.ttf", "inter-semibold.ttf"):
        assert os.path.exists(os.path.join(CODIGO, f)), f


def test_fondos_disponibles():
    assert len(glob.glob(os.path.join(CODIGO, "fondo-*.jpg"))) >= 3


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


# ---- Fase 2: variedad de fondos ----

def test_variante_es_determinista_y_varia():
    from plantillas import variante_de
    assert variante_de("Interbank") == variante_de("Interbank")          # determinista
    vals = {variante_de(n) for n in ["Interbank", "Frutos del Norte", "Constructora Lima"]}
    assert len(vals) >= 2                                                 # nombres distintos varían
    assert all(0 <= variante_de(n) <= 2 for n in ["a", "b", "c", "xyz"])  # en rango


def test_mismo_color_distinto_cliente_cambia_fondo():
    from plantillas import cara, construir_contexto
    from motor import cargar_logo
    logo = cargar_logo(LOGO_DISECOD)
    a = construir_contexto(logo, (0, 120, 200), (0, 80, 140), "Constructora Lima")  # variante 0
    b = construir_contexto(logo, (0, 120, 200), (0, 80, 140), "Frutos del Norte")   # variante 2
    html_a, _, _ = cara("aurora", "frontal", a)
    html_b, _, _ = cara("aurora", "frontal", b)
    assert html_a != html_b   # mismo color, distinto fondo


# ---- Fase 2: foto 1x1 (encuadre sin invocar el modelo pesado) ----

def test_encuadre_foto_carnet():
    from PIL import Image
    from foto1x1 import _encuadrar_retrato, FORMATOS
    persona = Image.new("RGBA", (400, 600), (0, 0, 0, 0))
    for x in range(120, 280):          # zona opaca = "persona"
        for y in range(80, 560):
            persona.putpixel((x, y), (90, 90, 90, 255))
    w, h = FORMATOS["3x4"]
    out = _encuadrar_retrato(persona, w, h)
    assert out.size == (w, h)
    assert out.mode == "RGB"
    assert out.getpixel((2, 2)) == (255, 255, 255)   # fondo blanco
