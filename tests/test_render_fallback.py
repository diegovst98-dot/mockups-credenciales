# -*- coding: utf-8 -*-
"""Cascada de modos headless de render.py. Bug de producción (vendedor, v27): Edge
devolvía rc=0 SIN escribir el PNG porque su versión trata `--headless=new --screenshot`
como no-op; se prueban `--headless=old`/`--headless` como respaldo."""
import os
import shutil
import sys
import tempfile

import pytest

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
sys.path.insert(0, CODIGO)

import render


def test_edge_screenshot_cae_al_modo_que_escribe(monkeypatch):
    """Si --headless=new no escribe, debe caer a --headless=old y PARAR ahí."""
    llamados = []

    def fake(exe, modo, hpath, opath, perfil, w, h, escala):
        llamados.append(modo)
        return (modo == "--headless=old", "no escribió")

    monkeypatch.setattr(render, "_intento_captura", fake)
    render._edge_screenshot("edge.exe", "h.html", "o.png", "perfil", 100, 100, 2,
                            modos=("--headless=new", "--headless=old", "--headless"))
    assert llamados == ["--headless=new", "--headless=old"]


def test_edge_screenshot_error_claro_con_version(monkeypatch):
    """Si NINGÚN modo escribe, el error trae la versión de Edge y cada modo probado."""
    monkeypatch.setattr(render, "_intento_captura", lambda *a, **k: (False, "rc=0 "))
    monkeypatch.setattr(render, "_edge_version", lambda exe: "Edge 110.0.1")
    with pytest.raises(RuntimeError) as e:
        render._edge_screenshot("edge.exe", "h", "o", "p", 10, 10, 2,
                                modos=("--headless=new", "--headless=old"))
    msg = str(e.value)
    assert "Edge 110.0.1" in msg
    assert "--headless=new" in msg and "--headless=old" in msg


@pytest.mark.skipif(render._navegador_sistema() is None, reason="sin Edge/Chrome")
def test_headless_old_escribe_en_esta_maquina():
    """El modo de respaldo (--headless=old) produce el PNG en esta máquina."""
    exe = render._navegador_sistema()
    base = tempfile.mkdtemp(prefix="t_render_")
    try:
        hp = os.path.join(base, "t.html")
        with open(hp, "w", encoding="utf-8") as f:
            f.write("<html><body style='margin:0'>"
                    "<div style='width:80px;height:60px;background:#1d9e75'></div></body></html>")
        op = os.path.join(base, "o.png")
        ok, det = render._intento_captura(exe, "--headless=old", hp, op,
                                          os.path.join(base, "p"), 80, 60, 2)
        assert ok, det
    finally:
        shutil.rmtree(base, ignore_errors=True)
