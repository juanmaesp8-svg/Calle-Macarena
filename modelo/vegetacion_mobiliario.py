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
    """Manufactured solid with physically rounded edges, dimensions unchanged."""
    sx, sy, sz = [v * 0.5 for v in size]
    verts = [(x * sx, y * sy, z * sz) for x, y, z in
             [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    obj = _mesh(name, verts, faces, col, parent, [material])
    obj.location = location
    if bevel:
        modifier = obj.modifiers.new('Radio físico de canto', 'BEVEL')
        modifier.width = min(bevel, min(size) * 0.42)
        modifier.segments = 5
        modifier.limit_method = 'ANGLE'
        modifier.harden_normals = True
        modifier = obj.modifiers.new('Normales de superficie manufacturada', 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
        modifier.weight = 50
    return obj


def _curve(name, points, col, parent, material, radius=0.002, closed=False):
    data = bpy.data.curves.new(name + ' · curva', 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 1
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p, xyz in zip(spline.points, points):
        p.co = (*xyz,1)
    spline.use_cyclic_u = closed
    obj = bpy.data.objects.new(name,data)
    _collection(col).objects.link(obj)
    obj.parent = parent
    data.materials.append(material)
    obj['procedencia'] = NOTE
    return obj


def _rod(name, start, end, radius0, radius1, col, parent, material, sides=20):
    vertices, faces = [], []
    _tube(vertices,faces,[start,end],[radius0,radius1],sides)
    obj = _mesh(name,vertices,faces,col,parent,[material])
    for face in obj.data.polygons[-2:]:
        face.use_smooth = False
    return obj


def _spow(value, exponent):
    return math.copysign(abs(value)**exponent,value)


def _upholstered(name, location, size, col, parent, material,
                 rotation=(0,0,0), fullness=0.36, wrinkles=0.002, seam=True):
    """Closed soft cushion, not a bevelled cube; small sewn compression folds.

    Cardinal vertices retain its supplied dimensions. Seams lie inside the
    cushion envelope. Height, puff and folds are visual furnishing choices.
    """
    hx,hy,hz=[v*.5 for v in size]
    nt,nv=48,20
    verts=[]
    for j in range(nv+1):
        phi=-math.pi/2+1e-6+(math.pi-2e-6)*j/nv
        cp=abs(math.cos(phi))**fullness
        zp=_spow(math.sin(phi),fullness)
        for i in range(nt):
            theta=2*math.pi*i/nt
            x=hx*cp*_spow(math.cos(theta),0.30)
            y=hy*cp*_spow(math.sin(theta),0.30)
            # Local folds close to the edge, disappearing at cardinal/pole
            # extrema: volume is within original bbox, no simulated sculpture.
            edge=math.exp(-((abs(phi)-.34)/.25)**2)
            ripple=wrinkles*math.sin(theta*13+.4)*math.sin(theta*2)**2*edge
            z=hz*zp+ripple
            z=max(-hz,min(hz,z))
            verts.append((x,y,z))
    faces=[]
    for j in range(nv):
        for i in range(nt):
            a=j*nt+i;b=j*nt+(i+1)%nt
            faces.append((a,b,b+nt,a+nt))
    faces.append(tuple(reversed(range(nt))))
    faces.append(tuple(nv*nt+i for i in range(nt)))
    obj=_mesh(name,verts,faces,col,parent,[material])
    obj.location=location
    obj.rotation_euler=rotation
    result=[obj]
    if seam:
        radius=min(.0017,min(size)*.013)
        inset=max(radius*2.5,.0025)
        points=[]
        for i in range(96):
            t=2*math.pi*i/96
            points.append(((hx-inset)*_spow(math.cos(t),.30),
                           (hy-inset)*_spow(math.sin(t),.30),0))
        line=_curve(name+' · vivo cosido',points,col,parent,material,radius,True)
        line.location=location
        line.rotation_euler=rotation
        result.append(line)
    return result


def _fit_xy(parent, objects, size):
    """Normalize accessory XY envelope to supplied source footprint exactly.

    Evaluates the actual meshes, including cloth, piping and nested chair
    groups. Only the accessory transform changes; source centre and Z remain.
    """
    bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get()
    inverse=parent.matrix_world.inverted()
    points=[]
    for obj in objects:
        if obj.type not in ('MESH','CURVE'):
            continue
        evaluated=obj.evaluated_get(graph)
        data=evaluated.to_mesh()
        matrix=inverse@evaluated.matrix_world
        points.extend(matrix@v.co for v in data.vertices)
        evaluated.to_mesh_clear()
    if not points:
        raise ValueError('Accessory has no geometry')
    lo=[min(p[i] for p in points) for i in (0,1)]
    hi=[max(p[i] for p in points) for i in (0,1)]
    shift=[(a+b)/2 for a,b in zip(lo,hi)]
    for obj in objects:
        if obj.parent==parent:
            obj.location.x-=shift[0]
            obj.location.y-=shift[1]
    parent.scale.x*=size[0]/(hi[0]-lo[0])
    parent.scale.y*=size[1]/(hi[1]-lo[1])
    parent['huella_asset_m']=list(size)
    parent['altura_asset_evaluada_m']=max(p.z for p in points)
    parent['control_xy']='Envolvente evaluada ajustada a size, centro de fuente conservado'
    bpy.context.view_layer.update()


def _chair(name, local_xy, yaw, col, parent, mats, scale=1):
    """Refined bent-wood dining chair; nominal silhouette .47×.46m."""
    group=bpy.data.objects.new(name,None)
    _collection(col).objects.link(group)
    group.parent=parent
    group.location=(*local_xy,0)
    group.rotation_euler.z=yaw
    group.scale=(scale,scale,scale)
    group['procedencia']=NOTE
    result=[group]
    wood=_mat(mats,'madera_mesa','madera_pergola','wood')
    vertical=_mat(mats,'madera_patas','madera_mesa','madera_pergola','wood')
    fabric=_mat(mats,'tejido_tapizado','tejido','fabric')
    dark=_mat(mats,'metal_mobiliario','carpinteria_antracita','frame')
    # Tapered, subtly splayed legs, real frame and rubber floor glides.
    for signx in (-1,1):
        for signy in (-1,1):
            lower=(signx*.204,signy*.188,.018)
            upper=(signx*.172,signy*.145,.421)
            result.append(_rod(name+' · pata torneada',lower,upper,.016,.023,col,group,vertical))
            result.append(_rod(name+' · apoyo de suelo',
                (lower[0],lower[1],0),(lower[0],lower[1],.023),.018,.018,col,group,dark))
    result.extend(_upholstered(name+' · asiento tapizado',(0,-.005,.466),
                  (.47,.46,.093),col,group,fabric,fullness=.28,wrinkles=.0012))
    # Slender apron under the seat, no massive floating slab.
    for x in (-.176,.176):
        result.append(_rod(name+' · larguero lateral',(x,-.158,.419),(x,.147,.419),.015,.015,col,group,wood))
    result.append(_rod(name+' · travesaño frontal',(-.18,-.151,.419),(.18,-.151,.419),.017,.017,col,group,wood))
    for sx in (-1,1):
        line=[]
        for j in range(13):
            t=j/12
            line.append((sx*(.177-.015*math.sin(math.pi*t)),.145+.046*t,.425+.382*t))
        result.append(_curve(name+' · montante curvo',line,col,group,vertical,.015))
    # Back is a curved, closed laminated shell, upholstered on its front.
    width=.445; nx,nz=24,8; vertices=[]; faces=[]
    for j in range(nz+1):
        t=j/nz
        for i in range(nx+1):
            u=-1+2*i/nx
            vertices.append((u*width/2,.187-.036*u*u+.011*t,.579+.230*t-.008*u*u))
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
    shell=_mesh(name+' · respaldo de madera curvada',vertices,faces,col,group,[wood])
    solid=shell.modifiers.new('Lámina de madera curvada 14mm','SOLIDIFY');solid.thickness=.014;solid.offset=0
    bevel=shell.modifiers.new('Canto suavizado 3mm','BEVEL');bevel.width=.003;bevel.segments=3
    result.append(shell)
    result.extend(_upholstered(name+' · acolchado de respaldo',(0,.172,.700),
                  (.414,.055,.204),col,group,fabric,rotation=(math.radians(-3),0,0),
                  fullness=.25,wrinkles=.0008))
    return result


def make_chair(name, center, size, z, collection, mats, yaw=0):
    """One source-position chair; size is its WORLD-XY bbox, including rotation.

    Back at +Y for yaw0, -X for yaw+pi/2. For source symbols partly tucked
    under a table this preserves the documented visible footprint; dimensions
    of a named manufacturer chair are not claimed.
    """
    parent=_parent(name,(center[0],center[1],z),collection)
    result=[parent]+_chair(name+' · estructura',(0,0),0,collection,parent,mats)
    quarter=abs(math.sin(yaw))>0.99
    local_size=(size[1],size[0]) if quarter else size
    _fit_xy(parent,result,local_size)
    parent.rotation_euler.z=yaw
    parent['altura_asset_m']=.815
    return result


def make_table(name, center, size, z, collection, mats, height=.75, coffee=False):
    """Thin physically rounded table; footprint exactly follows caller's size."""
    parent=_parent(name,(center[0],center[1],z),collection)
    sx,sy=size
    result=[parent]
    wood=_mat(mats,'madera_mesa','madera_pergola','wood')
    metal=_mat(mats,'metal_mobiliario','carpinteria_antracita','frame')
    topmat=_mat(mats,'porcelanico_exterior','paving') if coffee else wood
    thickness=.034 if not coffee else .028
    result.append(_box(name+' · tablero de canto fino',(0,0,height-thickness/2),
                  (sx,sy,thickness),collection,parent,topmat,.008))
    # Fine timber/steel support and a recessed apron below the top.
    if not coffee:
        for sign in (-1,1):
            result.append(_box(name+' · faldón longitudinal',(sign*sx*.39,0,height-.057),
                (.023,sy*.69,.042),collection,parent,metal,.004))
    for ix in (-1,1):
        for iy in (-1,1):
            x=ix*sx*.375;y=iy*sy*.345
            result.append(_rod(name+' · pata cónica',
                (x*1.035,y*1.035,.009),(x,y,height-thickness),
                .015 if coffee else .018,.022 if coffee else .026,
                collection,parent,metal))
            result.append(_rod(name+' · protector de apoyo',
                (x*1.035,y*1.035,0),(x*1.035,y*1.035,.011),.017,.017,
                collection,parent,metal))
    _fit_xy(parent,result,size)
    parent['altura_asset_m']=height
    return result


def make_dining(name, center, size, z, collection, mats):
    """Complete dining set inside source bbox; source set centre is unchanged."""
    parent=_parent(name,(center[0],center[1],z),collection)
    sx,sy=size
    clearance=min(.62,sy*.27,sx*.27)
    tx,ty=max(.50,sx-2*clearance),max(.48,sy-2*clearance)
    # make_table coordinates are relative to the global set parent after attach.
    table=make_table(name+' · mesa',(0,0),(tx,ty),0,collection,mats)
    table[0].parent=parent
    result=[parent]+table
    chair_scale=min(1.0,clearance/.54)
    seat_y=ty/2+clearance*.51
    n=3 if tx>1.75 else 2 if tx>1.0 else 1
    for sign in (-1,1):
        for index in range(n):
            x=0 if n==1 else (index/(n-1)-.5)*tx*.70
            result.extend(_chair(name+f' · silla {sign}_{index}',(x,seat_y*sign),
                0 if sign>0 else math.pi,collection,parent,mats,chair_scale))
    _fit_xy(parent,result,size)
    parent['altura_asset_m']=.815
    return result


def make_sofa(name, center, size, z, collection, mats):
    """Soft upholstered sofa/butaca, same source centre and total XY envelope."""
    parent=_parent(name,(center[0],center[1],z),collection)
    sx,sy=size
    result=[parent]
    fabric=_mat(mats,'tejido_tapizado','tejido','fabric')
    metal=_mat(mats,'metal_mobiliario','carpinteria_antracita','frame')
    ottoman=('ottoman' in name.lower() or 'asiento_' in name.lower())
    result.extend(_upholstered(name+' · bastidor tapizado',(0,0,.265),
                  (sx,sy,.285),collection,parent,fabric,fullness=.22,wrinkles=.0005))
    for x in (-sx*.39,sx*.39):
        for y in (-sy*.35,sy*.35):
            result.append(_rod(name+' · pata cilíndrica',(x,y,0),(x,y,.15),
                          .017,.021,collection,parent,metal))
    if ottoman:
        result.extend(_upholstered(name+' · cojín superior',(0,0,.461),
                    (sx*.985,sy*.985,.170),collection,parent,fabric,fullness=.31))
    else:
        arm=min(.16,sx*.12)
        result.extend(_upholstered(name+' · carcasa de respaldo',(0,sy*.387,.654),
                    (sx*.996,sy*.224,.414),collection,parent,fabric,
                    fullness=.23,wrinkles=.0011))
        for sign in (-1,1):
            result.extend(_upholstered(name+' · apoyabrazos '+str(sign),
                    (sign*(sx/2-arm/2),-.01*sy,.484),
                    (arm,sy*.984,.356),collection,parent,fabric,
                    fullness=.23,wrinkles=.0011))
        seats=max(1,min(4,round(sx/.78)))
        usable=sx-2*arm
        width=usable/seats
        for index in range(seats):
            x=-usable/2+(index+.5)*width
            result.extend(_upholstered(name+f' · cojín asiento {index+1}',
                    (x,-sy*.11,.462),(width-.012,sy*.716,.178),
                    collection,parent,fabric,fullness=.30,wrinkles=.0021))
            result.extend(_upholstered(name+f' · cojín respaldo {index+1}',
                    (x,sy*.276,.682),(width-.014,sy*.155,.355),
                    collection,parent,fabric,rotation=(math.radians(-5),0,0),
                    fullness=.28,wrinkles=.0018))
        # Loose side cushions sit on the seat, well within source footprint.
        if sx>1.5:
            for sign in (-1,1):
                pillow=min(.36,sy*.46)
                result.extend(_upholstered(name+' · almohadón suelto '+str(sign),
                    (sign*(usable/2-pillow*.52),sy*.045,.641),
                    (pillow,.135,pillow),collection,parent,fabric,
                    rotation=(math.radians(-12),math.radians(sign*9),math.radians(sign*6)),
                    fullness=.48,wrinkles=.0022))
    _fit_xy(parent,result,size)
    parent['altura_asset_m']=.88 if not ottoman else .55
    parent['detalle_visual']='Tapizado cerrado con compresión milimétrica, vivos cosidos y cojines separados'
    return result


def _inside_xy(point, polygon):
    x,y=point;inside=False
    for i,(a,b) in enumerate(polygon):
        c,d=polygon[(i+1)%len(polygon)]
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:
            inside=not inside
    return inside


def make_sofa_l(name, footprint_xy, z, collection, mats):
    """Sectional sofa following an axis-aligned source L polygon, no bbox fill.

    New helper for the builder: source polygon determines every occupied cell.
    Back rests remain on the north/west boundaries already drawn in V1.
    """
    xs=sorted(set(p[0] for p in footprint_xy));ys=sorted(set(p[1] for p in footprint_xy))
    center=((xs[0]+xs[-1])/2,(ys[0]+ys[-1])/2)
    parent=_parent(name,(*center,z),collection)
    result=[parent]
    fabric=_mat(mats,'tejido_tapizado','tejido','fabric')
    metal=_mat(mats,'metal_mobiliario','carpinteria_antracita','frame')
    cells=[]
    for a,b in zip(xs[:-1],xs[1:]):
        for c,d in zip(ys[:-1],ys[1:]):
            if _inside_xy(((a+b)/2,(c+d)/2),footprint_xy):cells.append((a,b,c,d))
    for i,(a,b,c,d) in enumerate(cells):
        x=(a+b)/2-center[0];y=(c+d)/2-center[1];sx=b-a;sy=d-c
        result.extend(_upholstered(name+f' · base modular {i+1}',(x,y,.270),
                      (sx,sy,.29),collection,parent,fabric,fullness=.20,wrinkles=.0006))
        # Multiple real seat pads on wide row; chaise occupies its own source cell.
        count=max(1,round(sx/.78))
        for j in range(count):
            px=x-sx/2+(j+.5)*sx/count
            result.extend(_upholstered(name+f' · asiento modular {i+1}_{j+1}',
                      (px,y,.467),(sx/count-.014,sy-.024,.178),
                      collection,parent,fabric,fullness=.29,wrinkles=.0020))
        for dx in (-1,1):
            for dy in (-1,1):
                p=(x+dx*sx*.36,y+dy*sy*.34)
                result.append(_rod(name+f' · pata módulo {i+1}',(*p,0),(*p,.15),
                              .017,.020,collection,parent,metal))
    width=xs[-1]-xs[0];depth=ys[-1]-ys[0]
    north_y=ys[-1]-center[1]-.085
    west_x=xs[0]-center[0]+.080
    result.extend(_upholstered(name+' · respaldo norte',(0,north_y,.68),
                  (width,.17,.36),collection,parent,fabric,fullness=.23))
    result.extend(_upholstered(name+' · respaldo oeste',(west_x,0,.68),
                  (.16,depth,.36),collection,parent,fabric,fullness=.23))
    parent['huella_poligono_xy_m']=[list(p) for p in footprint_xy]
    parent['huella_asset_m']=[width,depth]
    parent['altura_asset_m']=.86
    return result


def _blanket(name, location, size, col, parent, material):
    sx,sy=size;nx,ny=32,36;vertices=[];faces=[]
    for j in range(ny+1):
        y=(-.5+j/ny)*sy
        for i in range(nx+1):
            x=(-.5+i/nx)*sx
            u=x/(sx/2);v=y/(sy/2)
            # Small fabric folds and perimeter fall, not deep sculpted terrain.
            fold=.0038*math.sin(16*u+2.7*v)*math.sin(4.3*v+.3)
            fold+=.0027*math.sin(25*v-3*u)*math.cos(5*u)
            fall=-.027*(abs(u)**12)-.022*(max(0,-v)**12)
            vertices.append((x,y,fold+fall))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
    obj=_mesh(name,vertices,faces,col,parent,[material]);obj.location=location
    solid=obj.modifiers.new('Espesor de tejido 1.5mm','SOLIDIFY');solid.thickness=.0015;solid.offset=-1
    return obj


def make_bed(name, center, size, z, collection, mats):
    """Upholstered bed, closed mattress, layered linens; headboard at +Y."""
    parent=_parent(name,(center[0],center[1],z),collection)
    sx,sy=size;result=[parent]
    wood=_mat(mats,'madera_mesa','madera_clara_vertical','wood')
    fabric=_mat(mats,'tejido_tapizado','tejido','fabric')
    linen=_mat(mats,'tejido_sabanas','tejido_tapizado','tejido','fabric')
    metal=_mat(mats,'metal_mobiliario','carpinteria_antracita','frame')
    result.append(_box(name+' · bastidor',(0,-sy*.015,.205),
                  (sx*.985,sy*.975,.245),collection,parent,wood,.014))
    for x in (-sx*.38,sx*.38):
        for y in (-sy*.37,sy*.37):
            result.append(_rod(name+' · apoyo',(x,y,0),(x,y,.095),.025,.030,
                          collection,parent,metal))
    result.extend(_upholstered(name+' · cabecero cosido',(0,sy/2-.060,.607),
                  (sx,.12,1.01),collection,parent,fabric,fullness=.16,wrinkles=.0008))
    result.extend(_upholstered(name+' · colchón',(0,-sy*.019,.462),
                  (sx*.969,sy*.936,.265),collection,parent,linen,
                  fullness=.23,wrinkles=.0012))
    result.append(_blanket(name+' · sábana con pliegues',(0,-sy*.03,.599),
                  (sx*.965,sy*.902),collection,parent,linen))
    result.append(_blanket(name+' · manta ligera',(0,-sy*.160,.610),
                  (sx*.967,sy*.59),collection,parent,fabric))
    count=2 if sx>1.1 else 1
    for i in range(count):
        x=(i-(count-1)/2)*sx*.47
        result.extend(_upholstered(name+f' · almohada {i+1}',(x,sy*.288,.658),
                      (sx*.428 if count==2 else sx*.80,sy*.215,.145),
                      collection,parent,linen,fullness=.47,wrinkles=.0022))
    _fit_xy(parent,result,size)
    parent['altura_asset_m']=1.12
    parent['detalle_visual']='Colchón cerrado, ropa de cama por capas y almohadas cosidas'
    return result
