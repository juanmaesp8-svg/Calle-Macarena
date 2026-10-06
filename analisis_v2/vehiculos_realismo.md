# Vehículos procedurales, revisión v2

Se ha sustituido exclusivamente `modelo/vehiculos.py`. API `make_car(name, center_xy, size_xy, collection, mats, z=0)` y retorno `parent/objects/bbox_xy_m/altura_visual_m` conservados. Cada vehículo sigue mirando hacia +Y, con su centro original y caja exterior exacta que incluye retrovisores. No se modificó arquitectura, cámaras, constructor, vegetación ni render.

La planimetría determina centros, orientación y símbolo XY. El sedán no reproduce una marca ni un vehículo especificado por el proyecto. Su altura de 1,45 m y todos los detalles de automoción son accesorios de visualización y quedan identificados en las propiedades del padre. Generación matemática original; no se descargaron activos ni se atribuyeron licencias externas.

## Cambios

- Carrocería de 61 secciones longitudinales × 48 muestras transversales, interpolación cúbica monótona sin sobreoscilación, hombros continuos, capó/maletero abombados y remates convexos.
- Cuatro pasos de rueda abiertos mediante booleanos exactos y rebordes finos; ninguna rueda insertada en una caja cerrada.
- Techo cambrado, parabrisas y luneta curvos, cuatro ventanillas curvadas de espesor cerrado, juntas y pilares A/B/C separados.
- Habitáculo con cuatro asientos, respaldos, reposacabezas, costuras, consola, salpicadero y volante. Reutiliza `cuero_claro`, `tejido_tapizado` o `tejido` si están disponibles.
- Neumáticos de perfil axial ancho, hombros/flancos curvos, canales y laminillas finas; llantas de diez radios volumétricos con barril, buje, tornillos, rotor y pinza.
- Faros de reflector y lente separada, firma diurna, pilotos rojos y parrilla que siguen el remate convexo. Los rayos geométricos confirman que las ópticas exteriores quedan fuera de la chapa.
- Retrovisores convexos, tiradores enrasados, molduras y juntas de puertas. Materiales editables PBR sin textura externa ni logotipos.

## Verificación geométrica real

Blender 4.3.2, escena `--factory-startup` vacía. Tres instancias generadas, dos canónicas y una con caja alternativa 2,20 × 5,10 m. No se hicieron renders.

| Instancia | Caja XYZ evaluada, m | Centro XY, m | Caras evaluadas | Triángulos | Aristas no manifold de chapa |
|---|---|---|---:|---:|---:|
| Coche 01 | 2,084000587×4,934000015×1,450000048 | 5,886334896; 3,781425953 |29590|58700|0|
| Coche plata 02 | 2,083999634×4,934000015×1,450000018 |9;8|29590|58700|0|
| Escala alternativa |2,200000048×5,099999905×1,450000048|0;0|29590|58700|0|

Error máximo observado de caja canónica: 0,000000587 m, propio de precisión numérica; no expresa exactitud del proyecto. Centros y plano inferior `z` correctos también al trasladar la segunda instancia a +0,15 m.284 objetos editables por vehículo. El padre únicamente escala XY para cajas alternativas.

La carrocería tiene volumen orientado positivo y cero aristas no manifold. Las seis superficies acristaladas evaluadas y las cuatro lentes ópticas tienen volumen positivo y cero aristas no manifold. Distancia mínima de piel óptica a chapa en dirección longitudinal: faros 9,109 mm; pilotos 6,100 mm. Espesores de vidrio y lentes se orientan hacia el interior.

Una calibración final propia del accesorio corrige mínimos espesores/proyección de ópticas y laminillas: X × 0,999999947; Y × 0,996008013; Z × 1,000690163. Sólo afecta al sedán y garantiza la envolvente pedida; no afecta a elementos arquitectónicos.

El test editable está en `/tmp/vehiculos_v2_test.blend`; no es un entregable del proyecto. La valoración fotográfica debe realizarla el responsable de los renders con el modelo definitivo y su iluminación. El generador no cambia ninguna configuración de render.
