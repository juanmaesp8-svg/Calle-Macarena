"""GLB portátil: arquitectura y assets, sin fondo gráfico ni microfibras.
Las microfibras y todos los shaders se conservan íntegros en el archivo blend.
"""
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
for ob in bpy.context.scene.objects:
 ob.select_set(ob.type=='MESH' and not ob.hide_render and ob.get('categoria') not in {'entorno_visual','jardin_microgeometria_material'})
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Calle_Macarena_modelo_1a1.glb'),export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
print('GLB V2 portátil exportado')
