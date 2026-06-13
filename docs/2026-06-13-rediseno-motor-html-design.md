# Rediseño del motor de mockups — de Pillow a HTML/CSS + fondos IA (v8)

> Diseño acordado en sesión de brainstorming 2026-06-13. Reemplaza el motor de
> generación (no la idea del producto). Pendiente de aprobación de Diego antes de
> escribir el plan de implementación.

## El problema (por qué cambiamos)

El motor actual (`codigo/motor.py`, v7) dibuja las tarjetas con **Pillow**: código que
pinta rectángulos, líneas y círculos. Le metimos un loop de calidad de 3 horas y 7
versiones, y aun así los resultados se ven "de plantilla" (palabras de Diego:
*"qué feo se ve, saliendo de este programa"*). **No es falta de esfuerzo: es el techo
de la herramienta.** Pillow no tiene el vocabulario de un diseñador (glassmorphism,
gradientes mesh, texturas, tipografía con buen kerning, sombras realistas, profundidad).

## Objetivo

Que el vendedor genere automáticamente, desde el logo del cliente, **3 propuestas de
credencial muy buenas, creativas y que varíen según el logo**, en un brief de
presentación con marca DISECOD, más los archivos para mandar a producir y la foto 1x1
cuando el cliente la pida. Calidad de estudio, flujo simple, costo controlado.

## Decisión central: composición híbrida en 2 capas

La IA generativa pura NO puede hacer una credencial imprimible (deforma el logo del
cliente, escribe texto basura, no da archivo CR80 editable). La solución es separar:

1. **Capa de fondo / dirección de arte** → da el "wow" y la variación por marca.
   Fuente del fondo, en orden de costo:
   - Fase 1: gradientes/texturas generados por **CSS** (gratis, determinista).
   - Fase 2: **banco de fondos pre-generados** con el ChatGPT Plus del equipo
     (gratis; ver abajo), recoloreados al color de la marca.
   - Fase 3 (opcional): **API de imagen** (Ideogram ~$0.03/img) para fondo único en
     vivo. Solo si Diego lo pide.
2. **Capa de composición** → el **logo real exacto + texto nítido + foto + datos**,
   maquetado en **HTML/CSS y renderizado con navegador headless (Playwright)**.
   Aquí nunca interviene la IA: el logo y el texto salen perfectos e imprimibles.

Prototipo validado el 2026-06-13 (`salida/_proto/`): 3 direcciones de arte con el logo
de Interbank, color sacado del logo real, calidad muy superior a Pillow, **costo $0**.

## Las 3 direcciones de arte (reemplazan los 9 estilos de Pillow)

Diego pidió **3** opciones fuertes, no 9 tibias. Punto de partida (a refinar en
implementación):

1. **Aurora** — oscuro premium: gradiente mesh nacido del color de marca, panel de
   datos con glassmorphism, foto rectangular, nombre serif (Playfair), hairline oro.
2. **Editorial** — claro/marfil: banda lateral de marca, foto, nombre serif grande,
   cargo en itálica, mucho aire, acento oro fino.
3. **Glass** — color pleno de marca: formas blur, tarjeta interna glassmorphism, foto
   circular, datos en blanco.

Cada una en **frontal + reverso**, CR80 a 300 dpi (1011×638 px / vertical 638×1011),
recoloreadas al color dominante del logo. La "variedad según el logo" sale de:
color de marca + (Fase 2) elección y recoloreo de fondo del banco.

## Banco de fondos pre-generados (Fase 2, costo $0)

- El equipo usa el **ChatGPT Plus que ya paga** (no API) para generar a mano ~30–50
  **fondos abstractos sin logo ni texto** (mesh, geométrico, ondas, mármol, degradados).
  ~5 prompts × 8 variaciones. Trabajo de una vez; renovable cuando se quiera.
- Se guardan en el repo (`codigo/fondos/`) y viajan por auto-update como cualquier asset.
- En generación: la app elige el fondo que mejor calza con el color/tono del logo y lo
  **recolorea** al color de marca (duotono / multiply en CSS). Combinatoria:
  40 fondos × recoloreo × 3 estilos = cientos de resultados percibidos.
- Automatizar la web de ChatGPT desde la app queda DESCARTADO (contra TOS, frágil).

## Módulo de foto 1x1

Cuando el cliente aprueba y va a producción, se necesita la foto carnet de cada persona.
Módulo aparte que **reusa la lógica de recorte de fondo del fotochecks-editor**:
- Entrada: foto de la persona.
- Salida: foto 1x1 normalizada (fondo blanco/neutro, encuadre carnet, 300 dpi) lista
  para CardPresso / impresión.
- Es independiente del generador de mockups (se usa en otra etapa del flujo de venta).

## Entregables por corrida (igual que hoy, mejor hechos)

En `salida/<Cliente>-<fecha>/`:
1. `brief-presentacion.png` — las 3 direcciones (frontal + reverso) con cabecera y pie
   DISECOD, para mandar por WhatsApp al cliente. (Hoy = `lamina-presentacion.png`.)
2. `direccion-1..3-<nombre>.png` — cada propuesta en grande.
3. `para-diseno/` — caras limpias full-bleed CR80 300 dpi (base para el diseñador /
   CardPresso). Se conserva tal cual del motor actual.

## Arquitectura

```
codigo/
├── motor.py        # orquestación: logo → color/paleta → datos para la plantilla
├── plantillas/     # HTML/CSS por dirección de arte (1 archivo por estilo)
├── render.py       # Playwright: HTML → PNG (deviceScaleFactor para 300 dpi)
├── fondos/         # (Fase 2) banco de fondos pre-generados
├── foto1x1.py      # módulo de recorte/normalización de foto carnet
├── app.py          # GUI tkinter (igual de simple que hoy)
└── (assets: fuentes, foto-persona, logo DISECOD)
```

- Se conserva: cargar_logo() y paleta_del_logo() (ya funcionan bien), el launcher de
  auto-update, el empaquetado PyInstaller, el flujo del vendedor (logo + nombre + Generar).
- Cambia: la capa de dibujo (Pillow → HTML/CSS + Playwright).
- **Nueva dependencia en el exe:** Chromium de Playwright (~170 MB). Sube el tamaño del
  instalador; a evaluar en el plan si se hornea o se instala una vez. (Riesgo principal.)

## Cómo lo usa el vendedor (sin cambios de fricción)

1. Abre "Mockups DISECOD".
2. Escribe el nombre del cliente, elige el logo.
3. "Generar" → en segundos se abre la carpeta con el brief + las 3 direcciones + para-diseno.
4. (Si el cliente pide foto 1x1) usa el módulo de foto aparte.
Todo offline para componer; online solo si algún día se activa la Fase 3 (API).

## Costos

| Fase | Qué agrega | Costo por cliente | Costo recurrente |
|------|-----------|-------------------|------------------|
| 1 | HTML/CSS, fondos CSS | $0 | $0 |
| 2 | Banco de fondos (ChatGPT Plus manual) | $0 | $0 (usa suscripción ya pagada) |
| 3 (opcional) | Fondo único en vivo (API Ideogram) | ~$0.03–0.10 | según uso |

## Plan por fases

- **Fase 1:** motor HTML/CSS + Playwright, 3 direcciones frontal/reverso, brief DISECOD,
  para-diseno, recoloreo por color de marca. Reemplaza a Pillow. (Gratis.)
- **Fase 2:** banco de fondos + recoloreo + selección por logo. Módulo foto 1x1. (Gratis.)
- **Fase 3 (opcional):** API de imagen para fondo único en vivo.

## Riesgos y mitigaciones

- **Tamaño del instalador (Chromium ~170 MB):** evaluar en el plan hornear vs instalar
  una sola vez; el código sigue llegando liviano por auto-update.
- **Velocidad de render:** Playwright tarda ~1–3 s por página; aceptable. Cachear el
  navegador entre las 3 direcciones.
- **Fuentes web (Playfair/Inter):** hornearlas como assets locales para no depender de
  internet al renderizar.
- **Calidad del recoloreo de fondos:** validar con logos pálidos, oscuros y monocromos
  (los 9 casos de prueba que ya usamos).

## Decisiones a confirmar por Diego (en la revisión)

1. ¿3 direcciones de arte (vs los 9 actuales)? — propuesto: sí, 3 fuertes.
2. ¿Las 3 direcciones propuestas (Aurora / Editorial / Glass) o quieres otra vibra?
3. ¿La foto 1x1 va dentro de esta app o como módulo separado del flujo? — propuesto: módulo separado.
4. ¿Arrancamos por Fase 1 sola (gratis) y luego Fase 2? — propuesto: sí.

## Fuera de alcance (YAGNI por ahora)

- Fase 3 (API en vivo) hasta que Diego la pida.
- Widget web v2 en fotochecks.pe (proyecto aparte).
- Automatización de la web de ChatGPT (descartado por TOS).
