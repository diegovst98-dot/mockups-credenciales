# -*- coding: utf-8 -*-
"""Modelo mh7 — "Vegetata" (horizontal). Ref: docs/referencias-modelos/h7.jpeg.
Gesto: gran CÍRCULO oscuro (var(--oscuro)) que asoma por el borde izquierdo, con la
foto circular y aro blanco encima. A la derecha, sobre fondo blanco: logo arriba,
nombre en negro, DNI en acento de marca (var(--acc)), regla divisoria y cargo sobrio
debajo. Sin banda inferior. Sin campos extra."""
from plantillas.base import _shell, filas_html, H
from plantillas.registro import registrar

_CSS = """
.mh7{background:#fff}
.mh7 .circ{position:absolute;left:-210px;top:-96px;width:830px;height:830px;border-radius:50%;background:var(--oscuro)}
.mh7 .foto{position:absolute;left:70px;top:150px;width:330px;height:330px;border-radius:50%;border:8px solid #fff;object-fit:cover;object-position:center 22%;background:#fff;z-index:2}
.mh7 .logo{position:absolute;top:70px;left:690px;width:268px;height:150px;object-fit:contain;object-position:left center;z-index:2}
.mh7 .info{position:absolute;left:690px;right:30px;top:262px;z-index:2}
.mh7 .name{font-weight:800;font-size:34px;line-height:1.08;color:#1a1a1a;text-transform:uppercase;letter-spacing:.005em}
.mh7 .dni{margin-top:12px;font-weight:800;font-size:34px;color:var(--acc)}
.mh7 .rule{margin-top:24px;height:5px;background:#1a1a1a}
.mh7 .cargo{margin-top:24px;font-weight:700;font-size:40px;color:#1a1a1a;letter-spacing:.005em}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='circ'></div>"
        "<img class='foto' src='%s'>"
        "<img class='logo' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='rule'></div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        % (ctx["foto_uri"], ctx["logo_uri"], d["nombre"], filas_html(ctx), d["cargo"]))
    return _shell(ctx, "mh7", _CSS, cuerpo, *H), H[0], H[1]


registrar("mh7", "Vegetata (horizontal)", "H", _frontal)
