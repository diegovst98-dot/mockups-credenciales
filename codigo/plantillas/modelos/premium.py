# -*- coding: utf-8 -*-
"""DIRECCIÓN 3 — PREMIUM (vertical elegante)."""
from plantillas.base import _shell, _icono, filas_html, V
from plantillas.registro import registrar

_CSS_PREMIUM = """
.prem{background:#fbf8ef;background-image:repeating-linear-gradient(45deg,rgba(201,161,74,.045) 0 1px,transparent 1px 11px)}
.prem .frame{position:absolute;inset:30px;border:3px solid var(--acc);border-radius:26px;opacity:.85}
.prem .frame::after{content:'';position:absolute;inset:7px;border:1px solid var(--oro);border-radius:20px}
.prem .corners{position:absolute;inset:0;pointer-events:none}
.prem .corners i{position:absolute;width:11px;height:11px;background:var(--oro);transform:rotate(45deg)}
.prem .corners i:nth-child(1){top:48px;left:48px}
.prem .corners i:nth-child(2){top:48px;right:48px}
.prem .corners i:nth-child(3){bottom:64px;left:48px}
.prem .corners i:nth-child(4){bottom:64px;right:48px}
.prem .botbar{position:absolute;left:0;right:0;bottom:0;height:46px;background:var(--oscuro);border-top:4px solid var(--oro)}
.prem .safe{position:absolute;left:56px;right:56px;top:60px;bottom:60px;display:flex;flex-direction:column;align-items:center;text-align:center}
.prem .logohdr{height:92px;display:flex;align-items:center;margin-top:4px}
.prem .logohdr img{max-height:92px;max-width:380px;object-fit:contain}
.prem .foto{margin-top:28px;width:252px;aspect-ratio:4/5;border:3px solid var(--acc);object-fit:cover;object-position:center 22%}
.prem .name{font-family:'Playfair';font-weight:600;font-size:50px;line-height:1.05;color:var(--acc);margin-top:28px}
.prem .goldline{width:330px;height:3px;background:var(--oro);margin:14px auto;position:relative}
.prem .goldline::after{content:'';position:absolute;left:50%;top:50%;width:13px;height:13px;background:var(--oro);transform:translate(-50%,-50%) rotate(45deg)}
.prem .role{font-size:28px;color:#2a2a2a;margin-bottom:32px}
.prem .data{width:344px;display:grid;gap:18px;text-align:left}
.prem .row{display:grid;grid-template-columns:54px 1px 1fr;gap:16px;align-items:center}
.prem .ic{width:54px;height:54px;border-radius:50%;background:var(--oscuro);display:flex;align-items:center;justify-content:center}
.prem .vline{height:54px;background:var(--acc);opacity:.6}
.prem .lb{color:var(--acc);font-weight:700;font-size:19px;text-transform:uppercase;letter-spacing:.08em}
.prem .vl{font-size:26px;color:#222}
.prem .bsafe{position:absolute;left:56px;right:56px;top:74px;bottom:74px;display:flex;flex-direction:column;align-items:center;text-align:center}
.prem .scan{font-size:26px;color:var(--acc);font-weight:800;letter-spacing:3px;text-transform:uppercase;margin-top:12px;margin-bottom:26px}
.prem .qrbox{width:286px;height:286px;background:#fff;border:10px solid #fff;outline:3px solid var(--acc);border-radius:6px;display:flex;align-items:center;justify-content:center;margin-bottom:28px}
.prem .qrbox img{width:100%;height:100%;object-fit:contain}
.prem .transfer{font-size:26px;line-height:1.3;color:#222;margin-bottom:26px}
.prem .web{border:2px solid var(--acc);border-radius:10px;padding:13px 30px;font-size:26px;color:var(--acc);font-weight:800;margin-bottom:36px;display:flex;align-items:center;gap:10px}
.prem .vig{font-size:27px;font-weight:800;color:var(--acc);display:flex;align-items:center;justify-content:center;gap:10px}
"""


def _premium(lado, ctx, d):
    if lado == "frontal":
        cuerpo = (
            "<div class='frame'></div><div class='botbar'></div><div class='corners'><i></i><i></i><i></i><i></i></div>"
            "<div class='safe'>"
            "<div class='logohdr'><img src='%s'></div>"
            "<img class='foto' src='%s'>"
            "<div class='name'>%s</div>"
            "<div class='goldline'></div>"
            "<div class='role'>%s</div>"
            "<div class='data'>%s</div></div>"
            % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["cargo"], filas_html(ctx)))
    else:
        cuerpo = (
            "<div class='frame'></div><div class='botbar'></div><div class='corners'><i></i><i></i><i></i><i></i></div>"
            "<div class='bsafe'>"
            "<div class='scan'>Escanea para validar</div>"
            "<div class='qrbox'><img src='%s'></div>"
            "<div class='goldline'></div>"
            "<div class='transfer'>Credencial personal<br>e intransferible</div>"
            "<div class='web'>%s %s</div>"
            "<div class='vig'>%s Vigencia 2026 — 2027</div>"
            "</div>"
            % (ctx["qr_uri"], _icono("globo", ctx["prim_legible"], 19), ctx["web"],
               _icono("calendario", ctx["prim_legible"], 19)))
    return _shell(ctx, "prem", _CSS_PREMIUM, cuerpo, *V), V[0], V[1]


registrar("premium", "Premium", "V", _premium)
