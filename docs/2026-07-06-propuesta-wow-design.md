# Propuesta Wow — de catálogo de 18 a propuesta de agencia (design)

> Aprobado por Diego 2026-07-06. Contexto de negocio: escalón 1 del Money Model
> ("boceto gratis que asombra") — ver `claude-cerebro\playbook-ventas.md`.

## Problema (diagnóstico visual del catálogo DISECOD 25-jun)

1. Portada débil: texto chico gris flotando + marco azul hardcodeado (`ACENTO=(0,120,200)`
   en `folleto.py`) que no es del color del cliente.
2. Rótulos con caracteres sospechosos en el PDF ("Acciün", "Müdico") — verificar si es
   render o OCR, y de paso subir tamaño/calidad de captions.
3. Color único aplicado igual a los 18 → modelos de bandas grandes quedan lavados con
   tintas claras (lavanda DISECOD); gris huérfano en mh4 (Gaio).
4. 18 modelos: el débil arrastra la percepción; menú largo paraliza.
5. Nombres internos visibles ("Böka", "Rosestore", "Vegetata").

## Solución

- **Curaduría automática** (`plantillas/curaduria.py`): cada modelo declara afinidades
  (necesita acento oscuro / tolera pastel / score base). Con la paleta del cliente se
  eligen los TOP 6 (1 estrella + 5 alternativas). Los 18 siguen disponibles en Personalizar.
- **Folleto v2** (`folleto.py`): portada de agencia con el color del cliente (bandas
  planas, logo intacto en zona clara), página "Nuestra recomendación" (estrella grande),
  alternativas con aire (2-3 por página), captions con **nombres comerciales**, cierre
  CTA: "¿Cuál le gustó? Se lo preparamos con los datos de su equipo".
- **Color 2.0** (`motor.py`): `paleta_marca(prim, sec)` con regla anti-lavado (tinta
  clara → bandas usan versión profunda saturada; fondos la clara). Consumida por
  `generar()` y `render_modelo()` (consistencia con Personalizar). Fix gris de mh4.
- **Nombres comerciales**: mapping central clave→nombre cliente (en curaduria.py),
  usado SOLO en el folleto (el registro interno no cambia).

## Qué NO cambia

Motor HTML→Edge, los 18 modelos y sus claves, pestaña Personalizar, `para-diseno\`,
auto-update, y las 🔒 reglas fijas (logo jamás recoloreado, colores planos Evolis,
sin placas tras el logo).

## Validación

Regla de oro del proyecto: **renderizar y MIRAR**. Catálogo completo con 3 logos de
tintas distintas (lavanda DISECOD, uno rojo/saturado, uno oscuro) revisado visualmente
antes de publicar. Publicación (publicar.py) solo con OK de Diego sobre los renders.
