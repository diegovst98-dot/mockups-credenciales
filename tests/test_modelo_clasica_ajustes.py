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


def test_clasica_declara_capacidades():
    from plantillas import catalogo
    m = next(x for x in catalogo() if x.clave == "clasica")
    assert "tipo_sangre" in m.campos_opcionales
    assert "codigo" in m.campos_opcionales
    assert "der" in m.logo_posiciones


# Nota: el VALOR "O+" es muy corto y colisiona con el base64 del logo/foto, así que
# afirmamos sobre la ETIQUETA de la fila ("T. Sangre", "Código"), que es única y no
# aparece en el base64 ni en el CSS — marcador robusto de que la fila se renderizó.

def test_clasica_sin_campos_no_muestra_extras():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx())
    assert "T. Sangre" not in html
    assert "Código" not in html and "Codigo" not in html


def test_clasica_con_tipo_sangre_lo_muestra():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"campos": {"tipo_sangre": True}}))
    assert "T. Sangre" in html


def test_clasica_con_codigo_lo_muestra():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"campos": {"codigo": True}}))
    assert "Código" in html


def test_clasica_logo_pos_der_cambia_alineacion():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"logo_pos": "der"}))
    assert "flex-end" in html


def test_clasica_no_recolorea_logo_con_ajustes():
    from plantillas import cara
    html, _, _ = cara("clasica", "frontal", _ctx({"campos": {"tipo_sangre": True}, "logo_pos": "izq"}))
    assert "brightness(0)" not in html and "invert(" not in html
