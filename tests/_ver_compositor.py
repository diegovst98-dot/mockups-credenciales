# -*- coding: utf-8 -*-
"""Arnés de render-and-look: arma un caso real con el compositor y guarda un PNG para MIRAR."""
import os
import sys

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo"))
RECURSOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recursos"))
sys.path.insert(0, CODIGO)

from PIL import Image
import lienzo
import estado

# Logo real de DISECOD (tinta real, NO se recolorea) + foto placeholder.
logo_ruta = os.path.join(RECURSOS, "logo-disecod-oscuro.png")
logo = Image.open(logo_ruta).convert("RGBA") if os.path.exists(logo_ruta) else Image.new("RGBA", (400, 200), (20, 110, 80, 255))
foto = Image.new("RGBA", (300, 380), (200, 200, 205, 255))

a = estado.ajustes_inicial("clasica")
recursos = {
    "logo": {"tipo": "imagen", "img": logo},
    "foto": {"tipo": "imagen", "img": foto},
    "nombre": {"tipo": "texto", "texto": "Nombre Apellido", "peso": 800, "color": (30, 30, 30)},
    "cargo": {"tipo": "texto", "texto": "Cargo del colaborador", "peso": 600, "color": (90, 90, 90)},
    "datos": {"tipo": "datos", "filas": [("Código", "A-102"), ("Área", "Operaciones")],
              "color_etq": (20, 110, 80), "color_val": (40, 40, 40)},
}
fondo = Image.new("RGBA", (1011, 638), (245, 246, 248, 255))
out = lienzo.componer(fondo, a["capas"], recursos, 1011, 638)
ruta = os.path.join(os.path.dirname(__file__), "_ver_compositor.png")
out.convert("RGB").save(ruta)
print(ruta)
