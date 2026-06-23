# -*- coding: utf-8 -*-
"""DIRECCIÓN 2 — GAFETE (vertical moderno)."""
from plantillas.base import _shell, _icono, V
from plantillas.registro import registrar

_CSS_GAFETE = """
.gaf{background:#fff}
.gaf .wave{position:absolute;left:-40px;right:-40px;bottom:-30px;height:116px;background:var(--oscuro);border-radius:42% 42% 0 0}
.gaf .safe{position:absolute;inset:46px;display:flex;flex-direction:column;align-items:center;text-align:center}
.gaf .logohdr{height:94px;display:flex;align-items:center}
.gaf .logohdr img{max-height:94px;max-width:440px;object-fit:contain}
.gaf .foto{margin-top:26px;width:300px;aspect-ratio:4/5;border:3px solid #fff;border-radius:10px;object-fit:cover;object-position:center 22%;box-shadow:0 12px 30px -12px rgba(0,0,0,.35),0 0 0 1px #e3e3df}
.gaf .nameband{margin:28px -46px 18px;width:calc(100% + 92px);background:var(--oscuro);color:#fff;font-family:'Inter';font-weight:800;font-size:44px;line-height:1.1;padding:20px 14px;letter-spacing:-.01em;border-top:4px solid var(--acc2)}
.gaf .role{font-size:27px;color:var(--acc);font-weight:800;border-bottom:4px solid var(--acc2);padding-bottom:9px;margin-bottom:30px;letter-spacing:.05em;text-transform:uppercase}
.gaf .data{width:436px;display:grid;gap:16px;text-align:left}
.gaf .row{display:grid;grid-template-columns:58px 1fr;gap:16px;align-items:center;border-bottom:2px solid #d8e0d6;padding-bottom:13px}
.gaf .ic{width:50px;height:50px;border-radius:50%;background:#fff;border:3px solid var(--acc);display:flex;align-items:center;justify-content:center}
.gaf .lb{color:var(--acc);font-weight:700;font-size:19px;text-transform:uppercase;letter-spacing:.09em}
.gaf .vl{font-size:27px;color:#1a1a1a;font-weight:700}
.gaf .bsafe{position:absolute;inset:46px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:18px}
.gaf .qrbox{width:280px;height:280px;background:#fff;border:10px solid #fff;outline:3px solid var(--acc);border-radius:8px;display:flex;align-items:center;justify-content:center;margin-top:6px}
.gaf .qrbox img{width:100%;height:100%;object-fit:contain}
.gaf .pill{display:flex;align-items:center;gap:12px;border:3px solid var(--acc);border-radius:999px;padding:10px 24px;color:var(--acc);font-size:22px;font-weight:800;letter-spacing:.05em;text-transform:uppercase}
.gaf .transfer{font-size:23px;color:var(--acc);font-weight:700;display:flex;align-items:center;justify-content:center;gap:9px}
.gaf .web{font-size:27px;font-weight:800;color:var(--acc);display:flex;align-items:center;justify-content:center;gap:9px}
.gaf .vig{position:absolute;left:0;right:0;bottom:30px;color:#fff;font-size:25px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:9px}
"""


def _gafete(lado, ctx, d):
    if lado == "frontal":
        cuerpo = (
            "<div class='wave'></div>"
            "<div class='safe'>"
            "<div class='logohdr'><img src='%s'></div>"
            "<img class='foto' src='%s'>"
            "<div class='nameband'>%s</div>"
            "<div class='role'>%s</div>"
            "<div class='data'>"
            "<div class='row'><span class='ic'>%s</span><span><div class='lb'>Empresa</div><div class='vl'>%s</div></span></div>"
            "<div class='row'><span class='ic'>%s</span><span><div class='lb'>DNI</div><div class='vl'>%s</div></span></div>"
            "</div></div>"
            % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"],
               _icono("edificio", ctx["prim_legible"], 24), ctx["cliente"],
               _icono("persona", ctx["prim_legible"], 24), d["id"]))
    else:
        cuerpo = (
            "<div class='wave'></div>"
            "<div class='bsafe'>"
            "<div class='logohdr'><img src='%s'></div>"
            "<div class='qrbox'><img src='%s'></div>"
            "<div class='pill'>%s Escanea para validar</div>"
            "<div class='transfer'>%s Credencial personal e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "</div>"
            "<div class='vig'>%s Vigencia 2026 — 2027</div>"
            % (ctx["logo_uri"], ctx["qr_uri"], _icono("globo", ctx["prim_legible"], 20),
               _icono("escudo", ctx["prim_legible"], 20), _icono("globo", ctx["prim_legible"], 20),
               ctx["web"], _icono("calendario", "#fff", 18)))
    return _shell(ctx, "gaf", _CSS_GAFETE, cuerpo, *V), V[0], V[1]


registrar("gafete", "Gafete", "V", _gafete)
