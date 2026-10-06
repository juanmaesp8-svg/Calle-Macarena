"""Aplica la planta final sin alterar los datos archivados de la revisión V1.

La auditoría conserva los vectores originales. Aquí se priorizan únicamente
las cotas nominales nuevas del trastero y piscina, con ajustes inferiores a la
cuantización de 6,35 mm. Las alturas del trastero proceden del usuario.
"""
import json, copy, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'modelo'
A=json.loads((ROOT/'analisis_v2/auditoria_planta_final.json').read_text())
U=json.loads((DIR/'confirmaciones_usuario_v2.json').read_text())
assert hashlib.sha256((ROOT/'fuentes/planta_final_proyecto_obra.pdf').read_bytes()).hexdigest()==U['fuente_planta']['sha256'],'El PDF no coincide con la revisión confirmada'
def prior(n):return json.loads((ROOT/'fuentes/datos_v1'/n).read_text())
P=prior('datos_planta.json'); H=prior('datos_alturas.json'); F=prior('datos_mobiliario.json'); CAM=prior('criterios_qa_camaras.json')
def area(xy):return abs(sum(xy[i][0]*xy[(i+1)%len(xy)][1]-xy[(i+1)%len(xy)][0]*xy[i][1] for i in range(len(xy)))/2)
def bbox(xy):return [min(v[0] for v in xy),min(v[1] for v in xy),max(v[0] for v in xy),max(v[1] for v in xy)]
def contorno(v,declared,source):return {'points_xy_m':v,'declared_area_m2':declared,'area_traced_m2':area(v),'difference_area_m2':area(v)-declared,'source':source}
adjustments=[{'elemento':'Trastero interior','cota_directa_m':[7.15,3.94],'anclas':'Oeste interior X3.2512; norte interior Y12.0777','max_desplazamiento_m':.00335},
 {'elemento':'Trastero frente','cota_directa_m':4.19,'espesor_directo_m':.25,'max_desplazamiento_m':.001},
 {'elemento':'Puerta norte trastero, hueco bruto','cota_directa_m':.96,'ancla':'Jamba oeste X7.3025','max_desplazamiento_m':.0052},
 {'elemento':'Piscina','cota_directa_m':[3.5,5.0],'anclas':'Esquina NO X11.7094/Y10.8585','max_desplazamiento_m':.0038}]
remap_x={10.4013:10.4012,8.2677:8.2625};remap_y={8.13435:8.1377,7.8867:7.8877}
def mapped(p):
 x,y=p
 return [next((b for a,b in remap_x.items() if abs(x-a)<1e-5),x),next((b for a,b in remap_y.items() if abs(y-a)<1e-5),y)]
P.update(version=2,estado='Planta final V2, cotas nominales nuevas prioritarias',paginas={'planta_final':1,'fuente_z_original':[38,39]},fuente_pdf='fuentes/planta_final_proyecto_obra.pdf',fuente_sha256=U['fuente_planta']['sha256'],ajustes_nominales=adjustments)
P['criterio']='Registro PDF final +112.68ptX al sistema existente; escala 1:150. Nuevas cotas nominales de trastero/piscina prevalecen sobre cuantización. Ningún ajuste para imponer superficies rotuladas.'
P['muros']=copy.deepcopy(A['muros'])
trseq=A['trastero']['muros_seqno_pdf']
for w in P['muros']:
 if w['seqno_pdf'] in trseq:
  w['poligonos_xy_m']=[[mapped(v) for v in pg] for pg in w['poligonos_xy_m']]
 w['bbox_xy_m']=bbox([v for pg in w['poligonos_xy_m'] for v in pg]);w['clasificacion']='trastero' if w['seqno_pdf'] in trseq else 'vivienda_existente'
 w['fuente_pagina']=1;w['altura_m']=3.35
P['tendedero']=copy.deepcopy(A['tendedero'])
P['parcela']=contorno(A['parcela']['poligono_xy_m'],635.60,'Planta final PDF1: 10 vértices vectoriales, lindero irregular.')
P['huella_vivienda']=contorno([mapped(v) for v in A['huella_vivienda_con_trastero']['poligono_xy_m']],211.63,'Planta final PDF1: vivienda y trastero; cierre de huecos en fachada.')
T=copy.deepcopy(A['trastero'])
for k in ['contorno_exterior','interior_base','umbral_sur']:
 T[k]['poligono_xy_m']=[mapped(v) for v in T[k]['poligono_xy_m']];T[k]['area_modelada_m2']=area(T[k]['poligono_xy_m'])
T['puerta_norte']['bbox_xy_m']=[7.3025,12.0777,8.2625,12.42695]
T['porton_sur']['bbox_xy_m']=[4.826,7.8877,8.8265,8.1377]
T['interior_dimensiones_modeladas_m']=[7.15,3.94];T['profundidad_exterior_modelada_m']=4.19
T['fuente_z']='Confirmaciones expresas del usuario, 2026-10-06'
P['trastero']=T
P['pergola']={'estado':'RETIRADA por planta final V2','vigas_visibles_planta_cubierta':[]}
P['cesped_patches']=copy.deepcopy(A['cesped_patches'])
for v in P['cesped_patches']:v['fuente']='Planta final PDF1: relleno césped, seq '+str(v['fuente']['seqno_pdf'])
P['piscina'].update(poligono_xy_m=[[11.7094,10.8585],[15.2094,10.8585],[15.2094,5.8585],[11.7094,5.8585]],area_m2=17.5,dimensiones_directas_m=[3.5,5],fuente='Planta final PDF1, cotas directas3.50×5.00; esquinaNO registrada')
for s in P['piscina']['escalera']:
 s['poligono_xy_m']=[[x-.00635+( .00115 if abs(x-15.2146)<1e-4 else 0),y] for x,y in s['poligono_xy_m']]
 s['fuente']='Planta final PDF1: referencias XY escalones; Z sin dato'
P['incertidumbres']=copy.deepcopy(A['incertidumbres'])
oldholes={h['nombre']:h for h in H['huecos_exteriores']}
holes=[]
for h in A['huecos_exteriores_compartidos_v1']:
 q=copy.deepcopy(oldholes[h['nombre']]);q['bbox_xy_m']=h['bbox_xy_m_registro_parcela'];q['bbox_pdf_pt']=h['bbox_pdf_v2_pt'];q['fuente']='Planta final PDF1, gap vectorial entre muros';q['ancho_modelado_m']=h['ancho_vector_m'];q['ancho_grafico_m']=h['ancho_vector_m'];holes.append(q)
q={'nombre':'P_porton_trastero_sur','estancia':'Trastero','fachada_local':'S','tipo_documental_propuesto':'Porton','bbox_xy_m':T['porton_sur']['bbox_xy_m'],'z_antepecho_m':0,'z_dintel_m':2.5,'normal_exterior_xy':[0,-1],'fuente':'Planta final PDF1, hueco frontal vectorial4.0005m','fuente_z':'Usuario confirma portón alto2.50m','ancho_modelado_m':4.0005,'alto_modelado_m':2.5,'ancho_documental_m':None,'discrepancia':'Mecanismo y despiece no especificados; hoja opaca neutra, sin carriles ni sistema supuesto.'}
holes.append(q);H['huecos_exteriores']=holes;P['huecos_exteriores']=copy.deepcopy(holes)
H.update(version=2,estado='Z vivienda original y Z trastero confirmadas por usuario',revision='V2')
H['trastero_confirmaciones_usuario']=copy.deepcopy(U['confirmaciones_usuario'])
H['puerta_interior_trastero']={'nombre':'P_interior_trastero_norte','bbox_xy_m':T['puerta_norte']['bbox_xy_m'],'alto_m':2.03,'ancho_hueco_nominal_m':.96,'ancho_hoja_grafico_m':.81915,'apertura':'Hacia trastero; bisagra oeste','fuente_xy':'Planta final PDF1, símbolo carpintería','fuente_z':'Confirmación usuario2.03m'}
H['pergola']={'estado':'RETIRADA por planta final; sin geometría'}
H['incertidumbres']=[v for v in H['incertidumbres'] if 'pergola' not in str(v).lower()]
H['cubierta']['panos']=[v for v in H['cubierta']['panos'] if 'instalaciones' not in v['nombre']]
H['cubierta']['panos'].append({'nombre':'Pano_trastero_V2','coronacion_m':4.4,'base_peto_m':3.7,'exterior':{'vertices_xy_m':T['contorno_exterior']['poligono_xy_m']},'regla':'XYplanta final; Zusuario; respetar intersección con portal y cuerpo alto existentes'})
H['cubierta']['petos_tramos']=[v for v in H['cubierta']['petos_tramos'] if 'instalaciones' not in v['nombre']]
for name,b in [('W',[2.9972,7.8877,3.14325,11.2776]),('S',[3.14325,7.8877,10.5029,8.0391]),('E',[10.5029,8.0391,10.64895,12.0777])]:
 H['cubierta']['petos_tramos'].append({'nombre':'Peto_trastero_'+name,'bbox_xy_m':b,'z_base_m':3.7,'z_coronacion_m':4.4,'fuente':'XYplanta final, espesorpeto existentePDF37; altura4.40confirmadausuario'})
# Mobiliario: sólo huellas dibujadas, las alturas siguen siendo assets de visualización.
disappeared=set(A['mobiliario_desaparecido_nombres_v1'])
F['objetos']=[v for v in F['objetos'] if v['nombre'] not in disappeared]
updates={v['nombre']:v for v in A['mobiliario_cambiado'] if 'bbox_xy_m' in v and v['accion'] in ['mover','sustituir']}
updates.update({v['nombre']:v for v in A['sillas_comedor_interior_v2']})
for it in F['objetos']:
 if it['nombre'] in updates:
  b=updates[it['nombre']]['bbox_xy_m'];it.update(bbox_xy_m=b,centro_xy_m=[(b[0]+b[2])/2,(b[1]+b[3])/2],tamano_bbox_xy_m=[b[2]-b[0],b[3]-b[1]],huella_xy_m=[[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]]],fuente='Planta final PDF1, símbolo actualizado')
F.update(version=2,fuente_pdf='fuentes/planta_final_proyecto_obra.pdf',pagina=1,estado='Mobiliario existente común y símbolos actualizados en planta final. Trastero racks/gym/moto sólo referenciasXY; no inventar assetsdimensionales.')
F['referencias_trastero']=[v for v in A['mobiliario_cambiado'] if v['accion']=='anadir']
CAM['revision']='V2';CAM['fuente_planta_final']='fuentes/planta_final_proyecto_obra.pdf'
for ca in CAM['camaras_renders']:
 ca['explicacion']='Cámara de la revisión V2; toda geometría permanece idéntica entre vistas. Ajustes de cámara no alteran la parcela.'
 if ca['id']=='08':ca.update(posicion_m=[15.7,17.8,1.65],objetivo_m=[11.8,20.1,1.65],focal_mm=30,shift_y=.03)
for name,data in [('datos_planta.json',P),('datos_alturas.json',H),('datos_mobiliario.json',F),('criterios_qa_camaras.json',CAM)]:
 (DIR/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
(ROOT/'analisis_v2/ajustes_nominales_aplicados.json').write_text(json.dumps(adjustments,ensure_ascii=False,indent=2))
print('V2 aplicada:',len(P['muros']),'muros;',len(holes),'huecos exteriores; parcela',P['parcela']['area_traced_m2'],'m²; edificación',P['huella_vivienda']['area_traced_m2'],'m²')
