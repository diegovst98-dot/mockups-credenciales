# -*- coding: utf-8 -*-
"""Modulo de foto carnet (1x1 / 3x4) para cuando el cliente aprueba y va a produccion.
Quita el fondo de la foto de la persona (rembg/U2Net, local y gratis), la pone sobre
fondo blanco y la encuadra al formato carnet pedido, a 300 dpi listo para CardPresso.

Es independiente del generador de mockups: se usa en otra etapa del flujo de venta.
Uso:  py foto1x1.py "ruta\\foto.jpg" [1x1|3x4]
"""
import os
import sys

from PIL import Image, ImageOps

# Formatos carnet a 300 dpi. (ancho_px, alto_px)
FORMATOS = {
    "1x1": (300, 300),      # 1 x 1 pulgada
    "3x4": (354, 472),      # 3 x 4 cm (foto carnet peruana estandar)
    "carnet": (354, 472),
}

_session = None


def _quitar_fondo(img):
    """Devuelve la persona en RGBA con fondo transparente (rembg/U2Net)."""
    global _session
    from rembg import remove, new_session
    if _session is None:
        _session = new_session("u2net")
    return remove(img, session=_session).convert("RGBA")


def _encuadrar_retrato(persona_rgba, ancho, alto):
    """Centra el recorte de la persona (segun su bbox alpha) en un lienzo blanco
    del formato pedido, con aire arriba/abajo proporcional a un retrato carnet."""
    bbox = persona_rgba.getchannel("A").getbbox()
    if bbox:
        persona_rgba = persona_rgba.crop(bbox)
    # margen: la persona ocupa ~82% del alto, centrada horizontal, anclada un poco arriba
    pw, ph = persona_rgba.size
    escala = (alto * 0.86) / ph
    nuevo = (max(1, int(pw * escala)), max(1, int(ph * escala)))
    persona_rgba = persona_rgba.resize(nuevo, Image.LANCZOS)
    if persona_rgba.width > ancho:  # si queda muy ancho, reescalar por ancho
        escala2 = (ancho * 0.92) / persona_rgba.width
        persona_rgba = persona_rgba.resize(
            (int(persona_rgba.width * escala2), int(persona_rgba.height * escala2)), Image.LANCZOS)
    lienzo = Image.new("RGB", (ancho, alto), (255, 255, 255))
    x = (ancho - persona_rgba.width) // 2
    y = int(alto * 0.08)  # aire arriba (cabeza no pegada al borde)
    lienzo.paste(persona_rgba, (x, y), persona_rgba)
    return lienzo


def generar_foto(ruta_foto, formato="3x4", carpeta_salida=None):
    """Crea la foto carnet con fondo blanco. Devuelve la ruta del PNG."""
    ancho, alto = FORMATOS.get(formato, FORMATOS["3x4"])
    img = Image.open(ruta_foto).convert("RGB")
    img = ImageOps.exif_transpose(img)
    persona = _quitar_fondo(img)
    carnet = _encuadrar_retrato(persona, ancho, alto)
    if carpeta_salida is None:
        carpeta_salida = os.path.dirname(os.path.abspath(ruta_foto))
    os.makedirs(carpeta_salida, exist_ok=True)
    base = os.path.splitext(os.path.basename(ruta_foto))[0]
    ruta = os.path.join(carpeta_salida, f"{base}-carnet-{formato}.png")
    carnet.save(ruta, dpi=(300, 300))
    return ruta


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Uso: py foto1x1.py "ruta\\foto.jpg" [1x1|3x4]')
        sys.exit(1)
    fmt = sys.argv[2] if len(sys.argv) > 2 else "3x4"
    print("Listo:", generar_foto(sys.argv[1], fmt))
