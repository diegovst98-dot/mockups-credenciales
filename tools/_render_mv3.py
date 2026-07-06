# -*- coding: utf-8 -*-
"""Herramienta de sesión: renderiza mv3 con 3 logos a salida/_loop/<tag>/."""
import os
import sys

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AQUI, "codigo"))
import motor  # noqa: E402

LOGOS = [
    (r"C:\Users\Diego\CLAUDE CODE+\03 - Marca y logos\logo-disecod-header-transparent.png", "DISECOD"),
    (os.path.join(AQUI, "entrada", "logo-prueba-frutos.png"), "Frutos del Norte"),
    (os.path.join(AQUI, "entrada", "logo-prueba-negro.png"), "Constructora Lima"),
]


def main():
    tag = sys.argv[1]
    out = os.path.join(AQUI, "salida", "_loop", tag)
    os.makedirs(out, exist_ok=True)
    for ruta, nombre in LOGOS:
        logo = motor.cargar_logo(ruta)
        img = motor.render_modelo(logo, nombre, {"modelo": "mv3"})
        p = os.path.join(out, "mv3-%s.png" % nombre.split()[0].lower())
        img.convert("RGB").save(p)
        print(p)


if __name__ == "__main__":
    main()
