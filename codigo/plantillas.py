# -*- coding: utf-8 -*-
"""HTML/CSS de cada cara de credencial (3 direcciones: Aurora/Editorial/Glass).
Autocontenido: logo y foto en base64, fuentes horneadas via @font-face. El color
y el tratamiento salen del logo real (varia segun la marca). Lo rasteriza render.py.

v10: remates de acabado (íconos, panel de datos con borde + divisor, marco fino en
la foto, editorial con foto a sangre + curva, glass con paneles de vidrio). Sobre la
grilla consistente de v9 (margen de seguridad, foto frontal, nombre en 2 líneas)."""
import base64
import glob as _glob
import hashlib
import io
import os

from PIL import Image, ImageDraw, ImageFilter

RUTA = os.path.dirname(os.path.abspath(__file__))
FOTO_PERSONA = os.path.join(RUTA, "foto-persona.jpg")
F_PLAYFAIR = os.path.join(RUTA, "fuente-display.ttf")   # Playfair Display (OFL)
F_INTER = os.path.join(RUTA, "inter.ttf")
F_INTER_SB = os.path.join(RUTA, "inter-semibold.ttf")

DATOS = {"nombre": "Carlos González M.", "cargo": "Supervisor de Operaciones", "id": "45678123"}
ORO = "#c9a14a"
H, V = (1011, 638), (638, 1011)
MG = 60  # margen de seguridad de impresion (~5mm)

_BG_AURORA = [
    ("radial-gradient(120% 140% at 12% 8%, var(--medio) 0%, transparent 42%),"
     "radial-gradient(120% 130% at 95% 95%, var(--prim) 0%, transparent 38%),"
     "linear-gradient(135deg, var(--oscuro), #0c0e11 75%)"),
    ("radial-gradient(100% 120% at 88% 6%, var(--prim) 0%, transparent 40%),"
     "linear-gradient(160deg, #0b0d10 0%, var(--oscuro) 55%, var(--medio) 135%)"),
    ("radial-gradient(150% 120% at 50% -12%, var(--medio) 0%, transparent 46%),"
     "radial-gradient(90% 90% at 10% 100%, var(--prim) 0%, transparent 40%),"
     "linear-gradient(180deg, var(--oscuro), #0b0d10 82%)"),
]
_BG_GLASS = [
    ("radial-gradient(90% 120% at 85% 8%, rgba(255,255,255,.26), transparent 45%),"
     "radial-gradient(120% 120% at 8% 96%, var(--oscuro), transparent 55%),"
     "linear-gradient(150deg, var(--prim), var(--medio))"),
    ("radial-gradient(100% 100% at 15% 8%, rgba(255,255,255,.22), transparent 42%),"
     "linear-gradient(165deg, var(--medio), var(--prim) 68%, var(--oscuro))"),
    ("radial-gradient(120% 130% at 92% 96%, rgba(255,255,255,.20), transparent 46%),"
     "radial-gradient(80% 80% at 6% 8%, var(--claro), transparent 40%),"
     "linear-gradient(200deg, var(--prim), var(--oscuro))"),
]
_BG_EDIT_BANDA = [
    "linear-gradient(160deg,var(--prim),var(--medio))",
    "linear-gradient(205deg,var(--medio),var(--prim) 70%,var(--oscuro))",
    "linear-gradient(150deg,var(--prim),var(--oscuro))",
]


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
}


def _icono(nombre, color, tam=26, sw=1.8):
    return ("<svg width='%d' height='%d' viewBox='0 0 24 24' fill='none' stroke='%s' "
            "stroke-width='%s' stroke-linecap='round' stroke-linejoin='round'>%s</svg>"
            % (tam, tam, color, sw, _ICON_PATHS[nombre]))


# ---------- banco de fondos (recoloreados a la marca) ----------

def _duotono(gray, sombra, luz):
    lut = []
    for ch in range(3):
        a, b = sombra[ch], luz[ch]
        lut.extend(int(a + (b - a) * i / 255) for i in range(256))
    return gray.convert("RGB").point(lut)


def _recolorear_fondo(ruta, prim, estilo):
    img = Image.open(ruta).convert("L")
    if estilo == "aurora":
        sombra, luz = _ajustar(prim, 0.10), _ajustar(prim, 0.80)
    elif estilo == "glass":
        sombra, luz = _ajustar(prim, 0.60), _ajustar(prim, 1.45)
    else:
        sombra, luz = (236, 234, 230), (252, 250, 247)
    return _duotono(img, sombra, luz)


def fondo_imagen(estilo, ctx):
    archivos = sorted(_glob.glob(os.path.join(RUTA, "fondo-%s-*.jpg" % estilo)))
    if not archivos:
        return None
    idx = variante_de(ctx["cliente"], len(archivos))
    img = _recolorear_fondo(archivos[idx], ctx["_prim"], estilo)
    return _b64_img(img, "JPEG")


# ---------- foto del demo: 3 estrategias (color / silueta / duotono) ----------

def _silueta_uri(prim):
    """Placeholder estilo FOTO CARNET (DNI/pasaporte): fondo claro uniforme y
    busto centrado con aire arriba — cabeza completa, hombros en la base, sin
    cortes ni descuadre. Intencional para un demo, sin el uncanny de una cara IA."""
    W, Hh = 660, 880           # proporción carnet (≈3:4)
    SS = 2                      # supersample para bordes suaves
    w, h = W * SS, Hh * SS
    base = Image.new("RGB", (w, h), (233, 236, 240))   # fondo carnet gris-celeste claro
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    col = (156, 163, 173, 255)
    cx = w // 2
    rcab = int(150 * SS)
    cy = int(312 * SS)                                  # cabeza con ~17% de aire arriba
    d.ellipse([cx - rcab, cy - rcab, cx + rcab, cy + rcab], fill=col)        # cabeza
    d.ellipse([cx - int(308 * SS), cy + rcab - int(6 * SS),                  # hombros amplios
               cx + int(308 * SS), h + int(250 * SS)], fill=col)
    capa = capa.filter(ImageFilter.GaussianBlur(2.4 * SS))
    base = Image.alpha_composite(base.convert("RGBA"), capa).convert("RGB")
    base = base.resize((W, Hh), Image.LANCZOS)
    return _b64_img(base, "JPEG")


def _foto_duotono_uri(prim):
    """Foto IA tratada en duotono del color de marca: se ve editorial/intencional
    y disimula el 'realismo fallido' de la cara IA."""
    img = Image.open(FOTO_PERSONA).convert("L")
    duo = _duotono(img, _ajustar(prim, 0.30), (244, 244, 246))
    return _b64_img(duo, "JPEG")


def _foto_uri(prim):
    # Default: silueta carnet (decisión Diego 2026-06-15: la cara IA se veía "off").
    # MOCKUPS_FOTO=duotono|color para las otras estrategias.
    modo = os.environ.get("MOCKUPS_FOTO", "silueta").lower()
    if modo == "duotono":
        return _foto_duotono_uri(prim)
    if modo == "color":
        return _b64_file(FOTO_PERSONA, "image/jpeg")
    return _silueta_uri(prim)


# ---------- contexto ----------

def construir_contexto(logo, prim, sec, cliente):
    from motor import web_cliente, luminancia, marca_legible, pseudo_qr
    oscuro = luminancia(prim) < 0.45
    return {
        "_prim": tuple(int(x) for x in prim[:3]),
        "logo_uri": _b64_img(logo),
        "foto_uri": _foto_uri(prim),
        "qr_uri": _b64_img(pseudo_qr(cliente, 360)),
        "prim_css": _rgb(prim),
        "medio_css": _rgb(_ajustar(prim, 0.58)),
        "oscuro_css": _rgb(_ajustar(prim, 0.20)),
        "claro_css": _rgb(_ajustar(prim, 1.7)),
        "prim_legible": _rgb(marca_legible(prim)),
        "txt_sobre_prim": "#ffffff" if oscuro else "#1d1f24",
        "logo_oscuro": oscuro,
        "variante": variante_de(cliente),
        "cliente": cliente,
        "web": web_cliente(cliente),
        "datos": DATOS,
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
        ".lab{font-size:16px;letter-spacing:2.5px;text-transform:uppercase;font-weight:600}"
        ".val{font-size:27px;font-weight:600;margin-top:2px}"
        ".nm{font-family:'Playfair';font-weight:800;line-height:1.0}"
        ".clip{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
        ".item{display:flex;align-items:center;gap:15px}"
        % (pf, inter, inter_sb)
    )


def _root(ctx):
    return (":root{--prim:%s;--medio:%s;--oscuro:%s;--claro:%s;--oro:%s;}"
            % (ctx["prim_css"], ctx["medio_css"], ctx["oscuro_css"], ctx["claro_css"], ORO))


def _shell(ctx, clase, css_estilo, cuerpo, ancho, alto, fondo=None):
    style = (" style='background:%s'" % fondo) if fondo else ""
    return ("<!doctype html><html><head><meta charset='utf-8'><style>%s%s"
            ".card{width:%dpx;height:%dpx;position:relative;overflow:hidden}%s"
            "</style></head><body><div class='card %s'%s>%s</div></body></html>"
            % (css_base(), _root(ctx), ancho, alto, css_estilo, clase, style, cuerpo))


def _qr(cx, top, qr_uri, lado=240, bg="#fff"):
    left = int(cx - lado / 2)
    pad = 22
    return ("<div style='position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;"
            "background:%s;border-radius:18px;box-shadow:0 12px 30px -12px rgba(0,0,0,.5);"
            "display:flex;align-items:center;justify-content:center'>"
            "<img src='%s' style='width:%dpx;height:%dpx;border-radius:6px'></div>"
            % (left, top, lado, lado, bg, qr_uri, lado - pad * 2, lado - pad * 2))


# ⛔ REGLA FIJA — EL LOGO DEL CLIENTE NUNCA SE RECOLOREA (decisión Diego 2026-06-15).
# Se respeta SIEMPRE su tinta original; solo se permite ajustar tamaño/posición.
# Prohibido brightness(0)/invert/duotono/teñido y placas-caja detrás del logo. En
# fondos oscuros (Aurora/Glass) la legibilidad se da con un halo suave (drop-shadow)
# que NO toca el color del logo.
_LOGO_GLOW = ("filter:drop-shadow(0 1px 1px rgba(0,0,0,.35)) "
              "drop-shadow(0 0 9px rgba(255,255,255,.45))")


# ============================ AURORA (horizontal, oscuro premium) ============================

_CSS_AURORA = """
.aurora .logo{position:absolute;top:58px;left:60px;height:76px;max-width:330px;object-fit:contain;object-position:left}
.aurora .foto{position:absolute;top:110px;right:60px;width:298px;height:392px;border-radius:18px;object-fit:cover;object-position:center 28%;box-shadow:0 20px 44px -16px rgba(0,0,0,.7);border:2px solid var(--oro)}
.aurora .nm{position:absolute;top:168px;left:60px;font-size:62px;color:#fff;max-width:560px}
.aurora .hair{position:absolute;top:330px;left:62px;width:90px;height:3px;background:var(--oro)}
.aurora .cargo{position:absolute;top:360px;left:62px;font-size:27px;color:rgba(255,255,255,.78)}
.aurora .panel{position:absolute;left:60px;right:60px;bottom:52px;display:flex;align-items:center;padding:24px 30px;border:1px solid rgba(255,255,255,.18);border-radius:18px;background:rgba(255,255,255,.045)}
.aurora .cell{flex:1;display:flex;align-items:center;gap:16px}
.aurora .divisor{width:1px;align-self:stretch;background:rgba(255,255,255,.18);margin:2px 14px}
.aurora .lab{color:rgba(255,255,255,.55)}.aurora .val{color:#fff}
.aurora .rtit{position:absolute;top:150px;left:0;right:0;text-align:center;color:rgba(255,255,255,.55);font-size:19px;letter-spacing:4px;text-transform:uppercase;font-weight:600}
.aurora .rfoot{position:absolute;left:0;right:0;bottom:64px;text-align:center;color:#fff}
.aurora .rfoot .t1{font-size:26px;font-weight:600}.aurora .rfoot .t2{font-size:22px;color:rgba(255,255,255,.7);margin-top:8px}
"""


def _aurora(lado, ctx, d):
    if lado == "frontal":
        n1, n2 = _nombre2(d["nombre"])
        cuerpo = (
            "<img class='logo' src='%s' style='%s'>"
            "<div class='nm'>%s<br>%s</div><div class='hair'></div>"
            "<div class='cargo'>%s</div>"
            "<img class='foto' src='%s'>"
            "<div class='panel'>"
            "<div class='cell'>%s<div><div class='lab'>Empresa</div><div class='val clip' style='max-width:280px'>%s</div></div></div>"
            "<div class='divisor'></div>"
            "<div class='cell' style='flex:0 0 230px'>%s<div><div class='lab'>DNI</div><div class='val'>%s</div></div></div>"
            "</div>"
            % (ctx["logo_uri"], _LOGO_GLOW, n1, n2, d["cargo"], ctx["foto_uri"],
               _icono("edificio", ORO, 30), ctx["cliente"], _icono("persona", ORO, 30), d["id"]))
    else:
        cuerpo = (
            "<img class='logo' src='%s' style='%s;left:50%%;transform:translateX(-50%%);top:66px;height:62px'>"
            "<div class='rtit'>Escanea para validar</div>"
            "%s"
            "<div class='rfoot'><div class='t1'>Credencial personal e intransferible</div>"
            "<div class='t2'>%s &nbsp;·&nbsp; Vigencia 2026 — 2027</div></div>"
            % (ctx["logo_uri"], _LOGO_GLOW, _qr(H[0] / 2, 192, ctx["qr_uri"], 240), ctx["web"]))
    fimg = fondo_imagen("aurora", ctx)
    fondo = ('url("%s") center/cover' % fimg) if fimg else _BG_AURORA[ctx["variante"]]
    return _shell(ctx, "aurora", _CSS_AURORA, cuerpo, *H, fondo=fondo), H[0], H[1]


# ============================ EDITORIAL (horizontal claro, foto a sangre) ============================

_CSS_EDITORIAL = """
.editorial{background:#faf8f4}
.editorial .band{position:absolute;left:0;top:0;bottom:0;width:362px}
.editorial .foto{position:absolute;left:52px;top:50%;transform:translateY(-50%);width:282px;height:376px;border-radius:16px;object-fit:cover;object-position:center 30%;box-shadow:0 22px 46px -18px rgba(0,0,0,.5);border:3px solid rgba(255,255,255,.85)}
.editorial .logo{position:absolute;top:62px;right:60px;height:60px;max-width:280px;object-fit:contain;object-position:right}
.editorial .nm{position:absolute;top:172px;left:424px;font-size:52px;color:#1d1f24;line-height:1.05;max-width:430px}
.editorial .cargo{position:absolute;top:308px;left:426px;font-style:italic;font-size:27px;color:#6c6f78;font-family:'Playfair'}
.editorial .hair{position:absolute;top:360px;left:426px;width:88px;height:3px;background:var(--oro)}
.editorial .campos{position:absolute;left:424px;bottom:78px;display:flex;gap:48px}
.editorial .lab{color:#a6a8b0}.editorial .val{color:#1d1f24}
.editorial .icon-c{width:42px;height:42px;border-radius:50%;border:1.5px solid var(--prim);display:flex;align-items:center;justify-content:center}
.editorial .rband{position:absolute;left:0;top:0;bottom:0;width:362px}
.editorial .rlogo{position:absolute;top:64px;right:60px;height:58px;max-width:280px;object-fit:contain;object-position:right}
.editorial .rtit{position:absolute;top:150px;left:362px;right:0;text-align:center;color:#9a9ca4;font-size:18px;letter-spacing:3.5px;text-transform:uppercase;font-weight:600}
.editorial .rfoot{position:absolute;left:362px;right:0;bottom:74px;text-align:center;color:#1d1f24}
.editorial .rfoot .t1{font-size:25px;font-weight:600}.editorial .rfoot .t2{font-size:21px;color:#6c6f78;margin-top:8px}
"""


def _editorial(lado, ctx, d):
    banda = _BG_EDIT_BANDA[ctx["variante"]]
    if lado == "frontal":
        n1, n2 = _nombre2(d["nombre"])
        cuerpo = (
            "<div class='band' style='background:%s'></div>"
            "<img class='foto' src='%s'>"
            "<img class='logo' src='%s'>"
            "<div class='nm'>%s<br>%s</div>"
            "<div class='cargo'>%s</div><div class='hair'></div>"
            "<div class='campos'>"
            "<div class='item'><div class='icon-c'>%s</div><div><div class='lab'>Empresa</div><div class='val clip' style='max-width:220px'>%s</div></div></div>"
            "<div class='item'><div class='icon-c'>%s</div><div><div class='lab'>DNI</div><div class='val'>%s</div></div></div>"
            "</div>"
            % (banda, ctx["foto_uri"], ctx["logo_uri"], n1, n2, d["cargo"],
               _icono("edificio", ctx["prim_legible"], 22), ctx["cliente"],
               _icono("persona", ctx["prim_legible"], 22), d["id"]))
    else:
        cuerpo = (
            "<div class='rband' style='background:%s'></div>"
            "<img class='rlogo' src='%s'>"
            "<div class='rtit'>Escanea para validar</div>"
            "%s"
            "<div class='rfoot'><div class='t1'>Credencial personal e intransferible</div>"
            "<div class='t2'>%s &nbsp;·&nbsp; Vigencia 2026 — 2027</div></div>"
            % (banda, ctx["logo_uri"], _qr(362 + (H[0] - 362) / 2, 196, ctx["qr_uri"], 230), ctx["web"]))
    return _shell(ctx, "editorial", _CSS_EDITORIAL, cuerpo, *H), H[0], H[1]


# ============================ GLASS (vertical color, paneles de vidrio) ============================

_CSS_GLASS = """
.glass .logo{position:absolute;top:60px;left:50%;transform:translateX(-50%);height:66px;max-width:420px;object-fit:contain;filter:drop-shadow(0 1px 1px rgba(0,0,0,.35)) drop-shadow(0 0 9px rgba(255,255,255,.45))}
.glass .card2{position:absolute;left:50%;transform:translateX(-50%);top:176px;width:486px;padding:38px 0 32px;border-radius:26px;background:rgba(255,255,255,.15);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.28);display:flex;flex-direction:column;align-items:center;gap:22px;box-shadow:0 20px 50px -20px rgba(0,0,0,.4)}
.glass .foto{width:252px;height:252px;border-radius:50%;object-fit:cover;object-position:center 30%;border:5px solid rgba(255,255,255,.8);box-shadow:0 14px 32px -12px rgba(0,0,0,.5)}
.glass .nm{font-size:50px;color:#fff;text-align:center;line-height:1.02}
.glass .cargo{color:rgba(255,255,255,.92);font-size:25px;margin-top:-6px}
.glass .hair{width:96px;height:3px;background:rgba(255,255,255,.9);margin:2px auto 0}
.glass .panel{position:absolute;left:50%;transform:translateX(-50%);bottom:64px;width:486px;padding:24px 0;border-radius:20px;background:rgba(255,255,255,.13);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.24);display:flex;justify-content:center;align-items:center;color:#fff}
.glass .cell{flex:1;text-align:center}
.glass .divisor{width:1px;align-self:stretch;background:rgba(255,255,255,.26);margin:4px 0}
.glass .lab{color:rgba(255,255,255,.75)}.glass .val{color:#fff}
.glass .rpanel{position:absolute;left:50%;transform:translateX(-50%);bottom:96px;width:486px;padding:34px 30px;border-radius:22px;background:rgba(255,255,255,.13);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.24);text-align:center;color:#fff}
.glass .rpanel .esc{display:flex;justify-content:center;margin-bottom:14px}
.glass .rpanel .t1{font-size:24px;font-weight:600}
.glass .rpanel .web{display:flex;align-items:center;justify-content:center;gap:10px;font-size:22px;color:rgba(255,255,255,.9);margin-top:14px}
.glass .rpanel .t2{font-size:20px;color:rgba(255,255,255,.8);margin-top:6px}
.glass .rtit{position:absolute;top:300px;left:0;right:0;text-align:center;color:rgba(255,255,255,.7);font-size:18px;letter-spacing:3.5px;text-transform:uppercase;font-weight:600}
"""


def _glass(lado, ctx, d):
    if lado == "frontal":
        n1, n2 = _nombre2(d["nombre"])
        cuerpo = (
            "<img class='logo' src='%s'>"
            "<div class='card2'><img class='foto' src='%s'>"
            "<div class='nm'>%s<br>%s</div>"
            "<div class='cargo'>%s</div><div class='hair'></div></div>"
            "<div class='panel'>"
            "<div class='cell'><div class='lab'>Empresa</div><div class='val clip' style='max-width:200px;margin:0 auto'>%s</div></div>"
            "<div class='divisor'></div>"
            "<div class='cell'><div class='lab'>DNI</div><div class='val'>%s</div></div>"
            "</div>"
            % (ctx["logo_uri"], ctx["foto_uri"], n1, n2, d["cargo"], ctx["cliente"], d["id"]))
    else:
        cuerpo = (
            "<img class='logo' src='%s'>"
            "<div class='rtit'>Escanea para validar</div>"
            "%s"
            "<div class='rpanel'>"
            "<div class='esc'>%s</div>"
            "<div class='t1'>Credencial personal e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "<div class='t2'>Vigencia 2026 — 2027</div>"
            "</div>"
            % (ctx["logo_uri"], _qr(V[0] / 2, 360, ctx["qr_uri"], 230),
               _icono("escudo", ORO, 34), _icono("globo", "rgba(255,255,255,.9)", 22), ctx["web"]))
    fimg = fondo_imagen("glass", ctx)
    fondo = ('url("%s") center/cover' % fimg) if fimg else _BG_GLASS[ctx["variante"]]
    return _shell(ctx, "glass", _CSS_GLASS, cuerpo, *V, fondo=fondo), V[0], V[1]


# ---------- dispatcher ----------

_FNS = {"aurora": _aurora, "editorial": _editorial, "glass": _glass}


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto). estilo in {aurora,editorial,glass}; lado in {frontal,reverso}."""
    return _FNS[estilo](lado, ctx, ctx["datos"])
