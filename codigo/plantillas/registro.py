# -*- coding: utf-8 -*-
"""Registro central de modelos de credencial. Cada módulo de plantillas.modelos
llama a registrar() al importarse; motor.py consume catalogo() para iterar el folleto.
v2: cada modelo declara qué campos opcionales y qué posiciones de logo soporta, para
que el editor ofrezca solo lo posible y el asistente sugiera otro modelo cuando no."""


class Modelo:
    def __init__(self, clave, nombre, orientacion, frontal, reverso=None, campos=(),
                 campos_opcionales=(), logo_posiciones=()):
        self.clave = clave
        self.nombre = nombre
        self.orientacion = orientacion      # 'V' (638x1011) o 'H' (1011x638)
        self.frontal = frontal              # fn(lado, ctx, d) -> (html, ancho, alto)
        self.reverso = reverso              # opcional; si None, cara() cae al frontal
        self.campos = tuple(campos)         # datos extra que muestra (legacy, sin uso v1)
        self.campos_opcionales = tuple(campos_opcionales)   # v2: campos que prende/apaga
        self.logo_posiciones = tuple(logo_posiciones)       # v2: presets de logo que soporta


_MODELOS = {}


def registrar(clave, nombre, orientacion, frontal, reverso=None, campos=(),
              campos_opcionales=(), logo_posiciones=()):
    _MODELOS[clave] = Modelo(clave, nombre, orientacion, frontal, reverso, campos,
                             campos_opcionales, logo_posiciones)


def catalogo():
    """Lista de modelos en orden de registro."""
    return list(_MODELOS.values())


def modelos_con_campo(campo):
    """Modelos cuyo 'campos_opcionales' incluye 'campo' (para sugerencias del asistente)."""
    return [m for m in _MODELOS.values() if campo in m.campos_opcionales]


def modelos_con_logo_pos(pos):
    """Modelos cuyo 'logo_posiciones' incluye 'pos' (para sugerencias del asistente)."""
    return [m for m in _MODELOS.values() if pos in m.logo_posiciones]


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto). estilo = clave registrada; lado in {frontal, reverso}."""
    m = _MODELOS[estilo]
    fn = m.frontal if lado == "frontal" else (m.reverso or m.frontal)
    return fn(lado, ctx, ctx["datos"])
