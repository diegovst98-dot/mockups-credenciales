# -*- coding: utf-8 -*-
"""Herramienta del loop de calidad: renderiza todos los estilos con un set de
logos reales en una sola corrida. Uso:
    py render_pruebas.py <tag> [logo1 logo2 ...]
Sin logos explícitos usa el set estándar. Salida: salida\\_loop\\<tag>\\<logo>\\
"""
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "codigo"))
import motor  # noqa: E402

LOGOS = {
    "unilever": (r"C:\Users\Diego\Downloads\UNILEVER.jpg", "Unilever Andina"),
    "anay": (r"C:\Users\Diego\Downloads\AÑAY FRUITS.jpg", "Añay Fruits"),
    "gv": (r"C:\Users\Diego\Downloads\LOGO GV (1).png", "Gestión Vertical"),
    "interbank": (r"C:\Users\Diego\Downloads\Interbank_logo.svg.png", "Interbank"),
    "frutosnorte": (r"C:\Users\Diego\Downloads\logo frutos del norte.jpeg", "Frutos del Norte"),
    "negro": (os.path.join(AQUI, "entrada", "logo-prueba-negro.png"), "Constructora Lima"),
    "blanco": (os.path.join(AQUI, "entrada", "logo-prueba-blanco.png"), "Clínica San Borja"),
    "acme": (os.path.join(AQUI, "entrada", "logo-prueba-acme.png"), "ACME Corp"),
    # caso extremo: razón social larga (prueba de overflow de campos)
    "largo": (os.path.join(AQUI, "entrada", "logo-prueba-frutos.png"),
              "Corporación Andina de Seguridad Integral"),
}
SET_ESTANDAR = ["unilever", "anay", "gv", "interbank"]


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else time.strftime("%H%M")
    claves = sys.argv[2:] or SET_ESTANDAR
    base = os.path.join(AQUI, "salida", "_loop", tag)
    for clave in claves:
        ruta, nombre = LOGOS[clave]
        if not os.path.exists(ruta):
            print(f"[SKIP] {clave}: no existe {ruta}")
            continue
        t0 = time.time()
        carpeta = os.path.join(base, clave)
        motor.generar(ruta, nombre, carpeta_salida=carpeta)
        print(f"[OK] {clave} ({nombre}) -> {carpeta}  {time.time() - t0:.1f}s")
    print("BASE:", base)


if __name__ == "__main__":
    main()
