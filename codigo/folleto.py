# -*- coding: utf-8 -*-
"""Arma el PDF folleto personalizado: portada con el logo del cliente + páginas con
los modelos (frentes) pintados con su marca. Espejo del folleto de muestras de DISECOD.

armar_pdf(cliente, logo_img, items, ruta_pdf) -> int (número de páginas)
  items: list[(nombre_modelo, orientacion 'V'|'H', PIL.Image del frente)]
Compone cada página como imagen RGB y guarda un PDF multipágina con Pillow."""
import os

from PIL import Image, ImageDraw, ImageFont
from PIL import JpegImagePlugin  # noqa: F401  fuerza registrar Image.SAVE["JPEG"] (PDF RGB usa DCTDecode)

RUTA = os.path.dirname(os.path.abspath(__file__))
PAG = (1240, 1754)            # A4 vertical a ~150 dpi
MARGEN = 70
TINTA = (40, 40, 40)
GRIS = (120, 120, 120)
ACENTO = (0, 120, 200)        # marco/título de portada (neutro de marca DISECOD)


def _fuente(tam, bold=False):
    nombre = "inter-semibold.ttf" if bold else "inter.ttf"
    candidatas = [os.path.join(RUTA, nombre),
                  # fallback a fuentes del sistema (con ñ, tildes y —); el
                  # load_default() bitmap final no cubre esos glifos
                  "seguisb.ttf" if bold else "segoeui.ttf",
                  "arialbd.ttf" if bold else "arial.ttf"]
    for c in candidatas:
        try:
            return ImageFont.truetype(c, tam)
        except Exception:
            pass
    return ImageFont.load_default()


def _centrar_texto(d, txt, font, y, fill, ancho=PAG[0]):
    w = d.textlength(txt, font=font)
    d.text(((ancho - w) // 2, y), txt, font=font, fill=fill)


def _portada(cliente, logo_img):
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    d.rectangle([30, 30, PAG[0] - 30, PAG[1] - 30], outline=ACENTO, width=4)
    # logo del cliente centrado arriba
    if logo_img is not None:
        lg = logo_img.convert("RGBA")
        lg.thumbnail((540, 320))
        pag.paste(lg, ((PAG[0] - lg.width) // 2, 250), lg)
    _centrar_texto(d, "Propuesta de credenciales", _fuente(58, True), 640, TINTA)
    _centrar_texto(d, "para %s" % cliente, _fuente(40), 722, TINTA)
    _centrar_texto(d, "Elige tu modelo — el color se ajusta a tu marca",
                   _fuente(26), 800, GRIS)
    _centrar_texto(d, "DISECOD · www.fotochecks.pe", _fuente(26), PAG[1] - 110, GRIS)
    return pag


def _fuente_display(tam):
    try:
        return ImageFont.truetype(os.path.join(RUTA, "fuente-display.ttf"), tam)
    except Exception:
        return _fuente(tam, True)


def _portada_v2(cliente, logo_img, marca):
    """Portada de agencia: bandas planas con la marca del cliente, logo intacto
    en zona clara, título display. marca=(prim, sec)."""
    prim, sec = marca
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    # banda superior delgada + bloque de color al pie (planos, sin degradados)
    d.rectangle([0, 0, PAG[0], 26], fill=prim)
    d.rectangle([0, PAG[1] - 210, PAG[0], PAG[1]], fill=sec)
    d.rectangle([0, PAG[1] - 224, PAG[0], PAG[1] - 210], fill=prim)
    # zona clara: logo del cliente intacto, grande y centrado
    if logo_img is not None:
        lg = logo_img.convert("RGBA")
        lg.thumbnail((640, 360))
        pag.paste(lg, ((PAG[0] - lg.width) // 2, 300), lg)
    _centrar_texto(d, "Propuesta de credenciales", _fuente_display(72), 800, sec)
    _centrar_texto(d, cliente.upper(), _fuente(54, True), 930, prim)
    _centrar_texto(d, "Diseños seleccionados para tu marca — listos para producir",
                   _fuente(28), 1050, TINTA)
    from datetime import date
    _centrar_texto(d, date.today().strftime("Lima, %d/%m/%Y"), _fuente(24), 1130, GRIS)
    _centrar_texto(d, "DISECOD · fotochecks.pe", _fuente(26, True),
                   PAG[1] - 130, (255, 255, 255))
    return pag


def _grid(items, cols, titulo):
    if not items:
        return []
    paginas = []
    f_t, f_l = _fuente(34, True), _fuente(22)
    ax, ay = MARGEN, MARGEN + 74
    cw = (PAG[0] - 2 * MARGEN) // cols
    # alto de celda según orientación de los items de esta grilla
    es_horiz = items[0][1] == "H"
    cell_h = int(cw * 0.66) if es_horiz else int(cw * 1.46)
    fila_h = cell_h + 54
    rows = max(1, (PAG[1] - ay - MARGEN) // fila_h)
    por_pag = cols * rows
    for p in range(0, len(items), por_pag):
        pag = Image.new("RGB", PAG, "white")
        d = ImageDraw.Draw(pag)
        d.text((MARGEN, MARGEN), titulo, font=f_t, fill=TINTA)
        for i, (nombre, _o, img) in enumerate(items[p:p + por_pag]):
            r, c = divmod(i, cols)
            x = ax + c * cw
            y = ay + r * fila_h
            th = img.convert("RGB").copy()
            th.thumbnail((cw - 30, cell_h - 24))
            pag.paste(th, (x + (cw - th.width) // 2, y))
            lw = d.textlength(nombre, font=f_l)
            d.text((x + (cw - lw) // 2, y + cell_h - 10), nombre, font=f_l, fill=GRIS)
        paginas.append(pag)
    return paginas


def armar_pdf(cliente, logo_img, items, ruta_pdf):
    verticales = [it for it in items if it[1] == "V"]
    horizontales = [it for it in items if it[1] == "H"]
    paginas = [_portada(cliente, logo_img)]
    paginas += _grid(verticales, 3, "Modelos verticales")
    paginas += _grid(horizontales, 2, "Modelos horizontales")
    carpeta = os.path.dirname(os.path.abspath(ruta_pdf))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    paginas[0].save(ruta_pdf, "PDF", save_all=True, append_images=paginas[1:],
                    resolution=150.0, quality=95)
    return len(paginas)
