# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _ctx(ajustes=None):
    from plantillas import construir_contexto
    from motor import cargar_logo
    return construir_contexto(cargar_logo(LOGO), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)


def test_mv7_declara_tipo_sangre():
    from plantillas import catalogo
    m = next(x for x in catalogo() if x.clave == "mv7")
    assert "tipo_sangre" in m.campos_opcionales


# Nota: "O+" colisiona con el base64; afirmamos sobre la etiqueta "Tipo de sangre".
def test_mv7_sin_campo_no_muestra_sangre():
    from plantillas import cara
    html, _, _ = cara("mv7", "frontal", _ctx())
    assert "Tipo de sangre" not in html


def test_mv7_con_campo_muestra_sangre():
    from plantillas import cara
    html, _, _ = cara("mv7", "frontal", _ctx({"campos": {"tipo_sangre": True}}))
    assert "Tipo de sangre" in html
    assert "brightness(0)" not in html and "invert(" not in html
