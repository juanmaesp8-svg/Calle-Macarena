"""Extrae geometría XY vectorial del PDF, sin modificar planos ni forzar superficies."""
from pathlib import Path
import json,math,collections
import fitz
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'fuentes/proyecto_basico.pdf'
OUT=ROOT/'modelo/datos_planta.json'
F=127/2400
ORIGIN=(205.64,770.32)
def pt(p):return [round(float(p[0]),4),round(float(p[1]),4)]
def xy(p):return [round((p[0]-ORIGIN[0])*F,6),round((ORIGIN[1]-p[1])*F,6)]
def bbxy(r):return [round((r[0]-ORIGIN[0])*F,6),round((ORIGIN[1]-r[3])*F,6),round((r[2]-ORIGIN[0])*F,6),round((ORIGIN[1]-r[1])*F,6)]
def poly(name,points,source=None):
 return {'nombre':name,'poligono_pdf_pt':[pt(p) for p in points],'poligono_xy_m':[xy(p) for p in points],'fuente':source,'area_m2':round(abs(sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))/2)*F*F,6)}
def boundaries(d):
 edges=[]
 for it in d['items']:
  if it[0]=='l': edges.append((tuple(pt(it[1])),tuple(pt(it[2]))))
  elif it[0]=='qu':
   q=it[1];vs=[tuple(pt(q.ul)),tuple(pt(q.ur)),tuple(pt(q.lr)),tuple(pt(q.ll))];edges.extend(zip(vs,vs[1:]+vs[:1]))
  elif it[0]=='re':
   r=it[1];vs=[(r.x0,r.y0),(r.x1,r.y0),(r.x1,r.y1),(r.x0,r.y1)];edges.extend(zip(vs,vs[1:]+vs[:1]))
 counts=collections.Counter(tuple(sorted(e)) for e in edges if e[0]!=e[1])
 bd=[list(e) for e,n in counts.items() if n%2]
 polys=[]
 while bd:
  a,b=bd.pop(0);vs=[a,b]
  while vs[-1]!=vs[0]:
   found=False
   for i,e in enumerate(bd):
    if vs[-1] in e:
     q=e[1] if e[0]==vs[-1] else e[0];vs.append(q);bd.pop(i);found=True;break
   if not found:break
  if len(vs)>3 and vs[-1]==vs[0]:vs.pop();polys.append(vs)
 return polys
p=fitz.open(PDF)
d35=p[34].get_drawings();d37=p[36].get_drawings()
data={'version':1,'estado':'datos_XY_extraidos_del_PDF_para_modelo_documental','origen_pdf_pt':list(ORIGIN),'factor_m_por_pt':F,'ejes':'X derecha de plano; Y hacia lindero trasero; Z suelo vivienda=0','paginas':{'base':35,'cubierta':37,'distribucion_vegetacion':36},'resolucion_vector_m':.00635,'criterio':'Coordenadas vectoriales a escala nominal 1:150; no ajustar geometría para imponer áreas declaradas. Elementos sin dimensiones suficientes se identifican con null, no se rediseñan.','muros':[],'tendedero':[],'huecos_exteriores':[],'cesped_patches':[],'pavimentos':{},'pergola':{},'piscina':{},'referencias':{},'incertidumbres':[]}
for d in d35:
 r=d['rect'];c=d.get('fill')
 if d['layer']=='000 SOBREADO' and c and abs(c[0]-.38824)<.0005 and abs(c[1]-.41569)<.0005 and r.x0<600:
  target='tendedero' if r.x1<266 and r.y1<126 else 'muros'
  n=len(data[target])+1
  ps=boundaries(d)
  # Contornos tessellados conservados, con bbox sólo como envolvente auxiliar.
  entry={'nombre':f'{target}_{n:03d}','fuente_pagina':35,'capa':d['layer'],'seqno_pdf':d['seqno'],'bbox_pdf_pt':list(r),'bbox_xy_m':bbxy(r),'poligonos_pdf_pt':ps,'poligonos_xy_m':[[xy(v) for v in vs] for vs in ps],'espesor_grafico_min_m':round(min(r.width,r.height)*F,6),'altura_m':None,'clasificacion':'tabique_cerramiento' if min(r.width,r.height)*F>=.085 else 'elemento_fino_azul_posible_armario_carpinteria','area_bbox_m2':round(r.width*r.height*F*F,6)}
  if target=='tendedero':entry['grupo_modelo']='tendedero'
  elif r.y0>=616 and r.x0>=395:entry['grupo_modelo']='pergola_pilar_frontal_derecho'
  elif r.y0>=542:entry['grupo_modelo']='cuarto_instalaciones'
  else:entry['grupo_modelo']='vivienda'
  data[target].append(entry)
# Huecos: los intervalos son vacíos exactos entre rellenos de cerramiento en planta35.
huecos=[
 ('V_bano1_norte','C. baño nº1','N',(276.56,122.44,295.40,129.04),'V4'),
 ('V_despacho_oeste','Despacho','W',(262.40,226.60,269.00,245.44),'V4'),
 ('V_bano2_oeste','C. baño nº2','W',(262.40,285.16,269.00,300.28),'V2'),
 ('V_lavadero_oeste','Lavadero','W',(262.40,337.60,269.00,348.88),'V3'),
 ('P_lavadero_oeste','Lavadero','W',(262.40,359.08,269.00,377.32),None),
 ('V_aseo_oeste','Aseo','W',(262.40,386.20,269.00,401.32),'V2'),
 ('P_principal_oeste','Hall entrada','W',(262.40,425.56,269.00,450.88),None),
 ('V_salon_oeste','Salón comedor','W',(262.40,478.84,269.00,516.64),'V1'),
 ('V_dormitorio1_este','Dormitorio nº1','E',(446.60,141.04,453.20,178.84),'V1'),
 ('V_dormitorio1_sur','Dormitorio nº1','S',(412.64,190.72,440.96,197.32),'V5'),
 ('V_dormitorio2_este','Dormitorio nº2','E',(400.28,211.60,406.88,239.92),'V5'),
 ('V_dormitorio3_este','Dormitorio nº3','E',(400.28,293.08,406.88,321.40),'V5'),
 ('V_cocina_este','Cocina','E',(400.28,348.88,406.88,427.00),'V6'),
 ('V_salon_este','Salón comedor','E',(400.28,433.60,406.88,535.48),'V7'),
 ('P_instalaciones_sur','Cuarto instalaciones','S',(282.08,616.60,307.40,621.28),None),
]
for name,room,side,r,typ in huecos:
 width=(r[3]-r[1] if side in ('W','E') else r[2]-r[0])*F
 if side in ('W','E'): endpoints=[((r[0]+r[2])/2,r[1]),((r[0]+r[2])/2,r[3])]
 else:endpoints=[(r[0],(r[1]+r[3])/2),(r[2],(r[1]+r[3])/2)]
 data['huecos_exteriores'].append({'nombre':name,'estancia':room,'fachada_local':side,'tipo_documental_propuesto':typ,'tipo_criterio':'coincidencia ancho y ubicación; confirmar con alzado y memoria','bbox_pdf_pt':list(r),'bbox_xy_m':bbxy(r),'eje_extremos_xy_m':[xy(v) for v in endpoints],'ancho_grafico_m':round(width,6),'ancho_documental_m':None,'z_antepecho_m':None,'z_dintel_m':None,'fuente':'Página35, espacios entre rellenos azules000SOBREADO; sin cotas escritas de posiciones.'})
# Patches reales de relleno césped en cubierta37; nunca usar verde de retranqueos.
for d in d37:
 c=d.get('fill');r=d['rect']
 if c and .90<c[0]<.92 and .90<c[1]<.92 and .74<c[2]<.76 and r.x0<600:
  for vs in boundaries(d):
   if len(vs)>2:
    data['cesped_patches'].append(poly(f'cesped_patch_{len(data["cesped_patches"])+1:03d}',vs,'Página37, capa0, rellenoRGB≈0.9098/0.9098/0.7490; contorno fiel por patches, incluye recortes gráficos detrás de mobiliario.'))
# Dos tumbonas representadas en el jardín delantero recortan gráficamente su fondo verde.
# Reponer césped debajo es una deducción de representación, no añadir dos áreas de pavimento.
data['cesped_bajo_mobiliario_deducido']=[
 poly('cesped_bajo_tumbona_01',[(428.12,676.00),(465.92,676.00),(465.92,690.16),(428.12,690.16)],'Página37: fondo verde interrumpido sólo por el símbolo de tumbona. Continuidad de jardín deducida.'),
 poly('cesped_bajo_tumbona_02',[(428.12,694.24),(465.92,694.24),(465.92,708.40),(428.12,708.40)],'Página37: fondo verde interrumpido sólo por el símbolo de tumbona. Continuidad de jardín deducida.')]

# Contornos auxiliares básicos trazados y registrados en la fase de auditoría.
audit=json.loads((ROOT/'analisis/auditoria_coordenadas_planta.json').read_text())
data['parcela']=audit['polygons']['parcela']
data['huella_vivienda']=audit['polygons']['envolvente_vivienda_incl_instalaciones']
data['porche_descubierto']=audit['polygons']['porche_descubierto_candidato']
data['referencias']['aparcamiento']=audit['parking'];data['referencias']['accesos']=audit['access']
# Piscina y cinco huellas de escalera: XY explícito; profundidad y contrahuella no documentadas.
poolpts=[(426.92,565.12),(493.16,565.12),(493.16,659.68),(426.92,659.68)]
data['piscina']=poly('piscina_vaso',poolpts,'Página35/37, cuatro segmentos000SOLERÍA')
data['piscina'].update({'profundidad_m':None,'cota_agua_z_m':None,'espesor_vaso_m':None,'escalera':[],'criterio_z':'No se documenta profundidad, contrahuella ni lámina de agua. Representación superficial a jardín; registrar cualquier profundidad de visualización elegida como hipótesis no contractual.'})
step_y=[565.12,570.88,576.52,582.16,587.80,593.56]
for i in range(5):
 st=poly(f'piscina_peldano_{i+1:02d}',[(470.48,step_y[i]),(493.16,step_y[i]),(493.16,step_y[i+1]),(470.48,step_y[i+1])],'Página35/37, líneas000SOLERÍA de escalera')
 st.update({'huella_grafica_m':round((step_y[i+1]-step_y[i])*F,6),'contrahuella_m':None,'z_m':None})
 data['piscina']['escalera'].append(st)
# Vigas visibles en cubierta: cinco longitudinales más travesaño frontal. No inventar partes ocultas.
data['pergola']={'contorno_exterior':audit['polygons']['pergola_piscina_exterior_candidato'],'vigas_visibles_planta_cubierta':[],'altura_inferior_z_m':None,'canto_vertical_m':None,'seccion_vertical_documentada':False,'criterio':'Forma y posiciones XY según relleno gris cubierta37; cantos/alturas se cruzan con alzados. Longitudes visibles se acortan donde las cubre el vuelo de entrada.'}
for d in d37:
 r=d['rect'];c=d.get('fill')
 if d['layer']=='000 SOBREADO' and c and abs(c[0]-.81569)<.0005 and r.x0>=310 and r.x1<=408 and r.y0>=540 and r.y1<=624:
  for vs in boundaries(d):
   beam=poly(f'pergola_viga_{len(data["pergola"]["vigas_visibles_planta_cubierta"])+1:02d}',vs,'Página37,000SOBREADO, rellenoRGB≈.81569/.81961/.82353')
   beam.update({'bbox_pdf_pt':list(r),'bbox_xy_m':bbxy(r),'seqno_pdf':d['seqno'],'ancho_grafico_m':round(min(r.width,r.height)*F,6),'longitud_visible_m':round(max(r.width,r.height)*F,6),'continuacion_oculta_bajo_cubierta':None,'canto_vertical_m':None})
   data['pergola']['vigas_visibles_planta_cubierta'].append(beam)
# Límites de solería exactamente dibujados, separados de las superficies semánticas.
data['pavimentos']['segmentos_originales']=[]
for d in d35:
 if d['layer']=='000 SOLERÍA' and d['rect'].x0<600:
  for it in d['items']:
   if it[0]=='l':data['pavimentos']['segmentos_originales'].append({'pdf_pt':[pt(it[1]),pt(it[2])],'xy_m':[xy(it[1]),xy(it[2])],'fuente_pagina':35,'seqno_pdf':d['seqno']})
data['pavimentos']['anillo_piscina']=poly('pavimento_entorno_piscina',[(415.64,553.84),(504.44,553.84),(504.44,670.96),(415.64,670.96)],'Extremos exterior000SOLERÍA; borde superior izquierdo se prolonga a terraza sin línea de división física.')
data['pavimentos']['anillo_piscina']['huecos']=[data['piscina']['poligono_xy_m']]
data['pavimentos']['banda_terraza']=poly('terraza_lateral',[(406.88,197.32),(470.24,197.32),(470.24,553.84),(406.88,553.84)],'Fachada oriental y borde pavimento000SOLERÍA; incluye franja frontal de conexión además del área rotulada porche61,12m².')
data['pavimentos']['banda_trasera']=poly('paso_pavimentado_trasero',[(265.16,105.52),(470.24,105.52),(470.24,122.44),(265.16,122.44)],'Línea000SOLERÍA superior y testero vivienda; encuentros laterales se unen al pavimento general.')
data['pavimentos']['criterio_general']='Las superficies exteriores blancas no tienen un contorno cerrado independiente salvo borde césped/solería. Puede representarse suelo parcelario neutro y aplicar patches césped exactos a la misma cota, ocultando huella vivienda, tendedero y piscina. No inventar un borde de plazas ni la superficie46,86m². El área blanca detrás de símbolos de mobiliario puede ser una máscara del dibujo, no suelo distinto.'
# Referencias originales de carpintería; curvas y hojas permiten ubicar puertas interiores sin fabricar cotas.
data['referencias']['carpinteria_vectorial_planta']=[]
for d in d35:
 r=d['rect']
 if d['layer']=='000 CARPINTERIA' and r.x0<600:
  its=[]
  for it in d['items']:
   if it[0] in ('l','c'):its.append({'tipo':it[0],'puntos_pdf_pt':[pt(v) for v in it[1:]],'puntos_xy_m':[xy(v) for v in it[1:]]})
   elif it[0]=='qu':
    q=it[1];vs=[q.ul,q.ur,q.lr,q.ll];its.append({'tipo':'poligono_hoja','puntos_pdf_pt':[pt(v) for v in vs],'puntos_xy_m':[xy(v) for v in vs]})
  if its:data['referencias']['carpinteria_vectorial_planta'].append({'seqno_pdf':d['seqno'],'bbox_pdf_pt':list(r),'bbox_xy_m':bbxy(r),'segmentos':its,'elemento': 'arco_apertura_puerta' if any(i['tipo']=='c' for i in its) else 'lineas_carpinteria'})
data['referencias']['vegetacion']='Geometría fina de árboles/plantas omitida como sólido: la posición de las zonas verdes se conserva en cesped_patches y se puede consultar página36/37 para símbolos. No añadir plantas que oculten arquitectura.'
data['incertidumbres']=[
 {'elemento':'Cotas interiores de puertas','valor':None,'criterio':'Conservar aperturas/gaps planta; una altura no cotada sólo puede usarse como supuesto explícito de visualización.'},
 {'elemento':'Piscina profundidad/agua/escalonesZ','valor':None,'criterio':'Contorno y escaleraXY documentados; sección de vaso no localizada.'},
 {'elemento':'Pérgola canto vertical','valor':None,'criterio':'Las vigas visibles de planta fijanXY pero no profundidadZ; cruce independiente con alzados.'},
 {'elemento':'Aparcamiento contorno exacto46,86m²','valor':None,'criterio':'Conservar dos posiciones de vehículos y pavimento dibujado, sin incorporar bordes de plazas inventados.'},
 {'elemento':'Particiones azules de3cm','valor':None,'criterio':'Posibles hojas de armarios/carpinterías. Contornos exactos guardados; no equiparar todas con pared de ladrillo.'}
]

# Guardado inicial: geometría sólida y huecos disponibles aunque elementos restantes se amplíen después.
OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('Guardado',OUT,'muros',len(data['muros']),'tendedero',len(data['tendedero']),'huecos',len(data['huecos_exteriores']),'cesped_patches',len(data['cesped_patches']))
