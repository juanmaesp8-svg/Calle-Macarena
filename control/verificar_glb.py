"""Importación independiente de GLB: metros y conservación de vértices/bounds."""
from pathlib import Path
import bpy,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'Calle_Macarena_modelo_1a1.glb'))
ref=json.loads((ROOT/'control/mediciones_mesh_real.json').read_text())
checked=[]
for r in ref['objetos']:
    if r['categoria'] not in {'muro_vivienda','forjado','peto','marquesina','piscina','carpinteria','vidrio','pilar_pergola','viga_pergola','rejilla','porton_vehiculos'}:continue
    ob=bpy.data.objects.get(r['nombre'])
    if not ob:raise RuntimeError('Falta objetoGLB '+r['nombre'])
    vs=[ob.matrix_world@v.co for v in ob.data.vertices]
    bbox=[min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)]
    error=max(abs(a-b) for a,b in zip(bbox,r['bbox_xyz']))
    if error>.001:raise RuntimeError(f'GLB cambia dimensión {ob.name}: {error}m')
    checked.append({'objeto':ob.name,'error_bbox_max_m':error})
result={'valido':True,'unidades':'Metros conforme especificación glTF2.0; XYZ convertido de nuevo a Z-arriba mediante importadorBlender',
        'objetos_verificados':len(checked),'error_max_m':max(r['error_bbox_max_m'] for r in checked),'controles':checked}
(ROOT/'control/control_glb.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print('GLB_VALIDADO',result['objetos_verificados'],result['error_max_m'])
