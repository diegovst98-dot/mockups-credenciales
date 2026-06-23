# Renombrador de Cotizaciones DC — diseño

> Fecha: 2026-06-23 · Proyecto: mockups-credenciales (app del vendedor) · Estado: aprobado por Diego, pendiente de plan e implementación.
> Pedido original: el vendedor deja cotizaciones PDF crudas en una carpeta y quiere que un programa las lea, las clasifique y las renombre automáticamente con `DC + CATEGORÍA + cliente`. Tiene que ser fácil y visual.

## 1. Objetivo

Una función que toma una carpeta de cotizaciones DISECOD en PDF (las "DC") y deja cada archivo renombrado de forma consistente, leyendo el contenido del PDF — **sin conectarse al ERP** (todo el dato necesario ya está impreso dentro del PDF). El vendedor revisa en una tabla y corrige con un clic antes de aplicar.

Nombre destino:
```
DC [CATEGORÍA] - [CLIENTE] DD-MM.pdf
```
Ejemplo real: `DC FOTOCHECKS - FLOPOWER PERU S.A.C. 23-06.pdf`

## 2. Decisiones tomadas (brainstorming 2026-06-23)

| Tema | Decisión |
|---|---|
| Dónde vive | Pestaña nueva **"Renombrar Cotizaciones"** en la app de Mockups (la del vendedor). |
| Categoría en mezclas | **Gana la categoría del mayor monto** (suma de soles por categoría dentro de la cotización). |
| Fuera de las 5 | Se agregan **IMPRESORAS** (rubro frecuente) y bolsa **OTROS**. Total 7 categorías automáticas. |
| Vocabulario fino | Auto pone una de las **7**; el menú desplegable de la tabla de revisión trae el **vocabulario completo** (PVC, PVC ADHESIVO, TARJETAS IMPRESAS, modelos de impresora) para afinar manualmente con 1 clic. |
| Cola del nombre | **Fecha de emisión** del PDF en formato `DD-MM` (la costumbre actual del vendedor). Si el nombre ya existe → agregar ` (2)`, ` (3)`. |
| Originales | **Renombrar en el sitio** (sin copiar, mover ni borrar). |
| Número ERP | Se lee del PDF y se muestra como referencia en la tabla, pero **no** va en el nombre (el vendedor prefirió la fecha). |

Las 7 categorías automáticas: `FOTOCHECKS · ACCESORIOS · INSUMOS · KIT DE LIMPIEZA · MANTENIMIENTO · IMPRESORAS · OTROS`.

Vocabulario completo del desplegable (las 7 + las finas que el vendedor usa a mano): añadir `PVC`, `PVC ADHESIVO`, `TARJETAS IMPRESAS`, `GIFT CARD`, y modelos de impresora frecuentes (`ZENIUS 2 CLASSIC`, `PRIMACY 2 DUPLEX`, etc.) como rótulos elegibles. Lista editable en una constante.

## 3. Las dos plantillas de cotización (verificado sobre PDFs reales)

Hay dos formatos de PDF en circulación. El lector debe soportar ambos:

**Plantilla A — ERP / "PROPUESTA ECONÓMICA"** (Soluflex). Orden de líneas:
```
PROPUESTA ECONÓMICA
DC-001-00000070        ← número de documento
Fecha: 23/06/2026      ← fecha de emisión
LAFAYETTE HOLDINGS S.A.C.   ← CLIENTE (línea inmediatamente debajo de "Fecha:")
R.U.C. : 20601342724       ← o "D.N.I. :" si es persona natural, o ausente
Señores:
Por medio de la presente...
[ CÓDIGO / DESCRIPCIÓN / CANT. / P. TOTAL / P. UNIT (/ TOTAL INC IGV) ]
<bloques de producto>
SUBTOTAL ... IGV ... TOTAL
[CONDICIONES COMERCIALES ...]   ← contiene el RUC propio de DISECOD (no usar)
```

**Plantilla B — carta / "Lima, fecha"**:
```
DC-12942-2026          ← número (a veces prefijo DJ-, ver §7)
Lima, 08 de Junio del 2026   ← fecha de emisión
Señores:
MAYRO CARLOS           ← CLIENTE (línea debajo de "Señores:", antes de "Presente.-")
[ALEX FRANCO]          ← a veces hay una persona de contacto debajo de la empresa
Presente.-
[ Item / Descripción / Cant / Precio Unit / Precio Total / Total Inc Igv ]
<bloques de producto numerados 01, 02, ...>
```

## 4. Lógica de extracción (módulo puro, sin GUI)

Todo lo siguiente vive en `codigo/renombrador.py`, sin Tkinter, testeable solo.

### 4.1 Texto
`pypdfium2` extrae el texto de la página 1 (los datos de cabecera y la tabla de productos están en la pág. 1). Motivo de la librería: licencia permisiva (BSD/Apache), igual que en el fotochecks-editor; **NO usar PyMuPDF/fitz** (AGPL) porque este repo es público.

> ⚠️ **Re-validar en implementación:** las anclas (§4.5) y la segmentación de bloques (§4.6) se verificaron en diseño con un extractor de texto (PyMuPDF) sobre los PDFs reales. `pypdfium2` puede devolver el texto en un **orden distinto** (p.ej. por columnas en vez de por filas). El primer paso de TDD es imprimir el texto crudo que da `pypdfium2` sobre 2-3 PDFs reales y confirmar/ajustar las anclas antes de seguir. No asumir que el orden es idéntico al de la prueba.

### 4.2 Detección de plantilla
`"PROPUESTA ECON"` presente en el texto → Plantilla A; si no → Plantilla B.

### 4.3 Número de documento
Regex que acepta cualquier prefijo de 2 letras: `\b[A-Z]{2}-\d{2,5}-\d{3,8}\b` (cubre `DC-001-00000070`, `DC-12942-2026` y la variante real `DJ-12845-2026`). Si no hay match → marcar baja confianza.

### 4.4 Fecha de emisión → `DD-MM`
- Plantilla A: línea `Fecha: DD/MM/YYYY` → `DD-MM`.
- Plantilla B: línea `Lima, DD de <mes> del YYYY` → mapear nombre de mes español a número → `DD-MM`.
- Si no se encuentra → dejar la fecha vacía (el vendedor la completa o se omite del nombre).

### 4.5 Cliente (ancla robusta verificada)
- Plantilla A: **la línea inmediatamente debajo de "Fecha:"**. (Funciona con RUC, con DNI o sin documento; resuelve los casos "CLIENTES VARIOS" y "D.N.I." que rompían el ancla por-RUC.)
- Plantilla B: **la primera línea debajo de "Señores:"** que no sea "Presente.-" (toma la empresa, ignora la persona de contacto que a veces va debajo).

Limpieza del nombre (`_limpiar_cliente`):
- Si el nombre trae `" - "` y el lado derecho termina en sufijo societario (`S.A.C.`, `E.I.R.L.`, `S.A.`, `S.R.L.`), usar el lado derecho corto. Ej: `SNIPER TECH SOCIEDAD ANONIMA CERRADA - SNIPER TECH S.A.C.` → `SNIPER TECH S.A.C.`
- Quitar `"SOCIEDAD ANONIMA CERRADA"` redundante si quedó.
- Quitar caracteres prohibidos en nombres de archivo Windows: `\ / : * ? " < > |`.
- Recortar si supera ~45 caracteres.
- **Cuidado:** algunos clientes tienen guion en su propia razón social (`CUTTING - EDGE PERU SAC`). La limpieza no debe partir esos nombres; el separador del nombre de archivo (`" - "` entre categoría y cliente) lo pone el formateador, no se infiere del cliente.

### 4.6 Clasificación por mayor monto
1. Cortar el cuerpo al primer `SUBTOTAL` o `CONDICIONES COMERCIALES` (para no leer totales ni el RUC de DISECOD).
2. **Segmentar en bloques de ítem** (consciente de plantilla):
   - Plantilla A: nuevo bloque al detectar una **línea-código** (regex tipo `^[A-Z]{2,5}[A-Z0-9-]*\d[A-Z0-9-]*-?$`: `F400102`, `RCT223NAAA`, `ACL001`, `SERV-MANT-`, `COLLARCOLL-`). **No** segmentar por enteros sueltos (son cantidades, no ítems — este fue el bug del borrador).
   - Plantilla B: nuevo bloque al detectar una **línea de índice** (`^\d{1,2}$`) **seguida de una línea con texto** (descripción). Así no confunde la cantidad "100" con un índice de ítem.
3. Por bloque: **categoría = primera palabra clave** que matchee en orden de especificidad (regla "producto principal del ítem": ignora los "incluye cinta/kit/tarjetas" del combo de impresora porque aparecen después del titular). **monto del bloque = mayor número con decimales** (`^\d{1,3}(?:,\d{3})*\.\d{2}$`; las cantidades enteras no cuentan).
4. **Sumar monto por categoría; gana la de mayor suma.** Si ningún bloque clasifica → `OTROS`.

Orden de prioridad de palabras clave (más específica primero):
```
MANTENIMIENTO   → "SERVICIO DE MANTENIMIENTO", "SERV-MANT", "MANTENIMIENTO"
KIT DE LIMPIEZA → "KIT DE LIMPIEZA", "ACL001"
IMPRESORAS      → "IMPRESORA DE CARNETS", "IMPRESORA DE FOTOCHECKS", "IMPRESORA EVOLIS",
                  "ZENIUS", "PRIMACY", "ELYPSO", "BADGY"
INSUMOS         → "RIBBON", "RCT", "YMCKO", "PELICULA", "CINTA DE"
FOTOCHECKS      → "FOTOCHECK"
ACCESORIOS      → "PORTAFOTOCHECK", "COLLAR", "GANCHO", "YOYO", "ARNES"
OTROS           → "GIFT CARD", "TARJETA DE REGALO"
```
(Las constantes van en `renombrador.py` y se ajustan con TDD contra los PDFs reales.)

### 4.7 Confianza (para el semáforo)
Marcar **ámbar** (revisar) cuando: no se halló número; cliente vacío, genérico ("CLIENTES VARIOS") o muy corto; categoría = OTROS; no se parsearon montos; o el producto parece tarjeta genérica (posible gift card sin la palabra "gift"). El resto, **verde**.

## 5. Nombre destino y colisiones
`_nombre_destino(cat, cliente, fecha) -> "DC {cat} - {cliente} {DD-MM}.pdf"` (si no hay fecha, se omite el sufijo). Antes de aplicar, si el destino ya existe en la carpeta, agregar ` (2)`, ` (3)`… Nunca sobrescribir.

## 6. Interfaz (pestaña en `codigo/app.py`)

`app.py` hoy es una sola ventana. Se introduce un `ttk.Notebook` con dos pestañas:
- **"Mockups"** — el flujo actual, movido tal cual a un `Frame` (sin cambios funcionales).
- **"Renombrar Cotizaciones"** — nuevo `Frame`:
  - Botón **"Elegir carpeta…"** + label con la ruta elegida.
  - **Tabla** (`ttk.Treeview`): columnas *Archivo · Categoría · Cliente · Fecha · N° (ref)*.
    - *Categoría* es editable con un `Combobox` (vocabulario completo).
    - *Cliente* y *Fecha* editables (doble clic).
    - Fila **verde** = confianza alta; **ámbar** = revisar (§4.7).
  - Botón **"Renombrar todo"** → aplica, renombra en el sitio, y muestra resumen: "X renombrados · Y por revisar".
- Ventana: ampliar geometría (la tabla necesita más alto/ancho que los 560×420 actuales).

Se reutiliza el patrón "proponer y confirmar" del fotochecks-editor: el programa propone, el humano corrige antes de aplicar (misma filosofía anti-error).

## 7. Empaquetado y distribución

- **`pypdfium2` es librería binaria → recompilar el `.exe` una vez.** Editar `MockupsDISECOD.spec` (hiddenimports / `collect_all('pypdfium2')` según haga falta, igual que el editor manejó pypdfium2). Agregar `pypdfium2` a `requirements.txt`.
- **`codigo/renombrador.py` es Python puro → se agrega a `ARCHIVOS` en `publicar.py`** para que futuros ajustes a la lógica lleguen por auto-update sin recompilar.
- `app.py` modificado también viaja en `ARCHIVOS` (ya está).
- **Timing a favor:** la app de Mockups sigue pendiente de instalarle al vendedor. El `.exe` recompilado con `pypdfium2` + la pestaña nueva es el que se instala — una sola entrega trae Mockups + Renombrar, sin doble trabajo.
- Subir versión + manifest + push: `publicar.py` / `publicar.bat` (cuando Diego apruebe publicar).

## 8. Casos borde verificados (cubrir en tests)
- Prefijo `DJ-` además de `DC-` (MAS ÚTILES).
- Cliente con `D.N.I.` en vez de `R.U.C.`, o sin documento (`CLIENTES VARIOS` → ámbar).
- Persona de contacto debajo de la empresa en plantilla B (tomar la empresa).
- Cliente con guion en la razón social (`CUTTING - EDGE PERU SAC`).
- Combo de impresora que menciona "incluye cinta/kit/tarjetas" en la descripción → debe ganar IMPRESORAS por monto, ignorando los regalos.
- Gift card descrita genéricamente como "tarjeta impresa en pvc" (sin "gift") → cae en la categoría más cercana + ámbar; el vendedor corrige con el desplegable.
- Empate o cotización sin montos parseables → ámbar.

## 9. Fuera de alcance (YAGNI)
- No conectar al ERP / Soluflex (innecesario).
- No mover a subcarpetas, no copiar, no borrar.
- No auto-detectar perfectamente los sub-tipos finos de tarjeta (PVC vs adhesivo vs tarjetas impresas): eso lo resuelve el desplegable de revisión, no el clasificador.
- No OCR (las cotizaciones son PDFs de texto, no escaneos).

## 10. Pruebas
- `tests/test_renombrador.py` con los ~18 PDFs reales como fixtures locales (en `Downloads` y `Desktop\cotizaciones para renombrar`).
- **Los PDFs reales NO se commitean** (tienen razón social, RUC y precios de clientes). Quedan solo en la PC de Diego; los tests apuntan a rutas locales o a una carpeta de fixtures fuera de git.
- Criterio de aceptación medido: sobre los 5 de `Desktop\cotizaciones para renombrar`, el clasificador ya reproduce 4/5 nombres idénticos al naming manual del vendedor; el 5º (Universidad del Altiplano) da FOTOCHECKS por mayor monto (más consistente que el "Accesorios" manual). La meta es ≥ ese nivel en el set completo, con lo dudoso marcado en ámbar.

## 11. Riesgos / límites honestos
- El parseo de montos depende de que el PDF sea de texto y mantenga el layout actual del ERP. Si Soluflex cambia la plantilla, hay que re-calibrar (mitigado por el semáforo + edición manual).
- La frontera FOTOCHECKS / PVC / TARJETAS IMPRESAS es intrínsecamente ambigua en el texto; por eso es decisión manual vía desplegable, no automática.

## 12. Archivos que se tocan
- **Nuevo:** `codigo/renombrador.py` (lógica pura), `tests/test_renombrador.py`.
- **Modificados:** `codigo/app.py` (Notebook + pestaña), `publicar.py` (ARCHIVOS += renombrador.py), `MockupsDISECOD.spec` (bundle pypdfium2), `requirements.txt` (pypdfium2).
