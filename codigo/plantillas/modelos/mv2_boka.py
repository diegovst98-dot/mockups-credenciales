# -*- coding: utf-8 -*-
"""mv2 — Boka (vertical). Blobs de color de marca arriba (der. e izq.) con la foto
CIRCULAR en un disco blanco recortado sobre el color, logo arriba a la izquierda,
nombre + DNI centrados y banda inferior OSCURA con el cargo."""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv2{background:#fff}
/* Blob color de marca arriba-derecha (esquina), curva hacia abajo-izquierda */
.mv2 .blobR{position:absolute;top:-170px;right:-170px;width:330px;height:470px;background:var(--prim);border-radius:0 0 0 100%;z-index:1}
/* Acento oscuro arriba-izquierda (esquina), para el bicolor estilo Böka */
.mv2 .blobTL{position:absolute;top:-190px;left:-190px;width:300px;height:380px;background:var(--oscuro);border-radius:0 0 100% 0;z-index:1}
/* Blob menor color de marca a la izquierda, detras del disco de la foto */
.mv2 .blobL{position:absolute;top:330px;left:-150px;width:430px;height:430px;background:var(--prim);border-radius:50%;z-index:1}
/* Disco blanco que "perfora" el color y enmarca la foto */
.mv2 .disco{position:absolute;top:300px;left:50%;transform:translateX(-50%);width:430px;height:430px;border-radius:50%;background:#fff;z-index:2}
.mv2 .foto{position:absolute;top:316px;left:50%;transform:translateX(-50%);width:398px;height:398px;border-radius:50%;object-fit:cover;object-position:center 22%;background:#fff;z-index:3}
/* Logo arriba centrado, sobre fondo blanco (su tinta real), SIEMPRE por encima de los blobs */
.mv2 .logo{position:absolute;top:58px;left:0;right:0;margin:0 auto;display:block;width:auto;max-width:54%;height:148px;object-fit:contain;object-position:center;z-index:6}
/* Bloque de textos centrado, por encima de la banda de cargo */
.mv2 .info{position:absolute;left:28px;right:28px;top:748px;bottom:130px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;z-index:4;overflow:hidden}
.mv2 .name{font-weight:800;font-size:46px;line-height:1.05;color:#1a1a1a;letter-spacing:0;text-transform:uppercase;max-width:100%}
.mv2 .dni{margin-top:22px;font-weight:800;font-size:40px;color:#1a1a1a;letter-spacing:.01em}
/* Banda inferior OSCURA con el cargo */
.mv2 .cargo{position:absolute;left:0;right:0;bottom:0;height:118px;background:var(--oscuro);color:var(--txtprim);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:34px;line-height:1.1;letter-spacing:.05em;text-transform:uppercase;text-align:center;padding:0 26px;z-index:5}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='blobR'></div><div class='blobTL'></div><div class='blobL'></div>"
        "<div class='disco'></div><img class='foto' src='%s'>"
        "<img class='logo' src='%s'>"
        "<div class='info'><div class='name'>%s</div><div class='datos'>%s</div></div>"
        "<div class='cargo'>%s</div>"
        % (ctx["foto_uri"], ctx["logo_uri"], d["nombre"], filas_html(ctx), d["cargo"])
    )
    return _shell(ctx, "mv2", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv2", "Böka (vertical)", "V", _frontal)
