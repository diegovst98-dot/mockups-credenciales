# -*- coding: utf-8 -*-
"""
Lanzador delgado de Mockups DISECOD.

Misma receta que el fotochecks-editor: el exe (Python + Pillow + tkinter, ~30 MB)
casi nunca cambia; el codigo del programa (codigo/app.py y codigo/motor.py, pocos KB)
cambia seguido mientras pulimos plantillas. Por eso el codigo NO va horneado dentro
del exe: vive en la carpeta codigo/ al lado, y al abrir el programa se revisa GitHub
y se actualiza solo antes de arrancar. Publicar una mejora = publicar.bat.
"""

import os
import sys
import importlib
from pathlib import Path


def base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE = base_dir()
CODIGO = BASE / "codigo"

USUARIO_REPO = "diegovst98-dot"
NOMBRE_REPO = "mockups-credenciales"
RAMA = "main"
_RAW = "https://raw.githubusercontent.com/%s/%s/%s" % (USUARIO_REPO, NOMBRE_REPO, RAMA)
URL_MANIFEST = _RAW + "/manifest.json"
URL_CODIGO = _RAW + "/codigo"


def _log(msg):
    try:
        with open(BASE / "actualizacion.log", "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass


def _solo_entero(texto):
    import re
    m = re.search(r"\d+", str(texto))
    return int(m.group()) if m else 0


def _version_local():
    try:
        return _solo_entero((CODIGO / "version.txt").read_text(encoding="utf-8"))
    except Exception:
        return 0


def _contexto_ssl():
    # El codigo descargado se EJECUTA: verificacion de certificados obligatoria.
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def buscar_actualizacion():
    # True si actualizo. Cualquier error (sin internet, descarga a medias) => no
    # toca nada y arranca con lo que ya hay instalado.
    import json
    import shutil
    import tempfile
    import urllib.request

    ctx = _contexto_ssl()
    try:
        with urllib.request.urlopen(URL_MANIFEST, timeout=6, context=ctx) as r:
            manifest = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        _log("fallo al leer manifest: %r" % (e,))
        return False

    remota = _solo_entero(manifest.get("version", 0))
    archivos = manifest.get("archivos", [])
    _log("version local=%s remota=%s" % (_version_local(), remota))
    if remota <= _version_local() or not archivos:
        return False

    # Descarga atomica: todo a temporal, validar, recien reemplazar.
    tmp = Path(tempfile.mkdtemp(prefix="mockups_upd_"))
    try:
        for nombre in archivos:
            with urllib.request.urlopen(URL_CODIGO + "/" + nombre, timeout=20, context=ctx) as r:
                data = r.read()
            if not data:
                return False
            if nombre.endswith(".py"):
                compile(data.decode("utf-8"), nombre, "exec")
            destino_tmp = tmp / nombre
            destino_tmp.parent.mkdir(parents=True, exist_ok=True)  # subcarpetas (fuentes/)
            destino_tmp.write_bytes(data)
        CODIGO.mkdir(parents=True, exist_ok=True)
        for nombre in archivos:
            destino = CODIGO / nombre
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(tmp / nombre, destino)
        _log("actualizado a version %s OK" % (remota,))
        return True
    except Exception as e:
        _log("fallo al descargar/instalar: %r" % (e,))
        return False
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)


# --- Forzar que PyInstaller meta las librerias al exe (el codigo que las usa vive afuera) ---
import PIL.Image          # noqa: F401
import PIL.ImageDraw      # noqa: F401
import PIL.ImageFilter    # noqa: F401
import PIL.ImageFont      # noqa: F401
import PIL.ImageOps       # noqa: F401
import certifi            # noqa: F401
import pypdfium2          # noqa: F401  (lo usa codigo/renombrador.py para leer PDFs)
import tkinter            # noqa: F401
import tkinter.filedialog  # noqa: F401
import tkinter.font       # noqa: F401
import tkinter.messagebox  # noqa: F401


def main():
    try:
        (BASE / "actualizacion.log").write_text("", encoding="utf-8")
    except Exception:
        pass
    _log("arranque - version instalada: %s" % (_version_local(),))
    try:
        buscar_actualizacion()
    except Exception as e:
        import traceback
        _log("EXCEPCION: %r\n%s" % (e, traceback.format_exc()))

    sys.path.insert(0, str(CODIGO))
    try:
        app = importlib.import_module("app")
    except Exception as e:
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk(); r.withdraw()
            messagebox.showerror(
                "Mockups DISECOD",
                "No se pudo cargar el programa desde la carpeta 'codigo'.\n\nDetalle: " + str(e))
            r.destroy()
        except Exception:
            print("ERROR cargando codigo/app.py:", e)
        return
    app.main()


if __name__ == "__main__":
    main()
