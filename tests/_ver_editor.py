# -*- coding: utf-8 -*-
"""Simula lo que el vendedor VE en el lienzo: preview compuesto + recuadros de capa
+ asas (como dibuja _p_dibujar_cajas en el canvas). Solo para mirar el resultado."""
import os
import sys

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
sys.path.insert(0, CODIGO)

from PIL import Image, ImageDraw
import estado
import motor
from plantillas import catalogo

clave = catalogo()[0].clave
logo = motor.cargar_logo(os.path.join(RECURSOS, "logo-disecod-oscuro.png"))
a = estado.ajustes_inicial(clave)
img = motor.render_modelo(logo, "ACME SAC", a, escala=1.0).convert("RGB")
W, H = img.size
d = ImageDraw.Draw(img)

SEL = "logo"   # capa "seleccionada" para el demo
for cid, c in a["capas"].items():
    x0, y0 = c["x"] * W, c["y"] * H
    x1, y1 = (c["x"] + c["w"]) * W, (c["y"] + c["h"]) * H
    sel = (cid == SEL)
    col = (55, 138, 221) if sel else (185, 185, 201)
    d.rectangle([x0, y0, x1, y1], outline=col, width=(3 if sel else 1))
    d.rectangle([x1 - 7, y1 - 7, x1 + 7, y1 + 7], fill=(255, 255, 255), outline=(55, 138, 221), width=2)

ruta = os.path.join(os.path.dirname(__file__), "_ver_editor.png")
img.save(ruta)
print(ruta, img.size)
