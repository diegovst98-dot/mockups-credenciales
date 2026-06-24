# -*- coding: utf-8 -*-
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
LOGO = os.path.join(RECURSOS, "logo-disecod-oscuro.png")


def _hay_navegador():
    from render import _navegador_sistema
    return _navegador_sistema() is not None


requiere_edge = pytest.mark.skipif(not _hay_navegador(), reason="no hay Edge/Chrome para rasterizar")


@requiere_edge
def test_render_modelo_vertical_tamano_cr80():
    from motor import cargar_logo, render_modelo
    from estado import ajustes_inicial
    img = render_modelo(cargar_logo(LOGO), "Interbank", ajustes_inicial("mv7"))
    assert img.size == (638, 1011)        # vertical CR80 300 dpi


@requiere_edge
def test_render_modelo_horizontal_color_manual():
    from motor import cargar_logo, render_modelo
    from estado import ajustes_inicial, aplicar_cambios
    aj = aplicar_cambios(ajustes_inicial("clasica"), {"color": "#1f7a3d"})
    img = render_modelo(cargar_logo(LOGO), "Interbank", aj)
    assert img.size == (1011, 638)


@requiere_edge
def test_exportar_personalizado_crea_png_y_pdf(tmp_path):
    from motor import cargar_logo, exportar_personalizado
    from estado import ajustes_inicial
    carpeta, archivos = exportar_personalizado(
        cargar_logo(LOGO), "Interbank", ajustes_inicial("clasica"),
        carpeta_salida=str(tmp_path))
    assert any(a.endswith(".png") for a in archivos)
    assert any(a.endswith(".pdf") for a in archivos)
    for a in archivos:
        assert os.path.getsize(a) > 0
