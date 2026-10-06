"""Assets de visualización, sin colocación global ni arquitectura.

Todas las funciones devuelven una lista de objetos, con un Empty padre primero.
Las plantas usan xy=(x,y) y suelo -0.15m, o xy=(x,y,z). Los muebles usan
center=(x,y), size=(largo,ancho) y z=suelo. size es la huella total del asset,
también en el comedor: las sillas quedan dentro de ella. Las alturas de los
assets son decisiones de visualización, no cotas del proyecto básico.

Ejemplo:
    objetos = make_palm('Palmera_01', (4, 12, -0.15), 4.0, coleccion, mats)
    mesa = make_dining('Comedor', (5, 16), (3.4, 2.8), 0.0, coleccion, mats)
"""

import hashlib
import math
import random
import bpy
from mathutils import Vector


NOTE = 'Asset de visualización: tipología y alturas no acotadas en el proyecto.'


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


def _parent(name, xyz, col):
    obj = bpy.data.objects.new(name, None)
    _collection(col).objects.link(obj)
    obj.location = xyz
    obj['procedencia'] = NOTE
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = 0.18
    return obj


def _mesh(name, verts, faces, col, parent, materials=(), indices=None):
    mesh = bpy.data.meshes.new(name + ' · malla')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    _collection(col).objects.link(obj)
    obj.parent = parent
    for material in materials:
        mesh.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True
        if indices is not None:
            face.material_index = indices[face.index]
    obj['procedencia'] = NOTE
    return obj


def _mat(mats, *keys):
    for key in keys:
        if key in mats:
            return mats[key]
    return next(iter(mats.values()))


def _leaf_mats(mats, olive=False):
    result = []
    for index in range(4):
        name = ('Olivo' if olive else 'Mediterráneo') + f' · hoja variación {index + 1}'
        material = bpy.data.materials.get(name)
        if material is None:
            material = bpy.data.materials.new(name)
            material.use_nodes = True
            shader = material.node_tree.nodes.get('Principled BSDF')
            scale = 0.78 + index * 0.13
            color = (0.12, 0.19, 0.058) if olive else (0.072, 0.185, 0.028)
            shader.inputs['Base Color'].default_value = (*[v * scale for v in color], 1)
            shader.inputs['Roughness'].default_value = 0.52 + index * 0.06
            shader.inputs['Subsurface Weight'].default_value = 0.05
            shader.inputs['IOR'].default_value = 1.4
            material.diffuse_color = (*[v * scale for v in color], 1)
        result.append(material)
    return result


def _tube(verts, faces, centers, radii, sides=7):
    """Append a smoothly curved tube, with stable ring frames."""
    offset = len(verts)
    for i, raw in enumerate(centers):
        center = Vector(raw)
        previous = Vector(centers[max(0, i - 1)])
        following = Vector(centers[min(len(centers) - 1, i + 1)])
        direction = (following - previous).normalized()
        if abs(direction.z) < 0.92:
            u = direction.cross(Vector((0, 0, 1))).normalized()
        else:
            u = direction.cross(Vector((0, 1, 0))).normalized()
        v = direction.cross(u).normalized()
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            point = center + (math.cos(angle) * u + math.sin(angle) * v) * radii[i]
            verts.append(tuple(point))
    for i in range(len(centers) - 1):
        for j in range(sides):
            a = offset + i * sides + j
            b = offset + i * sides + (j + 1) % sides
            c = offset + (i + 1) * sides + (j + 1) % sides
            d = offset + (i + 1) * sides + j
            faces.append((a, b, c, d))
    faces.append(tuple(offset + j for j in range(sides - 1, -1, -1)))
    faces.append(tuple(offset + (len(centers) - 1) * sides + j for j in range(sides)))


def _blade(verts, faces, indices, start, end, width, material, droop=0.0, segments=5):
    """Curved, keeled botanical blade, three vertices across each cross-section."""
    start, end = Vector(start), Vector(end)
    direction = (end - start).normalized()
    cross = direction.cross(Vector((0, 0, 1)))
    if cross.length < 0.01:
        cross = Vector((1, 0, 0))
    cross.normalize()
    offset = len(verts)
    for section in range(segments + 1):
        t = section / segments
        center = start.lerp(end, t)
        center.z -= droop * math.sin(math.pi * t)
        leaf_width = width * (math.sin(math.pi * t) ** 0.72) * 0.5
        if section in (0, segments):
            leaf_width = width * 0.006
        for transverse in (-1, 0, 1):
            point = center + cross * transverse * leaf_width
            if transverse == 0:
                point.z += leaf_width * 0.18
            verts.append(tuple(point))
    for section in range(segments):
        for j in range(2):
            a = offset + section * 3 + j
            faces.append((a, a + 1, a + 4, a + 3))
            indices.append(material)


def _xyz(xy):
    return (xy[0], xy[1], xy[2] if len(xy) > 2 else -0.15)


def make_palm(name, xy, height, col, mats):
    """Phoenix-type palm with a layered crown; under 16k mesh faces."""
    rng = _rng(name)
    parent = _parent(name, _xyz(xy), col)
    parent['altura_asset_m'] = height
    result = [parent]
    trunk_height = height * 0.70
    verts, faces = [], []
    centers, radii = [], []
    trunk_radius = max(0.13, min(0.34, height * 0.055))
    for i in range(35):
        t = i / 34
        centers.append((0.025 * math.sin(t * 2.0), 0.03 * t * t, trunk_height * t))
        radii.append(trunk_radius * (1.08 - 0.18 * t) * (1 + 0.018 * math.sin(i * math.pi)))
    _tube(verts, faces, centers, radii, 14)
    result.append(_mesh(name + ' · tronco', verts, faces, col, parent, [_mat(mats, 'tronco', 'trunk')]))
    # Small rings of old leaf bases create the characteristic texture in geometry.
    base_verts, base_faces = [], []
    for ring in range(18):
        z = trunk_height * (0.15 + ring / 18 * 0.78)
        for index in range(8):
            angle = index * 2 * math.pi / 8 + ring * 0.4
            radial = Vector((math.cos(angle), math.sin(angle), 0))
            side = Vector((-math.sin(angle), math.cos(angle), 0))
            c = radial * trunk_radius * 1.04 + Vector((0, 0, z))
            off = len(base_verts)
            base_verts += [tuple(c - side * 0.052 + Vector((0, 0, -0.04))),
                           tuple(c + side * 0.052 + Vector((0, 0, -0.04))),
                           tuple(c + radial * 0.035 + Vector((0, 0, 0.075)))]
            base_faces.append((off, off + 1, off + 2))
    result.append(_mesh(name + ' · bases foliares', base_verts, base_faces, col, parent,
                        [_mat(mats, 'tronco', 'trunk')]))
    blades, blade_faces, indices = [], [], []
    rachis_verts, rachis_faces = [], []
    for frond in range(24):
        # Three biological generations of leaves: lower spreading, arching,
        # and the upright central crown. All remain inside the existing asset
        # envelope. A coplanar crown looks bare even with many small leaflets.
        layer = 0 if frond < 10 else 1 if frond < 18 else 2
        layer_index = frond if layer == 0 else frond - 10 if layer == 1 else frond - 18
        layer_count = (10, 8, 6)[layer]
        angle = layer_index * 2 * math.pi / layer_count + layer * 0.38 + rng.uniform(-0.10, 0.10)
        radial = Vector((math.cos(angle), math.sin(angle), 0))
        lateral = Vector((-math.sin(angle), math.cos(angle), 0))
        length = height * rng.uniform(*( (0.40, 0.44), (0.32, 0.38), (0.16, 0.23) )[layer])
        drop = height * rng.uniform(*( (0.15, 0.20), (0.04, 0.10), (-0.24, -0.20) )[layer])
        peak = height * (0.11, 0.19, 0.075)[layer]
        def axis(t):
            p = radial * (length * t) + Vector((0, 0, trunk_height))
            p.z += peak * math.sin(math.pi * t) - drop * t
            return p
        line = [axis(i / 14) for i in range(15)]
        _tube(rachis_verts, rachis_faces, line,
              [height * 0.004 * (1 - i / 14 * 0.94) for i in range(15)], 5)
        for pair in range(24):
            t = 0.12 + pair / 23 * 0.84
            root = axis(t)
            leaflet_length = height * 0.13 * (math.sin(math.pi * t) ** 0.75) + height * 0.01
            for sign in (-1, 1):
                endpoint = root + lateral * sign * leaflet_length + radial * leaflet_length * 0.25
                endpoint.z -= leaflet_length * (0.25 + t * 0.48)
                _blade(blades, blade_faces, indices, root, endpoint,
                       height * 0.014 * (1 - 0.35 * t), rng.randrange(4), leaflet_length * 0.09, 5)
        _blade(blades, blade_faces, indices, axis(0.89), axis(1.04), height * 0.017,
               rng.randrange(4), 0.025, 5)
    result.append(_mesh(name + ' · raquis', rachis_verts, rachis_faces, col, parent,
                        [_mat(mats, 'hojas', 'leaf')]))
    result.append(_mesh(name + ' · hojas pinnadas', blades, blade_faces, col, parent,
                        _leaf_mats(mats), indices))
    # Standardize the requested visual asset height while leaving its base at soil.
    maximum = max(vertex.co.z for obj in result[1:] for vertex in obj.data.vertices)
    factor = height / maximum
    for obj in result[1:]:
        for vertex in obj.data.vertices:
            vertex.co *= factor
    return result


def make_shrub(name, xy, radius, col, mats):
    """Compact Mediterranean shrub with individual curved leaves, about 3k faces."""
    rng = _rng(name)
    parent = _parent(name, _xyz(xy), col)
    parent['radio_asset_m'] = radius
    verts, faces, indices = [], [], []
    branches, branch_faces = [], []
    count = 260
    for index in range(count):
        azimuth = rng.uniform(0, 2 * math.pi)
        cos_phi = rng.uniform(-0.50, 1)
        sin_phi = math.sqrt(1 - cos_phi * cos_phi)
        shell = rng.uniform(0.55, 1.0)
        c = Vector((radius * shell * math.cos(azimuth) * sin_phi,
                    radius * shell * math.sin(azimuth) * sin_phi,
                    radius * 0.50 + radius * 0.55 * shell * cos_phi))
        direction = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.2, 1))).normalized()
        length = min(0.11, radius * 0.18) * rng.uniform(0.75, 1.25)
        for side in (-1, 1):
            _blade(verts, faces, indices, c, c + direction * side * length,
                   length * 0.44, rng.randrange(4), length * 0.10, 4)
        if index % 20 == 0:
            _tube(branches, branch_faces, [(0, 0, 0.05), tuple(c * 0.8)], [0.012, 0.004], 5)
    result = [parent,
              _mesh(name + ' · ramas', branches, branch_faces, col, parent, [_mat(mats, 'tronco', 'trunk')]),
              _mesh(name + ' · follaje', verts, faces, col, parent, _leaf_mats(mats), indices)]
    return result


def make_olive(name, xy, height, col, mats):
    """Open olive canopy, curved branches and slender leaves; under 16k faces."""
    rng = _rng(name)
    parent = _parent(name, _xyz(xy), col)
    parent['altura_asset_m'] = height
    trunk, trunk_faces = [], []
    centers = [(0.03 * math.sin(i * 0.7), 0.025 * math.cos(i * 0.6), height * 0.62 * i / 12)
               for i in range(13)]
    _tube(trunk, trunk_faces, centers, [height * 0.036 * (1 - i / 12 * 0.68) for i in range(13)], 11)
    leafverts, leaffaces, indices = [], [], []
    radius = height * 0.32
    for branch in range(18):
        angle = 2 * math.pi * branch / 18 + rng.uniform(-0.25, 0.25)
        radial = Vector((math.cos(angle), math.sin(angle), 0))
        start = Vector(centers[5 + branch % 6])
        end = radial * radius * rng.uniform(0.5, 1) + Vector((0, 0, height * rng.uniform(0.65, 0.91)))
        middle = start.lerp(end, 0.5) + Vector((0, 0, height * 0.06))
        _tube(trunk, trunk_faces, [start, middle, end], [height * 0.013, height * 0.008, height * 0.0025], 7)
        # More separate leaves, fewer subdivisions per blade. The previous
        # sparse population left most branches visually bare at aerial scale.
        for leaf in range(190):
            c = end + Vector((rng.uniform(-radius * 0.32, radius * 0.32),
                              rng.uniform(-radius * 0.32, radius * 0.32),
                              rng.uniform(-height * 0.10, height * 0.09)))
            direction = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.8))).normalized()
            length = rng.uniform(0.06, 0.10) * min(1.0, height / 2.5)
            _blade(leafverts, leaffaces, indices, c, c + direction * length,
                   length * 0.24, rng.randrange(4), length * 0.06, 2)
    result = [parent,
              _mesh(name + ' · tronco y ramas', trunk, trunk_faces, col, parent, [_mat(mats, 'tronco', 'trunk')]),
              _mesh(name + ' · hojas lanceoladas', leafverts, leaffaces, col, parent,
                    _leaf_mats(mats, True), indices)]
    maximum = max(vertex.co.z for obj in result[1:] for vertex in obj.data.vertices)
    factor = height / maximum
    for obj in result[1:]:
        for vertex in obj.data.vertices:
            vertex.co *= factor
    return result


def _box(name, location, size, col, parent, material, bevel=0.02):
    sx, sy, sz = [v * 0.5 for v in size]
    verts = [(x * sx, y * sy, z * sz) for x, y, z in
             [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    obj = _mesh(name, verts, faces, col, parent, [material])
    obj.location = location
    if bevel:
        modifier = obj.modifiers.new('Bordes del mueble', 'BEVEL')
        modifier.width = min(bevel, min(size) * 0.23)
        modifier.segments = 3
        modifier.limit_method = 'ANGLE'
        modifier = obj.modifiers.new('Normales del mueble', 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
    return obj


def _chair(name, local_xy, yaw, col, parent, mats, scale=1):
    """Minimal dining chair with actual legs/back, no intersecting planes."""
    group = bpy.data.objects.new(name, None)
    _collection(col).objects.link(group)
    group.parent = parent
    group.location = (*local_xy, 0)
    group.rotation_euler.z = yaw
    group.scale = (scale, scale, scale)
    group['procedencia'] = NOTE
    result = [group]
    wood = _mat(mats, 'madera_pergola', 'wood')
    fabric = _mat(mats, 'tejido', 'fabric')
    for x in (-0.19, 0.19):
        for y in (-0.18, 0.18):
            result.append(_box(name + ' · pata', (x, y, 0.225), (0.038, 0.038, 0.45), col, group, wood, 0.008))
    result.append(_box(name + ' · asiento', (0, 0, 0.455), (0.47, 0.46, 0.07), col, group, fabric, 0.03))
    for x in (-0.19, 0.19):
        result.append(_box(name + ' · montante', (x, 0.19, 0.63), (0.03, 0.035, 0.35), col, group, wood, 0.008))
    result.append(_box(name + ' · respaldo', (0, 0.19, 0.76), (0.46, 0.055, 0.22), col, group, wood, 0.025))
    return result


def make_dining(name, center, size, z, collection, mats):
    """Dining set contained in size=(X,Y), with nominal 0.75m table height."""
    parent = _parent(name, (center[0], center[1], z), collection)
    sx, sy = size
    parent['huella_asset_m'] = f'{sx} × {sy}'
    result = [parent]
    wood = _mat(mats, 'madera_pergola', 'wood')
    metal = _mat(mats, 'carpinteria_antracita', 'frame')
    clearance = min(0.62, sy * 0.27, sx * 0.27)
    tx, ty = max(0.5, sx - clearance * 2), max(0.48, sy - clearance * 2)
    result.append(_box(name + ' · tablero', (0, 0, 0.745), (tx, ty, 0.045), collection, parent, wood, 0.025))
    for x in (-tx * 0.4, tx * 0.4):
        for y in (-ty * 0.34, ty * 0.34):
            result.append(_box(name + ' · pata mesa', (x, y, 0.36), (0.04, 0.04, 0.72), collection, parent, metal, 0.008))
    chair_scale = min(1.0, clearance / 0.54)
    seat_y = (ty / 2 + clearance * 0.51)
    n = 3 if tx > 1.75 else 2 if tx > 1.0 else 1
    for sign in (-1, 1):
        for index in range(n):
            x = 0 if n == 1 else (index / (n - 1) - 0.5) * tx * 0.70
            result.extend(_chair(name + f' · silla {sign}_{index}', (x, seat_y * sign),
                                 0 if sign > 0 else math.pi, collection, parent, mats, chair_scale))
    return result


def make_sofa(name, center, size, z, collection, mats):
    """Neutral contemporary sofa, exact outer X/Y footprint supplied by caller."""
    parent = _parent(name, (center[0], center[1], z), collection)
    sx, sy = size
    parent['huella_asset_m'] = f'{sx} × {sy}'
    result = [parent]
    fabric = _mat(mats, 'tejido', 'fabric')
    dark = _mat(mats, 'carpinteria_antracita', 'frame')
    result.append(_box(name + ' · base', (0, 0, 0.22), (sx, sy, 0.30), collection, parent, fabric, 0.055))
    result.append(_box(name + ' · respaldo', (0, sy * 0.39, 0.58), (sx, sy * 0.22, 0.46), collection, parent, fabric, 0.08))
    arm = min(0.16, sx * 0.10)
    for sign in (-1, 1):
        result.append(_box(name + ' · brazo', (sign * (sx / 2 - arm / 2), 0, 0.48),
                           (arm, sy, 0.36), collection, parent, fabric, 0.055))
    seats = max(1, round(sx / 0.85))
    width = (sx - 2 * arm) / seats
    for index in range(seats):
        result.append(_box(name + f' · cojín {index+1}', (-sx/2 + arm + (index+0.5)*width, -sy*0.075, 0.42),
                           (width * 0.965, sy * 0.70, 0.16), collection, parent, fabric, 0.065))
    for x in (-sx * 0.41, sx * 0.41):
        for y in (-sy * 0.37, sy * 0.37):
            result.append(_box(name + ' · pata', (x,y,0.05),(0.05,0.05,0.10),collection,parent,dark,0.005))
    return result


def make_bed(name, center, size, z, collection, mats):
    """Simple neutral bed; supplied footprint is respected, headboard at +Y."""
    parent = _parent(name, (center[0], center[1], z), collection)
    sx, sy = size
    parent['huella_asset_m'] = f'{sx} × {sy}'
    result = [parent]
    wood = _mat(mats, 'madera_clara_vertical', 'wood')
    fabric = _mat(mats, 'tejido', 'fabric')
    white = _mat(mats, 'pared_interior', 'white')
    result.append(_box(name + ' · estructura', (0,0,0.22),(sx,sy,0.28),collection,parent,wood,0.025))
    result.append(_box(name + ' · colchón', (0,-sy*0.015,0.46),(sx*0.98,sy*0.95,0.25),collection,parent,white,0.07))
    result.append(_box(name + ' · cabecero', (0,sy/2-0.035,0.61),(sx,0.07,1.02),collection,parent,fabric,0.04))
    result.append(_box(name + ' · ropa de cama', (0,-sy*0.10,0.595),(sx*0.96,sy*0.76,0.065),collection,parent,fabric,0.032))
    pillows = 2 if sx > 1.1 else 1
    for index in range(pillows):
        px = (index-(pillows-1)/2)*sx*0.47
        result.append(_box(name + f' · almohada {index+1}', (px,sy*0.30,0.62),
                           (sx*0.42 if pillows==2 else sx*0.80,sy*0.22,0.12),collection,parent,white,0.05))
    return result
