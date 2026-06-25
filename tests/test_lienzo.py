# -*- coding: utf-8 -*-
"""Compositor de capas: matemática de cajas, snap, y composición determinista (puro)."""
import os
import sys

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
sys.path.insert(0, CODIGO)

from PIL import Image
import lienzo


# ---- Task 3: cajas y snap ----

def test_caja_px_convierte_normalizado_a_pixel():
    assert lienzo.caja_px({"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}, 1000, 600) == (0, 0, 500, 300)
    assert lienzo.caja_px({"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5}, 1000, 600) == (500, 300, 1000, 600)


def test_snap_pega_a_guia_cercana():
    assert lienzo.snap(0.49) == 0.5
    assert lienzo.snap(0.012) == 0.0
    assert lienzo.snap(0.30) == 0.30


# ---- Task 4: compositor ----

def test_componer_devuelve_tamano_pedido():
    fondo = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    out = lienzo.componer(fondo, {}, {}, 1011, 638)
    assert out.size == (1011, 638)


def test_capa_imagen_centrada_cae_al_centro():
    fondo = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    rojo = Image.new("RGBA", (50, 50), (255, 0, 0, 255))
    capas = {"logo": {"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2}}
    recursos = {"logo": {"tipo": "imagen", "img": rojo}}
    out = lienzo.componer(fondo, capas, recursos, 100, 100)
    assert out.getpixel((50, 50))[:3] == (255, 0, 0)        # rojo en el centro
    assert out.getpixel((5, 5))[:3] == (255, 255, 255)      # esquina sigue blanca


def test_encajar_mantiene_proporcion():
    img = Image.new("RGBA", (200, 100), (0, 0, 0, 255))     # 2:1
    out = lienzo.encajar_en(img, 50, 50)
    assert out.size == (50, 25)                              # cabe sin deformar
