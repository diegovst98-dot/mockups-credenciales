# -*- coding: utf-8 -*-
"""Modelo mv7 — "Médico" (vertical). Ref: docs/referencias-modelos/v7.jpeg.
Gesto: estilo médico/limpio sobre blanco. Esquinas superiores con dos arcos curvos
(banda primaria + filo oscuro) que enmarcan; barrido curvo en la esquina inferior
derecha. Logo arriba, foto rectangular con marco de color, nombre, DNI en acento y
cargo en negro. Sin banda de cargo: jerarquía de texto centrado sobre blanco."""
from plantillas.base import _shell, V
from plantillas.registro import registrar

_CSS = """
.mv7{background:#fff}
/* --- arco superior: anillo curvo que enmarca las esquinas de arriba ---
   se hace con un círculo grande de BORDE grueso (banda) recortado por overflow
   de la tarjeta, dejando una franja curva fina. Filo oscuro detrás + banda primaria. */
.mv7 .topdark{position:absolute;top:-560px;left:-90px;width:820px;height:820px;
  border-radius:50%;border:44px solid var(--oscuro);background:transparent}
.mv7 .topprim{position:absolute;top:-578px;left:-72px;width:820px;height:820px;
  border-radius:50%;border:40px solid var(--prim);background:transparent}
/* --- barrido curvo inferior derecho: anillo recortado en la esquina --- */
.mv7 .botdark{position:absolute;bottom:-690px;right:-300px;width:760px;height:760px;
  border-radius:50%;border:46px solid var(--oscuro);background:transparent}
.mv7 .botprim{position:absolute;bottom:-708px;right:-282px;width:760px;height:760px;
  border-radius:50%;border:42px solid var(--prim);background:transparent}
/* --- zona segura de contenido (no se enciman con los arcos) --- */
.mv7 .safe{position:absolute;left:0;right:0;top:0;bottom:150px;z-index:3;
  display:flex;flex-direction:column;align-items:center;text-align:center;padding:0 40px}
.mv7 .logo{margin-top:170px;height:126px;max-width:60%;object-fit:contain}
.mv7 .foto{margin-top:30px;width:282px;height:312px;border:6px solid var(--acc);
  object-fit:cover;object-position:center 22%;background:#fff}
.mv7 .name{margin-top:28px;font-weight:800;font-size:48px;line-height:1.04;
  color:#2b2b2b;max-width:100%;letter-spacing:.005em}
.mv7 .dni{margin-top:13px;font-weight:800;font-size:37px;color:var(--acc)}
.mv7 .cargo{margin-top:7px;font-weight:800;font-size:37px;color:#1a1a1a;
  max-width:100%;line-height:1.08}
"""


def _frontal(lado, ctx, d):
    extra = ""
    if ctx["campos"].get("tipo_sangre"):
        extra = "<div class='dni'>Tipo de sangre: %s</div>" % d["tipo_sangre"]
    cuerpo = (
        "<div class='topdark'></div><div class='topprim'></div>"
        "<div class='botdark'></div><div class='botprim'></div>"
        "<div class='safe'>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='name'>%s</div>"
        "<div class='dni'>DNI: %s</div>"
        "<div class='cargo'>%s</div>"
        "%s"
        "</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], d["id"], d["cargo"], extra))
    return _shell(ctx, "mv7", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv7", "Médico (vertical)", "V", _frontal,
          campos_opcionales=("tipo_sangre",),
          logo_posiciones=("default",))
