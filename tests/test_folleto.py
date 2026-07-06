# -*- coding: utf-8 -*-
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
from PIL import Image  # noqa: E402


def test_armar_pdf_genera_archivo_y_paginas():
    from folleto import armar_pdf
    logo = Image.new("RGBA", (300, 120), (0, 120, 200, 255))
    items = ([("Modelo V%d" % i, "V", Image.new("RGB", (638, 1011), (240, 240, 240))) for i in range(4)] +
             [("Modelo H%d" % i, "H", Image.new("RGB", (1011, 638), (235, 235, 235))) for i in range(3)])
    pdf = os.path.join(tempfile.mkdtemp(prefix="t_foll_"), "cat.pdf")
    n = armar_pdf("Acme S.A.C.", logo, items, pdf)
    assert os.path.exists(pdf) and os.path.getsize(pdf) > 1000
    assert n >= 3  # portada + verticales + horizontales (al menos)


def test_armar_pdf_solo_verticales():
    from folleto import armar_pdf
    logo = Image.new("RGBA", (300, 120), (200, 60, 40, 255))
    items = [("V%d" % i, "V", Image.new("RGB", (638, 1011), (250, 250, 250))) for i in range(8)]
    pdf = os.path.join(tempfile.mkdtemp(prefix="t_foll2_"), "cat.pdf")
    n = armar_pdf("Solo Verticales", logo, items, pdf)
    assert os.path.exists(pdf)
    assert n >= 2  # portada + al menos una pagina de verticales


def _item(nombre, ori):
    from PIL import Image
    w, h = (638, 1011) if ori == "V" else (1011, 638)
    return (nombre, ori, Image.new("RGB", (w, h), (200, 200, 210)))


def test_armar_propuesta_estructura(tmp_path):
    import folleto
    from PIL import Image
    marca = ((90, 70, 190), (40, 30, 90))
    logo = Image.new("RGBA", (400, 160), (10, 10, 10, 255))
    alts = [_item("Ejecutiva", "H"), _item("Minimalista", "V"),
            _item("Círculo", "H"), _item("Clásica", "H"), _item("Ondas", "V")]
    ruta = str(tmp_path / "propuesta.pdf")
    n = folleto.armar_propuesta("ACME SAC", logo, _item("Premium", "V"), alts, ruta, marca)
    assert os.path.exists(ruta)
    # portada + estrella + alternativas (5 con aire → ≥2 páginas) + CTA
    assert n >= 5


def test_portada_v2_chrome_disecod():
    """La portada es documento de marca DISECOD (LILA/CARBON): el color del
    cliente ya NO pinta bandas; su logo sí sigue protagonista (intacto)."""
    import folleto
    from PIL import Image
    marca = ((200, 30, 40), (90, 10, 20))     # marca roja del cliente
    logo = Image.new("RGBA", (120, 48), (200, 30, 40, 255))
    pag = folleto._portada_v2("ACME SAC", logo, marca)
    assert pag.size == folleto.PAG
    px = pag.convert("RGB")
    colores = px.getcolors(pag.size[0] * pag.size[1])
    planos = {c: n for n, c in colores}
    assert folleto.LILA in planos and folleto.CARBON in planos
    assert (0, 120, 200) not in planos                # adiós azul hardcodeado
    # el rojo del cliente aparece SOLO como logo (exactamente su área),
    # no como banda (una banda ocuparía el ancho completo de la página)
    assert planos.get(marca[0], 0) == 120 * 48


def test_cta_banda_carbon_con_logo_disecod():
    import folleto
    pag = folleto._pagina_cta("ACME SAC", ((200, 30, 40), (90, 10, 20)))
    colores = pag.convert("RGB").getcolors(pag.size[0] * pag.size[1])
    planos = {c for _n, c in colores}
    assert folleto.CARBON in planos and folleto.LILA in planos
    assert folleto._logo_disecod_blanco() is not None  # asset presente en codigo\\
