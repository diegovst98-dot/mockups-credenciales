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
ACENTO = (0, 120, 200)        # (legado) marco/título de la portada v1

# Colores oficiales DISECOD — el chrome de la propuesta es documento de MARCA
# DISECOD; las credenciales adentro llevan el color del cliente.
LILA = (153, 135, 247)        # #9987F7
LIMA = (231, 248, 73)         # #E7F849 (solo hairline, discreto)
CARBON = (56, 56, 56)         # #383838
BLANCO = (255, 255, 255)


def _logo_disecod_blanco():
    try:
        return Image.open(os.path.join(RUTA, "logo-disecod-blanco.png")).convert("RGBA")
    except Exception:
        return None


def _banda_disecod(pag, alto=150):
    """Banda inferior CARBON con el logo blanco de DISECOD, discreto."""
    d = ImageDraw.Draw(pag)
    y0 = PAG[1] - alto
    d.rectangle([0, y0, PAG[0], PAG[1]], fill=CARBON)
    lg = _logo_disecod_blanco()
    if lg is not None:
        lg = lg.copy()
        lg.thumbnail((320, 46))
        pag.paste(lg, ((PAG[0] - lg.width) // 2, y0 + (alto - lg.height) // 2 - 14), lg)
        _centrar_texto(d, "fotochecks.pe · Lince, Lima", _fuente(22),
                       y0 + alto // 2 + 26, (200, 200, 205))
    else:
        _centrar_texto(d, "DISECOD · fotochecks.pe · Lince, Lima", _fuente(24, True),
                       y0 + alto // 2 - 14, BLANCO)


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
    """Portada de agencia con chrome DISECOD (LILA/CARBON + hairline LIMA):
    la propuesta es documento de marca DISECOD; el color del CLIENTE vive en
    las credenciales de adentro. El logo del cliente sigue protagonista,
    intacto en la zona clara. marca=(prim, sec) queda por compatibilidad."""
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    # banda superior LILA + hairline LIMA fino (planos, sin degradados)
    d.rectangle([0, 0, PAG[0], 26], fill=LILA)
    d.rectangle([0, 26, PAG[0], 31], fill=LIMA)
    # zona clara: logo del cliente intacto, grande y centrado
    if logo_img is not None:
        lg = logo_img.convert("RGBA")
        lg.thumbnail((640, 360))
        pag.paste(lg, ((PAG[0] - lg.width) // 2, 300), lg)
    _centrar_texto(d, "Propuesta de credenciales", _fuente_display(72), 800, CARBON)
    _centrar_texto(d, cliente.upper(), _fuente(54, True), 930, LILA)
    _centrar_texto(d, "Una muestra visual con tu marca: elige tu favorito",
                   _fuente(28), 1040, TINTA)
    _centrar_texto(d, "y lo perfeccionamos contigo antes de imprimir.",
                   _fuente(28), 1082, TINTA)
    from datetime import date
    _centrar_texto(d, date.today().strftime("Lima, %d/%m/%Y"), _fuente(24), 1130, GRIS)
    # banda inferior CARBON con logo blanco DISECOD + hairline LILA encima
    _banda_disecod(pag, alto=210)
    d.rectangle([0, PAG[1] - 224, PAG[0], PAG[1] - 210], fill=LILA)
    return pag


def _pagina_estrella(item, marca):
    """'Nuestra recomendación': un solo modelo, grande y con aire.
    Acentos en chrome DISECOD (LILA/CARBON); marca queda por compatibilidad."""
    nombre, ori, img = item
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    d.rectangle([0, 0, PAG[0], 16], fill=LILA)
    d.text((MARGEN, MARGEN), "Nuestra recomendación", font=_fuente_display(54), fill=CARBON)
    d.text((MARGEN, MARGEN + 78), "El punto de partida que mejor le calza a tu marca",
           font=_fuente(26), fill=GRIS)
    th = img.convert("RGB").copy()
    lado = 920 if ori == "H" else 760
    th.thumbnail((lado, 1150))
    # bloque tarjeta+caption centrado verticalmente en el área libre
    f_cap = _fuente(34, True)
    alto_bloque = th.height + 34 + 42
    y_top = MARGEN + 78 + 60                      # debajo del encabezado
    y0 = y_top + max(0, (PAG[1] - MARGEN - y_top - alto_bloque) // 2)
    pag.paste(th, ((PAG[0] - th.width) // 2, y0))
    y_cap = y0 + th.height + 34
    w = d.textlength(nombre, font=f_cap)
    d.text(((PAG[0] - w) // 2, y_cap), nombre, font=f_cap, fill=TINTA)
    return pag


def _pagina_cta(cliente, marca):
    """Cierre en chrome DISECOD: bloque CARBON + acento LILA + hairline LIMA;
    banda inferior CARBON con logo blanco. marca queda por compatibilidad."""
    pag = Image.new("RGB", PAG, "white")
    d = ImageDraw.Draw(pag)
    d.rectangle([0, PAG[1] // 2 - 200, PAG[0], PAG[1] // 2 + 200], fill=CARBON)
    _centrar_texto(d, "¿Cuál le gustó?", _fuente_display(64), PAG[1] // 2 - 145,
                   BLANCO)
    _centrar_texto(d, "Estos diseños son la base: elija su favorito y lo personalizamos",
                   _fuente(28), PAG[1] // 2 - 45, BLANCO)
    _centrar_texto(d, "con los datos y fotos de su equipo. Verá la muestra final",
                   _fuente(28), PAG[1] // 2 + 5, BLANCO)
    _centrar_texto(d, "y la aprueba ANTES de imprimir — sin costo y sin compromiso.",
                   _fuente(28), PAG[1] // 2 + 55, BLANCO)
    _centrar_texto(d, "Responda este WhatsApp con el nombre del modelo elegido.",
                   _fuente(24), PAG[1] // 2 + 125, (200, 200, 205))
    d.rectangle([0, PAG[1] // 2 + 200, PAG[0], PAG[1] // 2 + 214], fill=LILA)
    d.rectangle([0, PAG[1] // 2 + 214, PAG[0], PAG[1] // 2 + 218], fill=LIMA)
    _banda_disecod(pag, alto=150)
    return pag


def _grid(items, cols, titulo):
    if not items:
        return []
    paginas = []
    f_t, f_l = _fuente(34, True), _fuente(30)
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
        d.rectangle([MARGEN, MARGEN + 48, MARGEN + 56, MARGEN + 54], fill=LILA)
        d.text((MARGEN, MARGEN), titulo, font=f_t, fill=CARBON)
        for i, (nombre, _o, img) in enumerate(items[p:p + por_pag]):
            r, c = divmod(i, cols)
            x = ax + c * cw
            y = ay + r * fila_h
            th = img.convert("RGB").copy()
            th.thumbnail((cw - 60, cell_h - 40))
            pag.paste(th, (x + (cw - th.width) // 2, y))
            lw = d.textlength(nombre, font=f_l)
            d.text((x + (cw - lw) // 2, y + cell_h - 10), nombre, font=f_l, fill=GRIS)
        paginas.append(pag)
    return paginas


def armar_propuesta(cliente, logo_img, estrella, alternativas, ruta_pdf, marca,
                    resto=()):
    """Propuesta de agencia: portada v2 + estrella + alternativas (2 por página
    con aire, caption 30px con nombre comercial) + anexo con el resto del
    catálogo (grilla compacta, opcional) + CTA. Devuelve nº de páginas."""
    paginas = [_portada_v2(cliente, logo_img, marca), _pagina_estrella(estrella, marca)]
    vs = [it for it in alternativas if it[1] == "V"]
    hs = [it for it in alternativas if it[1] == "H"]
    paginas += _grid(vs, 2, "Alternativas — verticales")
    paginas += _grid(hs, 2, "Alternativas — horizontales")
    if resto:
        rvs = [it for it in resto if it[1] == "V"]
        rhs = [it for it in resto if it[1] == "H"]
        paginas += _grid(rvs, 3, "Más modelos de nuestro catálogo — verticales")
        paginas += _grid(rhs, 2, "Más modelos de nuestro catálogo — horizontales")
    paginas.append(_pagina_cta(cliente, marca))
    carpeta = os.path.dirname(os.path.abspath(ruta_pdf))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    paginas[0].save(ruta_pdf, "PDF", save_all=True, append_images=paginas[1:],
                    resolution=150.0, quality=95)
    return len(paginas)


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
