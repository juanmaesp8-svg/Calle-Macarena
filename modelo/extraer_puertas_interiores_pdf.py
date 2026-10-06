"""Puertas interiores: vectores PDF36 registrados al sistema de planta35."""
from pathlib import Path
import fitz,json,math
PDF=Path('/workspace/attachments/7d44de5b-6e10-466c-a21a-671bc224714e/001 PROYECTO BÁSICO DE VIVIENDA UNIFAMILIAR EN CALLE MACARENA Nº16.pdf')
OUT=Path('/workspace/arquitectura-macarena/modelo/datos_puertas_interiores.json')
F=127/2400;OR=(205.64,770.32);DY=1.68
p=fitz.open(PDF);draw={d['seqno']:d for d in p[35].get_drawings()}
def pt35(v):return [round(v[0],6),round(v[1]+DY,6)]
def xy(v):return [round((v[0]-OR[0])*F,6),round((OR[1]-v[1])*F,6)]
def bbox35(r):return [round(r[0],6),round(r[1]+DY,6),round(r[2],6),round(r[3]+DY,6)]
def bboxxy(r):return [round((r[0]-OR[0])*F,6),round((OR[1]-r[3])*F,6),round((r[2]-OR[0])*F,6),round((OR[1]-r[1])*F,6)]
def qupoly(d):
 q=d['items'][0][1];return [pt35(v) for v in [q.ul,q.ur,q.lr,q.ll]]
def build(name,room,typ,seq,gap,hinge_side=None,closed_vec=None,arc_seq=None,source_jambs=None,notes=None,confidence='alta_para_XY'):
 d=draw[seq];b=bbox35(d['rect']);horizontal=b[2]-b[0]>b[3]-b[1]
 ends=[(b[0],(b[1]+b[3])/2),(b[2],(b[1]+b[3])/2)] if horizontal else [((b[0]+b[2])/2,b[1]),((b[0]+b[2])/2,b[3])]
 width=math.dist(*ends)*F
 obj={'nombre':name,'estancias':room,'tipo':typ,'estado_identificacion':confidence,'seqno_hoja_pdf36':seq,'fuente_pagina':36,'registro_a_pagina35_dy_pt':DY,'hoja_poligono_pdf35_pt':qupoly(d),'hoja_bbox_pdf35_pt':b,'hoja_bbox_xy_m':bboxxy(b),'hoja_eje_pdf35_pt':ends,'hoja_eje_xy_m':[xy(v) for v in ends],'ancho_hoja_grafico_m':round(width,6),'ancho_generico_memoria_m':.825,'ancho_modelado_m':round(width,6),'espesor_modelado_m':.035,'altura_hoja_m':2.03 if confidence!='ambigua' else None,'z_base_m':0,'z_dintel_real_m':None,'intervalo_superior_hueco_no_definido_z_m':[2.03,3.35],'fuente_altura_hoja':'Memoria p21: puertas ciegas hoja lisa y fijo superior DMF lacado,203×82,5×3,5cm. Altura2,03 y espesor0,035 directos; ancho simbología conserva diferencias.', 'fuente_dintel':'Memoria p28 cita altura libre mínima2,50m; no es cota de dintel de cada puerta. No crear geometría de dintel/fijo superior.','notas':notes,'hueco_posible_bbox_pdf35_pt':gap,'hueco_posible_bbox_xy_m':bboxxy(gap) if gap else None,'hueco_criterio':'Intervalo vacío entre rellenos azules del plano35; caja de paso derivada. No se modifica ninguno de los muros existentes.' if gap else 'No se identifica un hueco de paso inequívoco; sólo referencia.'}
 if typ=='abatible':
  hinge=ends[0] if hinge_side=='first' else ends[1];free=ends[1] if hinge_side=='first' else ends[0]
  hw=xy(hinge);fw=xy(free);cv=[closed_vec[0],-closed_vec[1]]
  openangle=math.atan2(fw[1]-hw[1],fw[0]-hw[0]);closedangle=math.atan2(cv[1],cv[0]);delta=(openangle-closedangle+math.pi)%(2*math.pi)-math.pi
  obj.update({'bisagra_pdf35_pt':hinge,'bisagra_xy_m':hw,'punta_libre_xy_m':fw,'direccion_cerrada_xy':cv,'direccion_abierta_xy':[round((fw[0]-hw[0])/width,6),round((fw[1]-hw[1])/width,6)],'sentido_apertura_visto_desde_arriba':'antihorario' if delta>0 else 'horario','angulo_apertura_grafico_grados':round(abs(math.degrees(delta)),4),'angulo_hoja_abierta_xy_grados':round(math.degrees(openangle),4),'seqno_arco_pdf36':arc_seq,'arco_bezier_pdf35_pt':[pt35(v) for v in draw[arc_seq]['items'][0][1:]] if arc_seq else None})
 elif typ=='corredera':obj.update({'bisagra_xy_m':None,'sentido_apertura':'Hoja conservada en posición desplazada dibujada; eje de desplazamiento paralelo al eje largo. Signo/recorrido no acotados.','recorrido_desplazamiento_m':None})
 else:obj.update({'bisagra_xy_m':None,'sentido_apertura':None,'recorrido_desplazamiento_m':None})
 obj['jambas_referencia_pdf35_pt']=[bbox35(draw[s]['rect']) for s in (source_jambs or [])]
 return obj
objs=[]
# Hoja exacta representada abierta a90grados; huecos de rellenos azules página35.
specs=[
 ('P_int_cocina_distribuidor1','Cocina / distribuidor1',3476,[323.84,348.88,328.52,367.12],'first',(0,1),3478,[3475,3477]),
 ('P_int_dormitorio3','Dormitorio3 / distribuidor2',3483,[323.84,278.80,328.52,296.92],'first',(0,1),3485,[3482,3484]),
 ('P_int_dormitorio2','Dormitorio2 / distribuidor2',3489,[323.84,236.08,328.52,254.20],'first',(0,-1),3491,[3488,3490]),
 ('P_int_suite_principal','Suite dormitorio1 / distribuidor2',3499,[305.24,209.56,323.36,211.48],'last',(1,0),3501,[3498,3500]),
 ('P_int_bano2','Baño2 / distribuidor2',3511,[302.96,298.84,304.88,315.88],'last',(0,-1),3513,[3510,3512]),
 ('P_int_distribuidor2','Distribuidor2 / distribuidor1',4456,[305.24,335.68,323.36,337.60],'last',(1,0),4458,[4455,4457]),
 ('P_int_aseo','Aseo / distribuidor1',4680,[302.96,379.12,304.88,396.16],'last',(0,1),4682,[4679,4681]),
 ('P_int_despacho','Despacho / distribuidor2',4711,[302.96,250.24,304.88,268.36],'last',(0,-1),4713,[4710,4712]),
]
for n,r,s,g,h,cl,a,j in specs:objs.append(build(n,r,'abatible',s,g,h,cl,a,j))
# Correderas: hoja dibujada estacionada en bolsillo, sin inventar posición cerrada ni recorrido.
slides=[
 ('P_int_bano1_corredera','Baño1 / paso suite',4290,[302.96,171.76,304.88,190.72],'Hoja vertical aparcada hacia parte superior del plano, entre dos paredes finas del bolsillo.'),
 ('P_int_vestidor_corredera','Vestidor / paso suite',4510,[325.64,169.96,342.68,171.76],'Hoja horizontal desplazada hacia izquierda y parcialmente dentro del hueco.'),
 ('P_int_cocina_hall_corredera','Cocina / hall entrada',4587,[323.84,433.60,328.52,455.20],'Hoja vertical desplazada hacia cocina, parte superior del plano; hueco inferido hasta encuentro con partición salón.'),
 ('P_int_lavadero_corredera','Lavadero / distribuidor1',4884,[302.96,360.28,304.88,377.32],'Hoja vertical aparcada hacia parte superior del plano, bolsillo entre paredes finas.'),
]
for n,r,s,g,note in slides:objs.append(build(n,r,'corredera',s,g,notes=note))
objs.append(build('Referencia_hoja_horizontal_servicios','Encuentro lavadero/aseo/distribuidor1','no_asignada',4717,None,notes='Línea/hoja horizontal en partición entre lavadero y aseo. No hay un hueco de paso inequívoco asociado y podría ser carpintería/panel. Guardar como referencia visible en viewport, oculta en render.',confidence='ambigua'))
data={'version':1,'fuente_pdf':str(PDF),'factor_m_por_pt':F,'origen_pdf35_pt':OR,'estado':'12hojas interiores identificables+1referencia ambigua; hojas abiertas según planta','puertas':objs,'criterio_modelado':'Añadir sólo hojas de2,03m de altura y0,035m de espesor. Anchos y posicionesXY proceden del símbolo del PDF, no de la medida genérica82,5cm. No crear dinteles ni fijos superiores sin cota. Intervalo2,03–3,35m del hueco interior permanece no definido y se registra mediante referencias. No transformar ni desplazar muros existentes.'}
OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('Guardado',OUT,'puertas',len(objs),'hojas modelables',sum(x['altura_hoja_m'] is not None for x in objs))
for o in objs:print(o['nombre'],o['tipo'],o['ancho_hoja_grafico_m'],o.get('sentido_apertura_visto_desde_arriba','desplazada'))
