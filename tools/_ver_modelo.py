# -*- coding: utf-8 -*-
"""Renderiza UN modelo a tamaño completo (como sale en el catálogo) para mirarlo.
Uso: python tools/_ver_modelo.py <clave> <ruta_logo> <salida.png>"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
import estado
import motor

clave, logo_ruta, salida = sys.argv[1], sys.argv[2], sys.argv[3]
logo = motor.cargar_logo(logo_ruta)
a = estado.ajustes_inicial(clave)
motor.render_modelo(logo, "DISECOD", a, escala=1.0).convert("RGB").save(salida)
print("OK", clave, "->", salida)
