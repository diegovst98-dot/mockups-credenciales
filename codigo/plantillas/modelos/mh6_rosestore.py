# -*- coding: utf-8 -*-
"""Modelo mh6 — "Rosestore" (horizontal). Ref: docs/referencias-modelos/h6.jpeg.
Gesto: foto GRANDE a la derecha (casi a sangre, alto completo, esquinas redondeadas)
con esquinas angulares bicolor (clip-path) detrás. Logo arriba-izquierda en su tinta real.
Nombre y DNI en negro a la izquierda; cargo en color de marca (REPARTIDOR). Sin banda de cargo.
Esquina inferior-izquierda negra + barrido rojo angular abajo."""
from plantillas.base import _shell, filas_html, H
from plantillas.registro import registrar

_CSS = """
.mh6{background:#fff}
/* --- foto grande a la derecha, alto casi completo, esquinas redondeadas --- */
.mh6 .foto{position:absolute;right:48px;top:170px;width:470px;height:430px;
  border-radius:26px;object-fit:cover;object-position:center 22%;background:#fff;z-index:3}
/* --- esquina angular roja arriba-derecha (detras de la foto, baja desde el borde) --- */
.mh6 .trojo{position:absolute;top:0;right:0;width:48%;height:300px;background:var(--prim);
  clip-path:polygon(30% 0,100% 0,100% 100%,68% 100%)}
/* --- esquina angular negra arriba-derecha (acento delgado pegado al borde sup.) --- */
.mh6 .tneg{position:absolute;top:0;right:0;width:22%;height:130px;background:var(--oscuro);
  clip-path:polygon(58% 0,100% 0,100% 100%)}
/* --- barrido rojo angular en la base (de izquierda a derecha) --- */
.mh6 .brojo{position:absolute;left:0;right:0;bottom:0;height:130px;background:var(--prim);
  clip-path:polygon(0 64%,100% 0,100% 100%,0 100%)}
/* --- esquina negra angular abajo-izquierda (encima del barrido rojo) --- */
.mh6 .bneg{position:absolute;left:0;bottom:0;width:40%;height:96px;background:var(--oscuro);
  clip-path:polygon(0 30%,80% 100%,0 100%)}
/* --- contenido textual izquierda (zona segura, no se encima con el barrido inferior) --- */
.mh6 .logo{position:absolute;top:58px;left:62px;height:120px;max-width:46%;object-fit:contain;z-index:4}
.mh6 .info{position:absolute;left:62px;top:228px;right:556px;z-index:4}
.mh6 .name{font-weight:800;font-size:56px;line-height:1.0;color:#1a1a1a;letter-spacing:.002em}
.mh6 .dni{margin-top:12px;font-weight:700;font-size:40px;color:#1a1a1a}
.mh6 .cargo{margin-top:24px;font-weight:800;font-size:40px;letter-spacing:.01em;
  text-transform:uppercase;color:var(--acc);line-height:1.05}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='trojo'></div><div class='tneg'></div>"
        "<div class='brojo'></div><div class='bneg'></div>"
        "<img class='foto' src='%s'>"
        "<img class='logo' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        % (ctx["foto_uri"], ctx["logo_uri"], d["nombre"], filas_html(ctx), d["cargo"]))
    return _shell(ctx, "mh6", _CSS, cuerpo, *H), H[0], H[1]


registrar("mh6", "Rosestore (horizontal)", "H", _frontal)
