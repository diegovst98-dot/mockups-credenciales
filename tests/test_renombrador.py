import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codigo"))
import renombrador as r

TEXTO_A = """PROPUESTA ECONÓMICA
DC-001-00000070
Fecha: 23/06/2026
ACME PERU S.A.C.
R.U.C. : 20123456789
Señores:
Por medio de la presente nos es grato hacerle llegar nuestras propuesta económica:
CÓDIGO
DESCRIPCIÓN
CANT.
P. TOTAL
P. UNIT
RCT223NAAA
RIBBON NEGRO RINDE 2000 CARAS
2
86.44
172.88
SUBTOTAL
S/
172.88
"""

TEXTO_B = """DJ-12845-2026
Lima, 11 de Junio del 2026
Señores:
DEMO IMPORT E.I.R.L.
JUAN CONTACTO
Presente.-
Item
Descripción
Cant
Precio Unit
01
IMPRESORA DE CARNETS PRIMACY 2 DUPLEX
01
762.71
900.00
"""

TEXTO_A_DNI = """PROPUESTA ECONÓMICA
DC-001-00000028
Fecha: 08/06/2026
CLIENTES VARIOS
D.N.I. :
Señores:
Por medio de la presente nos es grato hacerle llegar nuestras propuesta económica:
"""

def test_detectar_plantilla_A():
    assert r.detectar_plantilla(TEXTO_A) == "A"

def test_detectar_plantilla_B():
    assert r.detectar_plantilla(TEXTO_B) == "B"

def test_numero_plantilla_A():
    assert r.extraer_numero(TEXTO_A) == "DC-001-00000070"

def test_numero_plantilla_B_acepta_DJ():
    assert r.extraer_numero(TEXTO_B) == "DJ-12845-2026"

def test_numero_ausente():
    assert r.extraer_numero("sin numero aqui") is None

def test_fecha_plantilla_A():
    assert r.extraer_fecha(TEXTO_A, "A") == "23-06"

def test_fecha_plantilla_B():
    assert r.extraer_fecha(TEXTO_B, "B") == "11-06"

def test_fecha_ausente():
    assert r.extraer_fecha("sin fecha", "A") is None

def test_cliente_plantilla_A():
    assert r.extraer_cliente(TEXTO_A, "A") == "ACME PERU S.A.C."

def test_cliente_plantilla_A_con_dni():
    # ancla = linea bajo "Fecha:", funciona sin R.U.C.
    assert r.extraer_cliente(TEXTO_A_DNI, "A") == "CLIENTES VARIOS"

def test_cliente_plantilla_B_toma_empresa_no_contacto():
    assert r.extraer_cliente(TEXTO_B, "B") == "DEMO IMPORT E.I.R.L."

def test_limpiar_nombre_societario_largo():
    crudo = "SNIPER TECH SOCIEDAD ANONIMA CERRADA - SNIPER TECH S.A.C."
    assert r.limpiar_cliente(crudo) == "SNIPER TECH S.A.C."

def test_limpiar_conserva_guion_en_razon_social():
    # el cliente tiene guion propio y NO termina en sufijo societario en el lado derecho
    assert r.limpiar_cliente("CUTTING - EDGE PERU SAC") == "CUTTING - EDGE PERU SAC"

def test_limpiar_quita_caracteres_prohibidos():
    assert r.limpiar_cliente('A/B:C*?"<>|') == "ABC"
