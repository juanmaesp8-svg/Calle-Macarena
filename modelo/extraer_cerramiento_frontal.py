from pathlib import Path
import json, math, fitz
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT/'modelo'
base=json.loads((ROOT/'geometria_base.json').read_text());F=base['transformacion_planta_base']['factor_m_por_pt']
source=Path(base['fuente']['ruta']);pdf=fitz.open(source if source.is_absolute() else ROOT/source);page=pdf[37]
P0=[0.0,0.0];P1=[18.61185,1.02235]
L=math.dist(P0,P1);T=[(P1[i]-P0[i])/L for i in range(2)];N=[-T[1],T[0]]
# Absolute right boundary governs orientation and the end wall. Do not scale an unknown scheme.
SRC_END=574.52;SRC_BASE=753.16;ZBASE=-.15
WALL_DEPTH=4.8*F
C_OFFSET=WALL_DEPTH/2

def s(u):return L+(u-SRC_END)*F

def xyz(u,v,offset=C_OFFSET):
 ss=s(u);return [round(P0[0]+T[0]*ss+N[0]*offset,6),round(P0[1]+T[1]*ss+N[1]*offset,6),round(ZBASE+(SRC_BASE-v)*F,6)]

def reg_box(b):
 return {'bbox_pdf_pt':b,'intervalo_s_m':[round(s(b[0]),6),round(s(b[2]),6)],'ancho_m':round((b[2]-b[0])*F,6),
         'z_inferior_m':round(ZBASE+(SRC_BASE-b[3])*F,6),'z_superior_m':round(ZBASE+(SRC_BASE-b[1])*F,6),
         'esquinas_xyz_m':[xyz(b[0],b[3]),xyz(b[2],b[3]),xyz(b[2],b[1]),xyz(b[0],b[1])]}

# Extract the actual visible wire line pairs; no mesh count, pitch, or profile depth invented.
all_lines=set()
for path in page.get_drawings():
 c=path['color']
 if not c or max(c)>.001 or path['fill']:continue
 for item in path['items']:
  if item[0]!='l':continue
  a,b=item[1:3];aa=(round(a.x,2),round(a.y,2));bb=(round(b.x,2),round(b.y,2))
  if 424<=aa[0]<=564 and 424<=bb[0]<=564 and 715<=aa[1]<=744 and 715<=bb[1]<=744:
   all_lines.add(tuple(sorted((aa,bb))))

def pair_values(values):
 vals=sorted(set(values));out=[];i=0
 while i<len(vals):
  if i+1<len(vals) and vals[i+1]-vals[i]<=.40:
   out.append([vals[i],vals[i+1]]);i+=2
  else:
   out.append([vals[i],vals[i]]);i+=1
 return out

def grille(index,b,outer_frame,inner):
 r={'nombre':f'Rejilla_frontal_{index}',**reg_box(b),'marco_exterior':reg_box(outer_frame),'claro_interior':reg_box(inner)}
 xmin,ymin,xmax,ymax=inner
 vxs=[];hys=[];lines=[]
 for a,bb in sorted(all_lines):
  if not(xmin-.01<=a[0]<=xmax+.01 and xmin-.01<=bb[0]<=xmax+.01 and ymin-.01<=a[1]<=ymax+.01 and ymin-.01<=bb[1]<=ymax+.01):continue
  lines.append({'extremos_pdf_pt':[list(a),list(bb)],'extremos_xyz_m':[xyz(*a),xyz(*bb)]})
  if abs(a[0]-bb[0])<.01 and abs(a[1]-ymin)<.01 and abs(bb[1]-ymax)<.01 and xmin+.01<a[0]<xmax-.01:vxs.append(a[0])
  if abs(a[1]-bb[1])<.01 and abs(a[0]-xmin)<.01 and abs(bb[0]-xmax)<.01 and ymin+.01<a[1]<ymax-.01:hys.append(a[1])
 vbars=[]
 for u0,u1 in pair_values(vxs):
  vbars.append({'u_limites_pdf_pt':[u0,u1],'ancho_grafico_frontal_m':round((u1-u0)*F,6),'vertices_xyz_m':[xyz(u0,ymax),xyz(u1,ymax),xyz(u1,ymin),xyz(u0,ymin)]})
 hbars=[]
 for v0,v1 in pair_values(hys):
  hbars.append({'v_limites_pdf_pt':[v0,v1],'alto_grafico_frontal_m':round((v1-v0)*F,6),'vertices_xyz_m':[xyz(xmin,v1),xyz(xmax,v1),xyz(xmax,v0),xyz(xmin,v0)]})
 r.update({'trazos_vectoriales':lines,'barrotes_verticales_planos':vbars,'barrotes_horizontales_planos':hbars,
           'espesor_normal_barrotes_m':None,'criterio_barrotes':'Los pares de trazos definen anchuras visibles en alzado. Conservar como caras planas/2D o trazos. No extruir perfiles de profundidad desconocida ni sustituir por34/12 unidades uniformes inventadas.'})
 return r

gr1=grille(1,[424.28,715.36,488.12,743.68],[424.64,715.36,487.76,743.44],[426.08,716.92,486.32,741.88])
gr2=grille(2,[499.40,715.36,563.24,743.68],[499.76,715.36,563.00,743.44],[501.20,716.92,561.44,741.88])
D={
 'version':1,'fuente':'PDF38, esquema CERRAMIENTO EXTERIOR, escalaA3 1:150, vectores, no raster.',
 'unidades':'metros, escala1:1; coordenadasPDFpuntos',
 'factor_m_por_pt':F,'resolucion_pt':.12,'resolucion_m':.12*F,
 'estado':'Mediciones exactas respecto geometría vectorial del PDF, con registro documentado y contradicción de longitud total. No rediseñar parcela ni puertas para encajar esquema.',
 'registro':{
  'criterio':'Anclar extremo derecho del esquema u574,52pt al vértice frontal/derecho de parcela y usar dirección real del lindero. Escala nominal fija. Puertas permanecen segúnplanta36; el esquema sólo aporta rejillas/muros del tramo derecho.',
  'lindero_inicio_xy_m':P0,'lindero_fin_xy_m':P1,'largo_lindero_m':L,'tangente_xy':T,'normal_interior_xy':N,
  'origen_u_pdf_pt':SRC_END,'origen_v_pdf_pt':SRC_BASE,'z_base_representacion_m':ZBASE,
  'espesor_muro_deducido_planta_m':WALL_DEPTH,'desplazamiento_plano_rejilla_al_centro_muro_m':C_OFFSET,
  'formula_s':'s=18,639908155...+(u−574,52)×0,0529166667; XYZ=P0+T×s+N×0,127; Z=−0,15+(753,16−v)×F.',
  'formula_s_exacta':'Usar registro.largo_lindero_m, no literal redondeado.',
  'sin_reescalado':'No normalizar18,758m de esquema para ajustar18,640m de planta: cambiaría anchos de rejillas.'
 },
 'dimensiones_esquema':{
  'intervalo_total_pdf_pt':[220.04,574.52],'longitud_total_m':(574.52-220.04)*F,
  'base_y_pt':753.16,'coronacion_y_pt':715.36,'altura_m':(753.16-715.36)*F,
  's_total_registrado_m':[s(220.04),s(574.52)],'coronacion_modelo_m':ZBASE+(SRC_BASE-715.36)*F
 },
 'rejillas':[gr1,gr2],
 'panos_muro_tramo_derecho':[
  {'nombre':'Machon_izquierdo_junto_garaje',**reg_box([413.00,715.36,424.28,753.16])},
  {'nombre':'Machon_intermedio_rejillas',**reg_box([488.12,715.36,499.40,753.16])},
  {'nombre':'Machon_derecho_lindero',**reg_box([563.24,715.36,574.52,753.16])},
  {'nombre':'Zocalo_continuo_bajo_rejillas',**reg_box([413.00,743.68,574.52,753.16])}
 ],
 'portones_esquema_solo_referencia':{
  'vehiculos_u_pdf_pt':[299.96,413.00],'luz_m':(413.00-299.96)*F,
  'peatonal_hoja_candidata_u_pdf_pt':[266.36,288.32],'ancho_m':(288.32-266.36)*F,
  'regla':'No aplicar estosintervalos para trasladar/cambiar puerta peatonal ni portón delmodelo; ya gobernados por planta.'
 },
 'contradicciones':[
  {'id':'Ancho_total','planta_m':L,'esquema_m':(574.52-220.04)*F,'diferencia_m':(574.52-220.04)*F-L,'impacto':'Registro al extremo derecho deja inicio esquema en s≈−0,118m; no modelar ese inicio ni mover lindero.'},
  {'id':'Jamba_vehiculos','s_jamba_esquema_registrada_m':s(413.00),'evidencia_planta':'Cara de poste enplanta36 x395,48/y753,40; registrarY+1,68 a35. Su proyección al lindero gobiernaapertura.',
   'recomendacion':'Conservar acceso vehicular segúnplanta. Si cara esquema difiere, recortar exclusivamente extremo de machón izquierdo al poste existente y documentar residual; no modificar luz puerta ni rejillas.'},
  {'id':'Hoja_peatonal','planta_m':.820355,'alzado_candidata_m':(288.32-266.36)*F,'impacto':'No aplicar alzado dehoja a puerta existente.'},
  {'id':'Espesor_barrotes','valor_m':None,'impacto':'Alzado2D define ancho visible/paso pero no profundidad normal debarrotes; representarlos con caras/trazos explícitos.'},
  {'id':'Franja_coronacion','valor':'Aberturas empiezan en y715,36, misma coronación de muro. No existe dintel blanco por encima de estasrejillas en elesquema.'}
 ],
 'cambio_builder_recomendado':{
  'sustituir_intervalos_aproximados':'Leer rejillas[].esquinas_xyz_m y panos_muro_tramo_derecho en lugar X10,75–14,29/14,76–18,14.',
  'z_huecos_m':[round(ZBASE+(SRC_BASE-743.68)*F,6),round(ZBASE+(SRC_BASE-715.36)*F,6)],
  'quitar_dintel_inventado':'Eliminar muro blanco sobre ambas aberturas; mantener tresmachones y zócalo continuo.',
  'detalle_rejillas':'Conservar coordenadasdelmarco exterior/interior; usar barrotes_verticales_planos/horizontales_planos como2D, sin volumen adicionalindocumentado.',
  'puertas':'Preservar posiciones ydimensiones de planta; no importar portones de esteesquema.'
 }
}
# Add exact comparison at the existing gate post rather than relying on a verbal estimate.
post_pdf=[395.48,753.40+1.68];O=base['transformacion_planta_base']['origen_pdf_pt'];post_xy=[(post_pdf[0]-O[0])*F,(O[1]-post_pdf[1])*F]
s_post=sum((post_xy[i]-P0[i])*T[i] for i in range(2))
D['contradicciones'][1].update({'poste_planta35_pdf_pt':post_pdf,'poste_xy_m':post_xy,'s_poste_planta_m':s_post,'diferencia_al_registro_m':s(413.0)-s_post})
(MODEL/'datos_cerramiento_frontal.json').write_text(json.dumps(D,ensure_ascii=False,indent=2))
print('Grilles:',[(len(g['barrotes_verticales_planos']),len(g['barrotes_horizontales_planos'])) for g in D['rejillas']])
print('Intervals s',[(g['intervalo_s_m'],[g['z_inferior_m'],g['z_superior_m']]) for g in D['rejillas']])
print('Jamba residual',s(413.0)-s_post,'m; total length residual',D['contradicciones'][0]['diferencia_m'],'m')
