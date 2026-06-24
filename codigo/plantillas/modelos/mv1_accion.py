# -*- coding: utf-8 -*-
"""Modelo mv1 — "Acción" (vertical). Ref: docs/referencias-modelos/v4.jpeg.
Gesto: chevrons diagonales bicolor en las esquinas superiores; foto cuadrada con
borde de marca; banda inferior con el cargo."""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv1{background:#fff}
.mv1 .tlb{position:absolute;top:0;left:0;width:54%;height:238px;background:var(--oscuro);clip-path:polygon(0 0,100% 0,0 100%)}
.mv1 .tl{position:absolute;top:0;left:0;width:50%;height:214px;background:var(--prim);clip-path:polygon(0 0,100% 0,0 100%)}
.mv1 .trb{position:absolute;top:0;right:0;width:54%;height:238px;background:var(--oscuro);clip-path:polygon(100% 0,0 0,100% 100%)}
.mv1 .tr{position:absolute;top:0;right:0;width:50%;height:214px;background:var(--prim);clip-path:polygon(100% 0,0 0,100% 100%)}
.mv1 .safe{position:absolute;left:0;right:0;top:0;bottom:150px;display:flex;flex-direction:column;align-items:center;text-align:center}
.mv1 .logo{margin-top:148px;height:104px;max-width:78%;object-fit:contain}
.mv1 .foto{margin-top:24px;width:258px;height:258px;border:6px solid var(--acc);object-fit:cover;object-position:center 22%}
.mv1 .name{margin-top:30px;font-weight:800;font-size:46px;line-height:1.08;color:#3a3a3a;max-width:92%;letter-spacing:.01em}
.mv1 .dni{margin-top:14px;font-weight:800;font-size:36px;color:var(--acc)}
.mv1 .cargo{position:absolute;left:0;right:0;bottom:0;min-height:150px;background:var(--prim);color:var(--txtprim);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:36px;letter-spacing:.05em;text-transform:uppercase;padding:22px 34px;text-align:center;line-height:1.12}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='tlb'></div><div class='tl'></div>"
        "<div class='trb'></div><div class='tr'></div>"
        "<div class='safe'>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "</div>"
        "<div class='cargo'>%s</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], filas_html(ctx), d["cargo"]))
    return _shell(ctx, "mv1", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv1", "Acción (vertical)", "V", _frontal)
