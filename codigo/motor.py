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
            # encuadre ancho: cabeza con aire + pecho visible (no pasaporte asfixiado)
            img = img.crop((int(W * 0.10), 0, int(W * 0.90), H))
            img = ImageOps.fit(img, (ancho, alto), Image.LANCZOS, centering=(0.5, 0.35))
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


def placa_qr(semilla, lado_qr, oro=None, relleno=22):
    """QR sobre placa blanca redondeada sólida (sin contornos decorativos)."""
    lado = lado_qr + relleno * 2
    placa = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    ImageDraw.Draw(placa).rounded_rectangle([0, 0, lado - 1, lado - 1], 18, fill=(255, 255, 255, 255))
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

def campo(d, xy, etiqueta, valor, color_etq, color_val, centrado=False, tam_valor=30):
    """Estructura tipográfica de credencial: ETIQUETA en versalitas + valor en bold."""
    x, y = xy
    f_e = fuente("semibold", 19)
    f_v = fuente("semibold", tam_valor)
    if centrado:
        texto_tracking(d, (x, y), etiqueta, f_e, color_etq, tracking=4, centrado=True)
        d.text((x, y + 32), valor, font=f_v, fill=color_val, anchor="ma")
    else:
        texto_tracking(d, (x, y), etiqueta, f_e, color_etq, tracking=4)
        d.text((x, y + 32), valor, font=f_v, fill=color_val)


GRIS_ETIQUETA = (152, 154, 160)


def estilo1_frontal(logo, pal, cliente):
    """Corporativo: banda lateral sólida con la foto, área blanca con grilla limpia."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    banda_txt = texto_sobre(prim)
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    BANDA = 332
    d.rectangle([0, 0, BANDA, CARD_H], fill=tuple(prim[:3]))
    d.rectangle([BANDA, 0, BANDA + 2, CARD_H], fill=tuple(oro[:3]))
    # foto protagonista en la banda, sin marcos
    t.alpha_composite(foto_redondeada(250, 314, 14), ((BANDA - 250) // 2, 88))
    texto_tracking(d, (BANDA // 2, 444), "DNI", fuente("semibold", 19),
                   mezcla(banda_txt, prim, 0.4), tracking=5, centrado=True)
    d.text((BANDA // 2, 474), DATOS["id"].split()[-1], font=fuente("semibold", 31), fill=banda_txt, anchor="ma")
    # área blanca: logo flotante, nombre y campos
    pegar_logo(t, logo, (396, 56, 340, 96), fondo_claro=True, tinte=prim_txt, alinear="izquierda")
    d.text((396, 218), DATOS["nombre"], font=fuente("display-bold", 56), fill=TINTA)
    d.line([398, 310, 558, 310], fill=tuple(oro[:3]), width=2)
    campo(d, (398, 358), "CARGO", DATOS["cargo"], GRIS_ETIQUETA, TINTA)
    campo(d, (398, 466), "EMPRESA", cliente, GRIS_ETIQUETA, prim_txt)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo1_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, 14, CARD_H], fill=tuple(prim[:3]))
    cx = CARD_W // 2
    pegar_logo(t, logo, (cx - 170, 64, 340, 96), fondo_claro=True, tinte=marca_legible(prim))
    t.paste(pseudo_qr(cliente, 200), (cx - 100, 218))
    d.text((cx, 452), "Escanee para validar la credencial",
           font=fuente("semibold", 26), fill=TINTA, anchor="ma")
    d.text((cx, 494), "www.suempresa.com  ·  (01) 000 0000",
           font=fuente("regular", 24), fill=GRIS_ETIQUETA, anchor="ma")
    d.line([cx - 80, 562, cx + 80, 562], fill=tuple(oro[:3]), width=2)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo2_frontal(logo, pal, cliente):
    """Full color: color de marca pleno, logo en silueta blanca, panel blanco curvo al pie."""
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    col_txt = (255, 255, 255) if not claro else TINTA
    col_suave = mezcla(col_txt, prim, 0.30)
    t = gradiente_vertical(V_W, V_H, ajustar(prim, 1.04), ajustar(prim, 0.86)).convert("RGBA")
    d = ImageDraw.Draw(t)
    # logo en silueta (blanca sobre oscuro / tinta sobre claro), flotando
    pieza = logo_tenido(logo, 320, 112, (255, 255, 255) if not claro else marca_legible(prim))
    t.alpha_composite(pieza, ((V_W - pieza.width) // 2, 56 + (112 - pieza.height) // 2))
    # foto circular con un solo aro blanco
    t.alpha_composite(aro(310, (255, 255, 255), 8), ((V_W - 310) // 2, 238))
    t.alpha_composite(foto_circular(290), ((V_W - 290) // 2, 248))
    # color pleno de borde a borde: los datos van en blanco sobre el color
    d.text((V_W // 2, 618), DATOS["nombre"], font=fuente("display-bold", 52), fill=col_txt, anchor="ma")
    d.text((V_W // 2, 698), DATOS["cargo"], font=fuente("regular", 30), fill=col_suave, anchor="ma")
    d.line([V_W // 2 - 60, 762, V_W // 2 + 60, 762], fill=tuple(oro[:3]), width=2)
    campo(d, (V_W // 2, 806), "EMPRESA", cliente, col_suave, col_txt, centrado=True)
    campo(d, (V_W // 2, 902), "DNI", DATOS["id"].split()[-1], col_suave, col_txt, centrado=True, tam_valor=28)
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo2_reverso(logo, pal, cliente):
    """Reverso full color: el logo como héroe en silueta gigante + lema."""
    prim, sec, oro = pal
    base = ajustar(prim, 0.68)
    t = Image.new("RGBA", (V_W, V_H), tuple(base[:3]) + (255,))
    d = ImageDraw.Draw(t)
    # héroe: silueta del logo en tinte claro
    heroe = logo_tenido(logo, 430, 300, ajustar(prim, 1.45) if saturacion(prim) > 0.12 else (255, 255, 255), alpha=60)
    t.alpha_composite(heroe, ((V_W - heroe.width) // 2, 96 + (300 - heroe.height) // 2))
    d.multiline_text((V_W // 2, 470), "Comprometidos con la excelencia,\nla seguridad y el desarrollo.",
                     font=fuente("display-italic", 31), fill=(248, 247, 244), anchor="ma",
                     align="center", spacing=14)
    d.line([V_W // 2 - 60, 596, V_W // 2 + 60, 596], fill=tuple(oro[:3]), width=2)
    t.alpha_composite(placa_qr(cliente + "-r", 192), ((V_W - 236) // 2, 648))
    d.text((V_W // 2, 922), "www.suempresa.com", font=fuente("semibold", 26), fill=(248, 247, 244), anchor="ma")
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo3_frontal(logo, pal, cliente):
    """Premium: oscuridad plana, marco fino dorado y silencio. Nada más."""
    prim, sec, oro = pal
    fondo = mezcla((30, 30, 34), prim, 0.10)
    t = Image.new("RGBA", (CARD_W, CARD_H), tuple(fondo[:3]) + (255,))
    d = ImageDraw.Draw(t, "RGBA")
    d.rounded_rectangle([26, 26, CARD_W - 27, CARD_H - 27], RADIO - 14,
                        outline=tuple(oro[:3]) + (200,), width=2)
    tinte_claro = ajustar(prim, 1.75) if saturacion(prim) > 0.12 else ORO_CLARO
    pegar_logo(t, logo, (76, 64, 300, 88), fondo_claro=False, tinte=tinte_claro, alinear="izquierda")
    d.text((76, 198), DATOS["nombre"], font=fuente("display-bold", 56), fill=(246, 245, 242))
    d.line([78, 290, 238, 290], fill=tuple(oro[:3]) + (255,), width=2)
    campo(d, (78, 338), "CARGO", DATOS["cargo"], (140, 142, 150), (228, 228, 232))
    campo(d, (78, 446), "EMPRESA", cliente, (140, 142, 150), ORO_CLARO)
    # foto circular con un solo aro dorado fino + DNI centrado debajo
    t.alpha_composite(aro(296, oro, 3), (646, 172))
    t.alpha_composite(foto_circular(280), (654, 180))
    campo(d, (794, 500), "DNI", DATOS["id"].split()[-1], (140, 142, 150), (228, 228, 232),
          centrado=True, tam_valor=28)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo3_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    fondo = mezcla((30, 30, 34), prim, 0.10)
    t = Image.new("RGBA", (CARD_W, CARD_H), tuple(fondo[:3]) + (255,))
    d = ImageDraw.Draw(t, "RGBA")
    d.rounded_rectangle([26, 26, CARD_W - 27, CARD_H - 27], RADIO - 14,
                        outline=tuple(oro[:3]) + (200,), width=2)
    tinte_claro = ajustar(prim, 1.75) if saturacion(prim) > 0.12 else ORO_CLARO
    pegar_logo(t, logo, (CARD_W // 2 - 160, 120, 320, 130), fondo_claro=False, tinte=tinte_claro)
    d.line([CARD_W // 2 - 60, 310, CARD_W // 2 + 60, 310], fill=tuple(oro[:3]) + (255,), width=2)
    d.text((CARD_W // 2, 348), "Esta credencial es personal e intransferible.",
           font=fuente("regular", 26), fill=(178, 180, 188), anchor="ma")
    d.text((CARD_W // 2, 404), "www.suempresa.com", font=fuente("semibold", 28), fill=ORO_CLARO, anchor="ma")
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def _cabecera_arco(t, prim, alto_recto, alto_total):
    """Cabecera sólida con borde de arco + filo dorado único."""
    mascara_arco = Image.new("L", (V_W, alto_total), 0)
    da = ImageDraw.Draw(mascara_arco)
    da.rectangle([0, 0, V_W, alto_recto], fill=255)
    da.ellipse([-200, alto_recto - (alto_total - alto_recto), V_W + 200, alto_total], fill=255)
    t.paste(Image.new("RGB", (V_W, alto_total), tuple(prim[:3])), (0, 0), mascara_arco)
    return [-200, alto_recto - (alto_total - alto_recto), V_W + 200, alto_total]


def estilo4_frontal(logo, pal, cliente):
    """Institucional: cabecera de arco sólida, foto solapada, campos centrados."""
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    t = Image.new("RGBA", (V_W, V_H), (255, 255, 255, 255))
    caja_arco = _cabecera_arco(t, prim, 270, 440)
    d = ImageDraw.Draw(t)
    d.arc(caja_arco, 8, 172, fill=tuple(oro[:3]), width=3)
    pieza = logo_tenido(logo, 340, 124, (255, 255, 255) if not claro else marca_legible(prim))
    t.alpha_composite(pieza, ((V_W - pieza.width) // 2, 46 + (124 - pieza.height) // 2))
    # foto circular solapando el arco, un solo aro blanco
    t.alpha_composite(aro(296, (255, 255, 255), 10), ((V_W - 296) // 2, 256))
    t.alpha_composite(foto_circular(272), ((V_W - 272) // 2, 268))
    d.text((V_W // 2, 618), DATOS["nombre"], font=fuente("display-bold", 48), fill=TINTA, anchor="ma")
    d.text((V_W // 2, 692), DATOS["cargo"], font=fuente("regular", 30), fill=(110, 113, 120), anchor="ma")
    d.line([V_W // 2 - 60, 752, V_W // 2 + 60, 752], fill=tuple(oro[:3]), width=2)
    campo(d, (V_W // 2, 796), "EMPRESA", cliente, GRIS_ETIQUETA, marca_legible(prim), centrado=True)
    campo(d, (V_W // 2, 892), "DNI", DATOS["id"].split()[-1], GRIS_ETIQUETA, TINTA, centrado=True)
    d.rectangle([0, V_H - 14, V_W, V_H], fill=tuple(prim[:3]))
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo4_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    t = Image.new("RGBA", (V_W, V_H), (255, 255, 255, 255))
    caja_arco = _cabecera_arco(t, prim, 150, 290)
    d = ImageDraw.Draw(t)
    d.arc(caja_arco, 8, 172, fill=tuple(oro[:3]), width=3)
    pieza = logo_tenido(logo, 300, 104, (255, 255, 255) if not claro else marca_legible(prim))
    t.alpha_composite(pieza, ((V_W - pieza.width) // 2, 42 + (104 - pieza.height) // 2))
    t.paste(pseudo_qr(cliente + "-r", 212), ((V_W - 212) // 2, 386))
    d.text((V_W // 2, 648), "Escanee para validar la credencial",
           font=fuente("semibold", 26), fill=TINTA, anchor="ma")
    d.text((V_W // 2, 692), "www.suempresa.com  ·  (01) 000 0000",
           font=fuente("regular", 24), fill=GRIS_ETIQUETA, anchor="ma")
    d.line([V_W // 2 - 60, 768, V_W // 2 + 60, 768], fill=tuple(oro[:3]), width=2)
    d.rectangle([0, V_H - 14, V_W, V_H], fill=tuple(prim[:3]))
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo5_frontal(logo, pal, cliente):
    """Moderno: una sola diagonal de marca a la derecha con la foto; lo demás blanco."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    d.polygon([(704, 0), (CARD_W, 0), (CARD_W, CARD_H), (584, CARD_H)], fill=tuple(prim[:3]))
    d.line([704, 0, 584, CARD_H], fill=tuple(oro[:3]), width=3)
    # foto protagonista en el panel diagonal
    banda_txt = texto_sobre(prim)
    t.alpha_composite(foto_redondeada(252, 316, 14), (706, 88))
    texto_tracking(d, (832, 446), "DNI", fuente("semibold", 19),
                   mezcla(banda_txt, prim, 0.4), tracking=5, centrado=True)
    d.text((832, 476), DATOS["id"].split()[-1], font=fuente("semibold", 31), fill=banda_txt, anchor="ma")
    # área blanca
    pegar_logo(t, logo, (64, 56, 340, 96), fondo_claro=True, tinte=prim_txt, alinear="izquierda")
    d.text((64, 214), DATOS["nombre"], font=fuente("display-bold", 52), fill=TINTA)
    d.line([66, 300, 226, 300], fill=tuple(oro[:3]), width=2)
    campo(d, (66, 348), "CARGO", DATOS["cargo"], GRIS_ETIQUETA, TINTA)
    campo(d, (66, 456), "EMPRESA", cliente, GRIS_ETIQUETA, prim_txt)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo5_reverso(logo, pal, cliente):
    prim, sec, oro = pal
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    d.polygon([(CARD_W - 36, 0), (CARD_W, 0), (CARD_W, CARD_H), (CARD_W - 86, CARD_H)], fill=tuple(prim[:3]))
    cx = (CARD_W - 60) // 2
    pegar_logo(t, logo, (cx - 170, 64, 340, 96), fondo_claro=True, tinte=marca_legible(prim))
    t.paste(pseudo_qr(cliente, 200), (cx - 100, 218))
    d.text((cx, 452), "Escanee para validar la credencial",
           font=fuente("semibold", 26), fill=TINTA, anchor="ma")
    d.text((cx, 494), "www.suempresa.com  ·  (01) 000 0000",
           font=fuente("regular", 24), fill=GRIS_ETIQUETA, anchor="ma")
    d.line([cx - 80, 562, cx + 80, 562], fill=tuple(oro[:3]), width=2)
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
