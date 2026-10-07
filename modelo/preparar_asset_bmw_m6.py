"""Prepara sólo el BMW M6 CC0 desde los PLY de PBRT; no importa el estudio.
Ejecutar con Blender --background --factory-startup --python-exit-code 1.
"""
import bpy, json, re, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/vehiculos/BMW_M6_PBRT'
OUT=ROOT/'assets/vehiculos/BMW_M6_vehiculo_CC0.blend'


def read_ply(path):
    data=path.read_bytes();cut=data.index(b'end_header\n')+len(b'end_header\n');header=data[:cut].decode()
    assert 'format binary_little_endian 1.0' in header
    nv=int(re.search(r'element vertex (\d+)',header)[1]);nf=int(re.search(r'element face (\d+)',header)[1])
    vertexheader=header.split('element vertex ')[1].split('element face ')[0]
    props=re.findall(r'property (\w+) (\w+)',vertexheader)
    assert all(t=='float' for t,k in props), props
    dtype=np.dtype([(name,'<f4') for typ,name in props]);verts=np.frombuffer(data,dtype=dtype,count=nv,offset=cut)
    offset=cut+nv*dtype.itemsize
    raw=np.frombuffer(data,dtype=np.dtype([('n','u1'),('indices','<i4',(3,))]),count=nf,offset=offset)
    assert np.all(raw['n']==3),'Se esperaban triángulos originales de PBRT'
    pos=np.column_stack((verts['x'],verts['y'],verts['z'])).astype(np.float32)
    nor=np.column_stack((verts['nx'],verts['ny'],verts['nz'])).astype(np.float32)
    # PBRT Y arriba. Rotación propia, sin reflexión: Xfinal=-Z, Yfinal=-X, Zfinal=Y.
    return np.column_stack((-pos[:,2],-pos[:,0],pos[:,1])),np.column_stack((-nor[:,2],-nor[:,0],nor[:,1])),raw['indices'].copy()


def main():
    assert 'Creative Commons Zero (Public Domain)' in (SOURCE/'BLENDSWAP_LICENSE.txt').read_text()
    manifest=json.loads((SOURCE/'MANIFIESTO_FUENTE_BMW_M6.json').read_text())
    lookup={e['archivo']:e for e in manifest['archivos']}
    script=(SOURCE/'bmw-m6.pbrt').read_text()
    parts=[]
    for block in re.finditer(r'AttributeBegin(.*?)AttributeEnd',script,re.S):
        text=block[1]
        names=re.findall(r'# Name "([^"]+)"',script[:block.start()]);oldname=names[-1] if names else 'Componente'
        for file in re.finditer(r'"string filename"\s*\[\s*"(geometry/[^"\n]+\.ply)"\s*\]',text):
            materials=re.findall(r'NamedMaterial\s+"([^"]+)"',text[:file.start()])
            assert materials
            rel=file[1];material=materials[-1]
            if material=='floor':continue
            path=SOURCE/rel;assert hashlib.sha256(path.read_bytes()).hexdigest()==lookup[rel]['sha256']
            pos,nor,faces=read_ply(path)
            parts.append((rel,material,oldname,pos,nor,faces))
    allpoints=np.concatenate([p[3] for p in parts]);lo=allpoints.min(axis=0);hi=allpoints.max(axis=0)
    center=(lo+hi)/2;center[2]=lo[2]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection=bpy.data.collections.new('BMW M6 CC0 · sólo vehículo');bpy.context.scene.collection.children.link(collection)
    optimizados=[]
    for index,(rel,material,oldname,pos,nor,faces) in enumerate(parts):
        pos-=center
        mesh=bpy.data.meshes.new('BMW_M6_'+Path(rel).stem)
        mesh.from_pydata(pos.tolist(),[],faces.tolist());mesh.update()
        for face in mesh.polygons:face.use_smooth=True
        mesh.normals_split_custom_set_from_vertices(nor.tolist())
        ob=bpy.data.objects.new('BMW_M6_'+Path(rel).stem+'_'+material,mesh);collection.objects.link(ob)
        ob['componente_original']=oldname;ob['material_original_pbrt']=material;ob['archivo_original']=rel
        ob['archivo_original_sha256']=lookup[rel]['sha256'];ob['autor']='tyrant monkey';ob['licencia']='CC0 / Public Domain'
        ratios={'tiresidewall':.10,'WheelRim':.35,'Seal':.15,'brakeDisc':.15,'LEATHER':.5,'shinychrome':.65}
        ratio=.25 if rel=='geometry/mesh_00004.ply' else ratios.get(material,1)
        if ratio<1 and len(mesh.polygons)>1800:
            bpy.context.view_layer.objects.active=ob;ob.select_set(True)
            modifier=ob.modifiers.new('Optimización sólo accesorio decorativo','DECIMATE');modifier.ratio=ratio;modifier.use_collapse_triangulate=True
            bpy.ops.object.modifier_apply(modifier=modifier.name);ob.select_set(False)
            ob['optimizado_solo_accesorio']=True;ob['ratio_colapso_decorativo']=ratio
            optimizados.append({'componente':rel,'material':material,'triangulos_originales':len(faces),'triangulos_finales':len(ob.data.polygons),'ratio':ratio})
    bpy.context.scene['fuente']='BMW M6 2006 by tyrant monkey; PBRT scenes repository mmp/pbrt-v4-scenes'
    bpy.context.scene['licencia']='Creative Commons Zero (Public Domain)'
    bpy.context.scene['frente']='Y positivo; rotación propia de ejes PBRT, no reflexión'
    bpy.context.scene['dimensiones_originales_m']=(hi-lo).tolist()
    bpy.context.scene['transformacion_original']='Xfinal=-Zpbrt,Yfinal=-Xpbrt,Zfinal=Ypbrt; centradoXY y baseZ0'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    report={'asset':OUT.name,'asset_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'componentes':len(parts),'vertices':sum(len(o.data.vertices) for o in collection.objects),'triangulos':sum(len(o.data.polygons) for o in collection.objects),'triangulos_fuente':sum(len(p[5]) for p in parts),'optimizacion_decorativa':optimizados,'dimensiones_originales_m':(hi-lo).tolist(),'bb_original_rotado_m':lo.tolist()+hi.tolist(),'excluidos':['geometry/mesh_00106.ply: floor (suelo del estudio)'],'fuente_commit':manifest['commit'],'autor':'tyrant monkey','licencia':'Creative Commons Zero (Public Domain)','transformacion':'X=-Zpbrt,Y=-Xpbrt,Z=Ypbrt; centradoXY y baseZ0; normales originales conservadas'}
    (ROOT/'assets/vehiculos/BMW_M6_preparacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('BMW_M6_PREPARADO',json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
