# -*- coding: utf-8 -*-
"""HTML/CSS de cada cara de credencial (3 direcciones: Aurora/Editorial/Glass).
Autocontenido: logo y foto en base64, fuentes horneadas via @font-face. El color
y el tratamiento salen del logo real (varia segun la marca). Lo rasteriza render.py.

CSS de los frontales basado en el prototipo validado salida/_proto/proto_html.py."""
import base64
import hashlib
import io
import os

RUTA = os.path.dirname(os.path.abspath(__file__))
FOTO_PERSONA = os.path.join(RUTA, "foto-persona.jpg")
F_PLAYFAIR = os.path.join(RUTA, "fuentes", "playfair.ttf")
F_INTER = os.path.join(RUTA, "fuentes", "inter.ttf")
F_INTER_SB = os.path.join(RUTA, "fuentes", "inter-semibold.ttf")

DATOS = {"nombre": "Carlos González M.", "cargo": "Supervisor de Operaciones", "id": "45678123"}
ORO = "#c9a14a"
H, V = (1011, 638), (638, 1011)

# Variantes de fondo por dirección: mismo color de marca, distinta composición.
# La variante se elige por el NOMBRE del cliente (determinista) -> dos empresas del
# mismo color reciben fondos distintos. Sumarán las imágenes del banco (Fase 2b).
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


# ---------- utilidades ----------

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


def construir_contexto(logo, prim, sec, cliente):
    from motor import web_cliente, luminancia, marca_legible, pseudo_qr
    oscuro = luminancia(prim) < 0.45
    return {
        "logo_uri": _b64_img(logo),
        "foto_uri": _b64_file(FOTO_PERSONA, "image/jpeg"),
        "qr_uri": _b64_img(pseudo_qr(cliente, 360)),
        "prim_css": _rgb(prim),
        "medio_css": _rgb(_ajustar(prim, 0.58)),
        "oscuro_css": _rgb(_ajustar(prim, 0.20)),
        "claro_css": _rgb(_ajustar(prim, 1.6)),
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
        ".lab{font-size:18px;letter-spacing:3px;text-transform:uppercase;font-weight:600}"
        ".val{font-size:30px;font-weight:600;margin-top:2px}"
        ".nm{font-family:'Playfair';font-weight:800;line-height:1}"
        ".clip{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
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


def _qr(left, top, qr_uri, lado=190, bg="#fff"):
    """Placa blanca redondeada con el QR decorativo (PIL) del motor, embebido."""
    return ("<div style='position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;"
            "background:%s;border-radius:16px;box-shadow:0 10px 24px -10px rgba(0,0,0,.45);"
            "display:flex;align-items:center;justify-content:center'>"
            "<img src='%s' style='width:%dpx;height:%dpx;border-radius:6px'></div>"
            % (left, top, lado, lado, bg, qr_uri, lado - 28, lado - 28))


def _logo_oscuro_filter(ctx):
    return "filter:brightness(0) invert(1)" if True else ""


# ---------- AURORA (horizontal, oscuro premium, glassmorphism) ----------

_CSS_AURORA = """
.aurora{background:
   radial-gradient(120% 140% at 12% 8%, var(--medio) 0%, transparent 42%),
   radial-gradient(120% 130% at 95% 95%, var(--prim) 0%, transparent 38%),
   linear-gradient(135deg, var(--oscuro), #0c0e11 75%)}
.aurora .noise{position:absolute;inset:0;opacity:.05;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>")}
.aurora .logo{position:absolute;top:50px;left:60px;height:64px;max-width:360px;object-fit:contain;object-position:left}
.aurora .foto{position:absolute;top:128px;right:60px;width:230px;height:288px;border-radius:18px;object-fit:cover;box-shadow:0 16px 34px -10px rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.18)}
.aurora .nm{position:absolute;top:150px;left:60px;font-size:60px;color:#fff;max-width:470px;line-height:1.04}
.aurora .hair{position:absolute;top:292px;left:62px;width:120px;height:2px;background:var(--oro)}
.aurora .glass{position:absolute;left:52px;bottom:46px;right:320px;padding:26px 30px;border-radius:18px;background:rgba(255,255,255,.08);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.16)}
.aurora .row{display:flex;gap:46px}
.aurora .lab{color:rgba(255,255,255,.55)}.aurora .val{color:#fff}
.aurora .rev-mid{position:absolute;left:0;right:0;bottom:84px;text-align:center;color:#fff}
.aurora .rev-mid .t1{font-size:26px;font-weight:600}.aurora .rev-mid .t2{font-size:22px;color:rgba(255,255,255,.75);margin-top:8px}
"""


def _aurora(lado, ctx, d):
    lf = _logo_oscuro_filter(ctx)
    if lado == "frontal":
        cuerpo = (
            "<div class='noise'></div>"
            "<img class='logo' src='%s' style='%s'>"
            "<div class='nm'>%s</div><div class='hair'></div>"
            "<img class='foto' src='%s'>"
            "<div class='glass'><div class='row'>"
            "<div><div class='lab'>Cargo</div><div class='val'>%s</div></div>"
            "<div><div class='lab'>DNI</div><div class='val'>%s</div></div>"
            "</div></div>"
            % (ctx["logo_uri"], lf, d["nombre"], ctx["foto_uri"], d["cargo"], d["id"]))
    else:
        cuerpo = (
            "<div class='noise'></div>"
            "<img class='logo' src='%s' style='%s;left:50%%;transform:translateX(-50%%);top:64px'>"
            "%s"
            "<div class='rev-mid'><div class='t1'>Credencial personal e intransferible</div>"
            "<div class='t2'>%s &nbsp;·&nbsp; Vigencia 2026 — 2027</div></div>"
            % (ctx["logo_uri"], lf, _qr((H[0] - 190) // 2, 150, ctx["qr_uri"]), ctx["web"]))
    fondo = _BG_AURORA[ctx["variante"]]
    return _shell(ctx, "aurora", _CSS_AURORA, cuerpo, *H, fondo=fondo), H[0], H[1]


# ---------- EDITORIAL (horizontal, claro/marfil) ----------

_CSS_EDITORIAL = """
.editorial{background:#faf8f4}
.editorial .band{position:absolute;left:0;top:0;bottom:0;width:250px;background:linear-gradient(160deg,var(--prim),var(--medio))}
.editorial .foto{position:absolute;left:54px;top:84px;width:218px;height:272px;border-radius:14px;object-fit:cover;box-shadow:0 18px 34px -12px rgba(0,0,0,.45)}
.editorial .logo{position:absolute;top:58px;right:62px;height:58px;max-width:330px;object-fit:contain;object-position:right}
.editorial .nm{position:absolute;top:150px;left:330px;font-size:58px;color:#1d1f24;font-weight:700;max-width:600px}
.editorial .cargo{position:absolute;top:240px;left:332px;font-style:italic;font-size:28px;color:#6c6f78;font-family:'Playfair'}
.editorial .hair{position:absolute;top:300px;left:332px;width:120px;height:2px;background:var(--oro)}
.editorial .data{position:absolute;left:332px;bottom:60px;display:flex;gap:54px}
.editorial .lab{color:#a6a8b0}.editorial .val{color:#1d1f24}
.editorial .rev-logo{position:absolute;top:70px;left:50%;transform:translateX(-50%);height:60px;max-width:360px;object-fit:contain}
.editorial .rev-mid{position:absolute;left:0;right:0;bottom:90px;text-align:center;color:#1d1f24}
.editorial .rev-mid .t1{font-size:26px;font-weight:600}.editorial .rev-mid .t2{font-size:22px;color:#6c6f78;margin-top:8px}
"""


def _editorial(lado, ctx, d):
    banda = _BG_EDIT_BANDA[ctx["variante"]]
    if lado == "frontal":
        cuerpo = (
            "<div class='band' style='background:%s'></div><img class='foto' src='%s'>"
            "<img class='logo' src='%s'>"
            "<div class='nm clip'>%s</div>"
            "<div class='cargo'>%s</div><div class='hair'></div>"
            "<div class='data'>"
            "<div><div class='lab'>Empresa</div><div class='val clip' style='max-width:360px'>%s</div></div>"
            "<div><div class='lab'>DNI</div><div class='val'>%s</div></div>"
            "</div>"
            % (banda, ctx["foto_uri"], ctx["logo_uri"], d["nombre"], d["cargo"], ctx["cliente"], d["id"]))
    else:
        cuerpo = (
            "<div class='band' style='background:%s'></div>"
            "<img class='rev-logo' src='%s'>"
            "%s"
            "<div class='rev-mid'><div class='t1'>Credencial personal e intransferible</div>"
            "<div class='t2'>%s &nbsp;·&nbsp; Vigencia 2026 — 2027</div></div>"
            % (banda, ctx["logo_uri"], _qr((H[0] - 190) // 2 + 50, 150, ctx["qr_uri"]), ctx["web"]))
    return _shell(ctx, "editorial", _CSS_EDITORIAL, cuerpo, *H), H[0], H[1]


# ---------- GLASS (vertical, color pleno + glassmorphism) ----------

_CSS_GLASS = """
.glass{background:
   radial-gradient(90% 120% at 85% 8%, rgba(255,255,255,.26), transparent 45%),
   radial-gradient(120% 120% at 8% 96%, var(--oscuro), transparent 55%),
   linear-gradient(150deg, var(--prim), var(--medio))}
.glass .blob{position:absolute;width:360px;height:360px;border-radius:50%;filter:blur(55px);opacity:.45}
.glass .b1{background:#fff;top:-130px;right:-70px}.glass .b2{background:var(--oscuro);bottom:-150px;left:-60px}
.glass .logo{position:absolute;top:60px;left:50%;transform:translateX(-50%);height:66px;max-width:420px;object-fit:contain;filter:brightness(0) invert(1)}
.glass .card2{position:absolute;left:50%;transform:translateX(-50%);top:190px;width:430px;padding:34px 0 30px;border-radius:24px;background:rgba(255,255,255,.14);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.25);display:flex;flex-direction:column;align-items:center;gap:22px}
.glass .foto{width:230px;height:230px;border-radius:50%;object-fit:cover;border:5px solid rgba(255,255,255,.7);box-shadow:0 14px 30px -10px rgba(0,0,0,.45)}
.glass .nm{font-size:50px;color:#fff;text-align:center}
.glass .cargo{color:rgba(255,255,255,.85);font-size:26px;margin-top:-6px}
.glass .hair{width:120px;height:2px;background:rgba(255,255,255,.85);margin:6px auto 0}
.glass .data{position:absolute;left:0;right:0;bottom:70px;display:flex;justify-content:center;gap:60px;color:#fff;text-align:center}
.glass .lab{color:rgba(255,255,255,.7)}.glass .val{color:#fff}
.glass .rev-mid{position:absolute;left:0;right:0;bottom:120px;text-align:center;color:#fff}
.glass .rev-mid .t1{font-size:26px;font-weight:600}.glass .rev-mid .t2{font-size:22px;color:rgba(255,255,255,.8);margin-top:8px}
"""


def _glass(lado, ctx, d):
    if lado == "frontal":
        cuerpo = (
            "<div class='blob b1'></div><div class='blob b2'></div>"
            "<img class='logo' src='%s'>"
            "<div class='card2'><img class='foto' src='%s'>"
            "<div class='nm' style='max-width:400px'>%s</div>"
            "<div class='cargo'>%s</div><div class='hair'></div></div>"
            "<div class='data'>"
            "<div><div class='lab'>Empresa</div><div class='val clip' style='max-width:230px'>%s</div></div>"
            "<div><div class='lab'>DNI</div><div class='val'>%s</div></div>"
            "</div>"
            % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"], ctx["cliente"], d["id"]))
    else:
        cuerpo = (
            "<div class='blob b1'></div><div class='blob b2'></div>"
            "<img class='logo' src='%s'>"
            "%s"
            "<div class='rev-mid'><div class='t1'>Credencial personal e intransferible</div>"
            "<div class='t2'>%s</div><div class='t2'>Vigencia 2026 — 2027</div></div>"
            % (ctx["logo_uri"], _qr((V[0] - 190) // 2, 300, ctx["qr_uri"]), ctx["web"]))
    fondo = _BG_GLASS[ctx["variante"]]
    return _shell(ctx, "glass", _CSS_GLASS, cuerpo, *V, fondo=fondo), V[0], V[1]


# ---------- dispatcher ----------

_FNS = {"aurora": _aurora, "editorial": _editorial, "glass": _glass}


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto). estilo in {aurora,editorial,glass}; lado in {frontal,reverso}."""
    return _FNS[estilo](lado, ctx, ctx["datos"])
