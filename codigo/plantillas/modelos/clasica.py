# -*- coding: utf-8 -*-
"""DIRECCIÓN 1 — CLÁSICA (horizontal limpia)."""
from plantillas.base import _shell, _icono, filas_html, H
from plantillas.registro import registrar

_CSS_CLASICA = """
.clas{background:#fff}
.clas .safe{position:absolute;inset:50px;display:grid;grid-template-columns:286px 1fr;grid-template-rows:118px 1fr;column-gap:48px;row-gap:16px;z-index:1}
.clas .wm{position:absolute;right:-18px;bottom:-58px;font-family:'Playfair';font-weight:900;font-size:300px;line-height:.8;color:var(--acc);opacity:.045;z-index:0;pointer-events:none}
.clas .logohdr{grid-column:1/3;display:flex;align-items:center;justify-content:center}
.clas .logohdr img{height:104px;max-width:780px;object-fit:contain}
.clas .foto{grid-column:1;grid-row:2;align-self:center;width:286px;aspect-ratio:4/5;border:3px solid var(--acc);border-radius:10px;object-fit:cover;object-position:center 22%}
.clas .info{grid-column:2;grid-row:2;align-self:center}
.clas .name{font-family:'Inter';font-weight:800;font-size:58px;line-height:1.0;color:var(--acc);letter-spacing:-.01em;margin-bottom:24px;max-width:560px;position:relative}
.clas .name::after{content:'';position:absolute;left:2px;bottom:-11px;width:74px;height:4px;background:var(--acc2);border-radius:2px}
.clas .role{font-size:30px;font-weight:700;color:var(--acc);margin-bottom:30px;letter-spacing:.01em}
.clas .rows{display:grid;gap:16px;font-size:26px}
.clas .row{display:flex;align-items:center;gap:16px;border-top:2px solid #e4e6e2;padding-top:14px}
.clas .row .lb{color:var(--acc);font-weight:700}
.clas .ic{width:46px;height:46px;border-radius:50%;background:var(--oscuro);display:flex;align-items:center;justify-content:center;flex:0 0 auto}
.clas .bsafe{position:absolute;inset:50px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px}
.clas .oline{width:520px;height:2px;background:linear-gradient(90deg,transparent,var(--acc),transparent);opacity:.9}
.clas .scan{font-size:29px;color:var(--acc);font-weight:800;letter-spacing:3px;text-transform:uppercase}
.clas .qrbox{width:232px;height:232px;background:#fff;border:10px solid #fff;outline:3px solid var(--acc);border-radius:6px;display:flex;align-items:center;justify-content:center}
.clas .qrbox img{width:100%;height:100%;object-fit:contain}
.clas .ptxt{font-size:25px;color:#333;display:flex;align-items:center;justify-content:center;gap:9px}
.clas .web,.clas .vig{font-size:28px;font-weight:800;color:var(--acc);display:flex;align-items:center;justify-content:center;gap:9px}
"""


def _clasica(lado, ctx, d):
    if lado == "frontal":
        # zona de datos = filas editables (etiqueta:valor) del vendedor
        pos = {"izq": "flex-start", "der": "flex-end", "centro": "center"}.get(
            ctx["logo_pos"], "center")
        cuerpo = (
            "<div class='wm'>%s</div>"
            "<div class='safe'>"
            "<div class='logohdr' style='justify-content:%s'><img src='%s'></div>"
            "<img class='foto' src='%s'>"
            "<div class='info'>"
            "<div class='name'>%s</div>"
            "<div class='role'>%s</div>"
            "<div class='rows'>%s</div>"
            "</div></div>"
            % (ctx["monograma"], pos, ctx["logo_uri"], ctx["foto_uri"],
               d["nombre"], d["cargo"], filas_html(ctx)))
    else:
        cuerpo = (
            "<div class='bsafe'>"
            "<div class='oline'></div>"
            "<div class='scan'>Escanea para validar</div>"
            "<div class='qrbox'><img src='%s'></div>"
            "<div class='oline'></div>"
            "<div class='ptxt'>%s Credencial personal e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "<div class='vig'>%s Vigencia 2026 — 2027</div>"
            "</div>"
            % (ctx["qr_uri"], _icono("escudo", ctx["prim_legible"], 20),
               _icono("globo", ctx["prim_legible"], 20), ctx["web"],
               _icono("calendario", ctx["prim_legible"], 19)))
    return _shell(ctx, "clas", _CSS_CLASICA, cuerpo, *H), H[0], H[1]


registrar("clasica", "Clásica", "H", _clasica,
          campos_opcionales=("tipo_sangre", "codigo"),
          logo_posiciones=("default", "izq", "der", "centro"))
