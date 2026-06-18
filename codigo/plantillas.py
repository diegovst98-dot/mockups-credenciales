# -*- coding: utf-8 -*-
"""HTML/CSS de cada cara de credencial (3 direcciones: Clásica/Gafete/Premium).
Autocontenido: logo y foto en base64, fuentes horneadas via @font-face.

Diseños reproducidos de las referencias profesionales aprobadas por Diego (2026-06-15):
P1 horizontal limpia, P4 vertical gafete moderno, P3 vertical premium. El LAYOUT es fijo;
el COLOR DE ACENTO sale del logo del cliente (--acc = marca legible, --oscuro = banda con
texto blanco), así la misma plantilla se ve on-brand para cualquier logo. El logo del
cliente va en su tinta real, NUNCA se recolorea. Lo rasteriza render.py (Edge/Playwright)."""
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

def construir_contexto(logo, prim, sec, cliente):
    from motor import web_cliente, luminancia, marca_legible, pseudo_qr, distancia, saturacion
    oscuro = luminancia(prim) < 0.45
    # color secundario de la marca como ACENTO que "puntua" (5-10%): solo si es
    # realmente distinto y con color; si no, cae al oro. Regla: un color manda, otro puntua.
    sec_distinta = distancia(prim, sec) > 70 and saturacion(sec) > 0.18
    acc2 = marca_legible(sec) if sec_distinta else None
    return {
        "_prim": tuple(int(x) for x in prim[:3]),
        "logo_uri": _b64_img(logo),
        "foto_uri": _foto_uri(prim),
        "qr_uri": _b64_img(pseudo_qr(cliente, 360)),
        "prim_css": _rgb(prim),
        "medio_css": _rgb(_ajustar(prim, 0.58)),
        "oscuro_css": _rgb(_ajustar(prim, 0.22)),
        "claro_css": _rgb(_ajustar(prim, 1.7)),
        "prim_legible": _rgb(marca_legible(prim)),
        "acc2_css": _rgb(acc2) if acc2 else ORO,
        "txt_sobre_prim": "#ffffff" if oscuro else "#1d1f24",
        "logo_oscuro": oscuro,
        "variante": variante_de(cliente),
        "cliente": cliente,
        "monograma": ("".join(w[0] for w in (cliente or "").split()[:2]).upper() or "•"),
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
        % (pf, inter, inter_sb)
    )


def _root(ctx):
    return (":root{--prim:%s;--medio:%s;--oscuro:%s;--claro:%s;--oro:%s;--acc:%s;--acc2:%s;}"
            % (ctx["prim_css"], ctx["medio_css"], ctx["oscuro_css"],
               ctx["claro_css"], ORO, ctx["prim_legible"], ctx["acc2_css"]))


def _shell(ctx, clase, css_estilo, cuerpo, ancho, alto):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>%s%s"
            ".card{width:%dpx;height:%dpx;position:relative;overflow:hidden}%s"
            "</style></head><body><div class='card %s'>%s</div></body></html>"
            % (css_base(), _root(ctx), ancho, alto, css_estilo, clase, cuerpo))


# ⛔ REGLA FIJA — EL LOGO DEL CLIENTE NUNCA SE RECOLOREA (decisión Diego 2026-06-15).
# Se respeta SIEMPRE su tinta original; solo se ajusta tamaño/posición. Prohibido
# brightness(0)/invert/duotono/teñido. Todos los fondos son claros (blanco/crema), así
# el logo en color real siempre se lee. El color de marca tiñe el DISEÑO, no el logo.


# ============================ DIRECCIÓN 1 — CLÁSICA (horizontal limpia) ============================

_CSS_CLASICA = """
.clas{background:#fff}
.clas .safe{position:absolute;inset:50px;display:grid;grid-template-columns:286px 1fr;grid-template-rows:118px 1fr;column-gap:48px;row-gap:16px;z-index:1}
.clas .wm{position:absolute;right:-18px;bottom:-58px;font-family:'Playfair';font-weight:900;font-size:300px;line-height:.8;color:var(--acc);opacity:.045;z-index:0;pointer-events:none}
.clas .logohdr{grid-column:1/3;display:flex;align-items:center;justify-content:center}
.clas .logohdr img{height:104px;max-width:780px;object-fit:contain}
.clas .foto{grid-column:1;grid-row:2;align-self:center;width:286px;aspect-ratio:4/5;border:3px solid var(--acc);border-radius:10px;object-fit:cover;object-position:center 22%}
.clas .info{grid-column:2;grid-row:2;align-self:center}
.clas .name{font-family:'Inter';font-weight:800;font-size:58px;line-height:1.0;color:var(--acc);letter-spacing:-.01em;margin-bottom:24px;max-width:560px;position:relative}
.clas .name::after{content:'';position:absolute;left:2px;bottom:-11px;width:74px;height:4px;background:var(--acc2);border-radius:2px}
.clas .role{font-size:30px;font-weight:700;color:var(--acc);margin-bottom:30px;letter-spacing:.01em}
.clas .rows{display:grid;gap:16px;font-size:26px}
.clas .row{display:flex;align-items:center;gap:16px;border-top:2px solid #e4e6e2;padding-top:14px}
.clas .row .lb{color:var(--acc);font-weight:700}
.clas .ic{width:46px;height:46px;border-radius:50%;background:var(--oscuro);display:flex;align-items:center;justify-content:center;flex:0 0 auto}
.clas .bsafe{position:absolute;inset:50px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px}
.clas .oline{width:520px;height:2px;background:linear-gradient(90deg,transparent,var(--acc),transparent);opacity:.9}
.clas .scan{font-size:29px;color:var(--acc);font-weight:800;letter-spacing:3px;text-transform:uppercase}
.clas .qrbox{width:232px;height:232px;background:#fff;border:10px solid #fff;outline:3px solid var(--acc);border-radius:6px;display:flex;align-items:center;justify-content:center}
.clas .qrbox img{width:100%;height:100%;object-fit:contain}
.clas .ptxt{font-size:25px;color:#333;display:flex;align-items:center;justify-content:center;gap:9px}
.clas .web,.clas .vig{font-size:28px;font-weight:800;color:var(--acc);display:flex;align-items:center;justify-content:center;gap:9px}
"""


def _clasica(lado, ctx, d):
    if lado == "frontal":
        cuerpo = (
            "<div class='wm'>%s</div>"
            "<div class='safe'>"
            "<div class='logohdr'><img src='%s'></div>"
            "<img class='foto' src='%s'>"
            "<div class='info'>"
            "<div class='name'>%s</div>"
            "<div class='role'>%s</div>"
            "<div class='rows'>"
            "<div class='row'><span class='ic'>%s</span><span><span class='lb'>Empresa:</span> %s</span></div>"
            "<div class='row'><span class='ic'>%s</span><span><span class='lb'>DNI:</span> %s</span></div>"
            "</div></div></div>"
            % (ctx["monograma"], ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"],
               _icono("edificio", "#fff", 24), ctx["cliente"], _icono("persona", "#fff", 24), d["id"]))
    else:
        cuerpo = (
            "<div class='bsafe'>"
            "<div class='oline'></div>"
            "<div class='scan'>Escanea para validar</div>"
            "<div class='qrbox'><img src='%s'></div>"
            "<div class='oline'></div>"
            "<div class='ptxt'>%s Credencial personal e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "<div class='vig'>%s Vigencia 2026 — 2027</div>"
            "</div>"
            % (ctx["qr_uri"], _icono("escudo", ctx["prim_legible"], 20),
               _icono("globo", ctx["prim_legible"], 20), ctx["web"],
               _icono("calendario", ctx["prim_legible"], 19)))
    return _shell(ctx, "clas", _CSS_CLASICA, cuerpo, *H), H[0], H[1]


# ============================ DIRECCIÓN 2 — GAFETE (vertical moderno) ============================

_CSS_GAFETE = """
.gaf{background:#fff}
.gaf .wave{position:absolute;left:-40px;right:-40px;bottom:-34px;height:150px;background:var(--oscuro);border-radius:55% 55% 0 0}
.gaf .slot{position:absolute;top:20px;left:50%;transform:translateX(-50%);width:104px;height:15px;border:3px solid var(--acc);border-radius:9px;opacity:.4}
.gaf .safe{position:absolute;inset:46px;display:flex;flex-direction:column;align-items:center;text-align:center}
.gaf .logohdr{height:94px;display:flex;align-items:center}
.gaf .logohdr img{max-height:94px;max-width:440px;object-fit:contain}
.gaf .foto{margin-top:26px;width:300px;aspect-ratio:4/5;border:3px solid #fff;border-radius:10px;object-fit:cover;object-position:center 22%;box-shadow:0 12px 30px -12px rgba(0,0,0,.35),0 0 0 1px #e3e3df}
.gaf .nameband{margin:28px -46px 18px;width:calc(100% + 92px);background:var(--oscuro);color:#fff;font-family:'Inter';font-weight:800;font-size:44px;line-height:1.1;padding:20px 14px;letter-spacing:-.01em;border-top:4px solid var(--acc2)}
.gaf .role{font-size:27px;color:var(--acc);font-weight:800;border-bottom:4px solid var(--acc2);padding-bottom:9px;margin-bottom:30px;letter-spacing:.05em;text-transform:uppercase}
.gaf .data{width:436px;display:grid;gap:16px;text-align:left}
.gaf .row{display:grid;grid-template-columns:58px 1fr;gap:16px;align-items:center;border-bottom:2px solid #d8e0d6;padding-bottom:13px}
.gaf .ic{width:50px;height:50px;border-radius:50%;background:#fff;border:3px solid var(--acc);display:flex;align-items:center;justify-content:center}
.gaf .lb{color:var(--acc);font-weight:700;font-size:19px;text-transform:uppercase;letter-spacing:.09em}
.gaf .vl{font-size:27px;color:#1a1a1a;font-weight:700}
.gaf .bsafe{position:absolute;inset:46px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:18px}
.gaf .qrbox{width:280px;height:280px;background:#fff;border:10px solid #fff;outline:3px solid var(--acc);border-radius:8px;display:flex;align-items:center;justify-content:center;margin-top:6px}
.gaf .qrbox img{width:100%;height:100%;object-fit:contain}
.gaf .pill{display:flex;align-items:center;gap:12px;border:3px solid var(--acc);border-radius:999px;padding:10px 24px;color:var(--acc);font-size:22px;font-weight:800;letter-spacing:.05em;text-transform:uppercase}
.gaf .transfer{font-size:23px;color:var(--acc);font-weight:700;display:flex;align-items:center;justify-content:center;gap:9px}
.gaf .web{font-size:27px;font-weight:800;color:var(--acc);display:flex;align-items:center;justify-content:center;gap:9px}
.gaf .vig{position:absolute;left:0;right:0;bottom:30px;color:#fff;font-size:25px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:9px}
"""


def _gafete(lado, ctx, d):
    if lado == "frontal":
        cuerpo = (
            "<div class='wave'></div><div class='slot'></div>"
            "<div class='safe'>"
            "<div class='logohdr'><img src='%s'></div>"
            "<img class='foto' src='%s'>"
            "<div class='nameband'>%s</div>"
            "<div class='role'>%s</div>"
            "<div class='data'>"
            "<div class='row'><span class='ic'>%s</span><span><div class='lb'>Empresa</div><div class='vl'>%s</div></span></div>"
            "<div class='row'><span class='ic'>%s</span><span><div class='lb'>DNI</div><div class='vl'>%s</div></span></div>"
            "</div></div>"
            % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"],
               _icono("edificio", ctx["prim_legible"], 24), ctx["cliente"],
               _icono("persona", ctx["prim_legible"], 24), d["id"]))
    else:
        cuerpo = (
            "<div class='wave'></div><div class='slot'></div>"
            "<div class='bsafe'>"
            "<div class='logohdr'><img src='%s'></div>"
            "<div class='qrbox'><img src='%s'></div>"
            "<div class='pill'>%s Escanea para validar</div>"
            "<div class='transfer'>%s Credencial personal e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "</div>"
            "<div class='vig'>%s Vigencia 2026 — 2027</div>"
            % (ctx["logo_uri"], ctx["qr_uri"], _icono("globo", ctx["prim_legible"], 20),
               _icono("escudo", ctx["prim_legible"], 20), _icono("globo", ctx["prim_legible"], 20),
               ctx["web"], _icono("calendario", "#fff", 18)))
    return _shell(ctx, "gaf", _CSS_GAFETE, cuerpo, *V), V[0], V[1]


# ============================ DIRECCIÓN 3 — PREMIUM (vertical elegante) ============================

_CSS_PREMIUM = """
.prem{background:#fbf8ef;background-image:repeating-linear-gradient(45deg,rgba(201,161,74,.045) 0 1px,transparent 1px 11px)}
.prem .frame{position:absolute;inset:30px;border:3px solid var(--acc);border-radius:26px;opacity:.85}
.prem .frame::after{content:'';position:absolute;inset:7px;border:1px solid var(--oro);border-radius:20px}
.prem .corners{position:absolute;inset:0;pointer-events:none}
.prem .corners i{position:absolute;width:11px;height:11px;background:var(--oro);transform:rotate(45deg)}
.prem .corners i:nth-child(1){top:48px;left:48px}
.prem .corners i:nth-child(2){top:48px;right:48px}
.prem .corners i:nth-child(3){bottom:64px;left:48px}
.prem .corners i:nth-child(4){bottom:64px;right:48px}
.prem .botbar{position:absolute;left:0;right:0;bottom:0;height:46px;background:var(--oscuro);border-top:4px solid var(--oro)}
.prem .safe{position:absolute;left:56px;right:56px;top:60px;bottom:60px;display:flex;flex-direction:column;align-items:center;text-align:center}
.prem .logohdr{height:92px;display:flex;align-items:center;margin-top:4px}
.prem .logohdr img{max-height:92px;max-width:380px;object-fit:contain}
.prem .foto{margin-top:28px;width:252px;aspect-ratio:4/5;border:3px solid var(--acc);object-fit:cover;object-position:center 22%}
.prem .name{font-family:'Playfair';font-weight:600;font-size:50px;line-height:1.05;color:var(--acc);margin-top:28px}
.prem .goldline{width:330px;height:3px;background:var(--oro);margin:14px auto;position:relative}
.prem .goldline::after{content:'';position:absolute;left:50%;top:50%;width:13px;height:13px;background:var(--oro);transform:translate(-50%,-50%) rotate(45deg)}
.prem .role{font-size:28px;color:#2a2a2a;margin-bottom:32px}
.prem .data{width:344px;display:grid;gap:18px;text-align:left}
.prem .row{display:grid;grid-template-columns:54px 1px 1fr;gap:16px;align-items:center}
.prem .ic{width:54px;height:54px;border-radius:50%;background:var(--oscuro);display:flex;align-items:center;justify-content:center}
.prem .vline{height:54px;background:var(--acc);opacity:.6}
.prem .lb{color:var(--acc);font-weight:700;font-size:19px;text-transform:uppercase;letter-spacing:.08em}
.prem .vl{font-size:26px;color:#222}
.prem .bsafe{position:absolute;left:56px;right:56px;top:74px;bottom:74px;display:flex;flex-direction:column;align-items:center;text-align:center}
.prem .scan{font-size:26px;color:var(--acc);font-weight:800;letter-spacing:3px;text-transform:uppercase;margin-top:12px;margin-bottom:26px}
.prem .qrbox{width:286px;height:286px;background:#fff;border:10px solid #fff;outline:3px solid var(--acc);border-radius:6px;display:flex;align-items:center;justify-content:center;margin-bottom:28px}
.prem .qrbox img{width:100%;height:100%;object-fit:contain}
.prem .transfer{font-size:26px;line-height:1.3;color:#222;margin-bottom:26px}
.prem .web{border:2px solid var(--acc);border-radius:10px;padding:13px 30px;font-size:26px;color:var(--acc);font-weight:800;margin-bottom:36px;display:flex;align-items:center;gap:10px}
.prem .vig{font-size:27px;font-weight:800;color:var(--acc);display:flex;align-items:center;justify-content:center;gap:10px}
"""


def _premium(lado, ctx, d):
    if lado == "frontal":
        cuerpo = (
            "<div class='frame'></div><div class='botbar'></div><div class='corners'><i></i><i></i><i></i><i></i></div>"
            "<div class='safe'>"
            "<div class='logohdr'><img src='%s'></div>"
            "<img class='foto' src='%s'>"
            "<div class='name'>%s</div>"
            "<div class='goldline'></div>"
            "<div class='role'>%s</div>"
            "<div class='data'>"
            "<div class='row'><span class='ic'>%s</span><span class='vline'></span><span><div class='lb'>Empresa</div><div class='vl'>%s</div></span></div>"
            "<div class='row'><span class='ic'>%s</span><span class='vline'></span><span><div class='lb'>DNI</div><div class='vl'>%s</div></span></div>"
            "</div></div>"
            % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"],
               _icono("edificio", "#fff", 24), ctx["cliente"], _icono("persona", "#fff", 24), d["id"]))
    else:
        cuerpo = (
            "<div class='frame'></div><div class='botbar'></div><div class='corners'><i></i><i></i><i></i><i></i></div>"
            "<div class='bsafe'>"
            "<div class='scan'>Escanea para validar</div>"
            "<div class='qrbox'><img src='%s'></div>"
            "<div class='goldline'></div>"
            "<div class='transfer'>Credencial personal<br>e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "<div class='vig'>%s Vigencia 2026 — 2027</div>"
            "</div>"
            % (ctx["qr_uri"], _icono("globo", ctx["prim_legible"], 19), ctx["web"],
               _icono("calendario", ctx["prim_legible"], 19)))
    return _shell(ctx, "prem", _CSS_PREMIUM, cuerpo, *V), V[0], V[1]


# ---------- dispatcher ----------

_FNS = {"clasica": _clasica, "gafete": _gafete, "premium": _premium}


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto). estilo in {clasica,gafete,premium}; lado in {frontal,reverso}."""
    return _FNS[estilo](lado, ctx, ctx["datos"])
