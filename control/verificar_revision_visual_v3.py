"""Blender: compara los vértices reales de la revisión visual con V2 validada.

La decoración puede cambiar. La arquitectura, los huecos y el trazado del
jardín deben conservar todos sus vértices, caras y objetos.
"""
from pathlib import Path
import bpy
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
reference_path=ROOT/'fuentes/geometria_validada_v2.json'
reference=json.loads(reference_path.read_text())
expected={o['nombre']:o for o in reference['objetos']}
categories={o['categoria'] for o in expected.values()}
actual={o.name:o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('categoria') in categories}
checks=[]
def check(name,value,detail=''):
    checks.append({'control':name,'cumple':bool(value),'detalle':detail})
check('Mismos objetos arquitectónicos',set(expected)==set(actual),f'{len(expected)} de referencia; {len(actual)} reales')
maximum=0.0
for name,ref in expected.items():
    ob=actual.get(name)
    if ob is None:
        check(name,False,'Objeto ausente');continue
    vertices=[list(ob.matrix_world@v.co) for v in ob.data.vertices]
    faces=[list(p.vertices) for p in ob.data.polygons]
    equal_faces=faces==ref['caras']
    deviation=max((abs(a-b) for u,v in zip(vertices,ref['vertices']) for a,b in zip(u,v)),default=0.0)
    maximum=max(maximum,deviation)
    check(name,len(vertices)==len(ref['vertices']) and equal_faces and deviation<1e-7,f'Diferencia máxima de coordenada {deviation:.12g} m')
    check(name+' visible',ob.hide_render==(name=='Parcela_limite_documental'),'Referencias de parcela ocultas; arquitectura restante visible')
required=['I01','I02','I03','E01','E02','E03','E04']
cameras=[]
for ident in required:
    camera=next((o for o in bpy.context.scene.objects if o.type=='CAMERA' and o.name.startswith(ident+'_')),None)
    check('Cámara '+ident,camera is not None)
    if camera:
        check('Focal '+ident,24<=camera.data.lens<=50,str(camera.data.lens))
        cameras.append({'id':ident,'nombre':camera.name,'posicion_m':list(camera.location),'focal_mm':camera.data.lens,'shift_y':camera.data.shift_y,'exposicion_ev':camera.get('exposicion_ev',None)})
check('Escala métrica 1:1',bpy.context.scene.unit_settings.system=='METRIC' and math.isclose(bpy.context.scene.unit_settings.scale_length,1.0))
check('Planta final idéntica',sha(ROOT/'fuentes/planta_final_proyecto_obra.pdf')==reference['fuente_sha256'])
failed=[v for v in checks if not v['cumple']]
result={'revision':'V3_visual_sobre_planta_final_V2','valido':not failed,'modelo_sha256':sha(ROOT/'Calle_Macarena_modelo_1a1.blend'),'referencia_geometrica_sha256':sha(reference_path),'arquitectura_objetos_comparados':len(expected),'maxima_diferencia_coordenada_m':maximum,'controles':len(checks),'fallos':failed,'camaras':cameras,'detalle':checks}
(ROOT/'control/control_revision_visual_v3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('IDENTIDAD_ARQUITECTURA_V3',len(expected),'objetos','error',maximum,'fallos',len(failed),flush=True)
if failed:
    print(json.dumps(failed,ensure_ascii=False,indent=2));raise RuntimeError('La revisión visual ha cambiado la arquitectura')
