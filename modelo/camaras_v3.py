"""Cámaras de fotografía V3: sólo cámaras; conserva íntegra la geometría.

Coordenadas en metros, sensor de 36 mm y eje óptico horizontal. Los
encuadres se basan en la planta final y se prueban sobre el .blend real.
"""
import json
from pathlib import Path


def aplicar_camaras(scene=None):
    import bpy
    from mathutils import Vector

    scene = scene or bpy.context.scene
    path = Path(__file__).with_suffix('.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    collection = bpy.data.collections.get('Camaras')
    if collection is None:
        collection = bpy.data.collections.new('Camaras')
        scene.collection.children.link(collection)
    prefixes = {c['id'] + '_' for c in data['camaras']}
    for obj in list(bpy.data.objects):
        if obj.type == 'CAMERA' and any(obj.name.startswith(p) for p in prefixes):
            old_data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if old_data.users == 0:
                bpy.data.cameras.remove(old_data)
    created = []
    for spec in data['camaras']:
        name = spec['id'] + '_' + spec['nombre']
        camera_data = bpy.data.cameras.new(name)
        camera = bpy.data.objects.new(name, camera_data)
        collection.objects.link(camera)
        camera.location = spec['posicion_m']
        direction = Vector(spec['objetivo_m']) - camera.location
        assert abs(direction.z) < 1e-9, 'El eje óptico debe ser horizontal'
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        camera_data.type = 'PERSP'
        camera_data.lens = spec['focal_mm']
        camera_data.sensor_width = 36.0
        camera_data.sensor_fit = 'HORIZONTAL'
        camera_data.shift_x = spec.get('shift_x', 0.0)
        camera_data.shift_y = spec['shift_y']
        camera_data.clip_start = 0.035
        camera_data.clip_end = 250.0
        camera_data.dof.use_dof = False
        camera['resolucion_px'] = [2500, 1667]
        camera['revision_visual'] = 'V3'
        camera['exposicion_ev'] = spec['exposicion_ev']
        camera['espacio'] = spec['espacio']
        camera['objetivo_m'] = spec['objetivo_m']
        camera['fuente_encuadre'] = spec['fuente']
        camera['verticales'] = 'Eje óptico horizontal y desplazamiento óptico vertical'
        camera['arquitectura_visible_integra'] = True
        created.append(camera)
    return created
