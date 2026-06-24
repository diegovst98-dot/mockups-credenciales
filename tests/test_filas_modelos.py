# -*- coding: utf-8 -*-
"""Las filas de datos (etiqueta:valor) del vendedor se dibujan en la zona de datos de
CADA modelo (filas_html). Campos libres -> aparecen como Empresa/DNI, sin romper el logo."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")

# representativos de cada familia: base, verticales (incl. mv4 de banda), horizontales
MODELOS = ["clasica", "gafete", "premium", "mv1", "mv4", "mv7", "mh1", "mh2", "mh5", "mh7"]


def _ctx(ajustes=None):
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)


def test_campo_libre_aparece_en_los_modelos():
    # "Área" (con tilde) es marcador seguro: no colisiona con el base64 del logo/foto
    ajustes = {"filas": [{"etiqueta": "DNI", "valor": "45678123"},
                         {"etiqueta": "Área", "valor": "Operaciones"}]}
    for clave in MODELOS:
        html, _, _ = cara_html(clave, ajustes)
        assert "Área" in html, clave
        assert "brightness(0)" not in html and "invert(" not in html, clave


def cara_html(clave, ajustes):
    from plantillas import cara
    return cara(clave, "frontal", _ctx(ajustes))


def test_empresa_por_defecto_en_filas():
    # la mayoría antepone Empresa (con_empresa=True)
    html, _, _ = cara_html("clasica", {"filas": []})
    assert "Empresa" in html


def test_mv3_no_duplica_empresa():
    # mv3 muestra la empresa en su banda -> filas SIN Empresa (con_empresa=False)
    html, _, _ = cara_html("mv3", {"filas": [{"etiqueta": "DNI", "valor": "123"}]})
    assert html.count("class='fetq'") == 1     # solo DNI, no Empresa+DNI


def test_mh2_ya_no_trae_gs_hardcodeado():
    html, _, _ = cara_html("mh2", {"filas": []})
    assert "GS:" not in html                   # el tipo de sangre ahora es campo libre
