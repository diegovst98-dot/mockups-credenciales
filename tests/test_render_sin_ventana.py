# -*- coding: utf-8 -*-
"""Anti-parpadeo: al generar el catálogo, NINGUNA invocación de Edge debe mostrar
ventana. Todas las llamadas subprocess de render.py deben llevar
creationflags=CREATE_NO_WINDOW + startupinfo (SW_HIDE) + stdin redirigido
(técnica documentada en el cerebro: redirigir stdin es clave en apps --noconsole)."""
import ast
import os
import subprocess
import sys

CODIGO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "codigo")
sys.path.insert(0, CODIGO)


def _llamadas_subprocess():
    with open(os.path.join(CODIGO, "render.py"), encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr in ("run", "Popen", "call", "check_output", "check_call")
                and isinstance(nodo.func.value, ast.Name)
                and nodo.func.value.id == "subprocess"):
            yield nodo


def test_toda_llamada_edge_va_oculta():
    llamadas = list(_llamadas_subprocess())
    assert llamadas, "render.py ya no usa subprocess? revisar el test"
    for c in llamadas:
        kw = {k.arg for k in c.keywords}
        assert "creationflags" in kw, "llamada subprocess (línea %d) sin creationflags=CREATE_NO_WINDOW" % c.lineno
        assert "startupinfo" in kw, "llamada subprocess (línea %d) sin startupinfo (SW_HIDE)" % c.lineno
        assert "stdin" in kw or "capture_output" in kw or any(
            k.arg == "stdin" for k in c.keywords), \
            "llamada subprocess (línea %d) sin stdin redirigido" % c.lineno
        assert any(k.arg == "stdin" for k in c.keywords), \
            "llamada subprocess (línea %d) sin stdin=DEVNULL" % c.lineno


def test_startupinfo_oculto():
    import render
    si = render._startupinfo_oculto()
    if not hasattr(subprocess, "STARTUPINFO"):
        assert si is None
        return
    assert si.dwFlags & subprocess.STARTF_USESHOWWINDOW
    assert si.wShowWindow == subprocess.SW_HIDE
