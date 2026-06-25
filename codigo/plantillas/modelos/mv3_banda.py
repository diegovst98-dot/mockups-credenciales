# -*- coding: utf-8 -*-
"""Modelo mv3 — "Banda superior" (vertical). Ref: docs/referencias-modelos/v2.jpeg.
Gesto: banda superior de marca (con segunda banda oscura desfasada a la derecha y
esquina inferior izquierda redondeada) que lleva el logo + nombre del cliente; foto
CIRCULAR con marco montada sobre el borde de la banda; nombre, DNI y cargo centrados
sobre mucho blanco; banda inferior oscura con la web del cliente. Campo extra: web."""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv3{background:#fff}
.mv3 .bandob{position:absolute;top:0;right:0;width:62%;height:560px;background:var(--oscuro);border-bottom-left-radius:80px}
.mv3 .banda{position:absolute;top:0;left:0;right:0;height:500px;background:var(--prim);border-bottom-left-radius:90px}
.mv3 .logo{position:absolute;top:56px;left:0;right:0;margin:0 auto;height:118px;max-width:62%;object-fit:contain;background:#fff;padding:22px 30px;border-radius:18px;box-shadow:0 6px 20px rgba(0,0,0,.18);z-index:3}
.mv3 .cli{position:absolute;top:248px;left:0;right:0;text-align:center;color:var(--txtprim);font-weight:800;font-size:38px;letter-spacing:.12em;text-transform:uppercase;z-index:3}
.mv3 .foto{position:absolute;top:330px;left:0;right:0;margin:0 auto;width:320px;height:320px;border-radius:50%;border:10px solid #111;object-fit:cover;object-position:center 20%;background:#fff;z-index:4}
.mv3 .info{position:absolute;left:0;right:0;top:690px;bottom:118px;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center}
.mv3 .name{font-weight:800;font-size:54px;line-height:1.04;color:#1a1a1a;max-width:94%}
.mv3 .dni{margin-top:12px;font-weight:800;font-size:38px;color:var(--acc)}
.mv3 .sep{margin-top:22px;width:120px;height:5px;background:#1a1a1a;border-radius:3px}
.mv3 .cargo{margin-top:22px;font-weight:700;font-size:42px;color:#1a1a1a;max-width:94%}
.mv3 .web{position:absolute;left:0;right:0;bottom:0;height:96px;background:var(--oscuro);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:34px;letter-spacing:.04em;z-index:3}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='bandob'></div>"
        "<div class='banda'></div>"
        "<img class='logo' src='%s'>"
        "<div class='cli'>%s</div>"
        "<img class='foto' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='sep'></div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        "<div class='web'>%s</div>"
        % (ctx["logo_uri"], ctx["cliente"], ctx["foto_uri"],
           d["nombre"], filas_html(ctx, con_empresa=False), d["cargo"], ctx["web"]))
    return _shell(ctx, "mv3", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv3", "Banda superior (vertical)", "V", _frontal, campos=['web'])
