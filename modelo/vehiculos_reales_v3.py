"""Dos BMW M6 CC0 como accesorios, ajustados al símbolo de aparcamiento.

Sólo sustituye los vehículos. No importa suelo, luces, cámaras ni entorno del
asset. API aplicar_vehiculos(scene); devuelve informe y verifica arquitectura.
"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'assets/vehiculos/BMW_M6_vehiculo_CC0.blend'


def _material(nombre,tono=None):
    key='BMW V3 · '+nombre+(' · '+tono if tono else '')
    mat=bpy.data.materials.get(key)
    if mat:return mat
    mat=bpy.data.materials.new(key);mat.use_nodes=True
    nodes,links=mat.node_tree.nodes,mat.node_tree.links;p=nodes.get('Principled BSDF')
    colors={'LogoAzure':(.13,.27,.49),'LogoBlack':(.017,.019,.022),'LogoBlue':(.1,.3,.56),'LogoRed':(.48,.025,.013),'LogoWhite':(.72,.73,.73)}
    color=colors.get(nombre,(.035,.037,.04));rough=.4;metal=0;transmission=0;coat=0
    if nombre=='CarPaint':
        color=(.063,.073,.087) if tono=='antracita' else (.32,.345,.37);rough=.235;metal=.62;coat=1
    elif nombre in {'WheelRim','shinychrome','grillmetal','LogoSilver'}:
        color=(.48,.51,.54);rough=.17 if nombre=='WheelRim' else .11;metal=1
    elif nombre in {'LightGlass','HeadLightGlass','HeadLightGlass01','WindscreenGlass'}:
        color=(.72,.8,.87) if nombre=='WindscreenGlass' else (.96,.97,.98);rough=.015;transmission=1
    elif nombre in {'tire','tiresidewall'}:color=(.018,.021,.025);rough=.72
    elif nombre=='LEATHER':color=(.12,.105,.087);rough=.6
    elif nombre=='brakeDisc':color=(.24,.265,.28);rough=.42;metal=.95
    elif nombre=='brake_clipper':color=(.14,.145,.15);rough=.33;metal=.7
    elif nombre=='HeadLight':color=(.7,.71,.72);rough=.12;metal=.65
    elif nombre=='None':color=(.65,.64,.6);rough=.38
    elif nombre=='mattefloor':color=(.025,.023,.022);rough=.82
    elif nombre in {'carbonfibre','WindowSeal','Seal'}:color=(.022,.025,.028);rough=.45
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal;p.inputs['Transmission Weight'].default_value=transmission
    p.inputs['IOR'].default_value=1.52;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.075
    mat.diffuse_color=(*color,1)
    if nombre in {'CarPaint','tire','tiresidewall','LEATHER'}:
        geo=nodes.new('ShaderNodeNewGeometry');noise=nodes.new('ShaderNodeTexNoise');bump=nodes.new('ShaderNodeBump')
        noise.inputs['Scale'].default_value=2200 if nombre=='CarPaint' else 850 if nombre=='LEATHER' else 420
        noise.inputs['Detail'].default_value=2;links.new(geo.outputs['Position'],noise.inputs['Vector'])
        bump.inputs['Strength'].default_value=.15 if nombre=='CarPaint' else .27
        bump.inputs['Distance'].default_value=.000025 if nombre=='CarPaint' else .00022
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
    mat['fuente_geometria']='BMW M6 2006, tyrant monkey; CC0 / Public Domain'
    mat['acabado_v3']='PBR procedural físico: pintura neutra, capa transparente y microasperidades métricas; sin alterar geometría'
    return mat


def _world_bounds(objects):
    lows=[];highs=[]
    for ob in objects:
        v=np.empty(len(ob.data.vertices)*3,dtype=np.float32);ob.data.vertices.foreach_get('co',v)
        v=v.reshape((-1,3)).astype(np.float64);m=np.array(ob.matrix_world,dtype=np.float64)
        w=v@m[:3,:3].T+m[:3,3];lows.append(w.min(axis=0));highs.append(w.max(axis=0))
    return np.min(lows,axis=0),np.max(highs,axis=0)


def _snapshot_architectura(scene):
    names=[o['nombre'] for o in json.loads((ROOT/'control/mediciones_mesh_real.json').read_text())['objetos']]
    result={}
    for name in names:
        ob=scene.objects.get(name);assert ob and ob.type=='MESH',name
        result[name]=(tuple(v for row in ob.matrix_world for v in row),tuple(tuple(v.co) for v in ob.data.vertices),tuple(tuple(p.vertices) for p in ob.data.polygons))
    return result


def aplicar_vehiculos(scene=None):
    scene=scene or bpy.context.scene
    before=_snapshot_architectura(scene)
    evidence=json.loads((ROOT/'assets/vehiculos/BMW_M6_preparacion.json').read_text())
    sha=hashlib.sha256(ASSET.read_bytes()).hexdigest();assert sha==evidence['asset_sha256']
    assert 'Creative Commons Zero (Public Domain)' in (ROOT/'assets/vehiculos/BMW_M6_PBRT/BLENDSWAP_LICENSE.txt').read_text()
    plan=json.loads((ROOT/'modelo/datos_planta.json').read_text())
    centers=plan['referencias']['aparcamiento']['car_symbol_centers_xy_m']
    assert centers==[[5.886335,3.781426],[8.407515,3.781426]]
    # Sólo raíces conocidas de vehículos y sus componentes, nunca arquitectura.
    deleting=set()
    for ob in scene.objects:
        if ob.name in {'Vehiculo_01_posicion_plano','Vehiculo_02_posicion_plano'} or ob.get('vehiculo_real_v3'):
            deleting.add(ob);deleting.update(ob.children_recursive)
    for ob in list(deleting):
        data=ob.data if ob.type in {'MESH','CURVE'} else None
        bpy.data.objects.remove(ob,do_unlink=True)
        if data and data.users==0:
            (bpy.data.meshes if isinstance(data,bpy.types.Mesh) else bpy.data.curves).remove(data)
    collection=bpy.data.collections.get('Aparcamiento')
    assert collection is not None
    with bpy.data.libraries.load(str(ASSET),link=False) as (available,loaded):
        loaded.objects=[n for n in available.objects if n.startswith('BMW_M6_mesh_')]
    prototypes=[ob for ob in loaded.objects if ob and ob.type=='MESH']
    assert len(prototypes)==evidence['componentes']
    # Bounds of actual optimized geometry, then fit exact source symbol in XY.
    lo,hi=_world_bounds(prototypes);dims=hi-lo;mid=(lo+hi)/2;mid[2]=lo[2]
    sx,sy=2.084/dims[0],4.934/dims[1];sz=sy
    fitting=Matrix.Diagonal(Vector((sx,sy,sz,1)))@Matrix.Translation(Vector((-mid[0],-mid[1],-mid[2])))
    reports=[]
    for index,xy in enumerate(centers,1):
        parent=bpy.data.objects.new(f'Vehiculo_{index:02d}_posicion_plano',None);collection.objects.link(parent)
        parent.location=(xy[0],xy[1],0);parent['vehiculo_real_v3']=True;parent['frente']='+Y'
        parent['procedencia_xy']='Centro y envolvente del símbolo de aparcamiento del plano final; no altera ubicación ni orientación'
        parent['fuente_asset']='BMW M6 2006 by tyrant monkey; mmp/pbrt-v4-scenes';parent['licencia']='CC0 / Public Domain'
        parent['altura_visual_m']=float(dims[2]*sz);parent['altura']='Proporción del asset decorativo, no cota del proyecto'
        parent['caja_xy_m']=[2.084,4.934];objects=[]
        for proto in prototypes:
            ob=proto if index==1 else proto.copy()
            if index==2:ob.data=proto.data
            ob.name=f'Vehiculo_{index:02d}_BMW_M6_'+ob.get('archivo_original','').split('/')[-1].replace('.ply','')
            collection.objects.link(ob);ob.parent=parent;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=fitting
            ob['vehiculo_real_v3']=True;ob['categoria']='vehiculo_decorativo';ob['asset_sha256']=sha
            ob['fuente']='Asset BMW M6 CC0, sólo vehículo; XY exactos del símbolo del proyecto'
            original=ob['material_original_pbrt'];tono=('antracita' if index==1 else 'gris') if original=='CarPaint' else None;mat=_material(original,tono)
            if not ob.data.materials:ob.data.materials.append(mat)
            ob.material_slots[0].link='OBJECT';ob.material_slots[0].material=mat
            objects.append(ob)
        bpy.context.view_layer.update()
        carlo,carhi=_world_bounds(objects);targetlo=np.array([xy[0]-1.042,xy[1]-2.467,0]);targethi=np.array([xy[0]+1.042,xy[1]+2.467,float(dims[2]*sz)])
        error=float(max(np.max(np.abs(carlo-targetlo)),np.max(np.abs(carhi-targethi))))
        assert error<.00002,('Error envolvente vehículo',error)
        reports.append({'nombre':parent.name,'centro_xy_m':xy,'bbox_real_m':carlo.tolist()+carhi.tolist(),'dimensiones_reales_m':(carhi-carlo).tolist(),'frente':'+Y','error_max_bbox_m':error,'componentes':len(objects),'acabado':'antracita' if index==1 else 'gris','cota_z_apoyo_m':0,'fuente_z_apoyo':'Superficie pavimentada existente del modelo, cara superior Z0'})
    assert before==_snapshot_architectura(scene),'No se permite modificar arquitectura al sustituir vehículos'
    report={'revision_visual':'V3','asset_sha256':sha,'autor':'tyrant monkey','licencia':'Creative Commons Zero (Public Domain)','fuente_repo':'mmp/pbrt-v4-scenes','fuente_commit':evidence['fuente_commit'],'arquitectura_intacta':len(before),'geometria_compartida_entre_dos_coches':True,'altura_decorativa_proporcional':True,'vehiculos':reports}
    (ROOT/'control/vehiculos_reales_v3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report

aplicar_vehiculos_reales=aplicar_vehiculos
