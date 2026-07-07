# Loop de color — Iteración 2 (2026-07-06)

Punto de partida: los 4 defectos restantes de `iteracion-1.md`. Hojas de contacto:
`salida\_loop\famosos\iter1-despues\` (antes) vs `salida\_loop\famosos\iter2-despues\`
(después). Suite: **168 passed, 1 skipped** (incluye `test_logo_cliente_no_se_recolorea`).
Tests nuevos: `tests\test_paleta_iter2.py` (15).

## Qué se arregló

### 1. El 2º color REAL ahora pinta área media (acc2_real ≠ acc2 humo)
- `motor.paleta_roles` expone el rol **`acc2_real`**: el 2º cluster real del logo
  (legible) o `None` si no existe. El humo derivado sigue viviendo solo en `acc2`.
- Nueva variable CSS **`--acc2m`** (+ `--txtacc2m`) en `plantillas/base.py`: si el
  `sec` del combo tiene MATIZ distinto (≥30°) y color real → `marca_legible(sec)`;
  si es humo/derivado → cae exactamente a `--prim` (render idéntico al de siempre).
- Dos modelos del top la usan en área media: **mh1 Ejecutiva** (banda del cargo) y
  **mv6 Minimalista** (banda b2; su combo pasó de `("acc","carbon")` a `("acc","acc2")`).
- Evidencia: **Pepsi** = bandas azul + ROJA en mv6 y cargo rojo en mh1 (por fin es
  Pepsi bicolor); **BCP** = banda naranja real en mv6 + cargo naranja en mh1;
  **Interbank** = verde + banda azul real; **Cinemark** = roja + banda DORADA
  (estilo marquee de cine). Monocolores (Coca, Spotify) idénticos: el humo no pinta.

### 2. Estrella color-forward para marcas vivas
- `curaduria.es_viva(prim)` (S≥0.50, L≤0.62): con marca viva, los modelos
  **color-forward** (`mh7`, `mh2`, `mv6`) suben a score 10 → la estrella siempre
  lleva el color del cliente y rota entre los tres por hash (variedad intacta).
  Premium sigue en el top-6 pero ya no se roba la estrella (caso McDonald's/Coca).
- Evidencia: Coca-Cola antes estrella=Premium (crema) → ahora mv6 rojo; McDonald's
  estrella mv6 amarillo vivo.

### 3. Tope anti-neón (Spotify)
- En `paleta_roles`: acento con S>0.75 **y** luminancia>0.45 → baja a L≤0.44, S=0.70
  (verde rico imprimible en Evolis plano, no ácido). **Excluye matices luminosos
  40–90°**: el amarillo McD ES la marca y su legibilidad la da el texto oscuro —
  la 1ª corrida lo volvía ocre y se revirtió (test `test_acc_amarillo_iconico_no_se_apaga`).
- Los saturados oscuros (rojo Coca lum 0.19, azul Pepsi 0.10) no se tocan.
- Evidencia: hoja-spotify iter2 = bandas verde profundo con blanco, ya no chillonas.

### 4. `marca_legible` con matices luminosos (texto con peso)
- Matiz 40–90° con S≥0.25 → corre −12° al ámbar y profundiza a tope 0.20 (antes
  0.32): el nombre en Premium ya no queda mostaza débil sobre crema, sino marrón
  dorado editorial. Evidencia: hoja-mcdonalds Premium (nombre con peso) y Cinemark
  (dorados más ricos en hairlines/cargo, sin perder el carácter).

## Antes / después por caso

| Marca | Antes (iter1) | Después (iter2) |
|---|---|---|
| Pepsi | rojo solo en swatch/hairline | mv6 estrella azul+banda ROJA; cargo mh1 rojo — bicolor real |
| BCP | naranja invisible | banda naranja mv6 + cargo naranja mh1 |
| McDonald's | estrella a veces crema; nombre mostaza débil | estrella mv6 amarillo vivo; nombre Premium marrón dorado |
| Spotify | bandas un pelo neón | verde rico (L 0.44 / S 0.70), matiz intacto |
| Cinemark | ya bien | mejor: banda dorada real en mv6 (marquee) |
| Interbank | sano | sano + banda azul real en mv6 (bonus del fix 1) |
| Coca-Cola | sano | idéntico en color; estrella ahora color-forward |

## Defectos restantes

Mirando las 7 hojas con ojo de director de arte, **no encuentro defectos
transversales nuevos**. Matices menores (gusto, no defecto): (a) el cargo naranja
de BCP en mh1 es llamativo — es el color real del banco, decisión defendible;
(b) `es_viva` usa umbral duro S=0.50 — un logo justo en la frontera cambia de
régimen, sin efecto feo observado.

**Veredicto: candidato a fascinante — listo para juicio final.** Rendimientos
decrecientes: los cambios que quedan son de gusto fino por marca, no reglas
transversales.
