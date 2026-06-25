# -*- coding: utf-8 -*-
"""Modelo mh5 — "Podcast" (horizontal). Ref: docs/referencias-modelos/h5.jpeg.
Gesto: banda SUPERIOR de marca de ancho completo con un "bump" blanco semicircular
al centro donde va el logo; foto rectangular con esquinas redondeadas y borde oscuro
a la IZQUIERDA; a la derecha el nombre grande, el DNI dentro de una PASTILLA (pill) de
marca con texto var(--txtprim), y el cargo en texto oscuro debajo. Fondo blanco."""
from plantillas.base import _shell, filas_html, H
from plantillas.registro import registrar

_CSS = """
.mh5{background:#fff}
.mh5 .topband{position:absolute;top:0;left:0;right:0;height:182px;background:var(--prim)}
.mh5 .bump{position:absolute;top:0;left:50%;transform:translateX(-50%);width:420px;height:236px;background:#fff;border-radius:0 0 150px 150px}
.mh5 .logo{position:absolute;top:52px;left:50%;transform:translateX(-50%);height:108px;max-width:300px;object-fit:contain;z-index:2}
.mh5 .foto{position:absolute;left:90px;top:286px;width:282px;height:282px;border-radius:30px;border:8px solid #111;object-fit:cover;object-position:center 22%;background:#fff}
.mh5 .info{position:absolute;left:448px;right:56px;top:298px}
.mh5 .name{font-weight:800;font-size:52px;line-height:1.05;color:#1a1a1a;letter-spacing:.005em;text-transform:uppercase}
.mh5 .dni{margin-top:20px;display:inline-block;background:var(--prim);color:var(--txtprim);font-weight:800;font-size:33px;letter-spacing:.02em;padding:11px 38px;border-radius:999px}
.mh5 .cargo{margin-top:24px;font-weight:800;font-size:36px;line-height:1.1;letter-spacing:.02em;color:#1a1a1a;text-transform:uppercase}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='topband'></div>"
        "<div class='bump'></div>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], filas_html(ctx), d["cargo"]))
    return _shell(ctx, "mh5", _CSS, cuerpo, *H), H[0], H[1]


registrar("mh5", "Podcast (horizontal)", "H", _frontal)
