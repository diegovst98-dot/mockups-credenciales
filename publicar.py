# -*- coding: utf-8 -*-
"""
Publica una actualizacion del codigo de Mockups DISECOD.

Que hace: sube version.txt en 1, regenera manifest.json, hace commit y push a
GitHub. Con eso, TODAS las copias instaladas (la del vendedor incluida) se
actualizan solas la proxima vez que abran el programa. El exe no se reenvía:
solo cambia si algun dia cambiamos de librerias.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CODIGO = BASE / "codigo"
ARCHIVOS = ["app.py", "motor.py", "version.txt"]


def main():
    v_txt = CODIGO / "version.txt"
    m = re.search(r"\d+", v_txt.read_text(encoding="utf-8"))
    version = (int(m.group()) if m else 0) + 1
    v_txt.write_text(str(version), encoding="utf-8")

    (BASE / "manifest.json").write_text(
        json.dumps({"version": version, "archivos": ARCHIVOS}, indent=2) + "\n",
        encoding="utf-8")

    # validar que el codigo compile antes de publicarlo
    for nombre in ARCHIVOS:
        if nombre.endswith(".py"):
            compile((CODIGO / nombre).read_text(encoding="utf-8"), nombre, "exec")

    mensaje = sys.argv[1] if len(sys.argv) > 1 else f"Actualizacion v{version}"
    subprocess.run(["git", "add", "-A"], cwd=BASE, check=True)
    subprocess.run(["git", "commit", "-m", f"{mensaje} (v{version})"], cwd=BASE, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=BASE, check=True)
    print(f"\nPublicado: version {version}. Las copias instaladas se actualizan solas al abrir.")


if __name__ == "__main__":
    main()
