# Auditoría V2 — alturas, huecos y sustitución del anexo por trastero

Fuentes examinadas: `fuentes/planta_final_proyecto_obra.pdf` (una página A3, lámina01: dos representaciones de la misma planta, con y sin cotas); `fuentes/proyecto_basico.pdf`, páginas38–39, alzados y secciones anteriores; y su extracción `modelo/datos_alturas.json`. Los documentos se utilizan como evidencia del proyecto. No se ha creado ni modificado geometría3D. Durante esta revisión, el usuario confirmó explícitamente los niveles del nuevo trastero: forjado inferior+3,35/superior+3,70m, peto+4,40m, puerta interior2,03m y portónfrontal2,50m. Esa confirmación resuelve las alturas pendientes; es fuente **usuario**, no cota delPDF.

## Qué cambia inequívocamente

La nueva planta rotula un único **TRASTERO29,17m²** en el rectángulo delantero que anteriormente se repartía entre cuarto de instalaciones y barbacoa/comedor bajo pérgola. Se elimina el tabique longitudinal que los separaba; aparece cerramiento continuo al este y el testero frontal se dispone con una abertura central ancha. La puerta anterior del cuarto de instalaciones deja de corresponder al nuevo recinto.

En la representación izquierda de la planta final, el trastero queda entre X149,60–294,20pt e Y535,48–621,28pt; el recinto interior empieza en Y542,08pt. Los intervalos específicos quedan recogidos en JSON. Registro con básico: desplazamiento aproximado+112,68pt enX por parcela, o+112,80pt por cara oeste de vivienda; Yse conserva. La diferencia0,12pt (~6,35mm) entre registros refleja cuantización/capas, no un rediseño del emplazamiento.

Cotas escritas del recinto: **7,15m** de ancho interior, **3,94m** hasta cara interior del muro frontal y **4,19m** hasta el exterior en el hueco frontal. La diferencia0,25m corresponde a su espesor de muro/umbral frontal. El cómputo29,17m² es compatible con `7,15×3,94 + 4,00×0,25 =29,171m²`: interior rectangular más umbral de la abertura frontal. Esta es una deducción aritmética que explica la superficie; no obliga a deformar el rectángulo. El ancho4,00m de abertura frontal es medido gráficamente, no una cota escrita asignada de forma inequívoca a ese hueco.

## Huecos nuevos

| Hueco | Evidencia XY de planta final izquierda | Ancho | AlturaZ |
|---|---|---|---|
| Salón→trastero, en muro norte | X230,96–249,20/Y535,48–542,08pt | Cota escrita0,96m; gráfico0,9652m | **2,03m, confirmada por usuario; no aparece enPDF** |
| Abertura frontal trastero→aparcamiento, frente al vial | X184,16–259,76/Y616,60–621,28pt | Gráfico4,0005m | **2,50m, confirmada por usuario; no aparece enPDF** |

La abertura norte muestra una hoja abatible hacia el trastero, con bisagra en lado izquierdo/oeste. El testero frontal tiene interrupción del cerramiento, pero no una hoja o mecanismo representados que permitan determinar si es corredera, seccional, abatible o hueco permanentemente abierto. No añadir una tipología de portón por intuición.

El alzado anterior al vial muestra la antigua puerta de instalaciones≈1,34m en planta y≈1,59m en su dibujo frontal, con altura≈2,50m. **No corresponde a la nueva abertura central de4,00m** y no permite certificar su altura. La nueva puerta salón→trastero tampoco existía en ese testero del salón en la versión anterior: no heredar automáticamente2,50m de otra puerta: enV2 el usuario ha confirmado una altura distinta de2,03m para esta puerta interior.

No se identifican ventanas en los nuevos cerramientos oeste, este o frontal del trastero. No añadirlas a partir de la composición anterior.

## Niveles que pueden conservarse y límites de esa herencia

| Dato del básico | Valor | Aplicabilidad en V2 |
|---|---:|---|
| Datum suelo vivienda | +0,00m | Se conserva como referencia de vivienda; anteriormente instalaciones y pavimento de pérgola aparecen al mismo nivel. Es referencia coherente para la nueva zona, **sin convertirla en cota nueva expresamente acotada de trastero**. |
| Jardín | −0,15m | Conservable como dato del emplazamiento existente mientras no se modifique terreno. |
| Forjado vivienda existente | Inferior+3,35/superior+3,70m | Conservable en volumen principal no modificado. **No demuestra la existencia ni las caras del nuevo forjado sobre antigua pérgola.** |
| Peto alto cuerpo central | +5,10m | Conservable sólo en paño principal existente, con las discrepancias anteriores ya registradas. |
| Peto bajo alas existentes | +4,40m | Conservable sólo en sus tramos no alterados. La antigua cubierta de instalaciones cubría únicamente la franja oeste del nuevo recinto; no autoriza extender automáticamente esa coronación a todo el trastero. |
| Portal de entrada | Base+3,35/coronación+4,75m | Conservable en elementos existentes cuya posición/planta no cambia. Debe distinguirse del nuevo techo del anexo. |
| Cielorraso vivienda | +3,20m | Conservable en estancias existentes; no está documentado para trastero. |
| Marquesina terraza este | Inferior+3,35/superior+3,55m | Existente según básico y proyecciones anteriores, termina junto al testero del salón. No constituye cubierta de nueva zona trastero. |
| Pérgola anterior | Vigas inferior+2,50/superior+2,85m | **No heredable como techo del recinto nuevo.** El usuario sustituye esa zona y la planta final la cierra. |

La planta final no contiene sección, alzado, planta de cubierta ni cotas de dintel, forjado o peto del trastero. Tiene cotas horizontales de una planta; **4,19m es longitud de recinto, no altura**. La aplicación de forjado3,35/3,70 y peto4,40 en el anexo completo queda autorizada por la confirmación del usuario; no es medición deducida delPDF. Copiar en cambio la antigua pérgola de2,85m contradiría la confirmación recibida.

## Elementos antiguos que no deben reutilizarse automáticamente

1. Las seis vigas del modelo de pérgola y sus cortes por vuelo de portal: pertenecen al comedor exterior abierto sustituido. No conservarlas como cubierta interior del trastero sin indicación nueva.
2. Pilar delantero derecho de pérgola con coronación2,85m: queda absorbido/sustituido por un cerramiento este completo; no mantenerlo como poste independiente de altura anterior ni extruir todo el nuevo muro a partir de ese poste.
3. Tabique longitudinal entre instalaciones y barbacoa: desaparece. Su antiguo cerramiento no puede quedar oculto dentro del nuevo recinto.
4. Puerta frontal antigua de instalaciones, sus jambas y hueco1,34m: desaparecen a favor del hueco central ancho. No conservar ambas puertas.
5. Techo, petos y slab exclusivos de antigua instalaciones: conservar su evidencia, pero no extenderlos a la zona que antes estaba abierta. La continuidad de techo/forjado y forma de remate de todo el nuevo anexo necesita definición vertical.
6. Mobiliario de barbacoa y comedor de piscina: la nueva planta los reemplaza porRACK/TABLAS/GYM/MOTO. Son anotaciones/representaciones de uso, no cotas de altura de edificación.

## Esquina posterior

La pequeña zona noroeste sigue rotulada **TENDEDERO7,00m²**. Sus nueve rellenos de muros coinciden con la antigua planta dentro de desplazamiento y cuantización: contorno abierto por el lado de acceso, no una segunda edificación nueva definida con cubierta. No hay nueva planta de cubierta ni nuevosZ para esa zona. No transformarla en caseta, cuarto cubierto o nuevo trastero por su apariencia rectangular.

## Definición vertical confirmada y detalles aún no documentados

El usuario ha autorizado expresamente forjado inferior+3,35/superior+3,70m (canto0,35m), peto+4,40m, puerta interior2,03m y portónfrontal2,50m. Las aberturas se mantienen en las posiciones/ancho de la planta final. Se puede continuar el modelo con esa definición, etiquetándola como confirmación del usuario y conservando el datum previo de suelo+0,00m.

El sistema de cierre del portónfrontal no está dibujado; no añadir hojas o mecanismo que no se haya indicado. Tampoco hay nueva cota de cielorraso del trastero, acabado final de cubierta, pendientes o detalle del encuentro entre paños. La cubierta antigua de portal de4,75m vuela unos0,80m sobre el extremo norte de la zona ampliada; se debe resolver la unión geométrica conservando el elemento existente, sin añadir petos duplicados dentro de su intersección con el nuevo anexo.

La pequeña esquina posterior sigue siendo el tendedero existente. No aparece una caseta nueva ni una altura nueva que requiera confirmación porV2.
