# -*- coding: utf-8 -*-
"""Modelo mv3 — "Corporativa" (vertical). Ref: docs/referencias-modelos/v2.jpeg.
Gesto: cabecera BLANCA generosa donde el logo del cliente flota intacto (regla fija:
nunca placas/cajas tras el logo) — SIN rótulo del cliente debajo (los logos wordmark
ya llevan el nombre y se veía duplicado, fix 2026-07-06); banda de marca en la zona media (con segunda banda oscura desfasada a la derecha y
esquina inferior izquierda redondeada) sobre cuyo borde monta la foto CIRCULAR;
nombre, DNI y cargo centrados con aire; banda inferior oscura con la web. Extra: web."""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv3{background:#fff}
.mv3 .logo{position:absolute;top:84px;left:0;right:0;margin:0 auto;height:150px;max-width:68%;object-fit:contain;z-index:3}
.mv3 .bandob{position:absolute;top:316px;right:0;width:62%;height:258px;background:var(--oscuro);border-bottom-left-radius:80px}
.mv3 .banda{position:absolute;top:316px;left:0;right:0;height:210px;background:var(--prim);border-bottom-left-radius:90px}
.mv3 .foto{position:absolute;top:384px;left:0;right:0;margin:0 auto;width:304px;height:304px;border-radius:50%;border:10px solid #111;object-fit:cover;object-position:center 20%;background:#fff;z-index:4}
.mv3 .info{position:absolute;left:0;right:0;top:724px;bottom:132px;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center}
.mv3 .name{font-weight:800;font-size:52px;line-height:1.04;color:#1a1a1a;max-width:94%}
.mv3 .dni{margin-top:10px;font-weight:800;font-size:34px;color:var(--acc)}
.mv3 .sep{margin-top:18px;width:120px;height:5px;background:#1a1a1a;border-radius:3px}
.mv3 .cargo{margin-top:18px;font-weight:700;font-size:36px;color:#1a1a1a;max-width:94%}
.mv3 .web{position:absolute;left:0;right:0;bottom:0;height:84px;background:var(--oscuro);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:32px;letter-spacing:.06em;z-index:3}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='bandob'></div>"
        "<div class='banda'></div>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='sep'></div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        "<div class='web'>%s</div>"
        % (ctx["logo_uri"], ctx["foto_uri"],
           d["nombre"], filas_html(ctx, con_empresa=False), d["cargo"], ctx["web"]))
    return _shell(ctx, "mv3", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv3", "Banda superior (vertical)", "V", _frontal, campos=['web'])
