"""Materiales métricos y luz reproducible para la reconstrucción de Calle Macarena.

Blender 4.3 / Cycles. Sin imágenes externas, sin cambios geométricos y sin
dependencias de red. Las texturas se expresan en metros usando Geometry.Position.
Los acabados y la orientación del sol son decisiones de visualización; no son
dimensiones o datos constructivos extraídos del proyecto básico.
"""

import math
import bpy


def _material(name, color, roughness=0.5, metallic=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.name = 'PBR'
    shader.label = 'Acabado físico'
    shader.location = (500, 80)
    shader.inputs['Base Color'].default_value = (*color[:3], 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 80)
    material.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    material.diffuse_color = (*color[:3], 1)
    material.roughness = roughness
    material.metallic = metallic
    material['unidad_texturas'] = 'm'
    material['procedencia'] = 'Acabado de visualización, no dimensión del proyecto'
    return material, shader


def _position(material, scale=None):
    nodes = material.node_tree.nodes
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.location = (-1000, 80)
    geometry.label = 'Posición mundial, metros'
    if scale is None:
        return geometry.outputs['Position']
    multiply = nodes.new('ShaderNodeVectorMath')
    multiply.operation = 'MULTIPLY'
    multiply.inputs[1].default_value = scale
    multiply.location = (-810, 80)
    material.node_tree.links.new(geometry.outputs['Position'], multiply.inputs[0])
    return multiply.outputs['Vector']


def _noise(material, vector, scale, detail=2.0, roughness=0.6, location=(-560, 80)):
    noise = material.node_tree.nodes.new('ShaderNodeTexNoise')
    noise.location = location
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = detail
    noise.inputs['Roughness'].default_value = roughness
    material.node_tree.links.new(vector, noise.inputs['Vector'])
    return noise


def _ramp(material, source, low, high, location=(-160, 170)):
    ramp = material.node_tree.nodes.new('ShaderNodeValToRGB')
    ramp.location = location
    ramp.color_ramp.elements[0].position = 0.12
    ramp.color_ramp.elements[0].color = (*low[:3], 1)
    ramp.color_ramp.elements[1].position = 0.88
    ramp.color_ramp.elements[1].color = (*high[:3], 1)
    material.node_tree.links.new(source, ramp.inputs['Fac'])
    return ramp


def _bump(material, shader, source, distance, strength=0.2, invert=False, normal=None):
    bump = material.node_tree.nodes.new('ShaderNodeBump')
    bump.location = (200, -150)
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = distance
    bump.invert = invert
    material.node_tree.links.new(source, bump.inputs['Height'])
    if normal is not None:
        material.node_tree.links.new(normal, bump.inputs['Normal'])
    material.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return bump


def _plaster(name, exterior=True):
    mat, shader = _material(name, (0.77, 0.765, 0.735), 0.78)
    position = _position(mat)
    mottling = _noise(mat, position, 2.8, 2.0)
    color = _ramp(mat, mottling.outputs['Fac'], (0.745, 0.74, 0.72), (0.825, 0.82, 0.795))
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    fine = _noise(mat, position, 115.0, 3.0, location=(-540, -220))
    _bump(mat, shader, fine.outputs['Fac'], 0.0006 if exterior else 0.0003, 0.22)
    return mat


def _porcelain(name, tile=0.9, interior=False):
    mat, shader = _material(name, (0.64, 0.62, 0.575), 0.45 if interior else 0.63)
    position = _position(mat)
    brick = mat.node_tree.nodes.new('ShaderNodeTexBrick')
    brick.location = (-550, 230)
    brick.label = 'Junta de acabado; no modifica el pavimento'
    brick.offset = 0.0
    brick.offset_frequency = 1
    brick.squash = 1.0
    brick.inputs['Color1'].default_value = (0.64, 0.62, 0.575, 1)
    brick.inputs['Color2'].default_value = (0.73, 0.715, 0.67, 1)
    brick.inputs['Mortar'].default_value = (0.43, 0.425, 0.40, 1)
    brick.inputs['Scale'].default_value = 1.0
    brick.inputs['Mortar Size'].default_value = 0.0025
    brick.inputs['Mortar Smooth'].default_value = 0.001
    brick.inputs['Bias'].default_value = 0.0
    brick.inputs['Brick Width'].default_value = tile
    brick.inputs['Row Height'].default_value = tile
    mat.node_tree.links.new(position, brick.inputs['Vector'])
    mat.node_tree.links.new(brick.outputs['Color'], shader.inputs['Base Color'])
    pores = _noise(mat, position, 190, 2, location=(-520, -280))
    fine = _bump(mat, shader, pores.outputs['Fac'], 0.00035, 0.12)
    _bump(mat, shader, brick.outputs['Fac'], 0.0018, 0.5, True, fine.outputs['Normal'])
    mat['despiece'] = f'{tile:.2f} m; elección de acabado, no despiece acotado'
    return mat


def _wood(name):
    mat, shader = _material(name, (0.48, 0.295, 0.14), 0.51)
    # Small X/Y wavelength and long Z wavelength give a vertical wood grain.
    vector = _position(mat, (17.0, 17.0, 0.28))
    grain = _noise(mat, vector, 3.2, 3.0, 0.68)
    color = _ramp(mat, grain.outputs['Fac'], (0.32, 0.18, 0.075), (0.67, 0.46, 0.235))
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    _bump(mat, shader, grain.outputs['Fac'], 0.0006, 0.22)
    shader.inputs['Coat Weight'].default_value = 0.08
    shader.inputs['Coat Roughness'].default_value = 0.36
    return mat


def _gravel():
    mat, shader = _material('Cubierta · grava mineral', (0.44, 0.43, 0.39), 0.92)
    position = _position(mat)
    voronoi = mat.node_tree.nodes.new('ShaderNodeTexVoronoi')
    voronoi.location = (-540, 170)
    voronoi.voronoi_dimensions = '3D'
    voronoi.feature = 'F1'
    voronoi.distance = 'EUCLIDEAN'
    voronoi.inputs['Scale'].default_value = 53
    mat.node_tree.links.new(position, voronoi.inputs['Vector'])
    color = _ramp(mat, voronoi.outputs['Distance'], (0.245, 0.235, 0.205), (0.64, 0.625, 0.55))
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    _bump(mat, shader, voronoi.outputs['Distance'], 0.012, 0.48, True)
    return mat


def _grass():
    mat, shader = _material('Jardín · césped mediterráneo', (0.13, 0.21, 0.035), 0.94)
    position = _position(mat)
    variation = _noise(mat, position, 3.2, 2.0)
    color = _ramp(mat, variation.outputs['Fac'], (0.073, 0.142, 0.023), (0.12, 0.205, 0.039))
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    fine = _noise(mat, _position(mat, (1, 1, 0.15)), 160, 2, location=(-500, -200))
    _bump(mat, shader, fine.outputs['Fac'], 0.01, 0.3)
    return mat


def make_materials():
    """Return a Spanish/English key dictionary. Materials stay editable in Blender."""
    mats = {}
    mats['fachada_blanca'] = _plaster('Vivienda · estuco blanco')
    mats['muro_blanco'] = _plaster('Cerramiento · revoco blanco')
    mats['pared_interior'] = _plaster('Interior · pintura blanca', False)
    mats['porcelanico_exterior'] = _porcelain('Exterior · porcelánico claro mate')
    mats['suelo_interior'] = _porcelain('Interior · porcelánico neutro', 0.8, True)
    mats['madera_clara_vertical'] = _wood('Terraza · madera clara vertical')
    mats['madera_pergola'] = _wood('Pérgola · madera clara')
    mat, shader = _material('Carpinterías · aluminio antracita', (0.017, 0.021, 0.025), 0.30, 0.68)
    shader.inputs['Coat Weight'].default_value = 0.12
    mats['carpinteria_antracita'] = mat
    mat, shader = _material('Pérgola · metal antracita', (0.028, 0.031, 0.034), 0.40, 0.65)
    mats['metal_pergola'] = mat
    mat, shader = _material('Vidrio · transparente IOR 1.45', (0.97, 0.99, 1.0), 0.035)
    shader.inputs['Transmission Weight'].default_value = 1.0
    shader.inputs['IOR'].default_value = 1.45
    mats['vidrio'] = mat
    mat, shader = _material('Piscina · superficie de agua', (0.88, 0.965, 0.985), 0.05)
    shader.inputs['Transmission Weight'].default_value = 1.0
    shader.inputs['IOR'].default_value = 1.333
    position = _position(mat)
    ripples = _noise(mat, position, 13.0, 3.0, 0.55)
    _bump(mat, shader, ripples.outputs['Fac'], 0.011, 0.18)
    mat['advertencia_geometria'] = 'El material no define fondo, profundidad ni nivel de agua.'
    mats['agua'] = mat
    mats['grava'] = _gravel()
    mats['cesped'] = _grass()
    mat, shader = _material('Vegetación · hoja mediterránea', (0.10, 0.18, 0.035), 0.60)
    shader.inputs['Subsurface Weight'].default_value = 0.03
    mats['hojas'] = mat
    mat, shader = _material('Vegetación · tronco', (0.24, 0.13, 0.057), 0.85)
    texture = _noise(mat, _position(mat, (1, 1, 0.2)), 24, 2)
    _bump(mat, shader, texture.outputs['Fac'], 0.005, 0.35)
    mats['tronco'] = mat
    mat, shader = _material('Contexto · vial neutro', (0.22, 0.22, 0.215), 0.9)
    texture = _noise(mat, _position(mat), 95, 2)
    _bump(mat, shader, texture.outputs['Fac'], 0.002, 0.20)
    mats['vial'] = mat
    mat, shader = _material('Interior · tejido beige', (0.46, 0.42, 0.35), 0.88)
    mats['tejido'] = mat
    mat, shader = _material('Piscina · revestimiento claro provisional', (0.56, 0.65, 0.63), 0.5)
    mat['advertencia_geometria'] = 'Solo para geometría representada o explícitamente identificada como provisional.'
    mats['revestimiento_piscina'] = mat
    aliases = {
        'white': 'fachada_blanca', 'plaster': 'fachada_blanca', 'wall': 'muro_blanco',
        'paving': 'porcelanico_exterior', 'tile': 'porcelanico_exterior',
        'interior': 'suelo_interior', 'wood': 'madera_clara_vertical',
        'frame': 'carpinteria_antracita', 'dark': 'carpinteria_antracita',
        'glass': 'vidrio', 'water': 'agua', 'gravel': 'grava', 'grass': 'cesped',
        'leaf': 'hojas', 'trunk': 'tronco', 'road': 'vial', 'fabric': 'tejido',
        'pergola': 'metal_pergola', 'pool': 'revestimiento_piscina',
    }
    for alias, key in aliases.items():
        mats[alias] = mats[key]
    return mats


def setup_lighting(scene, mode='day'):
    """Configure Nishita sky + physical sun; does not change model geometry.

    The solar direction is a visualization choice: the PDF does not establish
    a geographic north and therefore these are not dated solar-study results.
    Returns the sun object. Calling repeatedly replaces only our own lighting.
    """
    if mode not in ('day', 'sunset'):
        raise ValueError("mode must be 'day' or 'sunset'")
    world = scene.world or bpy.data.worlds.new('Cielo mediterráneo')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes.clear()
    nodes = world.node_tree.nodes
    sky = nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_disc = False
    sky.sun_size = math.radians(0.55)
    sky.sun_elevation = math.radians(48.0 if mode == 'day' else 6.0)
    sky.sun_rotation = math.radians(315.0 if mode == 'day' else 330.0)
    sky.altitude = 35.0
    sky.air_density = 1.0
    sky.dust_density = 0.65 if mode == 'day' else 1.15
    sky.ozone_density = 1.0
    sky.location = (-500, 0)
    background = nodes.new('ShaderNodeBackground')
    background.inputs['Strength'].default_value = 0.38 if mode == 'day' else 0.20
    background.location = (-200, 0)
    output = nodes.new('ShaderNodeOutputWorld')
    output.location = (50, 0)
    world.node_tree.links.new(sky.outputs['Color'], background.inputs['Color'])
    world.node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
    light_name = 'Iluminación · sol mediterráneo'
    old = bpy.data.objects.get(light_name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.lights.new(light_name, 'SUN')
    sun = bpy.data.objects.new(light_name, data)
    collection = bpy.data.collections.get('ILUMINACION')
    if collection is None:
        collection = bpy.data.collections.new('ILUMINACION')
        scene.collection.children.link(collection)
    collection.objects.link(sun)
    elevation = sky.sun_elevation
    azimuth = sky.sun_rotation
    from mathutils import Vector
    direction = Vector((math.cos(elevation) * math.cos(azimuth),
                        math.cos(elevation) * math.sin(azimuth), math.sin(elevation)))
    sun.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    data.energy = 2.4 if mode == 'day' else 1.2
    data.angle = math.radians(0.55 if mode == 'day' else 0.72)
    data.color = (1.0, 0.935, 0.81) if mode == 'day' else (1.0, 0.51, 0.235)
    sun['orientacion'] = 'Elección de iluminación; norte geográfico no confirmado'
    sun['modo'] = mode
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    scene.view_settings.exposure = 0.1 if mode == 'day' else 0.4
    scene.view_settings.gamma = 1.0
    scene.render.engine = 'CYCLES'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.025
    scene.cycles.samples = 80 if mode == 'day' else 96
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 6
    scene.cycles.transparent_max_bounces = 8
    scene.cycles.volume_bounces = 0
    scene.cycles.sample_clamp_indirect = 5.0
    scene.cycles.use_light_tree = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    world['nota'] = 'Cielo Nishita. Atmósfera mediterránea de visualización, sin estudio solar fechado.'
    return sun


if __name__ == '__main__':
    make_materials()
    setup_lighting(bpy.context.scene)
    print('Materiales procedurales y luz preparados.')
