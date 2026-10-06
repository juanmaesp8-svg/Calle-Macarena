"""Registra ajustes milimétricos propuestos; no cambia modelo ni cotas fuente."""
from pathlib import Path
import json
P=Path(__file__).parent
D=json.loads((P/'auditoria_planta_final.json').read_text())
F=D['factor_m_por_pt']
rows=[]
for n,val,vect,ref in [('Ancho interior trastero',7.15,7.1501,61313),('Profundidad interior trastero',3.94,3.94335,61321),('Profundidad norte interior–sur exterior',4.19,4.191,61329),('Hueco bruto puerta norte',.96,.9652,61536),('Hueco puerta norte según extremos línea cota',.96,.95885,61536),('Portón sur, sin cota escrita específica',None,4.0005,59561),('Piscina ancho según bordes azul/solería izquierda',3.5,3.49885,54387),('Piscina ancho según línea cota derecha',3.5,3.5052,62204),('Piscina longitud',5,5.0038,62196)]:
 rows.append({'dimension':n,'cota_directa_m':val,'medida_vector_m':vect,'error_vector_m':None if val is None else round(vect-val,6),'error_mm':None if val is None else round((vect-val)*1000,3),'seqno_pdf':ref,'mayor_6_35mm':False if val is None else abs(vect-val)>.0063501})
proposal={
 'estado':'Propuesta de implementación para root; datos canónicos no modificados',
 'criterio':'Las cotas escritas rigen distancias. Conservar anclajes existentes y caras comunes; corregir sólo extremos libres por milímetros. No trasladar ni redimensionar estancias a partir de residuos del trazado.',
 'registro':'X/Y en metros, origen y escala V1. Registro de planta izquierda por parcela +112,68pt enX; Yigual.',
 'tabla_directa_vector':rows,
 'anclajes_confirmados':[
 {'elemento':'Cara interior oeste del nuevo trastero','x_m':3.2512,'evidencia':'V2left154,40pt +112,68=267,08pt V1, coincide con cara interior oeste instalaciones preexistente.'},
 {'elemento':'Cara interior norte del nuevo trastero','y_m':12.0777,'evidencia':'y542,08pt en ambas versiones, cara sur del muro salón/trastero.'},
 {'elemento':'Cara exterior este nuevo trastero','x_m':10.64895,'evidencia':'V2left294,20pt +112,68=406,88pt V1, coincide con línea exterior derecha de antigua pérgola y cuerpo principal.'},
 {'elemento':'Extremo este hueco puerta norte','x_m':8.2677,'evidencia':'V2left249,20pt +112,68=361,88pt; V2right633,44pt−271,56=361,88pt. Coinciden relleno y extremo de cota.'},
 {'elemento':'Fachada oeste común vivienda V1','x_m':3.00355,'evidencia':'Cara exterior x262,40pt del modelo V1. V2left149,60+112,68=262,28pt difiere6,35mm por registro/quantización; conservar continuidad con fachada V1 evita escalón artificial de6mm.'}],
 'caras_trastero_propuestas_m':{
 'interior_oeste_x':3.2512,
 'interior_este_x':10.4012,
 'interior_norte_y':12.0777,
 'interior_sur_y':8.1377,
 'exterior_sur_y':7.8877,
 'exterior_este_x':10.64895,
 'exterior_oeste_x_continuidad_vivienda':3.00355,
 'puerta_norte_extremo_este_x':8.2677,
 'puerta_norte_extremo_oeste_x':7.3077,
 'espesor_muro_sur_calculado_de_cotas_m':.25},
 'desplazamientos_locales_desde_vector_m':{
 'interior_este_x':-.0001,
 'interior_sur_y':.00335,
 'exterior_sur_y':.001,
 'puerta_norte_extremo_oeste_x':.0052},
 'restricciones_resultantes':{'interior_ancho_m':7.15,'interior_profundo_m':3.94,'profundo_hasta_exterior_sur_m':4.19,'hueco_norte_m':.96,'sin_modificar_norte_salon_y':True,'sin_modificar_oeste_interior_x':True,'sin_modificar_eje_exterior_este_x':True},
 'espesor_laterales':'No hay cota escrita de0,25m para laterales. Conservar caras exteriores comunes documentadas produce espesores0,24765m oeste y0,24775m este; no imponer0,25m a costa de desplazar fachadas.',
 'puerta_norte_hoja':'Cota0,96 es hueco bruto. Hoja gráfica0,81915m (~0,82), jambas~0,07m. Abre hacia trastero, bisagra oeste. Altura2,03m confirmada por usuario; no atribuirla a esta planta.',
 'porton_sur':'Abertura gráfica4,0005m; sin cota escrita exclusiva. Nominal4,00m es deducción cercana y compatible con29,17m²; conservar centro o extremo documentado y declarar0,5mm de ajuste si se adopta4,00.',
 'superficie':'No forzar29,17. El cómputo nominal interior7,15×3,94 + umbral4,00×0,25=29,171m² explica rotulación. Etiqueta29,17 no obliga a deformar paredes.',
 'piscina_propuesta_m':{'anclaje_lateral_oeste_x':11.7094,'anclaje_norte_y':10.8585,'dimension_x':3.5,'dimension_y':5.0,'nuevo_este_x':15.2094,'nuevo_sur_y':5.8585,'ajustes_desde_izquierda_vector_m':{'este_x':.00115,'sur_y':.0038},'criterio':'Mantener los bordes oeste/norte registrados; satisfacer dimensiones escritas3,50×5,00 mediante caras libres este/sur. Mantener posiciones XY de escalones, recortando su terminación a cara este exacta.'},
 'otras_cotas_mayor_6_35mm':[],
 'todos_los_datos':'auditoria_planta_final.json contiene93cotas, extremos y93asociaciones vectoriales; estas cotas se separan de muebles y máscaras gráficas.'
}
notes={
 61700:('Encimera longitudinal cocina','La línea de cota roja va367,00–433,72pt, pero el relleno real encimera va367,12–433,60pt:3,51790m, error−2,10mm respecto3,52. Diferencia de la línea de dimensión, no necesidad de desplazar muro.'),
 62116:('Aseo, relación con equipamiento','Línea de cota1,02va379,12–398,56pt; no es dimensión total de recinto. Diferencia8,70mm; aplicar nominal si se reproduce ese equipamiento, sin mover límites del aseo.'),
 61716:('Cocina, separación a isla','Línea roja incluye381,52pt, mientras isla real comienza381,40pt: distancia348,88–381,40=1,72085m, error+0,85mm respecto1,72. No altera muro.'),
 62060:('Baño2, profundidad interior','Vector285,16–335,68pt mide2,67335m frente cota2,68m:−6,65mm, supera una unidad de cuantización en0,30mm. Se identifica como discrepancia menor; no desplazar dormitorios o baño sin resolver sus demás cotas comunes.'),
 61676:('Isla cocina, longitud','Línea roja381,40–419,32pt mide2,00660m, pero relleno real381,40–419,20pt mide2,00025m, error+0,25mm. Cota2,00rige mueble.'),
 61421:('SofáL, fondo','Línea roja462,40–492,76pt mide1,60655m, relleno real462,52–492,64pt mide1,59385m. Nominal1,60rige asset; ambos extremos de línea sobrepasan relleno0,12pt. No es pared.')}
for e in D['cotas_discrepancia_mayor_una_unidad_grafica']:
 q=dict(e);q['contexto_preciso'],q['interpretacion']=notes.get(e['linea_central_seqno_pdf'],('No clasificado','Verificar contra geometría fuente.'))
 proposal['otras_cotas_mayor_6_35mm'].append(q)
(P/'auditoria_planta_final_ajustes.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2))
print('Guardado ajustes',len(proposal['otras_cotas_mayor_6_35mm']))
