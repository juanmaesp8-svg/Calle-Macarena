"""Detalles interiores reproducibles, sin cambios de arquitectura.

API: aplicar_interiores(bpy.context.scene). Se ejecuta sobre el modelo final V2.
Las huellas de cocina, mesas y sofá proceden del PDF; los accesorios, alturas de
muebles y luminarias son elecciones de visualización, nunca cotas de proyecto.
"""
from pathlib import Path
import bpy
import json
import math
import hashlib
import struct
import sys
from mathutils import Vector

DIR=Path(__file__).resolve().parent
ROOT=DIR.parent
NOTE='Detalle decorativo V3; no es dimensión arquitectónica ni prescripción del PDF'
C=None
M={}
CREATED=[]


def _tag(ob,source=NOTE):
    ob['categoria']='mobiliario_detalle_visual'
    ob['fuente']=source
    ob['estado_dimension']='Elección de visualización; ubicación mayor según símbolo PDF'
    ob['revision_visual']='V3_interiores'
    CREATED.append(ob)
    return ob


def _mesh(name,verts,faces,mat,smooth=False):
    me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);C.objects.link(ob)
    if mat:me.materials.append(mat)
    if smooth:
        for p in me.polygons:p.use_smooth=True
    return _tag(ob)


def _box(name,b,z0,z1,mat,bevel=.002):
    x0,y0,x1,y1=b
    vs=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
        (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    ob=_mesh(name,vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    if bevel:
        m=ob.modifiers.new('Cantos físicos de acabado','BEVEL');m.width=bevel;m.segments=3
        if name.startswith('sofa_L_salon_V3_'):
            # La misma malla/huella, con normales continuas sobre los cantos tapizados.
            # Los polígonos planos anulaban el suavizado del modificador de normales.
            for polygon in ob.data.polygons:polygon.use_smooth=True
            m.harden_normals=True
        m=ob.modifiers.new('Normales de acabado','WEIGHTED_NORMAL');m.keep_sharp=True
    return ob


def _rod(name,a,b,r0,r1,mat,segments=24):
    a,b=Vector(a),Vector(b);v=(b-a).normalized()
    u=v.cross(Vector((0,0,1)))
    if u.length<.01:u=v.cross(Vector((0,1,0)))
    u.normalize();w=v.cross(u).normalized()
    vs=[]
    for p,r in [(a,r0),(b,r1)]:
        for i in range(segments):
            t=2*math.pi*i/segments;vs.append(tuple(p+r*(math.cos(t)*u+math.sin(t)*w)))
    fs=[tuple(reversed(range(segments))),tuple(range(segments,2*segments))]
    fs += [(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
    return _mesh(name,vs,fs,mat,True)


def _tube(name,points,r,mat):
    cu=bpy.data.curves.new(name+'_curva','CURVE');cu.dimensions='3D';cu.resolution_u=2
    cu.bevel_depth=r;cu.bevel_resolution=3;cu.resolution_u=3
    s=cu.splines.new('POLY');s.points.add(len(points)-1)
    for p,q in zip(s.points,points):p.co=(*q,1)
    ob=bpy.data.objects.new(name,cu);C.objects.link(ob);cu.materials.append(mat)
    return _tag(ob)


def _lathe(name,center,profile,mat,segments=64):
    x,y,z=center;vs=[];fs=[]
    for r,h in profile:
        for i in range(segments):
            t=2*math.pi*i/segments;vs.append((x+r*math.cos(t),y+r*math.sin(t),z+h))
    for j in range(len(profile)-1):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments
            fs.append((a,b,b+segments,a+segments))
    return _mesh(name,vs,fs,mat,True)


def _ring(name,center,rx,ry,mat,r=.00065):
    x,y,z=center
    return _tube(name,[(x+rx*math.cos(2*math.pi*i/96),y+ry*math.sin(2*math.pi*i/96),z) for i in range(97)],r,mat)


def _material(name,color,rough=.45,metal=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');sh=n.new('ShaderNodeBsdfPrincipled');sh.name='PBR'
    sh.inputs['Base Color'].default_value=(*color,1)
    sh.inputs['Roughness'].default_value=rough;sh.inputs['Metallic'].default_value=metal
    l.new(sh.outputs['BSDF'],out.inputs['Surface']);m.diffuse_color=(*color,1)
    return m,sh


def _materials():
    mats={}
    mats['laca'],_= _material('V3 Interior · laca blanca cálida',(.72,.69,.63),.29)
    mats['sombra'],_= _material('V3 Interior · juntas y zócalo',(.018,.019,.021),.43)
    mats['acero'],sh= _material('V3 Interior · inox cepillado',(.54,.56,.58),.25,1)
    (sh.inputs.get('Anisotropic') or sh.inputs.get('Anisotropic IOR Level')).default_value=.35
    mats['vidrio_placa'],sh= _material('V3 Interior · vitrocerámica negra',(.005,.008,.01),.07)
    sh.inputs['IOR'].default_value=1.48
    mats['zonas'],_= _material('V3 Interior · serigrafía de inducción',(.19,.2,.2),.3)
    mats['ceramica'],sh= _material('V3 Interior · cerámica crema esmaltada',(.64,.6,.52),.17)
    sh.inputs['Coat Weight'].default_value=.22;sh.inputs['Coat Roughness'].default_value=.14
    mats['porcelana'],_= _material('V3 Interior · porcelana blanca',(.77,.755,.716),.16)
    mats['libro'],_= _material('V3 Interior · cubierta de libro lino',(.23,.19,.145),.76)
    mats['papel'],_= _material('V3 Interior · papel natural',(.62,.6,.54),.87)
    mats['tv'],_= _material('V3 Interior · pantalla apagada',(.009,.013,.018),.115)
    mats['oro'],_= _material('V3 Interior · latón oscuro satinado',(.34,.23,.095),.3,.82)
    mats['vidrio'],sh= _material('V3 Interior · cristal incoloro',(.96,.98,.99),.025)
    sh.inputs['Transmission Weight'].default_value=1;sh.inputs['IOR'].default_value=1.46
    # Wood's long grain follows Y on horizontal boards; fine fibers and diffuse
    # reflectance remain subtle instead of thick sculpted procedural ridges.
    mats['roble'],sh= _material('V3 Interior · roble natural tablero',(.36,.25,.135),.35)
    n=mats['roble'].node_tree.nodes;l=mats['roble'].node_tree.links
    pos=n.new('ShaderNodeNewGeometry');sc=n.new('ShaderNodeVectorMath');sc.operation='MULTIPLY';sc.inputs[1].default_value=(34,.58,34)
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.2;noise.inputs['Detail'].default_value=3.5;noise.inputs['Roughness'].default_value=.68
    l.new(pos.outputs['Position'],sc.inputs[0]);l.new(sc.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.19;ramp.color_ramp.elements[0].color=(.245,.165,.081,1)
    ramp.color_ramp.elements[1].position=.84;ramp.color_ramp.elements[1].color=(.49,.36,.205,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],sh.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.00012
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],sh.inputs['Normal'])
    mats['cuarzo'],sh= _material('V3 Interior · cuarzo crema compacto',(.66,.625,.55),.23)
    n=mats['cuarzo'].node_tree.nodes;l=mats['cuarzo'].node_tree.links
    pos=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1700;noise.inputs['Detail'].default_value=2
    l.new(pos.outputs['Position'],noise.inputs['Vector']);r=n.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].color=(.58,.552,.497,1);r.color_ramp.elements[1].color=(.73,.691,.611,1)
    l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],sh.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.00007
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],sh.inputs['Normal'])
    # Sheen + intersecting metric threads, not plastic smooth upholstered blocks.
    for key,name,c in [
        ('lino','V3 Interior · lino avena',(.49,.446,.376)),
        ('cojin','V3 Interior · lino tostado',(.225,.166,.11)),
        ('manta','V3 Interior · algodón crudo',(.57,.535,.468))]:
        mats[key],sh=_material(name,c,.86)
        sh.inputs['Sheen Weight'].default_value=.34;sh.inputs['Sheen Roughness'].default_value=.62
        n=mats[key].node_tree.nodes;l=mats[key].node_tree.links
        pos=n.new('ShaderNodeTexCoord');mult=n.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=(1,1,1)
        l.new(pos.outputs['Object'],mult.inputs[0])
        waves=[]
        for direction in ['X','Y']:
            w=n.new('ShaderNodeTexWave');w.wave_type='BANDS';w.bands_direction=direction;w.inputs['Scale'].default_value=1350;w.inputs['Distortion'].default_value=.15
            l.new(mult.outputs[0],w.inputs['Vector']);waves.append(w)
        mix=n.new('ShaderNodeMath');mix.operation='MULTIPLY';l.new(waves[0].outputs['Color'],mix.inputs[0]);l.new(waves[1].outputs['Color'],mix.inputs[1])
        b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.23;b.inputs['Distance'].default_value=.0002
        l.new(mix.outputs[0],b.inputs['Height']);l.new(b.outputs[0],sh.inputs['Normal'])
    mats['roble_patas']=mats['roble'].copy();mats['roble_patas'].name='V3 Interior · roble natural vertical'
    mats['pantalla'],sh=_material('V3 Interior · difusor cálido opal',(.74,.685,.57),.6)
    sh.inputs['Transmission Weight'].default_value=.16;sh.inputs['Emission Color'].default_value=(1,.84,.63,1);sh.inputs['Emission Strength'].default_value=.15
    return mats


def _fingerprint(scene):
    roles={'parcela','muro_vivienda','tendedero','forjado','peto','marquesina','pavimento','jardin','piscina','suelo_vivienda','cielorraso','carpinteria','vidrio','cerramiento','puerta_peatonal','porton_vehiculos','rejilla'}
    h=hashlib.sha256();count=0
    for ob in sorted(scene.objects,key=lambda o:o.name):
        if ob.type=='MESH' and ob.get('categoria') in roles:
            h.update(ob.name.encode());h.update(str(ob['categoria']).encode())
            for v in ob.data.vertices:h.update(struct.pack('<ddd',*(ob.matrix_world@v.co)))
            for f in ob.data.polygons:h.update(struct.pack('<I',len(f.vertices)));h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
            count+=1
    return h.hexdigest(),count


def _remove(prefix):
    obs=[o for o in list(bpy.data.objects) if o.name==prefix or o.name.startswith(prefix+'_') or o.name.startswith(prefix+' ·')]
    for ob in obs:
        if ob.get('categoria') not in {None,'mobiliario','mobiliario_detalle_visual'}:
            raise RuntimeError('Se intentó retirar arquitectura: '+ob.name)
    for ob in obs:bpy.data.objects.remove(ob,do_unlink=True)


def _pdf_bbox(f,q):
    s=f['factor_m_por_pt'];a,b=f['origen_pdf_pt'];return [(q[0]-a)*s,(b-q[3])*s,(q[2]-a)*s,(b-q[1])*s]


def _rounded_rect(x0,y0,x1,y1,r,z,n=12):
    pts=[]
    for x,y,start in [(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)]:
        for j in range(n):
            t=math.radians(start+90*j/n);pts.append((x+r*math.cos(t),y+r*math.sin(t),z))
    return pts


def _bowl(name,b):
    x0,y0,x1,y1=b;vs=[]
    # Closed stainless basin: .17 m depth is solely a fixture asset choice.
    rings=[(0,.914,.018),(.009,.899,.023),(.023,.757,.043),(.051,.744,.04)]
    for inset,z,r in rings:vs.extend(_rounded_rect(x0+inset,y0+inset,x1-inset,y1-inset,r,z))
    n=len(vs)//len(rings);fs=[]
    for j in range(len(rings)-1):
        fs += [(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for i in range(n)]
    fs.append(tuple((len(rings)-1)*n+i for i in range(n)))
    ob=_mesh(name,vs,fs,M['acero'],True)
    so=ob.modifiers.new('Chapa de cubeta 1mm','SOLIDIFY');so.thickness=.001
    cx=(x0+x1)/2;cy=(y0+y1)/2
    _lathe(name+'_desague',(cx,cy,.7448),[(.016,0),(.018,.001),(.018,.002),(.010,.002),(.010,.003)],M['acero'])
    _rod(name+'_fondo_desague',(cx,cy,.745),(cx,cy,.746),.010,.010,M['sombra'])


def _kitchen(f,by):
    linear=by['encimera_cocina']['bbox_xy_m'];island=by['isla_cocina']['bbox_xy_m']
    hob=_pdf_bbox(f,f['referencias_placa_bbox_pdf_pt']);sink=_pdf_bbox(f,f['referencias_fregadero_bbox_pdf_pt'])
    for p in ['encimera_cocina','isla_cocina']:_remove(p)
    x0,y0,x1,y1=linear
    _box('encimera_cocina_V3_zocalo',[x0+.045,y0+.035,x1-.08,y1-.035],0,.095,M['sombra'])
    _box('encimera_cocina_V3_caja_posterior',[x0,y0,x0+.018,y1],.095,.87,M['laca'])
    for y in [y0,y1-.018]:_box('encimera_cocina_V3_costado',[x0,y,x1,y+.018],.095,.87,M['laca'])
    _box('encimera_cocina_V3_base',[x0,y0,x1-.02,y1],.095,.113,M['laca'])
    hoby=(hob[1]+hob[3])/2;modules=6;module=(y1-y0)/modules
    oven_index=int((hoby-y0)/module)
    for i in range(modules):
        a=y0+i*module+.0015;b=y0+(i+1)*module-.0015
        if i==oven_index:
            _box('encimera_cocina_V3_horno_carcasa',[x1-.022,a,x1,b],.11,.83,M['sombra'],.004)
            _box('encimera_cocina_V3_horno_inox',[x1-.020,a+.025,x1+.0001,b-.025],.23,.69,M['acero'],.008)
            _box('encimera_cocina_V3_horno_cristal',[x1-.012,a+.062,x1+.0002,b-.062],.274,.630,M['vidrio_placa'],.012)
            _rod('encimera_cocina_V3_horno_tirador',(x1+.016,a+.045,.715),(x1+.016,b-.045,.715),.009,.009,M['acero'])
            for t in [.3,.7]:_rod('encimera_cocina_V3_mando_horno',(x1-.001,a+(b-a)*t,.775),(x1+.010,a+(b-a)*t,.775),.014,.014,M['acero'])
        else:
            for j,(za,zb) in enumerate([(.11,.475),(.478,.843)]):
                _box('encimera_cocina_V3_frente_%s_%s'%(i,j),[x1-.020,a,x1,b],za,zb,M['laca'],.002)
                _box('encimera_cocina_V3_uñero_%s_%s'%(i,j),[x1-.001,a+.035,x1+.0002,b-.035],zb-.009,zb-.006,M['sombra'],.001)
    counter=_box('encimera_cocina_V3_encimera',linear,.87,.91,M['cuarzo'],0)
    sx0,sy0,sx1,sy1=sink;mid=(sy0+sy1)/2
    # Two open bowls matching the two rectangular sinks drawn in the plan.
    bowl_boxes=[[sx0+.014,sy0+.015,sx1-.014,mid-.016],[sx0+.014,mid+.016,sx1-.014,sy1-.015]]
    for i,b in enumerate(bowl_boxes):
        cutter=_box('V3_Corte_temporal_cubeta',b,.86,.93,None,0)
        mod=counter.modifiers.new('Abertura real cubeta '+str(i+1),'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        bpy.context.view_layer.objects.active=counter;bpy.ops.object.modifier_apply(modifier=mod.name)
        CREATED.remove(cutter)
        bpy.data.objects.remove(cutter,do_unlink=True)
        _bowl('Fregadero_doble_V3_cubeta_'+str(i+1),b)
    be=counter.modifiers.new('Canto de cuarzo 2mm','BEVEL');be.width=.002;be.segments=3
    no=counter.modifiers.new('Normales encimera','WEIGHTED_NORMAL');no.keep_sharp=True
    # Faucet sits on the residual rear strip, never outside the cabinet footprint.
    gx=sx0-.056;gy=mid
    _rod('Grifo_V3_base',(gx,gy,.91),(gx,gy,.932),.027,.025,M['acero'])
    pts=[(gx,gy,.93),(gx,gy,1.12)]
    for i in range(25):
        t=math.pi*(1-i/24);pts.append((gx+.080+.080*math.cos(t),gy,1.12+.080*math.sin(t)))
    pts.append((gx+.16,gy,1.096))
    _tube('Grifo_V3_caño_monobloc',pts,.0115,M['acero'])
    _rod('Grifo_V3_mando',(gx,gy+.015,1.007),(gx,gy+.083,1.026),.006,.005,M['acero'])
    _rod('Grifo_V3_aireador',(gx+.16,gy,1.096),(gx+.16,gy,1.088),.012,.011,M['acero'])
    _box('Placa_V3_vidrio_induccion',hob,.91,.917,M['vidrio_placa'],.004)
    hx=(hob[0]+hob[2])/2;hy=(hob[1]+hob[3])/2
    zones=[(hx,hy+.16,.135),(hx-.099,hy-.092,.083),(hx+.099,hy-.092,.083)]
    for i,(x,y,r) in enumerate(zones):
        _ring('Placa_V3_zona_'+str(i),(x,y,.9173),r,r,M['zonas'],.00055)
        _ring('Placa_V3_zona_int_'+str(i),(x,y,.9173),r-.009,r-.009,M['zonas'],.00025)
    for i in range(3):
        _ring('Placa_V3_control_tactil_'+str(i),(hx+(i-1)*.063,hob[1]+.035,.9173),.010,.010,M['zonas'],.0006)
    # Island exact external XY outline, with recessed plinth and thinner doors.
    x0,y0,x1,y1=island
    _box('isla_cocina_V3_zocalo',[x0+.074,y0+.055,x1-.074,y1-.055],0,.095,M['sombra'])
    _box('isla_cocina_V3_caja',[x0+.018,y0+.018,x1-.018,y1-.018],.095,.87,M['laca'])
    for y in [y0,y1-.018]:_box('isla_cocina_V3_costado_roble',[x0,y,x1,y+.018],.095,.87,M['roble_patas'],.003)
    for side in ['oeste','este']:
        a=x0 if side=='oeste' else x1-.018
        for i in range(3):
            ya=y0+(y1-y0)*i/3+.0015;yb=y0+(y1-y0)*(i+1)/3-.0015
            _box('isla_cocina_V3_frente_'+side+'_'+str(i),[a,ya,a+.018,yb],.099,.849,M['roble_patas'],.002)
    _box('isla_cocina_V3_encimera',island,.87,.91,M['cuarzo'],.004)
    return {'encimera_lineal_bbox_xy_m':linear,'isla_bbox_xy_m':island,'placa_bbox_xy_m':hob,'fregadero_bbox_xy_m':sink,'fregadero_asset_profundidad_m':.17,'encimera_z_m':[.87,.91],'frentes_modulos':'Partición decorativa en seis frentes; no cotas arquitectónicas','horno':'Asset contenido bajo placa; la documentación no prescribe modelo de electrodoméstico'}


def _rebuild_chairs(by):
    from vegetacion_mobiliario import make_chair
    rec=[]
    maps={'madera_mesa':M['roble'],'madera_patas':M['roble_patas'],'tejido_tapizado':M['lino'],'metal_mobiliario':M['sombra']}
    for name,item in by.items():
        if not name.startswith('silla_interior'):continue
        b=item['bbox_xy_m'];x0,y0,x1,y1=b;depth=.52
        if '_izq_' in name:nb=[x0,y0,x0+depth,y1];yaw=math.pi/2;outer=x0;axis='Xmin'
        elif '_der_' in name:nb=[x1-depth,y0,x1,y1];yaw=-math.pi/2;outer=x1;axis='Xmax'
        elif '_norte' in name:nb=[x0,y1-depth,x1,y1];yaw=0;outer=y1;axis='Ymax'
        else:nb=[x0,y0,x1,y0+depth];yaw=math.pi;outer=y0;axis='Ymin'
        _remove(name)
        objects=make_chair(name,((nb[0]+nb[2])/2,(nb[1]+nb[3])/2),(nb[2]-nb[0],nb[3]-nb[1]),0,C,maps,yaw)
        for ob in objects:_tag(ob)
        objects[0]['bbox_simbolo_visible_pdf']=b;objects[0]['extension_oculta_bajo_tablero']=True
        objects[0]['borde_exterior_conservado']=json.dumps([axis,outer])
        rec.append({'nombre':name,'bbox_simbolo_visible_xy_m':b,'bbox_silla_completa_xy_m':nb,'borde_exterior':[axis,outer],'fondo_asset_visual_m':depth,'criterio':'Parte visible del símbolo conservada; prolongación exclusivamente bajo tablero para evitar comprimir una silla entera a 25cm de fondo'})
    return rec


def _barstools(by):
    from vegetacion_mobiliario import _upholstered
    rec=[]
    for name,item in by.items():
        if not name.startswith('taburete_isla'):continue
        _remove(name);b=item['bbox_xy_m'];x0,y0,x1,y1=b
        nb=[x0,y0,x0+.44,y1];cx=(nb[0]+nb[2])/2;cy=(y0+y1)/2;dy=y1-y0
        parent=bpy.data.objects.new(name,None);C.objects.link(parent);parent.location=(cx,cy,0);_tag(parent)
        # Stools face the island (east). External edge and row axes stay fixed.
        for sx in (-1,1):
            for sy in (-1,1):
                _rod(name+'_pata',(cx+sx*.175,cy+sy*dy*.38,0),(cx+sx*.145,cy+sy*dy*.31,.635),.012,.018,M['roble_patas'])
        _rod(name+'_reposapies',(cx-.172,cy-dy*.37,.25),(cx-.172,cy+dy*.37,.25),.009,.009,M['sombra'])
        obs=_upholstered(name+' · asiento real',(0,0,.665),(.43,dy-.007,.066),C,parent,M['lino'],fullness=.28,wrinkles=.001)
        obs+=_upholstered(name+' · respaldo bajo',(-.185,0,.817),(.055,dy-.035,.22),C,parent,M['lino'],fullness=.26,wrinkles=.0008)
        for ob in obs:_tag(ob)
        parent['bbox_simbolo_visible_pdf']=b;parent['bbox_asset_visual']=nb
        rec.append({'nombre':name,'bbox_simbolo_visible_xy_m':b,'bbox_completo_xy_m':nb,'z_asiento_visual_m':.665,'criterio':'Prolongación hacia isla bajo encimera; borde exterior Xmin y ejeY de símbolo conservados'})
    return rec


def _pillow(name,center,size,mat,rotation=(0,0,0),folds=.0023):
    """Sewn cushion with curved broad faces, soft perimeter and small folds.

    size is local X/Y/thickness; all local extrema remain within supplied box.
    A seated or vertical cushion is simply rotated, never a bevelled block.
    """
    from mathutils import Euler
    hx,hy,hz=[v/2 for v in size];nx,ny=32,32;vs=[];fs=[]
    for side in [-1,1]:
        for j in range(ny+1):
            v=-1+2*j/ny
            for i in range(nx+1):
                u=-1+2*i/nx
                x=hx*u*math.sqrt(1-.12*v*v)
                y=hy*v*math.sqrt(1-.12*u*u)
                bulge=max(0,(1-u*u)*(1-v*v))**.34
                z=side*hz*(.21+.79*bulge)
                # Narrow seam-pressure folds fade towards extrema and centre.
                taper=max(0,1-u*u)*max(0,1-v*v)
                rip=folds*taper*(math.sin(21*u+3*v)*math.exp(-((abs(v)-.78)/.18)**2)
                      +.8*math.sin(23*v-4*u)*math.exp(-((abs(u)-.77)/.17)**2))
                z=max(-hz,min(hz,z+side*rip))
                vs.append((x,y,z))
    n=(nx+1)*(ny+1)
    for side in [0,1]:
        for j in range(ny):
            for i in range(nx):
                a=side*n+j*(nx+1)+i;q=(a,a+1,a+nx+2,a+nx+1)
                fs.append(q if side else tuple(reversed(q)))
    perimeter=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    for i,a in enumerate(perimeter):
        b=perimeter[(i+1)%len(perimeter)];fs.append((a,b,b+n,a+n))
    rot=Euler(rotation,'XYZ').to_matrix();c=Vector(center)
    ob=_mesh(name,[tuple(c+rot@Vector(p)) for p in vs],fs,mat,True)
    # Piping lies inside its cushion rather than enlarging the furnishing bbox.
    seam=[]
    for a in perimeter:
        x,y,z=vs[a];seam.append(tuple(c+rot@Vector((x*.990,y*.990,0))))
    seam.append(seam[0]);_tube(name+'_vivo_cosido',seam,.0010,mat)
    return ob


def _salon_upholstery(by):
    """Furniture-only refinement of source L and two source accent chairs."""
    item=by['sofa_L_salon'];b=item['bbox_xy_m'];x0,y0,x1,y1=b
    xs=sorted(set(p[0] for p in item['huella_xy_m']));ys=sorted(set(p[1] for p in item['huella_xy_m']))
    xr=xs[1];yn=ys[1]
    _remove('sofa_L_salon')
    parent=bpy.data.objects.new('sofa_L_salon',None);C.objects.link(parent);_tag(parent)
    parent['huella_poligono_xy_m']=item['huella_xy_m'];parent['altura_asset_m']=.82
    # Low softly covered frame preserves the complete source L at every bound.
    _box('sofa_L_salon_V3_base_chaise',[x0,y0,xr,y1],.12,.345,M['lino'],.026)
    _box('sofa_L_salon_V3_base_lineal',[xr,yn,x1,y1],.12,.345,M['lino'],.026)
    _box('sofa_L_salon_V3_respaldo_estructura',[x0,y1-.096,x1,y1],.34,.80,M['lino'],.022)
    _box('sofa_L_salon_V3_brazo_chaise',[x0,y0,x0+.115,y1-.038],.33,.635,M['lino'],.042)
    _box('sofa_L_salon_V3_brazo_derecho',[x1-.125,yn,x1,y1-.038],.33,.635,M['lino'],.042)
    for x,y in [(x0+.12,y0+.13),(xr-.12,y0+.13),(x0+.13,y1-.13),(xr-.10,y1-.13),(x1-.14,yn+.12),(x1-.14,y1-.13)]:
        _rod('sofa_L_salon_V3_pata',(x,y,0),(x,y,.12),.016,.019,M['sombra'])
    _pillow('sofa_L_salon_V3_asiento_chaise',((x0+.137+xr-.018)/2,(y0+.021+y1-.139)/2,.433),
            (xr-x0-.155,y1-y0-.160,.192),M['lino'],folds=.0022)
    left=xr+.008;right=x1-.139;w=(right-left)/3
    for i in range(3):
        cx=left+(i+.5)*w
        _pillow('sofa_L_salon_V3_asiento_'+str(i),(cx,(yn+.020+y1-.139)/2,.433),
                (w-.014,y1-yn-.159,.192),M['lino'],folds=.0021+(i%2)*.0003)
    # Individual back pads lean 5–7 degrees; the frame remains in original bbox.
    back_centers=[((x0+.137+xr-.018)/2,xr-x0-.171)]
    back_centers += [(left+(i+.5)*w,w-.019) for i in range(3)]
    for i,(cx,width) in enumerate(back_centers):
        lean=[6,7,5,6.5][i]
        _pillow('sofa_L_salon_V3_cojin_respaldo_'+str(i),(cx,y1-.138,.659),
            (width,.350,.138),M['lino'],rotation=(math.radians(90-lean),0,math.radians([-.6,.8,-.4,.5][i])),folds=.0025)
    # Two loose, lightly leaned cushions with curved faces rather than cubes.
    _pillow('sofa_L_salon_V3_cojin_suelto_izq',(x0+.325,y1-.290,.628),(.35,.34,.115),M['cojin'],
            rotation=(math.radians(78),math.radians(-9),math.radians(-8)),folds=.0028)
    _pillow('sofa_L_salon_V3_cojin_suelto_der',(x1-.370,y1-.285,.621),(.37,.33,.120),M['cojin'],
            rotation=(math.radians(79),math.radians(8),math.radians(10)),folds=.0028)
    return {'huella_fuente_xy_m':item['huella_xy_m'],'altura_visual_m':.82,'cojines_respaldo':4,'inclinacion_grados':[6,7,5,6.5],'pliegues_visuales_m':[.0021,.0028],'criterio':'Sólo tapizado decorativo; bases conservan exactamente huella L, ubicación y escala de plano'}


def _butacas_sheen_asset(by):
    """Import a licensed sculpted upholstery asset and fit source XY exactly."""
    from materiales import aplicar_lino_fotografico
    path=ROOT/'assets/mobiliario/SheenChair/SheenChair.glb'
    if not path.is_file():raise FileNotFoundError('Falta asset documentado: '+str(path))
    records=[]
    for name in ['butaca_salon_1','butaca_salon_2']:
        item=by[name];b=item['bbox_xy_m'];_remove(name)
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(path))
        imported=[o for o in bpy.data.objects if o not in before]
        root=bpy.data.objects.new(name,None);C.objects.link(root);_tag(root)
        originals=[]
        for ob in imported:
            originals.append(ob.name);world=ob.matrix_world.copy()
            for col in list(ob.users_collection):col.objects.unlink(ob)
            C.objects.link(ob)
            ob.name=name+' · '+ob.name
            if ob.parent not in imported:ob.parent=root;ob.matrix_world=world
            _tag(ob)
            if ob.type=='MESH':
                for i,mat in enumerate(list(ob.data.materials)):
                    if mat and mat.name.lower().startswith('fabric'):
                        copy=mat.copy();copy.name='V3 Interior · butaca esculpida lino '+name
                        sh=next(n for n in copy.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
                        old=sh.inputs['Normal'].links[0].from_socket if sh.inputs['Normal'].is_linked else None
                        existing=set(copy.node_tree.nodes)
                        aplicar_lino_fotografico(copy,color=(.48,.438,.372),escala_m=.16)
                        bumps=[n for n in copy.node_tree.nodes if n not in existing and n.type=='BUMP']
                        # Preserve the source asset's normal texture (sewn and
                        # sculpted detail) beneath new photographic weave.
                        if old and bumps:copy.node_tree.links.new(old,bumps[0].inputs['Normal'])
                        tint=sh.inputs.get('Sheen Tint')
                        if tint and not tint.is_linked:
                            try:tint.default_value=(.65,.61,.55,1)
                            except TypeError:pass
                        sh.inputs['Metallic'].default_value=0
                        ob.data.materials[i]=copy
        # Khronos glTF +Z faces Blender -Y; -90deg rotation faces coffee table W.
        root.rotation_euler.z=-math.pi/2
        bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
        pts=[]
        for ob in imported:
            if ob.type!='MESH':continue
            ev=ob.evaluated_get(graph);me=ev.to_mesh();pts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
        lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
        center=[(lo[i]+hi[i])/2 for i in range(3)]
        # World scales are equivalent to swapped local scales after quarter yaw.
        wx=(b[2]-b[0])/(hi[0]-lo[0]);wy=(b[3]-b[1])/(hi[1]-lo[1]);wz=.78/(hi[2]-lo[2])
        root.scale=(wy,wx,wz)
        root.location=((b[0]+b[2])/2-wx*center[0],(b[1]+b[3])/2-wy*center[1],-wz*lo[2])
        bpy.context.view_layer.update()
        pts=[];graph=bpy.context.evaluated_depsgraph_get()
        for ob in imported:
            if ob.type!='MESH':continue
            ev=ob.evaluated_get(graph);me=ev.to_mesh();pts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
        actual=[min(p[i] for p in pts) for i in range(3)]+[max(p[i] for p in pts) for i in range(3)]
        expected=[b[0],b[1],0,b[2],b[3],.78]
        error=max(abs(x-y) for x,y in zip(actual,expected));assert error<.000004,(name,actual,expected)
        root['bbox_fuente_xy_m']=b;root['bbox_evaluado_xyz_m']=actual
        root['fuente_asset']='Khronos glTF-Sample-Assets SheenChair / Eric Chadwick, Wayfair; CC0, procedencia local'
        root['orientacion_visual']='Frente hacia mesa de centro oeste; símbolo visible en fuente no define modelo comercial'
        records.append({'nombre':name,'asset':'assets/mobiliario/SheenChair/SheenChair.glb','asset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bbox_fuente_xy_m':b,'bbox_evaluado_xyz_m':actual,'error_bbox_max_m':error,'altura_visual_m':.78,'orientacion_grados_z':-90,'licencia':'CC0 según READMEfuente actual; autoríaWayfair/EricChadwick preservada; importadorconserva mapas normales ydetalleesculpido'})
    return records


def _tables_and_sofa(by):
    from vegetacion_mobiliario import _upholstered
    dining=by['mesa_comedor_interior']['bbox_xy_m'];coffee=by['mesa_centro_salon']['bbox_xy_m']
    for name in ['mesa_comedor_interior','mesa_centro_salon']:_remove(name)
    x0,y0,x1,y1=dining
    _box('mesa_comedor_interior_V3_tablero',dining,.708,.75,M['roble'],.009)
    # Two slender, solid timber trestles recessed well inside the source top.
    for y in [y0+.35,y1-.35]:
        for x in [x0+.20,x1-.20]:_box('mesa_comedor_interior_V3_pata',[x-.025,y-.03,x+.025,y+.03],0,.708,M['roble_patas'],.005)
        _box('mesa_comedor_interior_V3_travesano',[x0+.19,y-.025,x1-.19,y+.025],.63,.675,M['roble'],.004)
    _box('mesa_centro_salon_V3_tablero',coffee,.353,.385,M['cuarzo'],.025)
    cx=(coffee[0]+coffee[2])/2;cy=(coffee[1]+coffee[3])/2
    for x in [cx-.33,cx+.33]:
        _lathe('mesa_centro_salon_V3_pedestal',(x,cy,0),[(.125,0),(.13,.015),(.095,.04),(.086,.335),(.10,.353)],M['roble_patas'])
    sofa_record=_salon_upholstery(by)
    butacas_record=_butacas_sheen_asset(by)
    parent=bpy.data.objects.get('sofa_L_salon')
    if parent:
        # Folded/draped cotton throw, actual mesh folds inside chaise footprint.
        sf=by['sofa_L_salon'];sx=sorted(set(q[0] for q in sf['huella_xy_m']));sy=sorted(set(q[1] for q in sf['huella_xy_m']))
        pcx=(sx[0]+.137+sx[1]-.018)/2;pcy=(sy[0]+.021+sy[-1]-.139)/2
        phx=(sx[1]-sx[0]-.155)/2;phy=(sy[-1]-sy[0]-.160)/2
        verts=[];faces=[];nx,ny=36,44
        for j in range(ny+1):
            y=14.89+j/ny*.58
            for i in range(nx+1):
                x=3.64+i/nx*.42
                u=(x-pcx)/phx;v=(y-pcy)/phy
                for _ in range(7):
                    u=(x-pcx)/(phx*math.sqrt(max(.001,1-.12*v*v)))
                    v=(y-pcy)/(phy*math.sqrt(max(.001,1-.12*u*u)))
                bulge=max(0,(1-u*u)*(1-v*v))**.34
                zz=.433+.096*(.21+.79*bulge)+.0045
                zz+=.0013*math.sin(i*.63+j*.17)+.0011*math.sin(j*.49)
                verts.append((x,y,zz))
        for j in range(ny):
            for i in range(nx):
                a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
        ob=_mesh('sofa_L_salon_V3_manta_algodon',verts,faces,M['manta'],True)
        mod=ob.modifiers.new('Espesor real tela 1.3mm','SOLIDIFY');mod.thickness=.0013
    # Low units explicitly visible in final plan: footprint exact, Z decorative.
    for i,b in enumerate([[3.34645,12.42695,7.3025,12.7254],[8.2677,12.42695,10.2997,12.7254]]):
        _box('Mueble_bajo_salon_PDF_final_V3_'+str(i),b,.08,.46,M['laca'],.006)
        _box('Mueble_bajo_salon_PDF_final_V3_zocalo_'+str(i),[b[0]+.025,b[1]+.025,b[2]-.025,b[3]-.025],0,.08,M['sombra'])
        for j in range(1,round((b[2]-b[0])/.6)):
            x=b[0]+(b[2]-b[0])*j/round((b[2]-b[0])/.6)
            _box('Mueble_bajo_salon_PDF_final_V3_junta',[x-.001,b[3]-.001,x+.001,b[3]+.0001],.10,.43,M['sombra'],0)
    # TV is a furniture asset, not a new wall recess or architectural opening.
    _box('TV_salon_V3_marco',[4.22,12.56,5.67,12.583],.535,1.365,M['sombra'],.007)
    _box('TV_salon_V3_pantalla',[4.233,12.5828,5.657,12.5833],.548,1.352,M['tv'],.004)
    for x in [4.58,5.30]:_rod('TV_salon_V3_soporte',(x,12.578,.54),(x,12.66,.46),.008,.008,M['sombra'])
    return {'mesa_comedor_bbox_xy_m':dining,'mesa_centro_bbox_xy_m':coffee,'alturas_visuales_m':{'mesa_comedor':.75,'mesa_centro':.385,'mueble_bajo':.46},'muebles_bajos_xy_fuente':'Rellenos grises de planta final PDF1; dos tramos junto pared sur salón','tv':'Accesorio de visualización sobre mueble bajo; no prescrito por planos','sofa':sofa_record,'butacas':butacas_record}


def _accessories(by):
    b=by['mesa_centro_salon']['bbox_xy_m'];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
    # Two restrained books, real page block and covers.
    for j in range(2):
        z=.385+j*.028;x=cx-.31+j*.024;y=cy-.08+j*.018
        bb=[x-.14,y-.10,x+.14,y+.10]
        _box('Libro_salon_V3_cubierta_'+str(j),bb,z,z+.0024,M['libro'],.001)
        _box('Libro_salon_V3_paginas_'+str(j),[bb[0]+.002,bb[1]+.003,bb[2]-.002,bb[3]-.003],z+.0024,z+.0256,M['papel'],.001)
        _box('Libro_salon_V3_tapa_'+str(j),bb,z+.0256,z+.028,M['libro'],.001)
    _lathe('Jarron_ceramica_salon_V3',(cx+.27,cy+.075,.385),[(.035,0),(.052,.012),(.055,.075),(.04,.12),(.022,.15),(.020,.156),(.015,.156),(.015,.15),(.033,.112),(.046,.073),(.043,.014),(.03,.007)],M['ceramica'])
    _lathe('Cuenco_salon_V3',(cx+.24,cy-.17,.385),[(.028,0),(.03,.008),(.072,.04),(.077,.048),(.073,.05),(.067,.037),(.027,.011),(.015,.01)],M['ceramica'])
    b=by['mesa_comedor_interior']['bbox_xy_m'];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
    # A couple of genuine ceramic plates and clear glasses, not a crowded set.
    for i,(x,y) in enumerate([(cx-.35,cy-.53),(cx+.35,cy+.53)]):
        _lathe('Plato_comedor_V3_'+str(i),(x,y,.752),[(.004,0),(.08,0),(.083,.003),(.125,.012),(.13,.017),(.125,.022),(.095,.016),(.079,.008),(.004,.008)],M['porcelana'])
        _lathe('Vaso_comedor_V3_'+str(i),(x+.12,y+.22,.751),[(.024,0),(.025,.003),(.027,.095),(.0245,.095),(.022,.01),(.02,.006)],M['vidrio'])
    _lathe('Centro_mesa_comedor_V3',(cx,cy,.75),[(.048,0),(.055,.011),(.10,.069),(.105,.075),(.10,.081),(.09,.064),(.05,.017),(.04,.01)],M['ceramica'])
    b=by['isla_cocina']['bbox_xy_m'];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
    _lathe('Cuenco_isla_cocina_V3',(cx+.20,cy+.50,.911),[(.055,0),(.058,.008),(.12,.058),(.127,.069),(.122,.075),(.113,.059),(.052,.016),(.039,.008)],M['ceramica'])
    # Cutting board lying entirely on the clear end of the island.
    _box('Tabla_cocina_V3',[cx-.26,cy-.77,cx+.06,cy-.54],.911,.928,M['roble'],.010)


def _pendant(name,xy,zbottom,radius):
    x,y=xy
    _rod(name+'_floron',(x,y,3.176),(x,y,3.2),.033,.033,M['sombra'])
    _rod(name+'_cable',(x,y,zbottom+.22),(x,y,3.178),.0017,.0017,M['sombra'],12)
    _lathe(name+'_pantalla',(x,y,zbottom),[(radius*.88,0),(radius,.024),(radius*.97,.08),(radius*.74,.19),(radius*.36,.228),(.021,.238),(.017,.238),(radius*.34,.222),(radius*.7,.185),(radius*.935,.078),(radius*.965,.027),(radius*.84,.008)],M['pantalla'])
    _rod(name+'_difusor',(x,y,zbottom+.009),(x,y,zbottom+.012),radius*.85,radius*.85,M['pantalla'])
    data=bpy.data.lights.new('Luz_interior_V3_'+name,'AREA');data.shape='DISK';data.size=radius*1.65;data.energy=12;data.color=(1,.86,.69)
    ob=bpy.data.objects.new('Luz_interior_V3_'+name,data);C.objects.link(ob);ob.location=(x,y,zbottom-.005)
    _tag(ob);ob['potencia_visual_w']=12


def aplicar_interiores(scene):
    """Refine decorative assets, assert the entire architecture is identical."""
    global C,M,CREATED
    CREATED=[]
    if bpy.data.collections.get('Mobiliario_Detalle_V3'):
        raise RuntimeError('Aplicar interiores sólo una vez sobre modelo V2 limpio')
    before=_fingerprint(scene)
    C=bpy.data.collections.new('Mobiliario_Detalle_V3')
    parent=bpy.data.collections.get('Mobiliario')
    (parent.children if parent else scene.collection.children).link(C)
    M=_materials()
    from materiales import aplicar_lino_fotografico, aplicar_madera_fotografica, aplicar_mineral_fotografico
    aplicar_madera_fotografica(M['roble'],eje_veta='Y')
    aplicar_madera_fotografica(M['roble_patas'],eje_veta='Z')
    for key in ['lino','cojin','manta']:
        aplicar_lino_fotografico(M[key],color=tuple(M[key].diffuse_color[:3]),escala_m=.16)
    aplicar_mineral_fotografico(M['cuarzo'],color=tuple(M['cuarzo'].diffuse_color[:3]),escala_m=.90)
    sys.path.insert(0,str(DIR))
    f=json.loads((DIR/'datos_mobiliario.json').read_text());by={x['nombre']:x for x in f['objetos']}
    report={'revision':'V3_visual_interiores','fuentes':{'mobiliario_json_sha256':hashlib.sha256((DIR/'datos_mobiliario.json').read_bytes()).hexdigest(),'planta_final_pdf':'fuentes/planta_final_proyecto_obra.pdf','proyecto_basico_pagina':35},'unidades':'m','licencia_assets':'Sofá/cocina/mesas y accesorios propios generados por este script. Butacas SheenChair Khronos / Eric Chadwick Wayfair, CC0 según README actual conservado en assets/mobiliario/SheenChair. Mapas fotográficos ambientCG CC0, modelo/materiales.py y assets/licencias.','regla':'Todas las alturas, grosores y despieces del mobiliario son decoración. No se atribuyen al proyecto dimensiones no escritas.'}
    report['materiales_fotograficos']={key:{'material':M[key].name,'fuente':M[key].get('fuente_PBR',''),'color_lineal':list(M[key].diffuse_color[:3])} for key in ['roble','roble_patas','lino','cojin','manta','cuarzo']}
    report['cocina']=_kitchen(f,by)
    report['sillas_comedor']=_rebuild_chairs(by)
    report['taburetes_isla']=_barstools(by)
    report['salon_comedor']=_tables_and_sofa(by)
    _accessories(by)
    dining=by['mesa_comedor_interior']['centro_xy_m'];island=by['isla_cocina']['centro_xy_m']
    _pendant('Colgante_comedor_V3',dining,2.30,.245)
    for i,y in enumerate([island[1]-.49,island[1]+.49]):_pendant('Colgante_isla_V3_'+str(i),(island[0],y),2.35,.116)
    report['iluminacion_decorativa']={'colgante_comedor_cota_inferior_m':2.30,'colgantes_isla_cota_inferior_m':2.35,'cielorraso_fuente_m':3.20,'potencia_luces_w':12,'descripcion':'Luminarias físicas sobre muebles, emisores cálidos de baja potencia; accesorios no indicados en PDF'}
    bpy.context.view_layer.update();after=_fingerprint(scene)
    assert before==after,(before,after)
    report['control_arquitectura']={'sha256_antes':before[0],'sha256_despues':after[0],'meshes_controlados':before[1],'cambios':0}
    valid=[o for o in CREATED if o.name in bpy.data.objects and bpy.data.objects[o.name]==o]
    report['objetos_detalle_creados']=len(valid)
    report['objetos']=[o.name for o in valid]
    target=DIR/'detalles_interiores_v3.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    scene['detalles_interiores_v3']=json.dumps({'fuentes':report['fuentes'],'control':report['control_arquitectura'],'objetos':len(valid)},ensure_ascii=False)
    text=bpy.data.texts.get('detalles_interiores_v3.json') or bpy.data.texts.new('detalles_interiores_v3.json');text.clear();text.write(target.read_text())
    print('INTERIORES_V3',len(valid),'arquitectura_sin_cambios',before[1],flush=True)
    return report
