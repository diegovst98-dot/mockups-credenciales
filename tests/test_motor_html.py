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
    for estilo in ("clasica", "gafete", "premium"):
        for lado in ("frontal", "reverso"):
            html, w, h = cara(estilo, lado, ctx)
            assert "class='card" in html
            assert ctx["prim_css"] in html
            assert (w, h) in (H_OK := [(1011, 638), (638, 1011)]), (estilo, lado, w, h)


# ---- Regla fija: el logo del cliente NUNCA se recolorea ----

def test_logo_cliente_no_se_recolorea():
    """El logo del cliente debe conservar su tinta original en TODAS las caras:
    nada de brightness(0)/invert/duotono que lo conviertan en silueta de un color."""
    from plantillas import cara, construir_contexto
    from motor import cargar_logo
    logo = cargar_logo(LOGO_DISECOD)
    ctx = construir_contexto(logo, (0, 164, 80), (0, 90, 44), "Interbank")
    # brightness(0)/invert solo se usaban para blanquear el logo: no deben aparecer
    # en ninguna cara. El logo va siempre en el frente (en algunos reversos manda el QR).
    for estilo in ("clasica", "gafete", "premium"):
        hf, _, _ = cara(estilo, "frontal", ctx)
        assert ctx["logo_uri"] in hf, (estilo, "logo ausente en el frente")
        for lado in ("frontal", "reverso"):
            html, _, _ = cara(estilo, lado, ctx)
            assert "brightness(0)" not in html, (estilo, lado, "recoloreo prohibido")
            assert "invert(" not in html, (estilo, lado, "recoloreo prohibido")


# ---- Task 8: generar arma el catálogo en PDF ----

def test_generar_produce_pdf_catalogo():
    from motor import generar
    from plantillas import catalogo
    out = tempfile.mkdtemp(prefix="t_gen_")
    carpeta, rutas = generar(LOGO_DISECOD, "Interbank", out)
    assert any(r.lower().endswith(".pdf") for r in rutas), rutas
    pdf = [r for r in rutas if r.lower().endswith(".pdf")][0]
    assert os.path.getsize(pdf) > 1000
    # un frente limpio por modelo del catálogo en para-diseno/
    diseno = glob.glob(os.path.join(carpeta, "para-diseno", "*.png"))
    assert len(diseno) >= len(catalogo()), (len(diseno), len(catalogo()))


def test_color_manual_se_respeta():
    from motor import generar
    out = tempfile.mkdtemp(prefix="t_col_")
    carpeta, rutas = generar(LOGO_DISECOD, "Acme", out, color="#cc2222")
    assert any(r.lower().endswith(".pdf") for r in rutas)


# ---- Task 6: robustez ----

def test_robustez_nombre_largo():
    from motor import generar
    out = tempfile.mkdtemp(prefix="t_rob_")
    carpeta, rutas = generar(LOGO_DISECOD, "Corporación Andina de Seguridad Integral del Perú", out)
    assert any(r.lower().endswith(".pdf") for r in rutas)


# ---- Propuesta wow (Task 5): generar() cura top-6, para-diseno conserva 18 ----

def test_generar_cura_top6_y_para_diseno_conserva_18(monkeypatch, tmp_path):
    import motor
    llamadas = {}

    def fake_armar_propuesta(cliente, logo, estrella, alts, ruta, marca, resto=()):
        llamadas["estrella"] = estrella[0]
        llamadas["n_alts"] = len(alts)
        llamadas["n_resto"] = len(resto)
        open(ruta, "wb").write(b"%PDF-1.4 fake")
        return 4
    import folleto
    monkeypatch.setattr(folleto, "armar_propuesta", fake_armar_propuesta)
    # render_caras es caro (Edge): sustituir por imágenes sintéticas
    from PIL import Image
    import render
    monkeypatch.setattr(render, "render_caras",
        lambda items: [Image.new("RGB", (a, b), (220, 220, 225)) for _h, a, b in items])
    # cargar_logo(None) explota (Image.open(None)): usar un logo sintético mínimo
    ruta_logo = str(tmp_path / "logo.png")
    Image.new("RGBA", (200, 80), (90, 70, 190, 255)).save(ruta_logo)
    carpeta, archivos = motor.generar(ruta_logo, "ACME SAC", carpeta_salida=str(tmp_path))
    assert llamadas["n_alts"] == 5
    assert llamadas["n_resto"] == 12   # anexo: el resto del catálogo (18 - 6)
    assert carpeta == str(tmp_path)
    assert archivos and archivos[0].endswith(".pdf") and os.path.exists(archivos[0])
    diseno = os.listdir(os.path.join(str(tmp_path), "para-diseno"))
    assert len([f for f in diseno if f.endswith(".png")]) == 18


# ---- Fase 2: variedad de fondos ----

def test_variante_es_determinista_y_varia():
    from plantillas import variante_de
    assert variante_de("Interbank") == variante_de("Interbank")          # determinista
    vals = {variante_de(n) for n in ["Interbank", "Frutos del Norte", "Constructora Lima"]}
    assert len(vals) >= 2                                                 # nombres distintos varían
    assert all(0 <= variante_de(n) <= 2 for n in ["a", "b", "c", "xyz"])  # en rango


def test_color_se_adapta_al_logo():
    """El layout es fijo pero el color de acento sale del logo del cliente:
    dos marcas de distinto color => distinto --acc/--prim en el mismo estilo."""
    from plantillas import cara, construir_contexto
    from motor import cargar_logo
    logo = cargar_logo(LOGO_DISECOD)
    verde = construir_contexto(logo, (0, 150, 70), (0, 90, 44), "Frutos del Norte")
    rojo = construir_contexto(logo, (200, 40, 40), (140, 20, 20), "Frutos del Norte")
    for estilo in ("clasica", "gafete", "premium"):
        hv, _, _ = cara(estilo, "frontal", verde)
        hr, _, _ = cara(estilo, "frontal", rojo)
        assert verde["prim_css"] in hv and rojo["prim_css"] in hr   # cada uno con su color
        assert hv != hr                                             # el diseño se recolorea


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
