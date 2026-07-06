# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))

LAVANDA = (169, 161, 216)   # tinta clara (caso DISECOD)
ROJO = (180, 30, 40)        # tinta saturada oscura


def test_top6_devuelve_6_claves_validas():
    from plantillas.curaduria import elegir_top
    from plantillas.registro import catalogo
    import plantillas  # noqa: F401  (importa y registra los 18 modelos)
    claves = {m.clave for m in catalogo()}
    top = elegir_top(LAVANDA)
    assert len(top) == 6 and len(set(top)) == 6
    assert set(top) <= claves


def test_top6_balancea_orientaciones():
    from plantillas.curaduria import elegir_top
    from plantillas.registro import catalogo
    import plantillas  # noqa: F401
    ori = {m.clave: m.orientacion for m in catalogo()}
    for tinta in (LAVANDA, ROJO):
        top = elegir_top(tinta)
        vs = sum(1 for c in top if ori[c] == "V")
        hs = sum(1 for c in top if ori[c] == "H")
        assert vs >= 2 and hs >= 2


def test_pastel_castiga_modelos_que_necesitan_oscuro():
    from plantillas.curaduria import elegir_top
    import plantillas  # noqa: F401
    top_pastel = elegir_top(LAVANDA)
    # mv1 (Acción) y mv2 (Böka) necesitan acento oscuro: con lavanda NO deben entrar
    assert "mv1" not in top_pastel and "mv2" not in top_pastel


def test_nombres_comerciales_cubren_todo_el_catalogo():
    from plantillas.curaduria import nombre_comercial, NOMBRES
    from plantillas.registro import catalogo
    import plantillas  # noqa: F401
    for m in catalogo():
        n = nombre_comercial(m.clave)
        assert n and "(" not in n          # sin "(vertical)"/"(horizontal)"
        assert n == NOMBRES.get(m.clave, n)
    # los nombres internos raros no se filtran al cliente
    prohibidos = {"Böka", "Rosestore", "Vegetata", "Gaio"}
    assert not (set(NOMBRES.values()) & prohibidos)
