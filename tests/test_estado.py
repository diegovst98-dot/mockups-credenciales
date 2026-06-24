# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))


def test_ajustes_inicial_tiene_llaves_y_defaults():
    from estado import ajustes_inicial, FILAS_DEFAULT
    a = ajustes_inicial("clasica")
    assert a["modelo"] == "clasica"
    assert a["color"] is None
    assert a["logo_pos"] == "default"
    assert a["textos"] == {}
    assert a["filas"] == FILAS_DEFAULT


def test_ajustes_inicial_filas_son_copia():
    from estado import ajustes_inicial, FILAS_DEFAULT
    a = ajustes_inicial("clasica")
    a["filas"].append({"etiqueta": "x", "valor": "y"})
    assert ajustes_inicial("clasica")["filas"] == FILAS_DEFAULT   # no contaminó el default


def test_aplicar_cambios_textos_hace_merge():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("clasica")
    a = aplicar_cambios(a, {"textos": {"nombre": "Juan Pérez"}})
    a = aplicar_cambios(a, {"textos": {"cargo": "Gerente"}})
    assert a["textos"] == {"nombre": "Juan Pérez", "cargo": "Gerente"}


def test_aplicar_cambios_filas_reemplaza():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("clasica")
    nuevas = [{"etiqueta": "Área", "valor": "Logística"}]
    a = aplicar_cambios(a, {"filas": nuevas})
    assert a["filas"] == nuevas


def test_aplicar_cambios_no_muta_el_original():
    from estado import ajustes_inicial, aplicar_cambios
    a = ajustes_inicial("clasica")
    b = aplicar_cambios(a, {"color": "#123456"})
    assert a["color"] is None and b["color"] == "#123456"


def test_filas_validas_limpia_y_descarta_sin_etiqueta():
    from estado import filas_validas
    out = filas_validas([{"etiqueta": " DNI ", "valor": " 123 "},
                         {"etiqueta": "", "valor": "x"},
                         {"etiqueta": "Área", "valor": ""}])
    assert out == [{"etiqueta": "DNI", "valor": "123"}, {"etiqueta": "Área", "valor": ""}]
