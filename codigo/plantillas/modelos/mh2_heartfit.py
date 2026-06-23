# -*- coding: utf-8 -*-
"""Modelo mh2 — "Heartfit" (horizontal). Ref: docs/referencias-modelos/h2.jpeg.
Gesto: panel izquierdo curvo de marca; foto circular con aro oscuro; banda inferior
con el cargo. Campo extra: tipo de sangre (GS)."""
from plantillas.base import _shell, H
from plantillas.registro import registrar

_CSS = """
.mh2{background:#fff}
.mh2 .panel{position:absolute;left:0;top:0;bottom:110px;width:215px;background:var(--prim);overflow:visible}
.mh2 .panel::after{content:'';position:absolute;right:-185px;top:0;bottom:0;width:380px;background:var(--prim);border-radius:50%}
.mh2 .foto{position:absolute;left:70px;top:150px;width:300px;height:300px;border-radius:50%;border:10px solid var(--oscuro);object-fit:cover;object-position:center 20%;background:#fff;z-index:2}
.mh2 .logo{position:absolute;top:42px;right:60px;height:104px;max-width:42%;object-fit:contain;z-index:2}
.mh2 .info{position:absolute;left:436px;right:56px;top:196px;z-index:2}
.mh2 .name{font-weight:800;font-size:60px;line-height:1.02;color:#1a1a1a}
.mh2 .dni{margin-top:20px;font-weight:800;font-size:38px;color:#1a1a1a}
.mh2 .gs{margin-top:14px;font-weight:800;font-size:38px;color:#1a1a1a}
.mh2 .cargo{position:absolute;left:0;right:0;bottom:0;height:110px;background:var(--oscuro);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:42px;letter-spacing:.08em;text-transform:uppercase;z-index:3}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='panel'></div>"
        "<img class='foto' src='%s'>"
        "<img class='logo' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='dni'>DNI: %s</div>"
        "<div class='gs'>GS: %s</div>"
        "</div>"
        "<div class='cargo'>%s</div>"
        % (ctx["foto_uri"], ctx["logo_uri"], d["nombre"], d["id"], d["tipo_sangre"], d["cargo"]))
    return _shell(ctx, "mh2", _CSS, cuerpo, *H), H[0], H[1]


registrar("mh2", "Heartfit (horizontal)", "H", _frontal)
