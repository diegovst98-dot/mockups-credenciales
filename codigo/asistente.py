# -*- coding: utf-8 -*-
"""Parser local de intención para la pestaña Personalizar (v2). Convierte lo que
escribe el vendedor en 'cambios' para el dict Ajustes. 100% offline, determinista,
gratis. La firma queda lista para, a futuro, delegar el parseo a un LLM detrás de la
misma interfaz, sin tocar el resto del sistema.

interpretar(texto, ajustes, modelo) -> (cambios, mensaje)
  cambios: dict para fusionar en Ajustes (vacío si no aplica nada)
  mensaje: respuesta en español para mostrar en el chat
"""
import re
import unicodedata

# colores nombrados frecuentes -> hex
_COLORES = {
    "azul": "#1f4ed8", "celeste": "#2563eb", "rojo": "#c81e1e", "verde": "#1f7a3d",
    "negro": "#222222", "dorado": "#c9a14a", "naranja": "#d2691e", "morado": "#6b46c1",
    "lila": "#9987f7", "gris": "#4b5563", "rosado": "#db2777", "rosa": "#db2777",
    "amarillo": "#d4a017", "turquesa": "#0d9488", "guinda": "#7a1f3d", "vino": "#7a1f3d",
}

# campo -> frases que lo activan (se buscan dentro del texto normalizado con espacios)
_CAMPOS_SINONIMOS = {
    "tipo_sangre": ("tipo de sangre", "grupo sanguineo", "factor rh"),
    "codigo": ("codigo de empleado", "codigo", "n de empleado", "numero de empleado"),
    "web": ("pagina web", "sitio web", "la web", "url", "dominio"),
}
_CAMPO_LABEL = {"tipo_sangre": "el tipo de sangre", "codigo": "el código", "web": "la web"}

_QUITAR = ("quita", "quitar", "saca", "sacar", " sin ", "elimina", "borra", "no pongas", "remueve")

_POS_SINONIMOS = {
    "der": ("a la derecha", "derecha"),
    "izq": ("a la izquierda", "izquierda"),
    "centro": ("al centro", "centrado", "al medio", "en el centro"),
}
_POS_LABEL = {"der": "a la derecha", "izq": "a la izquierda", "centro": "al centro",
              "default": "a su sitio"}

# textos editables: campo de Ajustes/DATOS -> sinónimos en el habla
_TEXTO_CAMPOS = (
    ("nombre", ("nombre",)),
    ("cargo", ("cargo", "puesto")),
    ("id", ("dni", "documento")),
    ("empresa", ("empresa", "razon social")),
)
_TEXTO_LABEL = {"nombre": "el nombre", "cargo": "el cargo", "id": "el DNI", "empresa": "la empresa"}


def _norm(texto):
    """minúsculas, sin acentos, con un espacio de borde para matchear palabras."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return " " + re.sub(r"\s+", " ", t).strip() + " "


def _ajustar_hex(hexv, factor):
    c = hexv.lstrip("#")
    rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    if factor <= 1:
        rgb = [int(x * factor) for x in rgb]
    else:
        rgb = [int(x + (255 - x) * (factor - 1)) for x in rgb]
    return "#%02x%02x%02x" % tuple(max(0, min(255, x)) for x in rgb)


def _texto_override(t):
    """Captura '<campo> ... <conector> <valor>'. Best-effort; los controles son el respaldo."""
    for campo, syns in _TEXTO_CAMPOS:
        for s in syns:
            m = re.search(r"\b%s\b.*?(?:que diga|sea|es|a|:|=)\s+(.+)$" % re.escape(s), t)
            if m:
                valor = m.group(1).strip().strip(".").strip()
                if valor and len(valor) <= 60:
                    return campo, valor.title()
    return None


def interpretar(texto, ajustes, modelo):
    from plantillas.registro import modelos_con_campo, modelos_con_logo_pos
    t = _norm(texto)
    quitar = any(k in t for k in _QUITAR)
    pos_pedida = next((p for p, syns in _POS_SINONIMOS.items() if any(s in t for s in syns)), None)

    # 1) POSICIÓN DEL LOGO ("el logo a la derecha", "ponlo a la derecha")
    if pos_pedida and ("logo" in t or "ponlo" in t or "muev" in t or " pon " in t):
        if pos_pedida in getattr(modelo, "logo_posiciones", ()):
            return {"logo_pos": pos_pedida}, "Listo, moví el logo %s." % _POS_LABEL[pos_pedida]
        otros = [m for m in modelos_con_logo_pos(pos_pedida) if m.clave != modelo.clave]
        if otros:
            return {}, ("Este modelo no permite mover el logo ahí. El modelo «%s» sí — "
                        "escribe «usa el modelo %s»." % (otros[0].nombre, otros[0].clave))
        return {}, "Este modelo mantiene el logo en su sitio. Puedes probar otro modelo."

    # 2) CAMPO opcional (tipo de sangre / código / web)
    for campo, syns in _CAMPOS_SINONIMOS.items():
        if any(s in t for s in syns):
            encender = not quitar
            if campo in getattr(modelo, "campos_opcionales", ()):
                verbo = "agregué" if encender else "quité"
                return {"campos": {campo: encender}}, "Listo, %s %s." % (verbo, _CAMPO_LABEL[campo])
            if encender:
                otros = [m for m in modelos_con_campo(campo) if m.clave != modelo.clave]
                if otros:
                    return {}, ("Este modelo no tiene espacio para %s. El modelo «%s» sí — "
                                "escribe «usa el modelo %s» para cambiarlo."
                                % (_CAMPO_LABEL[campo], otros[0].nombre, otros[0].clave))
                return {}, "Ningún modelo del catálogo muestra %s en el frente." % _CAMPO_LABEL[campo]
            return {}, "Ese dato no está en este modelo; no hay nada que quitar."

    # 3) COLOR (nombrado, hex, más oscuro/claro)
    m = re.search(r"#([0-9a-f]{6})", t)
    if m:
        return {"color": "#" + m.group(1)}, "Listo, apliqué el color #%s." % m.group(1)
    for nombre, hexv in _COLORES.items():
        if (" " + nombre + " ") in t:
            return {"color": hexv}, "Listo, cambié el color a %s." % nombre
    if "mas oscuro" in t or "oscurece" in t or "mas fuerte" in t:
        base = ajustes.get("color")
        if not base:
            return {}, "Primero dime un color (ej. «azul») y luego lo oscurezco."
        return {"color": _ajustar_hex(base, 0.8)}, "Listo, lo oscurecí un poco."
    if "mas claro" in t or "aclara" in t or "mas suave" in t:
        base = ajustes.get("color")
        if not base:
            return {}, "Primero dime un color (ej. «azul») y luego lo aclaro."
        return {"color": _ajustar_hex(base, 1.25)}, "Listo, lo aclaré un poco."

    # 4) CAMBIAR DE MODELO (por clave o por nombre)
    if "modelo" in t or "diseno" in t or "otro" in t:
        from plantillas import catalogo
        for mdl in catalogo():
            if (" " + mdl.clave + " ") in t or _norm(mdl.nombre).strip() in t:
                return {"modelo": mdl.clave}, "Listo, cambié al modelo «%s»." % mdl.nombre
        if "otro" in t or "modelo" in t:
            return {}, ("Dime cuál: por ejemplo «usa el modelo clasica». "
                        "También puedes elegirlo en el selector de arriba.")

    # 5) TEXTO override (nombre/cargo/DNI/empresa)
    cambio_txt = _texto_override(t)
    if cambio_txt:
        campo_txt, valor = cambio_txt
        return {"textos": {campo_txt: valor}}, "Listo, actualicé %s." % _TEXTO_LABEL[campo_txt]

    # 6) NADA
    return {}, ("No te entendí 🤔. Prueba con: «ponle tipo de sangre», «el logo a la derecha», "
                "«color azul», «cambia el cargo a Gerente» — o usa los controles de la derecha.")
