# -*- coding: utf-8 -*-
"""mv8 — "Ondas (vertical)". Reproduce el modelo v8 del folleto DISECOD:
ondas/chevrons planos en las 4 esquinas (2 tonos: var(--prim) y var(--oscuro)),
logo centrado, foto CIRCULAR con aro de marca, nombre, DNI (acento) y cargo.
Fondo blanco, rellenos planos (apto Evolis). El logo va en su tinta real."""
from plantillas.base import _shell, filas_html, V
from plantillas.registro import registrar

_CSS = """
.mv8{background:#fff}

/* --- ESQUINA SUPERIOR IZQUIERDA: onda naranja (prim), bajada en chevron --- */
.mv8 .tl{position:absolute;top:0;left:0;width:46%;height:118px;background:var(--prim);
  border-bottom-right-radius:34px;clip-path:polygon(0 0,100% 0,82% 100%,0 100%)}
/* --- ESQUINA SUPERIOR DERECHA: onda azul oscuro (oscuro), un poco mas baja --- */
.mv8 .tr{position:absolute;top:0;right:0;width:54%;height:150px;background:var(--oscuro);
  border-bottom-left-radius:40px;clip-path:polygon(18% 0,100% 0,100% 100%,0 100%)}

/* --- ESQUINA INFERIOR IZQUIERDA: onda naranja (espejo de la superior) --- */
.mv8 .bl{position:absolute;bottom:0;left:0;width:54%;height:118px;background:var(--prim);
  border-top-right-radius:40px;clip-path:polygon(0 0,100% 0,82% 100%,0 100%)}
/* --- ESQUINA INFERIOR DERECHA: onda azul oscuro (espejo de la superior) --- */
.mv8 .br{position:absolute;bottom:0;right:0;width:46%;height:96px;background:var(--oscuro);
  border-top-left-radius:34px;clip-path:polygon(18% 0,100% 0,100% 100%,0 100%)}

/* --- CONTENIDO (zona segura: no toca las ondas de arriba ni la de abajo) --- */
.mv8 .safe{position:absolute;left:0;right:0;top:0;bottom:150px;
  display:flex;flex-direction:column;align-items:center;text-align:center}
.mv8 .logo{margin-top:172px;height:148px;max-width:60%;object-fit:contain}
.mv8 .foto{margin-top:30px;width:300px;height:300px;border-radius:50%;
  border:10px solid var(--prim);object-fit:cover;object-position:center 20%;
  background:#fff;box-shadow:0 0 0 11px #fff}
.mv8 .name{margin-top:40px;font-weight:800;font-size:50px;line-height:1.04;
  color:var(--acc);letter-spacing:-.01em;max-width:96%;padding:0 22px}
.mv8 .dni{margin-top:12px;font-weight:800;font-size:36px;color:var(--prim)}
.mv8 .cargo{margin-top:14px;font-weight:700;font-size:38px;color:var(--acc);
  letter-spacing:.01em;max-width:90%}
"""


def _frontal(lado, ctx, d):
    cuerpo = (
        "<div class='tl'></div><div class='tr'></div>"
        "<div class='bl'></div><div class='br'></div>"
        "<div class='safe'>"
        "<img class='logo' src='%s'>"
        "<img class='foto' src='%s'>"
        "<div class='name'>%s</div>"
        "<div class='datos'>%s</div>"
        "<div class='cargo'>%s</div>"
        "</div>"
        % (ctx["logo_uri"], ctx["foto_uri"], d["nombre"], filas_html(ctx), d["cargo"])
    )
    return _shell(ctx, "mv8", _CSS, cuerpo, *V), V[0], V[1]


registrar("mv8", "Ondas (vertical)", "V", _frontal)
