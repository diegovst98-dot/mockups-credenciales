# -*- coding: utf-8 -*-
"""
Motor de mockups de credenciales DISECOD (agente #22, v1).
Recibe el logo de un cliente y genera 3 estilos de fotocheck (frontal + reverso)
+ una lámina de presentación con marco DISECOD. Sin internet, sin APIs: solo Pillow.
"""

import colorsys
import os
import random
import re
import sys
import unicodedata
from datetime import date

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

# ---------- Constantes ----------

CARD_W, CARD_H = 1011, 638          # CR80 a 300 dpi (horizontal)
RADIO = 36                          # esquinas redondeadas
GRIS_DISECOD = (56, 56, 56)         # #383838
LILA = (153, 135, 247)              # #9987F7
VERDE_LIMA = (231, 248, 73)         # #E7F849
DORADO = (201, 164, 92)             # acento de respaldo estilo premium
FONDO_OSCURO = (27, 27, 29)

DATOS = {"nombre": "María Fernández R.", "cargo": "Coordinadora de Operaciones", "id": "ID 00128"}

# Dentro del .exe (PyInstaller): la salida va junto al .exe y los recursos van empaquetados.
if getattr(sys, "frozen", False):
    RUTA_BASE = os.path.dirname(sys.executable)
    RUTA_RECURSOS = os.path.join(getattr(sys, "_MEIPASS", RUTA_BASE), "recursos")
else:
    RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
    RUTA_RECURSOS = os.path.join(RUTA_BASE, "recursos")
LOGO_DISECOD = os.path.join(RUTA_RECURSOS, "logo-disecod-oscuro.png")

_FUENTES = {
    "regular": r"C:\Windows\Fonts\segoeui.ttf",
    "bold": r"C:\Windows\Fonts\segoeuib.ttf",
    "semibold": r"C:\Windows\Fonts\seguisb.ttf",
    "light": r"C:\Windows\Fonts\segoeuil.ttf",
}
_cache_fuentes = {}


def fuente(peso, tam):
    clave = (peso, tam)
    if clave not in _cache_fuentes:
        ruta = _FUENTES.get(peso, _FUENTES["regular"])
        if not os.path.exists(ruta):
            ruta = _FUENTES["regular"]
        _cache_fuentes[clave] = ImageFont.truetype(ruta, tam)
    return _cache_fuentes[clave]


# ---------- Utilidades de color ----------

def luminancia(rgb):
    def canal(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def texto_sobre(rgb):
    """Blanco u oscuro según el fondo, con criterio WCAG."""
    return (255, 255, 255) if luminancia(rgb) < 0.45 else GRIS_DISECOD


def ajustar(rgb, factor):
    """factor < 1 oscurece, > 1 aclara hacia blanco."""
    if factor <= 1:
        return tuple(int(c * factor) for c in rgb[:3])
    return tuple(int(c + (255 - c) * (factor - 1)) for c in rgb[:3])


def saturacion(rgb):
    return colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb[:3]))[1]


def distancia(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])) ** 0.5


# ---------- Logo ----------

def cargar_logo(ruta):
    logo = Image.open(ruta).convert("RGBA")
    # recortar bordes transparentes
    bbox = logo.getchannel("A").getbbox()
    if bbox:
        logo = logo.crop(bbox)
    # recortar bordes blancos (logos JPG sobre fondo blanco)
    gris = Image.composite(logo.convert("L"), Image.new("L", logo.size, 255), logo.getchannel("A"))
    mascara_no_blanco = gris.point(lambda p: 255 if p < 242 else 0)
    bbox = mascara_no_blanco.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    return logo


def paleta_del_logo(logo):
    """Devuelve (primario, secundario). Ignora blancos y pondera saturación."""
    mini = logo.copy()
    mini.thumbnail((160, 160))
    pixeles = [
        (r, g, b) for r, g, b, a in mini.getdata()
        if a > 200 and not (luminancia((r, g, b)) > 0.88 and saturacion((r, g, b)) < 0.12)
    ]
    if not pixeles:
        return GRIS_DISECOD, LILA

    # agrupar colores parecidos
    grupos = []  # [color_representante, conteo]
    for px in pixeles:
        for grupo in grupos:
            if distancia(px, grupo[0]) < 55:
                grupo[1] += 1
                break
        else:
            grupos.append([px, 1])

    def puntaje(grupo):
        return grupo[1] * (0.25 + saturacion(grupo[0]))

    grupos.sort(key=puntaje, reverse=True)
    primario = grupos[0][0]

    secundario = None
    for grupo in grupos[1:]:
        if distancia(grupo[0], primario) > 110 and grupo[1] > len(pixeles) * 0.03:
            secundario = grupo[0]
            break
    if secundario is None:
        secundario = ajustar(primario, 0.55) if luminancia(primario) > 0.35 else ajustar(primario, 1.55)

    # logo monocromo oscuro → respaldo de marca
    if saturacion(primario) < 0.08 and luminancia(primario) < 0.25:
        return GRIS_DISECOD, LILA
    return tuple(primario), tuple(secundario)


def logo_es_oscuro(logo):
    mini = logo.copy()
    mini.thumbnail((120, 120))
    valores = [luminancia((r, g, b)) for r, g, b, a in mini.getdata() if a > 200]
    return (sum(valores) / len(valores) < 0.45) if valores else False


def encajar(img, ancho, alto):
    copia = img.copy()
    copia.thumbnail((ancho, alto), Image.LANCZOS)
    return copia


# ---------- Piezas dibujadas ----------

def tarjeta_base(ancho, alto, color):
    tarjeta = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(tarjeta)
    d.rounded_rectangle([0, 0, ancho - 1, alto - 1], RADIO, fill=color)
    return tarjeta


def mascara_redondeada(ancho, alto):
    m = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, ancho - 1, alto - 1], RADIO, fill=255)
    return m


def gradiente_vertical(ancho, alto, color_arriba, color_abajo):
    franja = Image.new("RGB", (1, 2))
    franja.putpixel((0, 0), color_arriba)
    franja.putpixel((0, 1), color_abajo)
    return franja.resize((ancho, alto), Image.BILINEAR)


def avatar_rect(ancho, alto):
    """Foto carnet genérica: silueta neutra, nada de personas reales."""
    img = Image.new("RGB", (ancho, alto), (221, 227, 234))
    d = ImageDraw.Draw(img)
    cx = ancho // 2
    r_cabeza = int(ancho * 0.23)
    cy_cabeza = int(alto * 0.36)
    color_silueta = (154, 167, 181)
    d.ellipse([cx - r_cabeza, cy_cabeza - r_cabeza, cx + r_cabeza, cy_cabeza + r_cabeza], fill=color_silueta)
    d.ellipse([cx - int(ancho * 0.42), int(alto * 0.62), cx + int(ancho * 0.42), int(alto * 1.25)], fill=color_silueta)
    return img


def avatar_circular(diametro):
    img = avatar_rect(diametro, diametro)
    mascara = Image.new("L", (diametro, diametro), 0)
    ImageDraw.Draw(mascara).ellipse([0, 0, diametro - 1, diametro - 1], fill=255)
    img.putalpha(mascara)
    return img


def pseudo_qr(semilla, tam, fg=(20, 20, 20), bg=(255, 255, 255)):
    """QR decorativo (no escaneable) para que el reverso se vea real."""
    modulos = 21
    rnd = random.Random(semilla)
    celda = max(2, tam // (modulos + 4))
    lado = celda * (modulos + 4)
    img = Image.new("RGB", (lado, lado), bg)
    d = ImageDraw.Draw(img)

    def cuadro(cx, cy, n, color):
        d.rectangle([(cx + 2) * celda, (cy + 2) * celda, (cx + n + 2) * celda - 1, (cy + n + 2) * celda - 1], fill=color)

    for y in range(modulos):
        for x in range(modulos):
            if rnd.random() < 0.45:
                cuadro(x, y, 1, fg)
    # patrones de posición
    for px, py in [(0, 0), (modulos - 7, 0), (0, modulos - 7)]:
        cuadro(px, py, 7, fg)
        cuadro(px + 1, py + 1, 5, bg)
        cuadro(px + 2, py + 2, 3, fg)
    return img.resize((tam, tam), Image.NEAREST)


def chip_logo(logo, ancho_max, alto_max, relleno=28, fondo=(255, 255, 255, 255)):
    """Logo sobre placa redondeada (para asegurar contraste con el fondo de la tarjeta)."""
    interior = encajar(logo, ancho_max - relleno * 2, alto_max - relleno * 2)
    chip = Image.new("RGBA", (interior.width + relleno * 2, interior.height + relleno * 2), (0, 0, 0, 0))
    ImageDraw.Draw(chip).rounded_rectangle([0, 0, chip.width - 1, chip.height - 1], 24, fill=fondo)
    chip.alpha_composite(interior, (relleno, relleno))
    return chip


def logo_es_claro(logo):
    mini = logo.copy()
    mini.thumbnail((120, 120))
    valores = [luminancia((r, g, b)) for r, g, b, a in mini.getdata() if a > 200]
    return (sum(valores) / len(valores) > 0.70) if valores else False


def pegar_logo(canvas, logo, caja, fondo_claro=True):
    """Pega el logo encajado en la caja (x, y, ancho, alto), con placa si hace falta contraste."""
    x, y, ancho, alto = caja
    if fondo_claro and logo_es_claro(logo):
        pieza = chip_logo(logo, ancho, alto, fondo=GRIS_DISECOD + (255,))
    elif not fondo_claro and logo_es_oscuro(logo):
        pieza = chip_logo(logo, ancho, alto)
    else:
        pieza = encajar(logo, ancho, alto)
    canvas.alpha_composite(pieza, (x + (ancho - pieza.width) // 2, y + (alto - pieza.height) // 2))


# ---------- Estilos ----------

def estilo1_frontal(logo, prim, sec, cliente):
    t = tarjeta_base(CARD_W, CARD_H, (255, 255, 255))
    d = ImageDraw.Draw(t)
    # banda superior y filo inferior
    d.rectangle([0, 0, CARD_W, 30], fill=prim)
    d.rectangle([0, CARD_H - 22, CARD_W, CARD_H], fill=sec)
    # logo
    pegar_logo(t, logo, (60, 70, 420, 150), fondo_claro=True)
    # foto
    foto = avatar_rect(260, 330)
    t.paste(foto, (700, 95))
    d.rectangle([700, 95, 960, 425], outline=prim, width=5)
    # textos
    d.text((60, 290), DATOS["nombre"], font=fuente("bold", 56), fill=GRIS_DISECOD)
    d.text((60, 368), DATOS["cargo"], font=fuente("regular", 36), fill=(90, 95, 102))
    d.text((60, 430), cliente, font=fuente("semibold", 30), fill=prim)
    # chip ID
    txt_id = DATOS["id"]
    f_id = fuente("semibold", 30)
    ancho_id = d.textlength(txt_id, font=f_id)
    d.rounded_rectangle([60, 500, 60 + ancho_id + 56, 560], 30, fill=prim)
    d.text((88, 511), txt_id, font=f_id, fill=texto_sobre(prim))
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo1_reverso(logo, prim, sec, cliente):
    t = tarjeta_base(CARD_W, CARD_H, (255, 255, 255))
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, CARD_W, 22], fill=sec)
    d.rectangle([0, CARD_H - 30, CARD_W, CARD_H], fill=prim)
    pegar_logo(t, logo, (CARD_W // 2 - 190, 60, 380, 130), fondo_claro=True)
    d.line([260, 235, CARD_W - 260, 235], fill=prim, width=4)
    qr = pseudo_qr(cliente, 210)
    t.paste(qr, (CARD_W // 2 - 105, 270))
    d.text((CARD_W // 2, 505), "Escanee para validar la credencial",
           font=fuente("regular", 28), fill=(110, 115, 122), anchor="ma")
    d.text((CARD_W // 2, 548), "www.suempresa.com  ·  (01) 000 0000",
           font=fuente("regular", 26), fill=(150, 154, 160), anchor="ma")
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo2_frontal(logo, prim, sec, cliente):
    alto, ancho = CARD_W, CARD_H  # vertical: 638 × 1011
    fondo = gradiente_vertical(ancho, alto, prim, ajustar(prim, 0.62)).convert("RGBA")
    t = Image.new("RGBA", (ancho, alto))
    t.paste(fondo, (0, 0))
    d = ImageDraw.Draw(t)
    # franja diagonal inferior en secundario
    d.polygon([(0, alto - 150), (ancho, alto - 230), (ancho, alto), (0, alto)], fill=sec)
    # chip de logo (placa oscura si el logo es claro)
    fondo_chip = GRIS_DISECOD + (255,) if logo_es_claro(logo) else (255, 255, 255, 255)
    chip = chip_logo(logo, 420, 170, fondo=fondo_chip)
    t.alpha_composite(chip, ((ancho - chip.width) // 2, 55))
    # foto circular con aro
    foto = avatar_circular(300)
    aro = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
    ImageDraw.Draw(aro).ellipse([0, 0, 319, 319], fill=(255, 255, 255, 255))
    t.alpha_composite(aro, ((ancho - 320) // 2, 280))
    t.alpha_composite(foto, ((ancho - 300) // 2, 290))
    # textos
    col_txt = texto_sobre(prim)
    d.text((ancho // 2, 635), DATOS["nombre"], font=fuente("bold", 50), fill=col_txt, anchor="ma")
    d.text((ancho // 2, 705), DATOS["cargo"], font=fuente("regular", 32), fill=col_txt, anchor="ma")
    f_emp = fuente("semibold", 28)
    d.text((ancho // 2, 760), cliente, font=f_emp, fill=col_txt, anchor="ma")
    # pill ID sobre la franja
    f_id = fuente("semibold", 30)
    ancho_id = d.textlength(DATOS["id"], font=f_id)
    x0 = (ancho - ancho_id - 60) // 2
    d.rounded_rectangle([x0, alto - 125, x0 + ancho_id + 60, alto - 63], 31, fill=(255, 255, 255))
    d.text((ancho // 2, alto - 112), DATOS["id"], font=f_id, fill=ajustar(prim, 0.55), anchor="ma")
    t.putalpha(mascara_redondeada(ancho, alto))
    return t


def estilo2_reverso(logo, prim, sec, cliente):
    alto, ancho = CARD_W, CARD_H
    t = Image.new("RGBA", (ancho, alto))
    t.paste(Image.new("RGB", (ancho, alto), ajustar(prim, 0.55)), (0, 0))
    d = ImageDraw.Draw(t)
    d.polygon([(0, 0), (ancho, 0), (ancho, 90), (0, 170)], fill=sec)
    fondo_chip = GRIS_DISECOD + (255,) if logo_es_claro(logo) else (255, 255, 255, 255)
    chip = chip_logo(logo, 380, 150, fondo=fondo_chip)
    t.alpha_composite(chip, ((ancho - chip.width) // 2, 230))
    caja_qr = Image.new("RGBA", (260, 260), (255, 255, 255, 255))
    caja_qr.paste(pseudo_qr(cliente + "-r", 220), (20, 20))
    t.alpha_composite(caja_qr, ((ancho - 260) // 2, 470))
    col_txt = texto_sobre(ajustar(prim, 0.55))
    d.text((ancho // 2, 790), "Credencial de identificación", font=fuente("regular", 28), fill=col_txt, anchor="ma")
    d.text((ancho // 2, 838), "www.suempresa.com", font=fuente("semibold", 30), fill=col_txt, anchor="ma")
    t.putalpha(mascara_redondeada(ancho, alto))
    return t


def estilo3_frontal(logo, prim, sec, cliente):
    acento = prim if saturacion(prim) > 0.22 else DORADO
    t = tarjeta_base(CARD_W, CARD_H, FONDO_OSCURO)
    d = ImageDraw.Draw(t)
    pegar_logo(t, logo, (70, 80, 380, 160), fondo_claro=False)
    d.line([74, 290, 254, 290], fill=acento, width=6)
    d.text((74, 330), DATOS["nombre"], font=fuente("bold", 52), fill=(244, 244, 246))
    d.text((74, 404), DATOS["cargo"], font=fuente("regular", 34), fill=(170, 174, 182))
    d.text((74, 470), cliente, font=fuente("semibold", 28), fill=acento)
    d.text((74, 540), DATOS["id"], font=fuente("light", 30), fill=(140, 144, 152))
    foto = avatar_circular(280)
    aro = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(aro).ellipse([0, 0, 299, 299], outline=acento, width=8)
    t.alpha_composite(foto, (660, 170))
    t.alpha_composite(aro, (650, 160))
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo3_reverso(logo, prim, sec, cliente):
    acento = prim if saturacion(prim) > 0.22 else DORADO
    t = tarjeta_base(CARD_W, CARD_H, FONDO_OSCURO)
    d = ImageDraw.Draw(t)
    d.rounded_rectangle([24, 24, CARD_W - 24, CARD_H - 24], 26, outline=acento, width=3)
    pegar_logo(t, logo, (CARD_W // 2 - 170, 130, 340, 150), fondo_claro=False)
    d.line([CARD_W // 2 - 90, 330, CARD_W // 2 + 90, 330], fill=acento, width=4)
    d.text((CARD_W // 2, 380), "Esta credencial es personal e intransferible.",
           font=fuente("regular", 26), fill=(170, 174, 182), anchor="ma")
    d.text((CARD_W // 2, 430), "www.suempresa.com", font=fuente("semibold", 28), fill=(220, 222, 228), anchor="ma")
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


ESTILOS = [
    ("Estilo 1 — Corporativo", estilo1_frontal, estilo1_reverso),
    ("Estilo 2 — Full color", estilo2_frontal, estilo2_reverso),
    ("Estilo 3 — Premium", estilo3_frontal, estilo3_reverso),
]


# ---------- Composición de salidas ----------

def con_sombra(canvas, pieza, xy, radio_sombra=18, alpha=70):
    x, y = xy
    sombra = Image.new("RGBA", (pieza.width + 80, pieza.height + 80), (0, 0, 0, 0))
    nucleo = Image.new("RGBA", pieza.size, (0, 0, 0, alpha))
    nucleo.putalpha(pieza.getchannel("A").point(lambda p: alpha if p > 10 else 0))
    sombra.alpha_composite(nucleo, (40, 40))
    sombra = sombra.filter(ImageFilter.GaussianBlur(radio_sombra))
    canvas.alpha_composite(sombra, (x - 40 + 8, y - 40 + 12))
    canvas.alpha_composite(pieza, (x, y))


def png_estilo(titulo, frontal, reverso):
    margen, sep, etiqueta_h = 70, 70, 90
    ancho = frontal.width + reverso.width + margen * 2 + sep
    alto = max(frontal.height, reverso.height) + margen + etiqueta_h + 50
    canvas = Image.new("RGBA", (ancho, alto), (247, 247, 248, 255))
    d = ImageDraw.Draw(canvas)
    d.text((margen, 28), titulo, font=fuente("bold", 40), fill=GRIS_DISECOD)
    for img, x, rotulo in [(frontal, margen, "FRONTAL"), (reverso, margen + frontal.width + sep, "REVERSO")]:
        con_sombra(canvas, img, (x, etiqueta_h + 20))
        d.text((x + img.width // 2, etiqueta_h - 18), rotulo, font=fuente("semibold", 24), fill=(150, 154, 160), anchor="ma")
    return canvas.convert("RGB")


def lamina(cliente, piezas):
    """piezas: lista de (titulo, frontal, reverso). Lámina con marco DISECOD."""
    ANCHO = 2300
    col_w = (ANCHO - 4 * 70) // 3
    esc_h = 0.55  # escala tarjetas horizontales

    canvas = Image.new("RGBA", (ANCHO, 1640), (247, 247, 248, 255))
    d = ImageDraw.Draw(canvas)

    # cabecera
    d.rectangle([0, 0, ANCHO, 170], fill=GRIS_DISECOD)
    d.rectangle([0, 170, ANCHO, 182], fill=LILA)
    if os.path.exists(LOGO_DISECOD):
        logo_d = encajar(Image.open(LOGO_DISECOD).convert("RGBA"), 380, 96)
        canvas.alpha_composite(logo_d, (70, (170 - logo_d.height) // 2))
    d.text((ANCHO - 70, 52), f"Propuesta de fotochecks — {cliente}",
           font=fuente("bold", 52), fill=(255, 255, 255), anchor="ra")
    d.text((ANCHO - 70, 118), date.today().strftime("Lima, %d/%m/%Y"),
           font=fuente("regular", 30), fill=VERDE_LIMA, anchor="ra")

    # columnas
    y_top = 250
    for i, (titulo, frontal, reverso) in enumerate(piezas):
        x0 = 70 + i * (col_w + 70)
        d.text((x0 + col_w // 2, y_top - 48), titulo, font=fuente("semibold", 32), fill=GRIS_DISECOD, anchor="ma")
        if frontal.width > frontal.height:  # horizontal: apiladas
            fr = frontal.resize((int(frontal.width * esc_h), int(frontal.height * esc_h)), Image.LANCZOS)
            rv = reverso.resize((int(reverso.width * esc_h), int(reverso.height * esc_h)), Image.LANCZOS)
            con_sombra(canvas, fr, (x0 + (col_w - fr.width) // 2, y_top + 30), 14, 60)
            con_sombra(canvas, rv, (x0 + (col_w - rv.width) // 2, y_top + 30 + fr.height + 70), 14, 60)
        else:  # vertical: lado a lado
            esc = (col_w - 50) / (frontal.width * 2)
            fr = frontal.resize((int(frontal.width * esc), int(frontal.height * esc)), Image.LANCZOS)
            rv = reverso.resize((int(reverso.width * esc), int(reverso.height * esc)), Image.LANCZOS)
            con_sombra(canvas, fr, (x0, y_top + 60), 14, 60)
            con_sombra(canvas, rv, (x0 + fr.width + 50, y_top + 60), 14, 60)

    # pie
    d.rectangle([0, 1640 - 120, ANCHO, 1640 - 116], fill=LILA)
    d.text((ANCHO // 2, 1640 - 86),
           "DISECOD — Fotochecks e impresoras EVOLIS",
           font=fuente("semibold", 32), fill=GRIS_DISECOD, anchor="ma")
    d.text((ANCHO // 2, 1640 - 42),
           "www.fotochecks.pe   ·   ventas@disecod.com   ·   Av. Arenales 1912 Of. 1304, Lince",
           font=fuente("regular", 26), fill=(110, 115, 122), anchor="ma")
    return canvas.convert("RGB")


# ---------- Orquestación ----------

def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", texto).strip("-") or "Cliente"


def generar(ruta_logo, cliente, carpeta_salida=None):
    cliente = (cliente or "Cliente").strip() or "Cliente"
    logo = cargar_logo(ruta_logo)
    prim, sec = paleta_del_logo(logo)

    piezas = []
    for titulo, fn_frontal, fn_reverso in ESTILOS:
        piezas.append((titulo, fn_frontal(logo, prim, sec, cliente), fn_reverso(logo, prim, sec, cliente)))

    if carpeta_salida is None:
        carpeta_salida = os.path.join(RUTA_BASE, "salida", f"{slug(cliente)}-{date.today():%Y-%m-%d}")
    os.makedirs(carpeta_salida, exist_ok=True)

    rutas = []
    nombres = ["estilo-1-corporativo.png", "estilo-2-fullcolor.png", "estilo-3-premium.png"]
    for (titulo, fr, rv), nombre in zip(piezas, nombres):
        ruta = os.path.join(carpeta_salida, nombre)
        png_estilo(titulo, fr, rv).save(ruta, optimize=True)
        rutas.append(ruta)

    ruta_lamina = os.path.join(carpeta_salida, "lamina-presentacion.png")
    lamina(cliente, piezas).save(ruta_lamina, optimize=True)
    rutas.insert(0, ruta_lamina)
    return carpeta_salida, rutas


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Uso: py motor.py "ruta\\al\\logo.png" "Nombre del Cliente"')
        sys.exit(1)
    carpeta, archivos = generar(sys.argv[1], sys.argv[2])
    print(f"Listo: {carpeta}")
    for a in archivos:
        print(" -", os.path.basename(a))
