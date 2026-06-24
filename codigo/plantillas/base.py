# -*- coding: utf-8 -*-
"""Utilidades compartidas de las plantillas: contexto, CSS base, shell, iconos,
foto demo y helpers de color. Autocontenido: logo y foto en base64, fuentes
horneadas vía @font-face.

El LAYOUT lo pone cada modelo (paquete plantillas.modelos); el COLOR DE ACENTO sale
del logo del cliente (--acc = marca legible, --oscuro = banda con texto blanco). El logo
del cliente va en su tinta real, NUNCA se recolorea. Lo rasteriza render.py (Edge/Playwright)."""
import base64
import hashlib
import io
import os

from PIL import Image, ImageDraw, ImageFilter

# base.py vive en codigo/plantillas/ → RUTA debe apuntar a codigo/ (donde están las fuentes y la foto)
RUTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOTO_PERSONA = os.path.join(RUTA, "foto-persona.jpg")
F_PLAYFAIR = os.path.join(RUTA, "fuente-display.ttf")   # Playfair Display (OFL)
F_INTER = os.path.join(RUTA, "inter.ttf")
F_INTER_SB = os.path.join(RUTA, "inter-semibold.ttf")

DATOS = {"nombre": "Carlos González M.", "cargo": "Supervisor de Operaciones", "id": "45678123",
         "tipo_sangre": "O+", "codigo": "10052", "fecha": "12/2027"}

# Campos extra UNIVERSALES: cualquier modelo los muestra (vía _shell -> _bloque_extra),
# así el editor los ofrece en TODOS los modelos sin tocar cada plantilla.
CAMPOS_EXTRA = ("tipo_sangre", "codigo", "fecha", "web")
CAMPOS_LABEL = {"tipo_sangre": "Tipo de sangre", "codigo": "Código",
                "fecha": "Fecha de venc.", "web": "Web"}
ORO = "#c9a14a"
H, V = (1011, 638), (638, 1011)
MG = 60  # margen de seguridad de impresion (~5mm)


def variante_de(cliente, n=3):
    return int(hashlib.md5((cliente or "x").encode("utf-8")).hexdigest(), 16) % n


# ---------- utilidades de imagen/color ----------

def _b64_img(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, fmt)
    return "data:image/%s;base64,%s" % (fmt.lower(), base64.b64encode(buf.getvalue()).decode())


def _b64_file(path, mime):
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


def _rgb(c):
    return "rgb(%d,%d,%d)" % tuple(int(x) for x in c[:3])


def _ajustar(c, f):
    if f <= 1:
        return tuple(int(x * f) for x in c[:3])
    return tuple(int(x + (255 - x) * (f - 1)) for x in c[:3])


def _nombre2(nombre):
    p = nombre.split()
    if len(p) <= 1:
        return nombre, ""
    return p[0], " ".join(p[1:])


# ---------- iconos line-art (SVG inline, color configurable) ----------

_ICON_PATHS = {
    "maletin": "<rect x='3' y='7.5' width='18' height='12.5' rx='2'/><path d='M8 7.5V5.5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'/><path d='M3 12h18'/>",
    "persona": "<circle cx='12' cy='8' r='3.6'/><path d='M5.5 20a6.5 6.5 0 0 1 13 0'/>",
    "edificio": "<rect x='5' y='3' width='14' height='18' rx='1.2'/><path d='M9 7h.01M15 7h.01M9 11h.01M15 11h.01M9 15h.01M15 15h.01'/><path d='M11 21v-3h2v3'/>",
    "escudo": "<path d='M12 3l7 3v5c0 4.6-3 7.9-7 9.6-4-1.7-7-5-7-9.6V6z'/><path d='M9 12l2 2 4-4'/>",
    "globo": "<circle cx='12' cy='12' r='9'/><path d='M3 12h18'/><path d='M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18'/>",
    "calendario": "<rect x='3.5' y='5' width='17' height='16' rx='2'/><path d='M3.5 9.5h17M8 3v3.5M16 3v3.5'/>",
}


def _icono(nombre, color, tam=26, sw=1.8):
    return ("<svg width='%d' height='%d' viewBox='0 0 24 24' fill='none' stroke='%s' "
            "stroke-width='%s' stroke-linecap='round' stroke-linejoin='round'>%s</svg>"
            % (tam, tam, color, sw, _ICON_PATHS[nombre]))


# ---------- foto del demo ----------

def _silueta_uri(prim):
    """Placeholder estilo FOTO CARNET (fondo claro uniforme + busto centrado)."""
    W, Hh = 660, 825           # proporción carnet 4:5
    SS = 2
    w, h = W * SS, Hh * SS
    base = Image.new("RGB", (w, h), (233, 236, 240))
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    col = (156, 163, 173, 255)
    cx = w // 2
    rcab = int(150 * SS)
    cy = int(300 * SS)
    d.ellipse([cx - rcab, cy - rcab, cx + rcab, cy + rcab], fill=col)
    d.ellipse([cx - int(308 * SS), cy + rcab - int(6 * SS),
               cx + int(308 * SS), h + int(250 * SS)], fill=col)
    capa = capa.filter(ImageFilter.GaussianBlur(2.4 * SS))
    base = Image.alpha_composite(base.convert("RGBA"), capa).convert("RGB")
    base = base.resize((W, Hh), Image.LANCZOS)
    return _b64_img(base, "JPEG")


def _foto_uri(prim):
    # Default: foto profesional real (decisión Diego 2026-06-15: se ve terminado).
    # MOCKUPS_FOTO=silueta para el placeholder gris neutro.
    modo = os.environ.get("MOCKUPS_FOTO", "color").lower()
    if modo == "silueta":
        return _silueta_uri(prim)
    return _b64_file(FOTO_PERSONA, "image/jpeg")


# ---------- contexto ----------

def _filas_de(ajustes):
    """Filas de datos del vendedor (DNI + las que agregó). La Empresa la antepone cada
    modelo vía filas_html(con_empresa=True), porque algunos ya la muestran aparte."""
    filas = []
    for f in ajustes.get("filas", []):
        etq = (f.get("etiqueta") or "").strip()
        if etq:
            filas.append((etq, (f.get("valor") or "").strip()))
    return filas


def construir_contexto(logo, prim, sec, cliente, ajustes=None):
    from motor import web_cliente, luminancia, marca_legible, pseudo_qr, distancia, saturacion
    ajustes = ajustes or {}
    textos = ajustes.get("textos", {})
    # empresa = campo de arriba (marca web/monograma); cae al cliente pasado al render
    empresa = (ajustes.get("empresa") or textos.get("empresa") or cliente)
    oscuro = luminancia(prim) < 0.45
    # color secundario de la marca como ACENTO que "puntua" (5-10%): solo si es
    # realmente distinto y con color; si no, cae al oro. Regla: un color manda, otro puntua.
    sec_distinta = distancia(prim, sec) > 70 and saturacion(sec) > 0.18
    acc2 = marca_legible(sec) if sec_distinta else None
    # textos demo con overrides del usuario (copia: NO muta el DATOS global)
    datos = dict(DATOS)
    datos.update({k: v for k, v in textos.items() if v and k in DATOS})
    return {
        "_prim": tuple(int(x) for x in prim[:3]),
        "logo_uri": _b64_img(logo),
        "foto_uri": _foto_uri(prim),
        "qr_uri": _b64_img(pseudo_qr(empresa, 360)),
        "prim_css": _rgb(prim),
        "medio_css": _rgb(_ajustar(prim, 0.58)),
        "oscuro_css": _rgb(_ajustar(prim, 0.22)),
        "claro_css": _rgb(_ajustar(prim, 1.7)),
        "prim_legible": _rgb(marca_legible(prim)),
        "acc2_css": _rgb(acc2) if acc2 else ORO,
        "txt_sobre_prim": "#ffffff" if oscuro else "#1d1f24",
        "logo_oscuro": oscuro,
        "variante": variante_de(empresa),
        "cliente": empresa,
        "monograma": ("".join(w[0] for w in (empresa or "").split()[:2]).upper() or "•"),
        "web": web_cliente(empresa),
        "datos": datos,
        "logo_pos": ajustes.get("logo_pos", "default"),
        "filas": _filas_de(ajustes),
    }


def css_base():
    pf = _b64_file(F_PLAYFAIR, "font/ttf")
    inter = _b64_file(F_INTER, "font/ttf")
    inter_sb = _b64_file(F_INTER_SB, "font/ttf")
    return (
        "@font-face{font-family:'Playfair';src:url(%s) format('truetype');font-weight:400 900;}"
        "@font-face{font-family:'Inter';src:url(%s) format('truetype');font-weight:400;}"
        "@font-face{font-family:'Inter';src:url(%s) format('truetype');font-weight:600 800;}"
        "*{margin:0;padding:0;box-sizing:border-box}"
        "body{margin:0;font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased}"
        # filas de datos (etiqueta:valor) compartidas: el modelo las coloca con filas_html()
        ".fdato{font-size:26px;line-height:1.28;letter-spacing:.005em}"
        ".fdato .fetq{color:var(--acc);font-weight:800}"
        ".fdato .fval{color:#262626;font-weight:600}"
        ".fdark .fdato .fval{color:#ececef}"
        ".datos{display:grid;gap:5px;margin-top:12px}"
        % (pf, inter, inter_sb)
    )


def _root(ctx):
    return (":root{--prim:%s;--medio:%s;--oscuro:%s;--claro:%s;--oro:%s;--acc:%s;--acc2:%s;--txtprim:%s;}"
            % (ctx["prim_css"], ctx["medio_css"], ctx["oscuro_css"],
               ctx["claro_css"], ORO, ctx["prim_legible"], ctx["acc2_css"], ctx["txt_sobre_prim"]))


def filas_html(ctx, con_empresa=True):
    """HTML de las filas de datos (etiqueta: valor) para que el MODELO las dibuje en su
    zona de datos. con_empresa=True antepone Empresa (los modelos que ya la muestran aparte
    pasan False). Estilo base en css_base (.fdato); fondo oscuro -> clase 'fdark' en la tarjeta."""
    filas = list(ctx.get("filas", []))
    if con_empresa:
        filas = [("Empresa", ctx.get("cliente", ""))] + filas
    n = len(filas)
    # achica el texto cuando hay muchos campos, para que entren en modelos con poco espacio
    fs = 27 if n <= 2 else 24 if n <= 3 else 21 if n <= 4 else 18 if n <= 6 else 16
    out = []
    for etq, val in filas:
        if val:
            out.append("<div class='fdato' style='font-size:%dpx'><span class='fetq'>%s</span> "
                       "<span class='fval'>%s</span></div>" % (fs, etq, val))
        else:
            out.append("<div class='fdato' style='font-size:%dpx'><span class='fetq'>%s</span></div>"
                       % (fs, etq))
    return "".join(out)


def _shell(ctx, clase, css_estilo, cuerpo, ancho, alto):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>%s%s"
            ".card{width:%dpx;height:%dpx;position:relative;overflow:hidden}%s"
            "</style></head><body><div class='card %s'>%s</div></body></html>"
            % (css_base(), _root(ctx), ancho, alto, css_estilo, clase, cuerpo))


# ⛔ REGLA FIJA — EL LOGO DEL CLIENTE NUNCA SE RECOLOREA (decisión Diego 2026-06-15).
# Se respeta SIEMPRE su tinta original; solo se ajusta tamaño/posición. Prohibido
# brightness(0)/invert/duotono/teñido. Todos los fondos son claros (blanco/crema), así
# el logo en color real siempre se lee. El color de marca tiñe el DISEÑO, no el logo.
