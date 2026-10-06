# Vegetación V2 — revisión de realismo

Se ha revisado la imagen V1 `05_Piscina_hacia_vivienda.png` y el código que produjo sus plantas. La palmera tenía 144 placas triangulares prominentes superpuestas al tronco, frondas muy repetitivas y pinnas casi coplanares. Los olivos tenían 3.420 hojas repartidas alrededor de 18 extremos de rama; la superficie foliar era insuficiente para presentar una copa continua desde las cámaras generales.

## Módulo incorporable

`modelo/vegetacion_v2.py` es independiente. Mantiene estas interfaces y el formato de devolución:

```python
from vegetacion_v2 import make_palm, make_olive, make_shrub
objetos = make_palm(nombre, xy, altura_m, coleccion, materiales)
# objetos[0] es el Empty raíz; objetos[1:] son las mallas.
```

El builder puede seguir importando mobiliario del módulo anterior, y sólo sustituir la importación de las tres funciones de vegetación. Este trabajo no cambia `vegetacion_mobiliario.py`, el builder, los datos de planta ni las posiciones de ninguna plantación.

## Geometría y materiales

- **Palmeras:** estípite con 64 segmentos alrededor y 96 a lo largo, cicatrices integradas de hasta 7 mm de relieve, corteza con grano y microrrelieve; se retiran las piezas triangulares salientes. Se generan 39 frondas de tres generaciones y tres lanzas nuevas. La curvatura, azimut, longitud, inclinación de pinnas y color presentan variación reproducible. Las 56 parejas de pinnas en las frondas exteriores y 43 en las jóvenes dan volumen a la copa manteniendo su radio máximo.
- **Olivos:** tronco curvado, doce ramas principales, sesenta secundarias y trescientas ramillas. Las 18.000 hojas lanceoladas se disponen por parejas opuestas y alternan orientación entre nudos, a lo largo de las ramillas. Se evita el conjunto de hojas flotantes alrededor de una rama desnuda. El haz es verde apagado y el envés gris plateado mediante el lado real de la superficie. La copa sigue siendo porosa y tiene tamaño contenido.
- **Arbustos:** lentiscos bajos con 36 ramillas y 1.296 hojas ovales, con variación de porte y orientación. El radio corresponde al parámetro del asset, evitando que el follaje invada una extensión mayor del jardín.
- **PBR botánico:** corteza procedural en coordenadas físicas; doble cara de la hoja, UV individual, nervadura tenue, rugosidad cuticular, microrrelieve y un pequeño componente de luz transmitida. Los colores varían en seis intervalos discretos por especie. Estos materiales se crean en el nuevo módulo y no requieren cambios en `materiales.py`.

## Conservación del modelo

La raíz XY/Z permanece exactamente en el parámetro recibido. Para los cuatro árboles de V1 se conservaron los radios máximos medidos en sus vértices, además de las alturas: 2,373479 m y 2,064219 m para las palmeras; 1,850478 m y 1,697387 m para los olivos. La envolvente de la copa se ajusta sin trasladar su raíz. Estas medidas pertenecen a los assets de paisajismo, no son cotas arquitectónicas de los planos. La distribución interna del follaje cambia para mejorar su representación.

La vegetación se entrega agrupada en tres mallas por palmera y dos por olivo o arbusto, además de su Empty. El coste de la plantación V1 completa —dos palmeras, dos olivos y veinte arbustos— es aproximadamente **467.912 caras**; la generación de los seis assets de comprobación tardó 6,56 s. Es una carga contenida para Cycles CPU y evita miles de objetos separados por hoja. Las geometrías no emplean planos con recortes transparentes, por lo que no añaden cadenas de rebotes de transparencia.

## Verificación ejecutada

Blender 4.3.2, `--background --python-exit-code 1`. Se crearon las cuatro especies/alturas existentes y dos tamaños de arbusto. Se comprobaron:

1. Posiciones de raíz originales, con tolerancia de representación float32.
2. Altura máxima del asset y radio máximo conservados.
3. Coordenadas finitas y ausencia de polígonos con área nula.
4. Mallas válidas según `Mesh.validate()` y asignación de UV/materiales.

Resultado: seis assets válidos. Las diferencias con las envolventes objetivo son inferiores a 1 μm por precisión float32. Esto certifica la transformación del asset, no la precisión del PDF. La prueba no generó renders ni alteró ningún archivo `.blend` canónico. Detalles: `analisis_v2/vegetacion_verificacion.json`.

## Procedencia y licencias

Toda la malla y todos los nodos de material se generan con el código original entregado. No se incorporaron modelos, imágenes, texturas ni recursos descargados de terceros. Por tanto, no hay una licencia de asset externo que adjuntar ni dependencia de una biblioteca de vegetación remota. Se conserva la semilla SHA256 del nombre en cada raíz para reproducir la misma planta.

La especie y el tamaño ornamental de las plantas siguen siendo criterios de visualización. Su detalle debe evaluarse en la siguiente vista de prueba del modelo completo, con la iluminación y la exposición finales; la fidelidad geométrica de la vivienda se verifica en su propio informe.

## Microgeometría opcional de césped artificial

Se añade `make_turf_fibres(nombre, S['cesped'], z, coleccion, materiales, density=2000)`, que devuelve un Empty y **una sola malla**. El builder decide si la activa. Las fibras usan `materiales['cesped_fibra']` cuando está disponible; el material coordinado con el módulo de acabados representa polímero verde de fibra corta.

La densidad expresa un presupuesto de representación y no una ficha técnica de producto. La altura 18–27 mm, anchura 0,55–1,15 mm, inclinación 0,4–3,2 mm y giro leve son microgeometría visual del acabado pedido por el usuario. La superficie base del jardín y sus bordes permanecen iguales. La distribución uniforme en área parte de los mismos triángulos existentes; bases, anchos y puntas se recortan en coordenadas baricéntricas para conservarse dentro de cada triángulo. Las comparaciones de planta deben mantener esta colección/objeto de microgeometría fuera de la medición arquitectónica.

La prueba en Blender 4.3.2 con las superficies V1 heredadas de 147,387776 m² generó **294.776 fibras, 884.328 caras y 2.358.208 vértices en 5,40 s**. El cap global es 333.333 fibras/999.999 caras, incluso si crece la superficie. `Mesh.validate()` no corrigió errores. Se comprobaron independientemente 47.624 vértices, incluidos los de las primeras y últimas fibras de cada triángulo, con distancia al borde calculada desde sus lados. La desviación máxima atribuible a float32 fue 1,574 μm, por debajo de la tolerancia de 4 μm de esta comprobación. Altura máxima local: 26,99995 mm. No se realizaron renders ni guardados del modelo canónico. Registro: `analisis_v2/cesped_fibras_verificacion.json`.

Las fibras aumentan la geometría de la escena y del GLB; para una revisión ligera puede omitirse esta llamada y conservar el material de base. Si se activan, conviene guardar el `.blend` comprimido para que la repetición de vértices y atributos tenga un coste menor en descarga. El render conserva la misma huella del jardín en ambos casos.
