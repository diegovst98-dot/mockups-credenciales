# -*- coding: utf-8 -*-
"""Modelo mv3 — "Corporativa" (vertical). Rediseño 2.0 (2026-07-06, feedback Diego):
pensar "credencial de banco": líneas RECTAS y simetría total, cero blobs ni esquinas
gigantes ni bandas desfasadas. Gesto: banda superior DELGADA plana en color de marca;
logo del cliente flotando en blanco debajo (grande, centrado, intacto — regla fija:
nunca placas tras el logo); foto RECTANGULAR con borde fino centrada; nombre en negro
fuerte, DNI en acento, separador fino, cargo; banda inferior oscura con la web.
Elegancia = alineación + aire. Extra: web."""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv3{background:#fff}
.mv3 .bandatop{position:absolute;top:0;left:0;right:0;height:44px;background:var(--prim)}
.mv3 .logo{position:absolute;top:112px;left:0;right:0;margin:0 auto;height:138px;max-width:64%;object-fit:contain}
.mv3 .foto{position:absolute;top:322px;left:0;right:0;margin:0 auto;width:300px;height:336px;border:4px solid var(--oscuro);object-fit:cover;object-position:center 20%;background:#fff}
.mv3 .info{position:absolute;left:30px;right:30px;top:700px;bottom:96px;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center}
.mv3 .name{font-weight:800;font-size:50px;line-height:1.05;color:#1a1a1a;max-width:100%}
.mv3 .dni{margin-top:12px;font-weight:800;font-size:34px;color:var(--acc)}
.mv3 .sep{margin-top:20px;width:110px;height:4px;background:var(--prim)}
.mv3 .cargo{margin-top:20px;font-weight:700;font-size:36px;color:#1a1a1a;max-width:100%;line-height:1.1}
.mv3 .web{position:absolute;left:0;right:0;bottom:0;height:80px;background:var(--oscuro);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:31px;letter-spacing:.06em}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='bandatop'></div>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='info'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='sep'></div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        "<div class='web'>%s</div>"
        % (ctx["logo_uri"], ctx["foto_uri"],
           d["nombre"], filas_html(ctx, con_empresa=False), d["cargo"], ctx["web"]))
    return _shell(ctx, "mv3", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv3", "Banda superior (vertical)", "V", _frontal, campos=['web'])
