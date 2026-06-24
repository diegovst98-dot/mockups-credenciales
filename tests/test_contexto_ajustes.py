# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _logo():
    from motor import cargar_logo
    return cargar_logo(LOGO)


def test_sin_ajustes_es_compatible():
    from plantillas import construir_contexto
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank")
    assert ctx["datos"]["nombre"] == "Carlos González M."   # DATOS demo intacto
    assert ctx["campos"] == {}                              # default v2
    assert ctx["logo_pos"] == "default"
    assert ctx["cliente"] == "Interbank"


def test_textos_override_no_muta_DATOS_global():
    from plantillas import construir_contexto, DATOS
    ajustes = {"textos": {"nombre": "Juan Pérez", "cargo": "Gerente"}}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["datos"]["nombre"] == "Juan Pérez"
    assert ctx["datos"]["cargo"] == "Gerente"
    assert ctx["datos"]["id"] == DATOS["id"]                # lo no override se conserva
    assert DATOS["nombre"] == "Carlos González M."          # el global NO se tocó


def test_empresa_override_cambia_cliente_y_web():
    from plantillas import construir_contexto
    ajustes = {"textos": {"empresa": "Acme SAC"}}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["cliente"] == "Acme SAC"
    assert "acme" in ctx["web"]


def test_campos_y_logo_pos_pasan_al_contexto():
    from plantillas import construir_contexto
    ajustes = {"campos": {"tipo_sangre": True}, "logo_pos": "der"}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["campos"] == {"tipo_sangre": True}
    assert ctx["logo_pos"] == "der"
