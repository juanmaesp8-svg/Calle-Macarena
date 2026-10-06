"""Vegetación mediterránea de visualización; geometría reproducible en metros.

API compatible con vegetacion_mobiliario.make_palm / make_olive / make_shrub.
No coloca ni transforma arquitectura, parcelas, pavimentos o polígonos de césped.
Cada función devuelve [Empty_raíz, objetos_malla...] y mantiene xy como raíz.
Las alturas y radios son envolventes del asset, no cotas del plano. Los cuatro
árboles ya existentes conservan la altura y el radio máximo del asset V1.
Todas las mallas y los materiales se crean aquí: no hay recursos externos.
"""
import hashlib
import math
import random

import bpy
from mathutils import Vector

NOTE = 'Vegetación de visualización V2; posición de raíz heredada, especie y porte no acotados.'
TAU = 2 * math.pi
# Radios V1 medidos de sus vértices; conservar el porte sin cambiar el jardín.
_SOURCE_RADII = {
    'Palmera_frente': (4.9, 2.3734788843201016),
    'Palmera_jardin_lateral': (4.25, 2.0642187903615112),
    'Olivo_trasero_derecho': (4.15, 1.8504775149211394),
    'Olivo_trasero_izquierdo': (3.7, 1.6973871119971164),
}


def _rng(name):
    return random.Random(int(hashlib.sha256(name.encode('utf-8')).hexdigest()[:8], 16))


def _collection(col):
    if isinstance(col, str):
        existing = bpy.data.collections.get(col)
        if existing is None:
            existing = bpy.data.collections.new(col)
            bpy.context.scene.collection.children.link(existing)
        return existing
    return col


def _parent(name, xy, col):
    root = bpy.data.objects.new(name, None)
    _collection(col).objects.link(root)
    root.location = (xy[0], xy[1], xy[2] if len(xy) > 2 else -0.15)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = 0.15
    root['procedencia'] = NOTE
    root['semilla_sha256'] = hashlib.sha256(name.encode()).hexdigest()[:8]
    root['geometria_asset'] = 'Procedural original; no modifica elementos arquitectónicos.'
    return root


def _mesh(name, verts, faces, col, parent, materials, indices=None, uv_vertices=None):
    mesh = bpy.data.meshes.new(name + ' · malla')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    _collection(col).objects.link(obj)
    obj.parent = parent
    obj['procedencia'] = NOTE
    for material in materials:
        mesh.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True
        if indices is not None:
            face.material_index = indices[face.index]
    if uv_vertices is not None:
        layer = mesh.uv_layers.new(name='Botánica · UV por hoja')
        # La misma UV del limbo permite nervadura y rugosidad a escala de hoja.
        for loop in mesh.loops:
            layer.data[loop.index].uv = uv_vertices[loop.vertex_index]
    return obj


def _material(name, color, roughness):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat, None
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    mat['procedencia'] = 'Material PBR procedural original V2; sin imágenes externas.'
    return mat, bsdf


def _bark(kind):
    is_palm = kind == 'palmera'
    base = (0.12, 0.073, 0.039) if is_palm else (0.105, 0.092, 0.075)
    mat, bsdf = _material('V2 botánica · corteza ' + kind, base, 0.86)
    if bsdf is None:
        return mat
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (1, 1, 0.35 if is_palm else 0.18)
    links.new(tex.outputs['Object'], mapping.inputs[0])
    coarse = nodes.new('ShaderNodeTexNoise')
    coarse.inputs['Scale'].default_value = 27 if is_palm else 18
    coarse.inputs['Detail'].default_value = 5
    coarse.inputs['Roughness'].default_value = 0.7
    links.new(mapping.outputs['Vector'], coarse.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.16
    ramp.color_ramp.elements[0].color = (*[v * 0.34 for v in base], 1)
    ramp.color_ramp.elements[1].position = 0.83
    ramp.color_ramp.elements[1].color = (*[v * 1.8 for v in base], 1)
    links.new(coarse.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    fine = nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 210
    fine.inputs['Detail'].default_value = 3
    links.new(mapping.outputs['Vector'], fine.inputs['Vector'])
    bump_fine = nodes.new('ShaderNodeBump')
    bump_fine.inputs['Strength'].default_value = 0.26
    bump_fine.inputs['Distance'].default_value = 0.0012
    links.new(fine.outputs['Fac'], bump_fine.inputs['Height'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.34
    bump.inputs['Distance'].default_value = 0.005 if is_palm else 0.007
    links.new(coarse.outputs['Fac'], bump.inputs['Height'])
    links.new(bump_fine.outputs['Normal'], bump.inputs['Normal'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['IOR'].default_value = 1.46
    return mat


def _leaf_materials(kind):
    """Haz/envés distintos, nervadura fina y transmisión de luz sobre limbos."""
    if kind == 'olivo':
        front, back = (0.049, 0.077, 0.032), (0.19, 0.225, 0.15)
        roughness, transmission = 0.52, 0.065
    elif kind == 'palmera':
        front, back = (0.026, 0.082, 0.021), (0.071, 0.14, 0.04)
        roughness, transmission = 0.48, 0.105
    else:
        front, back = (0.027, 0.071, 0.022), (0.071, 0.115, 0.039)
        roughness, transmission = 0.54, 0.075
    output = []
    for index in range(6):
        multiplier = 0.82 + index * 0.062
        front_i = tuple(c * multiplier for c in front)
        back_i = tuple(c * multiplier for c in back)
        mat, bsdf = _material(f'V2 botánica · {kind} hoja {index + 1}', front_i, roughness)
        output.append(mat)
        if bsdf is None:
            continue
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        geometry = nodes.new('ShaderNodeNewGeometry')
        sides = nodes.new('ShaderNodeMixRGB'); sides.blend_type = 'MIX'
        sides.inputs[1].default_value = (*front_i, 1)
        sides.inputs[2].default_value = (*back_i, 1)
        links.new(geometry.outputs['Backfacing'], sides.inputs[0])
        uv = nodes.new('ShaderNodeTexCoord')
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 75
        noise.inputs['Detail'].default_value = 2
        links.new(uv.outputs['UV'], noise.inputs['Vector'])
        subtle = nodes.new('ShaderNodeMixRGB'); subtle.blend_type = 'MULTIPLY'
        subtle.inputs[0].default_value = 0.12
        links.new(sides.outputs['Color'], subtle.inputs[1])
        links.new(noise.outputs['Color'], subtle.inputs[2])
        separate = nodes.new('ShaderNodeSeparateXYZ')
        links.new(uv.outputs['UV'], separate.inputs['Vector'])
        subtract = nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
        subtract.inputs[1].default_value = 0.5
        links.new(separate.outputs['X'], subtract.inputs[0])
        absolute = nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'
        links.new(subtract.outputs[0], absolute.inputs[0])
        vein = nodes.new('ShaderNodeMath'); vein.operation = 'LESS_THAN'
        vein.inputs[1].default_value = 0.020
        links.new(absolute.outputs[0], vein.inputs[0])
        strength = nodes.new('ShaderNodeMath'); strength.operation = 'MULTIPLY'
        strength.inputs[1].default_value = 0.16
        links.new(vein.outputs[0], strength.inputs[0])
        color = nodes.new('ShaderNodeMixRGB'); color.blend_type = 'SCREEN'
        links.new(strength.outputs[0], color.inputs[0])
        links.new(subtle.outputs['Color'], color.inputs[1])
        color.inputs[2].default_value = (*[c * 1.6 for c in front_i], 1)
        links.new(color.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['IOR'].default_value = 1.44
        bsdf.inputs['Coat Weight'].default_value = 0.065
        bsdf.inputs['Coat Roughness'].default_value = 0.35
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.16
        bump.inputs['Distance'].default_value = 0.00012
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        translucent = nodes.new('ShaderNodeBsdfTranslucent')
        links.new(sides.outputs['Color'], translucent.inputs['Color'])
        blend = nodes.new('ShaderNodeMixShader')
        blend.inputs[0].default_value = transmission
        links.new(bsdf.outputs['BSDF'], blend.inputs[1])
        links.new(translucent.outputs[0], blend.inputs[2])
        links.new(blend.outputs[0], nodes.get('Material Output').inputs['Surface'])
        mat['haz_enves'] = 'Verde en haz; verde claro / gris plateado en envés según especie.'
    return output


def _tube(verts, faces, centers, radii, sides=9, rough=0.0):
    offset = len(verts)
    for i, raw in enumerate(centers):
        center = Vector(raw)
        before = Vector(centers[max(0, i - 1)])
        after = Vector(centers[min(len(centers) - 1, i + 1)])
        direction = after - before
        if direction.length < 1e-9:
            direction = Vector((0, 0, 1))
        else:
            direction.normalize()
        u = direction.cross(Vector((0, 1, 0)) if abs(direction.z) > 0.94 else Vector((0, 0, 1))).normalized()
        v = direction.cross(u).normalized()
        for j in range(sides):
            a = TAU * j / sides
            r = radii[i] * (1 + rough * math.sin(a * 3 + i * 0.38))
            verts.append(tuple(center + (u * math.cos(a) + v * math.sin(a)) * r))
    for i in range(len(centers) - 1):
        for j in range(sides):
            a = offset + i * sides + j
            b = offset + i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(offset + j for j in range(sides - 1, -1, -1)))
    faces.append(tuple(offset + (len(centers) - 1) * sides + j for j in range(sides)))


def _leaf(verts, faces, indices, uv, start, end, width, material_index,
          normal, curl=0.0, segments=3, keel=0.07):
    """Limbo curvado con quilla, forma lanceolada y normal independiente."""
    start, end, normal = Vector(start), Vector(end), Vector(normal)
    delta = end - start
    direction = delta.normalized()
    across = direction.cross(normal)
    if across.length < 0.01:
        across = direction.cross(Vector((0, 1, 0)))
    if across.length < 0.01:
        across = direction.cross(Vector((1, 0, 0)))
    across.normalize()
    leaf_normal = across.cross(direction).normalized()
    offset = len(verts)
    for row in range(segments + 1):
        t = row / segments
        center = start + delta * t + leaf_normal * (curl * math.sin(math.pi * t))
        envelope = math.sin(math.pi * t) ** 0.82
        half = width * (0.012 if row in (0, segments) else envelope * 0.5)
        for lane in (-1, 0, 1):
            p = center + across * (lane * half)
            if lane == 0:
                p += leaf_normal * (half * keel)
            verts.append(tuple(p))
            uv.append((lane * 0.5 + 0.5, t))
    for row in range(segments):
        for lane in (0, 1):
            a = offset + row * 3 + lane
            faces.append((a, a + 1, a + 4, a + 3))
            indices.append(material_index)


def _fit(result, height=None, radius=None):
    """Encaja sólo el asset en la envolvente; la raíz xy nunca se desplaza."""
    objects = [obj for obj in result[1:] if obj.type == 'MESH']
    coordinates = [v.co for obj in objects for v in obj.data.vertices]
    if height is not None:
        maximum = max(v.z for v in coordinates)
        scale_z = height / maximum
        for obj in objects:
            for vertex in obj.data.vertices:
                vertex.co.z = max(0.0, vertex.co.z) * scale_z
    if radius is not None:
        maximum = max(math.hypot(v.x, v.y) for v in coordinates)
        scale_xy = radius / maximum
        for obj in objects:
            for vertex in obj.data.vertices:
                vertex.co.x *= scale_xy
                vertex.co.y *= scale_xy
    for obj in objects:
        obj.data.update()
    result[0]['caras_asset'] = sum(len(obj.data.polygons) for obj in objects)
    result[0]['vertices_asset'] = sum(len(obj.data.vertices) for obj in objects)


def _radius(name, height, fallback):
    old = _SOURCE_RADII.get(name)
    return old[1] * height / old[0] if old else height * fallback


def make_palm(name, xy, height, col, mats):
    """Phoenix pinnada: tronco liso en silueta, 39 frondas y follaje irregular."""
    rng = _rng(name)
    root = _parent(name, xy, col)
    radius = _radius(name, height, 0.485)
    root['altura_asset_m'] = height
    root['radio_asset_m'] = radius
    root['especie_visual'] = 'Phoenix, porte ornamental mediterráneo'
    root['criterio_envolvente'] = 'Altura y radio máximo V1; raíz sin desplazamiento.'
    result = [root]
    stem_height = height * 0.69
    nominal_r = max(0.13, min(0.34, height * 0.055))
    verts, faces = [], []
    rings, sides = 96, 64
    for i in range(rings + 1):
        t = i / rings
        z = stem_height * t
        cx = height * 0.0038 * math.sin(t * 2.5)
        cy = height * 0.0045 * t * t
        for j in range(sides):
            a = TAU * j / sides
            # Las bases foliares están integradas en el volumen, de pocos mm;
            # se eliminan las grandes piezas triangulares del asset anterior.
            diamonds = max(0.0, math.cos(a * 11 + z * 43) * math.cos(a * 11 - z * 43)) ** 3
            organic = 0.003 * math.sin(a * 5 + z * 7.2) + 0.002 * math.sin(a * 17 - z * 12.3)
            r = nominal_r * (1.055 - 0.12 * t) + organic + 0.007 * diamonds
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for i in range(rings):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides - 1, -1, -1)))
    faces.append(tuple(rings * sides + j for j in range(sides)))
    result.append(_mesh(name + ' · estípite y cicatrices finas', verts, faces, col, root, [_bark('palmera')]))
    leaf_verts, leaf_faces, indices, uv = [], [], [], []
    rachis, rachis_faces = [], []
    generations = [(15, (0.37, 0.44), (0.17, 0.23), (0.10, 0.145)),
                   (14, (0.33, 0.42), (0.045, 0.115), (0.16, 0.22)),
                   (10, (0.18, 0.30), (-0.20, -0.095), (0.09, 0.155))]
    counter = 0
    for generation, (count, lengths, drops, peaks) in enumerate(generations):
        for frond in range(count):
            angle = frond * TAU / count + generation * 0.48 + rng.uniform(-0.12, 0.12)
            radial = Vector((math.cos(angle), math.sin(angle), 0))
            side = Vector((-math.sin(angle), math.cos(angle), 0))
            length = height * rng.uniform(*lengths)
            drop = height * rng.uniform(*drops)
            peak = height * rng.uniform(*peaks)
            drift = height * rng.uniform(-0.025, 0.025)
            crown = Vector((height * 0.0038 * math.sin(2.5), height * 0.0045, stem_height))
            def axis(t):
                p = crown + radial * (nominal_r * 0.5 + length * t)
                p += side * (drift * math.sin(math.pi * t))
                p.z += peak * math.sin(math.pi * t) - drop * t
                return p
            line = [axis(i / 20) for i in range(21)]
            _tube(rachis, rachis_faces, line,
                  [height * 0.0042 * (1 - i / 20 * 0.965) for i in range(21)], 7)
            pairs = 56 if generation < 2 else 43
            for pair in range(pairs):
                t = 0.095 + pair / (pairs - 1) * 0.865
                envelope = math.sin(math.pi * t) ** 0.73
                leaflet_length = height * (0.010 + 0.116 * envelope) * rng.uniform(0.84, 1.08)
                for sign in (-1, 1):
                    offset_t = max(0.08, min(0.97, t + rng.uniform(-0.004, 0.004)))
                    start = axis(offset_t)
                    endpoint = start + side * (sign * leaflet_length)
                    endpoint += radial * (leaflet_length * rng.uniform(0.17, 0.39))
                    endpoint.z -= leaflet_length * (0.18 + t * 0.46 + rng.uniform(-0.08, 0.08))
                    normal = Vector((radial.x * 0.24, radial.y * 0.24, 1))
                    normal += side * rng.uniform(-0.45, 0.45)
                    width = height * 0.0058 * (0.86 - 0.32 * t) * rng.uniform(0.88, 1.18)
                    _leaf(leaf_verts, leaf_faces, indices, uv, start, endpoint, width,
                          rng.randrange(6), normal, -leaflet_length * 0.045, 3, 0.13)
            _leaf(leaf_verts, leaf_faces, indices, uv, axis(0.94), axis(1.018),
                  height * 0.0045, rng.randrange(6), (0, 0, 1), -0.01, 3, 0.18)
            counter += 1
    # Tres lanzas jóvenes cortas y plegadas; corona asimétrica, sin estrella radial.
    for spear in range(3):
        a = rng.uniform(0, TAU)
        start = Vector((0, 0, stem_height))
        end = Vector((math.cos(a) * height * rng.uniform(0.05, 0.075),
                      math.sin(a) * height * rng.uniform(0.05, 0.075), height * rng.uniform(0.98, 1.03)))
        _leaf(leaf_verts, leaf_faces, indices, uv, start, end, height * 0.025,
              spear + 2, (math.cos(a + 1), math.sin(a + 1), 0.4), 0.02, 8, 0.75)
    result.append(_mesh(name + ' · raquis arqueados', rachis, rachis_faces, col, root, _leaf_materials('palmera')[:1]))
    result.append(_mesh(name + ' · pinnas y lanzas jóvenes', leaf_verts, leaf_faces, col, root,
                        _leaf_materials('palmera'), indices, uv))
    root['frondas'] = counter
    _fit(result, height, radius)
    return result


def make_olive(name, xy, height, col, mats):
    """Olivo ramificado, copa porosa con 18.000 hojas decusadas haz/envés."""
    rng = _rng(name)
    root = _parent(name, xy, col)
    radius = _radius(name, height, 0.455)
    root['altura_asset_m'] = height
    root['radio_asset_m'] = radius
    root['especie_visual'] = 'Olea europaea, copa ornamental joven'
    root['criterio_envolvente'] = 'Altura y radio máximo V1; raíz sin desplazamiento.'
    result = [root]
    wood, wood_faces = [], []
    stem_height = height * 0.48
    centers = [(height * 0.009 * math.sin(i / 20 * 2.5),
                height * 0.006 * (1 - math.cos(i / 20 * 2.2)), stem_height * i / 20)
               for i in range(21)]
    _tube(wood, wood_faces, centers,
          [height * 0.036 * (1 - i / 20 * 0.64) for i in range(21)], 24, 0.14)
    verts, faces, indices, uv = [], [], [], []
    canopy_center = Vector((height * 0.004, height * 0.005, height * 0.69))
    canopy_r = height * 0.345
    canopy_z = height * 0.28
    leaf_count = 0
    for primary in range(12):
        angle = primary * math.pi * (3 - math.sqrt(5)) + rng.uniform(-0.19, 0.19)
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        start = Vector(centers[5 + primary % 12])
        end = canopy_center + direction * (canopy_r * rng.uniform(0.43, 0.70))
        end.z += height * rng.uniform(-0.08, 0.085)
        middle = start.lerp(end, 0.49) + Vector((height * rng.uniform(-0.025, 0.025),
                                                          height * rng.uniform(-0.025, 0.025), height * 0.055))
        _tube(wood, wood_faces, [start, start.lerp(middle, 0.5), middle, middle.lerp(end, 0.58), end],
              [height * 0.018, height * 0.0145, height * 0.010, height * 0.006, height * 0.003], 12, 0.10)
        for secondary in range(5):
            az = angle + rng.uniform(-0.48, 0.48)
            cos_phi = rng.uniform(-0.73, 0.94)
            sin_phi = math.sqrt(1 - cos_phi * cos_phi)
            shell = rng.uniform(0.65, 0.94)
            clump = canopy_center + Vector((math.cos(az) * canopy_r * sin_phi * shell,
                                            math.sin(az) * canopy_r * sin_phi * shell,
                                            canopy_z * cos_phi * shell))
            branch_start = middle.lerp(end, rng.uniform(0.35, 0.87))
            bend = branch_start.lerp(clump, 0.52) + Vector((0, 0, height * rng.uniform(0.005, 0.035)))
            _tube(wood, wood_faces, [branch_start, bend, clump],
                  [height * 0.0057, height * 0.0033, height * 0.0012], 8, 0.08)
            for twig in range(5):
                twig_az = az + rng.uniform(-1.0, 1.0)
                direction = Vector((math.cos(twig_az), math.sin(twig_az), rng.uniform(-0.42, 0.72))).normalized()
                length = rng.uniform(0.30, 0.51) * height / 4
                # Los puntos pertenecen a pequeñas ramillas, no a cubos de hojas.
                twig_start = clump + Vector((rng.uniform(-0.048, 0.048) * height,
                                              rng.uniform(-0.048, 0.048) * height,
                                              rng.uniform(-0.035, 0.035) * height))
                twig_end = twig_start + direction * length
                bend = twig_start.lerp(twig_end, 0.5) + Vector((0, 0, length * 0.09))
                _tube(wood, wood_faces, [clump, twig_start, bend, twig_end],
                      [0.0048, 0.0036, 0.0025, 0.0010], 5)
                across = direction.cross(Vector((0, 0, 1)))
                if across.length < 0.1:
                    across = Vector((1, 0, 0))
                across.normalize()
                normal = across.cross(direction).normalized()
                for pair in range(30):
                    t = 0.035 + pair / 29 * 0.94
                    node = twig_start.lerp(twig_end, t) + Vector((0, 0, length * 0.09 * math.sin(math.pi * t)))
                    # Filotaxis opuesta decusada, con variación natural entre nudos.
                    theta = (pair % 2) * math.pi * 0.5 + rng.uniform(-0.22, 0.22)
                    radial = across * math.cos(theta) + normal * math.sin(theta)
                    leaf_l = rng.uniform(0.059, 0.095) * min(1.0, height / 3.7)
                    for sign in (-1, 1):
                        start_leaf = node + radial * sign * 0.004
                        end_leaf = start_leaf + radial * (sign * leaf_l * 0.90) + direction * (leaf_l * 0.31)
                        end_leaf.z += rng.uniform(-0.018, 0.018)
                        leaf_normal = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(0.25, 1)))
                        _leaf(verts, faces, indices, uv, start_leaf, end_leaf,
                              leaf_l * rng.uniform(0.20, 0.27), rng.randrange(6),
                              leaf_normal, leaf_l * rng.uniform(0.025, 0.09), 3, 0.11)
                        leaf_count += 1
    result.append(_mesh(name + ' · tronco y ramificación natural', wood, wood_faces, col, root, [_bark('olivo')]))
    result.append(_mesh(name + ' · hojas lanceoladas haz y envés', verts, faces, col, root,
                        _leaf_materials('olivo'), indices, uv))
    root['hojas'] = leaf_count
    _fit(result, height, radius)
    return result


def make_shrub(name, xy, radius, col, mats):
    """Lentisco bajo: masa compacta de limbos, sin forma esférica perfecta."""
    rng = _rng(name)
    root = _parent(name, xy, col)
    root['radio_asset_m'] = radius
    root['especie_visual'] = 'Lentisco mediterráneo bajo, representación ornamental'
    wood, wood_faces = [], []
    verts, faces, indices, uv = [], [], [], []
    for stem in range(36):
        az = stem * math.pi * (3 - math.sqrt(5)) + rng.uniform(-0.25, 0.25)
        shell = rng.uniform(0.55, 1)
        zenith = rng.uniform(-0.20, 0.95)
        radial = Vector((math.cos(az), math.sin(az), 0))
        start = radial * radius * rng.uniform(0.025, 0.19) + Vector((0, 0, 0.018))
        end = radial * (radius * shell * math.sqrt(1 - zenith * zenith) * 0.92)
        end.z = radius * (0.43 + 0.60 * zenith)
        midpoint = start.lerp(end, 0.5) + Vector((0, 0, radius * 0.08))
        _tube(wood, wood_faces, [start, midpoint, end], [radius * 0.022, radius * 0.014, radius * 0.004], 5)
        side = Vector((-math.sin(az), math.cos(az), 0))
        for node in range(18):
            t = 0.14 + node / 17 * 0.86
            c = start.lerp(end, t) + Vector((0, 0, radius * 0.08 * math.sin(math.pi * t)))
            leaf_l = radius * rng.uniform(0.11, 0.19)
            for sign in (-1, 1):
                p = c + side * sign * leaf_l + radial * leaf_l * rng.uniform(0.1, 0.45)
                p.z += leaf_l * rng.uniform(0.05, 0.75)
                normal = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), 1))
                _leaf(verts, faces, indices, uv, c, p, leaf_l * rng.uniform(0.38, 0.52),
                      rng.randrange(6), normal, leaf_l * 0.05, 3, 0.08)
    result = [root,
              _mesh(name + ' · ramillas', wood, wood_faces, col, root, [_bark('olivo')]),
              _mesh(name + ' · masa foliar', verts, faces, col, root, _leaf_materials('lentisco'), indices, uv)]
    root['hojas'] = 36 * 18 * 2
    _fit(result, radius * 1.1, radius)
    return result


def make_turf_fibres(name, parts, z, col, mats, density=2000):
    """Microgeometría opcional de césped artificial dentro de triangles de parts.

    ``parts`` es la lista de superficies ``S['cesped']``: cada parte contiene
    ``vertices_xy`` y ``caras`` trianguladas. Las posiciones se muestrean por
    área sobre esos triángulos, sin alterar sus vértices ni crear nuevos bordes.
    Densidad es un presupuesto visual, no una especificación constructiva.
    Una sola malla, 3 caras por fibra y máximo 999.999 caras. Altura visual del
    pelo 18–27 mm; se deben desactivar estas fibras en comparaciones de planta.
    Devuelve [Empty_raíz, malla_fibras], igual que las otras funciones de assets.
    """
    if density < 0:
        raise ValueError('La densidad de fibras debe ser no negativa.')
    rng = _rng(name)
    root = _parent(name, (0, 0, z), col)
    root['procedencia'] = 'Microgeometría de material: césped artificial indicado por el usuario; pelo visual sin cota de proyecto.'
    root['categoria'] = 'jardin_microgeometria_material'
    root['criterio_arquitectura'] = 'No modifica huellas ni bordes del jardín; sólo pelo del material.'
    root['altura_pelo_visual_mm'] = '18–27; criterio de representación, no especificación constructiva.'
    triangles = []
    total_area = 0.0
    for part in parts:
        points = part['vertices_xy']
        for face in part['caras']:
            if len(face) != 3:
                raise ValueError('make_turf_fibres necesita superficies previamente trianguladas.')
            a, b, c = [points[index] for index in face]
            e1x, e1y = b[0] - a[0], b[1] - a[1]
            e2x, e2y = c[0] - a[0], c[1] - a[1]
            determinant = e1x * e2y - e1y * e2x
            area = abs(determinant) * 0.5
            if area <= 1e-12:
                continue
            triangles.append((a, e1x, e1y, e2x, e2y, determinant, area))
            total_area += area
    # El cap es global, incluso si cambia la superficie de césped de una revisión.
    total_count = min(333333, round(total_area * density))
    exact_counts = [total_count * tr[-1] / total_area if total_area else 0 for tr in triangles]
    counts = [int(value) for value in exact_counts]
    remainder = total_count - sum(counts)
    by_fraction = sorted(range(len(counts)), key=lambda i: exact_counts[i] - counts[i], reverse=True)
    for i in by_fraction[:remainder]:
        counts[i] += 1
    verts, faces = [], []
    minimum_barycentric = 1.0
    for tr, count in zip(triangles, counts):
        a, e1x, e1y, e2x, e2y, determinant, _ = tr
        inv = 1.0 / determinant
        for _ in range(count):
            # sqrt(U) proporciona muestreo uniforme en área del triángulo.
            sqrt_u = math.sqrt(rng.random())
            w2 = sqrt_u * rng.random()
            w1 = sqrt_u - w2
            w0 = 1 - sqrt_u
            base_x = a[0] + e1x * w1 + e2x * w2
            base_y = a[1] + e1y * w1 + e2y * w2
            minimum_barycentric = min(minimum_barycentric, w0, w1, w2)
            yaw = rng.uniform(0, TAU)
            across_x, across_y = math.cos(yaw), math.sin(yaw)
            width = rng.uniform(0.00055, 0.00115)
            pile_height = rng.uniform(0.018, 0.027)
            lean_angle = yaw + rng.uniform(-math.pi, math.pi)
            lean_amount = rng.uniform(0.0004, 0.0032)
            lean_x = math.cos(lean_angle) * lean_amount
            lean_y = math.sin(lean_angle) * lean_amount
            twist = rng.uniform(-0.28, 0.28)
            off = len(verts)
            for row, (t, taper) in enumerate(((0., 1.), (.36, .96), (.75, .85), (1., .22))):
                turn = twist * t
                ca, sa = math.cos(turn), math.sin(turn)
                side_x = across_x * ca - across_y * sa
                side_y = across_x * sa + across_y * ca
                for sign in (-1, 1):
                    dx = lean_x * t * t + side_x * sign * width * taper * 0.5
                    dy = lean_y * t * t + side_y * sign * width * taper * 0.5
                    # Recortar desplazamientos en coordenadas baricéntricas
                    # conserva también las puntas y el ancho dentro del jardín.
                    d1 = (dx * e2y - dy * e2x) * inv
                    d2 = (e1x * dy - e1y * dx) * inv
                    d0 = -d1 - d2
                    factor = 1.0
                    for w, dw in ((w0, d0), (w1, d1), (w2, d2)):
                        if dw < 0:
                            factor = min(factor, w / -dw * 0.999999)
                    verts.append((base_x + dx * factor, base_y + dy * factor, pile_height * t))
            for row in range(3):
                i = off + row * 2
                faces.append((i, i + 1, i + 3, i + 2))
    mat = mats.get('cesped_fibra', mats.get('cesped'))
    if mat is None:
        raise KeyError('make_turf_fibres necesita mats["cesped_fibra"] o mats["cesped"].')
    obj = _mesh(name + ' · pelo visual de polímero', verts, faces, col, root, [mat])
    obj['procedencia'] = root['procedencia']
    obj['categoria'] = root['categoria']
    obj['fuente_xy'] = 'Triangulación existente S[cesped]; se conserva sin modificaciones.'
    obj['microgeometria_material'] = True
    root['superficie_base_m2'] = total_area
    root['fibras'] = total_count
    root['caras_asset'] = len(faces)
    root['vertices_asset'] = len(verts)
    root['densidad_solicitada_m2'] = density
    root['densidad_efectiva_m2'] = total_count / total_area if total_area else 0.
    root['baricentrica_minima_base'] = minimum_barycentric if total_count else 0.
    root['bases_tips_dentro_triangulos'] = True
    return [root, obj]
