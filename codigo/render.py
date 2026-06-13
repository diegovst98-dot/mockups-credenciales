# -*- coding: utf-8 -*-
"""Rasteriza caras HTML a PIL.Image con Playwright (Chromium headless).
Reusa un solo navegador para todas las caras de una corrida (rapido).
Es el UNICO modulo que toca Playwright; el resto del motor no sabe de navegadores."""
import io

from PIL import Image
from playwright.sync_api import sync_playwright


def render_caras(items, escala=2):
    """items: list[(html, ancho, alto)]. Devuelve list[PIL.Image] (RGBA).
    Toma screenshot del elemento .card (full-bleed, sin sombras ni rotulos).
    escala = device_scale_factor: 2 => el doble de px (texto nitido, ~600 dpi)."""
    imgs = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--force-color-profile=srgb"])
        try:
            for html, ancho, alto in items:
                pg = b.new_page(device_scale_factor=escala,
                                viewport={"width": ancho, "height": alto})
                pg.set_content(html, wait_until="load")
                try:
                    pg.evaluate("document.fonts.ready")
                except Exception:
                    pass
                pg.wait_for_timeout(120)
                el = pg.query_selector(".card") or pg
                data = el.screenshot()
                pg.close()
                imgs.append(Image.open(io.BytesIO(data)).convert("RGBA"))
        finally:
            b.close()
    return imgs
