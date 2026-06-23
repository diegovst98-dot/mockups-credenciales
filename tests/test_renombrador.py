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

def test_limpiar_no_colapsa_marca_con_guion_y_sufijo():
    # izquierda NO es forma legal larga -> no se parte aunque la derecha tenga sufijo
    assert r.limpiar_cliente("ALPHA - BETA PERU SAC") == "ALPHA - BETA PERU SAC"

def test_limpiar_quita_caracteres_prohibidos():
    assert r.limpiar_cliente('A/B:C*?"<>|') == "ABC"

# Plantilla A: kit de limpieza unico
TEXTO_A_KIT = """PROPUESTA ECONÓMICA
DC-001-00000062
Fecha: 22/06/2026
DEMO HOLDING S.A.C.
R.U.C. : 20111111111
Señores:
CÓDIGO
DESCRIPCIÓN
CANT.
P. TOTAL
P. UNIT
ACL001
KIT DE LIMPIEZA - ACL001
1
90.00
90.00
SUBTOTAL
S/
90.00
"""

# Plantilla A: mezcla fotocheck (grande) + accesorios (chico) -> gana FOTOCHECKS
TEXTO_A_MIX = """PROPUESTA ECONÓMICA
DC-001-00000078
Fecha: 23/06/2026
DEMO MIX S.A.C.
R.U.C. : 20222222222
Señores:
CÓDIGO
DESCRIPCIÓN
CANT.
P. TOTAL
P. UNIT
TOTAL INC IGV
F400102
FOTOCHECK EN PVC AMBAS CARAS A COLOR
100
7.00
700.00
826.00
P400112
PORTAFOTOCHECK ACRILICO VERTICAL TRANSPARENTE
100
1.00
100.00
118.00
SUBTOTAL
S/
800.00
"""

# Plantilla B: impresora combo que menciona "incluye cinta/kit/tarjetas" -> gana IMPRESORAS
TEXTO_B_IMPR = """DC-12942-2026
Lima, 08 de Junio del 2026
Señores:
DEMO PRINT S.A.C.
Presente.-
Item
Descripción
01
IMPRESORA DE CARNETS ZENIUS 2 CLASSIC
Promoción incluye:
- 01 Cinta de color de 200 impresiones
- 100 tarjetas blancas PVC
- 01 tarjeta y 01 hisopo de limpieza
01
762.71
900.00
02
Tarjetas PVC Blanco
01
20.00
23.60
"""

def test_clasifica_kit_unico():
    cat, montos = r.clasificar(TEXTO_A_KIT, "A")
    assert cat == "KIT DE LIMPIEZA"

def test_clasifica_mezcla_gana_mayor_monto():
    cat, montos = r.clasificar(TEXTO_A_MIX, "A")
    assert cat == "FOTOCHECKS"
    assert montos["FOTOCHECKS"] > montos["ACCESORIOS"]

def test_clasifica_impresora_ignora_regalos_del_combo():
    cat, montos = r.clasificar(TEXTO_B_IMPR, "B")
    assert cat == "IMPRESORAS"

def test_clasifica_sin_match_es_otros():
    cat, montos = r.clasificar("PROPUESTA ECONÓMICA\nalgo raro\n5.00\nSUBTOTAL", "A")
    assert cat == "OTROS"

def test_nombre_destino_con_fecha():
    assert r.nombre_destino("FOTOCHECKS", "ACME PERU S.A.C.", "23-06") == "DC FOTOCHECKS - ACME PERU S.A.C. 23-06.pdf"

def test_nombre_destino_sin_fecha():
    assert r.nombre_destino("INSUMOS", "ACME", None) == "DC INSUMOS - ACME.pdf"

def test_analizar_texto_ok_confianza_alta():
    d = r.analizar_texto(TEXTO_A_MIX)
    assert d["categoria"] == "FOTOCHECKS"
    assert d["cliente"] == "DEMO MIX S.A.C."
    assert d["confianza"] == "alta"
    assert d["sugerido"] == "DC FOTOCHECKS - DEMO MIX S.A.C. 23-06.pdf"

def test_analizar_texto_clientes_varios_marca_revisar():
    d = r.analizar_texto(TEXTO_A_DNI + "ACL001\nKIT DE LIMPIEZA - ACL001\n1\n90.00\nSUBTOTAL")
    assert d["cliente"] == "CLIENTES VARIOS"
    assert d["confianza"] == "revisar"

def test_analizar_texto_otros_marca_revisar():
    d = r.analizar_texto("PROPUESTA ECONÓMICA\nDC-001-00000001\nFecha: 01-06\nX S.A.C.\nblah\nSUBTOTAL")
    assert d["confianza"] == "revisar"
