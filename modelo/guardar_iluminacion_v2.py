"""Guarda refinamiento de luz; verifica que las mallas medidas no cambian."""
from pathlib import Path
import bpy,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modelo'))
from materiales import setup_lighting
r=json.loads((ROOT/'control/mediciones_mesh_real.json').read_text())
for item in r['objetos']:
 ob=bpy.data.objects[item['nombre']]
 assert len(ob.data.vertices)==len(item['vertices'])
 for v,expected in zip(ob.data.vertices,item['vertices']):
  actual=ob.matrix_world@v.co
  assert max(abs(actual[i]-expected[i]) for i in range(3))<1e-6
setup_lighting(bpy.context.scene,'day')
bpy.context.scene.cycles.use_denoising=False
bpy.context.scene['entorno_reflejos']='Cielo físico y geometría de este modelo. HDRI fotográfico sólo relleno difuso, sin arquitectura ajena visible.'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Calle_Macarena_modelo_1a1.blend'),compress=True)
print('Luz refinada; geometría registrada idéntica')
