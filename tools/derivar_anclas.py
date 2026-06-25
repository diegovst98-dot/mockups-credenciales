# -*- coding: utf-8 -*-
"""Deriva las anclas (caja nativa de cada elemento) de los 18 modelos por diferencia de
imagen y escribe codigo/anclas.py. Además arma un contact sheet del estado INICIAL
(cada modelo sembrado con sus anclas) para mirar que arranque ordenado.

Uso:  python tools/derivar_anclas.py
"""
import json
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

LOGO = motor.cargar_logo(os.path.join(RECURSOS, "logo-disecod-oscuro.png"))
CLIENTE = "ACME SAC"

anclas = {}
modelos = catalogo()
for i, m in enumerate(modelos, 1):
    a = estado.ajustes_inicial(m.clave)
    try:
        anclas[m.clave] = {k: {kk: round(vv, 4) for kk, vv in box.items()}
                           for k, box in motor.anclas_de_modelo(LOGO, CLIENTE, a).items()}
        print("ancla %2d/%d %s OK" % (i, len(modelos), m.clave))
    except Exception as e:
        print("ancla %2d/%d %s FALLO: %s" % (i, len(modelos), m.clave, e))

# --- escribir codigo/anclas.py ---
destino = os.path.join(CODIGO, "anclas.py")
with open(destino, "w", encoding="utf-8") as f:
    f.write("# -*- coding: utf-8 -*-\n")
    f.write('"""Anclas nativas de cada modelo (caja normalizada por capa), DERIVADAS por\n')
    f.write("tools/derivar_anclas.py. El editor siembra las capas con esto para que cada\n")
    f.write('modelo ARRANQUE ORDENADO (su layout original) y de ahi se edite."""\n')
    f.write("ANCLAS = " + json.dumps(anclas, ensure_ascii=False, indent=0) + "\n")
print("escrito:", destino)

# --- contact sheet del estado inicial ---
COLS, CW, CH, PAD = 4, 480, 360, 12
filas_n = (len(modelos) + COLS - 1) // COLS
hoja = Image.new("RGB", (COLS * CW, filas_n * CH), (250, 250, 252))
draw = ImageDraw.Draw(hoja)
fnt = motor.fuente(700, 22)
for i, m in enumerate(modelos):
    a = estado.ajustes_inicial(m.clave)
    a["capas"] = {k: dict(v) for k, v in anclas.get(m.clave, a["capas"]).items()}
    try:
        img = motor.render_modelo(LOGO, CLIENTE, a, escala=1.0).convert("RGB")
    except Exception as e:
        img = Image.new("RGB", (400, 250), (255, 230, 230))
        ImageDraw.Draw(img).text((10, 10), "FALLO: %s" % e, fill=(150, 0, 0))
    cell = img.copy()
    cell.thumbnail((CW - 2 * PAD, CH - 48), Image.LANCZOS)
    cx = (i % COLS) * CW
    cy = (i // COLS) * CH
    draw.text((cx + PAD, cy + 6), "%s (%s)" % (m.nombre, m.clave), font=fnt, fill=(40, 40, 40))
    hoja.paste(cell, (cx + PAD, cy + 40))
ruta = os.path.join(AQUI, "_contact_anclas.png")
hoja.save(ruta)
print("contact sheet:", ruta, hoja.size)
