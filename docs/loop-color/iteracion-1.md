# Loop de color — Iteración 1 (2026-07-06)

Banco: 10 logos famosos (Wikimedia Commons, uso interno de prueba) en `entrada\famosos\`:
cocacola, pepsi, mcdonalds, bbva, bcp, interbank, cinemark, spotify, apple, nike.
Hojas de contacto: `salida\_loop\famosos\iter1-antes\` (antes) y `iter1-despues\` (después).
Herramienta: `tools\_hoja_famosos.py` (paleta + top-6 renderizado + swatches de roles).

## Crítica de director de arte (caso por caso)

| Marca | Veredicto | Defecto concreto | Causa probable | Fix propuesto |
|---|---|---|---|---|
| Coca-Cola | ✅ SIENTE Coca-Cola (rojo vivo + prof granate excelente) | acc2 fallback = marrón (130,80,53): swatch sucio junto al rojo vivo | análogo matiz+25° (rojo→naranja) y `marca_legible` lo apaga a marrón | acc2 derivado = MISMO matiz profundo apagado, no matiz inventado |
| Pepsi | ⚠️ salió marca ROJA (Pepsi es azul) | dominante = rojo (235,32,60); el azul quedó relegado a acc2 fino | bicolor casi 50/50 (rojo n=5204 vs azul n=3590); gana por presencia cruda de px | near-parity (≥60%): el matiz más PROFUNDO (menor L) es la estructura/dominante; el claro es acento |
| McDonald's | ⚠️ pasable pero turbio | (a) prof = mostaza dijon (143,114,0) — el "profundo" de amarillo es oliva/mostaza sucia; (b) acc2 = verde oliva (114,130,53) militar, nada McDonald's | (a) bajar L a matiz 60° cae en oliva; (b) análogo +25° de amarillo = oliva | (a) matices luminosos (40–90°): profundizar corriendo el matiz hacia ámbar (−12°) = marrón dorado rico; (b) mismo fix de acc2 |
| BCP | ✅ SIENTE BCP (azul + carbón) | el naranja real (249,106,83) queda solo en hairlines acc2 — casi invisible en el top-6 | COMBOS solo alimenta acc2 en detalles finos | anotado para iteración 2 (rol de acento secundario con más presencia) |
| Interbank | ✅ excelente — verde protagonista, azul real de acento | — | — | — (vigilar que el fix de Pepsi NO voltee Interbank: verde L=0.32 vs azul L=0.33, el verde sigue siendo el profundo) |
| BBVA | ✅ sobrio, corporativo, es BBVA | acc2 índigo (53,63,130) inventado (análogo), pasable pero no de marca | análogo +25° | mismo fix de acc2 |
| Cinemark | ✅ SIENTE Cinemark | acc2 dorado REAL del logo bien capturado — caso de éxito del v33 | — | — |
| Spotify | ✅ verde clavado (30,216,96) | verde muy luminoso en bandas de mv6/mh1 queda un pelo neón (menor) | acc se usa tal cual en áreas medianas | observar tras el fix de luminosos; iteración 2 si persiste |
| Apple | ✅ carbón elegante (ojo v33 funciona) | — | — | — |
| Nike | ✅ idem Apple | — | — | — |

## Las 3 mejoras transversales elegidas (iteración 1)

1. **acc2 armónico** (`motor.paleta_roles`): el fallback análogo (+25°) inventa matices
   ajenos y sucios (oliva en McD, marrón en Coca-Cola). Nuevo: derivado del MISMO matiz,
   profundo y apagado (L 0.30, S 0.30) — humo de la marca, jamás color ajeno. Mejora
   cualquier logo monocolor.
2. **Dominante en bicolores 50/50** (`motor.paleta_del_logo`): con dos clusters de
   presencia comparable (2º ≥ 60% del 1º), la presencia cruda de píxeles decide mal
   (Pepsi roja). Regla de diseñador: el matiz más PROFUNDO (menor L) es la estructura;
   el más claro/caliente es el acento. Pepsi → azul dominante + rojo acc2; Interbank
   y BCP no cambian.
3. **Profundidad de matices luminosos** (`motor.paleta_roles`): oscurecer amarillo/lima
   (matiz 40–90°) en el mismo matiz da mostaza/oliva sucia. Nuevo: prof y carbon de esos
   matices corren el matiz ~12° hacia el ámbar (más cálido) → marrón dorado rico estilo
   editorial. Mejora amarillos, dorados y limas de cualquier logo.

## Defectos RESTANTES para la iteración 2

1. **El 2º color real de marcas bicolor casi no se ve en el top-6** (BCP naranja,
   Pepsi rojo tras el fix): acc2 solo pinta hairlines. Evaluar un combo con acc2 en
   un área media (banda de cargo, círculo) para 1-2 modelos del top.
2. **Estrella para marcas vivas**: con tintas saturadas la estrella cae a veces en
   Premium (crema + hairline) y la marca casi no se ve (McDonald's). Evaluar en
   curaduría: marca viva (S alta) → favorecer modelo color-forward (mh7/mh2) como estrella.
3. **Spotify neón**: si tras el fix de luminosos las bandas verdes siguen chillonas,
   calibrar un tope de saturación para áreas medianas (acc en bandas).
4. **Premium con marca luminosa**: el nombre en dorado/mostaza sobre crema queda débil
   (McD) — revisar el tope de `marca_legible` para matices 40–90°.
