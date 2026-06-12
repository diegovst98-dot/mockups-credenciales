# Mockups de credenciales DISECOD — Spec de diseño (v1)

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
