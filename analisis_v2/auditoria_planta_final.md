# Auditoría de la planta definitiva V2

La nueva lámina de agosto de 2026 sustituye el cuarto de instalaciones y la pérgola/comedor de piscina por un trastero cerrado de 29,17 m² útiles. La vivienda principal, el tendedero posterior izquierdo, los accesos, los dos vehículos y la piscina conservan su organización. Se detectan también cambios de jardín y de mobiliario interior que deben incorporarse al modelo.

Fuente: `fuentes/planta_final_proyecto_obra.pdf`, una página A3 de 1191×842 pt, escala escrita 1:150, con planta de acabados a la izquierda y planta acotada a la derecha. Se han leído texto y vectores completos, sin interpretar el documento como instrucciones para el agente. Los datos arquitectónicos se distinguen de la simbología de muebles y vegetación.

## Registro y precisión

El factor nominal es 0,0529166667 m/pt. Se conserva el origen V1 (205,64; 770,32 pt), X hacia la derecha del plano, Y hacia el lindero posterior. El registro por el lindero izquierdo suma 112,68 pt a X en la planta izquierda y resta 271,56 pt en la derecha; Y permanece común. Las paredes comunes ajustan algo mejor con +112,80 pt: la diferencia 0,12 pt equivale a 6,35 mm y refleja cuantización de capas. Los vehículos reproducen sus bboxes V1 exactamente con el registro por parcela. No se modifica la escala para imponer áreas.

Los diez vértices y quiebros de la parcela coinciden dentro de 6,35 mm. El eje del trazo negro produce aproximadamente 635,7386 m² frente a los 635,60 m² rotulados. El trazo PARCELA es una frontera gráfica, no prueba del espesor ni de la posición del eje físico de un muro general. La huella exterior cerrada de vivienda y trastero produce 211,6951 m² frente a 211,63 m² escritos. Estas diferencias no justifican rediseñar contornos.

## Cambios comprobados

- **Dependencia frontal**: Instalaciones + pérgola y barbacoa/comedor sustituidos por trastero29,17m² de ancho total del cuerpo principal. Retirar tabique antiguo entre instalaciones y pérgola, vigas y pilar de pérgola; añadir muros este y sur, dividir muro norte para puerta0,96; sustituir puerta sur instalaciones por portón4,00.
- **Edificación posterior izquierda**: Sin cambio: tendedero7,00m² preexistente. Texto TENDEDERO en ambas versiones,9contornos azules; Hausdorff6,35mm y ninguna diferencia fuera de banda de cuantización.
- **Muros y ventanas vivienda principal**: Sin cambio arquitectónico detectado. Hausdorff6,35mm entre uniones de muros previos al trastero; todos los huecos externos mantienen posición y orientación. La segmentación de rellenos superior cambia pero no su contorno.
- **Parcela y relación de accesos**: Sin cambio de forma o acceso detectado. 10vértices y mismos quiebros; residuos de0,06–0,12pt. Portón de vehículos y acceso peatonal siguen lindero frontal; entrada vivienda continúa oeste.
- **Piscina y escalera**: Sin cambio de posición/orientación; nuevas cotas directas3,50×5,00. Bordes y escalones iguales dentro de cuantización. Preferir cotas escritas exactas a anchura vectorial3,49885/3,5052 o longitud5,0038.
- **Jardín aparcamiento**: Añadir franja de césped/vegetación a la izquierda de dos vehículos. Nuevos bordes de solería x149,60 y168,56 entrey639,28ylindero frontal. Ancho gráfico1,0033m; extensiónaprox6,5m. Ningún borde de plaza inventado.
- **Tumbonas**: Conservar emplazamientos; el relleno blanco bajo símbolos es máscara de dibujo, césped continuo deducido. Las dos retiradas en comparacion_cesped son sólo rectángulos de tumbona.
- **Hall/entrada**: Superficie rotulada pasa8,52a6,30m² sin mover sus muros. Contornos comunes iguales dentro cuantización; distinto cómputo/rotulación.
- **Despacho**: Renombrado SILICON VALLEY; superficie6,93m² mantenida. Texto y contornos; no nuevo recinto.
- **Mobiliario salón**: Cambian mesa de centro, mesa comedor, butacas y desaparece asiento adicional; ver mobiliario_cambiado. Cotas y rellenos grises nuevos; no modificar arquitectura a partir de mobiliario.
- **Superficie construida**: Texto V2 indica211,63m² frente190,61m² V1. La propia lámina indica que excede190,68m² permitidos; se transcribe como dato del documento, no como aprobación urbanística.

El tendedero de la esquina posterior izquierda está identificado literalmente como TENDEDERO, 7,00 m². Conserva nueve rellenos azules de muros y su contorno coincide con V1 dentro de 6,35 mm. No es un segundo trastero añadido. La unión de las paredes de la vivienda principal anterior al trastero tiene distancia de Hausdorff de 6,35 mm respecto a V1; no aparece un cambio de habitación, posición de acceso principal ni hueco exterior. Los cambios en la teselación de rellenos no son paredes nuevas.

La nueva banda ajardinada junto al lado izquierdo del aparcamiento procede de cuatro patches con seqno 3251/3253/3255/3257. Su ancho gráfico es 1,0033 m y su área vectorial 6,490572 m², con un encuentro irregular junto al portón. Debe conservarse ese contorno, no sustituirlo por un rectángulo de diseño. Las dos pérdidas de verde bajo las tumbonas son máscaras gráficas de los muebles; se mantiene la continuidad de césped inferida.

## Trastero y huecos

Los seis rellenos nuevos o modificados son seqno 1759, 1761, 1763, 1765, 59509 y 59511. Desaparece el tabique antiguo instalaciones/pérgola; el muro norte se divide para la nueva puerta; se cierra el lateral este y se forman dos paños en el frente sur con el gran portón intermedio. No hay ventana nueva en el trastero. La cubierta y las alturas se definen en la auditoría independiente de alturas y en la confirmación del usuario.

| Dimensión | Escrita (m) | Vector (m) | Error vector−escrita (mm) | Fuente seqno |
|---|---:|---:|---:|---:|
| Ancho interior trastero | 7.15000 | 7.15010 | +0.10 | 61313 |
| Profundidad interior trastero | 3.94000 | 3.94335 | +3.35 | 61321 |
| Profundidad norte interior–sur exterior | 4.19000 | 4.19100 | +1.00 | 61329 |
| Hueco bruto puerta norte | 0.96000 | 0.96520 | +5.20 | 61536 |
| Hueco puerta norte según extremos línea cota | 0.96000 | 0.95885 | -1.15 | 61536 |
| Portón sur, sin cota escrita específica | — | 4.00050 | — | 59561 |
| Piscina ancho según bordes azul/solería izquierda | 3.50000 | 3.49885 | -1.15 | 54387 |
| Piscina ancho según línea cota derecha | 3.50000 | 3.50520 | +5.20 | 62204 |
| Piscina longitud | 5.00000 | 5.00380 | +3.80 | 62196 |

La cota 7,50 m corresponde a la suite principal, no al trastero. La cota del trastero es 7,15 m entre caras interiores oeste y este. La profundidad 3,94 m llega a la cara interior del muro sur; 4,19 m llega a su cara exterior. De ambas se calcula un espesor sur nominal de 0,25 m.

La puerta norte abre hacia el trastero, con bisagra al oeste. Su hoja vectorial mide 0,81915 m de longitud y ocupa el bbox V2 [232,28;537,40;233,12;552,88] pt. La cota 0,96 m representa el hueco bruto, no el ancho de hoja; las jambas gráficas son aproximadamente 0,07 m. La altura de hoja 2,03 m procede de la confirmación del usuario. El portón sur tiene un único símbolo horizontal de ancho 4,0005 m; no se debe inferir su mecanismo de apertura a partir de esa línea.

Los 29,17 m² no son una contradicción con el rectángulo interior de aproximadamente 28,20 m²: 7,15×3,94 + umbral sur 4,00×0,25 = 29,171 m². Incluir ese umbral reconcilia el cómputo nominal; esta explicación es una deducción, no una instrucción para forzar superficies.

## Criterio final del modelo: cotas nominales con anclajes

El JSON de auditoría conserva los vectores literales para poder comparar modelo y documento. Para construir V2, el coordinador ha decidido priorizar las cotas escritas del trastero y de la piscina mediante ajustes locales inferiores a 6,35 mm. El resto de muros comunes utiliza los vectores nuevos. No debe afirmarse que los elementos normalizados reproducen literalmente cada milímetro del trazo PDF; reproducen sus dimensiones nominales y posiciones dentro de la cuantización documentada.

La cara interior norte del trastero se ancla en Y=12,0777 m y la oeste en X=3,2512 m. La cara interior este queda X=10,4012 m, la interior sur Y=8,1377 m y la exterior sur Y=7,8877 m: ancho 7,15 m, profundidad interior 3,94 m, profundidad hasta exterior 4,19 m y espesor sur 0,25 m. Frente a los vectores, los ajustes son −0,10 mm en este, +3,35 mm en sur interior y +1,00 mm en sur exterior. Los anclajes comunes de la vivienda no se desplazan.

El hueco norte se ancla en su extremo oeste X=7,3025 m y se termina en X=8,2625 m para obtener exactamente 0,96 m; el extremo este se corrige −5,20 mm respecto al relleno vectorial. Se conserva la posición de apertura dibujada de la hoja. Esta decisión difiere de la propuesta alternativa con anclaje este registrada en `auditoria_planta_final_ajustes.json`; la propuesta alternativa no es el criterio final.

La piscina se ancla en oeste X=11,7094 m y norte Y=10,8585 m. Sus caras libres quedan este X=15,2094 m y sur Y=5,8585 m, para 3,50×5,00 m exactos. Los cambios desde los bordes de la planta izquierda son +1,15 mm en este y +3,80 mm en sur. El trazado de escalones se conserva y sus terminaciones se ajustan a la cara este normalizada.

La huella exterior de otros recintos no se modifica para compensar superficies rotuladas. Las dimensiones y alturas de muebles son referencias de visualización separadas de los muros.

## Otras discrepancias de líneas de cota

Se han asociado las 93 cotas numéricas con sus líneas rojas y extremos de flecha. Seis diferencias entre longitud de línea y número escrito superan 6,35 mm; varias se explican por flechas o líneas que exceden 0,12 pt el relleno del mueble. No equivalen automáticamente a una discrepancia de muro.

| Cota | Línea vectorial (m) | Error (mm) | Elemento y explicación |
|---|---:|---:|---|
| 1,6m | 1.60655 | +6.55 | SofáL, fondo: Línea roja462,40–492,76pt mide1,60655m, relleno real462,52–492,64pt mide1,59385m. Nominal1,60rige asset; ambos extremos de línea sobrepasan relleno0,12pt. No es pared. |
| 2m | 2.00660 | +6.60 | Isla cocina, longitud: Línea roja381,40–419,32pt mide2,00660m, pero relleno real381,40–419,20pt mide2,00025m, error+0,25mm. Cota2,00rige mueble. |
| 3,52m | 3.53060 | +10.60 | Encimera longitudinal cocina: La línea de cota roja va367,00–433,72pt, pero el relleno real encimera va367,12–433,60pt:3,51790m, error−2,10mm respecto3,52. Diferencia de la línea de dimensión, no necesidad de desplazar muro. |
| 1,72m | 1.72720 | +7.20 | Cocina, separación a isla: Línea roja incluye381,52pt, mientras isla real comienza381,40pt: distancia348,88–381,40=1,72085m, error+0,85mm respecto1,72. No altera muro. |
| 2,68m | 2.67335 | -6.65 | Baño2, profundidad interior: Vector285,16–335,68pt mide2,67335m frente cota2,68m:−6,65mm, supera una unidad de cuantización en0,30mm. Se identifica como discrepancia menor; no desplazar dormitorios o baño sin resolver sus demás cotas comunes. |
| 1,02m | 1.02870 | +8.70 | Aseo, relación con equipamiento: Línea de cota1,02va379,12–398,56pt; no es dimensión total de recinto. Diferencia8,70mm; aplicar nominal si se reproduce ese equipamiento, sin mover límites del aseo. |

La profundidad interior del baño 2 presenta una diferencia real de −6,65 mm respecto a 2,68 m, sólo 0,30 mm superior a la unidad de cuantización. Queda explícita; la auditoría no inventa un desplazamiento de sus paredes para resolverla de forma aislada y afectar dormitorios adyacentes. Las demás diferencias citadas afectan relaciones de equipamiento o el trazado de cotas de muebles.

## Mobiliario y reproducción

`mobiliario_cambiado` contiene los nuevos bboxes de mesa central, mesa comedor, dos butacas, rack de tablas, gym, moto y los dos paños grises junto al muro norte del trastero. `sillas_comedor_interior_v2` contiene los ocho bboxes con nombres compatibles con JSONF V1. `mobiliario_desaparecido_nombres_v1` enumera el asiento oeste y los nueve objetos del comedor bajo la antigua pérgola. Cocina, isla, camas y mobiliario de terraza mantienen sus posiciones dentro de cuantización.

Los scripts de esta auditoría no modifican el modelo ni los JSON canónicos. Se reproducen desde la raíz V2 con:

```sh
python analisis_v2/extraer_auditoria_planta_final.py
python analisis_v2/preparar_ajustes_auditoria_planta_final.py
python analisis_v2/redactar_auditoria_planta_final.py
```

La primera salida es el trazado literal; la segunda es una propuesta de normalización y tabla de errores, incluida una alternativa de anclaje que no se usa en el criterio final; este informe documenta la selección efectiva del coordinador. La generación del modelo se realiza por el pipeline del coordinador.

## Tabla completa de cotas directas

Las distancias vectoriales de esta tabla se miden entre puntas de flechas de la planta acotada derecha. No todas son cotas de paredes: se conservan las cotas de muebles y equipamiento para permitir trazabilidad.

| Texto | Dirección | Vector (m) | Error (mm) | Seqno línea | Contexto |
|---|---|---:|---:|---:|---|
| 7,15m | X | 7.15010 | +0.10 | 61313 | trastero; cota recinto o mobiliario según posición |
| 3,94m | Y | 3.94335 | +3.35 | 61321 | trastero; cota recinto o mobiliario según posición |
| 4,19m | Y | 4.19100 | +1.00 | 61329 | trastero; cota recinto o mobiliario según posición |
| 3m | X | 3.00355 | +3.55 | 61413 | salón; cota recinto o mobiliario según posición |
| 1,6m | Y | 1.60655 | +6.55 | 61421 | salón; cota recinto o mobiliario según posición |
| 1,2m | X | 1.20015 | +0.15 | 61429 | salón; cota recinto o mobiliario según posición |
| 0,7m | Y | 0.70485 | +4.85 | 61437 | salón; cota recinto o mobiliario según posición |
| 0,75m | Y | 0.75565 | +5.65 | 61445 | salón; cota recinto o mobiliario según posición |
| 0,75m | Y | 0.74930 | -0.70 | 61453 | salón; cota recinto o mobiliario según posición |
| 0,8m | X | 0.80010 | +0.10 | 61461 | salón; cota recinto o mobiliario según posición |
| 0,8m | X | 0.80010 | +0.10 | 61469 | salón; cota recinto o mobiliario según posición |
| 4m | Y | 4.00050 | +0.50 | 61477 | salón; cota recinto o mobiliario según posición |
| 6,95m | X | 6.94690 | -3.10 | 61485 | salón; cota recinto o mobiliario según posición |
| 2m | Y | 2.00025 | +0.25 | 61493 | salón; cota recinto o mobiliario según posición |
| 1,2m | X | 1.20015 | +0.15 | 61501 | salón; cota recinto o mobiliario según posición |
| 0,96m | X | 0.95885 | -1.15 | 61536 | salón; cota recinto o mobiliario según posición |
| 5,39m | Y | 5.39115 | +1.15 | 61544 | salón; cota recinto o mobiliario según posición |
| 4,05m | X | 4.05130 | +1.30 | 61552 | hall/cocina/franja de acceso |
| 0,6m | Y | 0.60325 | +3.25 | 61612 | trastero; cota recinto o mobiliario según posición |
| 3,58m | X | 3.57505 | -4.95 | 61620 | trastero; cota recinto o mobiliario según posición |
| 1,7m | Y | 1.70180 | +1.80 | 61628 | trastero; cota recinto o mobiliario según posición |
| 2m | X | 2.00025 | +0.25 | 61636 | trastero; cota recinto o mobiliario según posición |
| 2,4m | Y | 2.40030 | +0.30 | 61644 | trastero; cota recinto o mobiliario según posición |
| 0,9m | X | 0.90170 | +1.70 | 61652 | trastero; cota recinto o mobiliario según posición |
| 5,08m | Y | 5.08635 | +6.35 | 61660 | cocina/lavadero/aseo |
| 1,2m | X | 1.20015 | +0.15 | 61668 | cocina/lavadero/aseo |
| 2m | Y | 2.00660 | +6.60 | 61676 | cocina/lavadero/aseo |
| 1m | X | 1.00330 | +3.30 | 61684 | cocina/lavadero/aseo |
| 1m | X | 0.99695 | -3.05 | 61692 | cocina/lavadero/aseo |
| 3,52m | Y | 3.53060 | +10.60 | 61700 | cocina/lavadero/aseo |
| 3,8m | X | 3.79730 | -2.70 | 61708 | cocina/lavadero/aseo |
| 1,72m | Y | 1.72720 | +7.20 | 61716 | cocina/lavadero/aseo |
| 3,2m | X | 3.20040 | +0.40 | 61724 | hall/cocina/franja de acceso |
| 1,8m | X | 1.79705 | -2.95 | 61732 | hall/cocina/franja de acceso |
| 4,8m | X | 4.80060 | +0.60 | 61740 | suite principal: dormitorio1/vestidor/baño1 |
| 4,2m | X | 4.19735 | -2.65 | 61748 | suite principal: dormitorio1/vestidor/baño1 |
| 3,26m | Y | 3.26390 | +3.90 | 61756 | suite principal: dormitorio1/vestidor/baño1 |
| 2,16m | Y | 2.16535 | +5.35 | 61764 | suite principal: dormitorio1/vestidor/baño1 |
| 4,26m | Y | 4.26085 | +0.85 | 61772 | suite principal: dormitorio1/vestidor/baño1 |
| 1m | Y | 0.99695 | -3.05 | 61780 | dormitorio2/despacho/baño1 |
| 1,8m | X | 1.79705 | -2.95 | 61788 | dormitorio2/despacho/baño1 |
| 2,26m | Y | 2.26060 | +0.60 | 61796 | suite principal: dormitorio1/vestidor/baño1 |
| 1,3m | X | 1.30175 | +1.75 | 61804 | suite principal: dormitorio1/vestidor/baño1 |
| 1,8m | X | 1.79705 | -2.95 | 61812 | suite principal: dormitorio1/vestidor/baño1 |
| 2,6m | X | 2.60350 | +3.50 | 61820 | suite principal: dormitorio1/vestidor/baño1 |
| 2,16m | Y | 2.16535 | +5.35 | 61828 | suite principal: dormitorio1/vestidor/baño1 |
| 2,16m | Y | 2.16535 | +5.35 | 61836 | suite principal: dormitorio1/vestidor/baño1 |
| 1,4m | X | 1.40335 | +3.35 | 61844 | suite principal: dormitorio1/vestidor/baño1 |
| 1,56m | Y | 1.56210 | +2.10 | 61852 | suite principal: dormitorio1/vestidor/baño1 |
| 2,66m | Y | 2.66065 | +0.65 | 61860 | suite principal: dormitorio1/vestidor/baño1 |
| 7,5m | X | 7.49935 | -0.65 | 61868 | suite principal: dormitorio1/vestidor/baño1 |
| 2,1m | Y | 2.10185 | +1.85 | 61876 | suite principal: dormitorio1/vestidor/baño1 |
| 1m | Y | 1.00330 | +3.30 | 61884 | suite principal: dormitorio1/vestidor/baño1 |
| 3,8m | X | 3.79730 | -2.70 | 61892 | dormitorio2/despacho/baño1 |
| 3,8m | X | 3.79730 | -2.70 | 61900 | dormitorio2/despacho/baño1 |
| 3,61m | Y | 3.61315 | +3.15 | 61908 | dormitorio2/despacho/baño1 |
| 3,01m | Y | 3.00990 | -0.10 | 61916 | dormitorio2/despacho/baño1 |
| 3,8m | X | 3.79730 | -2.70 | 61924 | dormitorio2/despacho/baño1 |
| 3,61m | Y | 3.61315 | +3.15 | 61932 | dormitorio3/baño2 |
| 3,61m | Y | 3.61315 | +3.15 | 61940 | dormitorio3/baño2 |
| 3,8m | X | 3.79730 | -2.70 | 61948 | dormitorio3/baño2 |
| 1,8m | X | 1.79705 | -2.95 | 61956 | dormitorio2/despacho/baño1 |
| 0,8m | Y | 0.80010 | +0.10 | 61964 | dormitorio2/despacho/baño1 |
| 3,8m | Y | 3.79730 | -2.70 | 61972 | dormitorio2/despacho/baño1 |
| 1,8m | X | 1.79705 | -2.95 | 61980 | dormitorio2/despacho/baño1 |
| 2,6m | Y | 2.59715 | -2.85 | 61988 | dormitorio2/despacho/baño1 |
| 1m | X | 1.00330 | +3.30 | 61996 | dormitorio2/despacho/baño1 |
| 1m | X | 1.00330 | +3.30 | 62004 | dormitorio3/baño2 |
| 1,8m | X | 1.79705 | -2.95 | 62012 | dormitorio3/baño2 |
| 0,88m | Y | 0.87630 | -3.70 | 62020 | dormitorio3/baño2 |
| 1m | Y | 0.99695 | -3.05 | 62028 | dormitorio3/baño2 |
| 1,3m | X | 1.30175 | +1.75 | 62036 | dormitorio3/baño2 |
| 1,8m | X | 1.79705 | -2.95 | 62044 | dormitorio3/baño2 |
| 1,8m | Y | 1.79705 | -2.95 | 62052 | dormitorio3/baño2 |
| 2,68m | Y | 2.67335 | -6.65 | 62060 | dormitorio3/baño2 |
| 1,8m | X | 1.79705 | -2.95 | 62068 | cocina/lavadero/aseo |
| 2,1m | Y | 2.10185 | +1.85 | 62076 | cocina/lavadero/aseo |
| 1,5m | Y | 1.50495 | +4.95 | 62084 | cocina/lavadero/aseo |
| 0,6m | Y | 0.60325 | +3.25 | 62092 | cocina/lavadero/aseo |
| 1,52m | Y | 1.52400 | +4.00 | 62100 | cocina/lavadero/aseo |
| 1m | X | 0.99695 | -3.05 | 62108 | cocina/lavadero/aseo |
| 1,02m | Y | 1.02870 | +8.70 | 62116 | cocina/lavadero/aseo |
| 1,8m | X | 1.79705 | -2.95 | 62124 | cocina/lavadero/aseo |
| 1m | X | 1.00330 | +3.30 | 62132 | cocina/lavadero/aseo |
| 1m | X | 1.00330 | +3.30 | 62140 | cocina/lavadero/aseo |
| 1,8m | X | 1.79705 | -2.95 | 62148 | tendedero |
| 2,83m | Y | 2.83210 | +2.10 | 62156 | tendedero |
| 2,85m | X | 2.85115 | +1.15 | 62164 | tendedero |
| 2,4m | Y | 2.40030 | +0.30 | 62172 | hall/cocina/franja de acceso |
| 1,8m | Y | 1.80340 | +3.40 | 62180 | hall/cocina/franja de acceso |
| 2,9m | X | 2.90195 | +1.95 | 62188 | hall/cocina/franja de acceso |
| 5m | Y | 5.00380 | +3.80 | 62196 | piscina |
| 3,5m | X | 3.50520 | +5.20 | 62204 | piscina |
