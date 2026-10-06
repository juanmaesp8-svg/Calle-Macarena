"""Cotejo independiente: vértices Blender reales contra extracción PDF literal.
No lee ni hereda el resultado V1. Los ajustes nominales se permiten solamente
dentro de la cuantización registrada de6.35mm; Z nuevas requieren fuente USER.
"""
import json,sys,csv,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'modelo/python_deps'))
from shapely.geometry import Polygon
from shapely.ops import unary_union
A=json.loads((ROOT/'analisis_v2/auditoria_planta_final.json').read_text())
U=json.loads((ROOT/'modelo/confirmaciones_usuario_v2.json').read_text())
R=json.loads((ROOT/'control/mediciones_mesh_real.json').read_text())
checks=[];EPS=.00001;TOL=.006351
def check(name,ok,detail=''):checks.append({'control':name,'cumple':bool(ok),'detalle':detail})
def near(a,b,tol=EPS):return abs(a-b)<=tol
def footprint(ob):
 vertices=ob['vertices'];parts=[]
 for face in ob['caras']:
  p=Polygon([(vertices[i][0],vertices[i][1]) for i in face])
  if p.is_valid and p.area>1e-10:parts.append(p)
 return unary_union(parts)
def unioncat(cat):return unary_union([footprint(o) for o in R['objetos'] if o['categoria']==cat])
check('Registro mediciones V2',R.get('version')==2 and R.get('revision')=='V2')
sourcehash=hashlib.sha256((ROOT/'fuentes/planta_final_proyecto_obra.pdf').read_bytes()).hexdigest()
check('Identidad PDF final',sourcehash==U['fuente_planta']['sha256']==R.get('fuente_sha256'))
objects=R['objetos'];seq={o['seqno_pdf_v2']:o for o in objects if o.get('seqno_pdf_v2') is not None}
check('Cantidad muros final',len(seq)==len(A['muros'])==69)
for w in A['muros']:
 ob=seq.get(w['seqno_pdf'])
 if ob is None:check('Muro '+w['nombre'],False,'Falta mesh');continue
 expected=unary_union([Polygon(p) for p in w['poligonos_xy_m']]);actual=footprint(ob)
 deviation=expected.hausdorff_distance(actual)
 check('Muro '+w['nombre'],deviation<=TOL and actual.difference(expected.buffer(TOL)).area<1e-8,f'Desviación {deviation:.8f}m; máximo cuantización6.35mm')
 check('Z muro '+w['nombre'],near(ob['bbox_xyz'][2],0) and near(ob['bbox_xyz'][5],3.35))
parcela=unioncat('parcela');ep=Polygon(A['parcela']['poligono_xy_m'])
tdobs=[o for o in objects if o['categoria']=='tendedero']
check('Nueve rellenos de tendedero existente',len(tdobs)==len(A['tendedero'])==9)
for w in A['tendedero']:
 ob=next((o for o in tdobs if o['nombre'].startswith(w['nombre']+'_')),None)
 expected=unary_union([Polygon(p) for p in w['poligonos_xy_m']])
 check('Tendedero '+w['nombre'],ob is not None and footprint(ob).hausdorff_distance(expected)<=EPS)
check('Parcela irregular 10vértices',parcela.hausdorff_distance(ep)<=EPS)
pool=unioncat('piscina');b=pool.bounds
check('Piscina3.50×5.00 nominal',near(b[2]-b[0],3.5) and near(b[3]-b[1],5))
check('Ancla NO piscina',near(b[0],11.7094) and near(b[3],10.8585))
check('Piscina contra PDF',pool.hausdorff_distance(Polygon(A['piscina']['poligono_xy_m']))<=TOL)
walls=unioncat('muro_vivienda')
names=[o['nombre'].lower() for o in objects]
check('Sin pérgola antigua',not any(o['categoria'] in {'viga_pergola','pilar_pergola'} for o in objects))
check('Sin puerta instalaciones antigua',not any('p_instalaciones' in n or 'p_cuarto_instalaciones' in n for n in names))
olddivider=Polygon([(5.399,8.14),(5.6,8.14),(5.6,12.07),(5.399,12.07)])
check('Sin tabique instalaciones/pérgola',walls.intersection(olddivider).area<1e-7)
west=seq[1763]['bbox_xyz'];east=seq[59509]['bbox_xyz'];north=seq[1759]['bbox_xyz'];south=seq[59511]['bbox_xyz']
tw=east[0]-west[3];td=north[1]-south[4];exdepth=north[1]-south[1];threshold=south[4]-south[1]
check('Trastero ancho nominal7.15',near(tw,7.15),tw)
check('Trastero fondo nominal3.94',near(td,3.94),td)
check('Trastero fondo a exterior4.19',near(exdepth,4.19),exdepth)
check('Umbral frontal0.25',near(threshold,.25),threshold)
holes={h['nombre']:h for h in R['huecos']}
for h in A['huecos_exteriores_compartidos_v1']:
 ob=holes.get(h['nombre']);check('Hueco '+h['nombre'],ob is not None and max(abs(a-b) for a,b in zip(ob['bbox_xy'],h['bbox_xy_m_registro_parcela']))<=EPS)
di=holes.get('P_interior_trastero_norte');door=holes.get('P_porton_trastero_sur');heights=U['confirmaciones_usuario']
check('Nueva puerta norte hueco0.96',di is not None and near(di['ancho'],.96))
check('Nueva puerta norte alto USER2.03',di is not None and near(di['alto'],heights['puerta_interior_trastero_alto_m']))
check('Nuevo portón frontal alto USER2.50',door is not None and near(door['alto'],heights['porton_frontal_trastero_alto_m']))
leaf=next(o for o in objects if o['nombre']=='P_interior_trastero_norte_hoja');l=leaf['bbox_xyz'];hinge=A['trastero']['puerta_norte']['hoja_referencia']['bisagra_xy_m']
check('Bisagra y hoja norte según plano',near((l[0]+l[3])/2,hinge[0]) and near(l[4],hinge[1]) and near(l[4]-l[1],.81915))
roofs=[o for o in objects if o['categoria']=='forjado'];rf=unary_union([footprint(o) for o in roofs])
check('Forjado USER3.35/3.70',all(near(o['bbox_xyz'][2],heights['forjado_trastero_inferior_m']) and near(o['bbox_xyz'][5],heights['forjado_trastero_superior_m']) for o in roofs))
tr=Polygon(A['trastero']['contorno_exterior']['poligono_xy_m'])
check('Cubierta cierra trastero',tr.difference(rf.buffer(TOL)).area<1e-8)
petos=[o for o in objects if 'Peto_trastero' in o['nombre']]
check('Tres petos trastero USER4.40',len(petos)==3 and all(near(o['bbox_xyz'][5],heights['coronacion_peto_trastero_m']) for o in petos))
check('Sin peto interior instalaciones',not any('peto' in n and 'instalaciones' in n for n in names))
check('Cielorraso nuevo no supuesto',all(footprint(o).intersection(tr.buffer(-TOL)).area<1e-8 for o in objects if o['categoria']=='cielorraso'))
grass=unioncat('jardin');eg=unary_union([Polygon(v['poligono_xy_m']) for v in A['cesped_patches']])
# Máscaras de tumbonas: continuidad de verde documentada; no son solería.
for v in json.loads((ROOT/'fuentes/datos_v1/datos_planta.json').read_text())['cesped_bajo_mobiliario_deducido']:
 eg=eg.union(Polygon(v['poligono_xy_m']))
house=unioncat('suelo_vivienda');eg=eg.intersection(ep).difference(house.union(pool))
check('Césped contorno final y máscaras deducidas',grass.hausdorff_distance(eg)<=EPS and grass.difference(eg.buffer(EPS)).area<1e-8 and eg.difference(grass.buffer(EPS)).area<1e-8,f'Error float32 de borde {grass.hausdorff_distance(eg):.9f}m; diferencia área {grass.symmetric_difference(eg).area:.9f}m²')
check('Césped franja nueva aparcamiento',grass.intersection(Polygon([(3.2,1.5),(3.8,1.5),(3.8,5.8),(3.2,5.8)])).area>2.0)
check('Pavimento/césped sin solapamiento',unioncat('pavimento').intersection(grass).area<1e-6)
check('Huella contra planta final',house.hausdorff_distance(Polygon(A['huella_vivienda_con_trastero']['poligono_xy_m']))<=TOL)
rows=[['Parcela superficie',635.60,parcela.area,'m²','PDFfinal rotulada; trazado calculado'],['Edificación superficie',211.63,house.area,'m²','PDFfinal rotulada; trazado ajustado a cotas; no forzar área'],['Trastero ancho interior',7.15,tw,'m','Cota directa PDFfinal'],['Trastero fondo interior',3.94,td,'m','Cota directa PDFfinal'],['Trastero profundidad exterior',4.19,exdepth,'m','Cota directa PDFfinal'],['Piscina ancho',3.5,b[2]-b[0],'m','Cota directa PDFfinal'],['Piscina largo',5,b[3]-b[1],'m','Cota directa PDFfinal'],['Puerta trastero hueco',.96,di['ancho'],'m','Cota directa PDFfinal'],['Puerta trastero altura',2.03,di['alto'],'m','Usuario'],['Portón trastero ancho',None,door['ancho'],'m','Calculado vectorPDFfinal'],['Portón trastero altura',2.5,door['alto'],'m','Usuario'],['Forjado inferior',3.35,roofs[0]['bbox_xyz'][2],'m','PDForiginal y usuario para trastero'],['Forjado superior',3.7,roofs[0]['bbox_xyz'][5],'m','PDForiginal y usuario para trastero'],['Peto trastero',4.4,petos[0]['bbox_xyz'][5],'m','Usuario'],['Porcelánico módulo',.9,.9,'m','Acabado usuario; shader métrico']]
with (ROOT/'control/dimensiones_principales_v2.csv').open('w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['Elemento','Nominal','Modelado','Unidad','Fuente']);writer.writerows(rows)
failed=[c for c in checks if not c['cumple']]
result={'version':2,'revision':'V2_planta_final_trastero','apto_para_renders':not failed,'total_controles':len(checks),'fallos':len(failed),'tolerancia_vector_xy_m':TOL,'tolerancia_nominal_m':EPS,'modelo_sha256':hashlib.sha256((ROOT/'Calle_Macarena_modelo_1a1.blend').read_bytes()).hexdigest(),'fuente_sha256':sourcehash,'advertencias_documentales':['Áreas rotuladas no fuerzan el contorno trazado','Baño2 profundidad gráfica2.67335frente2.68 escrita; discrepancia6.65mm registrada','Z piscina sin dato; representación superficial','Diferencia histórica de ancho de peto alto en alzado trasero/sección3 de0.80m registrada; XYplanta de cubierta prevalece'],'controles':checks}
(ROOT/'control/control_resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('CONTROL_V2',len(checks),'fallos',len(failed),'apto',not failed)
for c in failed:print(c)
if failed:sys.exit(1)
