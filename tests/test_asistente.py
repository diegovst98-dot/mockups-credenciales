# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))


class _ModeloFake:
    def __init__(self, clave="x", nombre="X", campos_opcionales=(), logo_posiciones=()):
        self.clave = clave
        self.nombre = nombre
        self.campos_opcionales = campos_opcionales
        self.logo_posiciones = logo_posiciones


def _aj(modelo="clasica", color=None):
    from estado import ajustes_inicial
    a = ajustes_inicial(modelo)
    a["color"] = color
    return a


def test_color_nombrado():
    from asistente import interpretar
    cambios, msg = interpretar("ponle color azul", _aj(), _ModeloFake())
    assert cambios == {"color": "#1f4ed8"}
    assert "azul" in msg.lower()


def test_color_hex_directo():
    from asistente import interpretar
    cambios, _ = interpretar("usa el color #0a66c2", _aj(), _ModeloFake())
    assert cambios == {"color": "#0a66c2"}


def test_mas_oscuro_requiere_color_base():
    from asistente import interpretar
    cambios, msg = interpretar("hazlo más oscuro", _aj(color=None), _ModeloFake())
    assert cambios == {}
    assert "color" in msg.lower()


def test_mas_oscuro_con_base():
    from asistente import interpretar
    cambios, _ = interpretar("más oscuro", _aj(color="#3366cc"), _ModeloFake())
    assert cambios["color"].startswith("#") and cambios["color"] != "#3366cc"


def test_campo_soportado_se_prende():
    from asistente import interpretar
    m = _ModeloFake(campos_opcionales=("tipo_sangre",))
    cambios, msg = interpretar("agrégale el tipo de sangre", _aj(), m)
    assert cambios == {"campos": {"tipo_sangre": True}}


def test_campo_soportado_se_quita():
    from asistente import interpretar
    m = _ModeloFake(campos_opcionales=("tipo_sangre",))
    cambios, _ = interpretar("quita el tipo de sangre", _aj(), m)
    assert cambios == {"campos": {"tipo_sangre": False}}


def test_campo_no_soportado_sugiere_modelo_real():
    from asistente import interpretar
    import plantillas  # noqa: F401  (puebla el registro)
    m = _ModeloFake(clave="premium", nombre="Premium", campos_opcionales=())
    cambios, msg = interpretar("ponle tipo de sangre", _aj("premium"), m)
    assert cambios == {}
    assert "modelo" in msg.lower()        # sugiere cambiar de modelo (o avisa que no hay)


def test_logo_a_la_derecha_soportado():
    from asistente import interpretar
    m = _ModeloFake(logo_posiciones=("default", "der"))
    cambios, _ = interpretar("el logo ponlo a la derecha", _aj(), m)
    assert cambios == {"logo_pos": "der"}


def test_logo_pos_no_soportada_no_falla():
    from asistente import interpretar
    m = _ModeloFake(logo_posiciones=("default",))
    cambios, msg = interpretar("logo a la izquierda", _aj(), m)
    assert cambios == {}
    assert msg                            # da un mensaje, no revienta


def test_cambiar_modelo_por_nombre():
    from asistente import interpretar
    import plantillas  # noqa: F401
    m = _ModeloFake(clave="premium", nombre="Premium")
    cambios, _ = interpretar("usa el modelo clasica", _aj("premium"), m)
    assert cambios == {"modelo": "clasica"}


def test_no_entiende_da_ayuda():
    from asistente import interpretar
    cambios, msg = interpretar("xyzzy qwerty", _aj(), _ModeloFake())
    assert cambios == {}
    assert "controles" in msg.lower() or "prueba" in msg.lower()


def test_texto_override_cargo():
    from asistente import interpretar
    cambios, _ = interpretar("cambia el cargo a Gerente de Ventas", _aj(), _ModeloFake())
    assert cambios == {"textos": {"cargo": "Gerente De Ventas"}}
