# -*- coding: utf-8 -*-
"""Regla fija de diseño: el logo del cliente FLOTA — nunca placas/cajas detrás.
mv3 tuvo un cuadro blanco redondeado tras el logo (background+padding+radius+shadow);
este test impide que vuelva."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "codigo"))

from plantillas.modelos import mv3_banda  # noqa: E402


def _regla_logo():
    m = re.search(r"\.mv3 \.logo\{([^}]*)\}", mv3_banda._CSS)
    assert m, "no se encontró la regla .mv3 .logo en el CSS"
    return m.group(1)


def test_mv3_logo_sin_placa():
    regla = _regla_logo()
    for prohibido in ("background", "box-shadow", "border-radius", "padding"):
        assert prohibido not in regla, (
            "el logo de mv3 lleva '%s': eso es una placa/caja detrás del logo "
            "(regla fija: el logo flota siempre)" % prohibido)
