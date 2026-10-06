"""Geometría XY de los símbolos de mobiliario mayor de lámina02; Z no definido."""
from pathlib import Path
import fitz,json
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'fuentes/proyecto_basico.pdf'
OUT=ROOT/'modelo/datos_mobiliario.json'
F=127/2400;OR=(205.64,770.32)
def xy(p):return [round((p[0]-OR[0])*F,6),round((OR[1]-p[1])*F,6)]
def boxpts(b):return [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]
p=fitz.open(PDF);draw=p[34].get_drawings()
objs=[]
def add(name,typ,room,bbox,foot=None,notes=None):
 vs=foot or boxpts(bbox)
 source=[]
 for d in draw:
  r=d['rect'];c=d.get('fill')
  if c and abs(c[0]-.8902)<.0005 and r.x0>=bbox[0]-.002 and r.x1<=bbox[2]+.002 and r.y0>=bbox[1]-.002 and r.y1<=bbox[3]+.002:
   source.append(d['seqno'])
 obj={'nombre':name,'tipo':typ,'estancia':room,'bbox_pdf_pt':list(bbox),'bbox_xy_m':[round((bbox[0]-OR[0])*F,6),round((OR[1]-bbox[3])*F,6),round((bbox[2]-OR[0])*F,6),round((OR[1]-bbox[1])*F,6)],'huella_pdf_pt':vs,'huella_xy_m':[xy(v) for v in vs],'centro_xy_m':xy(((bbox[0]+bbox[2])/2,(bbox[1]+bbox[3])/2)),'tamano_bbox_xy_m':[round((bbox[2]-bbox[0])*F,6),round((bbox[3]-bbox[1])*F,6)],'z_base_m':None,'altura_m':None,'fuente':'Página35/lámina02; símbolo vectorial000SOBREADO RGB≈.8902 y líneas000MOBILIARIO','seqno_rellenos_pdf':source,'criterio':'Medida gráfica derivada; no es cota escrita. Altura del asset decorativo a elegir y registrar; no cambiar huella o ubicación.', 'notas':notes}
 objs.append(obj)
 return obj
add('cama_dormitorio_1','cama_doble','Dormitorio nº1',(389.96,129.28,423.92,167.08),notes='Cabecero haciaYpositivo/parte superior de plano; símbolo completo2,00025m de longitud.')
add('cama_dormitorio_2','cama_doble','Dormitorio nº2',(347.36,197.56,381.44,235.36),notes='Cabecero haciaYpositivo/parte superior de plano.')
add('cama_dormitorio_3','cama_doble','Dormitorio nº3',(347.36,297.64,381.44,335.44),notes='Cabecero haciaYnegativo/parte inferior de plano; orientación opuesta al dormitorio2.')
add('sofa_L_salon','sofa_L','Salón comedor',(271.52,462.52,328.28,492.64),foot=[(271.52,462.52),(328.28,462.52),(328.28,476.80),(285.92,476.80),(285.92,492.64),(271.52,492.64)],notes='Contorno enL; no usar bbox rectangular como huella maciza.')
add('asiento_salon_oeste','asiento_ottoman','Salón comedor',(271.52,499.96,285.92,512.56))
add('butaca_salon_1','butaca','Salón comedor',(329.36,484.48,343.76,496.96))
add('butaca_salon_2','butaca','Salón comedor',(329.36,499.96,343.76,512.56))
add('mesa_centro_salon','mesa_baja','Salón comedor',(299.12,487.12,316.16,509.80))
add('mesa_comedor_interior','mesa_comedor','Salón comedor',(366.92,476.56,385.76,510.64))
# Seis sillas laterales y dos de cabecera del comedor interior.
for i,(ya,yb) in enumerate([(478.84,486.16),(489.88,497.32),(500.92,508.36)]):
 add(f'silla_interior_izq_{i+1}','silla_comedor','Salón comedor',(362.12,ya,366.92,yb))
 add(f'silla_interior_der_{i+1}','silla_comedor','Salón comedor',(385.76,ya,390.56,yb))
add('silla_interior_cabecera_norte','silla_comedor','Salón comedor',(372.68,471.88,380.00,476.56))
add('silla_interior_cabecera_sur','silla_comedor','Salón comedor',(372.68,510.64,380.00,515.32))
add('encimera_cocina','encimera_lineal','Cocina',(328.52,367.12,339.80,433.60),notes='Franja apoyada en tabique oeste de cocina; huecos de placa/fregadero incluidos como referencias, sin mobiliario en huecos de paso.')
add('isla_cocina','isla','Cocina',(358.76,381.40,381.44,419.20))
for i,(ya,yb) in enumerate([(385.24,392.68),(396.64,404.08),(408.04,415.48)]):add(f'taburete_isla_{i+1}','taburete','Cocina',(354.08,ya,358.76,yb))
add('mesa_comedor_terraza','mesa_comedor_exterior','Porche descubierto',(427.76,370.96,446.60,405.04))
for i,(ya,yb) in enumerate([(373.24,380.56),(384.28,391.72),(395.32,402.76)]):
 add(f'silla_terraza_izq_{i+1}','silla_comedor','Porche descubierto',(422.96,ya,427.76,yb))
 add(f'silla_terraza_der_{i+1}','silla_comedor','Porche descubierto',(446.60,ya,451.40,yb))
add('silla_terraza_cabecera_norte','silla_comedor','Porche descubierto',(433.52,366.28,440.84,370.96))
add('silla_terraza_cabecera_sur','silla_comedor','Porche descubierto',(433.52,405.04,440.84,409.72))
add('mesa_comedor_pergola','mesa_comedor_exterior','Comedor piscina/pérgola',(352.76,570.28,386.72,589.12),notes='Mesa girada90grados respecto mesas de salón/terraza; eje largoX.')
for i,(xa,xb) in enumerate([(354.92,362.36),(366.08,373.40),(377.12,384.56)]):
 add(f'silla_pergola_norte_{i+1}','silla_comedor','Comedor piscina/pérgola',(xa,565.48,xb,570.28))
 add(f'silla_pergola_sur_{i+1}','silla_comedor','Comedor piscina/pérgola',(xa,589.12,xb,593.80))
add('silla_pergola_cabecera_oeste','silla_comedor','Comedor piscina/pérgola',(347.96,575.92,352.76,583.36))
add('silla_pergola_cabecera_este','silla_comedor','Comedor piscina/pérgola',(386.72,575.92,391.52,583.36))
# Dos conjuntos de salón exterior idénticos, al lado de dormitorios y salón.
for prefix,offset in [('terraza_dormitorios',0),('terraza_salon',219.00)]:
 def shift(b):return (b[0],b[1]+offset,b[2],b[3]+offset)
 add(f'sofa_{prefix}','sofa_3_plazas_exterior','Porche descubierto',shift((411.68,247.60,426.08,285.40)))
 add(f'mesa_centro_{prefix}','mesa_baja_exterior','Porche descubierto',shift((437.72,255.16,450.92,277.84)))
 for i,b in enumerate([(430.40,231.88,443.00,246.28),(446.00,231.88,458.60,246.28),(430.40,286.72,443.00,301.12),(446.00,286.72,458.60,301.12)]):add(f'butaca_{prefix}_{i+1}','butaca_exterior','Porche descubierto',shift(b))
# Líneas de trabajo encimera/placa/fregadero, con trazado exacto a escala.
segments=[]
for d in draw:
 r=d['rect']
 if d['layer']=='000 MOBILIARIO' and r.x0>=328.50 and r.x1<=339.82 and r.y0>=367.10 and r.y1<=433.62:
  for it in d['items']:
   if it[0]=='l':segments.append({'puntos_pdf_pt':[[float(x) for x in it[1]],[float(x) for x in it[2]]],'puntos_xy_m':[xy(it[1]),xy(it[2])],'seqno_pdf':d['seqno']})
data={'version':1,'fuente_pdf':str(PDF),'pagina':35,'lamina':'02','origen_pdf_pt':OR,'factor_m_por_pt':F,'estado':'Mobiliario auxiliar extraído de simbología, no dimensiones arquitectónicas nuevas','ejes':'X derecha de plano;Y hacia trasero;metros','objetos':objs,'lineas_encimera':segments,'referencias_placa_bbox_pdf_pt':[331.52,377.08,339.44,390.28],'referencias_fregadero_bbox_pdf_pt':[330.68,409.12,339.20,423.28],'criterio_z':'Todas las alturas desconocidas sonnull. El creador del modelo puede asignar altura/material decorativos de assets y registrar dicha decisión; mantendrá XY y paso libre dibujados.'}
OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('Guardado',OUT,'objetos',len(objs),'lineas_encimera',len(segments),'sin_relleno_en_bbox',[o['nombre'] for o in objs if not o['seqno_rellenos_pdf']])
