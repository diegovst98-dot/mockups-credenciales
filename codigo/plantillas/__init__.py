# -*- coding: utf-8 -*-
"""Paquete de plantillas de credencial.

API pública (compatibilidad con motor.py y tests):
  cara(estilo, lado, ctx) -> (html, ancho, alto)
  construir_contexto(logo, prim, sec, cliente) -> dict
  css_base() -> str
  variante_de(cliente, n=3) -> int
  catalogo() -> list[Modelo]   (modelos en orden de registro)
  registrar(...)               (lo usan los módulos de plantillas.modelos)
"""
from plantillas.base import (construir_contexto, css_base, variante_de,
                             DATOS, ORO, H, V, MG, CAMPOS_EXTRA, CAMPOS_LABEL)
from plantillas.registro import registrar, catalogo, cara, Modelo
from plantillas import modelos  # noqa: F401  (importar puebla el registro)

__all__ = ["cara", "construir_contexto", "css_base", "variante_de",
           "catalogo", "registrar", "Modelo", "DATOS", "ORO", "H", "V", "MG",
           "CAMPOS_EXTRA", "CAMPOS_LABEL"]
