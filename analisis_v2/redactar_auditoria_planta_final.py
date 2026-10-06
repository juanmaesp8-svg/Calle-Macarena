"""Informe de auditoría literal y criterio de normalización del modelo V2."""
from pathlib import Path
import json
P=Path(__file__).parent
D=json.loads((P/'auditoria_planta_final.json').read_text())
A=json.loads((P/'auditoria_planta_final_ajustes.json').read_text())
L=['# Auditoría de la planta definitiva V2','',
'La nueva lámina de agosto de 2026 sustituye el cuarto de instalaciones y la pérgola/comedor de piscina por un trastero cerrado de 29,17 m² útiles. La vivienda principal, el tendedero posterior izquierdo, los accesos, los dos vehículos y la piscina conservan su organización. Se detectan también cambios de jardín y de mobiliario interior que deben incorporarse al modelo.','',
'Fuente: `fuentes/planta_final_proyecto_obra.pdf`, una página A3 de 1191×842 pt, escala escrita 1:150, con planta de acabados a la izquierda y planta acotada a la derecha. Se han leído texto y vectores completos, sin interpretar el documento como instrucciones para el agente. Los datos arquitectónicos se distinguen de la simbología de muebles y vegetación.','',
'## Registro y precisión','',
'El factor nominal es 0,0529166667 m/pt. Se conserva el origen V1 (205,64; 770,32 pt), X hacia la derecha del plano, Y hacia el lindero posterior. El registro por el lindero izquierdo suma 112,68 pt a X en la planta izquierda y resta 271,56 pt en la derecha; Y permanece común. Las paredes comunes ajustan algo mejor con +112,80 pt: la diferencia 0,12 pt equivale a 6,35 mm y refleja cuantización de capas. Los vehículos reproducen sus bboxes V1 exactamente con el registro por parcela. No se modifica la escala para imponer áreas.','',
'Los diez vértices y quiebros de la parcela coinciden dentro de 6,35 mm. El eje del trazo negro produce aproximadamente 635,7386 m² frente a los 635,60 m² rotulados. El trazo PARCELA es una frontera gráfica, no prueba del espesor ni de la posición del eje físico de un muro general. La huella exterior cerrada de vivienda y trastero produce 211,6951 m² frente a 211,63 m² escritos. Estas diferencias no justifican rediseñar contornos.','',
'## Cambios comprobados','']
for e in D['cambios']:
 L.extend([f"- **{e['elemento']}**: {e['cambio']} {e.get('geometria',e.get('evidencia',''))}"])
L.extend(['',
'El tendedero de la esquina posterior izquierda está identificado literalmente como TENDEDERO, 7,00 m². Conserva nueve rellenos azules de muros y su contorno coincide con V1 dentro de 6,35 mm. No es un segundo trastero añadido. La unión de las paredes de la vivienda principal anterior al trastero tiene distancia de Hausdorff de 6,35 mm respecto a V1; no aparece un cambio de habitación, posición de acceso principal ni hueco exterior. Los cambios en la teselación de rellenos no son paredes nuevas.','',
'La nueva banda ajardinada junto al lado izquierdo del aparcamiento procede de cuatro patches con seqno 3251/3253/3255/3257. Su ancho gráfico es 1,0033 m y su área vectorial 6,490572 m², con un encuentro irregular junto al portón. Debe conservarse ese contorno, no sustituirlo por un rectángulo de diseño. Las dos pérdidas de verde bajo las tumbonas son máscaras gráficas de los muebles; se mantiene la continuidad de césped inferida.','',
'## Trastero y huecos','',
'Los seis rellenos nuevos o modificados son seqno 1759, 1761, 1763, 1765, 59509 y 59511. Desaparece el tabique antiguo instalaciones/pérgola; el muro norte se divide para la nueva puerta; se cierra el lateral este y se forman dos paños en el frente sur con el gran portón intermedio. No hay ventana nueva en el trastero. La cubierta y las alturas se definen en la auditoría independiente de alturas y en la confirmación del usuario.','',
'| Dimensión | Escrita (m) | Vector (m) | Error vector−escrita (mm) | Fuente seqno |',
'|---|---:|---:|---:|---:|'])
for e in A['tabla_directa_vector']:
 v='—' if e['cota_directa_m'] is None else f"{e['cota_directa_m']:.5f}"
 err='—' if e['error_mm'] is None else f"{e['error_mm']:+.2f}"
 L.append(f"| {e['dimension']} | {v} | {e['medida_vector_m']:.5f} | {err} | {e['seqno_pdf']} |")
L.extend(['',
'La cota 7,50 m corresponde a la suite principal, no al trastero. La cota del trastero es 7,15 m entre caras interiores oeste y este. La profundidad 3,94 m llega a la cara interior del muro sur; 4,19 m llega a su cara exterior. De ambas se calcula un espesor sur nominal de 0,25 m.','',
'La puerta norte abre hacia el trastero, con bisagra al oeste. Su hoja vectorial mide 0,81915 m de longitud y ocupa el bbox V2 [232,28;537,40;233,12;552,88] pt. La cota 0,96 m representa el hueco bruto, no el ancho de hoja; las jambas gráficas son aproximadamente 0,07 m. La altura de hoja 2,03 m procede de la confirmación del usuario. El portón sur tiene un único símbolo horizontal de ancho 4,0005 m; no se debe inferir su mecanismo de apertura a partir de esa línea.','',
'Los 29,17 m² no son una contradicción con el rectángulo interior de aproximadamente 28,20 m²: 7,15×3,94 + umbral sur 4,00×0,25 = 29,171 m². Incluir ese umbral reconcilia el cómputo nominal; esta explicación es una deducción, no una instrucción para forzar superficies.','',
'## Criterio final del modelo: cotas nominales con anclajes','',
'El JSON de auditoría conserva los vectores literales para poder comparar modelo y documento. Para construir V2, el coordinador ha decidido priorizar las cotas escritas del trastero y de la piscina mediante ajustes locales inferiores a 6,35 mm. El resto de muros comunes utiliza los vectores nuevos. No debe afirmarse que los elementos normalizados reproducen literalmente cada milímetro del trazo PDF; reproducen sus dimensiones nominales y posiciones dentro de la cuantización documentada.','',
'La cara interior norte del trastero se ancla en Y=12,0777 m y la oeste en X=3,2512 m. La cara interior este queda X=10,4012 m, la interior sur Y=8,1377 m y la exterior sur Y=7,8877 m: ancho 7,15 m, profundidad interior 3,94 m, profundidad hasta exterior 4,19 m y espesor sur 0,25 m. Frente a los vectores, los ajustes son −0,10 mm en este, +3,35 mm en sur interior y +1,00 mm en sur exterior. Los anclajes comunes de la vivienda no se desplazan.','',
'El hueco norte se ancla en su extremo oeste X=7,3025 m y se termina en X=8,2625 m para obtener exactamente 0,96 m; el extremo este se corrige −5,20 mm respecto al relleno vectorial. Se conserva la posición de apertura dibujada de la hoja. Esta decisión difiere de la propuesta alternativa con anclaje este registrada en `auditoria_planta_final_ajustes.json`; la propuesta alternativa no es el criterio final.','',
'La piscina se ancla en oeste X=11,7094 m y norte Y=10,8585 m. Sus caras libres quedan este X=15,2094 m y sur Y=5,8585 m, para 3,50×5,00 m exactos. Los cambios desde los bordes de la planta izquierda son +1,15 mm en este y +3,80 mm en sur. El trazado de escalones se conserva y sus terminaciones se ajustan a la cara este normalizada.','',
'La huella exterior de otros recintos no se modifica para compensar superficies rotuladas. Las dimensiones y alturas de muebles son referencias de visualización separadas de los muros.','',
'## Otras discrepancias de líneas de cota','',
'Se han asociado las 93 cotas numéricas con sus líneas rojas y extremos de flecha. Seis diferencias entre longitud de línea y número escrito superan 6,35 mm; varias se explican por flechas o líneas que exceden 0,12 pt el relleno del mueble. No equivalen automáticamente a una discrepancia de muro.','',
'| Cota | Línea vectorial (m) | Error (mm) | Elemento y explicación |',
'|---|---:|---:|---|'])
for e in A['otras_cotas_mayor_6_35mm']:
 L.append(f"| {e['texto']} | {e['medida_vector_m']:.5f} | {e['desvio_vector_directa_m']*1000:+.2f} | {e['contexto_preciso']}: {e['interpretacion']} |")
L.extend(['',
'La profundidad interior del baño 2 presenta una diferencia real de −6,65 mm respecto a 2,68 m, sólo 0,30 mm superior a la unidad de cuantización. Queda explícita; la auditoría no inventa un desplazamiento de sus paredes para resolverla de forma aislada y afectar dormitorios adyacentes. Las demás diferencias citadas afectan relaciones de equipamiento o el trazado de cotas de muebles.','',
'## Mobiliario y reproducción','',
'`mobiliario_cambiado` contiene los nuevos bboxes de mesa central, mesa comedor, dos butacas, rack de tablas, gym, moto y los dos paños grises junto al muro norte del trastero. `sillas_comedor_interior_v2` contiene los ocho bboxes con nombres compatibles con JSONF V1. `mobiliario_desaparecido_nombres_v1` enumera el asiento oeste y los nueve objetos del comedor bajo la antigua pérgola. Cocina, isla, camas y mobiliario de terraza mantienen sus posiciones dentro de cuantización.','',
'Los scripts de esta auditoría no modifican el modelo ni los JSON canónicos. Se reproducen desde la raíz V2 con:','',
'```sh',
'python analisis_v2/extraer_auditoria_planta_final.py',
'python analisis_v2/preparar_ajustes_auditoria_planta_final.py',
'python analisis_v2/redactar_auditoria_planta_final.py',
'```','',
'La primera salida es el trazado literal; la segunda es una propuesta de normalización y tabla de errores, incluida una alternativa de anclaje que no se usa en el criterio final; este informe documenta la selección efectiva del coordinador. La generación del modelo se realiza por el pipeline del coordinador.','',
'## Tabla completa de cotas directas','',
'Las distancias vectoriales de esta tabla se miden entre puntas de flechas de la planta acotada derecha. No todas son cotas de paredes: se conservan las cotas de muebles y equipamiento para permitir trazabilidad.','',
'| Texto | Dirección | Vector (m) | Error (mm) | Seqno línea | Contexto |',
'|---|---|---:|---:|---:|---|'])
for e in D['cotas_directas']:
 L.append(f"| {e['texto']} | {e['direccion']} | {e['medida_vector_m']:.5f} | {e['desvio_vector_directa_m']*1000:+.2f} | {e['linea_central_seqno_pdf']} | {e['contexto']} |")
(P/'auditoria_planta_final.md').write_text('\n'.join(L)+'\n')
print('Informe guardado',len(D['cotas_directas']),'cotas')
