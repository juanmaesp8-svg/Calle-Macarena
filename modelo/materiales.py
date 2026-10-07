"""Materiales métricos y luz reproducible para la reconstrucción de Calle Macarena.

Blender 4.3 / Cycles. HDRIs fotográficos CC0 locales y empaquetados; materiales
PBR métricos, sin cambios geométricos ni red durante creación/render.
Los acabados y la orientación del sol son decisiones de visualización; no son
dimensiones o datos constructivos extraídos del proyecto básico.
"""

import math
from pathlib import Path
import bpy

ASSET_ROOT = Path(__file__).resolve().parent.parent / 'assets'


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


def _math(material, operation, first, second=None, location=(-400, 0)):
    node = material.node_tree.nodes.new('ShaderNodeMath')
    node.operation = operation
    node.location = location
    for index, source in enumerate((first, second)):
        if source is None:
            continue
        if isinstance(source, (int, float)):
            node.inputs[index].default_value = source
        else:
            material.node_tree.links.new(source, node.inputs[index])
    return node.outputs[0]


def _mix_color(material, factor, a, b, location=(0, 200)):
    node = material.node_tree.nodes.new('ShaderNodeMixRGB')
    node.blend_type = 'MIX'
    node.location = location
    if isinstance(factor, (int, float)):
        node.inputs[0].default_value = factor
    else:
        material.node_tree.links.new(factor, node.inputs[0])
    for index, source in enumerate((a, b), 1):
        if isinstance(source, tuple):
            node.inputs[index].default_value = (*source[:3], 1)
        else:
            material.node_tree.links.new(source, node.inputs[index])
    return node.outputs['Color']


def _metric_vector(material, axes=('X', 'Y', 'Z'), periods=(1.0, 1.0, 1.0)):
    """World metric mapping, independent of mesh UVs or object transforms."""
    xyz = material.node_tree.nodes.new('ShaderNodeSeparateXYZ')
    material.node_tree.links.new(_position(material), xyz.inputs[0])
    vector = material.node_tree.nodes.new('ShaderNodeCombineXYZ')
    for destination, source, pitch in zip(('X', 'Y', 'Z'), axes, periods):
        coordinate = _math(material, 'DIVIDE', xyz.outputs[source], pitch)
        material.node_tree.links.new(coordinate, vector.inputs[destination])
    return vector.outputs[0]


def _photo_map(material, asset, role, vector, box=False):
    """Load and pack the locally licensed, photographic ambientCG maps.

    Original KTX2 and decoded PNG checksums are in assets/licencias. The
    supplied 512 px maps provide photographic mesostructure; microdetail is
    combined procedurally, at real metric scales, without mesh displacement.
    """
    path = ASSET_ROOT / 'texturas' / 'ambientcg' / asset / f'{asset}_1K-PNG_{role}.png'
    if not path.is_file():
        raise FileNotFoundError(f'Mapa PBR CC0 necesario: {path}')
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = 'sRGB' if role == 'Color' else 'Non-Color'
    image.pack()
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    node.extension = 'REPEAT'
    node.interpolation = 'Linear'
    node.projection = 'BOX' if box else 'FLAT'
    node.projection_blend = 0.18 if box else 0.0
    node.label = f'Fotografía CC0 ambientCG · {asset} · {role}'
    material.node_tree.links.new(vector, node.inputs['Vector'])
    material['fuente_PBR'] = f'ambientCG / Lennart Demes, {asset}, CC0; mapa original + SHA en assets/licencias'
    return node.outputs['Color']


def _range(material, source, low, high, from_low=0.0, from_high=1.0):
    node = material.node_tree.nodes.new('ShaderNodeMapRange')
    node.clamp = True
    material.node_tree.links.new(source, node.inputs['Value'])
    for key, value in (('From Min', from_low), ('From Max', from_high),
                       ('To Min', low), ('To Max', high)):
        node.inputs[key].default_value = value
    return node.outputs['Result']


def _plaster(name, exterior=True):
    mat, shader = _material(name, (0.78, 0.775, 0.766), 0.78)
    position = _position(mat)
    photograph = _photo_map(mat, 'Plaster001', 'Color', _metric_vector(mat, periods=(1.6,)*3), True)
    color = _ramp(mat, photograph, (0.742, 0.738, 0.728), (0.802, 0.797, 0.788))
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    relief = _photo_map(mat, 'Plaster001', 'Displacement', _metric_vector(mat, periods=(1.6,)*3), True)
    render_grain = _noise(mat, position, 145.0, 3.5, location=(-540, -170))
    pores = _noise(mat, position, 540.0, 2.0, location=(-540, -430))
    photo_grain = _bump(mat, shader, relief, 0.00045 if exterior else 0.00012, 0.35)
    grain = _bump(mat, shader, render_grain.outputs['Fac'], 0.00028 if exterior else 0.00010,
                  0.30, normal=photo_grain.outputs['Normal'])
    _bump(mat, shader, pores.outputs['Fac'], 0.00015 if exterior else 0.00006, 0.22,
          normal=grain.outputs['Normal'])
    roughness = _photo_map(mat, 'Plaster001', 'Roughness', _metric_vector(mat, periods=(1.6,)*3), True)
    mat.node_tree.links.new(_range(mat, roughness, 0.68, 0.86), shader.inputs['Roughness'])
    shader.inputs['Specular IOR Level'].default_value = 0.24
    mat['microrelieve_m'] = 'Fotografía 0.45 mm + grano fino 0.28 mm + poro 0.15 mm; solo normal de sombreado.'
    return mat


def _porcelain(name, tile=0.9, interior=False):
    base = (0.60, 0.58, 0.54) if interior else (0.69, 0.644, 0.561)
    mat, shader = _material(name, base, 0.44 if interior else 0.52)
    position = _position(mat)
    xyz = mat.node_tree.nodes.new('ShaderNodeSeparateXYZ')
    mat.node_tree.links.new(position, xyz.inputs[0])
    xyz.location = (-850, 200)
    masks, cell = [], []
    # Explicit metric modulo, so the repeat pitch is exactly 0.90 m in X/Y.
    for axis in ('X', 'Y'):
        coordinate = xyz.outputs[axis]
        modulo = _math(mat, 'FLOORED_MODULO', coordinate, tile)
        mirrored = _math(mat, 'SUBTRACT', tile, modulo)
        distance = _math(mat, 'MINIMUM', modulo, mirrored)
        masks.append(_math(mat, 'LESS_THAN', distance, 0.0015))
        cell.append(_math(mat, 'FLOOR', _math(mat, 'DIVIDE', coordinate, tile)))
    joint = _math(mat, 'MAXIMUM', masks[0], masks[1])
    combine = mat.node_tree.nodes.new('ShaderNodeCombineXYZ')
    mat.node_tree.links.new(cell[0], combine.inputs['X'])
    mat.node_tree.links.new(cell[1], combine.inputs['Y'])
    piece = mat.node_tree.nodes.new('ShaderNodeTexWhiteNoise')
    piece.noise_dimensions = '3D'
    mat.node_tree.links.new(combine.outputs['Vector'], piece.inputs['Vector'])
    tile_tint = _ramp(mat, piece.outputs['Value'], tuple(v * 0.974 for v in base),
                      tuple(v * 1.022 for v in base))
    cloud = _noise(mat, position, 22.0, 4.0, location=(-500, 480))
    cloud_tint = _ramp(mat, cloud.outputs['Fac'], tuple(v * 0.978 for v in base),
                       tuple(v * 1.020 for v in base), (-160, 460))
    detail = _mix_color(mat, cloud.outputs['Fac'], tile_tint.outputs['Color'], cloud_tint.outputs['Color'])
    photograph_vector = _metric_vector(mat, periods=(tile, tile, tile))
    photograph = _photo_map(mat, 'Marble015', 'Color', photograph_vector)
    mineral = _ramp(mat, photograph, tuple(v * 0.94 for v in base), tuple(v * 1.025 for v in base))
    detail = _mix_color(mat, 0.75, detail, mineral.outputs['Color'])
    final_color = _mix_color(mat, joint, detail, (0.44, 0.41, 0.355), (220, 250))
    mat.node_tree.links.new(final_color, shader.inputs['Base Color'])
    pores = _noise(mat, position, 360, 2, location=(-520, -280))
    photo_relief = _photo_map(mat, 'Marble015', 'Displacement', photograph_vector)
    fine_relief = _bump(mat, shader, photo_relief, 0.00009, 0.25)
    fine = _bump(mat, shader, pores.outputs['Fac'], 0.00010, 0.24, normal=fine_relief.outputs['Normal'])
    _bump(mat, shader, joint, 0.00135, 0.70, True, fine.outputs['Normal'])
    shader.inputs['Specular IOR Level'].default_value = 0.38
    roughness = _photo_map(mat, 'Marble015', 'Roughness', photograph_vector)
    mat.node_tree.links.new(_range(mat, roughness, 0.28 if interior else 0.43,
                                 0.43 if interior else 0.58), shader.inputs['Roughness'])
    mat['despiece'] = f'{tile:.2f} × {tile:.2f} m de paso, junta 3 mm; elección de acabado.'
    mat['periodo_x_m'] = tile
    mat['periodo_y_m'] = tile
    mat['junta_ancho_m'] = 0.003
    return mat


def _wood(name, vertical=True):
    mat, shader = _material(name, (0.46, 0.35, 0.22), 0.48)
    # Source photograph grain runs in V. On the east-facing facade this maps
    # exactly to Z; on horizontal furniture it maps to X. No UV assumptions.
    vector = _metric_vector(mat, ('Y', 'Z', 'X') if vertical else ('Y', 'X', 'Z'),
                             (0.72, 2.60, 1.0))
    photo = _photo_map(mat, 'Wood058', 'Color', vector)
    gamma = mat.node_tree.nodes.new('ShaderNodeGamma')
    gamma.inputs['Gamma'].default_value = 0.76
    mat.node_tree.links.new(photo, gamma.inputs['Color'])
    neutral = mat.node_tree.nodes.new('ShaderNodeHueSaturation')
    neutral.inputs['Saturation'].default_value = 0.72
    neutral.inputs['Value'].default_value = 1.18
    mat.node_tree.links.new(gamma.outputs['Color'], neutral.inputs['Color'])
    color = neutral.outputs['Color']
    relief = _photo_map(mat, 'Wood058', 'Displacement', vector)
    grain = _bump(mat, shader, relief, 0.00028, 0.38)
    fine = _noise(mat, _position(mat, (35, 35, 0.12) if vertical else (0.12, 35, 35)), 4.0, 3.0)
    _bump(mat, shader, fine.outputs['Fac'], 0.00008, 0.24, normal=grain.outputs['Normal'])
    if vertical:
        xyz = mat.node_tree.nodes.new('ShaderNodeSeparateXYZ')
        mat.node_tree.links.new(_position(mat), xyz.inputs[0])
        seam = _math(mat, 'LESS_THAN', _math(mat, 'FLOORED_MODULO', xyz.outputs['Y'], 0.12), 0.0016)
        color = _mix_color(mat, seam, color, (0.13, 0.093, 0.050))
        _bump(mat, shader, seam, 0.00065, 0.45, True, grain.outputs['Normal'])
        mat['despiece_decorativo'] = 'Tablas verticales de acabado: paso 0.12 m; junta visual 1.6 mm. Sin modificar huecos/masa.'
    mat.node_tree.links.new(color, shader.inputs['Base Color'])
    shader.inputs['Coat Weight'].default_value = 0.08
    shader.inputs['Coat Roughness'].default_value = 0.38
    roughness = _photo_map(mat, 'Wood058', 'Roughness', vector)
    mat.node_tree.links.new(_range(mat, roughness, 0.39, 0.57), shader.inputs['Roughness'])
    mat['orientacion_veta'] = 'Z vertical' if vertical else 'X horizontal'
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
    mat, shader = _material('Jardín · césped artificial de fibra corta', (0.037, 0.158, 0.030), 0.73)
    position = _position(mat, (1.0, 0.35, 0.03))
    variation = _noise(mat, position, 190.0, 2.0)
    color = _ramp(mat, variation.outputs['Fac'], (0.028, 0.130, 0.022), (0.055, 0.192, 0.040))
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    fibers = _noise(mat, _position(mat, (1, 0.22, 0.015)), 750, 3, location=(-500, -200))
    _bump(mat, shader, fibers.outputs['Fac'], 0.0035, 0.45)
    shader.inputs['IOR'].default_value = 1.49
    shader.inputs['Specular IOR Level'].default_value = 0.36
    shader.inputs['Sheen Weight'].default_value = 0.22
    shader.inputs['Sheen Roughness'].default_value = 0.54
    shader.inputs['Anisotropic'].default_value = 0.20
    mat['tipo_cesped'] = 'ARTIFICIAL; fibra corta. Sin moteado macroscópico ni cambios al jardín.'
    mat['fibra_textura_m'] = '1.3–5.3 mm de variación; microrelieve visual 3.5 mm.'
    return mat


def _fabric(name, color, sheets=False):
    mat, shader = _material(name, color, 0.89 if sheets else 0.80)
    position = _position(mat)
    wave_a = mat.node_tree.nodes.new('ShaderNodeTexWave')
    wave_b = mat.node_tree.nodes.new('ShaderNodeTexWave')
    wave_c = mat.node_tree.nodes.new('ShaderNodeTexWave')
    for wave, direction in ((wave_a, 'X'), (wave_b, 'Y'), (wave_c, 'Z')):
        wave.wave_type = 'BANDS'
        wave.bands_direction = direction
        wave.inputs['Scale'].default_value = 470.0 if sheets else 310.0
        wave.inputs['Distortion'].default_value = 0.18
        wave.inputs['Detail'].default_value = 2
        mat.node_tree.links.new(position, wave.inputs['Vector'])
    xy = _math(mat, 'MULTIPLY', wave_a.outputs['Fac'], wave_b.outputs['Fac'])
    xz = _math(mat, 'MULTIPLY', wave_a.outputs['Fac'], wave_c.outputs['Fac'])
    yz = _math(mat, 'MULTIPLY', wave_b.outputs['Fac'], wave_c.outputs['Fac'])
    weave = _math(mat, 'MULTIPLY', _math(mat, 'ADD', _math(mat, 'ADD', xy, xz), yz), 1 / 3)
    _bump(mat, shader, weave, 0.00013 if sheets else 0.00028, 0.44)
    tint = _ramp(mat, weave, tuple(v * 0.92 for v in color), tuple(v * 1.035 for v in color))
    mat.node_tree.links.new(tint.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Sheen Weight'].default_value = 0.25
    shader.inputs['Sheen Roughness'].default_value = 0.70
    if not sheets:
        aplicar_lino_fotografico(mat, color, 0.16)
    return mat


def _principled(material):
    material.use_nodes = True
    shader = material.node_tree.nodes.get('PBR')
    if shader is None or shader.bl_idname != 'ShaderNodeBsdfPrincipled':
        shader = next((n for n in material.node_tree.nodes
                       if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
    if shader is None:
        raise ValueError(f'{material.name}: falta shader Principled PBR')
    return shader


def aplicar_lino_fotografico(material, color=None, escala_m=0.16):
    """Share licensed photographic weave across interior/exterior upholstery.

    Colour is linear RGB; the photographic structure is recoloured rather
    than imposing the source fabric's rust-red dye. Relief is shading only.
    """
    shader = _principled(material)
    color = tuple(color or shader.inputs['Base Color'].default_value[:3])
    vector = _metric_vector(material, periods=(escala_m,)*3)
    photograph = _photo_map(material, 'Fabric040', 'Color', vector, True)
    normalized = _range(material, photograph, 0.0, 1.0, 0.015, 0.30)
    tint = _ramp(material, normalized, tuple(v * 0.82 for v in color),
                 tuple(min(v * 1.075, 0.90) for v in color))
    material.node_tree.links.new(tint.outputs['Color'], shader.inputs['Base Color'])
    height = _photo_map(material, 'Fabric040', 'Displacement', vector, True)
    photo_bump = _bump(material, shader, height, 0.00022, 0.56)
    fine = _noise(material, _position(material), 1700, 2)
    _bump(material, shader, fine.outputs['Fac'], 0.000035, 0.22,
          normal=photo_bump.outputs['Normal'])
    roughness = _photo_map(material, 'Fabric040', 'Roughness', vector, True)
    material.node_tree.links.new(_range(material, roughness, 0.79, 0.94), shader.inputs['Roughness'])
    shader.inputs['Sheen Weight'].default_value = 0.34
    shader.inputs['Sheen Roughness'].default_value = 0.78
    shader.inputs['Specular IOR Level'].default_value = 0.19
    shader.inputs['Coat Weight'].default_value = 0.0
    material.diffuse_color = (*color, 1)
    material['escala_lino_m'] = escala_m
    material['microrelieve_lino_m'] = 0.00022
    return material


def aplicar_madera_fotografica(material, eje_veta='Y', tono=None):
    """Apply genuine wood grain to a Principled material, in a world axis."""
    shader = _principled(material)
    if eje_veta not in ('X', 'Y', 'Z'):
        raise ValueError('eje_veta debe ser X, Y o Z')
    across = 'X' if eje_veta == 'Y' else 'Y'
    third = next(a for a in ('X', 'Y', 'Z') if a not in (eje_veta, across))
    vector = _metric_vector(material, (across, eje_veta, third), (0.72, 2.60, 1.0))
    photograph = _photo_map(material, 'Wood058', 'Color', vector)
    if tono is None:
        gamma = material.node_tree.nodes.new('ShaderNodeGamma')
        gamma.inputs['Gamma'].default_value = 0.76
        material.node_tree.links.new(photograph, gamma.inputs['Color'])
        hue = material.node_tree.nodes.new('ShaderNodeHueSaturation')
        hue.inputs['Saturation'].default_value = 0.72
        hue.inputs['Value'].default_value = 1.18
        material.node_tree.links.new(gamma.outputs[0], hue.inputs['Color'])
        color = hue.outputs['Color']
    else:
        color = _ramp(material, photograph, tuple(v * 0.76 for v in tono),
                      tuple(min(v * 1.20, 0.9) for v in tono)).outputs['Color']
    material.node_tree.links.new(color, shader.inputs['Base Color'])
    height = _photo_map(material, 'Wood058', 'Displacement', vector)
    _bump(material, shader, height, 0.00028, 0.38)
    roughness = _photo_map(material, 'Wood058', 'Roughness', vector)
    material.node_tree.links.new(_range(material, roughness, 0.39, 0.57), shader.inputs['Roughness'])
    shader.inputs['Coat Weight'].default_value = 0.08
    shader.inputs['Coat Roughness'].default_value = 0.38
    material['orientacion_veta'] = eje_veta
    return material


def aplicar_mineral_fotografico(material, color=None, escala_m=0.90):
    """Subtle cream mineral mesostructure for quartz / ceramic decoration."""
    shader = _principled(material)
    color = tuple(color or shader.inputs['Base Color'].default_value[:3])
    vector = _metric_vector(material, periods=(escala_m,)*3)
    photograph = _photo_map(material, 'Marble015', 'Color', vector, True)
    tint = _ramp(material, photograph, tuple(v * 0.94 for v in color),
                 tuple(min(v * 1.035, 0.9) for v in color))
    material.node_tree.links.new(tint.outputs['Color'], shader.inputs['Base Color'])
    height = _photo_map(material, 'Marble015', 'Displacement', vector, True)
    _bump(material, shader, height, 0.00007, 0.2)
    roughness = _photo_map(material, 'Marble015', 'Roughness', vector, True)
    material.node_tree.links.new(_range(material, roughness, 0.24, 0.38), shader.inputs['Roughness'])
    return material


def _painted_metal(name, color, roughness=0.29):
    # Opaque powder coat is a dielectric layer over aluminium, not bare metal.
    mat, shader = _material(name, color, roughness, 0.02)
    shader.inputs['Coat Weight'].default_value = 0.15
    shader.inputs['Coat Roughness'].default_value = 0.30
    grain = _noise(mat, _position(mat), 1700, 2)
    _bump(mat, shader, grain.outputs['Fac'], 0.000045, 0.26)
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
    mat, shader = _material('Mobiliario · roble claro patas verticales', (0.46, 0.35, 0.22), 0.48)
    mats['madera_patas'] = aplicar_madera_fotografica(mat, 'Z')
    mats['madera_pergola'] = _wood('Pérgola · madera clara')
    mats['carpinteria_antracita'] = _painted_metal('Carpinterías · aluminio lacado antracita', (0.017, 0.021, 0.025))
    mats['metal_pergola'] = _painted_metal('Pérgola · metal lacado antracita', (0.022, 0.026, 0.029), 0.33)
    mat, shader = _material('Vidrio · neutro transparente IOR 1.52', (1.0, 1.0, 1.0), 0.006)
    shader.inputs['Transmission Weight'].default_value = 1.0
    shader.inputs['IOR'].default_value = 1.52
    # A parallel 8 mm clear glazing plate transmits direct solar irradiance
    # almost straight through. Cycles' disabled refractive caustics otherwise
    # treats that pane as an opaque obstruction to the Sun shadow ray. This
    # radiative shortcut affects ONLY the direct shadow test; camera rays,
    # transmission paths and reflections retain the full refractive BSDF.
    # 0.96 per surface -> 0.9216 through the two faces, an explicit visual
    # material assumption rather than a specified architectural glass product.
    paths = mat.node_tree.nodes.new('ShaderNodeLightPath')
    paths.label = 'Solo prueba de sombra solar directa'
    direct = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
    direct.inputs['Color'].default_value = (0.96, 0.96, 0.96, 1.0)
    direct.label = 'Transmisión recta de irradiancia: 96% por cara'
    mix = mat.node_tree.nodes.new('ShaderNodeMixShader')
    mat.node_tree.links.new(paths.outputs['Is Shadow Ray'], mix.inputs[0])
    mat.node_tree.links.new(shader.outputs['BSDF'], mix.inputs[1])
    mat.node_tree.links.new(direct.outputs['BSDF'], mix.inputs[2])
    output = next(n for n in mat.node_tree.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    mat.node_tree.links.new(mix.outputs[0], output.inputs['Surface'])
    mat['transmision_sombra_por_cara'] = 0.96
    mat['transmision_solar_dos_caras_visual'] = 0.9216
    mat['aproximacion_solar'] = ('Solo Is Shadow Ray: transmisión recta de placa paralela de vidrio '
                                'claro; cámara/reflexión/refracción conservan Principled IOR1.52. '
                                'Hipótesis material de visualización, no vidrio especificado en PDF.')
    mats['vidrio'] = mat
    mat, shader = _material('Piscina · superficie de agua', (0.88, 0.965, 0.985), 0.026)
    shader.inputs['Transmission Weight'].default_value = 1.0
    shader.inputs['IOR'].default_value = 1.333
    position = _position(mat)
    ripples = _noise(mat, _position(mat, (1.0, 0.62, 0.0)), 6.5, 3.0, 0.55)
    broad = _bump(mat, shader, ripples.outputs['Fac'], 0.0011, 0.22)
    surface = _noise(mat, _position(mat, (0.42, 1.0, 0.0)), 24.0, 2.5, 0.55)
    _bump(mat, shader, surface.outputs['Fac'], 0.00016, 0.18, normal=broad.outputs['Normal'])
    mat['ondas_visualizacion_m'] = 'Ondas de normal 1.1 mm + microondas 0.16 mm; sin modificar perímetro ni definir fondo.'
    mat['advertencia_geometria'] = 'El material no define fondo, profundidad ni nivel de agua.'
    mats['agua'] = mat
    mats['grava'] = _gravel()
    mats['cesped'] = _grass()
    mat, shader = _material('Jardín · fibra corta de césped artificial', (0.040, 0.165, 0.027), 0.64)
    fiber_tint = _noise(mat, _position(mat), 125, 2)
    tint = _ramp(mat, fiber_tint.outputs['Fac'], (0.028, 0.128, 0.018), (0.056, 0.196, 0.038))
    mat.node_tree.links.new(tint.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['IOR'].default_value = 1.49
    shader.inputs['Sheen Weight'].default_value = 0.30
    shader.inputs['Sheen Roughness'].default_value = 0.54
    shader.inputs['Subsurface Weight'].default_value = 0.018
    shader.inputs['Subsurface Scale'].default_value = 0.001
    mat['procedencia'] = 'Polímero de césped artificial; para fibras de visualización sobre huella existente.'
    mats['cesped_fibra'] = mat
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
    mats['tejido'] = _fabric('Interior · lino beige neutro', (0.50, 0.48, 0.435))
    mats['tejido_tapizado'] = mats['tejido']
    mats['tejido_sabanas'] = _fabric('Interior · algodón blanco roto', (0.77, 0.76, 0.735), True)
    mats['madera_mesa'] = _wood('Mobiliario · roble claro horizontal', False)
    mats['metal_mobiliario'] = _painted_metal('Mobiliario · metal negro satinado', (0.015, 0.017, 0.018), 0.35)
    mat, shader = _material('Interior · piel clara mate', (0.47, 0.44, 0.39), 0.50)
    pores = _noise(mat, _position(mat), 1300, 3)
    _bump(mat, shader, pores.outputs['Fac'], 0.00025, 0.32)
    shader.inputs['Coat Weight'].default_value = 0.08
    mats['cuero_claro'] = mat
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
    """Photographic HDRI fill + physical sun; no geometry changes.

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
    sky.sun_elevation = math.radians(28.0 if mode == 'day' else 5.5)
    sky.sun_rotation = math.radians(105.0 if mode == 'day' else 330.0)
    sky.altitude = 35.0
    sky.air_density = 1.0
    sky.dust_density = 0.55 if mode == 'day' else 0.85
    sky.ozone_density = 1.0
    sky.location = (-500, 0)
    background = nodes.new('ShaderNodeBackground')
    background.label = 'Cielo físico visible; no panorama ajeno como fondo'
    background.inputs['Strength'].default_value = 0.24 if mode == 'day' else 0.14
    background.location = (-50, 300)
    output = nodes.new('ShaderNodeOutputWorld')
    output.location = (50, 0)
    world.node_tree.links.new(sky.outputs['Color'], background.inputs['Color'])
    hdri_name = 'royal_esplanade_1k.hdr' if mode == 'day' else 'venice_sunset_1k.hdr'
    path = ASSET_ROOT / 'hdri' / hdri_name
    packed_hdri = bpy.data.images.get(hdri_name)
    if path.is_file() or (packed_hdri and packed_hdri.packed_file):
        environment = nodes.new('ShaderNodeTexEnvironment')
        environment.image = (bpy.data.images.load(str(path), check_existing=True)
                             if path.is_file() else packed_hdri)
        environment.image.pack()
        environment.label = 'HDRI fotográfico CC0 Poly Haven / espejo Three.js'
        environment.location = (-550, -200)
        coordinates = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Rotation'].default_value[2] = math.radians(35 if mode == 'day' else 155)
        world.node_tree.links.new(coordinates.outputs['Generated'], mapping.inputs['Vector'])
        world.node_tree.links.new(mapping.outputs['Vector'], environment.inputs['Vector'])
        # HDRI sun is clamped in the ambient layer, avoiding a second solar
        # source in addition to the explicit Sun lamp. Colour/cloud detail is
        # retained for fill and glossy reflections. No exposure-burned backdrop.
        ambient = nodes.new('ShaderNodeVectorMath')
        ambient.operation = 'MINIMUM'
        ambient.inputs[1].default_value = (8.0, 8.0, 8.0)
        world.node_tree.links.new(environment.outputs['Color'], ambient.inputs[0])
        fill = nodes.new('ShaderNodeBackground')
        fill.inputs['Strength'].default_value = 0.42 if mode == 'day' else 0.22
        fill.location = (-40, -200)
        world.node_tree.links.new(ambient.outputs['Vector'], fill.inputs['Color'])
        paths = nodes.new('ShaderNodeLightPath')
        visible = nodes.new('ShaderNodeMath')
        visible.operation = 'MAXIMUM'
        world.node_tree.links.new(paths.outputs['Is Camera Ray'], visible.inputs[0])
        world.node_tree.links.new(paths.outputs['Is Transmission Ray'], visible.inputs[1])
        # Reflections must show the model's garden and physical sky; the
        # foreign buildings in a photographic lighting panorama are not site
        # evidence. HDRI is used for indirect diffuse illumination only.
        sky_paths = nodes.new('ShaderNodeMath')
        sky_paths.operation = 'MAXIMUM'
        world.node_tree.links.new(visible.outputs[0], sky_paths.inputs[0])
        world.node_tree.links.new(paths.outputs['Is Glossy Ray'], sky_paths.inputs[1])
        mix = nodes.new('ShaderNodeMixShader')
        mix.location = (260, 0)
        world.node_tree.links.new(sky_paths.outputs[0], mix.inputs[0])
        world.node_tree.links.new(fill.outputs['Background'], mix.inputs[1])
        world.node_tree.links.new(background.outputs['Background'], mix.inputs[2])
        world.node_tree.links.new(mix.outputs[0], output.inputs['Surface'])
        world['fuente_hdri'] = 'https://polyhaven.com/a/' + hdri_name.replace('_1k.hdr', '')
        world['licencia_hdri'] = 'CC0; consulta assets/licencias/polyhaven_cc0_texto_oficial.json'
    else:
        # Supported local fallback: no network access is needed at runtime.
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
    # Nishita's RNA sun_rotation is clockwise from world +Y (Cycles maps it
    # internally to 2*pi-rotation then +pi/2). Match the explicit Sun to that
    # same convention. 125 degrees places the source at +X/-Y, illuminating
    # the long terrace facade; it is a visual coordinate choice, not north.
    direction = Vector((math.cos(elevation) * math.sin(azimuth),
                        math.cos(elevation) * math.cos(azimuth), math.sin(elevation)))
    sun.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    data.energy = 3.0 if mode == 'day' else 1.05
    data.angle = math.radians(0.53 if mode == 'day' else 0.62)
    data.color = (1.0, 0.975, 0.93) if mode == 'day' else (1.0, 0.64, 0.38)
    sun['orientacion'] = 'Elección de iluminación; norte geográfico no confirmado'
    sun['modo'] = mode
    sun['rotacion_coordenadas_grados'] = math.degrees(azimuth)
    sun['convencion_rotacion'] = 'Horario desde +Y mundial; no norte geográfico confirmado'
    sun['direccion_hacia_fuente'] = tuple(direction)
    # V1's orange glazing mostly came from amber interior area lamps, rather
    # than the almost neutral glass itself. In daytime daylight dominates;
    # decorative lighting is enabled for the evening photograph only.
    for obj in scene.objects:
        if obj.type != 'LIGHT' or obj == sun:
            continue
        if not obj.name.startswith(('Luz_interior_', 'Luz_exterior_')):
            continue
        lamp = obj.data
        if 'energia_base_visualizacion' not in lamp:
            lamp['energia_base_visualizacion'] = lamp.energy
        base_energy = lamp['energia_base_visualizacion']
        if obj.name.startswith('Luz_exterior_'):
            lamp.energy = 0.0 if mode == 'day' else base_energy
            lamp.color = (1.0, 0.78, 0.57)
        else:
            lamp.energy = base_energy * 0.18 if mode == 'day' else base_energy
            lamp.color = (1.0, 0.94, 0.86) if mode == 'day' else (1.0, 0.76, 0.54)
        lamp['criterio_luz_v2'] = 'Luz neutra tenue de día; cálida de tarde. Sin cambios de posición.'
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    scene.view_settings.exposure = 0.20 if mode == 'day' else 0.25
    scene.view_settings.gamma = 1.0
    scene.render.engine = 'CYCLES'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.008
    scene.cycles.samples = 384 if mode == 'day' else 512
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 14
    scene.cycles.diffuse_bounces = 5
    scene.cycles.glossy_bounces = 6
    scene.cycles.transmission_bounces = 12
    scene.cycles.transparent_max_bounces = 16
    scene.cycles.volume_bounces = 0
    scene.cycles.sample_clamp_indirect = 16.0
    scene.cycles.use_light_tree = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '16'
    world['nota'] = ('HDRI CC0 fotográfico para relleno difuso + sol físico; cielo Nishita a cámara y reflexión. '
                     'Orientación artística de luz, sin estudio solar fechado ni norte confirmado.')
    world['revision_visual'] = 'V3 · mañana mediterránea; materiales fotográficos CC0'
    return sun


if __name__ == '__main__':
    make_materials()
    setup_lighting(bpy.context.scene)
    print('Materiales procedurales y luz preparados.')
