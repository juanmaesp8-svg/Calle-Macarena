# Mobiliario y vehículos V2 — geometría para visualización realista

Se actualiza únicamente la construcción de accesorios en `modelo/vegetacion_mobiliario.py` desde `_box` y en `modelo/vehiculos.py`. No se modifican muros, huecos, cubiertas, posiciones del proyecto, constructor ni funciones de vegetación. Todas las alturas y detalles de estos accesorios permanecen identificados como decisiones de visualización, no como cotas arquitectónicas.

## Mobiliario

Los sofás y butacas tienen bastidores tapizados, apoyabrazos, cojines separados de asiento/respaldo y almohadones contenidos en la huella original. Los cojines son mallas cerradas de superficie suave, con volumen, pequeños pliegues de compresión de 1–2 mm y vivos cosidos. Se elimina el aspecto de cubos achaflanados. Los ottoman se distinguen de las butacas y no reciben respaldo o brazos inventados.

Las sillas utilizan patas torneadas ligeramente abiertas, montantes curvos, respaldo de madera laminada curva y almohadillas de asiento/respaldo. Las mesas tienen tablero fino con radio de canto real, faldones discretos y patas cónicas. Las camas incorporan colchón cerrado, cabecero acolchado, almohadas y ropa de cama por capas con pliegues milimétricos.

Los materiales se coordinan con el módulo de materiales V2: `tejido_tapizado`, `tejido_sabanas`, `madera_mesa`, `madera_patas` y `metal_mobiliario`. Se conserva compatibilidad con las keys anteriores. La veta de tablero es horizontal y la de patas/montantes vertical.

## Integración de funciones

Se conservan las API existentes de `make_sofa`, `make_bed` y `make_dining`. Nuevos helpers para sustituir los sólidos simples del constructor:

- `make_chair(name, center, size, z, collection, mats, yaw=0)`: `size` es la caja XY del mundo, incluida la rotación cardinal. Respaldo +Y con yaw0, −X con +π/2, +X con −π/2 y −Y con π.
- `make_table(name, center, size, z, collection, mats, height=.75, coffee=False)`: mantiene centro y tablero máximo del símbolo. Para mesa baja puede suministrarse altura y `coffee=True`.
- `make_sofa_l(name, footprint_xy, z, collection, mats)`: utiliza el polígono en L de la fuente, no su rectángulo envolvente macizo. Respaldos sobre bordes norte/oeste, conforme a la disposición del símbolo anterior.

Los centros de cada accesorio permanecen en los suministrados por el constructor. La huella XY se comprueba sobre mallas evaluadas, incluidos vivos, telas y piezas redondeadas. Los símbolos de silla parcialmente introducida bajo mesa mantienen su huella gráfica visible; no se declaran medidas de un fabricante a partir de esos símbolos. El comedor de piscina anterior no se crea desde este módulo: el constructor decide los elementos presentes en la nueva planta, cuyo espacio ahora corresponde al trastero.

## Comprobación geométrica

Prueba real en Blender 4.3.2 con escena vacía, sin renders. Se verificaron centro y envolvente evaluada del sofá, butaca, ottoman, cama, silla rotada 90°, mesa y conjunto de comedor. Error máximo XY inferior a 0,000002m por precisión flotante. El sofá en L produjo cero vértices fuera del polígono fuente con tolerancia de 0,00002m. Las bases permanecen a Z0. Los resultados numéricos están en `mobiliario_qa.json`.

| Accesorio | Caja XY evaluada (m) | Z evaluada (m) | Caras evaluadas |
|---|---|---|---|
| sofa | 2.700001×0.890001 | 0.000..0.862 | 20,848 |
| butaca | 0.762000×0.660400 | 0.000..0.861 | 10,468 |
| ottoman | 0.762000×0.666750 | 0.000..0.546 | 3,548 |
| cama | 1.650000×2.050000 | 0.000..1.112 | 12,106 |
| silla | 0.254000×0.387350 | 0.000..0.810 | 4,794 |
| mesa | 0.996950×1.803400 | 0.000..0.750 | 830 |
| comedor | 3.400000×2.800000 | 0.000..0.810 | 29,594 |
| sofa_L | Polígono L | 0..0,86 aprox. | 17,564 |

## Vehículos

El sedán V2 conserva API, centros, frente +Y y envolvente exacta de 2,084×4,934×1,45m. Incorpora carrocería con secciones suaves, capó/maletero curvos y extremos convexos, pasos de rueda abiertos, techo cambrado, vidrios laminados curvos cerrados, interior, neumáticos perfilados, llantas de diez radios y ópticas con profundidad real.

Pruebas de Blender 4.3.2: error máximo de caja 0,000000587m, centros conservados; ensayo de Z +0,15 y escala XY alternativa pasado. Chapa y seis vidrios tienen volumen positivo y cero aristas no manifold. Raycasts confirman ópticas delanteras al menos 9,109mm fuera de la chapa y pilotos al menos 6,100mm fuera. Cada coche tiene 29.590 caras evaluadas (58.700 triángulos) y 284 objetos. Los materiales conservan pintura con capa transparente y vidrio físico; el interior puede usar `cuero_claro`. Más detalle en `vehiculos_realismo.md`.

## Procedencia y alcance

Toda la geometría de accesorios se ha construido proceduralmente para este trabajo. No se han descargado modelos de terceros ni se atribuyen licencias CC0 a fuentes inexistentes. No se generan ni publican imágenes en esta subtarea. La evaluación fotográfica del resultado corresponde a las futuras previsualizaciones Cycles del conjunto, con la iluminación, materiales y óptica V2; estas pruebas verifican geometría y compatibilidad, no certifican todavía un render final.
