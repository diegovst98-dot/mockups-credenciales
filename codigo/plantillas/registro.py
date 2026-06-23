# -*- coding: utf-8 -*-
"""Registro central de modelos de credencial. Cada módulo de plantillas.modelos
llama a registrar() al importarse; motor.py consume catalogo() para iterar el folleto."""


class Modelo:
    def __init__(self, clave, nombre, orientacion, frontal, reverso=None, campos=()):
        self.clave = clave
        self.nombre = nombre
        self.orientacion = orientacion      # 'V' (638x1011) o 'H' (1011x638)
        self.frontal = frontal              # fn(lado, ctx, d) -> (html, ancho, alto)
        self.reverso = reverso              # opcional; si None, cara() cae al frontal
        self.campos = tuple(campos)         # datos extra que muestra (p.ej. ("tipo_sangre",))


_MODELOS = {}


def registrar(clave, nombre, orientacion, frontal, reverso=None, campos=()):
    _MODELOS[clave] = Modelo(clave, nombre, orientacion, frontal, reverso, campos)


def catalogo():
    """Lista de modelos en orden de registro."""
    return list(_MODELOS.values())


def cara(estilo, lado, ctx):
    """Devuelve (html, ancho, alto). estilo = clave registrada; lado in {frontal, reverso}."""
    m = _MODELOS[estilo]
    fn = m.frontal if lado == "frontal" else (m.reverso or m.frontal)
    return fn(lado, ctx, ctx["datos"])
