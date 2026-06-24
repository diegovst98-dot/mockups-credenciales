# -*- coding: utf-8 -*-
"""Cableado de la pestaña Personalizar (v2) sin rasterizar: con p_logo=None el
re-render hace early-return (no abre Edge), así probamos chat→Ajustes→controles
de forma rápida y headless. La lógica fina (asistente/estado/render) ya tiene sus
propios tests; aquí verificamos el pegamento de la GUI.

Se usa UN solo root Tk compartido + un Toplevel por test: crear muchos tk.Tk() en
un mismo proceso re-inicializa Tcl y falla intermitente ('init.tcl: No error')."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))

try:
    import tkinter as tk
    _ROOT = tk.Tk()
    _ROOT.withdraw()
    _TK_OK = True
except Exception:
    _ROOT = None
    _TK_OK = False

pytestmark = pytest.mark.skipif(not _TK_OK, reason="sin display tkinter")


def _app():
    """App sobre un Toplevel hijo del root compartido (no un Tk() nuevo)."""
    import app as appmod
    top = tk.Toplevel(_ROOT)
    top.withdraw()
    return top, appmod.App(top)


def test_tres_pestanas_incluye_personalizar():
    from tkinter import ttk
    top, a = _app()
    try:
        nb = [w for w in top.winfo_children() if isinstance(w, ttk.Notebook)][0]
        tabs = [nb.tab(t, "text") for t in nb.tabs()]
        assert tabs == ["Mockups", "Renombrar Cotizaciones", "Personalizar"]
    finally:
        top.destroy()


def test_selector_tiene_18_modelos():
    top, a = _app()
    try:
        assert len(a._modelos) == 18
        assert len(a.p_modelo_combo["values"]) == 18
    finally:
        top.destroy()


def test_controles_clasica_tienen_campos_opcionales():
    import estado
    top, a = _app()
    try:
        a.p_ajustes = estado.ajustes_inicial("clasica")
        a._p_rebuild_controles()
        assert set(a._p_campo_vars.keys()) == {"tipo_sangre", "codigo"}
    finally:
        top.destroy()


def test_chat_prende_campo_y_muta_ajustes():
    import estado
    top, a = _app()
    try:
        a.p_ajustes = estado.ajustes_inicial("clasica")
        a._p_rebuild_controles()
        a.p_entrada.insert(0, "ponle tipo de sangre")
        a._p_enviar()                                   # p_logo=None => sin Edge
        assert a.p_ajustes["campos"].get("tipo_sangre") is True
        assert a._p_campo_vars["tipo_sangre"].get() is True   # control sincronizado
    finally:
        top.destroy()


def test_chat_color_azul_muta_ajustes():
    top, a = _app()
    try:
        a.p_entrada.insert(0, "color azul")
        a._p_enviar()
        assert a.p_ajustes["color"] == "#1f4ed8"
    finally:
        top.destroy()


def test_cambiar_modelo_conserva_color_resetea_campos():
    import estado
    top, a = _app()
    try:
        a.p_ajustes = estado.aplicar_cambios(
            estado.ajustes_inicial("clasica"),
            {"color": "#123456", "campos": {"tipo_sangre": True}})
        nombre_premium = next(n for c, n in a._modelos if c == "premium")
        a.p_modelo_var.set(nombre_premium)
        a._p_cambiar_modelo()                           # p_logo=None => sin Edge
        assert a.p_ajustes["modelo"] == "premium"
        assert a.p_ajustes["color"] == "#123456"        # color se conserva
        assert a.p_ajustes["campos"] == {}              # campos se resetean (son por-modelo)
    finally:
        top.destroy()
