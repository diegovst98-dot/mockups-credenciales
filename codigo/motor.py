# -*- coding: utf-8 -*-
"""
Motor de mockups de credenciales DISECOD (agente #22, v2 visual).
Recibe el logo de un cliente y genera 3 estilos de fotocheck (frontal + reverso)
+ una lámina de presentación con marco DISECOD. Sin internet, sin APIs: solo Pillow.

v2: foto carnet realista (rostro sintético, no es persona real), logo como marca
de agua, ondas y acentos dorados, tipografía Playfair Display (OFL) e iconografía.
Los assets (fuente-display.ttf, foto-persona.jpg) viven en codigo/ para que el
auto-update del launcher los reparta; si faltan, todo degrada con elegancia
(Palatino/Georgia/Segoe y silueta neutra).
"""

import colorsys
import math
import os
import random
import re
import sys
import unicodedata
from datetime import date

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

# ---------- Constantes ----------

CARD_W, CARD_H = 1011, 638          # CR80 a 300 dpi (horizontal)
V_W, V_H = CARD_H, CARD_W           # vertical
RADIO = 36                          # esquinas redondeadas
GRIS_DISECOD = (56, 56, 56)         # #383838
LILA = (153, 135, 247)              # #9987F7
VERDE_LIMA = (231, 248, 73)         # #E7F849
FONDO_OSCURO = (26, 26, 29)

ORO = (197, 158, 84)                # acento metálico estándar
ORO_CLARO = (233, 207, 146)
ORO_OSCURO = (158, 120, 53)
MARFIL = (250, 247, 242)
TINTA = (40, 42, 46)                # texto principal sobre claro

DATOS = {"nombre": "Carlos González M.", "cargo": "Supervisor de Operaciones", "id": "DNI 45678123"}

# Este archivo vive en codigo/ y se actualiza solo desde GitHub (ver launcher.py).
# La salida va junto al .exe; los recursos van dentro del .exe, con override externo.
if getattr(sys, "frozen", False):
    RUTA_BASE = os.path.dirname(sys.executable)
    RUTA_RECURSOS = os.path.join(getattr(sys, "_MEIPASS", RUTA_BASE), "recursos")
else:
    RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RUTA_RECURSOS = os.path.join(RUTA_BASE, "recursos")
# Si hay carpeta recursos/ al lado del exe, manda ella (se puede actualizar sin recompilar)
_recursos_externos = os.path.join(RUTA_BASE, "recursos")
if os.path.isdir(_recursos_externos):
    RUTA_RECURSOS = _recursos_externos
LOGO_DISECOD = os.path.join(RUTA_RECURSOS, "logo-disecod-oscuro.png")

# Assets v2: viajan dentro de codigo/ para llegar por auto-update sin recompilar el exe
RUTA_CODIGO = os.path.dirname(os.path.abspath(__file__))
FUENTE_DISPLAY = os.path.join(RUTA_CODIGO, "fuente-display.ttf")
FUENTE_DISPLAY_ITALIC = os.path.join(RUTA_CODIGO, "fuente-display-italic.ttf")
FOTO_PERSONA = os.path.join(RUTA_CODIGO, "foto-persona.jpg")

_FUENTES = {
    "regular": r"C:\Windows\Fonts\segoeui.ttf",
    "bold": r"C:\Windows\Fonts\segoeuib.ttf",
    "semibold": r"C:\Windows\Fonts\seguisb.ttf",
    "light": r"C:\Windows\Fonts\segoeuil.ttf",
}
_PESOS_DISPLAY = {"display": 560, "display-bold": 720, "display-black": 850, "display-italic": 540}
_RESPALDO_DISPLAY = [r"C:\Windows\Fonts\palab.ttf", r"C:\Windows\Fonts\georgiab.ttf"]
_cache_fuentes = {}


def fuente(peso, tam):
    clave = (peso, tam)
    if clave in _cache_fuentes:
        return _cache_fuentes[clave]
    if peso in _PESOS_DISPLAY:
        ruta = FUENTE_DISPLAY_ITALIC if peso == "display-italic" else FUENTE_DISPLAY
        if os.path.exists(ruta):
            f = ImageFont.FreeTypeFont(ruta, tam)  # instancia propia: la variación es por-objeto
            try:
                f.set_variation_by_axes([_PESOS_DISPLAY[peso]])
            except Exception:
                pass
        else:
            f = None
            for respaldo in _RESPALDO_DISPLAY:
                if os.path.exists(respaldo):
                    f = ImageFont.truetype(respaldo, tam)
                    break
            if f is None:
                f = ImageFont.truetype(_FUENTES["bold"], tam)
        _cache_fuentes[clave] = f
        return f
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


def mezcla(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1[:3], c2[:3]))


def saturacion(rgb):
    return colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb[:3]))[1]


def marca_legible(rgb, tope=0.32):
    """Oscurece un color de marca hasta que sea legible sobre fondo claro
    (logos pastel → texto lavado si se usa el color tal cual)."""
    c = tuple(rgb[:3])
    for _ in range(6):
        if luminancia(c) <= tope:
            break
        c = ajustar(c, 0.82)
    return c


def distancia(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])) ** 0.5


# ---------- Logo ----------

def _quitar_fondo_claro(logo):
    """Logos JPG/opacos con fondo claro uniforme: vuelve el fondo transparente
    para que el logo FLOTE sobre la tarjeta (nunca un rectángulo de fondo propio)."""
    W, H = logo.size
    esquinas = []
    for caja in [(0, 0, 14, 14), (W - 14, 0, W, 14), (0, H - 14, 14, H), (W - 14, H - 14, W, H)]:
        esquinas += list(logo.crop(caja).convert("RGB").getdata())
    bg = tuple(sum(c) // len(esquinas) for c in zip(*esquinas))
    # solo actuar si el fondo es claro, poco saturado y uniforme (si el fondo es
    # un color de marca, es parte del diseño del logo y se respeta). Esquinas
    # perfectamente uniformes = fondo de estudio seguro → se acepta menos claro.
    if saturacion(bg) > 0.20:
        return logo
    var = max(distancia(px, bg) for px in esquinas[::7])
    if var > 42:
        return logo
    if luminancia(bg) < (0.60 if var <= 12 else 0.80):
        return logo
    dif = ImageChops.difference(logo.convert("RGB"), Image.new("RGB", (W, H), bg)).convert("L")
    # banda suave: parecido al fondo → transparente; distinto → opaco
    alfa = dif.point(lambda p: 0 if p <= 10 else (255 if p >= 32 else (p - 10) * 255 // 22))
    resultado = logo.copy()
    resultado.putalpha(ImageChops.multiply(logo.getchannel("A"), alfa))
    return resultado


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
    # logos opacos → quitar el fondo claro para que floten sobre la tarjeta
    if not tiene_transparencia(logo):
        logo = _quitar_fondo_claro(logo)
        bbox = logo.getchannel("A").getbbox()
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


def oro_del_logo(logo):
    """Si el logo trae tonos dorados/cobrizos, usarlos como acento; si no, oro estándar."""
    mini = logo.copy()
    mini.thumbnail((140, 140))
    dorados, total = [], 0
    for r, g, b, a in mini.getdata():
        if a < 200:
            continue
        total += 1
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        if 0.075 <= h <= 0.155 and s > 0.25 and v > 0.42:
            dorados.append((r, g, b))
    if total and len(dorados) > total * 0.02:
        promedio = tuple(sum(c) // len(dorados) for c in zip(*dorados))
        return mezcla(promedio, ORO, 0.45)
    return ORO


def tiene_transparencia(img):
    a = img.getchannel("A")
    datos = list(a.getdata())
    return sum(1 for p in datos if p < 60) > len(datos) * 0.05


def logo_es_oscuro(logo):
    """Solo cuenta la 'tinta' del logo (ignora el blanco interior/de fondo)."""
    mini = logo.copy()
    mini.thumbnail((120, 120))
    valores = [luminancia((r, g, b)) for r, g, b, a in mini.getdata() if a > 200]
    if not valores:
        return False
    tinta = [v for v in valores if v < 0.92]
    if len(tinta) < len(valores) * 0.02:
        return False  # prácticamente todo blanco → logo claro, no oscuro
    return sum(tinta) / len(tinta) < 0.45


def logo_es_claro(logo):
    """Solo cuenta la 'tinta' del logo: el blanco interior/de fondo no debe
    disparar la placa de contraste (caso Unilever: azul sobre blanco)."""
    mini = logo.copy()
    mini.thumbnail((120, 120))
    valores = [luminancia((r, g, b)) for r, g, b, a in mini.getdata() if a > 200]
    if not valores:
        return False
    tinta = [v for v in valores if v < 0.92]
    if len(tinta) < len(valores) * 0.02:
        return True  # prácticamente todo blanco → logo blanco de verdad
    return sum(tinta) / len(tinta) > 0.70


def encajar(img, ancho, alto):
    copia = img.copy()
    copia.thumbnail((ancho, alto), Image.LANCZOS)
    return copia


# ---------- Piezas dibujadas ----------

def mascara_redondeada(ancho, alto):
    m = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, ancho - 1, alto - 1], RADIO, fill=255)
    return m


def gradiente_vertical(ancho, alto, color_arriba, color_abajo):
    franja = Image.new("RGB", (1, 2))
    franja.putpixel((0, 0), tuple(color_arriba[:3]))
    franja.putpixel((0, 1), tuple(color_abajo[:3]))
    return franja.resize((ancho, alto), Image.BILINEAR)


def gradiente_3(ancho, alto, c_arriba, c_medio, c_abajo, corte=0.45):
    h1 = max(1, int(alto * corte))
    g = Image.new("RGB", (ancho, alto))
    g.paste(gradiente_vertical(ancho, h1, c_arriba, c_medio), (0, 0))
    g.paste(gradiente_vertical(ancho, alto - h1, c_medio, c_abajo), (0, h1))
    return g


def gradiente_diagonal(ancho, alto, c1, c2):
    n = 96
    mini = Image.new("RGB", (n, n))
    px = mini.load()
    for y in range(n):
        for x in range(n):
            px[x, y] = mezcla(c1, c2, (x + y) / (2 * n - 2))
    return mini.resize((ancho, alto), Image.BILINEAR)


def capa_onda(ancho, alto, color, alpha, y_base, amplitud, ciclos=1.3, fase=0.0, grosor=0, invertida=False):
    """Onda suave (supersampleada). grosor=0 rellena hasta abajo (o hasta arriba
    si invertida=True); grosor>0 dibuja una banda."""
    SS = 2
    W, H = ancho * SS, alto * SS
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    pts = []
    n = 72
    for i in range(n + 1):
        t = i / n
        y = (y_base
             + amplitud * math.sin(2 * math.pi * (ciclos * t + fase))
             + amplitud * 0.45 * math.sin(2 * math.pi * (2.6 * ciclos * t + fase * 2.0 + 0.55)))
        pts.append((W * t, y * SS))
    if grosor:
        d.polygon(pts + [(x, y + grosor * SS) for x, y in reversed(pts)], fill=tuple(color[:3]) + (alpha,))
    elif invertida:
        d.polygon(pts + [(W, 0), (0, 0)], fill=tuple(color[:3]) + (alpha,))
    else:
        d.polygon(pts + [(W, H), (0, H)], fill=tuple(color[:3]) + (alpha,))
    return capa.resize((ancho, alto), Image.LANCZOS)


def mascara_silueta(img):
    """Máscara de la forma del logo: alpha real si lo tiene, si no luminancia invertida."""
    a = img.getchannel("A")
    datos = list(a.getdata())
    transparentes = sum(1 for p in datos if p < 60)
    if transparentes > len(datos) * 0.05:
        return a
    return ImageOps.invert(img.convert("L"))


def marca_agua(logo, ancho, color, alpha):
    """El logo como arte de fondo: silueta teñida al color de marca, sutil."""
    escala = ancho / logo.width
    copia = logo.resize((ancho, max(1, int(logo.height * escala))), Image.LANCZOS)
    mascara = mascara_silueta(copia).point(lambda p: p * alpha // 255)
    capa = Image.new("RGBA", copia.size, tuple(color[:3]) + (0,))
    capa.putalpha(mascara)
    return capa.filter(ImageFilter.GaussianBlur(0.6))


def avatar_rect(ancho, alto):
    """Respaldo si falta foto-persona.jpg: silueta neutra."""
    img = Image.new("RGB", (ancho, alto), (221, 227, 234))
    d = ImageDraw.Draw(img)
    cx = ancho // 2
    r_cabeza = int(ancho * 0.23)
    cy_cabeza = int(alto * 0.36)
    color_silueta = (154, 167, 181)
    d.ellipse([cx - r_cabeza, cy_cabeza - r_cabeza, cx + r_cabeza, cy_cabeza + r_cabeza], fill=color_silueta)
    d.ellipse([cx - int(ancho * 0.42), int(alto * 0.62), cx + int(ancho * 0.42), int(alto * 1.25)], fill=color_silueta)
    return img


_foto_cache = {}


def foto_carnet(ancho, alto):
    """Foto carnet rectangular: rostro sintético empaquetado (no es una persona
    real). El asset trae aire alrededor; aquí se recorta al encuadre carnet."""
    clave = (ancho, alto)
    if clave not in _foto_cache:
        if os.path.exists(FOTO_PERSONA):
            img = Image.open(FOTO_PERSONA).convert("RGB")
            W, H = img.size
            img = img.crop((int(W * 0.16), int(H * 0.03), int(W * 0.84), H))
            img = ImageOps.fit(img, (ancho, alto), Image.LANCZOS, centering=(0.5, 0.32))
        else:
            img = avatar_rect(ancho, alto)
        _foto_cache[clave] = img
    return _foto_cache[clave].copy()


def _mascara_suave(ancho, alto, dibujo):
    SS = 4
    m = Image.new("L", (ancho * SS, alto * SS), 0)
    dibujo(ImageDraw.Draw(m), ancho * SS, alto * SS)
    return m.resize((ancho, alto), Image.LANCZOS)


def foto_redondeada(ancho, alto, radio=16):
    img = foto_carnet(ancho, alto).convert("RGBA")
    img.putalpha(_mascara_suave(ancho, alto, lambda d, w, h: d.rounded_rectangle([0, 0, w - 1, h - 1], radio * 4, fill=255)))
    return img


def _sombra_interna_circular(diametro, alpha=55):
    """Leve oscurecimiento del borde: da profundidad y funde el fondo extendido."""
    n = 128
    m = Image.new("L", (n, n), 0)
    px = m.load()
    c = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            r = ((x - c) ** 2 + (y - c) ** 2) ** 0.5 / c
            px[x, y] = 0 if r > 1 else int(alpha * max(0.0, (r - 0.72) / 0.28))
    capa = Image.new("RGBA", (diametro, diametro), (10, 10, 12, 0))
    capa.putalpha(m.resize((diametro, diametro), Image.LANCZOS))
    return capa


def foto_circular(diametro):
    """Recorte circular usando el frame completo del retrato: el aire alrededor
    de la cabeza es real (viene en la foto), no fabricado."""
    if os.path.exists(FOTO_PERSONA):
        clave = ("circ", diametro)
        if clave not in _foto_cache:
            img = Image.open(FOTO_PERSONA).convert("RGB")
            img = ImageOps.fit(img, (diametro, diametro), Image.LANCZOS, centering=(0.5, 0.46))
            _foto_cache[clave] = img
        img = _foto_cache[clave].copy().convert("RGBA")
    else:
        img = avatar_rect(diametro, diametro).convert("RGBA")
    img.alpha_composite(_sombra_interna_circular(diametro))
    img.putalpha(_mascara_suave(diametro, diametro, lambda d, w, h: d.ellipse([0, 0, w - 1, h - 1], fill=255)))
    return img


def _puntos_hexagono(D, margen):
    pts = []
    for i in range(6):
        a = -math.pi / 2 + i * math.pi / 3
        pts.append((D / 2 + (D / 2 - margen) * math.cos(a), D / 2 + (D / 2 - margen) * math.sin(a)))
    return pts


def foto_hexagonal(diametro):
    img = foto_carnet(diametro, diametro).convert("RGBA")
    img.putalpha(_mascara_suave(diametro, diametro, lambda d, w, h: d.polygon(_puntos_hexagono(w, 4), fill=255)))
    return img


def contorno_hexagonal(diametro, color, grosor):
    SS = 4
    D = diametro * SS
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon(_puntos_hexagono(D, grosor * SS), outline=tuple(color[:3]) + (255,), width=grosor * SS)
    return img.resize((diametro, diametro), Image.LANCZOS)


def aro(diametro, color, grosor, alpha=255):
    SS = 4
    D = diametro * SS
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    g = grosor * SS
    ImageDraw.Draw(img).ellipse([g // 2, g // 2, D - g // 2 - 1, D - g // 2 - 1],
                                outline=tuple(color[:3]) + (alpha,), width=g)
    return img.resize((diametro, diametro), Image.LANCZOS)


def icono(nombre, tam, color, detalle=None):
    """Iconos geométricos dibujados (supersampleados para bordes suaves)."""
    SS = 4
    T = tam * SS
    img = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = tuple(color[:3]) + (255,)
    w = max(2, T // 12)

    def E(*v):
        return [int(x * T) for x in v]

    if nombre == "persona":
        d.ellipse(E(0.30, 0.06, 0.70, 0.46), fill=c)
        d.ellipse(E(0.10, 0.54, 0.90, 1.30), fill=c)
    elif nombre == "maletin":
        d.rounded_rectangle(E(0.08, 0.34, 0.92, 0.92), T // 9, fill=c)
        d.rounded_rectangle(E(0.34, 0.10, 0.66, 0.40), T // 12, outline=c, width=w)
        if detalle:
            d.rectangle(E(0.44, 0.56, 0.56, 0.70), fill=tuple(detalle[:3]) + (255,))
    elif nombre == "credencial":
        d.rounded_rectangle(E(0.06, 0.16, 0.94, 0.86), T // 8, outline=c, width=w)
        d.ellipse(E(0.20, 0.32, 0.42, 0.54), fill=c)
        d.line(E(0.54, 0.36, 0.82, 0.36), fill=c, width=w)
        d.line(E(0.54, 0.52, 0.82, 0.52), fill=c, width=w)
        d.line(E(0.20, 0.68, 0.82, 0.68), fill=c, width=w)
    elif nombre == "escudo":
        d.polygon(E(0.50, 0.04, 0.90, 0.18, 0.90, 0.52, 0.50, 0.96, 0.10, 0.52, 0.10, 0.18), fill=c)
        if detalle:
            d.line(E(0.32, 0.46, 0.46, 0.62, 0.70, 0.30), fill=tuple(detalle[:3]) + (255,),
                   width=int(w * 1.4), joint="curve")
    elif nombre == "check":
        d.ellipse(E(0.06, 0.06, 0.94, 0.94), outline=c, width=w)
        d.line(E(0.28, 0.50, 0.45, 0.68, 0.72, 0.34), fill=c, width=int(w * 1.3), joint="curve")
    elif nombre == "estrella":
        pts = []
        for i in range(10):
            r = 0.47 if i % 2 == 0 else 0.20
            a = -math.pi / 2 + math.pi * i / 5
            pts += [0.5 + r * math.cos(a), 0.5 + r * math.sin(a)]
        d.polygon(E(*pts), fill=c)
    elif nombre == "globo":
        d.ellipse(E(0.08, 0.08, 0.92, 0.92), outline=c, width=w)
        d.ellipse(E(0.32, 0.08, 0.68, 0.92), outline=c, width=w)
        d.line(E(0.08, 0.50, 0.92, 0.50), fill=c, width=w)
    return img.resize((tam, tam), Image.LANCZOS)


def diamante(d, cx, cy, r, color):
    d.polygon([(cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r)], fill=tuple(color[:3]) + (255,))


def grid_puntos(d, x0, y0, color, filas=3, cols=4, paso=17, r=3):
    """Cuadrícula de puntos decorativa (detalle de diseño tipo ChatGPT)."""
    for f in range(filas):
        for c in range(cols):
            cx, cy = x0 + c * paso, y0 + f * paso
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(color[:3]) + (255,))


def divisor_oro(d, cx, y, medio_ancho, oro):
    d.line([cx - medio_ancho, y, cx + medio_ancho, y], fill=tuple(oro[:3]) + (255,), width=2)
    diamante(d, cx, y, 7, oro)


def texto_tracking(d, xy, txt, fnt, fill, tracking=4, centrado=False):
    anchos = [d.textlength(ch, font=fnt) for ch in txt]
    total = sum(anchos) + tracking * (len(txt) - 1)
    x, y = xy
    if centrado:
        x -= total / 2
    for ch, a in zip(txt, anchos):
        d.text((x, y), ch, font=fnt, fill=fill)
        x += a + tracking
    return total


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


def placa_qr(semilla, lado_qr, oro, relleno=22):
    """QR sobre placa blanca redondeada con filo dorado."""
    lado = lado_qr + relleno * 2
    placa = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(placa)
    d.rounded_rectangle([0, 0, lado - 1, lado - 1], 18, fill=(255, 255, 255, 255),
                        outline=tuple(oro[:3]) + (255,), width=2)
    placa.paste(pseudo_qr(semilla, lado_qr), (relleno, relleno))
    return placa


def logo_tenido(logo, ancho, alto, color, alpha=255):
    """Versión monocroma del logo teñida a un color, estilo ChatGPT: cuando el
    logo no contrasta con el fondo se pinta su silueta — NUNCA una placa/caja."""
    pieza = encajar(logo, ancho, alto)
    a = pieza.getchannel("A")
    tiene_alpha = tiene_transparencia(pieza)
    luz = ImageOps.invert(pieza.convert("L"))
    if tiene_alpha and not logo_es_claro(pieza):
        mascara = ImageChops.multiply(a, luz)  # conserva el detalle interior (letras, líneas)
    elif tiene_alpha:
        mascara = a
    else:
        # autocontraste SOLO para JPG opacos: logos pálidos darían silueta fantasma.
        # (Con transparencia rompería los logos oscuros: estiraría su tinta hacia 0.)
        mascara = ImageOps.autocontrast(luz, cutoff=2)
    if alpha < 255:
        mascara = mascara.point(lambda p: p * alpha // 255)
    capa = Image.new("RGBA", pieza.size, tuple(color[:3]) + (0,))
    capa.putalpha(mascara)
    return capa


def pegar_logo(canvas, logo, caja, fondo_claro=True, tinte=None, alinear="centro"):
    """Pega el logo encajado en la caja (x, y, ancho, alto). Si no contrasta con
    el fondo, lo reemplaza por su versión teñida (sin placas detrás del logo)."""
    x, y, ancho, alto = caja
    if fondo_claro and logo_es_claro(logo):
        pieza = logo_tenido(logo, ancho, alto, tinte or GRIS_DISECOD)
    elif not fondo_claro and (logo_es_oscuro(logo) or not tiene_transparencia(logo)):
        # sobre fondo oscuro: tinta oscura O un JPG opaco (mostraría su rectángulo blanco)
        pieza = logo_tenido(logo, ancho, alto, tinte or (245, 243, 238))
    else:
        pieza = encajar(logo, ancho, alto)
    x_pieza = x if alinear == "izquierda" else x + (ancho - pieza.width) // 2
    canvas.alpha_composite(pieza, (x_pieza, y + (alto - pieza.height) // 2))


# ---------- Estilos ----------

def estilo1_frontal(logo, pal, cliente):
    """Ejecutivo con banda lateral: columna en color de marca (foto + DNI) y
    área marfil con logo flotante, nombre serif y datos con iconos dorados."""
    prim, sec, oro = pal
    oro_l = ajustar(oro, 0.82)
    BANDA = 348
    t = gradiente_vertical(CARD_W, CARD_H, (255, 255, 255), MARFIL).convert("RGBA")
    banda = gradiente_vertical(BANDA, CARD_H, ajustar(prim, 1.08), ajustar(prim, 0.58)).convert("RGBA")
    t.paste(banda, (0, 0))
    wm = marca_agua(logo, 430, (255, 255, 255), 16)
    t.paste(wm, (-110, CARD_H - int(wm.height * 0.70)), wm)
    d = ImageDraw.Draw(t)
    # doble filo dorado que separa la banda
    d.rectangle([BANDA, 0, BANDA + 4, CARD_H], fill=tuple(oro[:3]))
    d.rectangle([BANDA + 9, 0, BANDA + 11, CARD_H], fill=ORO_CLARO)
    # foto con marco dorado, centrada en la banda
    fx = (BANDA - 240) // 2
    d.rounded_rectangle([fx - 11, 67, fx + 251, 393], 24, outline=tuple(oro[:3]), width=3)
    t.alpha_composite(foto_redondeada(240, 302, 16), (fx, 79))
    # DNI bajo la foto
    f_id = fuente("semibold", 26)
    ancho_id = d.textlength(DATOS["id"], font=f_id)
    x0 = (BANDA - int(ancho_id) - 48) // 2
    d.rounded_rectangle([x0, 436, x0 + ancho_id + 48, 490], 27, fill=(255, 255, 255))
    d.text((BANDA // 2, 448), DATOS["id"], font=f_id, fill=marca_legible(prim), anchor="ma")
    # área clara: logo flotante + datos
    pegar_logo(t, logo, (404, 44, 380, 138), fondo_claro=True, tinte=marca_legible(prim), alinear="izquierda")
    d.line([404, 212, 944, 212], fill=oro_l, width=2)
    diamante(d, 404, 212, 6, oro_l)
    grid_puntos(d, 886, 52, ORO_CLARO, filas=3, cols=3)
    d.text((404, 242), DATOS["nombre"], font=fuente("display-bold", 54), fill=TINTA)
    t.alpha_composite(icono("maletin", 26, oro_l, detalle=(255, 255, 255)), (406, 352))
    d.text((446, 346), DATOS["cargo"], font=fuente("regular", 32), fill=(96, 100, 108))
    t.alpha_composite(icono("credencial", 26, oro_l), (406, 408))
    d.text((446, 402), cliente, font=fuente("semibold", 28), fill=marca_legible(prim))
    # onda dorada al pie cruzando toda la tarjeta
    t.alpha_composite(capa_onda(CARD_W, CARD_H, oro, 200, CARD_H - 46, 12, 1.3, 0.2, grosor=4))
    t.alpha_composite(capa_onda(CARD_W, CARD_H, ORO_CLARO, 110, CARD_H - 32, 14, 1.3, 0.55, grosor=3))
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo1_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    oro_l = ajustar(oro, 0.82)
    t = gradiente_vertical(CARD_W, CARD_H, (255, 255, 255), MARFIL).convert("RGBA")
    # eco de la banda: franja delgada + filo dorado
    franja = gradiente_vertical(62, CARD_H, ajustar(prim, 1.08), ajustar(prim, 0.58)).convert("RGBA")
    t.paste(franja, (0, 0))
    wm = marca_agua(logo, 480, prim, 11)
    t.paste(wm, (CARD_W - int(wm.width * 0.62), CARD_H - int(wm.height * 0.55)), wm)
    d = ImageDraw.Draw(t)
    d.rectangle([62, 0, 66, CARD_H], fill=tuple(oro[:3]))
    cx = 66 + (CARD_W - 66) // 2
    pegar_logo(t, logo, (cx - 190, 46, 380, 122), fondo_claro=True, tinte=marca_legible(prim))
    divisor_oro(d, cx, 206, 130, oro_l)
    t.alpha_composite(placa_qr(cliente, 196, oro), (cx - 120, 232))
    d.text((cx, 494), "Escanee para validar la credencial",
           font=fuente("regular", 26), fill=(110, 115, 122), anchor="ma")
    d.text((cx, 534), "www.suempresa.com  ·  (01) 000 0000",
           font=fuente("semibold", 24), fill=(140, 144, 152), anchor="ma")
    t.alpha_composite(capa_onda(CARD_W, CARD_H, oro, 200, CARD_H - 40, 12, 1.4, 0.3, grosor=4))
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo2_frontal(logo, pal, cliente):
    prim, sec, oro = pal
    fondo_claro = luminancia(prim) >= 0.45
    col_txt = (255, 255, 255) if not fondo_claro else TINTA
    oro_txt = ORO_CLARO if not fondo_claro else ajustar(oro, 0.72)
    t = gradiente_3(V_W, V_H, ajustar(prim, 1.16), prim, ajustar(prim, 0.5), 0.40).convert("RGBA")
    # marca de agua en el cuerpo
    wm = marca_agua(logo, 560, (255, 255, 255) if not fondo_claro else ajustar(prim, 0.5), 18)
    t.paste(wm, ((V_W - wm.width) // 2, 300), wm)
    # ondas doradas cruzando detrás de la foto
    t.alpha_composite(capa_onda(V_W, V_H, oro, 255, 540, 22, 1.1, 0.2, grosor=64))
    t.alpha_composite(capa_onda(V_W, V_H, (255, 255, 255), 70, 562, 26, 1.1, 0.45, grosor=10))
    # base oscura al pie
    t.alpha_composite(capa_onda(V_W, V_H, ajustar(prim, 0.34), 235, 872, 16, 1.2, 0.6))
    # cabecera blanca con filo dorado: el logo va directo, sin placa
    t.alpha_composite(capa_onda(V_W, V_H, (255, 255, 255), 255, 212, 14, 1.1, 0.3, invertida=True))
    t.alpha_composite(capa_onda(V_W, V_H, oro, 220, 212, 14, 1.1, 0.3, grosor=4))
    d = ImageDraw.Draw(t)
    pegar_logo(t, logo, (139, 26, 360, 146), fondo_claro=True, tinte=marca_legible(prim))
    grid_puntos(d, 44, 40, mezcla(prim, (255, 255, 255), 0.45), filas=3, cols=3, paso=15, r=2)
    # foto circular con doble aro
    t.alpha_composite(aro(318, oro, 7), ((V_W - 318) // 2, 226))
    t.alpha_composite(aro(302, (255, 255, 255), 3, 210), ((V_W - 302) // 2, 234))
    t.alpha_composite(foto_circular(286), ((V_W - 286) // 2, 242))
    # textos
    d.text((V_W // 2, 656), DATOS["nombre"], font=fuente("display-bold", 50), fill=col_txt, anchor="ma")
    d.text((V_W // 2, 730), DATOS["cargo"], font=fuente("regular", 31), fill=col_txt, anchor="ma")
    divisor_oro(d, V_W // 2, 796, 52, oro_txt)
    d.text((V_W // 2, 814), cliente, font=fuente("semibold", 27), fill=oro_txt, anchor="ma")
    # chip ID dorado
    f_id = fuente("semibold", 28)
    ancho_id = d.textlength(DATOS["id"], font=f_id)
    x0 = (V_W - ancho_id - 56) // 2
    d.rounded_rectangle([x0, 884, x0 + ancho_id + 56, 942], 29, fill=tuple(oro[:3]))
    d.text((V_W // 2, 896), DATOS["id"], font=f_id, fill=(51, 40, 20), anchor="ma")
    d.text((V_W // 2, 960), "www.suempresa.com", font=fuente("regular", 24),
           fill=mezcla(col_txt, prim, 0.25), anchor="ma")
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo2_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    base = ajustar(prim, 0.46)
    col_txt = texto_sobre(base)
    t = gradiente_vertical(V_W, V_H, ajustar(prim, 0.62), ajustar(prim, 0.34)).convert("RGBA")
    wm = marca_agua(logo, 600, (255, 255, 255), 12)
    t.paste(wm, ((V_W - wm.width) // 2, 290), wm)
    # cabecera blanca con filo dorado: el logo va directo, sin placa
    t.alpha_composite(capa_onda(V_W, V_H, (255, 255, 255), 255, 196, 13, 1.2, 0.55, invertida=True))
    t.alpha_composite(capa_onda(V_W, V_H, oro, 220, 196, 13, 1.2, 0.55, grosor=4))
    d = ImageDraw.Draw(t)
    pegar_logo(t, logo, (149, 22, 340, 136), fondo_claro=True, tinte=marca_legible(prim))
    # lema
    d.multiline_text((V_W // 2, 318), "Comprometidos con la excelencia,\nla seguridad y el desarrollo.",
                     font=fuente("display-italic", 31), fill=(245, 243, 238), anchor="ma",
                     align="center", spacing=14)
    # fila de valores
    valores = [("escudo", "SEGURIDAD"), ("check", "COMPROMISO"), ("estrella", "EXCELENCIA")]
    f_val = fuente("semibold", 18)
    for i, (nombre_ic, etiqueta) in enumerate(valores):
        cx = V_W // 6 + i * (V_W // 3)
        ic = icono(nombre_ic, 54, ORO_CLARO, detalle=mezcla(base, (0, 0, 0), 0.25))
        t.alpha_composite(ic, (cx - 27, 470))
        texto_tracking(d, (cx, 542), etiqueta, f_val, (235, 233, 228), tracking=3, centrado=True)
    t.alpha_composite(placa_qr(cliente + "-r", 190, oro), ((V_W - 234) // 2, 622))
    d.text((V_W // 2, 898), "www.suempresa.com", font=fuente("semibold", 27), fill=(245, 243, 238), anchor="ma")
    t.alpha_composite(capa_onda(V_W, V_H, oro, 170, 975, 10, 1.5, 0.7, grosor=3))
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def _esquinas_deco(d, oro, margen=44, largo=46):
    """Acentos en L (art déco) en esquinas opuestas."""
    m, L = margen, largo
    for desfase in (0, 9):
        # superior izquierda
        d.line([m + desfase, m + L, m + desfase, m + desfase, m + L, m + desfase],
               fill=tuple(oro[:3]) + (255,), width=3, joint="curve")
        # inferior derecha
        d.line([CARD_W - m - desfase, CARD_H - m - L, CARD_W - m - desfase, CARD_H - m - desfase,
                CARD_W - m - L, CARD_H - m - desfase],
               fill=tuple(oro[:3]) + (255,), width=3, joint="curve")


def estilo3_frontal(logo, pal, cliente):
    prim, sec, oro = pal
    fondo_tinte = mezcla(FONDO_OSCURO, prim, 0.16)
    t = gradiente_diagonal(CARD_W, CARD_H, (24, 24, 27), fondo_tinte).convert("RGBA")
    wm = marca_agua(logo, 540, (255, 255, 255), 11)
    t.paste(wm, (CARD_W - int(wm.width * 0.78), CARD_H - int(wm.height * 0.66)), wm)
    t.alpha_composite(capa_onda(CARD_W, CARD_H, oro, 150, 596, 12, 1.6, 0.25, grosor=3))
    t.alpha_composite(capa_onda(CARD_W, CARD_H, oro, 60, 610, 14, 1.6, 0.55, grosor=2))
    d = ImageDraw.Draw(t, "RGBA")
    d.rounded_rectangle([22, 22, CARD_W - 23, CARD_H - 23], RADIO - 12,
                        outline=tuple(oro[:3]) + (150,), width=2)
    _esquinas_deco(d, ORO_CLARO)
    tinte_claro = ajustar(prim, 1.75) if saturacion(prim) > 0.12 else ORO_CLARO
    pegar_logo(t, logo, (72, 64, 330, 122), fondo_claro=False, tinte=tinte_claro)
    d.line([74, 220, 320, 220], fill=tuple(oro[:3]) + (255,), width=2)
    diamante(d, 74, 220, 6, oro)
    d.text((72, 248), DATOS["nombre"], font=fuente("display-bold", 54), fill=(245, 244, 241))
    t.alpha_composite(icono("maletin", 26, ORO_CLARO, detalle=fondo_tinte), (74, 352))
    d.text((112, 346), DATOS["cargo"], font=fuente("regular", 32), fill=(178, 180, 188))
    t.alpha_composite(icono("credencial", 26, ORO_CLARO), (74, 406))
    d.text((112, 400), cliente, font=fuente("semibold", 27), fill=ORO_CLARO)
    d.text((74, 478), DATOS["id"], font=fuente("light", 27), fill=(150, 152, 160))
    # foto circular con aro dorado doble
    t.alpha_composite(aro(330, ORO_CLARO, 2, 120), (644, 140))
    t.alpha_composite(aro(306, oro, 6), (656, 152))
    t.alpha_composite(foto_circular(274), (672, 168))
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo3_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    fondo_tinte = mezcla(FONDO_OSCURO, prim, 0.16)
    t = gradiente_diagonal(CARD_W, CARD_H, fondo_tinte, (24, 24, 27)).convert("RGBA")
    wm = marca_agua(logo, 500, (255, 255, 255), 9)
    t.paste(wm, (-int(wm.width * 0.28), CARD_H - int(wm.height * 0.60)), wm)
    d = ImageDraw.Draw(t, "RGBA")
    d.rounded_rectangle([22, 22, CARD_W - 23, CARD_H - 23], RADIO - 12,
                        outline=tuple(oro[:3]) + (150,), width=2)
    _esquinas_deco(d, ORO_CLARO)
    tinte_claro = ajustar(prim, 1.75) if saturacion(prim) > 0.12 else ORO_CLARO
    pegar_logo(t, logo, (CARD_W // 2 - 170, 96, 340, 136), fondo_claro=False, tinte=tinte_claro)
    divisor_oro(d, CARD_W // 2, 286, 110, oro)
    d.text((CARD_W // 2, 322), "Esta credencial es personal e intransferible.",
           font=fuente("regular", 26), fill=(176, 178, 186), anchor="ma")
    d.text((CARD_W // 2, 376), "www.suempresa.com", font=fuente("semibold", 28), fill=ORO_CLARO, anchor="ma")
    # emblema de diamantes al pie
    for dx, r in [(-34, 5), (0, 8), (34, 5)]:
        diamante(d, CARD_W // 2 + dx, 470, r, oro)
    t.alpha_composite(capa_onda(CARD_W, CARD_H, oro, 120, 560, 10, 1.8, 0.4, grosor=2))
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo4_frontal(logo, pal, cliente):
    """Institucional: cabecera en arco con el logo, foto circular solapando el arco."""
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    oro_l = ajustar(oro, 0.82)
    t = gradiente_vertical(V_W, V_H, (255, 255, 255), MARFIL).convert("RGBA")
    # cabecera con borde de arco
    mascara_arco = Image.new("L", (V_W, 450), 0)
    da = ImageDraw.Draw(mascara_arco)
    da.rectangle([0, 0, V_W, 250], fill=255)
    da.ellipse([-200, 110, V_W + 200, 450], fill=255)
    grad = gradiente_vertical(V_W, 450, ajustar(prim, 1.06), ajustar(prim, 0.66))
    t.paste(grad, (0, 0), mascara_arco)
    d = ImageDraw.Draw(t)
    d.arc([-200, 110, V_W + 200, 450], 8, 172, fill=tuple(oro[:3]), width=5)
    d.arc([-200, 122, V_W + 200, 462], 8, 172, fill=ORO_CLARO, width=2)
    wm = marca_agua(logo, 460, (255, 255, 255) if not claro else ajustar(prim, 0.5), 14)
    t.paste(wm, ((V_W - wm.width) // 2, 12), wm)
    pegar_logo(t, logo, (139, 40, 360, 136), fondo_claro=claro)
    # foto circular solapando el arco
    t.alpha_composite(aro(308, oro, 6), (165, 300))
    t.alpha_composite(aro(290, (255, 255, 255), 4, 230), (174, 309))
    t.alpha_composite(foto_circular(270), (184, 319))
    # datos
    d.text((V_W // 2, 640), DATOS["nombre"], font=fuente("display-bold", 50), fill=TINTA, anchor="ma")
    d.text((V_W // 2, 714), DATOS["cargo"], font=fuente("regular", 31), fill=(96, 100, 108), anchor="ma")
    divisor_oro(d, V_W // 2, 782, 52, oro_l)
    d.text((V_W // 2, 802), cliente, font=fuente("semibold", 27), fill=marca_legible(prim), anchor="ma")
    f_id = fuente("semibold", 27)
    ancho_id = d.textlength(DATOS["id"], font=f_id)
    x0 = (V_W - int(ancho_id) - 56) // 2
    d.rounded_rectangle([x0, 862, x0 + ancho_id + 56, 918], 28, outline=oro_l, width=2)
    d.text((V_W // 2, 874), DATOS["id"], font=f_id, fill=oro_l, anchor="ma")
    grid_puntos(d, 44, 580, ORO_CLARO, filas=3, cols=3, paso=15, r=2)
    grid_puntos(d, 552, 580, ORO_CLARO, filas=3, cols=3, paso=15, r=2)
    t.alpha_composite(capa_onda(V_W, V_H, prim, 255, V_H - 48, 13, 1.2, 0.3))
    t.alpha_composite(capa_onda(V_W, V_H, oro, 220, V_H - 54, 13, 1.2, 0.3, grosor=4))
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo4_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    oro_l = ajustar(oro, 0.82)
    t = gradiente_vertical(V_W, V_H, (255, 255, 255), MARFIL).convert("RGBA")
    mascara_arco = Image.new("L", (V_W, 310), 0)
    da = ImageDraw.Draw(mascara_arco)
    da.rectangle([0, 0, V_W, 150], fill=255)
    da.ellipse([-200, 30, V_W + 200, 310], fill=255)
    grad = gradiente_vertical(V_W, 310, ajustar(prim, 1.06), ajustar(prim, 0.66))
    t.paste(grad, (0, 0), mascara_arco)
    d = ImageDraw.Draw(t)
    d.arc([-200, 30, V_W + 200, 310], 8, 172, fill=tuple(oro[:3]), width=5)
    pegar_logo(t, logo, (139, 24, 360, 118), fondo_claro=claro)
    # caja dorada de valores
    d.rounded_rectangle([56, 380, V_W - 56, 580], 26, outline=oro_l, width=2)
    valores = [("escudo", "SEGURIDAD"), ("check", "COMPROMISO"), ("estrella", "EXCELENCIA")]
    f_val = fuente("semibold", 18)
    for i, (nombre_ic, etiqueta) in enumerate(valores):
        cx = V_W // 6 + i * (V_W // 3)
        t.alpha_composite(icono(nombre_ic, 54, marca_legible(prim), detalle=(255, 255, 255)), (cx - 27, 416))
        texto_tracking(d, (cx, 492), etiqueta, f_val, (96, 100, 108), tracking=3, centrado=True)
        if i:
            d.line([cx - V_W // 6, 412, cx - V_W // 6, 548], fill=ORO_CLARO, width=2)
    t.alpha_composite(placa_qr(cliente + "-r", 196, oro), ((V_W - 240) // 2, 624))
    d.text((V_W // 2, 892), "Escanee para validar la credencial",
           font=fuente("regular", 25), fill=(110, 115, 122), anchor="ma")
    d.text((V_W // 2, 930), "www.suempresa.com", font=fuente("semibold", 26), fill=marca_legible(prim), anchor="ma")
    t.alpha_composite(capa_onda(V_W, V_H, oro, 200, V_H - 38, 11, 1.4, 0.6, grosor=4))
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo5_frontal(logo, pal, cliente):
    """Moderno: cortes diagonales en las esquinas y foto hexagonal."""
    prim, sec, oro = pal
    prim_l = marca_legible(prim)
    osc = mezcla(GRIS_DISECOD, prim, 0.3)
    t = gradiente_vertical(CARD_W, CARD_H, (255, 255, 255), (250, 250, 252)).convert("RGBA")
    d = ImageDraw.Draw(t)
    # esquina superior izquierda: doble diagonal
    d.polygon([(0, 0), (470, 0), (0, 272)], fill=tuple(ajustar(prim, 0.62)))
    d.polygon([(0, 0), (400, 0), (0, 230)], fill=tuple(prim[:3]))
    d.line([400, 0, 0, 230], fill=tuple(oro[:3]), width=4)
    # esquina inferior derecha: oscura
    d.polygon([(CARD_W, CARD_H), (CARD_W - 480, CARD_H), (CARD_W, CARD_H - 256)], fill=tuple(ajustar(prim, 0.62)))
    d.polygon([(CARD_W, CARD_H), (CARD_W - 420, CARD_H), (CARD_W, CARD_H - 220)], fill=tuple(osc[:3]))
    d.line([CARD_W - 420, CARD_H, CARD_W, CARD_H - 220], fill=tuple(oro[:3]), width=4)
    grid_puntos(d, 880, 46, mezcla(prim, (255, 255, 255), 0.45), filas=3, cols=3)
    grid_puntos(d, 60, 530, ORO_CLARO, filas=2, cols=4, paso=15, r=2)
    # foto hexagonal sobre la diagonal
    t.alpha_composite(contorno_hexagonal(312, oro, 5), (94, 158))
    t.alpha_composite(foto_hexagonal(284), (108, 172))
    # logo flotante arriba a la derecha
    pegar_logo(t, logo, (520, 34, 420, 124), fondo_claro=True, tinte=prim_l)
    d.line([470, 196, 950, 196], fill=tuple(oro[:3]), width=2)
    diamante(d, 950, 196, 6, oro)
    # datos
    d.text((470, 226), DATOS["nombre"], font=fuente("display-bold", 48), fill=TINTA)
    t.alpha_composite(icono("maletin", 26, prim_l, detalle=(255, 255, 255)), (472, 322))
    d.text((512, 316), DATOS["cargo"], font=fuente("regular", 31), fill=(96, 100, 108))
    t.alpha_composite(icono("credencial", 26, prim_l), (472, 376))
    d.text((512, 370), cliente, font=fuente("semibold", 28), fill=prim_l)
    f_id = fuente("semibold", 26)
    ancho_id = d.textlength(DATOS["id"], font=f_id)
    d.rounded_rectangle([472, 440, 472 + ancho_id + 52, 494], 27, outline=tuple(prim_l), width=2)
    d.text((498, 451), DATOS["id"], font=f_id, fill=prim_l)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo5_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    prim_l = marca_legible(prim)
    osc = mezcla(GRIS_DISECOD, prim, 0.3)
    t = gradiente_vertical(CARD_W, CARD_H, (255, 255, 255), (250, 250, 252)).convert("RGBA")
    d = ImageDraw.Draw(t)
    d.polygon([(0, 0), (300, 0), (0, 170)], fill=tuple(prim[:3]))
    d.line([300, 0, 0, 170], fill=tuple(oro[:3]), width=3)
    d.polygon([(CARD_W, CARD_H), (CARD_W - 300, CARD_H), (CARD_W, CARD_H - 156)], fill=tuple(osc[:3]))
    d.line([CARD_W - 300, CARD_H, CARD_W, CARD_H - 156], fill=tuple(oro[:3]), width=3)
    wm = marca_agua(logo, 470, prim, 10)
    t.paste(wm, (CARD_W - int(wm.width * 0.66), CARD_H - int(wm.height * 0.6)), wm)
    pegar_logo(t, logo, (CARD_W // 2 - 190, 44, 380, 122), fondo_claro=True, tinte=prim_l)
    divisor_oro(d, CARD_W // 2, 202, 130, ajustar(oro, 0.82))
    t.alpha_composite(placa_qr(cliente, 192, oro), (CARD_W // 2 - 118, 228))
    d.text((CARD_W // 2, 486), "Escanee para validar la credencial",
           font=fuente("regular", 26), fill=(110, 115, 122), anchor="ma")
    d.text((CARD_W // 2, 526), "www.suempresa.com  ·  (01) 000 0000",
           font=fuente("semibold", 24), fill=(140, 144, 152), anchor="ma")
    grid_puntos(d, 884, 60, mezcla(prim, (255, 255, 255), 0.45), filas=3, cols=3, paso=15, r=2)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


ESTILOS = [
    ("Estilo 1 — Corporativo", estilo1_frontal, estilo1_reverso),
    ("Estilo 2 — Full color", estilo2_frontal, estilo2_reverso),
    ("Estilo 3 — Premium", estilo3_frontal, estilo3_reverso),
    ("Estilo 4 — Institucional", estilo4_frontal, estilo4_reverso),
    ("Estilo 5 — Moderno", estilo5_frontal, estilo5_reverso),
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
    canvas = gradiente_vertical(ancho, alto, (251, 251, 252), (239, 239, 242)).convert("RGBA")
    d = ImageDraw.Draw(canvas)
    d.text((margen, 28), titulo, font=fuente("bold", 40), fill=GRIS_DISECOD)
    for img, x, rotulo in [(frontal, margen, "FRONTAL"), (reverso, margen + frontal.width + sep, "REVERSO")]:
        con_sombra(canvas, img, (x, etiqueta_h + 20))
        d.text((x + img.width // 2, etiqueta_h - 18), rotulo, font=fuente("semibold", 24), fill=(150, 154, 160), anchor="ma")
    return canvas.convert("RGB")


def lamina(cliente, piezas):
    """piezas: lista de (titulo, frontal, reverso). Lámina con marco DISECOD.
    Acomoda los estilos en filas de 3 (la última fila se centra)."""
    ANCHO = 2300
    POR_FILA = 3
    filas = [piezas[i:i + POR_FILA] for i in range(0, len(piezas), POR_FILA)]
    col_w = (ANCHO - (POR_FILA + 1) * 70) // POR_FILA
    esc_h = 0.58       # escala tarjetas horizontales
    y_top = 252
    zona_h = 840       # alto de la zona de tarjetas por fila
    sep_filas = 70
    ALTO = y_top + len(filas) * zona_h + (len(filas) - 1) * sep_filas + 150

    canvas = Image.new("RGBA", (ANCHO, ALTO), (249, 248, 246, 255))
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

    # filas de columnas (cada columna centrada verticalmente en su zona)
    for nf, fila in enumerate(filas):
        y_fila = y_top + nf * (zona_h + sep_filas)
        offset_x = (ANCHO - (len(fila) * col_w + (len(fila) - 1) * 70)) // 2
        for i, (titulo, frontal, reverso) in enumerate(fila):
            x0 = offset_x + i * (col_w + 70)
            d.text((x0 + col_w // 2, y_fila - 48), titulo, font=fuente("semibold", 32), fill=GRIS_DISECOD, anchor="ma")
            if frontal.width > frontal.height:  # horizontal: apiladas
                fr = frontal.resize((int(frontal.width * esc_h), int(frontal.height * esc_h)), Image.LANCZOS)
                rv = reverso.resize((int(reverso.width * esc_h), int(reverso.height * esc_h)), Image.LANCZOS)
                alto_col = fr.height + rv.height + 60
                y0 = y_fila + (zona_h - alto_col) // 2
                con_sombra(canvas, fr, (x0 + (col_w - fr.width) // 2, y0), 14, 60)
                con_sombra(canvas, rv, (x0 + (col_w - rv.width) // 2, y0 + fr.height + 60), 14, 60)
            else:  # vertical: lado a lado
                esc = (col_w - 50) / (frontal.width * 2)
                fr = frontal.resize((int(frontal.width * esc), int(frontal.height * esc)), Image.LANCZOS)
                rv = reverso.resize((int(reverso.width * esc), int(reverso.height * esc)), Image.LANCZOS)
                y0 = y_fila + (zona_h - fr.height) // 2
                con_sombra(canvas, fr, (x0, y0), 14, 60)
                con_sombra(canvas, rv, (x0 + fr.width + 50, y0), 14, 60)

    # pie
    d.rectangle([0, ALTO - 120, ANCHO, ALTO - 116], fill=LILA)
    d.text((ANCHO // 2, ALTO - 86),
           "DISECOD — Fotochecks e impresoras EVOLIS",
           font=fuente("semibold", 32), fill=GRIS_DISECOD, anchor="ma")
    d.text((ANCHO // 2, ALTO - 42),
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
    pal = (prim, sec, oro_del_logo(logo))

    piezas = []
    for titulo, fn_frontal, fn_reverso in ESTILOS:
        piezas.append((titulo, fn_frontal(logo, pal, cliente), fn_reverso(logo, pal, cliente)))

    if carpeta_salida is None:
        carpeta_salida = os.path.join(RUTA_BASE, "salida", f"{slug(cliente)}-{date.today():%Y-%m-%d}")
    os.makedirs(carpeta_salida, exist_ok=True)

    rutas = []
    # caras limpias a tamaño real de imprenta (CR80 300 dpi, full-bleed,
    # sin sombras ni rótulos): base de trabajo para el diseñador / CardPresso
    carpeta_diseno = os.path.join(carpeta_salida, "para-diseno")
    os.makedirs(carpeta_diseno, exist_ok=True)
    for i, (titulo, fr, rv) in enumerate(piezas, 1):
        sufijo = slug(titulo.split("—")[-1]).lower()
        ruta = os.path.join(carpeta_salida, f"estilo-{i}-{sufijo}.png")
        png_estilo(titulo, fr, rv).save(ruta, optimize=True)
        rutas.append(ruta)
        fr.convert("RGB").save(os.path.join(carpeta_diseno, f"estilo-{i}-{sufijo}-frontal.png"), optimize=True)
        rv.convert("RGB").save(os.path.join(carpeta_diseno, f"estilo-{i}-{sufijo}-reverso.png"), optimize=True)

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
