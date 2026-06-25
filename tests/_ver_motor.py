# -*- coding: utf-8 -*-
"""Render-and-look del motor: fondo del modelo + render_modelo (preview vs export)."""
import os
import sys

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
sys.path.insert(0, CODIGO)

import estado
import motor
from plantillas import catalogo

clave = catalogo()[0].clave
logo = motor.cargar_logo(os.path.join(RECURSOS, "logo-disecod-oscuro.png"))
a = estado.ajustes_inicial(clave)

fondo = motor.fondo_de_modelo(logo, "ACME SAC", a)
fondo.convert("RGB").save(os.path.join(os.path.dirname(__file__), "_fondo.png"))

prev = motor.render_modelo(logo, "ACME SAC", a, escala=0.5)
expo = motor.render_modelo(logo, "ACME SAC", a, escala=1.0)
prev.convert("RGB").save(os.path.join(os.path.dirname(__file__), "_preview.png"))
expo.convert("RGB").save(os.path.join(os.path.dirname(__file__), "_export.png"))

print("modelo:", clave)
print("fondo:", fondo.size, "preview:", prev.size, "export:", expo.size)
