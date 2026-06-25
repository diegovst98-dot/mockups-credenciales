# -*- coding: utf-8 -*-
"""Contact sheet del estado INICIAL de los 18 modelos (usa anclas ya derivadas + el
shrink-to-fit del compositor). NO re-deriva anclas. Solo para mirar."""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CODIGO = os.path.abspath(os.path.join(AQUI, "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(AQUI, "..", "recursos"))
sys.path.insert(0, CODIGO)

from PIL import Image, ImageDraw
import estado
import motor
from plantillas import catalogo

_cands = [r"C:\Users\Diego\Downloads\LOGO GV (1).png",
          os.path.join(RECURSOS, "logo-disecod-oscuro.png")]
LOGO = motor.cargar_logo(next((c for c in _cands if os.path.exists(c)), _cands[-1]))
CLIENTE = "GV"
modelos = catalogo()

COLS, CW, CH, PAD = 4, 480, 360, 12
filas_n = (len(modelos) + COLS - 1) // COLS
hoja = Image.new("RGB", (COLS * CW, filas_n * CH), (250, 250, 252))
draw = ImageDraw.Draw(hoja)
fnt = motor.fuente(700, 22)
for i, m in enumerate(modelos):
    a = estado.ajustes_inicial(m.clave)           # YA siembra las anclas del modelo
    try:
        img = motor.render_modelo(LOGO, CLIENTE, a, escala=1.0).convert("RGB")
    except Exception as e:
        img = Image.new("RGB", (400, 250), (255, 230, 230))
        ImageDraw.Draw(img).text((10, 10), "FALLO: %s" % e, fill=(150, 0, 0))
    cell = img.copy()
    cell.thumbnail((CW - 2 * PAD, CH - 48), Image.LANCZOS)
    cx, cy = (i % COLS) * CW, (i // COLS) * CH
    draw.text((cx + PAD, cy + 6), "%s (%s)" % (m.nombre, m.clave), font=fnt, fill=(40, 40, 40))
    hoja.paste(cell, (cx + PAD, cy + 40))
ruta = os.path.join(AQUI, "_contact_sheet.png")
hoja.save(ruta)
print("contact sheet:", ruta, hoja.size)
