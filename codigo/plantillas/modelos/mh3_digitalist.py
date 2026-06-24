# -*- coding: utf-8 -*-
"""Modelo mh3 — "Digitalist" (horizontal). Ref: docs/referencias-modelos/h3.jpeg.
Gesto: barras DIAGONALES bicolor (marca + gris/oscuro) en las esquinas superior-derecha
e inferior (clip-path); código de barras decorativo a la izquierda (repeating-linear-gradient);
foto rectangular con borde de marca; bloque de texto con nombre, DNI, CÓDIGO y cargo de color.
Campo extra: codigo."""
from plantillas.base import _shell, filas_html, H
from plantillas.registro import registrar

_CSS = """
.mh3{background:#fff}

/* --- barras diagonales esquina superior derecha --- */
.mh3 .trd{position:absolute;top:0;right:0;width:62%;height:150px;background:var(--oscuro);
  clip-path:polygon(34% 0,100% 0,100% 100%,0 100%)}
.mh3 .trp{position:absolute;top:0;right:0;width:62%;height:96px;background:var(--prim);
  clip-path:polygon(22% 0,100% 0,100% 100%,0 100%)}

/* --- barras diagonales esquina inferior izquierda --- */
.mh3 .bld{position:absolute;bottom:0;left:0;width:46%;height:128px;background:var(--oscuro);
  clip-path:polygon(0 0,100% 100%,0 100%)}
.mh3 .blp{position:absolute;bottom:0;left:0;width:34%;height:128px;background:var(--prim);
  clip-path:polygon(0 26%,100% 100%,0 100%)}

/* --- barras diagonales esquina inferior derecha --- */
.mh3 .brd{position:absolute;bottom:0;right:0;width:46%;height:128px;background:var(--oscuro);
  clip-path:polygon(100% 0,100% 100%,0 100%)}
.mh3 .brp{position:absolute;bottom:0;right:0;width:30%;height:128px;background:var(--prim);
  clip-path:polygon(100% 30%,100% 100%,0 100%)}

/* --- código de barras decorativo --- */
.mh3 .barcode{position:absolute;left:44px;top:212px;width:36px;height:248px;
  background:repeating-linear-gradient(0deg,#111 0 6px,#fff 6px 10px,#111 10px 14px,#fff 14px 22px,#111 22px 26px,#fff 26px 32px,#111 32px 42px,#fff 42px 46px);
  z-index:2}

/* --- foto rectangular con borde de marca --- */
.mh3 .foto{position:absolute;left:122px;top:186px;width:300px;height:300px;
  border:9px solid var(--prim);object-fit:cover;object-position:center 22%;background:#fff;z-index:2}

/* --- logo del cliente (tinta real, sin filtros) --- */
.mh3 .logo{position:absolute;top:150px;right:74px;height:106px;max-width:44%;object-fit:contain;z-index:3}

/* --- bloque de texto --- */
.mh3 .info{position:absolute;left:470px;right:56px;top:196px;z-index:3}
.mh3 .name{font-weight:800;font-size:54px;line-height:1.04;color:#1a1a1a;max-width:100%}
.mh3 .dni{margin-top:18px;font-weight:800;font-size:38px;color:#1a1a1a}
.mh3 .cod{margin-top:12px;font-weight:800;font-size:38px;color:#1a1a1a}
.mh3 .cargo{margin-top:16px;font-weight:800;font-size:40px;letter-spacing:.04em;
  text-transform:uppercase;color:var(--acc);line-height:1.05}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='trd'></div><div class='trp'></div>"
        "<div class='bld'></div><div class='blp'></div>"
        "<div class='brd'></div><div class='brp'></div>"
        "<div class='barcode'></div>"
        "<img class='foto' src='%s'>"
        "<img class='logo' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        % (ctx["foto_uri"], ctx["logo_uri"], d["nombre"], filas_html(ctx), d["cargo"]))
    return _shell(ctx, "mh3", _CSS, cuerpo, *H), H[0], H[1]


registrar("mh3", "Digitalist (horizontal)", "H", _frontal, campos=['codigo'])
