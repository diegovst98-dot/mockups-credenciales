# -*- mode: python ; coding: utf-8 -*-

# pypdfium2 (lo usa codigo/renombrador.py) no trae hook de PyInstaller, así que su
# binario pdfium.dll + datos + módulos se recolectan a mano. Sin esto, la pestaña
# "Renombrar Cotizaciones" crashea en runtime por falta de pdfium.dll.
from PyInstaller.utils.hooks import collect_all

_pdf_datas, _pdf_bins, _pdf_hidden = [], [], []
for _pkg in ('pypdfium2', 'pypdfium2_raw'):
    _d, _b, _h = collect_all(_pkg)
    _pdf_datas += _d
    _pdf_bins += _b
    _pdf_hidden += _h


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=_pdf_bins,
    datas=[('recursos', 'recursos')] + _pdf_datas,
    hiddenimports=_pdf_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MockupsDISECOD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['recursos\\icono.ico'],
)
