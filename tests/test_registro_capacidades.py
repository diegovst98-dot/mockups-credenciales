# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "codigo")))


def test_modelo_tiene_capacidades_por_defecto_vacias():
    from plantillas.registro import Modelo
    m = Modelo("x", "X", "H", lambda lado, ctx, d: ("", 1, 1))
    assert m.campos_opcionales == ()
    assert m.logo_posiciones == ()


def test_registrar_acepta_capacidades():
    from plantillas import catalogo
    import plantillas  # noqa: F401  (puebla el registro)
    clasica = next(m for m in catalogo() if m.clave == "clasica")
    # se declaran en la Fase 2; aquí solo verificamos el canal (atributos existen)
    assert isinstance(clasica.campos_opcionales, tuple)
    assert isinstance(clasica.logo_posiciones, tuple)


def test_buscar_por_capacidad():
    # registra un modelo de prueba y LO QUITA al final (no contaminar el registro global)
    from plantillas.registro import (registrar, modelos_con_campo, modelos_con_logo_pos,
                                     _MODELOS)
    registrar("cap_test", "Cap Test", "H", lambda lado, ctx, d: ("", 1, 1),
              campos_opcionales=("tipo_sangre",), logo_posiciones=("der",))
    try:
        assert any(m.clave == "cap_test" for m in modelos_con_campo("tipo_sangre"))
        assert any(m.clave == "cap_test" for m in modelos_con_logo_pos("der"))
        assert all("tipo_sangre" in m.campos_opcionales for m in modelos_con_campo("tipo_sangre"))
    finally:
        _MODELOS.pop("cap_test", None)
