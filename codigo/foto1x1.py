# -*- coding: utf-8 -*-
"""Modulo de foto carnet (1x1 / 3x4) para cuando el cliente aprueba y va a produccion.
Quita el fondo de la foto de la persona, la pone sobre fondo blanco y la encuadra al
formato carnet pedido, a 300 dpi listo para CardPresso.

Es independiente del generador de mockups: se usa en otra etapa del flujo de venta y
NO viaja en el .exe del vendedor (usa rembg + numpy, que ya estan en la PC del disenador).

MOTOR (decision 2026-06-17, heredada del bake-off del fotochecks-editor v25->v31):
  - Modelo: isnet-general-use (no u2net: u2net es el mas viejo y deja 'casco/halo'
    blanco en el pelo sobre fondos de color). isnet recorta mechon a mechon, ~1.2s/foto,
    gratis (MIT/Apache 2.0) y offline. Fallback a u2net si isnet no esta disponible.
  - POST-PROCESO MINIMO, no cirugia: solo (a) antialias suave del borde (_alfa_minimo)
    y (b) descontaminacion del color del borde (_descontaminar). NO se hace erosion ni
    apertura de cerco: esa 'cirugia' fue justo lo que comia el pelo y causaba la
    oscilacion en el editor. La regla de oro: el matte del modelo ya es bueno, tocarlo
    lo menos posible.
  - GUARDIA DE FONDO LIMPIO: si la foto ya viene con fondo de estudio claro y uniforme,
    NO se recorta con IA (recortar lo limpio solo agrega riesgo de halo): se normaliza
    suave a blanco. Lo limpio no se sobre-edita.
  - Para una foto dificil puntual (pelo rizado, ropa clara contra pared clara), el escape
    es BiRefNet SOLO para esa (MOCKUPS_RECORTE=birefnet), nunca para el lote.

Uso:  py foto1x1.py "ruta\\foto.jpg" [1x1|3x4]
"""
import os
import sys

from PIL import Image, ImageFilter, ImageOps

# Formatos carnet a 300 dpi. (ancho_px, alto_px)
FORMATOS = {
    "1x1": (300, 300),      # 1 x 1 pulgada
    "3x4": (354, 472),      # 3 x 4 cm (foto carnet peruana estandar)
    "carnet": (354, 472),
}

_session = None
_modelo_activo = None


# ---------- motor de recorte ----------

def _nombre_modelo():
    """isnet por defecto; override con MOCKUPS_RECORTE=u2net|birefnet|..."""
    m = os.environ.get("MOCKUPS_RECORTE", "").strip().lower()
    if m == "birefnet":
        return "birefnet-portrait"     # escape para fotos dificiles (pesa ~900MB)
    if m in ("u2net", "u2netp", "u2net_human_seg", "isnet-general-use",
             "birefnet-general", "birefnet-general-lite", "birefnet-portrait"):
        return m
    return "isnet-general-use"


def _quitar_fondo(img):
    """Devuelve la persona en RGBA con fondo transparente (rembg, modelo isnet)."""
    global _session, _modelo_activo
    from rembg import remove, new_session
    if _session is None:
        try:
            _modelo_activo = _nombre_modelo()
            _session = new_session(_modelo_activo)
        except Exception:
            _modelo_activo = "u2net"            # fallback: el unico que casi siempre esta
            _session = new_session("u2net")
    return remove(img, session=_session).convert("RGBA")


# ---------- guardia de fondo limpio (no sobre-editar lo que ya esta bien) ----------

def _stats_borde(img):
    import numpy as np
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    h, w, _ = a.shape
    b = max(4, int(min(h, w) * 0.04))
    ring = np.concatenate([a[:b].reshape(-1, 3), a[-b:].reshape(-1, 3),
                           a[:, :b].reshape(-1, 3), a[:, -b:].reshape(-1, 3)])
    media = ring.mean(0)
    var = float(ring.std(0).max())
    lum = float((0.2126 * media[0] + 0.7152 * media[1] + 0.0722 * media[2]) / 255.0)
    return media, var, lum


def _fondo_uniforme_claro(img):
    """True si el fondo ya es de estudio: uniforme (poca varianza) y casi blanco."""
    _, var, lum = _stats_borde(img)
    return var < 12.0 and lum > 0.85


def _normalizar_blanco(img):
    """Fondo casi-blanco uniforme -> blanco puro, con umbral SUAVE. No recorta a la
    persona: solo empuja a blanco los pixeles claros parecidos al color de fondo."""
    import numpy as np
    media, _, _ = _stats_borde(img)
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    dif = np.abs(a - media).max(axis=2)           # distancia al color de fondo
    lum = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) / 255.0
    # peso 1 = es fondo (cerca del color y claro); 0 = es la persona
    peso = np.clip((18.0 - dif) / 12.0, 0.0, 1.0) * np.clip((lum - 0.80) / 0.10, 0.0, 1.0)
    out = a + (255.0 - a) * peso[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ---------- post-proceso MINIMO (sin cirugia) ----------

def _alfa_minimo(alpha, sigma=1.4):
    """Solo SUAVIZA el borde del matte (antialias), para quitar el dentado. NADA mas:
    sin erosion ni apertura (esas comian el pelo en el editor). Sirve igual para fondo
    blanco y de color."""
    return alpha.filter(ImageFilter.GaussianBlur(sigma))


def _descontaminar(rgb_img, alpha_img):
    """Limpia el COLOR del borde sin tocar la forma: el anillo semitransparente del
    contorno arrastra el color del fondo original (se ve como filo palido/halo al
    componer sobre blanco). Se reemplaza ese color por el del INTERIOR solido difundido
    hacia afuera. Es la version ligera (PIL+numpy) del _descontaminar del editor."""
    import numpy as np
    rgb = np.asarray(rgb_img.convert("RGB")).astype(np.float32)
    a = np.asarray(alpha_img)
    solido = a >= 217                              # interior ~85% opaco
    if not solido.any():
        return rgb_img.convert("RGB")
    h, w = a.shape
    sigma = max(2.0, min(h, w) * 0.012)

    def _gb(arr2d):
        im = Image.fromarray(np.clip(arr2d, 0, 255).astype(np.uint8), "L")
        return np.asarray(im.filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32)

    peso = solido.astype(np.float32)
    wb = _gb(peso * 255.0) / 255.0 + 1e-6          # cobertura difundida del interior
    difuso = np.zeros_like(rgb)
    for c in range(3):
        difuso[..., c] = _gb(rgb[..., c] * peso) / wb
    parcial = (a > 0) & (~solido)                  # anillo del borde
    out = rgb.copy()
    for c in range(3):
        ch = out[..., c]
        ch[parcial] = difuso[..., c][parcial]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def _persona_limpia(img):
    """Devuelve la persona en RGBA lista para componer: recorte + post-proceso minimo,
    o (si el fondo ya es limpio) normalizada a blanco sin recortar con IA."""
    if _fondo_uniforme_claro(img):
        base = _normalizar_blanco(img).convert("RGBA")   # nada de IA: lo limpio no se toca
        return base
    persona = _quitar_fondo(img)
    alpha = _alfa_minimo(persona.getchannel("A"))
    rgb = _descontaminar(persona.convert("RGB"), alpha)
    limpia = rgb.convert("RGBA")
    limpia.putalpha(alpha)
    return limpia


# ---------- encuadre carnet ----------

_cascade = None


def _detectar_rostro(rgb_img):
    """(fx,fy,fw,fh) del rostro mas grande, o None. Usa cv2 Haar si esta disponible."""
    global _cascade
    try:
        import cv2
        import numpy as np
    except Exception:
        return None
    if _cascade is None:
        _cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gris = cv2.cvtColor(np.asarray(rgb_img), cv2.COLOR_RGB2GRAY)
    caras = _cascade.detectMultiScale(gris, 1.1, 5, minSize=(80, 80))
    if len(caras) == 0:
        return None
    return max(caras, key=lambda f: f[2] * f[3])


def _caja_cabeza_hombros(rostro, alpha, ancho, alto, head_frac=0.58, headroom=0.09):
    """Caja (x,y,w,h) para un encuadre carnet head-and-shoulders: cabeza ~head_frac
    del alto, aire (headroom) arriba, corte al pecho. Relativa al rostro si lo hay."""
    aspect = ancho / float(alto)
    if rostro is not None:
        fx, fy, fw, fh = (float(v) for v in rostro)
        cx = fx + fw / 2.0
        crown_y = fy - 0.45 * fh             # corona, arriba de la frente
        head_h = 1.45 * fh                   # cabeza completa (corona a menton)
        crop_h = head_h / head_frac
        crop_w = crop_h * aspect
        top = crown_y - headroom * crop_h
        left = cx - crop_w / 2.0
        return int(round(left)), int(round(top)), int(round(crop_w)), int(round(crop_h))
    # sin rostro: aproximar por el bbox de la persona (ancla a la parte superior)
    bbox = alpha.getbbox()
    if not bbox:
        return 0, 0, alpha.width, alpha.height
    x0, y0, x1, y1 = bbox
    crop_w = (x1 - x0) * 1.7
    crop_h = crop_w / aspect
    cx = (x0 + x1) / 2.0
    return int(round(cx - crop_w / 2.0)), int(round(y0 - 0.06 * crop_h)), int(round(crop_w)), int(round(crop_h))


def _encuadrar_retrato(persona_rgba, ancho, alto):
    """Encuadra a la persona en formato CARNET head-and-shoulders sobre blanco:
    cabeza arriba (aire ~10%), corte al pecho. Usa deteccion de rostro para que el
    encuadre sea consistente sin importar cuanto zoom traiga la foto de origen.
    Ajustable con MOCKUPS_HEAD_FRAC (0.44 mas abierto, 0.50 mas cerrado)."""
    base = Image.new("RGB", persona_rgba.size, (255, 255, 255))
    base.paste(persona_rgba, (0, 0), persona_rgba)
    alpha = persona_rgba.getchannel("A")
    head_frac = float(os.environ.get("MOCKUPS_HEAD_FRAC", "0.58"))
    rostro = _detectar_rostro(base)
    x, y, w, h = _caja_cabeza_hombros(rostro, alpha, ancho, alto, head_frac=head_frac)
    w, h = max(1, w), max(1, h)
    lienzo = Image.new("RGB", (w, h), (255, 255, 255))
    sx0, sy0 = max(0, x), max(0, y)
    sx1, sy1 = min(base.width, x + w), min(base.height, y + h)
    if sx1 > sx0 and sy1 > sy0:
        lienzo.paste(base.crop((sx0, sy0, sx1, sy1)), (sx0 - x, sy0 - y))
    return lienzo.resize((ancho, alto), Image.LANCZOS)


def generar_foto(ruta_foto, formato="3x4", carpeta_salida=None):
    """Crea la foto carnet con fondo blanco. Devuelve la ruta del PNG."""
    ancho, alto = FORMATOS.get(formato, FORMATOS["3x4"])
    img = Image.open(ruta_foto).convert("RGB")
    img = ImageOps.exif_transpose(img)
    persona = _persona_limpia(img)
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
