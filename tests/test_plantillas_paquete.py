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
