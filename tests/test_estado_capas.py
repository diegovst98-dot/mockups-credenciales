# -*- coding: utf-8 -*-
"""Modelo de datos de capas del editor visual + persistencia de cotización (puro)."""
import json
import os
import sys

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
sys.path.insert(0, CODIGO)

import estado


# ---- Task 1: modelo de capas ----

def test_ajustes_inicial_trae_capas():
    a = estado.ajustes_inicial("clasica")
    assert set(a["capas"]) == set(estado.CAPAS_IDS)
    for caja in a["capas"].values():
        assert {"x", "y", "w", "h"} <= set(caja)


def test_mover_capa_copia_y_marca_movido():
    a = estado.ajustes_inicial("clasica")
    b = estado.mover_capa(a, "logo", x=0.5, y=0.5)
    assert b["capas"]["logo"]["x"] == 0.5 and b["capas"]["logo"]["y"] == 0.5
    assert b["capas"]["logo"].get("movido") is True
    assert not a["capas"]["logo"].get("movido")        # no mutó el original (copia)


def test_mover_capa_clampa_a_0_1():
    a = estado.ajustes_inicial("clasica")
    b = estado.mover_capa(a, "logo", x=-0.3, w=2.0)
    assert b["capas"]["logo"]["x"] == 0.0
    assert b["capas"]["logo"]["w"] == 1.0


# ---- Task 2: persistencia ----

def test_serializar_y_volver_es_identico():
    a = estado.ajustes_inicial("clasica")
    a = estado.mover_capa(a, "logo", x=0.1, y=0.2)
    data = estado.serializar(a, "ACME SAC", r"C:\logos\acme.png", None)
    txt = json.dumps(data)                              # debe ser JSON-safe
    vuelto = estado.deserializar(json.loads(txt))
    assert vuelto["ajustes"]["capas"]["logo"]["x"] == 0.1
    assert vuelto["empresa"] == "ACME SAC"
    assert vuelto["logo_ruta"].endswith("acme.png")


def test_deserializar_tolera_cotizacion_vieja():
    vuelto = estado.deserializar({"ajustes": {"modelo": "clasica"}})
    assert "capas" in vuelto["ajustes"]                 # rellena capas faltantes
    assert vuelto["empresa"] == ""
