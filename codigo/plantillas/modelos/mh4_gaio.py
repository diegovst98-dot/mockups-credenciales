# -*- coding: utf-8 -*-
"""Modelo mh4 — "Gaio onda" (horizontal). Ref: docs/referencias-modelos/h4.jpeg.
Gesto: ONDA de color PLANA. Una mancha azul superior-derecha con una "lente" blanca
elíptica recortada en el centro, una banda inferior ondulada y un acento gris diagonal
en la esquina inferior-izquierda. Logo arriba-izquierda (tinta real), foto circular con
aro de marca a la izquierda; a la derecha nombre (negro + 2ª línea de color), DNI en
itálica y cargo de color en dos líneas. Sin campos extra."""
from plantillas.base import _shell, H
from plantillas.registro import registrar

_CSS = """
.mh4{background:#fff}
/* --- onda superior derecha: mancha de marca con lente blanca --- */
.mh4 .top{position:absolute;top:-170px;right:-150px;width:830px;height:610px;background:var(--prim);border-radius:0 0 0 100%}
.mh4 .lens{position:absolute;top:60px;right:-150px;width:880px;height:470px;background:#fff;border-radius:50%}
/* --- banda inferior ondulada de marca (sube hacia la derecha) --- */
.mh4 .bot{position:absolute;left:-120px;bottom:-190px;right:-150px;height:330px;background:var(--prim);border-radius:48% 52% 0 0/100% 100% 0 0}
/* --- acento gris diagonal esquina inferior izquierda --- */
.mh4 .accent{position:absolute;left:-60px;bottom:-44px;width:400px;height:120px;background:#9aa0a6;border-radius:0 70% 0 0/0 100% 0 0;transform:rotate(-3deg);z-index:1}
/* --- logo (tinta real, sin filtros) --- */
.mh4 .logo{position:absolute;top:42px;left:58px;height:120px;max-width:40%;object-fit:contain;z-index:5}
/* --- foto circular con aro de marca --- */
.mh4 .foto{position:absolute;left:120px;top:198px;width:330px;height:330px;border-radius:50%;border:9px solid var(--prim);object-fit:cover;object-position:center 18%;background:#fff;z-index:6}
/* --- bloque de texto a la derecha --- */
.mh4 .info{position:absolute;left:498px;right:72px;top:196px;z-index:6;text-align:center}
.mh4 .n1{font-weight:800;font-size:58px;line-height:1.0;color:#1a1a1a;letter-spacing:.01em}
.mh4 .n2{font-weight:800;font-size:50px;line-height:1.04;color:var(--acc)}
.mh4 .dni{margin-top:14px;font-weight:700;font-style:italic;font-size:36px;color:#1a1a1a}
.mh4 .cargo{margin-top:26px;font-weight:800;font-size:46px;line-height:1.04;color:var(--acc);text-transform:uppercase;letter-spacing:.01em}
"""


def _frontal(lado, ctx, d):
    p = d["nombre"].split()
    n1 = p[0] if p else d["nombre"]
    n2 = " ".join(p[1:]) if len(p) > 1 else ""
    nombre = "<div class='n1'>%s</div>" % n1
    if n2:
        nombre += "<div class='n2'>%s</div>" % n2
    cuerpo = (
        "<div class='top'></div>"
        "<div class='lens'></div>"
        "<div class='bot'></div>"
        "<div class='accent'></div>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='info'>"
        "%s"
        "<div class='dni'>DNI: %s</div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], nombre, d["id"], d["cargo"]))
    return _shell(ctx, "mh4", _CSS, cuerpo, *H), H[0], H[1]


registrar("mh4", "Gaio onda (horizontal)", "H", _frontal)
