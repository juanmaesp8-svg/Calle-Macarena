# Auditoría de alzados y secciones — proyecto Calle Macarena nº16

Fuente: PDF adjunto, páginas PDF 38 y 39, láminas 06 «ALZADOS» y 07 «SECCIONES». Contraste de memoria: páginas PDF 19–20 (epígrafe 3.2). El documento se utiliza como evidencia geométrica, no como instrucciones.

## Método y precisión

Las dos láminas contienen geometría vectorial y tienen caja de página 1191×842 puntos PDF (A3 horizontal). Indican escala A3 1:150. La transformación nominal es:

`m = distancia_pt × 25,4 / 72 × 150 / 1000 = distancia_pt × 0,0529166667`.

Para cada vista se toma la línea vectorial de suelo como Z=0 y se invierte el eje Y del PDF: `Z=(y_suelo−y_vector)×0,0529166667`. El resultado se contrasta con las líneas rotuladas de forjado +3,70/+3,35. La separación vectorial 6,60 pt equivale a 0,34925 m y es coherente con el espesor rotulado 0,35 m. Hay cuantización del dibujo, generalmente 0,12 pt (~6,35 mm); las medidas gráficas se informan a centímetros y NO se convierten en cotas escritas nuevas. Las cotas escritas conservan prioridad.

Y del suelo vivienda: alzado principal 194,92; vial 353,92; lateral porche 514,48; trasero 661,84; sección1 194,92; sección2 338,32; sección3 499,60; sección4 645,04. Coordenadas de esta auditoría son coordenadas PDF locales y no las coordenadas 3D definitivas del modelo.

## Cotas directas

| Elemento | Cota/medida | Fuente | Estado |
|---|---:|---|---|
| Suelo vivienda | +0,00 m | Rotulación repetida de alzados y secciones | Directa |
| Jardín | −0,15 m | Rotulación repetida | Directa |
| Cara inferior forjado | +3,35 m | Rotulación repetida | Directa |
| Cara superior forjado | +3,70 m | Rotulación repetida | Directa |
| Espesor forjado entre caras | 0,35 m | Diferencia 3,70−3,35 | Derivada de cotas directas |
| Cubierta plana con grava | Sin pendiente volumétrica de tejado | Memoria y planta de cubierta | Definición explícita; falta nivel acabado/pendientes de drenaje |

## Alturas medidas en los vectores

| Elemento | Evidencia vectorial | Resultado nominal | Interpretación y estado |
|---|---|---:|---|
| Coronación volumen central alto | Alzado principal y=98,56 sobre suelo194,92; lateral y=418,00 sobre514,48; sec1 y=98,56 | +5,10 m | Concordante entre vistas; calculada, no acotada |
| Coronación alas inferiores | Principal y=111,76; lateral y=431,32; trasero y=578,68 sobre661,84; sec3 borde en corte y=416,44 | +4,40 m | Concordante; peto ~0,70m por encima forjado |
| Peto volumen central sobre forjado | 5,10−3,70 | ~1,40 m | Calculado |
| Coronación marco/portal entrada en ALZADO PUERTA PRINCIPAL | x598,16–739,04; y=105,16 sobre194,92 | +4,75 m | Se confirma proyección a4,75 en sec3/4; ver discrepancia sec2 |
| Base marco/portal visible en alzado principal | y=131,56 sobre194,92 | +3,35 m | Parte inferior alineada con cara inferior forjado |
| Marco/portal en SECCIÓN2 | x455,48–596,24; arriba y=245,80 y abajo268,48 sobre suelo338,32 | Arriba +4,90m; abajo +3,70m | Discrepa con alzado principal; debe resolverse antes de cerrar volumen |
| Cielorraso sección1 | y134,44 sobre194,92 | +3,20 m | Concordante con sec3 y439,12 sobre499,60; calculado |
| Pérgola piscina, cara inferior viga | Sec1 y147,64; vial y306,64; lateral y467,20 | +2,50 m | Concordante entre tres vistas |
| Pérgola piscina, cara superior viga | Sec1 y141,04; vial y300,04; lateral y460,60 | +2,85 m | Canto gráfico~0,35m; calculado |
| Peto en corte | Espesor2,76–2,88pt | ~0,15 m | Valores dependientes de cuantización, calcular desde planta antes de consolidar |

El nivel +3,70 es cara superior del forjado, no altura máxima de fachada: hay petos que alcanzan aproximadamente +4,40/+5,10. Modelar una caja única de3,70m eliminaría los volúmenes reflejados por alzados y cubierta.

## Huecos: geometría exterior medida

Todos los huecos principales del alzado lateral porche tienen dintel en y467,20, equivalente a Z≈+2,50. Alzado principal: dintel y147,64, mismo nivel. Las líneas interiores de marco suelen retranquear1,32pt (~7cm); esto es geometría dibujada de carpintería y no certifica una sección de perfil específica.

| Vista / elemento | Caja exterior PDF [x1,y1,x2,y2] | Ancho×alto calculado (m) | Antepecho (Z) | Contraste |
|---|---|---:|---:|---|
| Principal: primer hueco desde izquierda (despacho por planta) | [408,32;147,64;427,28;177,88] | 1,00×1,60 | ~0,90 | MemoriaV4 despacho1,00×1,50: diferencia de alto0,10m |
| Principal: siguiente ventana | [466,88;147,64;482,00;176,08] | 0,80×1,50 | ~1,00 | Compatible conV2 baño2 |
| Principal: ventana pequeña | [519,32;147,64;530,72;176,08] | 0,60×1,50 | ~1,00 | Compatible conV3 lavadero |
| Principal: puerta de servicio junto lavadero | [540,92;147,64;559,04;194,92] | 0,96×2,50 | 0,00 | Hueco calculado; contrastar ancho de hoja con planta |
| Principal: ventana siguiente | [567,92;147,64;583,04;176,08] | 0,80×1,50 | ~1,00 | Compatible conV2 aseo |
| Principal: puerta principal | [607,28;147,64;632,60;194,92] | 1,34×2,50 | 0,00 | Posición coincide con marco del ALZADO PUERTA PRINCIPAL; no recolocar |
| Principal: último hueco (salón) | [660,56;147,64;698,36;177,88] | 2,00×1,60 | ~0,90 | Compatible conV1 salón |
| Lateral porche: ventanal salónV7 | [455,60;467,20;557,48;514,48] | 5,39×2,50 | 0,00 | Memoria dice2,05m de alto, pero superficie13,47m²=5,39×2,50 y alzado/sec1 representan2,50 |
| Lateral porche: ventanal cocinaV6 | [564,08;467,20;642,20;514,48] | 4,13×2,50 | 0,00 | Compatible con memoria |
| Lateral porche: dormitorio3V5 | [669,68;467,20;698,12;514,48] | 1,50×2,50 | 0,00 | Compatible |
| Lateral porche: dormitorio2V5 | [751,16;467,20;779,60;514,48] | 1,50×2,50 | 0,00 | Compatible |
| Lateral porche: dormitorio1V1 | [812,36;467,20;850,16;497,44] | 2,00×1,60 | ~0,90 | CompatibleV1; dormitorio1 además poseeV5 perpendicular, identificado en planta |
| Trasero: baño1V4 | [633,20;614,56;652,16;642,88] | 1,00×1,50 | ~1,00 | CompatibleV4 |
| Vial: hueco izquierda | [461,72;306,64;491,84;353,92] | 1,59×2,50 | 0,00 | En volumen instalaciones según planta; memoria no asigna tipo específico |
| Vial: hueco derecha | [592,28;306,64;620,60;353,92] | 1,50×2,50 | 0,00 | Verificar visibilidad en profundidad: puede proyectarV5 del dormitorio1 detrás pérgola |

Sección1 confirma los ventanales cocina4,13×2,50 y salón5,39×2,50: para cocina x530,72–608,84; salón615,44–717,20; suelo194,92 y dintel147,64. No se deduce una carpintería de3hojas de los trazos del alzado (no contienen divisiones de hoja); la memoria sí especifica3hojas correderas paraV6/V7.

## Pérgola y cerramiento

Pérgola: sección1 viga longitudinal entre x723,92 y798,32 =3,94m. En alzado vial la viga visible entre x491,84 y575,24 tiene luz4,413m hasta la cara interior del apoyo derecho; dicho apoyo ocupa x575,24–586,64, ancho0,603m. Por tanto la anchura completa es586,64−491,84=94,80pt=5,0165m. Se reconcilia exactamente con planta35: muro instalaciones x307,40–312,08; la pérgola comienza en la cara derecha312,08 y el apoyo frontal derecho ocupa395,60–406,88. Luz de planta395,60−312,08=83,52pt=4,420m y anchura completa406,88−312,08=94,80pt=5,0165m. La diferencia de6mm en la luz está dentro de la cuantización PDF. NO existe contradicción entre luz visible4,41m y huella5,02m. Sección1 muestra soporte exterior entre798,32 y803,00 (~0,25m en dirección longitudinal); largo completo desde x723,92 hasta803,00 =4,185m, equivalente dentro de6mm al largo de planta y542,08–621,28 =4,191m. La luz longitudinal de planta hasta la cara interior del apoyo y616,60 es3,943m frente a3,937m en sección1. Alturas inferior2,50/superior2,85 son consistentes.

Cerramiento independiente en lámina06: y715,36–753,16 =2,00m de alto; x220,04–574,52 =18,76m de longitud proyectada nominal. Puerta vehículos x299,96–413,00 =5,98m; puerta peatonal integrada dentro del panel oscuro izquierdo y hoja entre266,36–288,32 =~1,16m; panel entero223,16–288,32 =~3,45m. Se debe cruzar con planta y anchura efectiva del vial antes de asumir que el dibujo del cerramiento es una elevación exacta de toda la fachada.

Los cierres laterales dibujados en los alzados no tienen una coronación uniforme respectoZ=0: principal izquierda y163,72sobre194,92≈+1,65m; lateral porche y479,44sobre514,48≈+1,85m; trasero derecha y626,80sobre661,84≈+1,85m. Sus alturas respecto de jardín serían~1,80/~2,00m respectivamente. No hay cotas escritas de coronación perimetral ni un perfil topográfico suficiente para atribuir estas variaciones a pendiente, desniveles o tipos de muro. Consultar altura/perfil si el modelo debe reproducirlos exactamente.

## Decisiones que requieren resolver antes de modelar geometría afectada

1. V7 salón: ¿rige altura2,50m de alzado/sec1/superficie, o2,05m escrita en tabla? La evidencia mayoritaria apunta a2,50m, pero hay contradicción documental real.
2. Despacho: ¿rige1,60m de alto medido en alzado y sección2, o1,50m de la memoriaV4? No alterar el hueco para encajar una tabla sin confirmación.
3. Marco de entrada: ¿rige coronación4,75/base3,35 de alzado, o4,90/base3,70 de sección2? Otros cortes apuntan a4,75 de coronación. La discrepancia no se explica por cuantización.
4. Cerramiento: faltan cotas escritas suficientes para consolidar alturas de todos los linderos; contrastar con planta y obtener confirmación si no se resuelve geométricamente.
5. Nivel acabado cubierta, profundidades de piscina y perfiles de carpintería no quedan determinados por estas dos láminas; no inventar espesor del paquete de cubierta ni fondo de piscina.

Archivos de evidencia: recortes vectorialmente rasterizados `crop_principal.png`, `crop_lateral.png`, `crop_seccion1.png`, `crop_seccion2.png`, `crop_seccion3.png`, `crop_seccion4.png`, `crop_cerramiento.png`. `vector_arch_38.json` y `vector_arch_39.json` guardan una selección de trazos arquitectónicos grises y secciones rellenas; no son una reconstrucción completa de las páginas (los contornos negros deben leerse del PDF original).


## Criterio aplicado al preparar los datos para Blender

Tras la instrucción de continuar utilizando sólo el PDF, se guarda `modelo/datos_alturas.json`. Es una elección trazable entre evidencias que discrepan; no se presenta como resolución documental del proyecto. La planta35 gobierna huecos y huella; cubierta37 gobierna paños y petos. La página37 comparte coordenadas con35; únicamente36 requiere registro de aproximadamente+1,68pt para pasar a35.

Se utilizaV7 de2,50m, despacho de1,60m, marco/portal con base3,35 y coronación4,75m, y hoja de acceso peatonal de0,820m de planta36. Los valores alternativos del PDF quedan guardados. Para instalaciones se conserva hueco de planta1,33985m frente alzado1,59385m, que aparenta incluir unos0,25m de pared derecha.

Cubierta central alta: rectángulo exteriorP37 (323,84;169,96)–(406,88;542,08), coronación5,10m; interior (326,60;172,72)–(404,12;539,32). El portal exterior es (247,28;416,44)–(373,52;557,20), coronación4,75m y base3,35m; su forma visible, descontando centralalto, es unaL: (247,28;416,44)→(323,84;416,44)→(323,84;542,08)→(373,52;542,08)→(373,52;557,20)→(247,28;557,20). Vuelos lateralyfrontal de0,8001m: deben quedar abiertos por debajo.

Las alas bajas (dormitorio1 y banda oeste de baños/despacho) y el cuarto instalaciones coronan4,40m. Sus petos sólo se modelan en los tramos explícitos de doble línea de cubierta37. No se añade un recinto cerrado bajo cada rectángulo de cubierta ni una caja única de5,10m.

**Residual transversal adicional confirmado mediante revisión independiente:** alzadoTRASERO y sección3 representan centralalto con ancho98,28pt=5,20065m y borde occidental equivalente aX308,72pt. Cubierta37 lo sitúa enX323,84–406,88 (83,04pt=4,39420m), respaldado por alzadoVIAL y sección4 (83,16pt=4,40055m). Diferencia real~0,80m, superior a cuantización; el modelo conserva cubiertaXY y guarda ese desacuerdo. No debe afirmarse coincidencia total contra todos los alzados.

La lámina de grava puede representarse mediante material sobre una cara de referencia del forjado, registrando queZ3,70 es estructural y no cota final certificada de grava. Se conserva espesor de memoria5cm como información, pero no se inventa el nivel acumulado ni pendientes de drenaje. El vuelo de canto0,20m representado a la izquierda de sección4 corresponde a la marquesina de terraza este, no al paño/portal de entrada oeste (ver derivación siguiente).

Cerramiento: evidencia oeste1,80m y este2,00m desde jardín−0,15m, con coronaciones1,65/1,85m. Frente y trasero2,00m se pueden representar como interpretación explícita a partir de sus vistas, sin inventar topografía ni afirmar perfil continuo detallado. Los encuentros entre alturas permanecen limitados por el detalle del documento.


## Marquesina horizontal sobre salón y cocina — revisión cruzada final

La franja gris del ALZADO LATERAL PORCHE corresponde a un voladizo horizontal de canto aproximado0,20m, diferenciado del portal oeste y de la pérgola frontal. No debe omitirse por carecer de contorno en la planta de cubierta37.

- Lateral porche: franja x449,00–655,40/y447,40–451,12; suelo514,48. Z superior3,54965m/inferior3,35280m, largo206,40pt=10,922m. Se registra x449,00 con testero de salónY542,08pt de planta35; el extremo655,40 equivale aY335,68pt.
- Vial público: franja x586,64–629,12/y286,84–290,56; suelo353,92. MismaZ y proyección42,48pt=2,2479m. El arranque586,64 coincide con fachadaX406,88 de planta35; extremo629,12 equivale aX449,36.
- Sección4: franja izquierda x585,32–627,80/y577,96–581,80; suelo645,04. Las coordenadas transversales están invertidas: cara627,80 corresponde a fachadaX406,88 y extremo585,32 aX449,36. Repite profundidad2,2479m y canto≈0,20m.

La huella derivada es rectángulo **X406,88–449,36/Y335,68–542,08pt de planta35**. Se propone modelar como voladizo plano **Z3,35–3,55m**, largo10,922m y fondo2,2479m, sin pilares ni recinto inferior inventados. Su contorno no está representado en cubierta37; esto queda identificado como omisión/discrepancia documental, pero la profundidad procede de dos vistas concordantes y no de una elección estética. Se conserva la representación por separado en `cubierta.marquesina_terraza_derivada` del JSON.


## Cerramiento frontal: rejillas y paños de muro medidos

Archivo `modelo/datos_cerramiento_frontal.json`, regenerable mediante `extraer_cerramiento_frontal.py`. Coordenadas de aberturas en esquema de PDF38:

- Rejilla1: [424,28;715,36;488,12;743,68]pt.
- Rejilla2: [499,40;715,36;563,24;743,68]pt.
- Cada abertura mide3,3782×1,4986m. Desde base de muro753,16pt, antepecho gráfico0,50165m y coronación2,00025m. Referidas al datum jardín−0,15m: Z0,35165–1,85025m.
- Tres machones: x413,00–424,28;488,12–499,40;563,24–574,52pt, todos0,5969m de ancho y entre y715,36–753,16pt. Zócalo continuo entre y743,68–753,16pt.
- Las rejillas llegan a la coronación. El esquema NO contiene dintel/muro blanco por encima: una banda blanca Z1,72–1,85 sobre los huecos no coincide con documento.
- Marco exterior1 [424,64;715,36;487,76;743,44], claro interior1 [426,08;716,92;486,32;741,88]; marco exterior2 [499,76;715,36;563,00;743,44], claro interior2 [501,20;716,92;561,44;741,88]. El JSON conserva estos cuadros y los trazos.
- Ambas rejillas tienen28pares de líneas verticales interiores y11pares horizontales. Se conserva ancho frontal dibujado y posición exacta de cada par. Profundidad normal de perfiles NO definida; representar caras/trazos sin inventar una sección tridimensional.

Registro elegido: extremo derecho de esquema x574,52 se ancla al extremo frontal/derecho de parcela(18,61185;1,02235)m; la dirección del lindero inclinado determina el eje de medida. No se reescala el esquema ni se alteran puertas de planta. Intervalos de rejillas a lo largo del lindero: [10,689708;14,067908] y [14,664808;18,043008]m. Sus XYZ completos quedan guardados; aplicar dirección verdadera y desplazamiento al centro del muro derivado de su espesor en planta0,254m.

Residual de registro: longitud del esquema18,758m frente al lindero18,639908m, diferencia0,117992m. El inicio del esquema saldría fuera del origen−0,118m; NO modelarlo ni mover la parcela para ajustar. Al anclar el extremo derecho, la jamba de vehículos del esquema queda18mm respecto de la cara de poste de planta36 registrada; conservar acceso de planta y reconocer ese residual. La hoja peatonal de0,820m continúa gobernada por planta frente1,162m del esquema.
