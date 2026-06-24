# -*- coding: utf-8 -*-
"""Campos extra UNIVERSALES: la franja inferior de _shell muestra tipo de sangre,
código, fecha y web en CUALQUIER modelo, así el editor nunca rebota 'usa otro modelo'."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")

# representativos: base (clasica/premium), verticales (mv4/mv7), horizontales (mh2/mh5)
MODELOS = ["clasica", "premium", "mv4", "mv7", "mh2", "mh5"]


def _ctx(ajustes=None):
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)


def test_sin_campos_no_hay_franja():
    from plantillas import cara
    for clave in MODELOS:
        html, _, _ = cara(clave, "frontal", _ctx())
        assert "cextra" not in html, clave


def test_tipo_sangre_universal_en_todos():
    from plantillas import cara
    for clave in MODELOS:
        html, _, _ = cara(clave, "frontal", _ctx({"campos": {"tipo_sangre": True}}))
        assert "cextra" in html and "T. SANGRE" in html, clave


def test_codigo_y_fecha_universales():
    from plantillas import cara
    html, _, _ = cara("mv4", "frontal", _ctx({"campos": {"codigo": True, "fecha": True}}))
    assert "CÓDIGO" in html and "VENCE" in html


def test_no_recolorea_logo_con_franja():
    from plantillas import cara
    for clave in MODELOS:
        html, _, _ = cara(clave, "frontal", _ctx({"campos": {"tipo_sangre": True, "codigo": True}}))
        assert "brightness(0)" not in html and "invert(" not in html, clave
