# -*- coding: utf-8 -*-
"""Modelo mv6 — "Minimalista" (vertical). Ref: docs/referencias-modelos/v6.jpeg.
Gesto: mucho blanco; logo arriba en su tinta real; dos bandas horizontales de marca
que cruzan detrás de una foto circular (con "muesca" blanca que las parte en dos);
nombre grande oscuro, DNI en píldora de marca, cargo sobrio sin banda y franja
inferior recortada en diagonal. Sobrio y limpio para Evolis (colores planos)."""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv6{background:#fff}
/* logo arriba, en su tinta real */
.mv6 .logo{position:absolute;top:78px;left:0;right:0;margin:0 auto;height:142px;max-width:74%;object-fit:contain}
/* bandas horizontales de marca que cruzan detras de la foto */
.mv6 .band{position:absolute;left:0;right:0;background:var(--prim)}
.mv6 .b1{top:368px;height:96px}
.mv6 .b2{top:500px;height:96px;background:var(--acc2m)}
/* foto circular centrada, encima de las bandas, anillo blanco para separarla */
.mv6 .foto{position:absolute;top:318px;left:0;right:0;margin:0 auto;width:300px;height:300px;border-radius:50%;border:10px solid #fff;object-fit:cover;object-position:center 20%;background:#fff;z-index:2}
.mv6 .ring{position:absolute;top:304px;left:0;right:0;margin:0 auto;width:328px;height:328px;border-radius:50%;background:var(--prim);z-index:1}
/* contenido de texto: empieza despues de las bandas, no se enciman */
.mv6 .info{position:absolute;left:48px;right:48px;top:668px;bottom:128px;display:flex;flex-direction:column;align-items:center;text-align:center}
.mv6 .name{font-weight:800;font-size:50px;line-height:1.05;color:#1a1a1a;letter-spacing:.01em}
.mv6 .pill{margin-top:24px;background:var(--prim);color:var(--txtprim);font-weight:800;font-size:32px;letter-spacing:.02em;padding:14px 40px;border-radius:40px}
.mv6 .cargo{margin-top:24px;font-weight:800;font-size:38px;color:#1a1a1a;letter-spacing:.06em;text-transform:uppercase;line-height:1.1}
/* franja inferior recortada en diagonal (acento de marca) */
.mv6 .foot{position:absolute;left:0;right:0;bottom:0;height:96px;background:var(--prim);clip-path:polygon(0 0,100% 0,100% 100%,72px 100%)}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<img class='logo' src='%s'>"
        "<div class='band b1'></div><div class='band b2'></div>"
        "<div class='ring'></div><img class='foto' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        "<div class='foot'></div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], filas_html(ctx), d["cargo"]))
    return _shell(ctx, "mv6", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv6", "Minimalista (vertical)", "V", _frontal)
