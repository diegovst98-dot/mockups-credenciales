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
    """Reescala manteniendo proporción para CABER en w×h (contain, sin deformar). Para logo."""
    w = max(1, int(w))
    h = max(1, int(h))
    out = img.copy()
    out.thumbnail((w, h), Image.LANCZOS)
    return out


def _cubrir(img, w, h):
    """Reescala para LLENAR w×h (cover) y recorta el sobrante al centro. Para fotos:
    llena el marco sin deformar ni dejar bordes."""
    w = max(1, int(w))
    h = max(1, int(h))
    iw, ih = img.size
    escala = max(w / iw, h / ih)
    nw, nh = max(1, int(iw * escala)), max(1, int(ih * escala))
    red = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = (nh - h) // 2
    return red.crop((x, y, x + w, y + h))


def _fuente(peso, tam):
    from motor import fuente            # import diferido: evita ciclo lienzo<->motor
    return fuente(peso, max(8, int(tam)))


def _fit_font(texto, w, h, peso):
    """Devuelve (fuente, (l, t)) con el mayor tamaño cuyo texto entra en w×h.
    (l, t) = offset del bbox para alinear la tinta visible a la esquina sup-izq."""
    tam = max(8, int(h))
    while tam > 8:
        fnt = _fuente(peso, tam)
        l, t, r, b = fnt.getbbox(texto or " ")
        if (r - l) <= w and (b - t) <= h:
            return fnt, (l, t)
        tam = int(tam * 0.92)
    fnt = _fuente(peso, 8)
    l, t, r, b = fnt.getbbox(texto or " ")
    return fnt, (l, t)


def _dibujar_texto(base, cpx, spec, H):
    x0, y0, x1, y1 = cpx
    texto = spec.get("texto", "")
    if not texto:
        return
    w = max(1, x1 - x0)
    # tope de altura de letra = fracción de la tarjeta -> el texto NO se infla aunque la
    # caja sea alta; el ancho de la caja sigue achicando si hace falta.
    h = min(max(1, y1 - y0), spec.get("max_frac", 0.08) * H)
    fnt, (l, t) = _fit_font(texto, w, h, spec.get("peso", 700))
    # alinea la tinta visible a (x0, y0): el bbox del modelo YA es la posición correcta
    ImageDraw.Draw(base).text((x0 - l, y0 - t), texto, font=fnt,
                              fill=tuple(spec.get("color", (30, 30, 30))))


def _dibujar_datos(base, cpx, spec, H):
    x0, y0, x1, y1 = cpx
    filas = [(e, v) for e, v in spec.get("filas", []) if e]
    if not filas:
        return
    w = max(1, x1 - x0)
    # alto de fila acotado: ni estira a llenar la caja con pocas filas, ni desborda
    rowh = min(max(1, y1 - y0) / len(filas), spec.get("max_frac", 0.052) * H)
    d = ImageDraw.Draw(base)
    for i, (etq, val) in enumerate(filas):
        linea = etq + ("  " + val if val else "")
        fnt, (l, t) = _fit_font(linea, w, rowh * 0.92, 700)
        yy = y0 + int(i * rowh)
        d.text((x0 - l, yy - t), etq, font=fnt, fill=tuple(spec.get("color_etq", (30, 110, 80))))
        if val:
            wlbl = d.textlength(etq + "  ", font=fnt)
            d.text((x0 - l + wlbl, yy - t), val, font=fnt, fill=tuple(spec.get("color_val", (40, 40, 40))))


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
            bw, bh = cpx[2] - cpx[0], cpx[3] - cpx[1]
            if spec.get("ajuste") == "cover":
                pieza = _cubrir(spec["img"].convert("RGBA"), bw, bh)
            else:
                pieza = encajar_en(spec["img"].convert("RGBA"), bw, bh)
            ox = cpx[0] + (bw - pieza.width) // 2
            oy = cpx[1] + (bh - pieza.height) // 2
            base.alpha_composite(pieza, (ox, oy))
        elif tipo == "texto":
            _dibujar_texto(base, cpx, spec, H)
        elif tipo == "datos":
            _dibujar_datos(base, cpx, spec, H)
    return base
