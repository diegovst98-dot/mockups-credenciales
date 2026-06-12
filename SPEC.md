# Mockups de credenciales DISECOD — Spec de diseño (v1 + v2 visual)

> **v5 — Rediseño de dirección de arte (2026-06-12, "no me gustan para nada" de Diego):**
> las 5 plantillas se reescribieron bajo reglas estrictas de diseño: UN gesto gráfico por
> tarjeta + blanco generoso; estructura tipográfica de credencial (helper `campo()`:
> ETIQUETA versalitas con tracking + valor en bold); colores PLANOS o degradado imperceptible
> (se acabaron los degradados saturados "plástico"); oro SOLO como hairline de 2px; cero
> contornos decorativos (QR directo sobre claro, placa blanca sólida sobre color); foto
> regradada a estudio neutro (más luz, menos calidez) con encuadre ancho (cabeza con aire +
> pecho). Gestos por estilo: 1=banda lateral sólida, 2=color pleno con logo en silueta
> blanca + panel blanco curvo, 3=oscuridad plana con marco fino oro, 4=cabecera de arco
> sólida, 5=diagonal derecha. Iconitos, puntos, rombos y barridos multicapa: eliminados.

> **5 estilos (2026-06-12, pedido de Diego):** se suman **Estilo 4 — Institucional**
> (vertical claro, cabecera en arco con filo dorado, foto circular solapando el arco,
> reverso con caja dorada de valores) y **Estilo 5 — Moderno** (horizontal claro, cortes
> diagonales en esquinas, foto HEXAGONAL con contorno dorado, acentos en color de marca).
> La lámina ahora acomoda los estilos en filas de 3 (última fila centrada) y los PNG
> se nombran dinámicamente (`estilo-N-<nombre>.png`). LEEME/GUIA actualizados a 5.

> **Loop 2 — calidad ChatGPT (2026-06-12 PM):** (1) `_quitar_fondo_claro()` en cargar_logo:
> los logos JPG con fondo claro uniforme se vuelven transparentes y FLOTAN sobre la tarjeta
> (umbral adaptativo: esquinas ultra-uniformes aceptan fondos menos claros — caso Añay
> lum 0.77/var 0.0); de yapa la paleta ahora sale de la tinta real del logo. (2) Foto nueva:
> persona = "Carlos González M., Supervisor de Operaciones" (calza con los ejemplos ChatGPT
> del equipo), retrato sintético calvo CON aire real arriba → se eliminó toda la fabricación
> de fondo que deformaba el pelo (la circular usa el frame completo; la rect recorta a carnet).
> (3) Estilo 1 rediseñado: banda lateral en color de marca (foto con marco dorado + DNI pill)
> + área marfil con logo flotante alineado a la izquierda; el reverso lleva franja eco.
> pegar_logo ganó `alinear="izquierda"`. Validado de nuevo con los 7 logos.

> **Loop de mejora (2026-06-12 PM, 30 min):** (1) foto circular sin distorsión — el aire
> alrededor del retrato ahora se crea con lienzo del color del fondo + fundido suave, no
> estirando bordes; (2) regla "nunca placas/cajas detrás del logo": cabecera blanca ondulada
> en estilo 2 y silueta teñida al color de marca en fondos oscuros (estilo ChatGPT);
> (3) `marca_legible()` — piso de contraste para textos en color de marca (logos pastel);
> (4) autocontraste de silueta SOLO para JPG opacos (con transparencia rompía logos oscuros);
> (5) marcas de agua en todos los reversos, grid de puntos, líneas de campo doradas, DNI
> peruano, fuentes mínimas ≥18px (imprimible Evolis CR80). Validado con 7 logos: Unilever,
> Añay Fruits (pálido), Gestión Vertical, Frutos (verde+oro), ACME, negro puro y blanco puro.

> **v2 visual (2026-06-12):** rediseño de plantillas para acercarse al estilo "ChatGPT"
> que prefiere el equipo, manteniendo la velocidad y el texto correcto. Cambios:
> foto carnet realista (rostro **sintético** de thispersondoesnotexist, recortada la marca
> StyleGAN — no es persona real, cumple la regla), logo como marca de agua de fondo,
> ondas y acentos dorados (detecta dorados del propio logo), tipografía Playfair Display
> (licencia OFL, redistribuible) con respaldo Palatino/Georgia/Segoe, iconografía dibujada
> (maletín, credencial, escudo/check/estrella), QR sobre placa con filo dorado y lámina
> centrada. Los assets nuevos viven en `codigo\` (fuente-display.ttf, fuente-display-italic.ttf,
> foto-persona.jpg) para que el auto-update los reparta sin recompilar el exe; si faltan,
> todo degrada con elegancia. Verificado con exe congelado en frío (3 logos: verde+oro,
> azul+naranja, monocromo→lima).

> Agente #22 del roster. Diseño validado con Diego el 2026-06-11 (sesión de brainstorming).
> Decisiones tomadas por Diego: frontal + reverso (C) · estilos basados en modelos reales (A,
> carpeta `Downloads\descargasfotochecksmodelos`, ver su INVENTARIO.md) · entrega lámina + PNGs
> sueltos (C) · vendedor autónomo desde su PC (opción 1: mini-app .exe, precedente
> fotochecks-editor) · programa APARTE del fotochecks-editor · entrega directa como .exe.

## Qué hace

El vendedor elige el logo del cliente, escribe el nombre de la empresa y aprieta "Generar".
El programa produce en `salida\<Cliente>-<fecha>\`:

1. `lamina-presentacion.png` — los 3 estilos (frontal + reverso) en una sola imagen con
   marco discreto de DISECOD (logo oficial oscuro, colores de marca, contacto) para reenviar
   por WhatsApp al cliente.
2. `estilo-1-corporativo.png`, `estilo-2-fullcolor.png`, `estilo-3-premium.png` — cada
   estilo en grande (frontal + reverso lado a lado).

## Los 3 estilos (de los patrones reales del inventario)

| # | Estilo | Base real | Layout |
|---|--------|-----------|--------|
| 1 | Corporativo claro | Niubiz, S. Abogados, NGR, Los Olivos | Horizontal, fondo blanco, banda superior en color primario del logo, foto carnet, nombre/cargo/código |
| 2 | Full color | TransportPass, Saint-Pierre, Mota-Engil, infovips | Vertical, fondo en color primario, chip blanco con logo, foto circular, textos blancos |
| 3 | Oscuro premium | UCV, China Polo, Pandora negra | Horizontal, fondo casi negro, logo + línea de acento en color del logo, textos claros |

- Tarjeta CR80 a 300 dpi: 1011×638 px (horizontal) / 638×1011 (vertical), esquinas redondeadas.
- Colores: se extraen los 2 dominantes del logo (cuantización Pillow, ignorando blancos/grises
  de fondo). Contraste del texto calculado (luminancia WCAG): blanco sobre oscuro, #383838 sobre claro.
- Datos ficticios fijos: "María Fernández R.", "Coordinadora de Operaciones", "ID 00128".
  Foto = avatar genérico dibujado (silueta neutra), NUNCA foto de persona real.
- Reverso por estilo: variación simple (color sólido + logo centrado + zona QR/datos de contacto
  genéricos del cliente).

## Marco DISECOD de la lámina

Banda superior #383838 con `logo-disecod-oscuro-oficial.png` + "Propuesta de diseño — <Cliente>"
+ fecha. Pie: www.fotochecks.pe · ventas@disecod.com · Av. Arenales 1912 Of. 1304, Lince.
Acentos lila #9987F7 / verde lima #E7F849 (proporciones del manual de marca; el logo no se altera).

## Arquitectura

```
mockups-credenciales\
├── motor.py        # generación: colores, plantillas, lámina (sin GUI)
├── app.py          # GUI tkinter: nombre cliente + elegir logo + Generar + abrir salida
├── recursos\       # logo DISECOD, avatar pre-renderizado si hace falta
├── entrada\        # opcional: logos que deja el vendedor
├── salida\         # resultados por cliente-fecha
└── MockupsDISECOD.spec / instalar.bat / publicar.bat  (empaquetado estilo fotochecks-editor)
```

- Python 3.12 + Pillow (sin navegador, sin API de Claude, sin internet). Fuentes Segoe UI del
  sistema (presentes en todo Windows; no se redistribuyen dentro del .exe).
- PyInstaller --onefile --windowed → `MockupsDISECOD.exe`.

## Manejo de errores

- Logo ilegible/corrupto → mensaje claro en la GUI, no genera.
- Logo con fondo blanco → se recortan bordes blancos automáticamente (trim) antes de medir colores.
- Logo monocromo/negro → paleta de respaldo: gris #383838 + acento lila DISECOD.
- Nombre vacío → usa "Cliente".

## Verificación

- Correr motor con ≥2 logos reales distintos (claro y oscuro) e inspeccionar PNGs visualmente.
- Probar el .exe compilado en frío (doble clic, generar, abrir salida).

## Etapas de entrega

1. **Hoy**: motor + GUI + .exe para que Diego pruebe.
2. **Pulido**: iteraciones de plantilla según feedback de Diego/vendedor (recompilar y repartir
   con publicar.bat).
3. **Instalación PC vendedor**: instalar.bat + mini guía PDF (como el fotochecks-editor).
