"""Añade hojas interiores documentadas sin transformar muros ni añadir dinteles.

Uso dentro del builder, antes de la exportación y del guardado:
    from anadir_puertas_interiores import anadir_puertas_interiores
    anadir_puertas_interiores()

También puede ejecutarse con Blender sobre una escena ya abierta. Este script
no guarda ni exporta archivos: el guardado corresponde al pipeline del proyecto.
"""
from pathlib import Path
import json,math
import bpy
from mathutils import Vector

DATA=Path(__file__).resolve().with_name('datos_puertas_interiores.json')
OWNER='puertas_interiores_pdf36'

def _collection(name,parent=None):
    c=bpy.data.collections.get(name)
    if c is None:
        c=bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def _material():
    name='Puertas interiores · DMF lacado blanco documental'
    mat=bpy.data.materials.get(name)
    if mat is None:
        mat=bpy.data.materials.new(name);mat.use_nodes=True
        p=mat.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=(.79,.78,.755,1)
        p.inputs['Roughness'].default_value=.32
        p.inputs['Coat Weight'].default_value=.10
    return mat

def _leaf(name,a,b,z0,z1,thickness,col,material):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    if length<=0:raise ValueError('Hoja sin longitud: '+name)
    nx,ny=-dy/length*thickness/2,dx/length*thickness/2
    footprint=[(a[0]+nx,a[1]+ny),(a[0]-nx,a[1]-ny),(b[0]-nx,b[1]-ny),(b[0]+nx,b[1]+ny)]
    vertices=[(x,y,z0) for x,y in footprint]+[(x,y,z1) for x,y in footprint]
    faces=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
    me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(vertices,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(material)
    return ob

def _reference(name,points,col,z=.025):
    me=bpy.data.meshes.new(name+'_mesh');vs=[(p[0],p[1],z) for p in points]
    me.from_pydata(vs,[(i,(i+1)%len(vs)) for i in range(len(vs))],[]);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob)
    ob.hide_render=True;ob.display_type='WIRE';ob.show_in_front=True
    return ob

def anadir_puertas_interiores(datos_json=None,material=None):
    """Repetible: elimina sólo objetos generados por este mismo módulo.

    No aplica booleans, no modifica objetos existentes ni sus transforms,
    no rellena dinteles, no supone cotas Z superiores y no guarda elblend.
    """
    path=Path(datos_json) if datos_json else DATA
    data=json.loads(path.read_text())
    for ob in list(bpy.data.objects):
        if ob.get('generador_puertas')==OWNER:bpy.data.objects.remove(ob,do_unlink=True)
    col=_collection('Puertas_interiores',bpy.data.collections.get('Carpinterias'))
    refs=_collection('Referencias_puertas_interiores',bpy.data.collections.get('Referencias_PDF'))
    mat=material or _material()
    leaves=[];references=[]
    for door in data['puertas']:
        name=door['nombre'];height=door['altura_hoja_m']
        if height is not None and door['estado_identificacion']!='ambigua':
            ob=_leaf(name+'_hoja_posicion_planta',*door['hoja_eje_xy_m'],door['z_base_m'],door['z_base_m']+height,door['espesor_modelado_m'],col,mat)
            ob['categoria']='carpinteria';ob['fuente']='PDF36 carpintería, registrada+1,68pt aPDF35; altura y espesor memoriaPDF21'
            ob['estado_dimension']='Hoja2,03×ancho gráfico×0,035m; posición abierta documental'
            ob['generador_puertas']=OWNER
            ob['id_vector_pdf36']=door['seqno_hoja_pdf36']
            ob['ancho_hoja_grafico_m']=door['ancho_hoja_grafico_m']
            ob['ancho_generico_memoria_m']=door['ancho_generico_memoria_m']
            ob['altura_hoja_m']=height;ob['espesor_hoja_m']=door['espesor_modelado_m']
            ob['tipo_apertura']=door['tipo']
            ob['dintel_real']='NO DEFINIDO'
            ob['intervalo_superior_hueco_no_definido']='Z2,03–3,35m; sin geometría de dintel/fijo superior'
            if door.get('bisagra_xy_m') is not None:ob['bisagra_xy_m']=door['bisagra_xy_m']
            if door.get('sentido_apertura_visto_desde_arriba'):ob['sentido_apertura']=door['sentido_apertura_visto_desde_arriba']
            leaves.append(ob)
        else:
            # No asignar altura de puerta a una hoja cuya función no está identificada.
            origin=data['origen_pdf35_pt'];factor=data['factor_m_por_pt']
            points=[((pdf[0]-origin[0])*factor,(origin[1]-pdf[1])*factor) for pdf in door['hoja_poligono_pdf35_pt']]
            ref=_reference(name+'_solo_referencia',points,refs)
            ref['generador_puertas']=OWNER;ref['categoria']='referencia_no_acotada'
            ref['fuente']='Hoja/líneaPDF36seq'+str(door['seqno_hoja_pdf36'])
            ref['motivo_oculto_render']=door['notas'];references.append(ref)
        gap=door.get('hueco_posible_bbox_xy_m')
        if gap:
            x0,y0,x1,y1=gap
            ref=_reference(name+'_hueco_XY_sin_dintel',[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],refs,z=2.03)
            ref['generador_puertas']=OWNER;ref['categoria']='referencia_no_acotada'
            ref['fuente']=door['hueco_criterio'];ref['intervalo_z_no_definido']=[2.03,3.35]
            ref['minimo_memoria_p28_m']=2.50;ref['dintel_real']='NULL, sin modelar'
            ref['muros_existentes']='No transformados ni recortados; sólo referencia del intervaloXY'
            references.append(ref)
    text=bpy.data.texts.get('datos_puertas_interiores.json') or bpy.data.texts.new('datos_puertas_interiores.json')
    text.clear();text.write(json.dumps(data,ensure_ascii=False,indent=2))
    bpy.context.scene['puertas_interiores_documentales']=len(leaves)
    bpy.context.scene['huecos_interiores_Z_superior']='Intervalo2,03–3,35m no definido; sin dinteles ni fijos superiores inventados.'
    print('Puertas interiores:',len(leaves),'hojas añadidas,',len(references),'referencias ocultas enrender; muros intactos.')
    return {'hojas':leaves,'referencias':references}

if __name__=='__main__':anadir_puertas_interiores()
