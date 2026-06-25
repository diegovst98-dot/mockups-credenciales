# Editor visual de la pestaña "Personalizar" — diseño

> Fecha: 2026-06-24
> Estado: APROBADO por Diego (brainstorming). Siguiente paso: plan de implementación.
> Reemplaza el enfoque de "editor de campos estático" (v25) por un **editor de capas
> arrastrable** dentro de la misma pestaña Personalizar.

## 1. Contexto y propósito

La app MockupsDISECOD la usa **el vendedor** para mandarle al cliente, por WhatsApp y en
plena conversación, una propuesta visual de su credencial con su marca. La pestaña
**Personalizar** (v25) ya deja editar 1 de 18 modelos con campos etiqueta:valor, color,
posición de logo y export PDF/PNG, con preview en vivo (mismo motor → WYSIWYG).

**Reencuadre clave de Diego (2026-06-24):** esta es una **herramienta del vendedor**, no la
credencial final. **La diseñadora (Mirza) hace el arte final aparte** (CardPresso → Evolis).
Por lo tanto el mockup se libera de tener que ser imprimible-perfecto y debe ser **lo más
personalizable posible**: mover el logo, mover/cambiar la foto, agregar campos, acomodar
todo en vivo, **sin que se destruyan las imágenes** (sin pixelar ni deformar).

## 2. Problema con lo que hay hoy

1. **Poca flexibilidad de colocación.** Hoy el layout de cada modelo es fijo; el vendedor
   no puede mover el logo/foto/textos para adaptarse a lo que el cliente pide en vivo.
2. **La foto no se puede cambiar.** Siempre es la misma cara de stock → el cliente no se
   "ve a sí mismo".
3. **Datos de relleno obviamente falsos** en la pieza que ve el cliente (DNI 45678123,
   teléfono (01) 700 0000, QR que no escanea) → se siente plantilla genérica.
4. **El trabajo del vendedor se pierde:** no hay guardar/reabrir; el nombre de empresa va
   suelto (se puede exportar "Cliente"); dos cotizaciones del mismo cliente se pisan.

## 3. Decisión de producto

Convertir Personalizar en un **editor visual de capas** con esta filosofía:
**parte de una plantilla linda + edición libre con red de seguridad.**

- El vendedor elige 1 de los 18 modelos como **punto de partida** (no lienzo en blanco).
- Encima, el **logo, la foto y cada bloque de texto** son objetos que se **arrastran y
  estiran con el mouse**.
- **Guías de alineación + snap** ayudan a que no salga descuadrado.
- Todo se compone a **máxima resolución** → no se pixelea al mover ni estirar.
- **Lo que se ve es lo que se exporta** (regla WYSIWYG, intacta).

### Por qué este enfoque (y no otros)
- **No lienzo en blanco:** el vendedor no es diseñador; partir de algo lindo lo hace rápido
  y a prueba de feo.
- **No "mini-CardPresso" completo:** se evita duplicar la herramienta del diseñador y el
  alto mantenimiento para un equipo chico. La libertad se acota con plantilla base + guías.
- **No recorte de foto por IA en la app del vendedor:** metería un modelo de ~176 MB y haría
  pesada la app. El encuadre manual (mover + zoom dentro del marco) es suficiente para un
  mockup de venta.

## 4. Alcance

### Entra en esta entrega
- Editor de capas: arrastrar y redimensionar **logo, foto y bloques de texto** (nombre,
  cargo, cada campo) sobre la plantilla elegida.
- **Guías de alineación + snap** al mover.
- **Cambiar la foto:** subir la foto real del cliente/empleado + **encuadre manual**
  (mover/zoom dentro del marco) + **2-3 caras de muestra** elegibles como respaldo.
- **Campos** etiqueta:valor (ya existe) ahora también arrastrables.
- **Color de marca** (auto del logo / manual) — se mantiene.
- **Guardar / reabrir** la cotización (archivo local con nombre de cliente + fecha).
- **Limpieza de datos falsos** por defecto (DNI/teléfono/web/QR ficticios fuera o vacíos;
  no se exportan si no se llenan).
- **Un solo botón "Exportar para WhatsApp"** que genera PNG + PDF de una pasada, a máxima
  resolución, con nombre de archivo trazable (cliente + fecha-hora, no se pisan).
- Bloquear el export si la empresa quedó vacía / "Cliente".

### NO entra (2da ola — depende de definición de negocio de Diego)
- **Franja con CTA / contacto DISECOD / precio o packs** impresa fuera de la tarjeta.
  Requiere definir texto, número oficial (catálogo-wa) y packs.
- **Pase automático de datos a Mirza** para CardPresso (carpeta de cara limpia + archivo de
  datos exactos). Requiere validar con Mirza el formato que ella usa.
- Medición del funnel en Kommo (mockup → cotizado → cerrado).

### Fuera de alcance (descartado)
- Lienzo en blanco total; segundo recoloreo del logo; recorte de fondo por IA en la app del
  vendedor; convertir la app en un editor tipo CardPresso completo.

## 5. Arquitectura (enfoque híbrido)

Para dar arrastre/estiramiento **sin reescribir las 18 plantillas** ni romper lo que ya se
ve bonito:

- **La plantilla aporta el FONDO/estilo.** Se genera el fondo decorativo del modelo (sin los
  datos editables) como imagen de alta resolución, con el motor actual (HTML → Edge), y se
  **cachea** por modelo+color.
- **El logo, la foto y los textos son CAPAS separadas**, posicionadas y dimensionadas por el
  vendedor.
- **Un único compositor (Pillow) arma preview y export** a partir de las mismas capas y
  coordenadas → garantiza WYSIWYG (preview = lo que se manda). El export es ese mismo
  compositor a resolución completa.
- **Lienzo interactivo (tkinter Canvas)** muestra el fondo + asas de arrastre/redimensión y
  las guías; al soltar, recompone (rápido, sin re-render HTML por cada movimiento).

### Componentes
- `estado.py` — ampliar `Ajustes` para guardar, por cada capa (logo, foto, cada texto/campo),
  su **posición y tamaño normalizados** (0–1 respecto a la tarjeta) + `foto` (ruta/elección)
  + `empresa` (cablear de verdad). Mantener `aplicar_cambios` / `filas_validas`.
- **Compositor de capas** (módulo nuevo, p. ej. `lienzo.py`) — recibe fondo + capas + ajustes
  y devuelve la imagen final a cualquier resolución. Reproduce el estilo de los datos
  (etiqueta en color de marca, valor, fuente compacta por cantidad) que hoy hace la plantilla.
- `plantillas/` — cada modelo expone su **fondo sin datos** + las **zonas/anclas por defecto**
  (dónde nacen logo, foto y datos) para sembrar las posiciones iniciales del editor.
- `motor.py` — `render_modelo` y `exportar_personalizado` pasan a usar el compositor de capas.
- `app.py` — pestaña Personalizar con el Canvas interactivo, asas, guías/snap, botón "Subir
  foto" + encuadre, "Guardar/Reabrir cotización", y "Exportar para WhatsApp".
- Persistencia: serializar `Ajustes` + empresa + ruta de logo/foto a **JSON local** con
  nombre cliente + fecha.

### Riesgo técnico principal a resolver en el plan
Reproducir en el compositor (Pillow) el **estilo de los datos** que hoy hace la plantilla
HTML (color de etiqueta = marca, valor, "fuente compacta por cantidad") para que el resultado
sea idéntico a lo que el cliente espera. La Fase 1 debe **probar el compositor en un modelo y
mirarlo** antes de escalar a los 18.

## 6. Reglas fijas del proyecto a respetar

- 🔒 **El logo del cliente NUNCA se recolorea** (solo mover/escalar/posicionar; su tinta real).
- 🔒 **WYSIWYG:** lo que se ve en el preview = lo que se exporta (mismo compositor).
- **App liviana:** no meter dependencias pesadas nuevas (sin rembg/modelos) → el .exe del
  vendedor sigue ligero; si cambian librerías, recompilar el exe (regla del build).
- **Auto-update con disciplina:** cualquier publicación llega a la PC del vendedor en plena
  venta → **Diego prueba el zip antes que Mirza**.
- **Renderizar y MIRAR** en cada hito (tests verdes ≠ experiencia; es la lección recurrente
  del proyecto).
- **Compat del exe viejo:** imports nuevos en `codigo/` → revisar si hay que forzarlos en
  `launcher.py`; imports que el exe viejo no trae (p. ej. ImageTk) → diferidos.

## 7. Fases

1. **Motor de capas con UN modelo.** Compositor Pillow (fondo + logo/foto/texto como capas),
   Canvas con arrastrar/estirar + guías/snap, export nítido. Verificar mirando el render.
2. **Los 18 modelos + foto.** Anclas por defecto de los 18; subir/cambiar foto con encuadre
   manual + caras de muestra. Verificar con contact-sheet de los 18.
3. **Persistencia + limpieza + export único.** Guardar/reabrir cotización (JSON con
   cliente+fecha); quitar datos falsos por defecto; un solo botón export PNG+PDF a full-res;
   bloquear export con empresa vacía/"Cliente".
4. **Pulido + empaque.** Mirar los 18, ajustes finos, empaquetar el .exe (recompilar si
   cambian librerías), zip instalador. **Diego prueba antes que Mirza.**

## 8. Criterios de éxito

- El vendedor puede, partiendo de un modelo, **mover y estirar logo, foto y campos** con el
  mouse, con guías que alinean, **sin pixelar**.
- Puede **subir y encuadrar la foto** del cliente (o elegir una de muestra).
- Lo que ve en pantalla es **idéntico** a lo que exporta (PNG+PDF, un botón).
- Puede **guardar y reabrir** una cotización; los archivos no se pisan.
- La pieza que recibe el cliente **no muestra datos obviamente falsos** ni dice "Cliente".
- El .exe sigue **liviano** y se publica respetando la disciplina de prueba.

## 9. Riesgos y mitigaciones

- **Foto mal encuadrada/fea:** empezar con encuadre asistido (marco fijo + mover/zoom) y
  previsualización antes de exportar; caras de muestra de respaldo.
- **Romper WYSIWYG** al separar capas: un único compositor para preview y export; probarlo
  en Fase 1 mirándolo.
- **Toca el motor de una app en producción:** fases chicas, verificar mirando, y la regla
  "Diego prueba el zip antes que Mirza".
- **Mantenimiento (equipo chico):** acotar la libertad con plantilla base + guías; no
  convertirlo en CardPresso.
- **Dato personal local** (foto/DNI en JSON en la PC): mantenerlo local y simple, sin nube.
