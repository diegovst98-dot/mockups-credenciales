# -*- coding: utf-8 -*-
"""mv4 — "Nombre en banda (vertical)".
Logo arriba sobre fondo blanco, foto rectangular con borde gris, y la mitad
inferior es una banda plena var(--prim): el NOMBRE va en grande sobre esa banda
(texto var(--txtprim)), luego una franja var(--oscuro) con el CARGO y al final
una franja var(--prim) con el DNI. Sin degradados (imprime en Evolis)."""
from plantillas.base import _shell, V
from plantillas.registro import registrar

_CSS = """
.mv4{background:#fff}
.mv4 .banda{position:absolute;left:0;right:0;bottom:0;height:328px;background:var(--prim)}
.mv4 .logo{position:absolute;top:60px;left:50%;transform:translateX(-50%);height:150px;max-width:70%;object-fit:contain}
.mv4 .foto{position:absolute;top:268px;left:50%;transform:translateX(-50%);width:300px;height:360px;border:7px solid #6b6f76;object-fit:cover;object-position:center 20%;background:#fff;z-index:2}
.mv4 .name{position:absolute;left:34px;right:34px;top:700px;height:172px;display:flex;flex-direction:column;justify-content:center;font-weight:800;font-size:58px;line-height:1.04;color:var(--txtprim);z-index:3}
.mv4 .cargo{position:absolute;left:0;right:0;bottom:118px;height:92px;background:var(--oscuro);color:var(--txtprim);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:42px;text-align:center;padding:0 28px;line-height:1.1;z-index:3}
.mv4 .dni{position:absolute;left:0;right:0;bottom:0;height:118px;display:flex;align-items:center;justify-content:center;color:var(--txtprim);font-weight:700;font-size:46px;letter-spacing:.01em;z-index:3}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='banda'></div>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='name'>%s</div>"
        "<div class='cargo'>%s</div>"
        "<div class='dni'>DNI: %s</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"], d["id"])
    )
    return _shell(ctx, "mv4", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv4", "Nombre en banda (vertical)", "V", _frontal)
