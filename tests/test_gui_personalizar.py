# -*- coding: utf-8 -*-
"""Cableado del editor de campos (v2.2) sin rasterizar: con p_logo=None el re-render hace
early-return (no abre Edge). UN root Tk compartido + un Toplevel por test (crear muchos
tk.Tk() rompe Tcl)."""
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
    finally:
        top.destroy()


def test_ya_no_hay_chat():
    top, a = _app()
    try:
        assert not hasattr(a, "p_chat")
    finally:
        top.destroy()


def test_agregar_y_editar_campo():
    import estado
    top, a = _app()
    try:
        a.p_ajustes = estado.ajustes_inicial("clasica")
        a._p_render_filas_editor()
        n0 = len(a.p_ajustes["filas"])
        a._p_agregar_fila()
        assert len(a.p_ajustes["filas"]) == n0 + 1
        a._p_fila_rows[-1][0].insert(0, "Área")
        a._p_fila_rows[-1][1].insert(0, "Logística")
        a._p_on_filas()
        assert a.p_ajustes["filas"][-1] == {"etiqueta": "Área", "valor": "Logística"}
    finally:
        top.destroy()


def test_quitar_campo():
    import estado
    top, a = _app()
    try:
        a.p_ajustes = estado.aplicar_cambios(
            estado.ajustes_inicial("clasica"),
            {"filas": [{"etiqueta": "DNI", "valor": "1"}, {"etiqueta": "Área", "valor": "2"}]})
        a._p_render_filas_editor()
        a._p_quitar_fila(0)
        assert [f["etiqueta"] for f in a.p_ajustes["filas"]] == ["Área"]
    finally:
        top.destroy()


def test_cambiar_modelo_conserva_campos_y_color():
    import estado
    top, a = _app()
    try:
        a.p_ajustes = estado.aplicar_cambios(
            estado.ajustes_inicial("clasica"),
            {"filas": [{"etiqueta": "Área", "valor": "X"}], "color": "#123456"})
        nombre = next(n for c, n in a._modelos if c == "gafete")
        a.p_modelo_var.set(nombre)
        a._p_cambiar_modelo()
        assert a.p_ajustes["modelo"] == "gafete"
        assert a.p_ajustes["color"] == "#123456"
        assert a.p_ajustes["filas"] == [{"etiqueta": "Área", "valor": "X"}]
    finally:
        top.destroy()


def _textos_de_botones(w):
    out = []
    for c in w.winfo_children():
        if isinstance(c, tk.Button):
            try:
                out.append(c.cget("text"))
            except Exception:
                pass
        out += _textos_de_botones(c)
    return out


def test_botones_clave_existen():
    top, a = _app()
    try:
        t = _textos_de_botones(top)
        assert "+ Agregar campo" in t
        assert "Exportar PDF" in t and "Exportar PNG" in t
    finally:
        top.destroy()
