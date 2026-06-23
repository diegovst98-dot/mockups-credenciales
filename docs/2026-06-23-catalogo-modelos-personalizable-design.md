# Diseño — Catálogo de modelos personalizable (Parte A)

> Fecha: 2026-06-23 · Proyecto: Mockups de credenciales (#22, app del vendedor)
> Origen: feedback del vendedor (nota de voz + chat 2026-06-23) + folleto real de muestras
> de la empresa (`Desktop\mockups modelos\Modelos para fotochecks - DISECOD (1).pdf`).

## 1. Contexto y problema

Hoy la app genera 3 estilos genéricos (Clásica / Gafete / Premium). El vendedor reporta
que los mockups salen **"muy sencillos"** y no convencen para cerrar. La empresa ya tiene
un **folleto de muestras** con ~16 modelos profesionales reales (9 verticales + 7
horizontales) que sí venden; hoy lo mandan tal cual (con logos de ejemplo) y el cliente
elige uno diciendo *"ese, pero con mi logo y mi color"*.

El folleto mismo declara la promesa de personalización:
- *"El color del diseño elegido es personalizable"*
- *"Vertical u Horizontal; ambas caras a color, o cara a color + reverso negro"*

## 2. Objetivo

Que la app **adelante ese paso de venta**: a partir del logo + nombre del cliente,
genere un **catálogo personalizado** (PDF folleto) con los modelos reales **ya pintados
con la marca del cliente** (color del logo) y con su logo insertado. El cliente se ve a
sí mismo en cada layout y elige; el vendedor lo manda por WhatsApp.

Esto es **ampliar el motor actual**, no rehacerlo: la app ya parametriza el color por la
tinta del logo e inserta el logo del cliente en su tinta real.

## 3. Alcance

**Parte A (este spec):** catálogo de modelos reales personalizable.

**Parte B (NO en este spec — etapa 2 aparte):** edición conversacional ("chatear con el
bot" para mover el logo, cambiar un color puntual, prender campos). Se documenta como
proyecto futuro. La arquitectura de la Parte A (modelos parametrizados) deja la puerta
abierta sin invertir de más ahora.

## 4. Decisiones acordadas (brainstorming 2026-06-23)

| # | Decisión | Valor acordado |
|---|----------|----------------|
| D1 | Foco | Parte A primero; Parte B = etapa 2 aparte |
| D2 | Qué genera | El **catálogo completo personalizado** de un toque |
| D3 | Color | **Automático** del logo, con **opción de cambiarlo** (selector en GUI) |
| D4 | Modelos | Meta = ~16 del folleto; **validar 2-3 primero** antes de escalar |
| D5 | Camino técnico | **Camino 1**: rehacer cada modelo en HTML/CSS (calidad imprenta) |
| D6 | Entrega | **PDF folleto** espejo del de muestras (+ se mantiene `para-diseno\`) |
| D7 | Caras en el folleto | **Solo frentes** (el reverso se arma cuando el cliente elige) |
| D8 | Plantillas viejas | **Mantenerlas**: catálogo = ~16 reales **+** Clásica/Gafete/Premium |
| D9 | Datos de muestra | **Demo fijos genéricos** (es un boceto de presentación) |
| D10 | Portada | **Personalizada**: "Propuesta de credenciales para [CLIENTE]" + logo cliente |

## 5. Arquitectura

### 5.1 Reproducción de modelos (Camino 1)

Cada modelo del folleto se reconstruye como una **plantilla HTML/CSS** nueva, igual al
patrón actual de `plantillas.py`: bloque CSS + función que arma el cuerpo + registro en el
dispatcher. La imagen del folleto es solo **referencia de layout**; el resultado lleva el
logo real + datos demo + color de la marca del cliente.

Se respetan las reglas fijas existentes:
- ⛔ **El logo del cliente NUNCA se recolorea** (tinta real; solo tamaño/posición).
- El **color de marca tiñe el DISEÑO** vía variables CSS (`--prim/--medio/--oscuro/--acc/
  --acc2`), que ya produce `construir_contexto()` a partir de la tinta del logo.
- Fondos claros → el logo a color siempre se lee; imprime sin bandeo en Evolis.

### 5.2 Refactor de `plantillas.py` → paquete `plantillas/`

Con ~19 modelos, un solo archivo crece demasiado (~850+ líneas) y mezcla
responsabilidades. Se reorganiza en un paquete, manteniendo cada modelo **aislado y
entendible por separado**:

```
codigo/plantillas/
  __init__.py        # API pública: cara(estilo, lado, ctx), REGISTRO, lista de modelos
  base.py            # css_base, construir_contexto, _shell, _root, iconos, utilidades color
  modelos/
    clasica.py       # (las 3 actuales se mueven aquí tal cual)
    gafete.py
    premium.py
    m01_<nombre>.py  # un archivo por modelo reproducido del folleto
    ...
```

- `__init__.py` expone `cara(estilo, lado, ctx)` y un `REGISTRO` (lista ordenada de
  modelos con metadatos: clave, nombre visible, orientación vertical/horizontal, campos
  extra que usa). `motor.py` consume el registro para iterar el catálogo.
- Cada `modelos/*.py` registra su estilo (CSS + función frontal). El reverso es opcional
  (no se usa en el folleto, D7) pero el contrato lo soporta para etapa posterior.
- Beneficio: cada modelo se entiende y se prueba solo; se puede reconstruir en paralelo;
  y expone sus "parámetros" (base para la Parte B futura).

> Nota: `motor.py` arrastra ~45 funciones Pillow muertas (estilos viejos). Son inofensivas;
> NO se refactorizan en este trabajo salvo que estorben directamente al cambio.

### 5.3 Datos demo y campos extra

`DATOS` se extiende con campos de muestra para los modelos que los usan en el original:
`tipo_sangre` ("O+"), `codigo` ("10052"), `web` (ya existe vía `web_cliente`). Cada modelo
decide qué campos muestra; los que no aplican simplemente no se renderizan. Foto demo y
nombre/cargo/DNI siguen fijos (D9).

### 5.4 Salida: PDF folleto personalizado

Nuevo módulo de armado (p.ej. `codigo/folleto.py`) que compone los renders en un PDF
espejo del folleto de muestras (D6, D10):

1. **Portada:** marco DISECOD + "Propuesta de credenciales para [CLIENTE]" + logo cliente.
2. **Modelos verticales:** frentes pintados con la marca, en grilla.
3. **Modelos horizontales:** ídem.
4. **Pie:** www.fotochecks.pe.

Se arma con PIL (componer páginas como imágenes y `save(..., save_all=True,
append_images=...)` a PDF), reusando el render Edge ya existente. Se mantiene además la
carpeta `para-diseno\` (caras limpias CR80 300dpi para CardPresso) tal como hoy.

### 5.5 GUI (`app.py`)

- Se agrega **selector de color**: la app muestra el color detectado del logo y un botón
  "Cambiar color…" (`tkinter.colorchooser.askcolor`). El color elegido sobreescribe el
  detectado y se pasa a `motor.generar(...)`.
- El botón principal pasa a **"Generar catálogo"**.
- Se mantiene la simpleza (equipo pequeño, bajo mantenimiento).

### 5.6 Flujo de datos

```
logo + nombre + (color opcional)
  → motor.generar(): extrae paleta del logo (o usa color elegido)
  → para cada modelo en REGISTRO: construir_contexto() → plantillas.cara(frontal) → render_caras() [Edge]
  → folleto.armar_pdf(renders, cliente, logo): PDF folleto personalizado
  → + para-diseno\ (caras limpias, como hoy)
  → abre la carpeta de salida
```

## 6. Plan por fases

- **Fase 1 — Validación de fidelidad (gate con Diego).** Reconstruir 2-3 modelos
  representativos (1 vertical fuerte, 1 horizontal, 1 con campos extra). Renderizar,
  **mirar**, y un jurado (subagente fresco) puntúa fidelidad vs la imagen de referencia.
  Diego aprueba el método antes de escalar.
- **Fase 2 — Catálogo completo.** Reconstruir los ~16 modelos del folleto (en paralelo,
  cada uno comparado contra su referencia y juzgado). Cada modelo se mira sobre fondo real.
- **Fase 3 — PDF folleto + color manual.** Armar `folleto.py` (PDF espejo, portada
  personalizada) y el selector de color en la GUI. Integrar en `motor.generar`.
- **Fase 4 — Publicar.** `publicar.py`/`publicar.bat` (sube versión, manifest, push). Si
  el paquete `plantillas/` agrega archivos nuevos, registrarlos en `ARCHIVOS` del manifest
  para el auto-update del vendedor.

## 7. Pruebas

- Cada modelo del registro **renderiza** sin error (Edge) y produce imagen del tamaño
  esperado (vertical/horizontal CR80).
- **El logo del cliente no se recolorea** (test ya existente, extendido a los modelos
  nuevos).
- **El color cambia** correctamente al pasar un color manual (las variables CSS reflejan
  el color elegido, no el del logo).
- El **PDF** se arma con el número correcto de páginas y abre sin error.
- Validación visual con varios logos reales (incl. el del cliente que mandó el vendedor)
  + logos de colores/proporciones distintas (oscuro, claro, multicolor, razón social larga).

## 8. Referencias de modelos

Las imágenes de referencia (folleto + 16 modelos) se copian al repo (p.ej.
`docs/referencias-modelos/`) y se mapean a su clave de modelo para que el jurado de
fidelidad y futuras iteraciones tengan la fuente versionada. Catálogo exacto (cuántos
frentes distintos vs reversos/duplicados del set de WhatsApp) se confirma al inicio de
Fase 1.

## 9. Qué NO incluye (YAGNI)

- Parte B conversacional ("chatear con el bot"); IA generativa libre.
- Reversos por modelo dentro del folleto (D7).
- Edición de los datos del empleado (D9).
- Refactor del código Pillow muerto de `motor.py` no relacionado.

## 10. Riesgos y mitigaciones

- **Fidelidad de reproducción:** algunos gestos gráficos (ondas, diagonales, barras) son
  delicados en CSS. → Gate de Fase 1 con jurado + mirar; afinar método antes de los 16.
- **Modelos multicolor del original:** algunos ejemplos usan varios colores. → Se adaptan a
  primario + acento de la marca del cliente (la variedad la dan los layouts, no los
  colores); el cliente ve su marca uniforme en cada formato.
- **Tamaño del PDF / tiempo de render:** ~16-19 renders. → Reusar el render Edge (rápido);
  si pesa, bajar DPI del folleto de presentación (las caras de imprenta van aparte en
  `para-diseno\`).
- **Auto-update:** archivos nuevos del paquete deben entrar al manifest o el vendedor no
  los recibe. → Checklist en Fase 4.
