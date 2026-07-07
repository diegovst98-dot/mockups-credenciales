# -*- coding: utf-8 -*-
"""Loop de color (iteración N): corre la paleta con logos famosos y arma UNA
hoja de contacto por marca (roles + top-6 renderizado). Uso interno de prueba.
    py tools\\_hoja_famosos.py [tag] [marca1 marca2 ...]
Salida: salida\\_loop\\famosos\\<tag>\\hoja-<marca>.png
"""
import os
import sys

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AQUI, "codigo"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
import motor  # noqa: E402
from plantillas import cara, construir_contexto  # noqa: E402
from plantillas.curaduria import COMBOS, elegir_top, nombre_comercial  # noqa: E402
import render  # noqa: E402

CARPETA = os.path.join(AQUI, "entrada", "famosos")
NOMBRES = {
    "cocacola": "Coca-Cola", "pepsi": "Pepsi", "mcdonalds": "McDonald's",
    "bbva": "BBVA", "bcp": "BCP", "interbank": "Interbank",
    "cinemark": "Cinemark", "spotify": "Spotify", "apple": "Apple", "nike": "Nike",
}
ROLES_ORDEN = ["acc", "prof", "carbon", "claro", "acc2"]


def fnt(tam):
    return ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", tam)


def hoja_marca(marca, destino):
    ruta = os.path.join(CARPETA, marca + ".png")
    logo = motor.cargar_logo(ruta)
    prim, sec = motor.paleta_del_logo(logo)
    prim_m, sec_m = motor.paleta_marca(prim, sec)
    roles = motor.paleta_roles(prim, sec)
    print(f"== {marca}: logo={prim}/{sec}  marca={prim_m}/{sec_m}")
    for r in ROLES_ORDEN:
        print(f"   {r:7s} rgb{roles[r]}")

    top = elegir_top(prim_m)
    items, metas = [], []
    for clave in top:
        c1, c2 = COMBOS.get(clave, ("acc", "prof"))
        ctx = construir_contexto(logo, roles[c1], roles[c2], NOMBRES.get(marca, marca))
        items.append(cara(clave, "frontal", ctx))
        metas.append((clave, c1, c2))
    caras = render.render_caras(items)

    # celda uniforme: encajar cada cara en 420x300
    CW, CH, PAD = 440, 340, 10
    COLS = 3
    filas = (len(caras) + COLS - 1) // COLS
    H_CAB = 96
    hoja = Image.new("RGB", (COLS * CW, H_CAB + filas * CH), (248, 248, 250))
    d = ImageDraw.Draw(hoja)
    d.text((14, 8), f"{NOMBRES.get(marca, marca)} — logo {prim} / {sec}", font=fnt(22), fill=(20, 20, 20))
    x = 14
    for r in ROLES_ORDEN:
        d.rectangle([x, 40, x + 120, 84], fill=roles[r])
        lum = motor.luminancia(roles[r])
        d.text((x + 6, 46), r, font=fnt(15), fill=(255, 255, 255) if lum < 0.5 else (10, 10, 10))
        x += 130
    for i, (img, (clave, c1, c2)) in enumerate(zip(caras, metas)):
        cel = img.copy()
        cel.thumbnail((CW - 2 * PAD, CH - 40), Image.LANCZOS)
        cx = (i % COLS) * CW
        cy = H_CAB + (i // COLS) * CH
        hoja.paste(cel, (cx + (CW - cel.width) // 2, cy + 30))
        estrella = " *ESTRELLA*" if i == 0 else ""
        d.text((cx + PAD, cy + 6), f"{nombre_comercial(clave)} ({clave}: {c1}+{c2}){estrella}",
               font=fnt(16), fill=(30, 30, 30))
    hoja.save(destino)
    print("   ->", destino)


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "iter1"
    marcas = sys.argv[2:] or sorted(NOMBRES)
    base = os.path.join(AQUI, "salida", "_loop", "famosos", tag)
    os.makedirs(base, exist_ok=True)
    for m in marcas:
        hoja_marca(m, os.path.join(base, f"hoja-{m}.png"))


if __name__ == "__main__":
    main()
