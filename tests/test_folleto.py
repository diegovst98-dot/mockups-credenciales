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
