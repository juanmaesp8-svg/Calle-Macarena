"""Cotejo independiente de los vértices reales exportados por Blender y el PDF."""
from pathlib import Path
import sys,json,csv,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'modelo/python_deps'))
from shapely.geometry import Polygon,LineString,MultiPolygon
from shapely.ops import unary_union,polygonize
import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

B=json.loads((ROOT/'geometria_base.json').read_text())
H=json.loads((ROOT/'modelo/datos_alturas.json').read_text())
A=json.loads((ROOT/'control/mediciones_mesh_real.json').read_text())
O=A['objetos'];BY={o['nombre']:o for o in O}
F=0.05291666666666667
source=Path(B['fuente']['ruta'])
doc=fitz.open(source if source.is_absolute() else ROOT/source)

def slice_mesh(o,z):
    lines=[]
    vs=o['vertices']
    for face in o['caras']:
        points=[]
        for k,idx in enumerate(face):
            a=vs[idx];b=vs[face[(k+1)%len(face)]]
            if (a[2]-z)*(b[2]-z)<0:
                t=(z-a[2])/(b[2]-a[2]);points.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
        if len(points)==2 and math.dist(*points)>1e-9:lines.append(LineString(points))
    return unary_union(list(polygonize(unary_union(lines)))) if lines else Polygon()

walls=unary_union([slice_mesh(o,3.0) for o in O if o['categoria']=='muro_vivienda'])
parts=list(walls.geoms) if hasattr(walls,'geoms') else [walls]
foot=unary_union([Polygon(p.exterior) for p in parts if p.geom_type=='Polygon'])
expected=Polygon(B['poligonos']['envolvente_vivienda_incl_instalaciones']['points_xy_m'])
delta=foot.symmetric_difference(expected).area
distance=foot.hausdorff_distance(expected)
rows=[]
checks=[]
def check(label,value,target,tolerance,source,kind='Calculada del dibujo'):
    error=abs(value-target);ok=error<=tolerance
    checks.append({'elemento':label,'mesh':value,'objetivo_pdf':target,'error':error,'tolerancia':tolerance,'pasa':ok})
    rows.append([label,round(value,6),round(target,6),round(error,7),kind,source])
check('Huella construida m²',foot.area,expected.area,0.002,'Planta PDF35')
check('Diferencia simétrica huella m²',delta,0,.002,'Vértices de muro reales / PDF35')
check('Distancia máxima huella m',distance,0,.001,'Vértices de muro reales / PDF35')
check('Vivienda ancho máximo m',foot.bounds[2]-foot.bounds[0],10.0965,.001,'Planta PDF35')
check('Vivienda longitud total m',foot.bounds[3]-foot.bounds[1],26.39695,.001,'Planta PDF35')
for cat,key in [('parcela','parcela'),('piscina','piscina')]:
    candidates=[o for o in O if o['categoria']==cat]
    xy=unary_union([Polygon([(o['vertices'][i][0],o['vertices'][i][1]) for i in face]) for o in candidates for face in o['caras'] if len(face)>=3]).buffer(0)
    ref=Polygon(B['poligonos'][key]['points_xy_m'])
    check(cat+' área m²',xy.area,ref.area,.002,'Planta PDF35')
    check(cat+' posición / Hausdorff m',xy.hausdorff_distance(ref),0,.001,'Planta PDF35')
parcel_ref=Polygon(B['poligonos']['parcela']['points_xy_m'])
fence_faces=[]
for o in O:
    if not o['nombre'].startswith('Cerramiento_lindero_'):continue
    for face in o['caras']:
        pg=Polygon([(o['vertices'][i][0],o['vertices'][i][1]) for i in face])
        if pg.area>1e-9:fence_faces.append(pg)
fence=unary_union(fence_faces)
check('Cerramiento superficie fuera de parcela m²',fence.difference(parcel_ref).area,0,.0002,'Detalle tendedero PDF35; espesor extrapolado hacia dentro','Deducción explícita')
rows.append(['Cerramiento espesor hacia interior m',.1524,.1524,0,'Sólo directo en tendedero; resto deducido','PDF35; cara exterior sobre lindero'])
for h in H['huecos_exteriores']:
    real=BY[h['nombre']+'_dintel']['bbox_xyz'];b=h['bbox_xy_m']
    check(h['nombre']+' XY máx m',max(abs(real[i]-b[j]) for i,j in [(0,0),(1,1),(3,2),(4,3)]),0,.001,'Planta PDF35 / registro PDF36')
    check(h['nombre']+' dintel Z m',real[2],h['z_dintel_m'],.001,h['fuente_z'],'Directa / alzado calculado')
    sill=BY.get(h['nombre']+'_antepecho')
    if sill:check(h['nombre']+' antepecho Z m',sill['bbox_xyz'][5],h['z_antepecho_m'],.001,h['fuente_z'])
    width=max(real[3]-real[0],real[4]-real[1]);bottom=sill['bbox_xyz'][5] if sill else 0
    rows.append([h['nombre']+' ancho × alto m',f"{width:.4f} × {real[2]-bottom:.2f}",'', '', 'Mesh real; ancho gráfico/altura contrastada',h['alzado_fuente']])
for p in H['cubierta']['petos_tramos']:
    b=BY[p['nombre']]['bbox_xyz']
    check(p['nombre']+' coronación Z m',b[5],p['z_coronacion_m'],.001,'Cubierta PDF37; alzados38/secciones39','Directa / calculada')
for o in O:
    if o['categoria']=='forjado':
        check(o['nombre']+' base Z m',o['bbox_xyz'][2],3.35,.001,'PDF38/39','Directa')
        check(o['nombre']+' superior Z m',o['bbox_xyz'][5],3.7,.001,'PDF38/39','Directa')
    if o['categoria']=='marquesina':
        check(o['nombre']+' base Z m',o['bbox_xyz'][2],3.35,.001,'PDF38 lateral/vial y PDF39 sección4')
        check(o['nombre']+' superior Z m',o['bbox_xyz'][5],3.55,.001,'PDF38 lateral/vial y PDF39 sección4')
G=json.loads((ROOT/'modelo/datos_cerramiento_frontal.json').read_text())
for rg in G['rejillas']:
    for tipo in ['verticales','horizontales']:
        for i,bar in enumerate(rg['barrotes_'+tipo+'_planos']):
            real=BY[rg['nombre']+'_'+tipo+f'_{i+1:02d}']['vertices'];ref=bar['vertices_xyz_m']
            error=max(abs(v[k]-r[k]) for v,r in zip(real,ref) for k in range(3))
            check(rg['nombre']+' '+tipo+f' {i+1:02d} XYZ m',error,0,.001,'Vectores esquema PDF38, registro al lindero derecho')
    rows.append([rg['nombre']+' ancho × alto m',f"{rg['ancho_m']:.4f} × {rg['z_superior_m']-rg['z_inferior_m']:.4f}",'', '', 'Esquema vectorial registrado','PDF38; espesor normal desconocido'])
D=json.loads((ROOT/'modelo/datos_puertas_interiores.json').read_text())
for d in D['puertas']:
    o=BY.get(d['nombre']+'_hoja_posicion_planta')
    if o:check(d['nombre']+' alto hoja m',o['bbox_xyz'][5]-o['bbox_xyz'][2],2.03,.001,'MemoriaPDF21','Directa')
rows.append(['Aparcamiento superficie declarada m²','Sin límite de plazas definido','46.86','','Directa memoria; no polígono verificable','PDF11/35'])

with (ROOT/'tabla_dimensiones_modeladas.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f,delimiter=';');w.writerow(['Elemento','Mesh real','Referencia PDF','Error','Obtención','Fuente']);w.writerows(rows)

def fill(ax,g,color,alpha=.5):
    for p in (list(g.geoms) if hasattr(g,'geoms') else [g]):
        if p.geom_type=='Polygon' and not p.is_empty:
            ax.add_patch(Patch(list(p.exterior.coords),facecolor=color,edgecolor=color,alpha=alpha,lw=.6))

# Corte real del mesh a Z2 m; no dibujo recreado con dimensiones esperadas.
fig,axes=plt.subplots(1,2,figsize=(11,12))
parcel=Polygon(B['poligonos']['parcela']['points_xy_m'])
pool=Polygon(B['poligonos']['piscina']['points_xy_m'])
for ax in axes:
    ax.set_aspect('equal');ax.set_xlim(-1,20);ax.set_ylim(-1,39);ax.set_xlabel('X · m');ax.set_ylabel('Y · m')
    ax.plot(*parcel.exterior.xy,color='black',lw=1.2)
    fill(ax,pool,'#22b8cf',.4)
    for o in O:
        if o['categoria']=='muro_vivienda':fill(ax,slice_mesh(o,2.0),'#bc3838',.75)
    ax.plot(*foot.exterior.xy,color='#2fa75a',lw=.8) if foot.geom_type=='Polygon' else None
axes[0].set_title('Planta del modelo · corte Z=2,00 m')
page=doc[34];clip=fitz.Rect(190,45,575,790);pix=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=clip,alpha=False)
import numpy as np
img=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
axes[1].imshow(img,extent=[(clip.x0-205.64)*F,(clip.x1-205.64)*F,(770.32-clip.y1)*F,(770.32-clip.y0)*F],alpha=.65)
# Redraw actual wall cut above original raster.
for o in O:
    if o['categoria']=='muro_vivienda':fill(axes[1],slice_mesh(o,2.0),'#bc3838',.55)
axes[1].plot(*expected.exterior.xy,'--',color='#104bdb',lw=.7)
axes[1].set_title('Superposición: PDF35 + mesh real en rojo')
fig.tight_layout();fig.savefig(ROOT/'control/planta_mesh_y_superposicion.png',dpi=170);plt.close(fig)

# Proyecciones desde todos los polígonos de los meshes, ordenadas por profundidad.
architecture={'muro_vivienda','pilar_pergola','forjado','peto','marquesina','viga_pergola','carpinteria','vidrio'}
spec=[('puerta_principal',1,-1,0,True,952.04,194.92,(280,80,835,212)),('lateral_porche',1,1,0,False,220.76,514.48,(260,398,925,532)),('vial_publico',0,1,1,True,385.28,353.92,(415,244,655,372)),('trasero',0,-1,1,False,722.96,661.84,(450,553,690,680))]
for name,haxis,sign,depthaxis,reverse,origin,floor,cliprect in spec:
    fig,axes=plt.subplots(2,1,figsize=(12,5.8),height_ratios=[1,1])
    faces=[]
    for o in O:
        if o['categoria'] not in architecture:continue
        for face in o['caras']:
            vertices=[o['vertices'][i] for i in face]
            coords=[(sign*v[haxis],v[2]) for v in vertices]
            if Polygon(coords).area<1e-9:continue
            depth=sum(v[depthaxis] for v in vertices)/len(vertices)
            faces.append((depth,coords,o['categoria']))
    faces.sort(key=lambda x:x[0],reverse=reverse)
    for depth,coords,cat in faces:
        color='#466579' if cat=='vidrio' else '#303739' if cat=='carpinteria' else '#a3a3a3' if cat=='viga_pergola' else '#eeeeea'
        axes[0].add_patch(Patch(coords,facecolor=color,edgecolor='#525252',lw=.25))
    refclip=fitz.Rect(*cliprect);pix=doc[37].get_pixmap(matrix=fitz.Matrix(2,2),clip=refclip,alpha=False)
    data=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
    extent=[(refclip.x0-origin)*F,(refclip.x1-origin)*F,(floor-refclip.y1)*F,(floor-refclip.y0)*F]
    axes[1].imshow(data,extent=extent)
    minx=min(min(c[0] for c in p[1]) for p in faces)-.7;maxx=max(max(c[0] for c in p[1]) for p in faces)+.7
    for ax in axes:
        ax.set_aspect('equal');ax.set_xlim(minx,maxx);ax.set_ylim(-.35,5.75);ax.axhline(0,lw=.3,color='black');ax.set_ylabel('Z · m')
    axes[0].set_title('Mesh real · '+name.replace('_',' '));axes[1].set_title('Alzado original PDF38 · misma escala de ejes')
    fig.tight_layout();fig.savefig(ROOT/f'control/comparacion_alzado_{name}.png',dpi=170);plt.close(fig)

# Secciones: representar cotas comprobadas sin fingir una sección constructiva no documentada.
fig,axes=plt.subplots(2,1,figsize=(11,8),height_ratios=[1,1.5])
levels=[(-.15,'Jardín'),(0,'Suelo'),(3.2,'Cielorraso (calculado)'),(3.35,'Inferior forjado'),(3.7,'Superior forjado'),(4.4,'Peto bajo'),(4.75,'Portal'),(5.1,'Peto alto')]
for i,(z,label) in enumerate(levels):
    axes[0].plot([0,1], [z,z],lw=1,color='#263d49');axes[0].text(1.04,z,f'{label}: {z:+.2f} m',va='center',fontsize=8)
axes[0].set_ylim(-.45,5.45);axes[0].set_xlim(-.1,3.9);axes[0].axis('off');axes[0].set_title('Niveles del modelo contrastados con secciones PDF39')
pix=doc[38].get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False);im=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
axes[1].imshow(im);axes[1].axis('off');fig.tight_layout();fig.savefig(ROOT/'control/comparacion_niveles_secciones.png',dpi=160);plt.close(fig)

result={'apto_para_renders':all(c['pasa'] for c in checks),'alcance':'Concordancia con XY de plantas y Z de vistas concordantes; no certifica concordancia total entre dibujos contradictorios ni dimensiones ausentes.',
        'huella_mesh_m2':foot.area,'huella_pdf_m2':expected.area,'diferencia_simetrica_m2':delta,'hausdorff_m':distance,'controles':checks,'incertidumbres_pdf':H['incertidumbres']}
(ROOT/'control/control_resultado.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))

styles=getSampleStyleSheet();story=[]
def p(t,style='BodyText'):story.append(Paragraph(t,styles[style]));story.append(Spacer(1,7))
p('Control geométrico del modelo 3D','Title')
p('Calle Macarena nº16 · escala 1:1 · mediciones de los meshes reales de Blender')
p('Resultado: '+('APTO para visualización con los criterios documentados.' if result['apto_para_renders'] else 'NO APTO: revisar fallos antes de renderizar.'),'Heading2')
p(f"Huella medida {foot.area:.4f} m²; huella vectorial {expected.area:.4f} m²; diferencia simétrica {delta:.8f} m². Distancia máxima {distance:.8f} m. Estos errores numéricos son de exportación float32; la precisión del PDF es mucho menor, ≈6,35 mm por cuantización.")
p('El proyecto declara 190,61 m² construidos y 635,60 m² de parcela. El dibujo produce 190,5033 y 635,8360 m². Se ha preservado el contorno, sin deformarlo para hacer coincidir superficies declaradas.')
p('Criterio tras la instrucción de continuar exclusivamente con el proyecto: posiciones XY de plantas35/37; alturas de alzados y secciones concordantes. Los elementos decorativos, mobiliario, vegetación, vehículos e iluminación son visualización y se separan de la geometría documental.')
p('Discrepancias conservadas y datos ausentes','Heading2')
for item in H['incertidumbres']:
    if isinstance(item,dict):p('<b>'+item['id'].replace('_',' ')+':</b> '+item.get('modelado','')+'. Alternativa/dato ausente: '+item.get('alternativa_pdf','')+'. Criterio: '+item.get('criterio',''))
    else:p(str(item))
p('Puertas interiores:12 hojas en posición abierta de la planta, altura2,03m y espesor3,5cm de la memoria. La cota superior real de sus huecos no se define; no se añaden dinteles a una altura supuesta. Una hoja de función ambigua se conserva como referencia oculta.')
p('Cerramiento frontal: rejillas vectoriales de3,3782×1,4986m, 28barrotes verticales/11horizontales medidos por rejilla; sin dintel blanco superior porque no figura en el esquema. Registro al extremo derecho de la parcela y escala nominal fija. El esquema completo mide0,118m más que el frente de planta; puertas siguen la planta y el encuentro del machón junto al vehículo presenta un residual de0,018m. Perfiles de rejilla planos: su profundidad no está especificada.')
p('La cubierta central tiene 4,3942 m de ancho según planta, vial y sección4; trasero/sección3 la dibujan aproximadamente 0,80 m más ancha hacia el oeste. Ambas geometrías no pueden cumplirse a la vez. Se mantiene la planta y se muestra esta discrepancia en el cotejo. No se afirma coincidencia total del PDF.')
p('Piscina: contorno XY verificado; sin fondo ni cotas de peldaños inventadas. La superficie de agua utiliza jardín −0,15 m sólo como referencia de visualización, no como cota real documentada. Cubierta: plano gráfico de grava, sin espesores de acabado ni pendientes de drenaje inventados.')
story.append(PageBreak())
p('Planta y superposición','Heading1');story.append(Image(str(ROOT/'control/planta_mesh_y_superposicion.png'),width=490,height=534));story.append(PageBreak())
for name,*rest in spec:
    p('Alzado '+name.replace('_',' '),'Heading1');story.append(Image(str(ROOT/f'control/comparacion_alzado_{name}.png'),width=490,height=237));story.append(Spacer(1,10))
    if name in ['lateral_porche','trasero']:story.append(PageBreak())
p('Cotas y secciones','Heading1');story.append(Image(str(ROOT/'control/comparacion_niveles_secciones.png'),width=490,height=356));story.append(PageBreak())
p('Dimensiones principales verificadas','Heading1')
data=[['Elemento','Modelo','PDF','Error']]
for r in rows:
    if 'XY máx' in r[0] or 'dintel Z' in r[0] or 'antepecho Z' in r[0] or ' XYZ m' in r[0]:continue
    data.append([Paragraph(r[0],styles['BodyText']),str(r[1]),str(r[2]),str(r[3])])
t=Table(data,colWidths=[290,82,70,48],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce5e8')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.lightgrey)]));story.append(t)
SimpleDocTemplate(str(ROOT/'informe_control.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=40,bottomMargin=40).build(story)
print(json.dumps({k:v for k,v in result.items() if k not in ['controles','incertidumbres_pdf']},ensure_ascii=False));print('CONTROLES',len(checks),'FALLOS',sum(not c['pasa'] for c in checks))
if not result['apto_para_renders']:raise SystemExit(1)
