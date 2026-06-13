# Fase 2b — Banco de fondos premium con ChatGPT Plus (opcional, costo $0)

> La Fase 2 ya entrega **variedad de fondos gratis** (3 variantes CSS por dirección,
> elegidas según el cliente — ver `codigo/plantillas.py`, `_BG_AURORA/_BG_GLASS/_BG_EDIT_BANDA`).
> Este documento es para cuando quieras subir aún más el "wow" usando el **ChatGPT Plus
> del equipo** (sin API, sin costo extra) para generar fondos de imagen reales.

## Idea

Generas a mano, una sola vez, una librería de **fondos abstractos** (sin logo, sin texto,
sin personas) y la app los recolorea al color de cada marca y los usa de fondo. Con eso
las direcciones Aurora y Glass pasan de gradiente CSS a textura/arte de verdad.

## Cómo generar los fondos (en chat.openai.com, plan de $20)

1. Abre ChatGPT → modo imagen.
2. Pega uno de estos prompts. Pide **fondo cuadrado y vertical** (2 tamaños) y **8 variaciones**.
3. Descarga los PNG y guárdalos en `codigo/fondos/` con nombres como `aurora-01.png`,
   `glass-03.png`, etc. (la dirección a la que sirven + número).

### Prompts (en gris/neutro para que el recoloreo funcione)

- **Aurora (oscuro premium):**
  > "Abstract dark premium background for a corporate ID card, deep charcoal with soft
  > radial glow, subtle mesh gradient, very fine film grain, no text, no logos, no people,
  > elegant, minimal, high resolution. Monochrome dark gray so it can be recolored."

- **Glass (color, glassmorphism):**
  > "Abstract soft gradient background with blurred light blobs and glassmorphism feel,
  > smooth, premium, no text, no logos, no people. Neutral gray tones for recoloring,
  > high resolution, both square and vertical."

- **Editorial (claro/marfil):**
  > "Minimal off-white editorial background with a subtle paper texture and one soft
  > diagonal band of light gray, lots of negative space, no text, no logos, premium,
  > high resolution."

**Reglas:** fondos en gris/neutro (se recolorean al color de marca), sin texto, sin logo,
sin personas, sin marcas de agua. ~5 prompts × 8 variaciones = 40 fondos en una sesión.

## Cómo se integrarían (trabajo futuro, ~media tarde)

En `codigo/plantillas.py`:
1. Al construir el contexto, si existe `codigo/fondos/<direccion>-*.png`, elegir uno por
   `variante_de(cliente)` y recolorearlo al color de marca (multiply/duotono en PIL),
   embeberlo como `data:` y usarlo de `background` en vez del gradiente CSS.
2. Si no hay fondos en la carpeta, se usa el gradiente CSS actual (degradación elegante).

Es **drop-in**: metes PNGs en `codigo/fondos/`, publicas, y la app los reparte por
auto-update. No hay que tocar el flujo del vendedor.

## Fase 3 (opcional, con costo): fondo único en vivo

Si algún día quieres un fondo **irrepetible por cliente generado en el momento**, ahí sí
entra una API de imagen (Ideogram ~$0.03/img). El resto del sistema no cambia: solo la
fuente del fondo. Se evalúa solo si el banco pre-generado se queda corto.
