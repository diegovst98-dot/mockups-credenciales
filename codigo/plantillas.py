# -*- coding: utf-8 -*-
"""HTML/CSS de cada cara de credencial (3 direcciones: Aurora/Editorial/Glass).
Autocontenido: logo y foto en base64, fuentes horneadas via @font-face. El color
y el tratamiento salen del logo real (varia segun la marca). Lo rasteriza render.py.

v9: grilla consistente (margen de seguridad), foto frontal mas grande e integrada,
nombre en dos lineas intencionales, QR grande y centrado, reversos rebalanceados."""
import base64
import glob as _glob
import hashlib
import io
import os

from PIL import Image

RUTA = os.path.dirname(os.path.abspath(__file__))
FOTO_PERSONA = os.path.join(RUTA, "foto-persona.jpg")
# Assets en nombres PLANOS (sin subcarpeta) para que el auto-update del launcher
# los reparta sin recompilar el exe. Fondos: fondo-<estilo>-N.jpg
F_PLAYFAIR = os.path.join(RUTA, "fuente-display.ttf")   # ya es Playfair Display (OFL)
F_INTER = os.path.join(RUTA, "inter.ttf")
F_INTER_SB = os.path.join(RUTA, "inter-semibold.ttf")

DATOS = {"nombre": "Carlos González M.", "cargo": "Supervisor de Operaciones", "id": "45678123"}
ORO = "#c9a14a"
H, V = (1011, 638), (638, 1011)
MG = 60  # margen de seguridad de impresion (zona segura, ~5mm)

# Variantes de fondo por dirección: mismo color de marca, distinta composición.
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
    """Índice de variante determinista por nombre de cliente (0..n-1)."""
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
    """Parte el nombre en (primera palabra, resto) para dos líneas equilibradas,
    evitando la inicial huérfana. 'Carlos González M.' -> ('Carlos','González M.')."""
    p = nombre.split()
    if len(p) <= 1:
        return nombre, ""
    return p[0], " ".join(p[1:])


# ---------- banco de fondos (Fase 2b): imágenes neutras recoloreadas a la marca ----------

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


# ---------- contexto ----------

def construir_contexto(logo, prim, sec, cliente):
    from motor import web_cliente, luminancia, marca_legible, pseudo_qr
    oscuro = luminancia(prim) < 0.45
    return {
        "_prim": tuple(int(x) for x in prim[:3]),
        "logo_uri": _b64_img(logo),
        "foto_uri": _b64_file(FOTO_PERSONA, "image/jpeg"),
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
        ".lab{font-size:17px;letter-spacing:2.5px;text-transform:uppercase;font-weight:600}"
        ".val{font-size:28px;font-weight:600;margin-top:3px}"
        ".nm{font-family:'Playfair';font-weight:800;line-height:1.0}"
        ".clip{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
        % (pf, inter, inter_sb)
    )


def _root(ctx):
    return (":root{--prim:%s;--medio:%s;--oscuro:%s;--claro:%s;--oro:%s;--acc:%s;}"
            % (ctx["prim_css"], ctx["medio_css"], ctx["oscuro_css"], ctx["claro_css"],
               ORO, ctx["claro_css"]))


def _shell(ctx, clase, css_estilo, cuerpo, ancho, alto, fondo=None):
    style = (" style='background:%s'" % fondo) if fondo else ""
    return ("<!doctype html><html><head><meta charset='utf-8'><style>%s%s"
            ".card{width:%dpx;height:%dpx;position:relative;overflow:hidden}%s"
            "</style></head><body><div class='card %s'%s>%s</div></body></html>"
            % (css_base(), _root(ctx), ancho, alto, css_estilo, clase, style, cuerpo))


def _qr(cx, top, qr_uri, lado=240, bg="#fff"):
    """Placa blanca redondeada con el QR, CENTRADA en cx (centro horizontal)."""
    left = int(cx - lado / 2)
    pad = 22
    return ("<div style='position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;"
            "background:%s;border-radius:18px;box-shadow:0 12px 30px -12px rgba(0,0,0,.5);"
            "display:flex;align-items:center;justify-content:center'>"
            "<img src='%s' style='width:%dpx;height:%dpx;border-radius:6px'></div>"
            % (left, top, lado, lado, bg, qr_uri, lado - pad * 2, lado - pad * 2))


_LOGO_BLANCO = "filter:brightness(0) invert(1)"


# ============================ AURORA (horizontal, oscuro premium) ============================

_CSS_AURORA = """
.aurora .logo{position:absolute;top:60px;left:60px;height:74px;max-width:330px;object-fit:contain;object-position:left}
.aurora .foto{position:absolute;top:115px;right:60px;width:300px;height:408px;border-radius:18px;object-fit:cover;object-position:center 28%;box-shadow:0 20px 44px -16px rgba(0,0,0,.7);border:1px solid rgba(255,255,255,.14)}
.aurora .nm{position:absolute;top:176px;left:60px;font-size:60px;color:#fff;max-width:560px}
.aurora .hair{position:absolute;top:322px;left:62px;width:88px;height:3px;background:var(--oro)}
.aurora .campos{position:absolute;left:60px;top:372px;right:400px}
.aurora .campo{margin-bottom:30px}
.aurora .row{display:flex;gap:60px}
.aurora .lab{color:rgba(255,255,255,.52)}.aurora .val{color:#fff}
.aurora .rtit{position:absolute;top:154px;left:0;right:0;text-align:center;color:rgba(255,255,255,.55);font-size:19px;letter-spacing:4px;text-transform:uppercase;font-weight:600}
.aurora .rfoot{position:absolute;left:0;right:0;bottom:66px;text-align:center;color:#fff}
.aurora .rfoot .t1{font-size:26px;font-weight:600}.aurora .rfoot .t2{font-size:22px;color:rgba(255,255,255,.7);margin-top:8px}
"""


def _aurora(lado, ctx, d):
    if lado == "frontal":
        n1, n2 = _nombre2(d["nombre"])
        cuerpo = (
            "<img class='logo' src='%s' style='%s'>"
            "<div class='nm'>%s<br>%s</div><div class='hair'></div>"
            "<img class='foto' src='%s'>"
            "<div class='campos'>"
            "<div class='campo'><div class='lab'>Cargo</div><div class='val'>%s</div></div>"
            "<div class='row'>"
            "<div><div class='lab'>Empresa</div><div class='val clip' style='max-width:230px'>%s</div></div>"
            "<div><div class='lab'>DNI</div><div class='val'>%s</div></div>"
            "</div></div>"
            % (ctx["logo_uri"], _LOGO_BLANCO, n1, n2, ctx["foto_uri"], d["cargo"], ctx["cliente"], d["id"]))
    else:
        cuerpo = (
            "<img class='logo' src='%s' style='%s;left:50%%;transform:translateX(-50%%);top:70px;height:64px'>"
            "<div class='rtit'>Escanea para validar</div>"
            "%s"
            "<div class='rfoot'><div class='t1'>Credencial personal e intransferible</div>"
            "<div class='t2'>%s &nbsp;·&nbsp; Vigencia 2026 — 2027</div></div>"
            % (ctx["logo_uri"], _LOGO_BLANCO, _qr(H[0] / 2, 196, ctx["qr_uri"], 244), ctx["web"]))
    fimg = fondo_imagen("aurora", ctx)
    fondo = ('url("%s") center/cover' % fimg) if fimg else _BG_AURORA[ctx["variante"]]
    return _shell(ctx, "aurora", _CSS_AURORA, cuerpo, *H, fondo=fondo), H[0], H[1]


# ============================ EDITORIAL (horizontal, claro/marfil) ============================

_CSS_EDITORIAL = """
.editorial{background:#faf8f4}
.editorial .band{position:absolute;left:0;top:0;bottom:0;width:362px}
.editorial .foto{position:absolute;left:52px;top:50%;transform:translateY(-50%);width:280px;height:380px;border-radius:16px;object-fit:cover;object-position:center 28%;box-shadow:0 20px 44px -16px rgba(0,0,0,.5)}
.editorial .logo{position:absolute;top:62px;right:60px;height:60px;max-width:300px;object-fit:contain;object-position:right}
.editorial .nm{position:absolute;top:150px;left:420px;font-size:56px;color:#1d1f24;max-width:540px}
.editorial .cargo{position:absolute;top:268px;left:422px;font-style:italic;font-size:29px;color:#6c6f78;font-family:'Playfair'}
.editorial .hair{position:absolute;top:330px;left:422px;width:88px;height:3px;background:var(--oro)}
.editorial .campos{position:absolute;left:422px;bottom:84px;display:flex;gap:64px}
.editorial .lab{color:#a6a8b0}.editorial .val{color:#1d1f24}
.editorial .rlogo{position:absolute;top:64px;right:60px;height:58px;max-width:300px;object-fit:contain;object-position:right}
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
            "<div class='nm'>%s %s</div>"
            "<div class='cargo'>%s</div><div class='hair'></div>"
            "<div class='campos'>"
            "<div><div class='lab'>Empresa</div><div class='val clip' style='max-width:330px'>%s</div></div>"
            "<div><div class='lab'>DNI</div><div class='val'>%s</div></div>"
            "</div>"
            % (banda, ctx["foto_uri"], ctx["logo_uri"], n1, n2, d["cargo"], ctx["cliente"], d["id"]))
    else:
        cuerpo = (
            "<div class='band' style='background:%s'></div>"
            "<img class='rlogo' src='%s'>"
            "<div class='rtit'>Escanea para validar</div>"
            "%s"
            "<div class='rfoot'><div class='t1'>Credencial personal e intransferible</div>"
            "<div class='t2'>%s &nbsp;·&nbsp; Vigencia 2026 — 2027</div></div>"
            % (banda, ctx["logo_uri"], _qr(362 + (H[0] - 362) / 2, 198, ctx["qr_uri"], 238), ctx["web"]))
    return _shell(ctx, "editorial", _CSS_EDITORIAL, cuerpo, *H), H[0], H[1]


# ============================ GLASS (vertical, color pleno + glassmorphism) ============================

_CSS_GLASS = """
.glass .logo{position:absolute;top:62px;left:50%;transform:translateX(-50%);height:66px;max-width:420px;object-fit:contain;filter:brightness(0) invert(1)}
.glass .card2{position:absolute;left:50%;transform:translateX(-50%);top:182px;width:474px;padding:40px 0 34px;border-radius:26px;background:rgba(255,255,255,.15);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.28);display:flex;flex-direction:column;align-items:center;gap:24px;box-shadow:0 20px 50px -20px rgba(0,0,0,.4)}
.glass .foto{width:250px;height:250px;border-radius:50%;object-fit:cover;object-position:center 30%;border:5px solid rgba(255,255,255,.75);box-shadow:0 14px 32px -12px rgba(0,0,0,.5)}
.glass .nm{font-size:50px;color:#fff;text-align:center;line-height:1.02}
.glass .cargo{color:rgba(255,255,255,.9);font-size:25px;margin-top:-8px}
.glass .hair{width:96px;height:3px;background:rgba(255,255,255,.9);margin:4px auto 0}
.glass .campos{position:absolute;left:0;right:0;bottom:88px;display:flex;justify-content:center;gap:70px;color:#fff;text-align:center}
.glass .lab{color:rgba(255,255,255,.72)}.glass .val{color:#fff}
.glass .rtit{position:absolute;top:300px;left:0;right:0;text-align:center;color:rgba(255,255,255,.7);font-size:18px;letter-spacing:3.5px;text-transform:uppercase;font-weight:600}
.glass .rfoot{position:absolute;left:0;right:0;bottom:130px;text-align:center;color:#fff}
.glass .rfoot .t1{font-size:25px;font-weight:600}.glass .rfoot .t2{font-size:21px;color:rgba(255,255,255,.82);margin-top:8px}
"""


def _glass(lado, ctx, d):
    if lado == "frontal":
        n1, n2 = _nombre2(d["nombre"])
        cuerpo = (
            "<img class='logo' src='%s'>"
            "<div class='card2'><img class='foto' src='%s'>"
            "<div class='nm'>%s<br>%s</div>"
            "<div class='cargo'>%s</div><div class='hair'></div></div>"
            "<div class='campos'>"
            "<div><div class='lab'>Empresa</div><div class='val clip' style='max-width:240px'>%s</div></div>"
            "<div><div class='lab'>DNI</div><div class='val'>%s</div></div>"
            "</div>"
            % (ctx["logo_uri"], ctx["foto_uri"], n1, n2, d["cargo"], ctx["cliente"], d["id"]))
    else:
        cuerpo = (
            "<img class='logo' src='%s'>"
            "<div class='rtit'>Escanea para validar</div>"
            "%s"
            "<div class='rfoot'><div class='t1'>Personal e intransferible</div>"
            "<div class='t2'>%s</div><div class='t2'>Vigencia 2026 — 2027</div></div>"
            % (ctx["logo_uri"], _qr(V[0] / 2, 388, ctx["qr_uri"], 240), ctx["web"]))
    fimg = fondo_imagen("glass", ctx)
    fondo = ('url("%s") center/cover' % fimg) if fimg else _BG_GLASS[ctx["variante"]]
    return _shell(ctx, "glass", _CSS_GLASS, cuerpo, *V, fondo=fondo), V[0], V[1]


# ---------- dispatcher ----------

_FNS = {"aurora": _aurora, "editorial": _editorial, "glass": _glass}


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto). estilo in {aurora,editorial,glass}; lado in {frontal,reverso}."""
    return _FNS[estilo](lado, ctx, ctx["datos"])
