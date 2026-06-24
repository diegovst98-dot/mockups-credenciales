# -*- coding: utf-8 -*-
"""mv5 — Tech onda (vertical).

Gesto gráfico: onda inferior PLANA en capas de color de marca (sin degradados,
imprenta Evolis). Logo arriba en su tinta real. Foto cuadrada con esquinas
redondeadas y borde de acento. Nombre, DNI de color, cargo en banda inferior.
"""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv5{background:#fff}

/* ---- ONDAS inferiores: capas planas de color (sin degradado) ----
   cada capa es un bloque ancho y plano; el borde superior se curva con
   border-radius en las esquinas superiores -> aspecto de onda de imprenta. */
.mv5 .ola{position:absolute;left:-10%;right:-10%;width:120%}
.mv5 .ola1{bottom:120px;height:96px;background:var(--acc2);border-top-left-radius:100% 80px;border-top-right-radius:100% 55px;transform:rotate(-3deg)}
.mv5 .ola2{bottom:74px;height:120px;background:var(--prim);border-top-left-radius:100% 95px;border-top-right-radius:100% 65px;transform:rotate(-3deg)}
.mv5 .ola3{bottom:34px;height:96px;background:var(--oscuro);border-top-left-radius:100% 55px;border-top-right-radius:100% 100px;transform:rotate(3deg)}
.mv5 .ola4{bottom:0;height:70px;background:var(--oro);border-top-left-radius:100% 110px;border-top-right-radius:100% 45px;transform:rotate(3deg)}

/* ---- zona segura: contenido por encima de las olas ---- */
.mv5 .safe{position:absolute;left:0;right:0;top:0;bottom:248px;display:flex;flex-direction:column;align-items:center;text-align:center;z-index:2}
.mv5 .logo{margin-top:80px;height:148px;max-width:74%;object-fit:contain}
.mv5 .foto{margin-top:30px;width:320px;height:320px;border:9px solid var(--acc2);border-radius:34px;object-fit:cover;object-position:center 22%;background:#fff}
.mv5 .name{margin-top:30px;font-weight:800;font-size:52px;line-height:1.0;color:#1a1a1a;max-width:94%;letter-spacing:.01em}
.mv5 .name .ape{display:block;font-size:40px;margin-top:6px}
.mv5 .dni{margin-top:18px;font-weight:800;font-size:40px;color:var(--acc);letter-spacing:.01em}
"""


def _nombre_partido(nombre):
    """Primera línea = nombres de pila; segunda = apellidos. Heurística por mitades."""
    p = nombre.replace(".", "").split()
    if len(p) <= 2:
        return nombre, ""
    corte = len(p) // 2
    return " ".join(p[:corte]), " ".join(p[corte:])


def _frontal(lado, ctx, d):
    pila, ape = _nombre_partido(d["nombre"])
    if ape:
        name_html = "%s<span class='ape'>%s</span>" % (pila.upper(), ape.upper())
    else:
        name_html = pila.upper()
    cuerpo = (
        "<div class='olawhite'></div>"
        "<div class='ola ola1'></div><div class='ola ola2'></div>"
        "<div class='ola ola3'></div><div class='ola ola4'></div>"
        "<div class='safe'>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], name_html, filas_html(ctx))
    )
    return _shell(ctx, "mv5", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv5", "Tech onda (vertical)", "V", _frontal)
