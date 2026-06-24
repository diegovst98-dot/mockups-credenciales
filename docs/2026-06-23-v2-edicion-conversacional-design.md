# Diseño — v2: Edición conversacional (Parte B)

> Fecha: 2026-06-23 · Proyecto: Mockups de credenciales (#22, app del vendedor)
> Continúa la Parte A (catálogo personalizable, v22 publicada). Esta es la **Parte B / "v2"**
> que el vendedor pidió en la nota de voz + chat (2026-06-23).

## 1. Contexto y problema

La app ya genera un **catálogo PDF** de 18 modelos pintados con la marca del cliente (Parte A).
El vendedor quiere poder **responder en vivo a lo que el cliente pide** sobre un modelo elegido,
sin volver donde el diseñador: *"agrégale un espacio para cargo / tipo de sangre / DNI", "atrás
pone la web", "en vez de que esté por acá, ponlo a la derecha", "el logo ponlo aquí", "cambia este
color por este"* — *"como lo hacía con Google Flow"*.

**Para qué sirve la app (decisivo para el alcance):** es una herramienta de **venta**. El vendedor
le dice al cliente *"esto es un boceto, una base; más adelante cuando pidas se hace al detalle"*. El
mockup **NO es el arte final imprimible** — el detalle fino lo hace el diseñador después en
CardPresso. El mockup solo debe verse pro y **responder al pedido del cliente para cerrar la venta**.

## 2. Objetivo

Una pestaña **"Personalizar"** donde, sobre **un modelo elegido**, el vendedor hace retoques por
**chat (lenguaje natural, parser local, gratis) + controles visibles**, ve el resultado en vivo, y
**exporta ese modelo** (PDF/PNG) para mandárselo al cliente.

## 3. Decisiones acordadas (brainstorming 2026-06-23)

| # | Decisión | Valor |
|---|----------|-------|
| D1 | Motor del chat | **Parser local** (offline, GRATIS, determinista) **+ controles visibles** de respaldo. NO IA con costo (la dejamos enchufable a futuro). |
| D2 | Flujo | Editar **UN modelo elegido** del catálogo (no diseñar desde cero). |
| D3 | Naturaleza | Es un **boceto de venta**, no el arte final → bastan ajustes acotados que se vean pro. |
| D4 | Qué se edita | (a) campos on/off, (b) textos de muestra, (c) color, (d) cambiar de modelo, (e) logo en **posiciones preset** donde el modelo lo permita. |
| D5 | Logo | **Posiciones preset por modelo**, NO arrastre libre. Donde no se pueda sin romper, el asistente **sugiere otro modelo**. |
| D6 | Salida | Exportar el modelo personalizado como **PDF y/o PNG**. |
| D7 | Principio | Cada modelo **declara qué ajustes soporta**; para lo que el modelo actual no puede, el asistente sugiere un modelo que sí. |

## 4. Alcance

**Incluye:** la pestaña Personalizar, el estado de edición, el parser local, los controles, el
preview en vivo, el export, y la **parametrización de los modelos** para soportar los ajustes.

**NO incluye (YAGNI):** arrastre libre de elementos; "diseñar cualquier credencial desde cero";
IA con costo (queda enchufable); editar el arte final imprimible (eso es CardPresso/diseñador).

## 5. Arquitectura

### 5.1 Estado de edición (`Ajustes`)

Un objeto/dict **`Ajustes`** es la única fuente de verdad de la edición; tanto el chat como los
controles lo mutan, y el preview se re-renderiza desde él:

```
Ajustes = {
  "modelo": "mh2",                 # clave del modelo elegido
  "color": None | "#RRGGBB",       # None = automático del logo
  "campos": {"tipo_sangre": True, "codigo": False, "web": False, ...},  # solo los que el modelo soporta
  "textos": {"nombre": ..., "cargo": ..., "id": ..., "empresa": ...},   # overrides del demo
  "logo_pos": "default" | "izq" | "centro" | "der" | ...                # solo presets que el modelo soporta
}
```

### 5.2 Capacidades declaradas por modelo

Cada `Modelo` (en `plantillas/registro.py`) declara qué puede ajustar, para que el editor ofrezca
solo lo posible y el asistente sepa cuándo sugerir otro modelo:

```
Modelo(..., campos_opcionales=("tipo_sangre","web"), logo_posiciones=("default","der"))
```

- **Global (todos los modelos):** color, textos de muestra, cambiar de modelo. (Funcionan ya con la
  arquitectura actual: color = variable CSS; textos = override de `DATOS`.)
- **Por modelo:** `campos_opcionales` (qué campos puede prender/apagar) y `logo_posiciones` (qué
  presets de logo soporta). Empezar declarando lo que cada modelo ya tiene; ampliar es mecánico.

### 5.3 Render con ajustes

`construir_contexto(logo, prim, sec, cliente, ajustes=None)` aplica los ajustes:
- `color` → sobreescribe `prim` (igual que el color manual de la Parte A).
- `textos` → override de `DATOS`.
- `campos` → el `ctx` lleva qué campos opcionales mostrar; cada modelo los lee para incluirlos/omitirlos.
- `logo_pos` → el `ctx` lleva la posición; los modelos que la soportan ajustan una clase CSS.

`motor.render_modelo(logo, cliente, ajustes) -> PIL.Image` (helper nuevo) renderiza **un** frente con
los ajustes, reutilizando `cara()` + `render_caras()`. Es lo que alimenta el preview y el export.

### 5.4 Parser local de intención (`asistente.py`, nuevo)

`interpretar(texto, ajustes, modelo) -> (cambios, mensaje)`:
- Normaliza (minúsculas, sin acentos) y matchea contra patrones con **sinónimos** para producir
  **intenciones**: `SET_COLOR`, `TOGGLE_CAMPO`, `SET_TEXTO`, `SET_LOGO_POS`, `CAMBIAR_MODELO`, `NADA`.
  Ejemplos: "tipo de sangre"/"grupo sanguineo"/"GS" → `TOGGLE_CAMPO(tipo_sangre, on)`; "ponlo a la
  derecha"/"el logo a la derecha" → `SET_LOGO_POS(der)`; "mas oscuro"/"azul" → `SET_COLOR(...)`;
  "otro modelo"/"muestrame otro" → `CAMBIAR_MODELO`.
- Si la intención **no la soporta el modelo actual** (campo o posición de logo) → devuelve un
  **mensaje** que lo explica y **sugiere un modelo que sí** (busca en el catálogo por capacidad).
- Si **no entiende** → mensaje pidiendo reformular + recordatorio de que están los controles.
- 100% determinista y testeable (frase → intención esperada). Sin red, sin costo.
- **Enganche futuro (sin costo hoy):** la firma permite, si algún día se quiere, delegar el parseo a
  un LLM en la nube detrás de la misma interfaz `interpretar(...)`; el resto del sistema no cambia.

### 5.5 GUI — pestaña "Personalizar" (`app.py`)

Tercera pestaña del Notebook (junto a "Mockups" y "Renombrar Cotizaciones"):
- **Arriba:** elegir logo + nombre del cliente + selector de modelo (los 18) — o se hereda lo último
  generado en la pestaña Mockups.
- **Izquierda:** **preview en vivo** (la imagen del modelo con los ajustes; re-render ~1-2 s por cambio).
- **Derecha:** **chat** (caja de texto + historial de lo aplicado) + **controles** (mismos parámetros:
  toggles de campos que el modelo soporta, selector de color, campos de texto, posición de logo,
  botón "otro modelo").
- **Abajo:** **Exportar** (PDF y/o PNG del modelo personalizado).
- El chat y los controles mutan el mismo `Ajustes`; cualquier cambio dispara el re-render del preview
  en un hilo (cuidando el patrón seguro de subprocess/hilo de la lección del build: stdin redirigido).

### 5.6 Flujo de datos

```
elegir modelo + logo  →  Ajustes inicial
   ┌──────────────┐         ┌─────────────────────────────────────┐
   │ chat (texto) │──interpretar()──► cambios ──► muta Ajustes ◄── controles
   └──────────────┘                                   │
                                                       ▼
                              motor.render_modelo(logo, cliente, Ajustes) ─► preview
                                                       │
                                                 Exportar ─► PDF/PNG
```

## 6. Plan por fases (resumen; el detalle va al plan)

- **Fase 1 — Núcleo sin GUI:** `Ajustes` + capacidades por modelo + `construir_contexto(ajustes)` +
  `motor.render_modelo()` + parser `asistente.interpretar()`. Tests del parser y del render con ajustes.
- **Fase 2 — Modelos:** declarar `campos_opcionales`/`logo_posiciones` y hacer que cada modelo lea
  los ajustes (empezar por los globales: color/textos/cambiar-modelo, que ya funcionan; luego campos
  y logo por modelo, mecánico).
- **Fase 3 — GUI:** pestaña Personalizar (preview + chat + controles + export).
- **Fase 4 — Publicar:** tests verdes + smoke del exe + `publicar.py` + zip (recordando: imports
  nuevos → forzarlos en `launcher.py`; recompilar exe si cambian librerías).

## 7. Pruebas

- **Parser:** tabla de frases → intención esperada (incluye sinónimos, "no entiende", "modelo no lo
  soporta → sugiere X"). Determinista, rápido.
- **Render con ajustes:** color override aplica; campo on/off cambia el HTML; texto override aparece;
  logo_pos cambia la clase; el logo del cliente **nunca se recolorea** (regla fija, test extendido).
- **render_modelo:** produce imagen del tamaño correcto por orientación.
- **Export:** genera PDF/PNG no vacío.
- Validación visual con 2-3 modelos + logos reales.

## 8. Manejo de errores

- Parser no entiende → mensaje claro + "usa los controles de la derecha".
- Pedido que el modelo no soporta → explica + sugiere modelo compatible (no falla).
- Render falla (Edge) → reusar el render robusto de la Parte A (reintentos + error real).

## 9. Riesgos y mitigaciones

- **Heterogeneidad de los 18 modelos** para campos/logo → mitigado por D7 (cada modelo declara lo que
  soporta; el asistente sugiere otro para lo que no). No hace falta que todos soporten todo.
- **Parser local entiende solo lo programado** → cubrir buen vocabulario + sinónimos; los controles
  visibles son el respaldo siempre disponible; interfaz lista para enchufar IA si hiciera falta.
- **Latencia del preview (~1-2 s/cambio)** → aceptable para un editor de boceto; render en hilo
  (patrón seguro de subprocess de la lección del build).
- **Romper el catálogo (Parte A)** → `ajustes=None` deja el comportamiento actual idéntico; la Parte A
  no cambia.
