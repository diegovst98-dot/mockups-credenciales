# -*- coding: utf-8 -*-
"""Específico de clasica: posición de logo y filas base. Los campos extra
(tipo de sangre/código/fecha) ya NO son de clasica — son universales (test_campos_universales)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _ctx(ajustes=None):
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)


def test_clasica_declara_logo_posiciones():
    from plantillas import catalogo
    m = next(x for x in catalogo() if x.clave == "clasica")
    assert "der" in m.logo_posiciones and "izq" in m.logo_posiciones


def test_clasica_muestra_empresa_y_dni_base():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx())
    assert "Empresa:" in html and "DNI:" in html


def test_clasica_logo_pos_der():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"logo_pos": "der"}))
    assert "flex-end" in html


def test_clasica_logo_pos_izq():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"logo_pos": "izq"}))
    assert "flex-start" in html


def test_clasica_no_recolorea_logo():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"logo_pos": "izq"}))
    assert "brightness(0)" not in html and "invert(" not in html
