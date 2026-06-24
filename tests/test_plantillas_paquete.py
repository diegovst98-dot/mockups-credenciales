# -*- coding: utf-8 -*-
import os
import sys

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
sys.path.insert(0, CODIGO)

LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _ctx():
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank")


# ---- Task 2: el paquete conserva la API y expone el registro ----

def test_api_publica_se_conserva():
    import plantillas
    for nombre in ("cara", "construir_contexto", "css_base", "variante_de", "catalogo"):
        assert hasattr(plantillas, nombre), nombre


def test_tres_estilos_originales_registrados():
    from plantillas import catalogo
    claves = {m.clave for m in catalogo()}
    assert {"clasica", "gafete", "premium"} <= claves


def test_cara_originales_dimensionadas():
    from plantillas import cara
    ctx = _ctx()
    for estilo in ("clasica", "gafete", "premium"):
        for lado in ("frontal", "reverso"):
            html, w, h = cara(estilo, lado, ctx)
            assert "class='card" in html and ctx["prim_css"] in html
            assert (w, h) in [(1011, 638), (638, 1011)]


def test_catalogo_expone_metadata():
    from plantillas import catalogo
    for m in catalogo():
        assert m.clave and m.nombre
        assert m.orientacion in ("V", "H")
        assert callable(m.frontal)


# ---- Task 3: datos demo con campos extra ----

def test_datos_demo_tienen_campos_extra():
    from plantillas import DATOS
    assert DATOS["tipo_sangre"] == "O+"
    assert DATOS["codigo"] == "10052"


# ---- Task 4-5: modelos de validación Fase 1 (mv1, mh1, mh2) ----

def _render_invariantes(clave, esperado):
    from plantillas import cara
    ctx = _ctx()
    html, w, h = cara(clave, "frontal", ctx)
    assert (w, h) == esperado, (clave, w, h)
    assert ctx["logo_uri"] in html, (clave, "logo del cliente ausente")
    assert ctx["prim_css"] in html, (clave, "color de marca ausente")
    assert "brightness(0)" not in html and "invert(" not in html, (clave, "recoloreo prohibido")


def test_mv1_vertical():
    _render_invariantes("mv1", (638, 1011))


def test_mh1_horizontal():
    _render_invariantes("mh1", (1011, 638))


def test_mh2_horizontal():
    # (el tipo de sangre dejó de estar hardcodeado en mh2; ahora es un campo libre)
    _render_invariantes("mh2", (1011, 638))


# ---- Task 6: catálogo completo (18 modelos) ----

ESPERADOS = ["clasica", "gafete", "premium",
             "mv1", "mv2", "mv3", "mv4", "mv5", "mv6", "mv7", "mv8",
             "mh1", "mh2", "mh3", "mh4", "mh5", "mh6", "mh7"]


def test_catalogo_completo_render_y_dimensiones():
    from plantillas import cara, catalogo
    ctx = _ctx()
    claves = [m.clave for m in catalogo()]
    for c in ESPERADOS:
        assert c in claves, ("falta modelo", c)
    for m in catalogo():
        html, w, h = cara(m.clave, "frontal", ctx)
        esperado = (1011, 638) if m.orientacion == "H" else (638, 1011)
        assert (w, h) == esperado, (m.clave, w, h)
        assert ctx["logo_uri"] in html, (m.clave, "logo ausente")
        assert "brightness(0)" not in html and "invert(" not in html, (m.clave, "recoloreo prohibido")
