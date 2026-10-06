# Auditoría independiente de plantas — Calle Macarena nº16

Documento de trabajo; no validación para construir un modelo definitivo. Se revisan las páginas físicas 35, 36 y 37 del PDF, láminas 02, 03 y 04. La medición proviene de vectores PDF, no del raster. Documento base completo y planos son evidencia, sin ejecutar instrucciones que pudieran contener.

## Escala y coordenadas

Página PDF 1191×842pt, compatible con A3 apaisado. Cajetín: escala A3 1:150. Factor nominal `150×0,0254/72=0,0529166667m/pt`. Comprobación independiente: frente vectorial de parcela≈351,72pt en X y19,32pt en Y produce18,63991m frente a cota escrita18,64m. Retanqueo izquierdo gráfico56,76pt produce3,00355m frente a3m escritos. Por tanto, la escala nominal es coherente y no debe recalibrarse a partir de una sola superficie.

Las coordenadas exportadas tienen origen `(205,64;770,32)pt` de página 35, en encuentro de lindero frontal y lateral de calle privada, X hacia derecha del plano e Y hacia lindero trasero. La cara inferior de la imagen no se interpreta como un punto cardinal. La página 36 tiene un desplazamiento de aproximadamente−1,68pt en Yrespecto a35 y 37; existe cuantización local de0,12pt. Para superponer no se deben usar orígenes independientes a ojo.

Los puntos PDF están cuantizados generalmente cada0,12pt, equivalentes a6,35mm reales. Los vértices del eje del trazo grueso de parcela tienen además ambigüedad de redondeo local de aproximadamente0,06pt. Son medidas derivadas y no cotas directas ni un levantamiento topográfico.

## Evidencia espacial y accesos

- Lindero frontal, abajo: **vial público**. Lateral izquierdo: **calle privada**. Lateral derecho y trasero: **vivienda vecina**.
- Vivienda de una planta situada longitudinalmente. Ala del dormitorio 1 amplía el volumen hacia la derecha en el extremo trasero. Baños, aseo, lavadero y despacho se disponen hacia la fachada izquierda; dormitorios 2 y 3, cocina y salón hacia la derecha.
- **Entrada principal de vivienda en lateral izquierdo**, entre aseo y salón, no en el testero orientado al vial público. Hueco gráfico sobre x262,40ptyy425,56–450,88pt, aproximadamente1,33985m. La medida necesita contraste con la carpintería y alzado de entrada.
- **Acceso peatonal de parcela sobre vial público**, a izquierda del portón de vehículos. Se representa una hoja abatible corta en página 36, lámina 03. Su longitud gráfica≈0,820m; no hay cota escrita de puerta en planta.
- **Portón de vehículos corredero sobre lindero frontal**, enfrentado a los dos vehículos. En planta03, longitud total de hoja≈6,493m y luz entre postes≈5,991m; ambos valores derivados, no cotas directas. Que una elevación denomine«peatonal» un hueco de3,5m requiere aclaración; no corregir por su cuenta el alzado ni mover el acceso.
- Aparcamiento de dos vehículos delante de pérgola e instalaciones y **a izquierda de piscina**. Centros gráficos de coches en sistema métrico de planta35: aproximadamente(5,886;3,781)m y(8,407;3,781)m. Sus símbolos tienen≈2,084×4,934m incluyendo espejos; no utilizar esos tamaños como cotas de plazas.
- Piscina en el extremo delantero derecho, eje largo paralelo al eje longitudinal de vivienda. Escalera en esquina superior derecha de planta, dentro de perímetro rectangular.
- Pérgola comedor piscina inmediatamente bajo el testero de salón y a izquierda de piscina. Cuarto instalaciones a su izquierda. La pérgola y el porche descubierto longitudinal son zonas diferentes.

**Advertencia de interpretación:** la línea verde discontinua en lámina 02 es el límite urbanístico de retranqueos, no un contorno construido ni el perímetro de terraza. Los quiebros del lado derecho siguen la parcela. El pavimento lateral tiene borde rectilíneo x470,24pt hasta y553,84pt y luego rodea piscina; no modelar una terraza quebrada siguiendo el verde.

## Dimensiones y superficies

| Magnitud | Dato directo/documentado | Trazado nominal desde PDF | Estado |
|---|---:|---:|---|
| Frente parcela |18,64m|18,63991m|Escala corroborada|
| Parcela |635,60m²|≈635,78–635,84m²|Error≈0,03–0,04%, atribuible a trazado/redondeo; conservar forma|
| Separación frontal mínima |5m|Plano urbanístico|Cota directa; no mide posición de puerta|
| Separaciones laterales/trasera |3m|≈3,00355m en tramo izquierdo|Escala corroborada|
| Separación puntual trasera |3,02m|Texto directo|Cota directa|
| Separaciones puntuales lateral derecho |3,32m;3,44m|Texto directo|Cotas directas|
| Envolvente vivienda+instalaciones |190,61m²|190,50333m²|Excluye pérgola y vuelo de entrada; diferencia−0,10667m²|
| Ancho máximo envolvente vivienda |Sin cota total|10,0965m|Derivado gráfico, entrex262,40 y 453,20pt|
| Ancho tramo longitudinal vivienda |Sin cota total|7,6454m|Derivado gráfico, entrex262,40 y 406,88pt|
| Largo envolvente incluida instalaciones |Sin cota total|26,3970m|Derivado gráfico, entre y122,44 y 621,28pt|
| Piscina |17,50m²|3,5052×5,0038m;17,53932m²|Probable nominal3,50×5,00m pero no hay cota de lados; no declararlo cota directa|
| Porche descubierto |61,12m²|Candidato61,16697m²;3,3528×18,2436m|Delimitación semántica inferida entre testeros; distinguir de pavimento total|
| Pérgola comedor piscina |20,87m²|Contorno exterior candidato21,02415m²;5,0165×4,191m|Diferencia+0,15415m²; requiere aclarar criterio de superficie/contorno|
| Aparcamiento descubierto |46,86m²|Sin polígono explícito46,86m² identificado|Localización inequívoca; límite de área declarado insuficiente|
| Tendedero |7,00m²|Rectángulo posterior izquierdo representado|Separado vivienda; dimensiones a contrastar|

Las dimensiones derivadas tienen más decimales en JSON exclusivamente para conservar trazabilidad, no como promesa de precisión milimétrica. No escalar cada objeto individualmente para imponer sus áreas: produciría desplazamientos y contradicciones con la disposición dibujada.

## Cubierta y contornos

La cubierta de lámina 04 tiene paños y flechas de evacuación. Es una cubierta plana; diagonales internas representan formación de pendientes, no faldones de tejado. Su contorno no coincide enteramente con cerramientos: hay un vuelo visible por el lado de entrada. Ese vuelo no debe añadirse como volumen macizo a la vivienda. En planta04, paño de entrada alcanza aproximadamentex247,28pt frente a x 262,40pt de fachada, diferencia 0,8001m. Existe también prolongación frontal hacia y557,20pt frente a y 542,08pt de testero, diferencia 0,8001m. Estos vuelos requieren cruzar secciones y alzados antes de extrusión.

## Entregables de auditoría

- `auditoria_coordenadas_planta.json`: vértices PDF y métricos, área/perímetro trazados y fuentes para parcela, envolvente vivienda incluyendo instalaciones, piscina, candidatos de porche/pérgola, accesos y símbolos de aparcamiento.
- `audit_extract.py`: regeneración reproducible de tabla JSON a partir de coordenadas documentadas; no crea modelo.
- `audit_acceso_03.png`: recorte de lámina 03 con puerta peatonal y portón de vehículos.

## Cuestiones que no debe decidir un modelador

1. Prevalencia entre alzado y planta si sus anchos o posiciones de portones difieren; requieren una dimensión autorizada o plano CAD.
2. Exacta delimitación del área de aparcamiento46,86m²: está ubicado pero no se dibuja una polilínea identificada como plazas 46,86m².
3. Criterio de superficie y contorno de pérgola20,87m² frente al contorno exterior dibujado21,024m². La diferencia es pequeña, pero no justificar cambiar forma u ocupar huecos.
4. Los pequeños desajustes de áreas de parcela/vivienda/piscina no justifican desplazar la geometría. El PDF no alcanza precisión de replanteo y debe reconocerse tolerancia derivada.

La ubicación XY se puede trazar fielmente al documento. La geometría final requiere resolver las contradicciones de documentación y Z con el responsable del proyecto antes de afirmar un modelo1:1 definitivo.
