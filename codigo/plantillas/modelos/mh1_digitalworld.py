# -*- coding: utf-8 -*-
"""Modelo mh1 — "Digital World" (horizontal). Ref: docs/referencias-modelos/h1.jpeg.
Gesto: banda superior de marca + barrido oscuro diagonal; foto cuadrada con borde
oscuro a la izquierda; nombre/DNI a la derecha; cargo en banda; acento angular abajo-derecha."""
from plantillas.base import _shell, filas_html, H
from plantillas.registro import registrar

_CSS = """
.mh1{background:#fff}
.mh1 .topband{position:absolute;top:0;left:0;width:60%;height:88px;background:var(--prim)}
.mh1 .topdark{position:absolute;top:0;left:26%;width:46%;height:120px;background:var(--oscuro);clip-path:polygon(20% 0,100% 0,80% 100%,0 100%)}
.mh1 .logo{position:absolute;top:34px;right:56px;height:120px;max-width:40%;object-fit:contain}
.mh1 .foto{position:absolute;left:62px;top:182px;width:300px;height:300px;border:7px solid var(--oscuro);object-fit:cover;object-position:center 22%}
.mh1 .info{position:absolute;left:436px;right:56px;top:196px}
.mh1 .name{font-weight:800;font-size:62px;line-height:1.04;color:#1a1a1a;letter-spacing:.005em}
.mh1 .dni{margin-top:22px;font-weight:800;font-size:40px;color:#1a1a1a}
.mh1 .cargo{margin-top:28px;display:inline-block;background:var(--prim);color:var(--txtprim);font-weight:800;font-size:34px;letter-spacing:.05em;text-transform:uppercase;padding:14px 48px}
.mh1 .botcorner{position:absolute;right:0;bottom:0;width:34%;height:118px;background:var(--oscuro);clip-path:polygon(42% 0,100% 0,100% 100%,0 100%)}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='topband'></div><div class='topdark'></div>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        "<div class='botcorner'></div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], filas_html(ctx), d["cargo"]))
    return _shell(ctx, "mh1", _CSS, cuerpo, *H), H[0], H[1]


registrar("mh1", "Digital World (horizontal)", "H", _frontal)
