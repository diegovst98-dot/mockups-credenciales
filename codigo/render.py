# -*- coding: utf-8 -*-
"""Rasteriza caras HTML a PIL.Image. DOS motores, se elige solo:

  1) Edge/Chrome del sistema por linea de comando (--screenshot) — el camino del
     VENDEDOR: Windows 11 SIEMPRE trae Edge, asi que el .exe NO necesita empaquetar
     ningun navegador ni Playwright. Cero descargas, el auto-update basta.
  2) Playwright (si esta instalado) — comodo en la PC de desarrollo.

Forzar uno: variable de entorno MOCKUPS_RENDER = "edge" | "playwright".
"""
import io
import os
import shutil
import subprocess
import tempfile

from PIL import Image


# ---------- motor 1: Edge/Chrome del sistema (sin dependencias) ----------

def _navegador_sistema():
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(p):
            return p
    return None


def _render_edge(items, escala, exe):
    imgs = []
    base = tempfile.mkdtemp(prefix="mockups_render_")
    try:
        for i, (html, w, h) in enumerate(items):
            hpath = os.path.join(base, "c%d.html" % i)
            opath = os.path.join(base, "c%d.png" % i)
            perfil = os.path.join(base, "perfil%d" % i)
            with open(hpath, "w", encoding="utf-8") as f:
                f.write(html)
            subprocess.run(
                [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                 "--no-sandbox", "--no-first-run", "--disable-extensions",
                 "--force-device-scale-factor=%d" % escala,
                 "--force-color-profile=srgb",
                 "--user-data-dir=" + perfil,
                 "--screenshot=" + opath,
                 "--window-size=%d,%d" % (w, h),
                 "file:///" + hpath.replace("\\", "/")],
                check=True, timeout=60,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(opath, "rb") as f:
                imgs.append(Image.open(io.BytesIO(f.read())).convert("RGBA"))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return imgs


# ---------- motor 2: Playwright (desarrollo) ----------

def _render_playwright(items, escala):
    from playwright.sync_api import sync_playwright
    imgs = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--force-color-profile=srgb"])
        try:
            for html, w, h in items:
                pg = b.new_page(device_scale_factor=escala, viewport={"width": w, "height": h})
                pg.set_content(html, wait_until="load")
                try:
                    pg.evaluate("document.fonts.ready")
                except Exception:
                    pass
                pg.wait_for_timeout(120)
                el = pg.query_selector(".card") or pg
                imgs.append(Image.open(io.BytesIO(el.screenshot())).convert("RGBA"))
                pg.close()
        finally:
            b.close()
    return imgs


# ---------- selección de motor ----------

def _playwright_disponible():
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        return False


def render_caras(items, escala=2):
    """items: list[(html, ancho, alto)]. Devuelve list[PIL.Image] (RGBA), full-bleed.
    Las plantillas hacen que el body sea exactamente la tarjeta, asi el screenshot
    del viewport (Edge) coincide con la cara."""
    modo = os.environ.get("MOCKUPS_RENDER", "").lower()
    exe = _navegador_sistema()
    if modo == "playwright" and _playwright_disponible():
        return _render_playwright(items, escala)
    if modo == "edge" and exe:
        return _render_edge(items, escala, exe)
    # auto: navegador del sistema primero (camino del vendedor); si no, Playwright
    if exe:
        return _render_edge(items, escala, exe)
    if _playwright_disponible():
        return _render_playwright(items, escala)
    raise RuntimeError("No hay navegador para renderizar (instala Edge/Chrome o Playwright).")
