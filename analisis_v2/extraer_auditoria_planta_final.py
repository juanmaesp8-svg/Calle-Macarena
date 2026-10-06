"""Auditoría XY reproducible de planta definitiva; no modifica datos de modelo."""
from pathlib import Path
import sys,json,math,re,collections,argparse
import fitz
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'modelo/python_deps'))
from shapely.geometry import Polygon
from shapely.ops import unary_union
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--datos-v1',type=Path,help='Datos literales V1 para comparación; no usar el JSON canónico ya actualizado aV2.')
args=parser.parse_args()
candidatos=[BASE/'fuentes/datos_v1/datos_planta.json',BASE/'revisiones_v1/modelo/datos_planta.json',BASE.parent/'arquitectura-macarena/modelo/datos_planta.json']
OLD=args.datos_v1 or next((q for q in candidatos if q.is_file()),None)
if OLD is None:
 raise FileNotFoundError('Se requiere referencia V1: proporcionar --datos-v1 /ruta/datos_planta.json')
F=127/2400
ORIGIN=(205.64,770.32)
SHIFT=112.68
ALIGN_SHIFT=112.8
PDF=BASE/'fuentes/planta_final_proyecto_obra.pdf'
OUT=BASE/'analisis_v2/auditoria_planta_final.json'
def point(p):return [round(float(p[0]),4),round(float(p[1]),4)]
def reg(p,shift=SHIFT):return [round(float(p[0])+shift,4),round(float(p[1]),4)]
def xy(p,shift=SHIFT):q=reg(p,shift);return [round((q[0]-ORIGIN[0])*F,6),round((ORIGIN[1]-q[1])*F,6)]
def bbox(r,shift=SHIFT):return [round((r[0]+shift-ORIGIN[0])*F,6),round((ORIGIN[1]-r[3])*F,6),round((r[2]+shift-ORIGIN[0])*F,6),round((ORIGIN[1]-r[1])*F,6)]
def boundaries(d):
 edges=[]
 for it in d['items']:
  if it[0]=='l':edges.append((tuple(point(it[1])),tuple(point(it[2]))))
  elif it[0]=='qu':
   q=it[1];vs=[tuple(point(q.ul)),tuple(point(q.ur)),tuple(point(q.lr)),tuple(point(q.ll))];edges.extend(zip(vs,vs[1:]+vs[:1]))
  elif it[0]=='re':
   r=it[1];vs=[tuple(point((r.x0,r.y0))),tuple(point((r.x1,r.y0))),tuple(point((r.x1,r.y1))),tuple(point((r.x0,r.y1)))];edges.extend(zip(vs,vs[1:]+vs[:1]))
 counts=collections.Counter(tuple(sorted(e)) for e in edges if e[0]!=e[1]);bd=[list(e) for e,n in counts.items() if n%2];polys=[]
 while bd:
  a,b=bd.pop(0);vs=[a,b]
  while vs[-1]!=vs[0]:
   found=False
   for i,e in enumerate(bd):
    if vs[-1] in e:vs.append(e[1] if e[0]==vs[-1] else e[0]);bd.pop(i);found=True;break
   if not found:break
  if len(vs)>3 and vs[-1]==vs[0]:polys.append(vs[:-1])
 return polys

def poly(name,vs,source=None):
 return {'nombre':name,'poligono_pdf_v2_pt':[point(p) for p in vs],'poligono_pdf_registrado_v1_pt':[reg(p) for p in vs],'poligono_xy_m':[xy(p) for p in vs],'area_vector_m2':round(Polygon(vs).area*F*F,6),'fuente':source}

def entry(d):
 ps=boundaries(d);r=d['rect']
 return {'seqno_pdf':d['seqno'],'capa':d['layer'],'bbox_pdf_v2_pt':[round(v,4) for v in r],'bbox_pdf_registrado_v1_pt':[round(r[0]+SHIFT,4),round(r[1],4),round(r[2]+SHIFT,4),round(r[3],4)],'bbox_xy_m':bbox(r),'poligonos_pdf_v2_pt':ps,'poligonos_xy_m':[[xy(p) for p in vs] for vs in ps],'espesor_min_vector_m':round(min(r.width,r.height)*F,6),'z_m':None}

def union_entries(arr,old=False,align=False):
 ps=[]
 for e in arr:
  pss=e['poligonos_xy_m']
  if align and not old:
   pss=[[[p[0]+(ALIGN_SHIFT-SHIFT)*F,p[1]] for p in pp] for pp in pss]
  ps.extend(Polygon(vs).buffer(0) for vs in pss if len(vs)>2)
 return unary_union(ps)

def change_parts(shape):
 if shape.is_empty:return []
 geoms=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
 return [{'area_m2':round(s.area,6),'bbox_xy_m':[round(v,6) for v in s.bounds],'poligono_xy_m':[[round(v,6) for v in p] for p in list(s.exterior.coords)[:-1]]} for s in geoms if s.geom_type=='Polygon' and s.area>.00001]

old=json.loads(OLD.read_text());doc=fitz.open(PDF);p=doc[0];ds=p.get_drawings()
D={'version':2,'fuente':str(PDF),'pagina':1,'tamano_pdf_pt':[p.rect.width,p.rect.height],'escala_directa':'1:150','factor_m_por_pt':F,'registro':{'origen_modelo_v1_pdf_pt':list(ORIGIN),'planta_izquierda_a_v1_pdf_pt':[SHIFT,0],'planta_derecha_a_v1_pdf_pt':[-271.56,0],'registro_alternativo_por_muros_izquierda_a_v1_pdf_pt':[ALIGN_SHIFT,0],'residuo_x_parcela_muros_m':.00635,'criterio':'Registro por lindero izquierdo PARCELA. Los muros comunes coinciden mejor con +112,80 pt; la diferencia 0,12 pt es la cuantización vectorial, no evidencia de traslado arquitectónico. No reescalar para ajustar áreas. Y común; esquinas del trazo de parcela difieren hasta 0,06 pt por cuantización.'},'muros':[],'tendedero':[],'cesped_patches':[],'soleria_segmentos':[],'carpinteria_vectorial':[],'cotas_directas':[],'textos_superficies':[],'cambios':[],'incertidumbres':[]}
for d in ds:
 r=d['rect'];c=d.get('fill')
 if r.x0>=450:continue
 if d['layer']=='000 SOBREADO' and c and abs(c[0]-.38824)<.0005 and abs(c[1]-.41569)<.0005:
  e=entry(d);target='tendedero' if r.x1<155 and r.y1<126 else 'muros'
  e['nombre']=f'{target}_v2_{len(D[target])+1:03d}';e['grupo']='trastero' if r.y0>=535.47 else target;D[target].append(e)
 if c and .90<c[0]<.92 and .90<c[1]<.92 and .74<c[2]<.76:
  for vs in boundaries(d):D['cesped_patches'].append(poly(f'cesped_v2_{len(D["cesped_patches"])+1:03d}',vs,{'seqno_pdf':d['seqno'],'capa':d['layer']}))
 if d['layer']=='000 SOLERÍA':
  for it in d['items']:
   if it[0]=='l':D['soleria_segmentos'].append({'seqno_pdf':d['seqno'],'pdf_v2_pt':[point(it[1]),point(it[2])],'pdf_registrado_v1_pt':[reg(it[1]),reg(it[2])],'xy_m':[xy(it[1]),xy(it[2])]})
 if d['layer']=='000 CARPINTERIA':
  its=[]
  for it in d['items']:
   if it[0] in ('l','c'):vs=[point(v) for v in it[1:]];its.append({'tipo':it[0],'pdf_v2_pt':vs,'xy_m':[xy(v) for v in vs]})
   elif it[0]=='qu':
    q=it[1];vs=[point(v) for v in [q.ul,q.ur,q.lr,q.ll]];its.append({'tipo':'qu','pdf_v2_pt':vs,'xy_m':[xy(v) for v in vs]})
  if its:D['carpinteria_vectorial'].append({'seqno_pdf':d['seqno'],'bbox_pdf_v2_pt':[round(v,4) for v in r],'bbox_xy_m':bbox(r),'items':its})
# Parcela: centros de pares de vértices del relleno negro de espesor gráfico 0,96 pt.
parcel=[(92.96,66.16),(393.5,64),(396.98,129.16),(415.88,129.16),(419,344.98),(397.64,364.06),(405.2,513.34),(435.68,529.9),(444.68,750.94),(92.96,770.26)]
D['parcela']=poly('parcela_v2',parcel,{'capas':'PARCELA','seqno_pdf':[4138,4141],'criterio':'Eje del trazo negro gráfico, no espesor constructivo de cerramiento.'})
D['huella_vivienda_con_trastero']=poly('huella_vivienda_v2',[(149.6,122.44),(340.52,122.44),(340.52,197.32),(294.2,197.32),(294.2,621.28),(149.6,621.28)],'Envolvente exterior de rellenos azules; nuevo trastero cierra antiguo contorno de pérgola.')
D['trastero']={'muros_seqno_pdf':[1759,1761,1763,1765,59509,59511],'contorno_exterior':poly('trastero_contorno',[(149.6,535.48),(294.2,535.48),(294.2,621.28),(149.6,621.28)]),'interior_base':poly('trastero_interior_hasta_cara_interior_sur',[(154.4,542.08),(289.52,542.08),(289.52,616.6),(154.4,616.6)]),'umbral_sur':poly('trastero_umbral_porton_sur',[(184.16,616.6),(259.76,616.6),(259.76,621.28),(184.16,621.28)]),'puerta_norte':{'cota_ancho_directa_m':.96,'bbox_pdf_v2_pt':[230.96,535.48,249.2,542.08],'bbox_pdf_registrado_v1_pt':[343.64,535.48,361.88,542.08],'bbox_xy_m':bbox([230.96,535.48,249.2,542.08]),'ancho_gap_vector_m':.9652,'altura_m':None,'criterio':'Cota escrita 0,96; hueco de rellenos azules 0,9652 por cuantización. Apertura dibujada hacia trastero; bisagra al oeste. Hueco bruto no equivale al ancho de hoja.'},'porton_sur':{'ancho_vector_m':4.0005,'bbox_pdf_v2_pt':[184.16,616.6,259.76,621.28],'bbox_pdf_registrado_v1_pt':[296.84,616.6,372.44,621.28],'bbox_xy_m':bbox([184.16,616.6,259.76,621.28]),'altura_m':None,'criterio':'Hueco entre muros sur; cuatro líneas horizontales superpuestas en carpintería; no deducir sistema de apertura por sí solo.'},'superficie_util_directa_m2':29.17,'reconciliacion_superficie':{'formula_nominal':'7,15 × 3,94 + 4,00 × 0,25','resultado_m2':29.171,'criterio':'El umbral del portón sur ocupa el espesor de muro y explica la superficie útil rotulada sin deformar geometría. Es una deducción de cómputo, no una nueva cota.'},'cubierta_z_m':None,'cotas_z':'Tratadas por otro agente y confirmación del usuario; esta auditoría sólo fija XY.'}
D['piscina']=poly('piscina_vaso_v2',[(314.24,565.12),(380.36,565.12),(380.36,659.68),(314.24,659.68)],{'capas':'000 SOLERÍA','seqno_pdf':[54387,54388,54389,54390]})
D['piscina']['dimensiones_directas_m']=[3.5,5.0]
D['piscina']['dimensiones_vector_m']=[round((380.36-314.24)*F,6),round((659.68-565.12)*F,6)]
D['piscina']['escalera_xy']={'x_pdf_v2_pt':[357.68,380.36],'y_pdf_v2_pt':[565.12,570.88,576.52,582.16,587.8,593.56],'bbox_xy_m':bbox([357.68,565.12,380.36,593.56]),'seqno_pdf':[54394,54395,54396,54397,54398,54399],'z_m':None}
# Todas las cotas directas de la planta derecha, asociadas a línea central roja.
redlines=[]
for d in ds:
 c=d.get('color');its=d['items']
 if d['rect'].x0<475 or not c or c[0]<.75 or c[1]>.2 or c[2]>.2 or len(its)!=1 or its[0][0]!='l':continue
 a,b=its[0][1:];dx,dy=b.x-a.x,b.y-a.y
 if abs(dx)<.002 and abs(dy)>3:ori='Y';L=abs(dy)
 elif abs(dy)<.002 and abs(dx)>3:ori='X';L=abs(dx)
 else:continue
 redlines.append({'seqno_pdf':d['seqno'],'a':point(a),'b':point(b),'ori':ori,'longitud_pt':L})
for bl in p.get_text('dict')['blocks']:
 for ln in bl.get('lines',[]):
  for s in ln.get('spans',[]):
   t=s['text'].strip();r=s['bbox']
   if r[0]<450 and ('m2' in t or t in ['TENDEDERO','TRASTERO','ENTRADA','HALL','SILICON VALLEY']):D['textos_superficies'].append({'texto':t,'bbox_pdf_v2_pt':[round(v,4) for v in r]})
   if not 475<r[0]<830 or not re.fullmatch(r'[0-9]+(?:[.,][0-9]+)?m?',t):continue
   v=float(t.rstrip('m').replace(',','.'));ori='X' if abs(ln['dir'][0])>.5 else 'Y';cx=(r[0]+r[2])/2;cy=(r[1]+r[3])/2;cand=[]
   for rd in redlines:
    if rd['ori']!=ori:continue
    a,b=rd['a'],rd['b'];expected=v/F;delta=abs(rd['longitud_pt']+1.92-expected)
    if delta>max(.28,expected*.008):continue
    mx=(a[0]+b[0])/2;my=(a[1]+b[1])/2
    norm=abs(cy-my) if ori=='X' else abs(cx-mx);along=abs(cx-mx) if ori=='X' else abs(cy-my)
    if norm>10 or along>max(10,expected*.35):continue
    cand.append((norm+along*.3+delta*2,rd))
   candidates=sorted(cand,key=lambda z:z[0]);rd=candidates[0][1] if candidates else None
   e={'texto':t,'valor_directo_m':v,'direccion':ori,'bbox_texto_pdf_v2_pt':[round(x,4) for x in r],'contexto':None,'linea_central_seqno_pdf':rd['seqno_pdf'] if rd else None}
   if rd:
    a,b=rd['a'],rd['b'];dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);ux,uy=dx/L,dy/L
    tips=[[a[0]-.96*ux,a[1]-.96*uy],[b[0]+.96*ux,b[1]+.96*uy]]
    e.update({'extremos_cota_pdf_v2_pt':[[round(z,4) for z in t] for t in tips],'extremos_cota_xy_m':[xy(t,-271.56) for t in tips],'medida_vector_m':round((L+1.92)*F,6),'desvio_vector_directa_m':round((L+1.92)*F-v,6),'asociacion':'Línea roja de igual orientación, longitud con flechas ±0,96 pt y proximidad al texto; verificar contexto.'})
   D['cotas_directas'].append(e)
# Comparación geométrica de muros, con alineación de muros comunes para no contar cuantización como cambio.
for target in ['muros','tendedero']:
 u1=union_entries(old[target],old=True);u2=union_entries(D[target],align=True)
 D['comparacion_'+target]={'n_contornos_v1':len(old[target]),'n_contornos_v2':len(D[target]),'area_huella_muros_v1_m2':round(u1.area,6),'area_huella_muros_v2_m2':round(u2.area,6),'hausdorff_union_m':round(u1.hausdorff_distance(u2),6),'anadido_sin_banda_cuantizacion_0_0065m':change_parts(u2.difference(u1.buffer(.0065))),'retirado_sin_banda_cuantizacion_0_0065m':change_parts(u1.difference(u2.buffer(.0065)))}
# Comparar sólo el sector vivienda anterior al trastero.
u1=union_entries([e for e in old['muros'] if e['bbox_pdf_pt'][1]<535.4],old=True)
u2=union_entries([e for e in D['muros'] if e['bbox_pdf_v2_pt'][1]<535.4],align=True)
D['comparacion_vivienda_principal_sin_trastero']={'area_diferencia_simetrica_m2':round(u1.symmetric_difference(u2).area,6),'hausdorff_m':round(u1.hausdorff_distance(u2),6),'criterio':'Geometría azul común, alineación +112,80 pt; nuevos cortes de teselación no equivalen a nuevas paredes.'}
g1=unary_union([Polygon(e['poligono_xy_m']) for e in old['cesped_patches']]+[Polygon(e['poligono_xy_m']) for e in old.get('cesped_bajo_mobiliario_deducido',[])])
g2=unary_union([Polygon(e['poligono_xy_m']) for e in D['cesped_patches']])
D['comparacion_cesped']={'area_patches_v1_m2':round(g1.area,6),'area_patches_v2_m2':round(g2.area,6),'anadido_fuera_banda_0_01m':change_parts(g2.difference(g1.buffer(.01))),'retirado_fuera_banda_0_01m':change_parts(g1.difference(g2.buffer(.01))),'criterio':'Comparación con patches V1 de cubierta y continuidad inferida bajo tumbonas. Los muebles y simbología pueden producir máscaras gráficas; no convertir máscaras en bordes de jardín.'}
# Huecos exteriores compartidos: nueva planta conserva sus posiciones relativas salvo cuantización.
D['huecos_exteriores_compartidos_v1']=[]
for e in old['huecos_exteriores']:
 if e['nombre']=='P_instalaciones_sur':continue
 r=e['bbox_pdf_pt'];raw=[round(r[0]-112.8,4),r[1],round(r[2]-112.8,4),r[3]]
 if e['nombre']=='V_bano1_norte':raw[2]=182.72
 elif e['nombre']=='V_dormitorio1_este':raw[0],raw[2]=333.92,340.52
 elif e['fachada_local']=='E':raw[0],raw[2]=287.6,294.2
 D['huecos_exteriores_compartidos_v1'].append({'nombre':e['nombre'],'estancia_v1':e['estancia'],'fachada_local':e['fachada_local'],'bbox_pdf_v2_pt':raw,'bbox_xy_m_registro_parcela':bbox(raw),'ancho_vector_m':round((raw[3]-raw[1] if e['fachada_local'] in ('W','E') else raw[2]-raw[0])*F,6),'verificacion':'Extremos de gaps entre rellenos azules V2 verificados; diferencias de una unidad gráfica frente a V1. Ventanas no añadidas en trastero.'})
D['resumen_cantidades']={'muros_v2':len(D['muros']),'tendedero_v2':len(D['tendedero']),'carpinteria_referencias_v2':len(D['carpinteria_vectorial']),'cesped_patches_v2':len(D['cesped_patches']),'cotas_directas':len(D['cotas_directas']),'cotas_asociadas_linea':sum(e['linea_central_seqno_pdf'] is not None for e in D['cotas_directas']),'superficie_construida_directa_v1_m2':190.61,'superficie_construida_directa_v2_m2':211.63,'superficie_parcela_directa_v2_m2':635.60}
D['incertidumbres']=[{'elemento':'Registro entre versiones','valor_m':.00635,'criterio':'Residuos de una unidad de cuantización; conservar forma y cotas directas, no cambiar escala.'},{'elemento':'Cerramiento lateral constructivo','valor_m':None,'criterio':'PARCELA dibuja lindero gráfico; no documenta espesor ni doble cara del cerramiento general. Tendedero posee muros explícitos.'},{'elemento':'Cota 7,50','criterio':'Corresponde al ancho combinado de suite dormitorio principal/vestidor, no al trastero. Trastero acotado 7,15 interiores.'},{'elemento':'Superficie hall','criterio':'Etiqueta nueva 6,30 frente a 8,52 V1; no se modifica geometría de muros del hall. Cambio de cómputo/rotulación, sin justificar desplazamiento.'}]

# Referencias de mobiliario claramente cambiado; alturas no arquitectónicas.
D['mobiliario_cambiado']=[
 {'nombre':'mesa_centro_salon','accion':'sustituir','bbox_pdf_v2_pt':[182,487.84,204.56,501.04],'bbox_xy_m':bbox([182,487.84,204.56,501.04]),'dimensiones_directas_m':[1.2,.7],'dimensiones_vector_m':[1.1938,.6985],'seqno_pdf':[53441],'v1_bbox_pdf_pt':[299.12,487.12,316.16,509.8],'criterio':'En V2 pasa a rectángulo horizontal; conservar ubicación y orientación nuevas.'},
 {'nombre':'mesa_comedor_interior','accion':'sustituir','bbox_pdf_v2_pt':[252.2,476.56,274.88,514.36],'bbox_xy_m':bbox([252.2,476.56,274.88,514.36]),'dimensiones_directas_m':[1.2,2.0],'dimensiones_vector_m':[1.20015,2.00025],'seqno_pdf':[53387,53459],'v1_bbox_pdf_pt':[366.92,476.56,385.76,510.64],'criterio':'V1 aproximadamente1,0×1,8; V2 expresamente1,2×2,0. Sillas laterales y cabecera sur deben seguir nuevo símbolo.'},
 {'nombre':'butaca_salon_1','accion':'mover','bbox_pdf_v2_pt':[213.32,484.48,227.72,496.96],'bbox_xy_m':bbox([213.32,484.48,227.72,496.96]),'seqno_pdf':[53403,53429],'criterio':'Desplazada al oeste unos0,17–0,18m frente a V1.'},
 {'nombre':'butaca_salon_2','accion':'mover','bbox_pdf_v2_pt':[213.32,499.96,227.72,512.56],'bbox_xy_m':bbox([213.32,499.96,227.72,512.56]),'seqno_pdf':[53439,53457],'criterio':'Desplazada al oeste unos0,17–0,18m frente a V1.'},
 {'nombre':'asiento_salon_oeste','accion':'retirar','v1_bbox_pdf_pt':[271.52,499.96,285.92,512.56],'criterio':'El símbolo V1 adicional bajo extremo oeste del sofá no aparece en V2.'},
 {'nombre':'muebles_norte_trastero_en_salon','accion':'sustituir_por_dos_segmentos','bboxes_pdf_v2_pt':[[156.2,529.84,230.96,535.48],[249.2,529.84,287.6,535.48]],'bboxes_xy_m':[bbox([156.2,529.84,230.96,535.48]),bbox([249.2,529.84,287.6,535.48])],'seqno_pdf':[53463,53465],'criterio':'Relleno gris interrumpido por nueva puerta norte; no convertir mobiliario en muro ni deducir altura.'},
 {'nombre':'rack_tablas_trastero','accion':'anadir','bbox_pdf_v2_pt':[154.4,542.08,221.96,553.48],'bbox_xy_m':bbox([154.4,542.08,221.96,553.48]),'dimensiones_directas_m':[3.58,.6],'criterio':'Referencia auxiliar nueva acotada; altura no definida.'},
 {'nombre':'gym_rack_trastero','accion':'anadir','bbox_pdf_v2_pt':[157.64,578.68,195.44,610.84],'bbox_xy_m':bbox([157.64,578.68,195.44,610.84]),'dimensiones_directas_m':[2,1.7],'criterio':'Referencia auxiliar nueva acotada; altura no definida.'},
 {'nombre':'moto_trastero','accion':'anadir','bbox_pdf_v2_pt':[265.4,563.8,282.44,609.16],'bbox_xy_m':bbox([265.4,563.8,282.44,609.16]),'dimensiones_directas_m':[.9,2.4],'criterio':'Referencia auxiliar nueva acotada; altura no definida.'},
 {'nombre':'mesa_comedor_pergola_y_sillas','accion':'retirar','criterio':'La pérgola y su comedor se sustituyen por trastero; no conservar ningún símbolo como mesa exterior bajo nueva cubierta.'}]
D['trastero']['puerta_norte']['hoja_referencia']={'bbox_pdf_v2_pt':[232.28,537.4,233.12,552.88],'bbox_xy_m':bbox([232.28,537.4,233.12,552.88]),'ancho_hoja_vector_m':.81915,'espesor_grafico_m':.04445,'bisagra_pdf_v2_pt':[232.7,537.4],'bisagra_xy_m':xy([232.7,537.4]),'sentido':'Abre hacia trastero, hoja abierta hacia sur del plano; bisagra al oeste del hueco.','seqno_pdf':[61346,61347,61348,61349],'criterio':'La cota0,96 rige hueco bruto, no hoja; espesor del símbolo no es cota física de puerta.'}
# Todos los cambios reales detectados, separados de residuos gráficos.
D['cambios']=[
 {'elemento':'Dependencia frontal','cambio':'Instalaciones + pérgola y barbacoa/comedor sustituidos por trastero29,17m² de ancho total del cuerpo principal.','geometria':'Retirar tabique antiguo entre instalaciones y pérgola, vigas y pilar de pérgola; añadir muros este y sur, dividir muro norte para puerta0,96; sustituir puerta sur instalaciones por portón4,00.'},
 {'elemento':'Edificación posterior izquierda','cambio':'Sin cambio: tendedero7,00m² preexistente.','evidencia':'Texto TENDEDERO en ambas versiones,9contornos azules; Hausdorff6,35mm y ninguna diferencia fuera de banda de cuantización.'},
 {'elemento':'Muros y ventanas vivienda principal','cambio':'Sin cambio arquitectónico detectado.','evidencia':'Hausdorff6,35mm entre uniones de muros previos al trastero; todos los huecos externos mantienen posición y orientación. La segmentación de rellenos superior cambia pero no su contorno.'},
 {'elemento':'Parcela y relación de accesos','cambio':'Sin cambio de forma o acceso detectado.','evidencia':'10vértices y mismos quiebros; residuos de0,06–0,12pt. Portón de vehículos y acceso peatonal siguen lindero frontal; entrada vivienda continúa oeste.'},
 {'elemento':'Piscina y escalera','cambio':'Sin cambio de posición/orientación; nuevas cotas directas3,50×5,00.','evidencia':'Bordes y escalones iguales dentro de cuantización. Preferir cotas escritas exactas a anchura vectorial3,49885/3,5052 o longitud5,0038.'},
 {'elemento':'Jardín aparcamiento','cambio':'Añadir franja de césped/vegetación a la izquierda de dos vehículos.','evidencia':'Nuevos bordes de solería x149,60 y168,56 entrey639,28ylindero frontal. Ancho gráfico1,0033m; extensiónaprox6,5m. Ningún borde de plaza inventado.'},
 {'elemento':'Tumbonas','cambio':'Conservar emplazamientos; el relleno blanco bajo símbolos es máscara de dibujo, césped continuo deducido.','evidencia':'Las dos retiradas en comparacion_cesped son sólo rectángulos de tumbona.'},
 {'elemento':'Hall/entrada','cambio':'Superficie rotulada pasa8,52a6,30m² sin mover sus muros.','evidencia':'Contornos comunes iguales dentro cuantización; distinto cómputo/rotulación.'},
 {'elemento':'Despacho','cambio':'Renombrado SILICON VALLEY; superficie6,93m² mantenida.','evidencia':'Texto y contornos; no nuevo recinto.'},
 {'elemento':'Mobiliario salón','cambio':'Cambian mesa de centro, mesa comedor, butacas y desaparece asiento adicional; ver mobiliario_cambiado.','evidencia':'Cotas y rellenos grises nuevos; no modificar arquitectura a partir de mobiliario.'},
 {'elemento':'Superficie construida','cambio':'Texto V2 indica211,63m² frente190,61m² V1.','evidencia':'La propia lámina indica que excede190,68m² permitidos; se transcribe como dato del documento, no como aprobación urbanística.'}]
for e in D['cotas_directas']:
 x,y=e['bbox_texto_pdf_v2_pt'][:2]
 if y>560 and x>690:e['contexto']='piscina'
 elif y>535:e['contexto']='trastero; cota recinto o mobiliario según posición'
 elif y>455:e['contexto']='salón; cota recinto o mobiliario según posición'
 elif y>407:e['contexto']='hall/cocina/franja de acceso'
 elif y>337:e['contexto']='cocina/lavadero/aseo'
 elif y>278:e['contexto']='dormitorio3/baño2'
 elif y>198:e['contexto']='dormitorio2/despacho/baño1'
 elif y>122:e['contexto']='suite principal: dormitorio1/vestidor/baño1'
 else:e['contexto']='tendedero'
D['cotas_discrepancia_mayor_una_unidad_grafica']=[e for e in D['cotas_directas'] if abs(e['desvio_vector_directa_m'])>.00635+1e-7]


# Sillas del comedor interior: nombres compatibles con JSONF V1 para sustitución.
D['sillas_comedor_interior_v2']=[]
for name,rect,seqs in [
 ('silla_interior_izq_1',[247.52,480.16,252.2,487.6],[53393,53399]),
 ('silla_interior_der_1',[274.88,480.16,279.68,487.6],[53389,53395]),
 ('silla_interior_izq_2',[247.52,491.8,252.2,499.12],[53425,53435]),
 ('silla_interior_der_2',[274.88,491.8,279.68,499.12],[53421,53431]),
 ('silla_interior_izq_3',[247.52,503.44,252.2,510.76],[53453]),
 ('silla_interior_der_3',[274.88,503.44,279.68,510.76],[53449]),
 ('silla_interior_cabecera_norte',[259.88,471.88,267.32,476.56],[53365]),
 ('silla_interior_cabecera_sur',[259.88,514.36,267.32,519.16],[53461])]:
 e={'nombre':name,'bbox_pdf_v2_pt':rect,'bbox_xy_m':bbox(rect),'dimensiones_vector_m':[round((rect[2]-rect[0])*F,6),round((rect[3]-rect[1])*F,6)],'seqno_pdf':seqs,'z_m':None,'criterio':'BBox de símbolo gris nuevo; reemplazar posición V1, no extrapolar desde mesa.'}
 D['sillas_comedor_interior_v2'].append(e)
D['mobiliario_desaparecido_nombres_v1']=['asiento_salon_oeste','mesa_comedor_pergola','silla_pergola_norte_1','silla_pergola_sur_1','silla_pergola_norte_2','silla_pergola_sur_2','silla_pergola_norte_3','silla_pergola_sur_3','silla_pergola_cabecera_oeste','silla_pergola_cabecera_este']
D['aparcamiento']={'vehiculos_bbox_pdf_v2_pt':[[184.503006,652.23999,223.892639,745.47998],[232.147354,652.23999,271.536987,745.47998]],'vehiculos_bbox_xy_m':[bbox([184.503006,652.23999,223.892639,745.47998]),bbox([232.147354,652.23999,271.536987,745.47998])],'criterio':'Dos grupos363trayectorias04-MOBILIARIO cada uno. Registro +112,68 reproduce bboxesV1 exactamente dentro0,000001m. No se dibuja nuevo contorno autónomo de plazas.'}
D['parcela']['comparacion_vertices_v1']=[{'vertice':i+1,'pdf_v1_pt':a,'pdf_v2_registrado_pt':b,'delta_m':[round((b[0]-a[0])*F,6),round((a[1]-b[1])*F,6)],'distancia_m':round(math.hypot(b[0]-a[0],b[1]-a[1])*F,6)} for i,(a,b) in enumerate(zip(old['parcela']['points_pdf_pt'],D['parcela']['poligono_pdf_registrado_v1_pt']))]
D['criterio_final_para_modelo']='Por indicación de root: preservar todos los vectores XY de V2 y registrar desfases escritos dentro de cuantización6,35mm. La propuesta de normalización nominal en archivo separado no se aplica. No alterar huellas de estancias comunes ni forzar superficies.'

OUT.write_text(json.dumps(D,ensure_ascii=False,indent=2))
print(json.dumps(D['resumen_cantidades'],ensure_ascii=False))
print('Principal',D['comparacion_vivienda_principal_sin_trastero'])
print('Tendedero',D['comparacion_tendedero'])
print('Grass additions',[(e['area_m2'],e['bbox_xy_m']) for e in D['comparacion_cesped']['anadido_fuera_banda_0_01m']])
print('Grass removes',[(e['area_m2'],e['bbox_xy_m']) for e in D['comparacion_cesped']['retirado_fuera_banda_0_01m']])
print('Footprint',D['huella_vivienda_con_trastero']['area_vector_m2'],'parcel',D['parcela']['area_vector_m2'])
