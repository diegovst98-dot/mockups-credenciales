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


def test_portada_v2_usa_la_marca_del_cliente():
    import folleto
    from PIL import Image
    marca = ((90, 70, 190), (40, 30, 90))
    logo = Image.new("RGBA", (400, 160), (10, 10, 10, 255))
    pag = folleto._portada_v2("ACME SAC", logo, marca)
    assert pag.size == folleto.PAG
    px = pag.convert("RGB")
    colores = px.getcolors(pag.size[0] * pag.size[1])
    planos = {c for _n, c in colores}
    assert marca[0] in planos or marca[1] in planos   # la marca está en la portada
    assert (0, 120, 200) not in planos                # adiós azul hardcodeado
