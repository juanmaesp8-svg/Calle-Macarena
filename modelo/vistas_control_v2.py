"""Vistas ortográficas analíticas V2 de una escena Blender ya cargada.

Uso, después de construir y guardar el modelo V2 y sus mediciones:
  blender -b Calle_Macarena_modelo_1a1.blend --python-exit-code 1 \
    --python modelo/vistas_control_v2.py -- --engine CYCLES --samples 24

Sólo verificar las fuentes y las mediciones, sin preparar ni renderizar vistas:
  blender -b Calle_Macarena_modelo_1a1.blend --python-exit-code 1 \
    --python modelo/vistas_control_v2.py -- --validate-only

Subset o fondo transparente:
  ... -- --ids PLANTA_CORTE,QA01,QA02 --background transparent

Sección adicional, únicamente cuando el operador aporte estación y orientación:
  ... -- --section 'S01:X:6.00:+' --section-source 'Estación indicada por operador'
  Formato ID:EJE:COORDENADA_M:LADO_CAMARA. '+' conserva el semiespacio inferior
  a la coordenada y mira desde el lado positivo; '-' hace lo contrario. No se
  asocian estas estaciones a las secciones del PDF sin evidencia adicional.

Motor predeterminado Cycles CPU, muestreo bajo y materiales analíticos opacos,
no OIDN. BLENDER_WORKBENCH está disponible si el host tiene contexto OpenGL.
Todas las imágenes se generan en escenas temporales con copias de las mallas.
No se ocultan, cambian, guardan ni exportan los objetos del modelo principal.
No lee registros, controles, imágenes ni archivos .blend de revisión V1.
El resultado es evidencia visual para cotejo, nunca una declaración de QA apta.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

import bpy
import bmesh
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'control' / 'visual_v2' / 'ortograficas'
DEFAULT_IDS = 'PLANTA_CORTE,PLANTA_CUBIERTA,QA01,QA02,QA03,QA04'
ARCH_COLLECTIONS = {
    'Vivienda', 'Cubierta', 'Porches', 'Pergola', 'Carpinterias',
    'Puertas_interiores', 'Trastero', 'Trastero_V2', 'Acabados_fachada',
}
ARCH_CATEGORIES = {
    'muro_vivienda', 'muro_trastero', 'forjado', 'peto', 'marquesina',
    'viga_pergola', 'pilar_pergola', 'carpinteria', 'vidrio', 'suelo_vivienda',
    'cielorraso', 'puerta_interior', 'puerta_trastero', 'porton_trastero',
    'acabado_fachada', 'grava_visual',
}
SITE_CATEGORIES = {
    'parcela', 'jardin', 'pavimento', 'piscina', 'cerramiento', 'tendedero',
    'puerta_peatonal', 'porton_vehiculos', 'rejilla',
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for part in iter(lambda: handle.read(1024*1024), b''):
            digest.update(part)
    return digest.hexdigest()


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT.resolve()))


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate_sources(source_scene):
    """Reject a V1 checkout/copy and prove registry geometry matches this scene.

    The builder writes measurements immediately BEFORE saving the .blend, so
    timestamps are not used as an assertion of identity. Names, world vertices
    and faces are compared directly; a stored hash is also checked if available.
    """
    filepath = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    if filepath is None or not filepath.is_file():
        raise RuntimeError('Debe cargar un .blend V2 guardado antes de generar controles.')
    try:
        parts = filepath.relative_to(ROOT.resolve()).parts
    except ValueError as error:
        raise RuntimeError('El .blend activo no pertenece a la raíz de esta revisión V2.') from error
    if any('v1' in part.lower() or 'revisiones' in part.lower() for part in parts):
        raise RuntimeError('No se admite un .blend archivado ni perteneciente a revisión V1.')
    confirmation_path = ROOT / 'modelo' / 'confirmaciones_usuario_v2.json'
    final_pdf = ROOT / 'fuentes' / 'planta_final_proyecto_obra.pdf'
    basic_pdf = ROOT / 'fuentes' / 'proyecto_basico.pdf'
    measurements_path = ROOT / 'control' / 'mediciones_mesh_real.json'
    criteria_path = ROOT / 'modelo' / 'criterios_qa_camaras.json'
    for path in (confirmation_path, final_pdf, basic_pdf, measurements_path, criteria_path):
        if not path.is_file():
            raise RuntimeError('Falta una fuente necesaria V2: '+relative(path))
    confirmation = _json(confirmation_path)
    if not str(confirmation.get('revision', '')).startswith('V2'):
        raise RuntimeError('Las confirmaciones no identifican una revisión V2.')
    pdf_hash = sha256(final_pdf)
    expected_hash = confirmation.get('fuente_planta', {}).get('sha256')
    if not expected_hash or pdf_hash != expected_hash:
        raise RuntimeError('El PDF de planta final no coincide con el SHA256 confirmado para V2.')
    trastero = [obj for obj in source_scene.objects
                if obj.type == 'MESH' and 'trastero' in obj.name.casefold()]
    if not trastero:
        raise RuntimeError('La escena no contiene mallas del trastero V2; puede ser una copia de V1.')
    measurements = _json(measurements_path)
    items = measurements.get('objetos', [])
    if not items:
        raise RuntimeError('El registro de mediciones está vacío.')
    by_name = {obj.name: obj for obj in source_scene.objects if obj.type == 'MESH'}
    registered_names = {item['nombre'] for item in items}
    if not any(obj.name in registered_names for obj in trastero):
        raise RuntimeError('Las mediciones no incluyen las nuevas mallas del trastero V2.')
    model_hash = sha256(filepath)
    registered_hash = measurements.get('modelo_sha256') or measurements.get('blend_sha256')
    if registered_hash and registered_hash != model_hash:
        raise RuntimeError('El SHA256 de las mediciones no corresponde al .blend activo.')
    maximum_error = 0.
    for item in items:
        obj = by_name.get(item['nombre'])
        if obj is None:
            raise RuntimeError('Objeto registrado ausente en esta escena: '+item['nombre'])
        vertices = item.get('vertices', [])
        if len(vertices) != len(obj.data.vertices):
            raise RuntimeError('Número de vértices distinto del registro: '+obj.name)
        for vertex, recorded in zip(obj.data.vertices, vertices):
            actual = obj.matrix_world @ vertex.co
            error = max(abs(actual[axis]-recorded[axis]) for axis in range(3))
            maximum_error = max(maximum_error, error)
            if error > 1e-5:
                raise RuntimeError('Mediciones desactualizadas en '+obj.name+': error '+str(error)+' m')
        faces = [list(polygon.vertices) for polygon in obj.data.polygons]
        if item.get('caras') != faces:
            raise RuntimeError('Topología distinta del registro: '+obj.name)
    return {
        'revision': confirmation['revision'],
        'modelo': relative(filepath), 'modelo_sha256': model_hash,
        'planta_final': relative(final_pdf), 'planta_final_sha256': pdf_hash,
        'proyecto_basico': relative(basic_pdf), 'proyecto_basico_sha256': sha256(basic_pdf),
        'confirmaciones_sha256': sha256(confirmation_path),
        'mediciones': relative(measurements_path), 'mediciones_sha256': sha256(measurements_path),
        'criterios_camaras_sha256': sha256(criteria_path),
        'script_sha256': sha256(Path(__file__)),
        'objetos_registrados_comparados': len(items),
        'error_max_vertices_registro_m': maximum_error,
        'modo_comparacion': 'Mallas base, vértices mundiales y caras; no identidad por fecha de archivo',
        'estado_qa': 'Evidencia visual pendiente de revisión; no declara aptitud para renders',
    }


def _family_collections(obj):
    names = {collection.name for collection in obj.users_collection}
    # Nested collections in the loaded scene: find parent ancestry without
    # assuming that a mesh is linked directly to its semantic root collection.
    changed = True
    while changed:
        changed = False
        for collection in bpy.data.collections:
            if collection.name not in names and any(child.name in names for child in collection.children):
                names.add(collection.name); changed = True
    return names


def selected_geometry(source_scene, mode):
    objects = []
    for obj in source_scene.objects:
        if obj.type != 'MESH':
            continue
        category = str(obj.get('categoria', ''))
        collections = _family_collections(obj)
        if 'Referencias_PDF' in collections or 'Mobiliario' in collections or 'Aparcamiento' in collections:
            continue
        architecture = category in ARCH_CATEGORIES or bool(collections & ARCH_COLLECTIONS)
        # Lawn surface is documentary; grass fibres, trees and shrub meshes
        # belong to visualisation and have no 'jardin' architectural category.
        site = category in SITE_CATEGORIES
        if not architecture and not (mode.startswith('PLANTA') and site):
            continue
        if mode == 'PLANTA_CORTE' and ('Cubierta' in collections or category in {'forjado', 'cielorraso', 'peto', 'grava_visual'}):
            continue
        objects.append(obj)
    if not objects:
        raise RuntimeError('No se han identificado mallas arquitectónicas para '+mode)
    return objects


def _material(stage, key, color):
    material = bpy.data.materials.new(stage.name+' · '+key)
    material.use_nodes = True
    material.diffuse_color = (*color, 1)
    nodes = material.node_tree.nodes
    nodes.clear()
    shader = nodes.new('ShaderNodeBsdfDiffuse')
    shader.inputs['Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = 1.
    output = nodes.new('ShaderNodeOutputMaterial')
    material.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    return material


def materials(stage):
    return {key: _material(stage, key, color) for key, color in {
        'pared': (.73, .74, .75), 'suelo': (.88, .88, .88),
        'carpinteria': (.12, .14, .16), 'vidrio': (.31, .36, .40),
        'jardin': (.77, .81, .77), 'pavimento': (.82, .82, .81),
        'piscina': (.60, .70, .73), 'cubierta': (.68, .68, .67),
        'corte': (.07, .08, .09), 'parcela': (.97, .97, .97),
    }.items()}


def _role_material(obj, mats):
    category = str(obj.get('categoria', ''))
    if category in {'suelo_vivienda', 'pavimento'}: return mats['suelo' if category == 'suelo_vivienda' else 'pavimento']
    if category == 'vidrio' or 'vidrio' in obj.name.casefold(): return mats['vidrio']
    if category in {'carpinteria', 'puerta_interior', 'puerta_peatonal', 'porton_vehiculos', 'rejilla', 'puerta_trastero', 'porton_trastero'}:
        return mats['carpinteria']
    if category == 'jardin': return mats['jardin']
    if category == 'piscina': return mats['piscina']
    if category == 'parcela': return mats['parcela']
    if category in {'grava_visual', 'forjado', 'peto'}: return mats['cubierta']
    return mats['pared']


def copy_geometry(stage, objects, depsgraph, mats, cut=None):
    """Freeze evaluated geometry into world coordinates and cut only its copies."""
    generated = []
    for source in objects:
        evaluated = source.evaluated_get(depsgraph)
        data = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=False, depsgraph=depsgraph)
        data.transform(source.matrix_world)
        data.materials.clear()
        data.materials.append(_role_material(source, mats))
        data.materials.append(mats['corte'])
        for polygon in data.polygons:
            polygon.material_index = 0
        if cut:
            axis, station, positive_side = cut
            normal = Vector((int(axis == 'X'), int(axis == 'Y'), int(axis == 'Z')))
            location = normal*station
            bm = bmesh.new(); bm.from_mesh(data)
            result = bmesh.ops.bisect_plane(
                bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces), dist=1e-7,
                plane_co=location, plane_no=normal, use_snap_center=False,
                clear_outer=positive_side, clear_inner=not positive_side,
            )
            cut_edges = [item for item in result['geom_cut'] if isinstance(item, bmesh.types.BMEdge) and item.is_boundary]
            if cut_edges:
                filled = bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)
                for face in filled.get('faces', []):
                    face.material_index = 1
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(data); bm.free()
        if not data.vertices or not data.polygons:
            bpy.data.meshes.remove(data)
            continue
        data.update()
        obj = bpy.data.objects.new(stage.name+' · '+source.name, data)
        stage.collection.objects.link(obj)
        obj['objeto_origen'] = source.name
        obj['categoria_origen'] = str(source.get('categoria', ''))
        generated.append(obj)
    if not generated:
        raise RuntimeError('El corte no deja mallas visibles; revise la estación indicada.')
    return generated


def camera(stage, spec):
    data = bpy.data.cameras.new(stage.name+' · cámara')
    obj = bpy.data.objects.new(stage.name+' · cámara', data)
    stage.collection.objects.link(obj)
    obj.location = Vector(spec['posicion_m'])
    forward = (Vector(spec['objetivo_m'])-obj.location).normalized()
    up = Vector(spec['camara_up_m']).normalized()
    right = forward.cross(up).normalized()
    up = right.cross(forward).normalized()
    if right.length < .99:
        raise RuntimeError('La dirección de cámara y su vector superior son paralelos.')
    obj.rotation_euler = Matrix((right, up, -forward)).transposed().to_quaternion().to_euler()
    data.type = 'ORTHO'; data.sensor_fit = 'HORIZONTAL'
    data.ortho_scale = spec['ortho_scale_m']
    data.clip_start = .01; data.clip_end = 500.
    stage.camera = obj
    return obj, list(right), list(up)


def configure(stage, spec, args):
    stage.render.engine = args.engine
    stage.render.resolution_x, stage.render.resolution_y = spec['resolucion_px']
    stage.render.resolution_percentage = 100
    stage.render.image_settings.file_format = 'PNG'
    stage.render.image_settings.color_mode = 'RGBA' if args.background == 'transparent' else 'RGB'
    stage.render.image_settings.color_depth = '8'
    stage.render.film_transparent = True
    stage.render.threads_mode = 'FIXED'; stage.render.threads = args.threads
    stage.world = bpy.data.worlds.new(stage.name+' · mundo neutro')
    stage.world.use_nodes = True
    bg = stage.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (1, 1, 1, 1)
    bg.inputs['Strength'].default_value = .65
    stage.view_settings.view_transform = 'Standard'
    stage.view_settings.exposure = 0.
    stage.view_settings.gamma = 1.
    try: stage.view_settings.look = 'None'
    except TypeError: pass
    if args.engine == 'CYCLES':
        stage.cycles.device = 'CPU'; stage.cycles.samples = args.samples
        stage.cycles.use_denoising = False
        stage.cycles.use_adaptive_sampling = False
        stage.cycles.max_bounces = 3
        stage.cycles.diffuse_bounces = 2
        stage.cycles.glossy_bounces = 0
        stage.cycles.transmission_bounces = 0
        stage.cycles.caustics_reflective = False
        stage.cycles.caustics_refractive = False
        data = bpy.data.lights.new(stage.name+' · área neutra', 'AREA')
        data.energy = 2400.; data.size = 25.
        light = bpy.data.objects.new(data.name, data)
        stage.collection.objects.link(light)
        light.location = (-18, -18, 38)
        light.rotation_euler = (Vector((8, 18, 0))-light.location).to_track_quat('-Z', 'Y').to_euler()
    else:
        shading = stage.display.shading
        shading.light = 'STUDIO'; shading.color_type = 'MATERIAL'
        shading.show_shadows = True; shading.show_cavity = True
        shading.cavity_type = 'BOTH'
        shading.show_object_outline = True
        shading.object_outline_color = (.10, .11, .12)
        shading.background_type = 'WORLD'
        stage.display.render_aa = '16'
    # Composite a true white backdrop; retain neutral world light for geometry.
    if args.background == 'white':
        stage.use_nodes = True
        tree = stage.node_tree; tree.nodes.clear()
        render = tree.nodes.new('CompositorNodeRLayers'); render.scene = stage
        alpha = tree.nodes.new('CompositorNodeAlphaOver')
        alpha.inputs[0].default_value = 1.
        alpha.inputs[1].default_value = (1, 1, 1, 1)
        tree.links.new(render.outputs['Image'], alpha.inputs[2])
        out = tree.nodes.new('CompositorNodeComposite')
        tree.links.new(alpha.outputs['Image'], out.inputs['Image'])


def specs(args):
    criteria = _json(ROOT/'modelo'/'criterios_qa_camaras.json')
    analytic = {spec['id']: spec for spec in criteria['camaras_analiticas']}
    for ident in ('QA00', 'QA01', 'QA02', 'QA03', 'QA04'):
        if ident not in analytic or analytic[ident]['tipo'] != 'ORTHO':
            raise RuntimeError('Falta cámara analítica ortográfica '+ident)
    top = dict(analytic['QA00'])
    top['corte'] = ('Z', args.cut_z, True)
    top['id'] = 'PLANTA_CORTE'
    top['nombre'] = 'V2_QA00_Planta_cortada_Z'+f'{args.cut_z:.2f}'.replace('.', '_')
    top['nota'] = 'Corte horizontal analítico a Z='+str(args.cut_z)+' m; no cubierta; cotas no reinterpretadas.'
    roof = dict(analytic['QA00'])
    roof['id'] = 'PLANTA_CUBIERTA'; roof['nombre'] = 'V2_QA00_Cubierta'
    roof['nota'] = 'Proyección superior de cubierta y parcela, sin corte y sin accesorios de paisajismo.'
    result = {'PLANTA_CORTE': top, 'PLANTA_CUBIERTA': roof}
    for ident in ('QA01', 'QA02', 'QA03', 'QA04'):
        value = dict(analytic[ident])
        value['nombre'] = 'V2_'+ident+'_'+value['nombre']
        value['nota'] = 'Fachada completa sin entorno, muebles, vehículos ni vegetación. Orientación del JSON de cámaras.'
        result[ident] = value
    chosen = []
    for ident in args.ids.split(','):
        ident = ident.strip()
        if ident not in result:
            raise ValueError('ID de vista desconocido: '+ident)
        chosen.append(result[ident])
    for text in args.section:
        parts = text.split(':')
        if len(parts) != 4:
            raise ValueError('Sección: se espera ID:EJE:COORDENADA_M:LADO_CAMARA')
        ident, axis, coordinate, side = parts
        axis = axis.upper()
        if axis not in {'X', 'Y'} or side not in {'+', '-'}:
            raise ValueError('Sección vertical: eje X/Y y lado +/-.')
        if not ident or any(character not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-' for character in ident):
            raise ValueError('El ID de sección debe contener letras, números, guion o guion bajo.')
        station = float(coordinate)
        if not math.isfinite(station):
            raise ValueError('La estación de corte debe ser finita.')
        chosen.append({'id': ident, 'nombre': 'V2_Seccion_analitica_'+ident,
                       'corte': (axis, station, side == '+'),
                       'seccion_solicitada': True, 'fuente_estacion': args.section_source,
                       'nota': 'Estación aportada por operador; sin atribuir a una sección del PDF salvo referencia expresa.'})
    if len({spec['id'] for spec in chosen}) != len(chosen):
        raise ValueError('Los ID de vista deben ser únicos.')
    return chosen


def section_frame(spec, meshes):
    axis, station, positive = spec['corte']
    coords = [vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = [min(point[axis] for point in coords) for axis in range(3)]
    high = [max(point[axis] for point in coords) for axis in range(3)]
    center = Vector([(low[axis]+high[axis])/2 for axis in range(3)])
    index = 0 if axis == 'X' else 1
    center[index] = station
    position = center.copy(); position[index] += 70 if positive else -70
    # Fit retained geometry to a landscape analytical viewport, no station guess.
    horizontal = high[1-index]-low[1-index]
    vertical = high[2]-low[2]
    width = max(horizontal*1.10, vertical*1.10*(2500/850), 1.)
    spec.update({'tipo': 'ORTHO', 'posicion_m': list(position), 'objetivo_m': list(center),
                 'camara_up_m': [0, 0, 1], 'ortho_scale_m': width, 'resolucion_px': [2500, 850]})


def cleanup(stage):
    world = stage.world
    materials_to_remove = {material for obj in stage.objects if obj.type == 'MESH' for material in obj.data.materials}
    for obj in list(stage.objects):
        data = obj.data; obj_type = obj.type
        bpy.data.objects.remove(obj, do_unlink=True)
        if data and data.users == 0:
            if obj_type == 'MESH': bpy.data.meshes.remove(data)
            elif obj_type == 'CAMERA': bpy.data.cameras.remove(data)
            elif obj_type == 'LIGHT': bpy.data.lights.remove(data)
    bpy.data.scenes.remove(stage)
    if world and world.users == 0: bpy.data.worlds.remove(world)
    for material in materials_to_remove:
        if material.users == 0: bpy.data.materials.remove(material)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ids', default=DEFAULT_IDS)
    parser.add_argument('--engine', choices=['CYCLES', 'BLENDER_WORKBENCH'], default='CYCLES')
    parser.add_argument('--samples', type=int, default=24)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--cut-z', type=float, default=1.20)
    parser.add_argument('--background', choices=['white', 'transparent'], default='white')
    parser.add_argument('--section', action='append', default=[])
    parser.add_argument('--section-source', default='Estación analítica indicada explícitamente por operador; sin línea documental atribuida')
    parser.add_argument('--validate-only', action='store_true')
    arguments = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    args = parser.parse_args(arguments)
    if args.samples < 1 or args.threads < 1 or not math.isfinite(args.cut_z):
        raise ValueError('Samples/threads deben ser positivos y cut-z finito.')
    source_scene = bpy.context.scene
    provenance = validate_sources(source_scene)
    print('FUENTES_V2_COINCIDENTES', json.dumps(provenance, ensure_ascii=False), flush=True)
    if args.validate_only:
        return
    requested = specs(args)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    initial_scene_names = {scene.name for scene in bpy.data.scenes}
    initial_object_names = {obj.name for obj in source_scene.objects}
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    record = {'revision': 'V2', 'run_id': run_id, 'fuentes': provenance, 'vistas': [],
              'nota': 'Materiales opacos neutros y mallas analíticas temporales; no certifica coincidencia con planos.',
              'fecha_utc': datetime.now(timezone.utc).isoformat()}
    for spec in requested:
        # A disposable scene keeps lights, world, render options and clipping
        # completely isolated from the photographic model and its saved file.
        stage = bpy.data.scenes.new('__CONTROL_V2_'+spec['id']+'_'+run_id)
        start = time.monotonic()
        try:
            mats = materials(stage)
            mode = spec['id'] if not spec.get('seccion_solicitada') else 'SECCION'
            selected = selected_geometry(source_scene, mode)
            meshes = copy_geometry(stage, selected, depsgraph, mats, spec.get('corte'))
            if spec.get('seccion_solicitada'):
                section_frame(spec, meshes)
            camera_obj, right, up = camera(stage, spec)
            configure(stage, spec, args)
            image_path = OUTPUT/(spec['nombre']+'.png')
            stage.render.filepath = str(image_path)
            print('INICIO_CONTROL_VISUAL_V2', spec['id'], str(image_path), flush=True)
            bpy.ops.render.render(write_still=True, scene=stage.name)
            if not image_path.is_file():
                raise RuntimeError('El motor no produjo la imagen esperada: '+str(image_path))
            x, y = spec['resolucion_px']
            width = spec['ortho_scale_m']; height = width*y/x
            item = {'id': spec['id'], 'nombre': spec['nombre'], 'png': relative(image_path),
                    'png_sha256': sha256(image_path), 'modelo_sha256': provenance['modelo_sha256'],
                    'planta_final_sha256': provenance['planta_final_sha256'],
                    'motor': args.engine, 'samples': args.samples if args.engine == 'CYCLES' else None,
                    'resolucion_px': [x, y], 'camara_posicion_m': list(camera_obj.location),
                    'camara_objetivo_m': spec['objetivo_m'], 'imagen_derecha_m': right, 'imagen_arriba_m': up,
                    'viewport_ancho_m': width, 'viewport_alto_m': height,
                    'corte': {'eje': spec['corte'][0], 'estacion_m': spec['corte'][1],
                              'se_elimina_lado_positivo': spec['corte'][2]} if spec.get('corte') else None,
                    'fuente_estacion': spec.get('fuente_estacion'), 'nota': spec['nota'],
                    'objetos_origen': [obj.name for obj in selected], 'mallas_visibles_analiticas': len(meshes),
                    'segundos': round(time.monotonic()-start, 3),
                    'proyeccion_pixel': 'u=(dot(P-objetivo,derecha)/ancho+0.5)*resX; v=(0.5-dot(P-objetivo,arriba)/alto)*resY'}
            record['vistas'].append(item)
        finally:
            cleanup(stage)
        # Write only this invocation. Never append or reuse inherited V1 entries.
        record_path = OUTPUT/('registro_v2_'+run_id+'.json')
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        (OUTPUT/'registro_v2.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    if {scene.name for scene in bpy.data.scenes} != initial_scene_names:
        raise RuntimeError('Una escena temporal no se ha retirado.')
    if {obj.name for obj in source_scene.objects} != initial_object_names:
        raise RuntimeError('La lista de objetos de la escena original ha cambiado.')
    if sha256(Path(bpy.data.filepath)) != provenance['modelo_sha256']:
        raise RuntimeError('El archivo .blend de origen cambió durante esta ejecución.')
    print('CONTROL_VISUAL_V2_TERMINADO', len(record['vistas']), 'vistas; modelo de origen sin guardar cambios.', flush=True)


if __name__ == '__main__':
    main()
