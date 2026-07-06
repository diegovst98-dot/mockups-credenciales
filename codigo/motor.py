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
import shutil
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
    # Preferir el color de MARCA (saturado y con presencia) por encima del gris/negro
    # dominante: un wordmark típico es texto gris/negro + un acento de color (el de la
    # marca, ej. la "D" morada de DISECOD = 20% pero el gris es 80%). Si hay un grupo con
    # color real (sat≥0.20) y presencia (>5%), ese manda; si no, el dominante.
    prominentes = [g for g in grupos if g[1] > len(pixeles) * 0.05]
    con_color = [g for g in prominentes if saturacion(g[0]) >= 0.20]
    if con_color:
        primario = max(con_color, key=lambda g: saturacion(g[0]) * (0.4 + g[1] / len(pixeles)))[0]
    else:
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


def paleta_marca(prim, sec):
    """Regla anti-lavado (propuesta wow 2026-07-06): si la tinta del cliente es
    pastel (clara o desaturada), las bandas usan una versión PROFUNDA del mismo
    matiz (L<=0.50, S>=0.45); una tinta ya fuerte no se toca. sec se deriva
    del prim final para mantener el par coherente."""
    r, g, b = [x / 255.0 for x in prim]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l > 0.60 or s < 0.30:
        l, s = min(l, 0.50), max(s, 0.45)
        prim = tuple(int(round(x * 255)) for x in colorsys.hls_to_rgb(h, l, s))
        sec = tuple(int(x * 0.55) for x in prim)
    if luminancia(sec) >= luminancia(prim):
        sec = tuple(int(x * 0.55) for x in prim)
    return prim, sec


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

def fuente_que_quepa(d, txt, peso, tam, max_ancho, tam_min=18):
    """Baja el tamaño hasta que el texto entre en max_ancho (piso imprimible 18px)."""
    f = fuente(peso, tam)
    while tam > tam_min and d.textlength(txt, font=f) > max_ancho:
        tam -= 1
        f = fuente(peso, tam)
    return f


def campo(d, xy, etiqueta, valor, color_etq, color_val, centrado=False, tam_valor=30, max_ancho=None):
    """Estructura tipográfica de credencial: ETIQUETA en versalitas + valor en bold.
    max_ancho: auto-reduce el valor para razones sociales largas (no desbordar)."""
    x, y = xy
    f_e = fuente("semibold", 19)
    f_v = fuente("semibold", tam_valor)
    if max_ancho:
        f_v = fuente_que_quepa(d, valor, "semibold", tam_valor, max_ancho)
    if centrado:
        texto_tracking(d, (x, y), etiqueta, f_e, color_etq, tracking=4, centrado=True)
        d.text((x, y + 32), valor, font=f_v, fill=color_val, anchor="ma")
    else:
        texto_tracking(d, (x, y), etiqueta, f_e, color_etq, tracking=4)
        d.text((x, y + 32), valor, font=f_v, fill=color_val)


GRIS_ETIQUETA = (152, 154, 160)


def web_cliente(cliente):
    """Dominio ficticio pero personalizado con el nombre del cliente:
    'www.unileverandina.pe' vende la ilusión; 'www.suempresa.com' la mata.
    Usa las 2 primeras palabras para que razones sociales largas no lo deformen."""
    palabras = [p for p in re.split(r"\s+", cliente.strip()) if p]
    base = re.sub(r"[^a-z0-9]", "", slug(" ".join(palabras[:2])).lower())[:20] or "suempresa"
    return f"www.{base}.pe"


def estilo2_frontal(logo, pal, cliente):
    """Full color: color de marca pleno, logo en silueta blanca, panel blanco curvo al pie."""
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    col_txt = (255, 255, 255) if not claro else TINTA
    col_suave = mezcla(col_txt, prim, 0.18)
    t = Image.new("RGBA", (V_W, V_H), tuple(prim[:3]) + (255,))  # color PLANO (regla v5)
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
    campo(d, (V_W // 2, 806), "EMPRESA", cliente, col_suave, col_txt, centrado=True, max_ancho=530)
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
    d.text((V_W // 2, 922), web_cliente(cliente), font=fuente("semibold", 26), fill=(248, 247, 244), anchor="ma")
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
    campo(d, (78, 446), "EMPRESA", cliente, (140, 142, 150), ORO_CLARO, max_ancho=278)
    campo(d, (380, 446), "DNI", DATOS["id"].split()[-1], (140, 142, 150), (228, 228, 232))
    # foto circular con aro neutro fino: el oro vive SOLO en el marco perimetral
    t.alpha_composite(aro(296, (206, 208, 214), 3), (646, 172))
    t.alpha_composite(foto_circular(280), (654, 180))
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
    d.text((CARD_W // 2, 404), web_cliente(cliente), font=fuente("semibold", 28), fill=ORO_CLARO, anchor="ma")
    campo(d, (CARD_W // 2, 478), "VIGENCIA", "2026 — 2027", (140, 142, 150), (228, 228, 232),
          centrado=True, tam_valor=27)
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
    d.text((V_W // 2, 630), DATOS["nombre"], font=fuente("display-bold", 48), fill=TINTA, anchor="ma")
    d.text((V_W // 2, 706), DATOS["cargo"], font=fuente("regular", 30), fill=(110, 113, 120), anchor="ma")
    d.line([V_W // 2 - 60, 768, V_W // 2 + 60, 768], fill=tuple(oro[:3]), width=2)
    campo(d, (192, 820), "EMPRESA", cliente, GRIS_ETIQUETA, marca_legible(prim), centrado=True, tam_valor=28, max_ancho=265)
    campo(d, (462, 820), "DNI", DATOS["id"].split()[-1], GRIS_ETIQUETA, TINTA, centrado=True, tam_valor=28)
    # eco del arco al pie (bookend): el gesto institucional cierra la tarjeta
    d.ellipse([-200, V_H - 86, V_W + 200, V_H + 150], fill=tuple(prim[:3]))
    d.arc([-200, V_H - 86, V_W + 200, V_H + 150], 188, 352, fill=tuple(oro[:3]), width=3)
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
    d.text((V_W // 2, 692), f"{web_cliente(cliente)}  ·  (01) 700 0000",
           font=fuente("regular", 24), fill=GRIS_ETIQUETA, anchor="ma")
    d.line([V_W // 2 - 60, 768, V_W // 2 + 60, 768], fill=tuple(oro[:3]), width=2)
    d.ellipse([-200, V_H - 86, V_W + 200, V_H + 150], fill=tuple(prim[:3]))
    d.arc([-200, V_H - 86, V_W + 200, V_H + 150], 188, 352, fill=tuple(oro[:3]), width=3)
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo5_frontal(logo, pal, cliente):
    """Moderno: diagonal de marca a la derecha con la foto; nombre sans en dos
    pesos (light + bold) y pleca de marca — tipografía propia, distinta del E1."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    d.polygon([(704, 0), (CARD_W, 0), (CARD_W, CARD_H), (584, CARD_H)], fill=tuple(prim[:3]))
    d.line([704, 0, 584, CARD_H], fill=tuple(oro[:3]), width=3)
    # foto cortada con el MISMO ángulo de la diagonal: pertenece al panel, no flota
    foto = foto_carnet(315, 380).convert("RGBA")
    foto.putalpha(_mascara_suave(315, 380, lambda d2, w, h: d2.polygon(
        [(int(w * 71 / 315), 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1)], fill=255)))
    t.alpha_composite(foto, (642, 88))
    # área blanca: nombre sans en dos pesos, pleca en color de marca
    pegar_logo(t, logo, (64, 52, 300, 84), fondo_claro=True, tinte=prim_txt, alinear="izquierda")
    nombre, _, apellido = DATOS["nombre"].partition(" ")
    d.text((64, 188), nombre, font=fuente("light", 60), fill=TINTA)
    d.text((64, 262), apellido, font=fuente("bold", 60), fill=TINTA)
    d.rectangle([66, 372, 114, 378], fill=tuple(prim_txt[:3]))
    campo(d, (66, 420), "CARGO", DATOS["cargo"], GRIS_ETIQUETA, TINTA, tam_valor=28)
    campo(d, (66, 518), "EMPRESA", cliente, GRIS_ETIQUETA, prim_txt, tam_valor=28, max_ancho=258)
    campo(d, (348, 518), "DNI", DATOS["id"].split()[-1], GRIS_ETIQUETA, TINTA, tam_valor=28)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo5_reverso(logo, pal, cliente):
    """Reverso moderno: la diagonal cambia de lado y carga el QR; área blanca
    con normas y contacto."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    banda_txt = texto_sobre(prim)
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    d.polygon([(0, 0), (424, 0), (304, CARD_H), (0, CARD_H)], fill=tuple(prim[:3]))
    d.line([424, 0, 304, CARD_H], fill=tuple(oro[:3]), width=3)
    placa = placa_qr(cliente, 168)
    t.alpha_composite(placa, (66, 168))
    d.text((172, 408), "Escanee para validar", font=fuente("semibold", 23), fill=banda_txt, anchor="ma")
    pegar_logo(t, logo, (478, 70, 320, 90), fondo_claro=True, tinte=prim_txt, alinear="izquierda")
    d.text((478, 232), "Esta credencial es personal", font=fuente("semibold", 28), fill=TINTA)
    d.text((478, 272), "e intransferible.", font=fuente("semibold", 28), fill=TINTA)
    d.line([480, 356, 640, 356], fill=tuple(oro[:3]), width=2)
    campo(d, (480, 404), "SITIO WEB", web_cliente(cliente), GRIS_ETIQUETA, TINTA, tam_valor=27)
    campo(d, (480, 504), "CENTRAL", "(01) 700 0000", GRIS_ETIQUETA, TINTA, tam_valor=27)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo6_frontal(logo, pal, cliente):
    """Ejecutivo: marfil minimal — tipografía, un hairline a todo lo ancho y
    silencio. El gesto es la contención (refs reales: S. Abogados, NGR, K)."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    t = Image.new("RGBA", (CARD_W, CARD_H), tuple(MARFIL) + (255,))
    d = ImageDraw.Draw(t)
    pegar_logo(t, logo, (84, 64, 280, 86), fondo_claro=True, tinte=prim_txt, alinear="izquierda")
    d.line([84, 198, CARD_W - 84, 198], fill=tuple(oro[:3]), width=2)
    d.text((84, 252), DATOS["nombre"], font=fuente("display-bold", 58), fill=TINTA)
    d.text((84, 344), DATOS["cargo"], font=fuente("display-italic", 31), fill=(120, 122, 128))
    campo(d, (84, 478), "EMPRESA", cliente, GRIS_ETIQUETA, prim_txt, tam_valor=29, max_ancho=360)
    campo(d, (470, 478), "DNI", DATOS["id"].split()[-1], GRIS_ETIQUETA, TINTA, tam_valor=29)
    t.alpha_composite(foto_redondeada(204, 256, 12), (CARD_W - 84 - 204, 252))
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo6_reverso(logo, pal, cliente):
    """Reverso ejecutivo: dos hairlines enmarcan logo, QR directo sobre marfil
    y contacto. Quieto a propósito."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    t = Image.new("RGBA", (CARD_W, CARD_H), tuple(MARFIL) + (255,))
    d = ImageDraw.Draw(t)
    d.line([84, 92, CARD_W - 84, 92], fill=tuple(oro[:3]), width=2)
    pegar_logo(t, logo, (CARD_W // 2 - 150, 136, 300, 86), fondo_claro=True, tinte=prim_txt)
    t.paste(pseudo_qr(cliente, 184, bg=MARFIL), (CARD_W // 2 - 92, 268))
    campo(d, (CARD_W // 2 - 200, 478), "SITIO WEB", web_cliente(cliente),
          GRIS_ETIQUETA, TINTA, centrado=True, tam_valor=27)
    campo(d, (CARD_W // 2 + 200, 478), "VIGENCIA", "2026 — 2027",
          GRIS_ETIQUETA, TINTA, centrado=True, tam_valor=27)
    d.line([84, 588, CARD_W - 84, 588], fill=tuple(oro[:3]), width=2)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo7_frontal(logo, pal, cliente):
    """Pase de visita: rol protagonista en blanco + bloque de marca al pie con
    número de pase (patrón Niubiz del inventario real — sin foto, es un pase)."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    claro = luminancia(prim) >= 0.45
    t = Image.new("RGBA", (V_W, V_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    pegar_logo(t, logo, ((V_W - 320) // 2, 88, 320, 112), fondo_claro=True, tinte=prim_txt)
    texto_tracking(d, (V_W // 2, 304), "PASE DE ACCESO", fuente("semibold", 21),
                   GRIS_ETIQUETA, tracking=6, centrado=True)
    d.text((V_W // 2, 352), "VISITANTE", font=fuente("display-black", 84), fill=TINTA, anchor="ma")
    d.line([V_W // 2 - 60, 496, V_W // 2 + 60, 496], fill=tuple(oro[:3]), width=2)
    d.text((V_W // 2, 532), "Válido únicamente el día de emisión.",
           font=fuente("regular", 26), fill=GRIS_ETIQUETA, anchor="ma")
    bloque_y = 668
    d.rectangle([0, bloque_y, V_W, V_H], fill=tuple(prim[:3]))
    col_blq = (255, 255, 255) if not claro else TINTA
    texto_tracking(d, (V_W // 2, bloque_y + 70), "N° DE PASE", fuente("semibold", 20),
                   mezcla(col_blq, prim, 0.15), tracking=5, centrado=True)
    d.text((V_W // 2, bloque_y + 106), "0128", font=fuente("display-bold", 88), fill=col_blq, anchor="ma")
    txt_aut = f"Autorizado por {cliente}"
    d.text((V_W // 2, bloque_y + 256), txt_aut,
           font=fuente_que_quepa(d, txt_aut, "semibold", 25, V_W - 110),
           fill=mezcla(col_blq, prim, 0.2), anchor="ma")
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo7_reverso(logo, pal, cliente):
    """Reverso del pase: normas de visita en lista con plecas + QR de registro."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    claro = luminancia(prim) >= 0.45
    col_cab = (255, 255, 255) if not claro else TINTA
    t = Image.new("RGBA", (V_W, V_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, V_W, 150], fill=tuple(prim[:3]))
    texto_tracking(d, (V_W // 2, 62), "NORMAS DE VISITA", fuente("semibold", 24),
                   col_cab, tracking=6, centrado=True)
    normas = [
        "Porte el pase en un lugar visible",
        "Circule solo por zonas autorizadas",
        "Devuélvalo al concluir su visita",
    ]
    y = 226
    for n in normas:
        d.rectangle([84, y + 12, 108, y + 18], fill=tuple(prim_txt[:3]))
        d.text((132, y), n, font=fuente("regular", 27), fill=TINTA)
        y += 84
    d.line([V_W // 2 - 60, y + 24, V_W // 2 + 60, y + 24], fill=tuple(oro[:3]), width=2)
    t.paste(pseudo_qr(cliente + "-r", 190), ((V_W - 190) // 2, y + 80))
    d.text((V_W // 2, y + 304), "Registre su ingreso y salida",
           font=fuente("semibold", 26), fill=TINTA, anchor="ma")
    d.text((V_W // 2, y + 348), web_cliente(cliente),
           font=fuente("regular", 24), fill=GRIS_ETIQUETA, anchor="ma")
    d.rectangle([0, V_H - 14, V_W, V_H], fill=tuple(prim[:3]))
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo8_frontal(logo, pal, cliente):
    """Clásico: banda superior de marca con el logo y la empresa, cuerpo blanco
    con foto izquierda y columna de datos (patrón Niubiz / Los Olivos)."""
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    ALTO_B = 168
    d.rectangle([0, 0, CARD_W, ALTO_B], fill=tuple(prim[:3]))
    d.rectangle([0, ALTO_B, CARD_W, ALTO_B + 2], fill=tuple(oro[:3]))
    pieza = logo_tenido(logo, 300, 96, (255, 255, 255) if not claro else marca_legible(prim))
    t.alpha_composite(pieza, (64, 36 + (96 - pieza.height) // 2))
    d.text((CARD_W - 76, 84), cliente,
           font=fuente_que_quepa(d, cliente, "semibold", 32, 520),
           fill=texto_sobre(prim), anchor="rm")
    t.alpha_composite(foto_redondeada(232, 290, 14), (64, 258))
    d.text((348, 260), DATOS["nombre"], font=fuente("display-bold", 50), fill=TINTA)
    d.line([350, 348, 510, 348], fill=tuple(oro[:3]), width=2)
    campo(d, (350, 404), "CARGO", DATOS["cargo"], GRIS_ETIQUETA, TINTA, tam_valor=28)
    campo(d, (760, 404), "DNI", DATOS["id"].split()[-1], GRIS_ETIQUETA, TINTA, tam_valor=28)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo8_reverso(logo, pal, cliente):
    """Reverso clásico: banda superior eco, QR a la izquierda y contacto a la derecha."""
    prim, sec, oro = pal
    claro = luminancia(prim) >= 0.45
    t = Image.new("RGBA", (CARD_W, CARD_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    ALTO_B = 110
    d.rectangle([0, 0, CARD_W, ALTO_B], fill=tuple(prim[:3]))
    d.rectangle([0, ALTO_B, CARD_W, ALTO_B + 2], fill=tuple(oro[:3]))
    pieza = logo_tenido(logo, 240, 70, (255, 255, 255) if not claro else marca_legible(prim))
    t.alpha_composite(pieza, ((CARD_W - pieza.width) // 2, 20 + (70 - pieza.height) // 2))
    t.paste(pseudo_qr(cliente, 196), (96, 196))
    d.text((194, 416), "Escanee para validar", font=fuente("semibold", 23), fill=GRIS_ETIQUETA, anchor="ma")
    d.text((360, 218), "Esta credencial es personal", font=fuente("semibold", 28), fill=TINTA)
    d.text((360, 258), "e intransferible.", font=fuente("semibold", 28), fill=TINTA)
    d.line([362, 342, 522, 342], fill=tuple(oro[:3]), width=2)
    campo(d, (362, 390), "SITIO WEB", web_cliente(cliente), GRIS_ETIQUETA, TINTA, tam_valor=27)
    campo(d, (362, 490), "CENTRAL", "(01) 700 0000", GRIS_ETIQUETA, TINTA, tam_valor=27)
    t.putalpha(mascara_redondeada(CARD_W, CARD_H))
    return t


def estilo9_frontal(logo, pal, cliente):
    """Retrato: foto a sangre completa en la mitad superior con costura de oro,
    panel blanco de datos abajo (badge contemporáneo; ref. mitad-foto del inventario)."""
    prim, sec, oro = pal
    prim_txt = marca_legible(prim)
    t = Image.new("RGBA", (V_W, V_H), (255, 255, 255, 255))
    ALTO_F = 520
    t.paste(foto_carnet(V_W, ALTO_F), (0, 0))
    d = ImageDraw.Draw(t)
    d.rectangle([0, ALTO_F, V_W, ALTO_F + 6], fill=tuple(marca_legible(prim)[:3]))
    pegar_logo(t, logo, (64, ALTO_F + 30, 320, 92), fondo_claro=True, tinte=prim_txt, alinear="izquierda")
    d.text((64, ALTO_F + 158), DATOS["nombre"], font=fuente("display-bold", 50), fill=TINTA)
    d.text((64, ALTO_F + 240), DATOS["cargo"], font=fuente("regular", 29), fill=GRIS_ETIQUETA)
    campo(d, (64, ALTO_F + 314), "EMPRESA", cliente, GRIS_ETIQUETA, prim_txt, tam_valor=27, max_ancho=312)
    campo(d, (400, ALTO_F + 314), "DNI", DATOS["id"].split()[-1], GRIS_ETIQUETA, TINTA, tam_valor=27)
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo9_reverso(logo, pal, cliente):
    """Reverso retrato: mitad superior en color de marca con la silueta del logo,
    mitad blanca con QR y contacto — espejo del frontal."""
    prim, sec, oro = pal
    t = Image.new("RGBA", (V_W, V_H), (255, 255, 255, 255))
    d = ImageDraw.Draw(t)
    ALTO_F = 520
    d.rectangle([0, 0, V_W, ALTO_F], fill=tuple(prim[:3]))
    d.rectangle([0, ALTO_F, V_W, ALTO_F + 6], fill=tuple(marca_legible(prim)[:3]))
    # silueta SIEMPRE legible sobre el panel: blanca en color oscuro, tinta en claro
    tinte = (255, 255, 255) if luminancia(prim) < 0.45 else mezcla(TINTA, prim, 0.2)
    pieza = logo_tenido(logo, 380, 200, tinte)
    t.alpha_composite(pieza, ((V_W - pieza.width) // 2, 160 + (200 - pieza.height) // 2))
    t.paste(pseudo_qr(cliente + "-r", 190), ((V_W - 190) // 2, 566))
    d.text((V_W // 2, 788), "Escanee para validar la credencial",
           font=fuente("semibold", 26), fill=TINTA, anchor="ma")
    d.text((V_W // 2, 832), f"{web_cliente(cliente)}  ·  (01) 700 0000",
           font=fuente("regular", 24), fill=GRIS_ETIQUETA, anchor="ma")
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo10_frontal(logo, pal, cliente):
    """Nocturno: vertical oscuro, aro de la foto en color de marca,
    fila de campos y filo de marca al pie (refs UCV / China Polo verticales).
    Con paleta de respaldo (logo negro/monocromo) usa grafito medio para no
    quedar gemelo del Premium."""
    prim, sec, oro = pal
    fondo = mezcla((30, 30, 34), prim, 0.10) if saturacion(prim) > 0.12 else (72, 74, 80)
    acento = ajustar(prim, 1.45) if saturacion(prim) > 0.12 else ORO
    tinte_claro = ajustar(prim, 1.75) if saturacion(prim) > 0.12 else ORO_CLARO
    t = Image.new("RGBA", (V_W, V_H), tuple(fondo[:3]) + (255,))
    d = ImageDraw.Draw(t)
    pegar_logo(t, logo, ((V_W - 320) // 2, 76, 320, 110), fondo_claro=False, tinte=tinte_claro)
    t.alpha_composite(aro(300, acento, 5), ((V_W - 300) // 2, 264))
    t.alpha_composite(foto_circular(282), ((V_W - 282) // 2, 273))
    d.text((V_W // 2, 642), DATOS["nombre"], font=fuente("display-bold", 50), fill=(246, 245, 242), anchor="ma")
    d.text((V_W // 2, 718), DATOS["cargo"], font=fuente("regular", 29), fill=(170, 172, 180), anchor="ma")
    d.line([V_W // 2 - 60, 780, V_W // 2 + 60, 780], fill=tuple(oro[:3]), width=2)
    campo(d, (192, 830), "EMPRESA", cliente, (140, 142, 150), tinte_claro, centrado=True, tam_valor=28, max_ancho=265)
    campo(d, (462, 830), "DNI", DATOS["id"].split()[-1], (140, 142, 150), (228, 228, 232), centrado=True, tam_valor=28)
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


def estilo10_reverso(logo, pal, cliente):
    """Reverso nocturno: logo arriba, QR sobre placa y contacto en claro."""
    prim, sec, oro = pal
    fondo = mezcla((30, 30, 34), prim, 0.10) if saturacion(prim) > 0.12 else (72, 74, 80)
    acento = ajustar(prim, 1.45) if saturacion(prim) > 0.12 else ORO
    tinte_claro = ajustar(prim, 1.75) if saturacion(prim) > 0.12 else ORO_CLARO
    t = Image.new("RGBA", (V_W, V_H), tuple(fondo[:3]) + (255,))
    d = ImageDraw.Draw(t)
    pegar_logo(t, logo, ((V_W - 300) // 2, 96, 300, 104), fondo_claro=False, tinte=tinte_claro)
    d.line([V_W // 2 - 60, 286, V_W // 2 + 60, 286], fill=tuple(oro[:3]), width=2)
    t.alpha_composite(placa_qr(cliente + "-r", 196), ((V_W - 240) // 2, 360))
    d.text((V_W // 2, 668), "Escanee para validar la credencial",
           font=fuente("semibold", 26), fill=(228, 228, 232), anchor="ma")
    d.text((V_W // 2, 714), web_cliente(cliente), font=fuente("semibold", 25), fill=tinte_claro, anchor="ma")
    d.text((V_W // 2, 850), "Esta credencial es personal e intransferible.",
           font=fuente("regular", 23), fill=(150, 152, 160), anchor="ma")
    d.rectangle([0, V_H - 10, V_W, V_H], fill=tuple(acento[:3]))
    t.putalpha(mascara_redondeada(V_W, V_H))
    return t


# Los números de cara al vendedor/cliente salen del ORDEN de esta lista
# (el nombre interno de las funciones es histórico). Tope del sistema: 9 plantillas;
# una idea nueva entra solo si desplaza a la de menor puntuación (loop 2026-06-12:
# Nocturno desplazó al Corporativo de banda lateral, cubierto por el Clásico).
ESTILOS = [
    ("Estilo 1 — Clásico", estilo8_frontal, estilo8_reverso),
    ("Estilo 2 — Full color", estilo2_frontal, estilo2_reverso),
    ("Estilo 3 — Premium", estilo3_frontal, estilo3_reverso),
    ("Estilo 4 — Institucional", estilo4_frontal, estilo4_reverso),
    ("Estilo 5 — Moderno", estilo5_frontal, estilo5_reverso),
    ("Estilo 6 — Ejecutivo", estilo6_frontal, estilo6_reverso),
    ("Estilo 7 — Retrato", estilo9_frontal, estilo9_reverso),
    ("Estilo 8 — Nocturno", estilo10_frontal, estilo10_reverso),
    ("Estilo 9 — Pase de visita", estilo7_frontal, estilo7_reverso),
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
    ESC = 0.48         # escala ÚNICA: el cliente compara diseños, no tamaños
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
            fr = frontal.resize((int(frontal.width * ESC), int(frontal.height * ESC)), Image.LANCZOS)
            rv = reverso.resize((int(reverso.width * ESC), int(reverso.height * ESC)), Image.LANCZOS)
            if frontal.width > frontal.height:  # horizontal: apiladas
                alto_col = fr.height + rv.height + 60
                y0 = y_fila + (zona_h - alto_col) // 2
                con_sombra(canvas, fr, (x0 + (col_w - fr.width) // 2, y0), 14, 60)
                con_sombra(canvas, rv, (x0 + (col_w - rv.width) // 2, y0 + fr.height + 60), 14, 60)
            else:  # vertical: lado a lado
                ancho_par = fr.width * 2 + 50
                y0 = y_fila + (zona_h - fr.height) // 2
                con_sombra(canvas, fr, (x0 + (col_w - ancho_par) // 2, y0), 14, 60)
                con_sombra(canvas, rv, (x0 + (col_w - ancho_par) // 2 + fr.width + 50, y0), 14, 60)

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


def _hex_a_rgb(c):
    """'#RRGGBB' o (r,g,b) -> (r,g,b)."""
    if isinstance(c, (tuple, list)):
        return tuple(int(x) for x in c[:3])
    c = str(c).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


# PNG transparente 1×1 (data URI) para vaciar logo/foto en el fondo del compositor.
_PIXEL_TRANSP = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1"
                 "HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def _prim_sec(logo, ajustes):
    color = (ajustes or {}).get("color")
    if color:
        prim = _hex_a_rgb(color)
        return paleta_marca(prim, tuple(int(x * 0.6) for x in prim))
    prim, sec = paleta_del_logo(logo)
    return paleta_marca(prim, sec)


def _ctx_elementos(logo, cliente, ajustes, mostrar):
    """ctx del modelo con SOLO los elementos en 'mostrar' visibles (logo/foto/nombre/
    cargo/datos); el resto se vacía. Sirve para el fondo limpio (mostrar=∅) y para
    derivar las anclas (un elemento a la vez)."""
    from plantillas import construir_contexto
    ajustes = ajustes or {}
    prim, sec = _prim_sec(logo, ajustes)
    # 'datos' incluye la fila Empresa -> solo pasamos cliente cuando datos está visible
    cli = cliente if ("datos" in mostrar) else ""
    ctx = construir_contexto(logo, prim, sec, cli, ajustes)
    if "logo" not in mostrar:
        ctx["logo_uri"] = _PIXEL_TRANSP
    if "foto" not in mostrar:
        ctx["foto_uri"] = _PIXEL_TRANSP
    if "datos" not in mostrar:
        ctx["filas"] = []
    nombre = ctx["datos"].get("nombre", "") if "nombre" in mostrar else ""
    cargo = ctx["datos"].get("cargo", "") if "cargo" in mostrar else ""
    ctx["datos"] = dict(ctx["datos"], nombre=nombre, cargo=cargo)
    return ctx


def _render_elementos(logo, cliente, ajustes, mostrar):
    """Rasteriza el modelo mostrando solo 'mostrar'. Devuelve PIL.Image a tamaño CR80."""
    from plantillas import cara
    from render import render_caras
    ctx = _ctx_elementos(logo, cliente, ajustes, mostrar)
    html, w, h = cara((ajustes or {})["modelo"], "frontal", ctx)
    img = render_caras([(html, w, h)])[0]
    destino = (CARD_W, CARD_H) if img.width > img.height else (V_W, V_H)
    return img.resize(destino, Image.LANCZOS)


def fondo_de_modelo(logo, cliente, ajustes):
    """SOLO la decoración del modelo (sin logo/foto/datos/héroe), para el compositor."""
    return _render_elementos(logo, cliente, ajustes, set())


def anclas_de_modelo(logo, cliente, ajustes):
    """Deriva la CAJA real (normalizada) de cada elemento del modelo por diferencia de
    imagen contra el fondo limpio. Devuelve {capa_id: {x,y,w,h}} para sembrar el editor
    con el layout NATIVO del modelo (arranca ordenado)."""
    from PIL import ImageChops
    import estado
    bg = _render_elementos(logo, cliente, ajustes, set())
    W, H = bg.size
    out = {}
    for cid in estado.CAPAS_IDS:
        el = _render_elementos(logo, cliente, ajustes, {cid})
        diff = ImageChops.difference(el.convert("RGB"), bg.convert("RGB"))
        bbox = diff.getbbox()
        if bbox:
            x0, y0, x1, y1 = bbox
            out[cid] = {"x": x0 / W, "y": y0 / H, "w": (x1 - x0) / W, "h": (y1 - y0) / H}
        else:
            out[cid] = dict(estado.capas_inicial("H")[cid])
    return out


def _foto_pil(ajustes):
    """Foto del cliente (si el vendedor la subió) o la del demo. Devuelve PIL RGBA."""
    ruta = (ajustes or {}).get("foto_ruta")
    if ruta and os.path.exists(ruta):
        return Image.open(ruta).convert("RGBA")
    from plantillas.base import FOTO_PERSONA
    return Image.open(FOTO_PERSONA).convert("RGBA")


def render_modelo(logo, cliente, ajustes, escala=1.0):
    """EL MODELO MANDA: el boceto base lo dibuja el modelo en HTML (texto, decoración y
    color perfectos, idéntico al catálogo). La FOTO la pinta SIEMPRE el modelo —que la
    enmarca según su forma—; el vendedor solo la sube. Solo el LOGO se vuelve capa (overlay)
    si el vendedor lo MUEVE (caja['movido']=True). Sin logo movido = render puro del modelo."""
    from plantillas import cara, construir_contexto
    from render import render_caras
    import lienzo
    ajustes = ajustes or {}
    capas = ajustes.get("capas") or {}
    logo_movido = bool(capas.get("logo", {}).get("movido"))
    prim, sec = _prim_sec(logo, ajustes)
    ctx = construir_contexto(logo, prim, sec, cliente, ajustes)
    # La FOTO la pinta SIEMPRE el modelo (la enmarca según su forma); el vendedor solo la sube.
    foto_ruta = ajustes.get("foto_ruta")
    if foto_ruta and os.path.exists(foto_ruta):
        from plantillas.base import _b64_img
        ctx["foto_uri"] = _b64_img(Image.open(foto_ruta).convert("RGB"))
    if logo_movido:
        ctx["logo_uri"] = _PIXEL_TRANSP
    html, w, h = cara(ajustes["modelo"], "frontal", ctx)
    base = render_caras([(html, w, h)])[0]
    destino = (CARD_W, CARD_H) if base.width > base.height else (V_W, V_H)
    base = base.resize(destino, Image.LANCZOS)
    W = int(base.width * escala)
    H = int(base.height * escala)
    if not logo_movido:                       # nada movido = render puro del modelo (perfecto)
        return base if escala == 1.0 else base.resize((W, H), Image.LANCZOS)
    recursos = {"logo": {"tipo": "imagen", "img": logo, "ajuste": "contain"}}
    return lienzo.componer(base, {"logo": capas["logo"]}, recursos, W, H)


def exportar_personalizado(logo, cliente, ajustes, carpeta_salida=None, pdf=True, png=True):
    """Renderiza el modelo elegido con sus ajustes y lo exporta como PNG y/o PDF
    (boceto de venta). Devuelve (carpeta, [rutas]). 'logo' ya viene de cargar_logo()."""
    from plantillas import catalogo
    from folleto import armar_pdf
    cliente = (cliente or "Cliente").strip() or "Cliente"
    img = render_modelo(logo, cliente, ajustes)
    modelo = next(m for m in catalogo() if m.clave == ajustes["modelo"])
    if carpeta_salida is None:
        from datetime import datetime
        sello = datetime.now().strftime("%Y%m%d-%H%M%S")
        carpeta_salida = os.path.join(RUTA_BASE, "salida", "%s-%s" % (slug(cliente), sello))
    os.makedirs(carpeta_salida, exist_ok=True)
    archivos = []
    base = "%s-%s" % (modelo.clave, slug(cliente))
    if png:
        rp = os.path.join(carpeta_salida, base + ".png")
        img.convert("RGB").save(rp, optimize=True)
        archivos.append(rp)
    if pdf:
        rpdf = os.path.join(carpeta_salida, "boceto-%s.pdf" % slug(cliente))
        armar_pdf(cliente, logo, [(modelo.nombre, modelo.orientacion, img)], rpdf)
        archivos.append(rpdf)
    return carpeta_salida, archivos


def generar(ruta_logo, cliente, carpeta_salida=None, color=None):
    """Arma la PROPUESTA personalizada: PDF curado top-6 (estrella + 5 alternativas
    con nombres comerciales) pintado con la marca del cliente + carpeta para-diseno
    con las caras limpias de los 18 modelos.
    color: opcional '#RRGGBB' o (r,g,b); si no, el color sale de la tinta del logo."""
    cliente = (cliente or "Cliente").strip() or "Cliente"
    logo = cargar_logo(ruta_logo)
    if color:
        prim = _hex_a_rgb(color)
        sec = tuple(int(x * 0.6) for x in prim)   # tono más oscuro como secundario
    else:
        prim, sec = paleta_del_logo(logo)
    prim, sec = paleta_marca(prim, sec)

    # --- frentes de cada modelo del catálogo, maquetados en HTML/CSS y rasterizados ---
    from plantillas import cara, construir_contexto, catalogo
    from plantillas.curaduria import elegir_top, nombre_comercial
    import render
    import folleto
    ctx = construir_contexto(logo, prim, sec, cliente)
    modelos = catalogo()
    items = [cara(m.clave, "frontal", ctx) for m in modelos]   # SOLO frentes (folleto)
    caras = render.render_caras(items)                         # PIL.Image a escala 2x

    def a_cr80(img):
        # baja del render 2x al tamaño real de imprenta (CR80 300 dpi) con LANCZOS
        destino = (CARD_W, CARD_H) if img.width > img.height else (V_W, V_H)
        return img.resize(destino, Image.LANCZOS)

    frentes = [a_cr80(c) for c in caras]

    if carpeta_salida is None:
        carpeta_salida = os.path.join(RUTA_BASE, "salida", f"{slug(cliente)}-{date.today():%Y-%m-%d}")
        # Limpiar corridas anteriores del mismo cliente/día (no apilar archivos viejos).
        if os.path.isdir(carpeta_salida):
            shutil.rmtree(carpeta_salida, ignore_errors=True)
    os.makedirs(carpeta_salida, exist_ok=True)

    # caras limpias a tamaño real de imprenta (CR80 300 dpi): base para el diseñador / CardPresso
    carpeta_diseno = os.path.join(carpeta_salida, "para-diseno")
    os.makedirs(carpeta_diseno, exist_ok=True)
    rutas_diseno = []
    for m, fr in zip(modelos, frentes):
        ruta = os.path.join(carpeta_diseno, f"{m.clave}-frontal.png")
        fr.convert("RGB").save(ruta, optimize=True)
        rutas_diseno.append(ruta)

    # PDF propuesta curada (portada v2 + estrella + 5 alternativas + anexo con
    # el resto del catálogo + CTA). para-diseno conserva los 18 igual.
    top = elegir_top(prim)
    por_clave = {m.clave: (m, fr) for m, fr in zip(modelos, frentes)}

    def item(clave):
        m, fr = por_clave[clave]
        return (nombre_comercial(clave), m.orientacion, fr)

    resto = [item(m.clave) for m in modelos if m.clave not in top]
    ruta_pdf = os.path.join(carpeta_salida, f"catalogo-{slug(cliente)}.pdf")
    folleto.armar_propuesta(cliente, logo, item(top[0]),
                            [item(c) for c in top[1:]], ruta_pdf, (prim, sec),
                            resto=resto)

    return carpeta_salida, [ruta_pdf] + rutas_diseno


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Uso: py motor.py "ruta\\al\\logo.png" "Nombre del Cliente"')
        sys.exit(1)
    carpeta, archivos = generar(sys.argv[1], sys.argv[2])
    print(f"Listo: {carpeta}")
    for a in archivos:
        print(" -", os.path.basename(a))
