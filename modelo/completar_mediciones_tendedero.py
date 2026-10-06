"""Completa el registro QA desde mallas ya guardadas; no guarda/cambia blend."""
import json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'control/mediciones_mesh_real.json';r=json.loads(p.read_text())
assert r['version']==2 and bpy.context.scene.get('revision','').startswith('V2')
r['objetos']=[o for o in r['objetos'] if o['categoria']!='tendedero']
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and ob.get('categoria')=='tendedero':
  vs=[list(ob.matrix_world@v.co) for v in ob.data.vertices]
  r['objetos'].append({'nombre':ob.name,'categoria':'tendedero','fuente':ob.get('fuente',''),'vertices':vs,'caras':[list(p.vertices) for p in ob.data.polygons],'bbox_xyz':[min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)]})
p.write_text(json.dumps(r,ensure_ascii=False))
print('Registro completo:',len(r['objetos']),'meshes reales')
