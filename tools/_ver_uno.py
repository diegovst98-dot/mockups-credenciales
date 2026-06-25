# -*- coding: utf-8 -*-
"""Render de modelos puntuales con logo a color, para mirar contraste/posiciones."""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CODIGO = os.path.abspath(os.path.join(AQUI, "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(AQUI, "..", "recursos"))
sys.path.insert(0, CODIGO)

from PIL import Image
import estado
import motor

CLAVES = sys.argv[1:] or ["mh3", "mv6"]
# logo a color si está; si no, el de prueba
cands = [r"C:\Users\Diego\Downloads\LOGO GV (1).png",
         os.path.join(RECURSOS, "logo-disecod-oscuro.png")]
logo_ruta = next((c for c in cands if os.path.exists(c)), cands[-1])
logo = motor.cargar_logo(logo_ruta)

imgs = []
for clave in CLAVES:
    a = estado.ajustes_inicial(clave)
    imgs.append((clave, motor.render_modelo(logo, "GV", a, escala=1.0).convert("RGB")))

ancho = max(i.width for _, i in imgs) + 20
alto = sum(i.height for _, i in imgs) + 20 * len(imgs)
hoja = Image.new("RGB", (ancho, alto), (245, 245, 248))
y = 10
for clave, im in imgs:
    hoja.paste(im, (10, y))
    y += im.height + 20
ruta = os.path.join(AQUI, "_ver_uno.png")
hoja.save(ruta)
print("logo:", os.path.basename(logo_ruta), "| modelos:", CLAVES, "->", ruta)
