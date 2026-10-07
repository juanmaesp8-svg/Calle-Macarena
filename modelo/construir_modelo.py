"""Blender: reconstrucción reproducible del proyecto básico Calle Macarena.

Ejecutar: blender -b --factory-startup --python construir_modelo.py
XY conserva vectores del PDF. Las decisiones Z y los datos ausentes se registran.
No se emplean imágenes generadas para modificar la arquitectura.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

DIR=Path(__file__).resolve().parent
ROOT=DIR.parent
sys.path.insert(0,str(DIR))
from materiales import make_materials, setup_lighting
from vegetacion_v2 import make_palm, make_olive, make_shrub, make_turf_fibres
from vegetacion_mobiliario import make_sofa, make_bed, make_chair, make_table, make_sofa_l
from vehiculos import make_car

P=json.loads((DIR/'datos_planta.json').read_text())
H=json.loads((DIR/'datos_alturas.json').read_text())
S=json.loads((DIR/'superficies_mesh.json').read_text())
F=json.loads((DIR/'datos_mobiliario.json').read_text())
CAM=json.loads((DIR/'criterios_qa_camaras.json').read_text())

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name=='Collection':bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS';scene.unit_settings.scale_length=1.0
scene['proyecto']='Vivienda unifamiliar Calle Macarena nº16 — reconstrucción del PDF'
scene['fuente']='V2: XY planta final proyectoobra PDF1; Z vivienda original alzados38/secciones39; Z trastero confirmadas por usuario'
scene['revision']='V2_planta_final_trastero'
scene['sha256_planta_final']=P['fuente_sha256']
scene['criterio_discrepancias']=H['regla']
scene['incertidumbres']=json.dumps(H['incertidumbres'],ensure_ascii=False)
scene['sin_dimensiones_inventadas']='Vaso sin fondo ni contrahuellas. Agua/grava son superficies gráficas, no cotas de acabado verificadas.'
scene['estado']='MODELO DOCUMENTAL; control geométrico independiente disponible en control/control_resultado.json'
names=['Parcela','Vivienda','Trastero','Cubierta','Porches','Piscina','Pavimentos','Cerramiento_exterior','Carpinterias','Aparcamiento','Jardin','Mobiliario','Iluminacion','Camaras','Referencias_PDF']
C={}
for name in names:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);C[name]=c
M=make_materials()

def metadata(obj,role,source='',status='calculado del PDF'):
    obj['categoria']=role;obj['fuente']=source;obj['estado_dimension']=status
    return obj

def mesh_obj(name,vertices,faces,col,mat,role='arquitectura',source='',status='calculado del PDF'):
    me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(vertices,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);C[col].objects.link(ob)
    if mat:me.materials.append(mat)
    metadata(ob,role,source,status)
    return ob

def prism(name,xy,z0,z1,col,mat,role='muro',source='',bevel=0):
    # Tessellate exclusivamente polígonos simples; superficies con huecos vienen de GEOS.
    xy=[tuple(v) for v in xy]
    if xy[0]==xy[-1]:xy=xy[:-1]
    area=sum(xy[i][0]*xy[(i+1)%len(xy)][1]-xy[(i+1)%len(xy)][0]*xy[i][1] for i in range(len(xy)))
    if area<0:xy.reverse()
    n=len(xy);vs=[(x,y,z0) for x,y in xy]+[(x,y,z1) for x,y in xy]
    vectors=[Vector((x,y,z1)) for x,y in xy]
    faces=[]
    for tr in tessellate_polygon([vectors]):
        ids=list(tr) if isinstance(tr[0],int) else [vectors.index(v) for v in tr]
        faces.append(tuple(i+n for i in ids));faces.append(tuple(reversed(ids)))
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ob=mesh_obj(name,vs,faces,col,mat,role,source)
    if bevel>0:
        mod=ob.modifiers.new('Redondeo de acabado sin modificar extremos','BEVEL');mod.width=bevel;mod.segments=2
        mod.affect='EDGES'
        mod=ob.modifiers.new('Normales de acabado','WEIGHTED_NORMAL');mod.keep_sharp=True
    return ob

def box(name,b,z0,z1,col,mat,role='muro',source='',bevel=0):
    a,c,d,e=b
    return prism(name,[(a,c),(d,c),(d,e),(a,e)],z0,z1,col,mat,role,source,bevel)

def surface(name,parts,z,col,mat,role,zbottom=None,source='',status='calculado del PDF'):
    obs=[]
    for index,part in enumerate(parts):
        xy=part['vertices_xy'];n=len(xy)
        vertices=[(x,y,z) for x,y in xy];faces=[tuple(f) for f in part['caras']]
        if zbottom is not None:
            vertices += [(x,y,zbottom) for x,y in xy]
            faces += [tuple(reversed([v+n for v in f])) for f in part['caras']]
            for ring in part['anillos']:
                faces += [(ring[i],ring[i]+n,ring[(i+1)%len(ring)]+n,ring[(i+1)%len(ring)]) for i in range(len(ring))]
        ob=mesh_obj(name+(f'_{index+1:02d}' if len(parts)>1 else ''),vertices,faces,col,mat,role,source,status)
        ob['area_xy_m2']=part['area_m2'];obs.append(ob)
    return obs

def thin_line(name,a,b,z0,z1,width,col,mat,role,source=''):
    ax,ay=a;bx,by=b;dx,dy=bx-ax,by-ay;length=math.hypot(dx,dy)
    nx,ny=-dy/length*width/2,dx/length*width/2
    return prism(name,[(ax+nx,ay+ny),(ax-nx,ay-ny),(bx-nx,by-ny),(bx+nx,by+ny)],z0,z1,col,mat,role,source)

def camera(name,position,target,lens=35,shift=0,ortho=None):
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);C['Camaras'].objects.link(ob)
    ob.location=position;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens;data.sensor_width=36;data.shift_y=shift;data.clip_start=.04;data.clip_end=500
    if ortho is not None:data.type='ORTHO';data.ortho_scale=ortho
    metadata(ob,'camara','Composición fotográfica; misma geometría en todas las vistas','visualización')
    return ob

# Terreno no volumetrizado: no se define cimentación ni profundidad de parcela.
surface('Parcela_limite_documental',S['parcela'],-.151,'Parcela',M['cesped'],'parcela',source='PDF35 capaPARCELA')
# La base parcelaria sólo define un plano XY; no debe verse bajo el vaso desconocido.
for ob in C['Parcela'].objects:ob.hide_render=True
surface('Jardin_cesped',S['cesped'],-.15,'Jardin',M['cesped'],'jardin',source='Planta final PDF1, césped artificial usuario; continuidad bajo tumbonas deducida')
make_turf_fibres('Cesped_artificial_fibras_visual',S['cesped'],-.15,C['Jardin'],M,density=2000)
surface('Pavimento_exterior_contorno_PDF',S['pavimentos'],0,'Pavimentos',M['porcelanico_exterior'],'pavimento',zbottom=-.15,source='Bordes césped/solería PDF35/37; altura suelo referencia0')
surface('Suelo_vivienda',S['suelo_vivienda'],0,'Vivienda',M['suelo_interior'],'suelo_vivienda',source='Huella PDF35; datum0')

# Muros y particiones: cada polígono procede del relleno azul del plano.
for wall in P['muros']:
    col='Trastero' if wall['clasificacion']=='trastero' else 'Vivienda'
    role='muro_vivienda';ztop=3.35
    for i,xy in enumerate(wall['poligonos_xy_m']):
        ob=prism(wall['nombre']+f'_{i+1:02d}',xy,0,ztop,col,M['fachada_blanca'],role,f"Planta final PDF1 relleno {wall['seqno_pdf']}",bevel=.0015)
        ob['id_vector_pdf']=wall['seqno_pdf'];ob['seqno_pdf_v2']=wall['seqno_pdf'];ob['clasificacion_planta']=wall['clasificacion']
for wall in P['tendedero']:
    for i,xy in enumerate(wall['poligonos_xy_m']):
        prism(wall['nombre']+f'_{i+1:02d}',xy,-.15,1.65,'Cerramiento_exterior',M['muro_blanco'],'tendedero','PDF35; altura inferida por cerramiento lateral')

OPEN=[]
def opening(h):
    b=h['bbox_xy_m'];x0,y0,x1,y1=b;z0=h['z_antepecho_m'];z1=h['z_dintel_m'];name=h['nombre']
    if z0>0:box(name+'_antepecho',b,0,z0,'Vivienda',M['fachada_blanca'],'muro_vivienda',h['fuente_z'])
    box(name+'_dintel',b,z1,3.35,'Vivienda',M['fachada_blanca'],'muro_vivienda',h['fuente_z'])
    axis='Y' if x1-x0<y1-y0 else 'X'
    width=(y1-y0) if axis=='Y' else (x1-x0)
    exterior=h['normal_exterior_xy'];depth=x1-x0 if axis=='Y' else y1-y0
    # Carpinterías de planos: marco≈1,32pt=0,06985m, retirado hacia la cara interior.
    profile=.06985; thick=.0635
    if axis=='Y':
        u0,u1=y0,y1;v=x0+profile if exterior[0]>0 else x1-profile
    else:
        u0,u1=x0,x1;v=y0+profile if exterior[1]>0 else y1-profile
    def framebox(s,a,b,low,high,material=M['carpinteria_antracita'],t=thick):
        bb=[v-t/2,a,v+t/2,b] if axis=='Y' else [a,v-t/2,b,v+t/2]
        return box(name+s,bb,low,high,'Carpinterias',material,'carpinteria',h['fuente_z'],.002)
    framebox('_jamba1',u0,u0+profile,z0,z1)
    framebox('_jamba2',u1-profile,u1,z0,z1)
    framebox('_superior',u0+profile,u1-profile,z1-profile,z1)
    framebox('_inferior',u0+profile,u1-profile,z0,z0+profile)
    typ=h['tipo_documental_propuesto']
    if name.startswith('P_'):
        material=M['carpinteria_antracita']
        ob=framebox('_hoja',u0+profile,u1-profile,z0+profile,z1-profile,material,.05)
        ob['estado_dimension']='Anchura/hueco de PDF; espesor y despiece de hoja como acabado gráfico'
        # Puerta principal con horizontales presentes en alzado, no cambiar hueco.
        if 'principal' in name:
            for zz in [.52,1.04,1.56,2.08]:
                framebox('_junta_'+str(zz),u0+profile,u1-profile,zz,zz+.007,M['metal_pergola'],.052)
        if 'porton_trastero' not in name:
            handleu=u1-.14
            handle=framebox('_tirador',handleu,handleu+.027,1.03,1.28,M['metal_pergola'],.12)
            handle['estado_dimension']='Accesorio decorativo; no acotado'
    else:
        leaves=3 if typ in ['V6','V7'] else 2 if typ in ['V1','V5'] else 1
        for j in range(leaves):
            a=u0+profile+(width-2*profile)*j/leaves;b2=u0+profile+(width-2*profile)*(j+1)/leaves
            if j>0:framebox('_montante_'+str(j),a-.018,a+.018,z0+profile,z1-profile)
            bb=[v-.004,a+.017,v+.004,b2-.017] if axis=='Y' else [a+.017,v-.004,b2-.017,v+.004]
            glass=box(name+f'_vidrio_{j+1}',bb,z0+profile,z1-profile,'Carpinterias',M['vidrio'],'vidrio',h['fuente_z'])
            glass['estado_dimension']='Hueco de PDF; vidrio8mm como representación de material, no detalle constructivo'
    # Empty contiene referencias del hueco; nunca altera su posición o anchura.
    empty=bpy.data.objects.new(name+'_referencia',None);C['Referencias_PDF'].objects.link(empty)
    empty.location=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
    empty['bbox_hueco_xy_m']=b;empty['z_antepecho_m']=z0;empty['z_dintel_m']=z1
    empty['fuente_xy']=h['fuente'];empty['fuente_z']=h['fuente_z']
    if h.get('discrepancia'):empty['discrepancia']=h['discrepancia']
    OPEN.append({'nombre':name,'bbox_xy':b,'zmin':z0,'zmax':z1,'ancho':width,'alto':z1-z0,'fuente':h['fuente_z'],'discrepancia':h.get('discrepancia','')})
for h in H['huecos_exteriores']:opening(h)

# Forjado común, petos de paños diferentes, portal abierto y marquesina derivada.
surface('Forjado_cubierta_3_35_3_70',S['cubierta'],3.7,'Cubierta',M['fachada_blanca'],'forjado',zbottom=3.35,source='Planta37; cotas directas3.35/3.70')
surface('Cielorraso_vivienda_existente_3_20',S['suelo_vivienda_existente'],3.2,'Cubierta',M['fachada_blanca'],'cielorraso',source='Secciones1/3; Zcalculada3.20; excluye trastero nuevo, sin dato de cielorraso')
surface('Grava_superficie_referencia_NO_cota_acabado',S['cubierta'],3.702,'Cubierta',M['grava'],'grava_visual',source='Memoria: plana grava; acabadoZsinacotar',status='Plano de referencia de visualización; no cota de acabado real')
for pa in H['cubierta']['petos_tramos']:
    # El portal empieza en3.35; sus primeros35cm ya pertenecen al forjado.
    # Evitar doble cara exterior coplanar: el sólido superior empieza en3.70.
    # La envolvente del conjunto mantiene exactamente base3.35/coronación4.75.
    base_solido=max(pa['z_base_m'],3.7)
    ob=box(pa['nombre'],pa['bbox_xy_m'],base_solido,pa['z_coronacion_m'],'Cubierta',M['fachada_blanca'],'peto',pa['fuente'])
    ob['z_base_fuente']=pa['z_base_m'];ob['z_coronacion_fuente']=pa['z_coronacion_m']
    ob['division_solidos']='Porción3.35–3.70 del portal incluida en Forjado; sin duplicar caras inferiores.'
can=H['cubierta']['marquesina_terraza_derivada']
box('Marquesina_terraza_sin_pilares',can['bbox_xy_m'],3.35,3.55,'Porches',M['fachada_blanca'],'marquesina','Alzado lateral/vial y sección4; contorno omitido enplantas')

# Trastero: nueva puerta norte en el hueco real, abierta hacia el recinto.
di=H['puerta_interior_trastero'];b=di['bbox_xy_m']
box('P_interior_trastero_norte_dintel',b,di['alto_m'],3.35,'Trastero',M['fachada_blanca'],'muro_vivienda','Hueco XYplanta final; alto2.03confirmadousuario')
xhinge,ynorth=P['trastero']['puerta_norte']['hoja_referencia']['bisagra_xy_m']
thin_line('P_interior_trastero_norte_hoja',(xhinge,ynorth),(xhinge,ynorth-di['ancho_hoja_grafico_m']),0,di['alto_m'],.035,'Carpinterias',M['fachada_blanca'],'carpinteria','Hoja gráfica0.81915 enplanta final; alto2.03usuario; espesorDMF existente35mm')
OPEN.append({'nombre':di['nombre'],'bbox_xy':b,'zmin':0,'zmax':di['alto_m'],'ancho':b[2]-b[0],'alto':di['alto_m'],'fuente':di['fuente_z'],'tipo':'interior'})

# Madera: láminas de acabado en caras de paños existentes, conservando huecos.
for i,(ya,yb) in enumerate([(17.8181,18.16735),(22.3012,23.75535),(25.25395,28.067)]):
    # Superficie sin volumen añadido. El tercer paño está dentro de muro entre dormitorios.
    xx=10.64905
    ob=mesh_obj('Acabado_madera_vertical_'+str(i+1),[(xx,ya,0),(xx,yb,0),(xx,yb,2.5),(xx,ya,2.5)],[(0,1,2,3)],'Carpinterias',M['madera_clara_vertical'],'acabado_decorativo','Preferencia usuario; paños existentes','elección de acabado; no cambia dimensiones')

# Piscina: sólo perímetro y superficie gráfica; no se inventa fondo ni contrahuellas.
water=M['agua'];shader=water.node_tree.nodes.get('PBR')
if shader:
    shader.inputs['Transmission Weight'].default_value=0.0
    shader.inputs['Base Color'].default_value=(.035,.24,.27,1)
    shader.inputs['Roughness'].default_value=.045
surface('Piscina_agua_representacion_superficial',S['piscina'],-.15,'Piscina',water,'piscina',source='XYplanta; Zagua noacotada, plano gráficoreferencia jardín',status='Superficie de visualización; NO define fondo ni nivel de agua real')
water['nota']='Reflexión superficial PBR. Sin simulación de profundidad/volumen: el PDF no define vasoZ.'
# Mantener huellas escalera como geometría 2D editable oculta en renders.
for step in P['piscina']['escalera']:
    xy=step['poligono_xy_m'];ob=mesh_obj(step['nombre']+'_XY_sin_Z',[(x,y,0) for x,y in xy],[(0,1,2,3)],'Referencias_PDF',None,'escalera_piscina_referencia',step['fuente'],'Contrahuella yZdesconocidas; referencia2D')
    ob.hide_render=True;ob.hide_viewport=True;ob['contrahuella_m']='SIN_DATO';ob['profundidad_m']='SIN_DATO'

# Cerramiento: quiebros reales del lindero, alturas por vista, sin rediseñar parcela.
pts=P['parcela']['points_xy_m']
for wall in S['cerramiento_linderos']:
    i=wall['indice_lindero']
    top=1.65 if i==9 else 1.85
    obs=surface(f'Cerramiento_lindero_{i+1:02d}',wall['partes'],top,'Cerramiento_exterior',M['muro_blanco'],'cerramiento',zbottom=-.15,source='Cara exterior sobre lindero PDF35; espesor hacia dentro deducido del detalle de tendedero',status='Espesor0.1524m extrapolado explícitamente; no cota directa en todos los tramos')
    for ob in obs:
        ob['criterio_altura']='Lateralcalleprivada1.80; opuesto/trasero2.00; inferenciaexplícita'
        ob['criterio_espesor']='Exterior en lindero, interior0.1524m; relación del tendedero extrapolada; no invadir parcela ajena'

def front_y(x):return .003175+x*(1.025525-.003175)/18.61185
def gate_line(name,x0,x1,z0,z1,material,role,width=.1016):
    return thin_line(name,(x0,front_y(x0)+.127),(x1,front_y(x1)+.127),z0,z1,width,'Cerramiento_exterior',material,role,'XYacceso planta36 registrado; altura2m esquemaalzado')
# Huecos de portones no se trasladan a partir del panel completo del alzado.
ped=H['puerta_peatonal_parcela'];hinge=ped['bisagra_xy_m'];pedw=ped['longitud_modelada_hoja_m'];pedx1=hinge[0];pedx0=pedx1-pedw*math.cos(math.atan2(1.02235,18.61185))
gate_line('Panel_fijo_peatonal',.10,pedx0,-.15,1.85,M['carpinteria_antracita'],'panel_fijo')
# Hoja abierta según planta; no una puerta frontal ficticia.
thin_line('Puerta_peatonal_hoja_abierta',ped['hoja_xy_m'][0],ped['hoja_xy_m'][1],-.15,1.85,.0381,'Cerramiento_exterior',M['carpinteria_antracita'],'puerta_peatonal','Hoja0.820m enplanta36, frentealzado1.162m')
gate_line('Muro_jamba_peatonal_garaje',pedx1,4.06442,-.15,1.85,M['muro_blanco'],'cerramiento',.254)
# Hoja de portón: ejes registrados exactos de planta36; conservar solape en postes.
gate_pdf=P['referencias']['accesos']['vehicle_gate_plan03']['leaf_endpoints_pdf_pt']
gate_xy=[((u-205.64)*.05291666666666667,(770.32-v-1.68)*.05291666666666667) for u,v in gate_pdf]
thin_line('Porton_corredera',*gate_xy,-.15,1.85,.1016,'Cerramiento_exterior',M['carpinteria_antracita'],'porton_vehiculos','Eje exacto PDF36 registrado a35; espesor de representación')
for zz in [.23,.62,1.01,1.40]:thin_line('Porton_junta_'+str(zz),*gate_xy,zz,zz+.008,.104,'Cerramiento_exterior',M['metal_pergola'],'acabado_porton','Juntas de acabado; no modifican hoja')
# Rejillas/machones: coordenadas vectoriales del esquema, registro al lindero derecho.
G=json.loads((DIR/'datos_cerramiento_frontal.json').read_text())
T=G['registro']['tangente_xy'];N=G['registro']['normal_interior_xy']
def front_s(name,s0,s1,z0,z1,width=.254,mat=None,role='cerramiento'):
    points=[(T[0]*t+N[0]*.127,T[1]*t+N[1]*.127) for t in [s0,s1]]
    return thin_line(name,*points,z0,z1,width,'Cerramiento_exterior',mat or M['muro_blanco'],role,'Esquema PDF38 registrado, planta gobierna lindero y puertas')
s_jamba=10.074810373902848 # Cara del poste vehicular PDF36 proyectada en lindero real.
for pa in G['panos_muro_tramo_derecho']:
    lo,hi=pa['intervalo_s_m']
    if lo<10.1:lo=s_jamba
    # Partir machones sobre zócalo para no duplicar caras exteriores coincidentes.
    base=pa['z_inferior_m'] if 'Zocalo' in pa['nombre'] else .35165
    ob=front_s(pa['nombre'],lo,hi,base,pa['z_superior_m'])
    ob['registro_residual_jamba_m']=.017997349715315636
for rg in G['rejillas']:
    outer=rg['marco_exterior'];inner=rg['claro_interior']
    a,b=outer['intervalo_s_m'];c,d=inner['intervalo_s_m'];z0=outer['z_inferior_m'];ztop=outer['z_superior_m']
    # Marco plano documentado; profundidad normal desconocida, sin extrusión supuesta.
    def face(s0,s1,za,zb,name):
        vs=[(T[0]*t+N[0]*.127,T[1]*t+N[1]*.127,z) for t,z in [(s0,za),(s1,za),(s1,zb),(s0,zb)]]
        return mesh_obj(name,vs,[(0,1,2,3)],'Cerramiento_exterior',M['carpinteria_antracita'],'rejilla','EsquemaPDF38; cara frontal, espesor normal SIN_DATO','Plano de perfil documental, no sólido de ejecución')
    face(a,b,outer['z_inferior_m'],inner['z_inferior_m'],rg['nombre']+'_marco_inferior')
    face(a,b,inner['z_superior_m'],outer['z_superior_m'],rg['nombre']+'_marco_superior')
    face(a,c,inner['z_inferior_m'],inner['z_superior_m'],rg['nombre']+'_marco_izquierdo')
    face(d,b,inner['z_inferior_m'],inner['z_superior_m'],rg['nombre']+'_marco_derecho')
    for tipo in ['verticales','horizontales']:
        for j,bar in enumerate(rg['barrotes_'+tipo+'_planos']):
            mesh_obj(rg['nombre']+'_'+tipo+f'_{j+1:02d}',bar['vertices_xyz_m'],[(0,1,2,3)],'Cerramiento_exterior',M['carpinteria_antracita'],'rejilla','Ancho frontal/paso medido PDF38; profundidad SIN_DATO','Perfil plano documental')

# Mobiliario conserva posiciones y huellas de símbolos; alturas son assets decorativos.
def decor_box(name,b,z0,z1,mat,bevel=.012):
    ob=box(name,b,z0,z1,'Mobiliario',mat,'mobiliario','XYsímbolo PDF35; altura decorativa noacotada',bevel)
    ob['estado_dimension']='XYdelPDF; altura/espesor de visualización';return ob
def chair(item):
    name=item['nombre']
    yaw=math.pi/2 if '_izq_' in name or '_oeste' in name else -math.pi/2 if '_der_' in name or '_este' in name else math.pi if '_sur' in name else 0
    return make_chair(name,item['centro_xy_m'],item['tamano_bbox_xy_m'],0,C['Mobiliario'],M,yaw=yaw)
for item in F['objetos']:
    typ=item['tipo'];b=item['bbox_xy_m'];xy=item['centro_xy_m'];size=item['tamano_bbox_xy_m'];name=item['nombre']
    if typ=='cama_doble':
        obs=make_bed(name,xy,size,0,C['Mobiliario'],M)
        if '3' in name:obs[0].rotation_euler.z=math.pi
    elif typ.startswith('sofa_3') or typ in ['butaca','butaca_exterior','asiento_ottoman']:
        rotate=size[1]>size[0];ss=(size[1],size[0]) if rotate else size
        obs=make_sofa(name,xy,ss,0,C['Mobiliario'],M)
        if rotate:obs[0].rotation_euler.z=math.pi/2
    elif typ=='sofa_L':
        make_sofa_l(name,item['huella_xy_m'],0,C['Mobiliario'],M)
    elif typ.startswith('mesa_comedor'):
        make_table(name,xy,size,0,C['Mobiliario'],M)
    elif typ=='silla_comedor':chair(item)
    elif typ in ['mesa_baja','mesa_baja_exterior']:
        make_table(name,xy,size,0,C['Mobiliario'],M,height=.385,coffee=True)
    elif typ in ['encimera_lineal','isla']:
        decor_box(name+'_mueble',b,0,.87,M['fachada_blanca'],.015)
        decor_box(name+'_encimera',b,.87,.91,M['porcelanico_exterior'],.007)
        for j in range(1,max(2,int(size[1]/.6))):
            yy=b[1]+size[1]*j/max(2,int(size[1]/.6));decor_box(name+'_junta'+str(j),[b[2]-.003,yy-.002,b[2]+.001,yy+.002],.13,.83,M['carpinteria_antracita'],0)
    elif typ=='taburete':
        decor_box(name+'_asiento',b,.64,.69,M['madera_clara_vertical'],.02)
        decor_box(name+'_base',[xy[0]-.014,xy[1]-.014,xy[0]+.014,xy[1]+.014],0,.64,M['carpinteria_antracita'])

for i,xy in enumerate(P['referencias']['aparcamiento']['car_symbol_centers_xy_m']):
    make_car(f'Vehiculo_{i+1:02d}_posicion_plano',xy,(2.084,4.934),C['Aparcamiento'],M,0)

# Vegetación secundaria; raíces sólo en patches de césped y lejos de huecos.
for name,xy,height,kind in [
    ('Olivo_trasero_derecho',(14.72,36.02),4.15,'olive'),
    ('Olivo_trasero_izquierdo',(4.8,36.02),3.7,'olive'),
    ('Palmera_frente',(17.15,2.9),4.9,'palm'),
    ('Palmera_jardin_lateral',(15.22,23.2),4.25,'palm'),
]:
    (make_palm if kind=='palm' else make_olive)(name,xy,height,C['Jardin'],M)
for i,(x,y) in enumerate([(11.0,2.8),(11.0,4.15),(17.5,6.0),(17.6,7.35),(17.7,8.7),(17.4,10.5),(16.6,14.2),(16.4,16),(16.2,18.2),(16.1,20.2),(15.8,25),(15.9,27),(15.9,29),(15.85,31),(15.2,35.9),(12.8,36.6),(10.8,36.6),(8.8,36.6),(6.8,36.6),(5.7,36.6)]):
    make_shrub(f'Plantacion_perimetral_{i+1:02d}',(x,y),.29 if i<12 else .26,C['Jardin'],M)

# Entorno sin lindes vecinos inventados: plano neutro; calzada sólo como fondo gráfico.
ground=mesh_obj('Entorno_neutro_sin_geometria_vecinal',[(-120,-120,-.155),(120,-120,-.155),(120,140,-.155),(-120,140,-.155)],[(0,1,2,3)],'Parcela',M['porcelanico_exterior'],'entorno_visual','Anchuras de calles/vecinos no definidas','Fondo de visualización; no parcela/calle acotada')
roadmat=bpy.data.materials.new('Contexto_vial_asfalto');roadmat.use_nodes=True
sh=roadmat.node_tree.nodes.get('Principled BSDF');sh.inputs['Base Color'].default_value=(.12,.125,.13,1);sh.inputs['Roughness'].default_value=.9
mesh_obj('Vial_publico_contexto_sin_anchura',[(-120,-120,-.154),(120,-120,-.154),(120,0,-.154),(-120,0,-.154)],[(0,1,2,3)],'Parcela',roadmat,'entorno_visual','Relaciónvialfrontal delPDF; borde lejano no definido','Contexto gráfico, no ancho de calle')
mesh_obj('Calle_privada_contexto_sin_anchura',[(-120,0,-.154),(0,0,-.154),(0,120,-.154),(-120,120,-.154)],[(0,1,2,3)],'Parcela',roadmat,'entorno_visual','Relacióncalleprivadalateral delPDF; borde lejano no definido','Contexto gráfico, no ancho de calle')

# Luces son accesorios decorativos; no alteran geometría ni huecos.
def area_light(name,location,power,size=1.0):
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.color=(1,.72,.46);ld.shape='DISK';ld.size=size
    ob=bpy.data.objects.new(name,ld);C['Iluminacion'].objects.link(ob);ob.location=location
    metadata(ob,'luz_decorativa','Visualización interior/exterior','acabado noacotado')
    return ob
for i,xy in enumerate([(8.8,14.6),(8.6,19.6),(8.6,24.5),(8.6,29.2),(10.8,32.7)]):area_light('Luz_interior_'+str(i),(*xy,3.12),65 if i<2 else 35,1.1)
for i,(x,y) in enumerate([(10.69,18.00),(10.69,23.1),(10.69,26.5),(3.00,17.6),(5.8,8.2),(13.14,31.0)]):
    box('Aplique_'+str(i),[x-.045,y-.045,x+.045,y+.045],2.72,2.82,'Iluminacion',M['carpinteria_antracita'],'luz_decorativa','Solicitudrenderatardecer; accesorio noacotado',.005)
    area_light('Luz_exterior_'+str(i),(x,y,2.70),18,.18)

for ca in CAM['camaras_renders']:
    ob=camera(ca['id']+'_'+ca['nombre'],ca['posicion_m'],ca['objetivo_m'],ca['focal_mm'],ca.get('shift_y',0))
    ob['id_render']=ca['id'];ob['modo_luz']=ca.get('iluminacion','day')
for ca in CAM['camaras_analiticas']:
    ob=camera(ca['id']+'_'+ca['nombre'],ca['posicion_m'],ca['objetivo_m'],ortho=ca['ortho_scale_m'])
    ob['resolucion_px']=ca['resolucion_px'];ob['analitica']=True
setup_lighting(scene,'day')
scene.cycles.use_denoising=False # Este build de Blender carece OIDN; se usa OIDNoficial externo.
scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=5
scene.render.use_persistent_data=True;scene.cycles.samples=384;scene.cycles.adaptive_threshold=.008
scene.cycles.adaptive_min_samples=12
scene.view_layers[0].cycles.denoising_store_passes=True
scene.render.resolution_x=2500;scene.render.resolution_y=1667;scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.camera=bpy.data.objects.get('01_Aerea_oblicua_parcela')
scene.world.color=(.5,.5,.5)
scene['denoise']='OpenImageDenoise oficial independiente; beauty/albedo/normal lineales'

# Exportar mediciones desde los meshes reales, no desde las dimensiones esperadas.
from anadir_puertas_interiores import anadir_puertas_interiores
anadir_puertas_interiores()
# Revisión visual V3: mismos sólidos arquitectónicos y distribución documental.
# Los tres módulos actúan sobre acabados, assets decorativos y cámaras.
from interiores_v3 import aplicar_interiores
from exteriores_v3 import aplicar_exteriores
from camaras_v3 import aplicar_camaras
from vehiculos_reales_v3 import aplicar_vehiculos
aplicar_interiores(scene)
aplicar_exteriores(scene)
aplicar_vehiculos(scene)
aplicar_camaras(scene)
# glTF conserva también grifos, costuras y luminarias al convertir sus curvas.
# Los sólidos arquitectónicos ya son mallas y no entran en esta operación.
curves=[ob for ob in scene.objects if ob.type=='CURVE']
if curves:
    bpy.ops.object.select_all(action='DESELECT')
    for ob in curves:ob.select_set(True)
    bpy.context.view_layer.objects.active=curves[0]
    bpy.ops.object.convert(target='MESH')
scene['curvas_decorativas_convertidas_para_glb']=len(curves)
scene['revision_visual']='V3_interiores_exteriores'
scene.camera=bpy.data.objects.get('I01_Salon')
scene.view_settings.exposure=scene.camera['exposicion_ev']
scene['alcance_v3']='Salón, cocina, comedor; terraza, piscina y aparcamiento descubierto.'
actual=[]
architectural={'parcela','muro_vivienda','tendedero','pilar_pergola','forjado','peto','marquesina','viga_pergola','pavimento','jardin','piscina','suelo_vivienda','cielorraso','carpinteria','vidrio','cerramiento','puerta_peatonal','porton_vehiculos','rejilla'}
for ob in scene.objects:
    if ob.type=='MESH' and ob.get('categoria') in architectural:
        vs=[list(ob.matrix_world@v.co) for v in ob.data.vertices]
        actual.append({'nombre':ob.name,'categoria':ob['categoria'],'fuente':ob.get('fuente',''),'seqno_pdf_v2':ob.get('seqno_pdf_v2'),'vertices':vs,'caras':[list(p.vertices) for p in ob.data.polygons],'bbox_xyz':[min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)]})
(ROOT/'control/mediciones_mesh_real.json').write_text(json.dumps({'version':2,'revision':'V2','fuente_sha256':P['fuente_sha256'],'decisiones_modelado':P['ajustes_nominales'],'unidades':'m','objetos':actual,'huecos':OPEN,'estado':'Meshes generados; cifras extraídas de vértices Blender'},ensure_ascii=False))
for filename in ['datos_planta.json','datos_alturas.json','datos_mobiliario.json','criterios_qa_camaras.json','datos_cerramiento_frontal.json','confirmaciones_usuario_v2.json']:
    txt=bpy.data.texts.new(filename);txt.write((DIR/filename).read_text())
txt=bpy.data.texts.new('LEEME_MODELO.txt');txt.write('REVISION V2: planta final PROY.OBRA. Metros 1:1. Arquitectura, parcela y huecos extraídos del PDF final, alturas existentes del proyecto básico.\nTrastero cerrado sustituye instalaciones y pérgola/comedor piscina. Interior7.15×3.94; hueco norte0.96; piscina3.50×5.00. Ajustes locales de cuantización documentados.\nZ trastero confirmadas por usuario: forjado3.35/3.70,peto4.40,puerta2.03,porton2.50.\nPorcelánico exterior crema90×90cm; césped artificial; madera clara vertical sobre paños existentes.\nVaso sin fondo y peldaños sólo referencia XY: no hay alturas en fuente. Agua/grava planos gráficos, no cotas de ejecución.\nVentanalV7 alto2.50 y despacho1.60 conforme alzados originales; discrepancias con memoria registradas.\nPañoalto XYcubierta37; trasero/sec3 ancho0.80mayor incompatible, registrado.\nMobiliario,vegetación,luces,entorno son visualización. HDRI empaquetado. Microfibras completas enblend; GLB conserva superficie césped sin microfibras y usa coloresbase.\nRenders exclusivamente de este modelo. Cotejo: control/informe_revision_v2.pdf.\n')
scene['objetos_modelados']=len(scene.objects)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Calle_Macarena_modelo_1a1.blend'),compress=True)
# glTF limita materiales procedurales a colores base; el .blend preserva shaders completos.
for ob in scene.objects:ob.select_set(ob.type=='MESH' and not ob.hide_render and ob.get('categoria') not in {'entorno_visual','jardin_microgeometria_material'})
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Calle_Macarena_modelo_1a1.glb'),export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
print('MODELO_GUARDADO',ROOT/'Calle_Macarena_modelo_1a1.blend',flush=True)
print('OBJETOS',len(scene.objects),'HUECOS',len(OPEN),flush=True)
