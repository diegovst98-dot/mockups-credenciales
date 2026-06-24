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
    assert ctx["cliente"] == "Interbank"
    assert ctx["datos"]["nombre"] == "Carlos González M."   # DATOS demo
    assert ctx["filas"] == []                              # sin filas del vendedor
    assert ctx["logo_pos"] == "default"


def test_textos_override_no_muta_DATOS_global():
    from plantillas import construir_contexto, DATOS
    ajustes = {"textos": {"nombre": "Juan Pérez", "cargo": "Gerente"}}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["datos"]["nombre"] == "Juan Pérez"
    assert ctx["datos"]["cargo"] == "Gerente"
    assert DATOS["nombre"] == "Carlos González M."          # el global NO se tocó


def test_filas_del_vendedor_pasan_al_contexto():
    from plantillas import construir_contexto
    ajustes = {"filas": [{"etiqueta": "DNI", "valor": "123"}, {"etiqueta": "Área", "valor": "Log"}]}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["filas"] == [("DNI", "123"), ("Área", "Log")]


def test_filas_descarta_sin_etiqueta():
    from plantillas import construir_contexto
    ajustes = {"filas": [{"etiqueta": "DNI", "valor": "123"}, {"etiqueta": "  ", "valor": "x"}]}
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", ajustes)
    assert ctx["filas"] == [("DNI", "123")]


def test_empresa_override_cambia_cliente_y_web():
    from plantillas import construir_contexto
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", {"empresa": "Acme SAC"})
    assert ctx["cliente"] == "Acme SAC"
    assert "acme" in ctx["web"]


def test_logo_pos_pasa_al_contexto():
    from plantillas import construir_contexto
    ctx = construir_contexto(_logo(), (0, 164, 80), (0, 90, 44), "Interbank", {"logo_pos": "der"})
    assert ctx["logo_pos"] == "der"
