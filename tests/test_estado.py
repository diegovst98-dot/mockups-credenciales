# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))


def test_ajustes_inicial_tiene_llaves_y_defaults():
    from estado import ajustes_inicial
    a = ajustes_inicial("clasica")
    assert a["modelo"] == "clasica"
    assert a["color"] is None
    assert a["campos"] == {} and a["textos"] == {}
    assert a["logo_pos"] == "default"


def test_aplicar_cambios_no_muta_el_original():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("clasica")
    b = aplicar_cambios(a, {"color": "#1f7a3d"})
    assert a["color"] is None          # original intacto
    assert b["color"] == "#1f7a3d"


def test_aplicar_cambios_fusiona_campos_y_textos():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("clasica")
    a = aplicar_cambios(a, {"campos": {"tipo_sangre": True}})
    a = aplicar_cambios(a, {"campos": {"codigo": True}})
    a = aplicar_cambios(a, {"textos": {"nombre": "Juan Pérez"}})
    assert a["campos"] == {"tipo_sangre": True, "codigo": True}   # fusiona, no reemplaza
    assert a["textos"] == {"nombre": "Juan Pérez"}


def test_aplicar_cambios_vacio_es_idempotente():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("mv7")
    assert aplicar_cambios(a, {}) == a
    assert aplicar_cambios(a, None) == a
