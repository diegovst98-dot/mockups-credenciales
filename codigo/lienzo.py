# -*- coding: utf-8 -*-
"""Compositor de capas del editor visual. Dado un fondo + capas (cajas normalizadas)
+ recursos (logo/foto/textos/datos), arma la credencial a cualquier resolucion con
Pillow. El MISMO compositor alimenta preview y export => WYSIWYG. Sin tkinter, sin red."""
from PIL import Image, ImageDraw

GUIAS = (0.0, 0.5, 1.0)   # bordes + centro


# ---------- matemática de cajas y snap ----------

def caja_px(caja, W, H):
    """Caja normalizada 0–1 -> (x0, y0, x1, y1) en pixeles enteros."""
    x0 = int(round(caja["x"] * W))
    y0 = int(round(caja["y"] * H))
    x1 = int(round((caja["x"] + caja["w"]) * W))
    y1 = int(round((caja["y"] + caja["h"]) * H))
    return (x0, y0, x1, y1)


def snap(v, guias=GUIAS, umbral=0.02):
    """Pega 'v' a la guía más cercana si está dentro de 'umbral'; si no, lo deja igual."""
    mejor = min(guias, key=lambda g: abs(g - v))
    return mejor if abs(mejor - v) <= umbral else v


# ---------- composición ----------

def encajar_en(img, w, h):
    """Reescala manteniendo proporción para caber en w×h (no deforma logo/foto)."""
    w = max(1, int(w))
    h = max(1, int(h))
    out = img.copy()
    out.thumbnail((w, h), Image.LANCZOS)
    return out


def _fuente(peso, tam):
    from motor import fuente            # import diferido: evita ciclo lienzo<->motor
    return fuente(peso, max(8, int(tam)))


def _dibujar_texto(base, cpx, spec):
    x0, y0, x1, y1 = cpx
    alto = max(8, y1 - y0)
    fnt = _fuente(spec.get("peso", 700), int(alto * 0.8))
    ImageDraw.Draw(base).text((x0, y0), spec.get("texto", ""), font=fnt,
                              fill=tuple(spec.get("color", (30, 30, 30))))


def _dibujar_datos(base, cpx, spec):
    x0, y0, x1, y1 = cpx
    filas = [(e, v) for e, v in spec.get("filas", []) if e]
    if not filas:
        return
    alto_fila = max(10, (y1 - y0) // max(1, len(filas)))
    fnt = _fuente(700, int(alto_fila * 0.62))
    d = ImageDraw.Draw(base)
    y = y0
    for etq, val in filas:
        d.text((x0, y), etq, font=fnt, fill=tuple(spec.get("color_etq", (30, 110, 80))))
        wlbl = d.textlength(etq + "   ", font=fnt)
        if val:
            d.text((x0 + wlbl, y), val, font=fnt, fill=tuple(spec.get("color_val", (40, 40, 40))))
        y += alto_fila


def componer(fondo, capas, recursos, W, H):
    """Compone la credencial: fondo reescalado a W×H + cada capa segun su caja y recurso.
    recursos[id] = {"tipo":"imagen","img":PIL} | {"tipo":"texto","texto":..,"peso":..,"color":..}
                 | {"tipo":"datos","filas":[(etq,val)],"color_etq":..,"color_val":..}"""
    if fondo is not None:
        base = fondo.convert("RGBA").resize((W, H), Image.LANCZOS)
    else:
        base = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    orden = ("datos", "nombre", "cargo", "foto", "logo")   # logo y foto encima del texto
    for cid in [c for c in orden if c in capas and c in recursos]:
        spec = recursos[cid]
        cpx = caja_px(capas[cid], W, H)
        tipo = spec.get("tipo")
        if tipo == "imagen" and spec.get("img") is not None:
            pieza = encajar_en(spec["img"].convert("RGBA"), cpx[2] - cpx[0], cpx[3] - cpx[1])
            base.alpha_composite(pieza, (cpx[0], cpx[1]))
        elif tipo == "texto":
            _dibujar_texto(base, cpx, spec)
        elif tipo == "datos":
            _dibujar_datos(base, cpx, spec)
    return base
