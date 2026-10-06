"""Sedanes procedurales de visualización para Blender 4.3.

El PDF define ubicación, orientación y caja XY de sus símbolos, no fabricante,
acabado, altura ni detalles de coches. Esos detalles son accesorios de
visualización. No cambian los centros ni la caja XY solicitados.
"""
import math
import bpy
from mathutils import Vector


def _mat(name, color, rough=0.3, metal=0.0, transmission=0.0, coat=0.0, emission=0.0):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Transmission Weight'].default_value = transmission
    p.inputs['IOR'].default_value = 1.48
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Coat Roughness'].default_value = 0.12
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    m.diffuse_color = (*color, 1)
    return m


def make_car(name, center_xy, size_xy, collection, mats, z=0):
    """Create one sedan, front +Y, exact requested XY envelope incl. mirrors.

    Returns {'parent': Empty, 'objects': [...], 'bbox_xy_m': (w,l),
    'altura_visual_m': 1.45}. Meshes/curves have local coordinates under the
    Empty at center_xy/z. Objects are linked only to the supplied collection.
    Existing architecture and camera objects are not accessed or modified.
    No third-party assets, external texture files or identifying logos.
    """
    if len(center_xy) != 2 or len(size_xy) != 2 or min(size_xy) <= 0:
        raise ValueError('center_xy and positive size_xy must have 2 entries')
    if isinstance(collection, str):
        collection = bpy.data.collections.get(collection)
        if collection is None:
            raise ValueError('Collection must already exist')
    parent = bpy.data.objects.new(name, None)
    collection.objects.link(parent)
    parent.empty_display_type = 'PLAIN_AXES'
    parent.empty_display_size = 0.35
    parent.location = (float(center_xy[0]), float(center_xy[1]), float(z))
    parent.scale = (float(size_xy[0])/2.084, float(size_xy[1])/4.934, 1.0)
    parent['procedencia_xy'] = 'Centro y símbolo de aparcamiento del PDF, eje longitudinal Y'
    parent['altura'] = '1.45 m: accesorio de visualización, no cota del proyecto'
    parent['caja_xy_m'] = list(size_xy)
    parent['frente'] = '+Y'
    objects = []
    silver = ('plata' in name.lower() or name.endswith('02') or name.endswith('2'))
    paint = mats.get('coche_plata' if silver else 'coche_antracita') or _mat(
        'Coche · pintura plata' if silver else 'Coche · pintura antracita',
        (0.36, 0.385, 0.405) if silver else (0.068, 0.083, 0.098), 0.23, 0.82, coat=0.85)
    rubber = _mat('Coche · caucho neumático', (0.018, 0.021, 0.024), 0.80)
    trim = _mat('Coche · polímero oscuro', (0.023, 0.026, 0.03), 0.50)
    alloy = _mat('Coche · aluminio cepillado', (0.30, 0.32, 0.34), 0.28, 0.92)
    glass = _mat('Coche · vidrio ahumado', (0.17, 0.215, 0.25), 0.055, transmission=0.85, coat=0.2)
    fabric = _mat('Coche · tapicería gris cálido', (0.18, 0.16, 0.14), 0.87)
    headlight = _mat('Coche · lente faro blanco', (0.81, 0.88, 0.92), 0.14, 0.18, coat=0.5)
    led = _mat('Coche · LED diurno', (0.93, 0.96, 1.0), 0.2, emission=0.35)
    tail = _mat('Coche · lente piloto rojo', (0.35, 0.014, 0.008), 0.18, 0.1, coat=0.6)
    brake = _mat('Coche · acero disco', (0.12, 0.13, 0.14), 0.42, 0.8)

    def link(obj, suffix, material=None):
        obj.name = name + ' · ' + suffix
        for col in list(obj.users_collection):
            col.objects.unlink(obj)
        collection.objects.link(obj)
        obj.parent = parent
        if material is not None and hasattr(obj.data, 'materials'):
            obj.data.materials.append(material)
        obj['tipo'] = 'Accesorio de visualización; no elemento arquitectónico'
        objects.append(obj)
        return obj

    def mesh(suffix, verts, faces, material, smooth=True):
        data = bpy.data.meshes.new(name + ' · ' + suffix)
        data.from_pydata(verts, [], faces)
        data.update()
        obj = bpy.data.objects.new(name + ' · ' + suffix, data)
        collection.objects.link(obj)
        obj.parent = parent
        data.materials.append(material)
        for face in data.polygons:
            face.use_smooth = smooth
        objects.append(obj)
        return obj

    def bevel(obj, width=0.012, segments=2):
        mod = obj.modifiers.new('Redondeado de carrocería', 'BEVEL')
        mod.width = width
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        try:
            normal = obj.modifiers.new('Normales de superficie', 'WEIGHTED_NORMAL')
            normal.keep_sharp = True
            normal.weight = 40
        except Exception:
            pass
        return obj

    def cube(suffix, xyz, dimensions, material, rounded=0.0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
        obj = link(bpy.context.object, suffix, material)
        obj.scale = dimensions
        # Apply scale before parenting-transform modifications; local coordinates.
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if rounded:
            bevel(obj, rounded, 2)
        return obj

    def line(suffix, points, material, radius=0.007):
        data = bpy.data.curves.new(name + ' · ' + suffix, 'CURVE')
        data.dimensions = '3D'
        data.resolution_u = 1
        data.bevel_depth = radius
        data.bevel_resolution = 1
        sp = data.splines.new('POLY')
        sp.points.add(len(points)-1)
        for p, xyz in zip(sp.points, points):
            p.co = (*xyz, 1)
        obj = bpy.data.objects.new(name + ' · ' + suffix, data)
        collection.objects.link(obj)
        obj.parent = parent
        data.materials.append(material)
        objects.append(obj)
        return obj

    def panel(suffix, points, material, thickness=0.006):
        obj = mesh(suffix, points, [tuple(range(len(points)))], material, False)
        sol = obj.modifiers.new('Espesor de panel', 'SOLIDIFY')
        sol.thickness = thickness
        sol.offset = 0
        return obj

    # Eight-point rounded shoulder cross-sections from rear bumper to nose.
    stations = [(-2.452, .71, .84), (-2.38, .80, .88), (-2.03, .88, .925),
                (-1.48, .902, .955), (-.70, .905, .948), (.50, .905, .950),
                (1.27, .898, .982), (1.85, .86, .950), (2.35, .80, .88),
                (2.452, .71, .83)]
    verts = []
    for yy, w, top in stations:
        verts += [(-w*.86, yy, .33), (-w, yy, .46), (-w, yy, top-.11),
                  (-w*.84, yy, top), (w*.84, yy, top), (w, yy, top-.11),
                  (w, yy, .46), (w*.86, yy, .33)]
    faces = [tuple(reversed(range(8)))]
    for i in range(len(stations)-1):
        for j in range(8):
            faces.append((i*8+j, i*8+(j+1)%8, (i+1)*8+(j+1)%8, (i+1)*8+j))
    faces.append(tuple((len(stations)-1)*8+j for j in range(8)))
    body = mesh('Carrocería con pasos de rueda', verts, faces, paint)
    # Supported local boolean holes; a single cylinder creates each axle's two
    # wheel arches. Use unapplied parent position: everything is local to Empty.
    # Boolean object's transform is evaluated in world; parent cutter identically.
    for ay in (-1.49, 1.49):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.365, depth=2.3,
                                           location=(0, ay, .345), rotation=(0, math.pi/2, 0))
        cutter = bpy.context.object
        for col in list(cutter.users_collection):
            col.objects.unlink(cutter)
        collection.objects.link(cutter)
        cutter.parent = parent
        mod = body.modifiers.new('Paso de rueda', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = cutter
        bpy.context.view_layer.objects.active = body
        body.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        body.select_set(False)
        bpy.data.objects.remove(cutter, do_unlink=True)
    bevel(body, 0.055, 3)
    cube('Bajos y umbrales', (0, 0, .28), (1.57, 3.58, .08), trim, .02)

    # Cambered paint roof, glazing and visible structural pillars.
    roof_verts = []
    roof_ys = (-.78, -.42, .22)
    for yy in roof_ys:
        for j in range(9):
            x = -.69 + 1.38*j/8
            zz = 1.45 - .032*(abs(x)/.69)**2 - (.007 if yy == -.78 else 0)
            roof_verts.append((x, yy, zz))
    roof_faces = []
    for iy in range(2):
        for ix in range(8):
            a = iy*9+ix
            roof_faces.append((a, a+1, a+10, a+9))
    roof = mesh('Techo curvo', roof_verts, roof_faces, paint)
    sol = roof.modifiers.new('Espesor de techo', 'SOLIDIFY'); sol.thickness = .025; sol.offset = -1
    rear_glass = [(-.806, -1.43, .944), (.806, -1.43, .944), (.684, -.775, 1.404), (-.684, -.775, 1.404)]
    front_glass = [(-.815, 1.235, .976), (.815, 1.235, .976), (.684, .235, 1.418), (-.684, .235, 1.418)]
    panel('Luneta trasera', rear_glass, glass)
    panel('Parabrisas delantero', list(reversed(front_glass)), glass)
    line('Borde luneta', rear_glass+[rear_glass[0]], trim, .012)
    line('Borde parabrisas', front_glass+[front_glass[0]], trim, .012)
    for side in (-1, 1):
        s = side
        back = [(s*.805,-1.385,.965),(s*.826,-.205,.974),
                (s*.697,-.205,1.414),(s*.700,-.740,1.397)]
        front = [(s*.826,-.130,.974),(s*.817,1.165,.991),
                 (s*.699,.190,1.412),(s*.697,-.130,1.418)]
        panel(f'Cristal puerta trasera {side:+d}', back if side > 0 else list(reversed(back)), glass)
        panel(f'Cristal puerta delantera {side:+d}', front if side > 0 else list(reversed(front)), glass)
        line(f'Marco cristal trasero {side:+d}', back+[back[0]], trim,.012)
        line(f'Marco cristal delantero {side:+d}', front+[front[0]], trim,.012)
        line(f'Pilar B {side:+d}',[(s*.823,-.166,.965),(s*.697,-.166,1.423)],trim,.031)
        line(f'Pilar C {side:+d}',[(s*.808,-1.42,.939),(s*.699,-.770,1.415)],paint,.031)
        line(f'Pilar A {side:+d}',[(s*.821,1.223,.977),(s*.702,.237,1.422)],paint,.027)
        line(f'Moldura bajo ventanillas {side:+d}',[(s*.822,-1.48,.942),(s*.841,-.2,.952),(s*.835,1.25,.972)],alloy,.008)
        # Door shutlines below glazing, handles and side sill details.
        line(f'Junta puerta trasera {side:+d}',[(s*.906,-1.34,.852),(s*.910,-1.25,.72),(s*.899,-1.17,.42),(s*.899,-.18,.42),(s*.913,-.18,.866)],trim,.0035)
        line(f'Junta puerta delantera {side:+d}',[(s*.913,-.125,.866),(s*.900,-.125,.42),(s*.900,1.05,.42),(s*.910,1.15,.75),(s*.903,1.15,.875)],trim,.0035)
        for hy in (-.72,.54):
            cube(f'Tirador {side:+d} {hy}',(s*.915,hy,.81),(.025,.16,.028),alloy,.008)
        # Mirrors have actual envelope X=+/-1.042 exactly incl. housing.
        line(f'Soporte retrovisor {side:+d}',[(s*.830,.81,1.015),(s*.948,.81,1.020)],trim,.026)
        mirror = cube(f'Retrovisor {side:+d}',(s*.985,.84,1.042),(.114,.234,.095),paint,.033)
        cube(f'Cristal retrovisor {side:+d}',(s*.985,.717,1.043),(.088,.007,.062),alloy,.01)

    # Interior is visible through tinted glazing instead of a black cabin block.
    cube('Bandeja trasera',(0,-1.09,.910),(1.44,.68,.033),trim,.016)
    cube('Salpicadero',(0,.93,.913),(1.48,.47,.08),trim,.025)
    for yy in (-.85,.18):
        for xx in (-.43,.43):
            cube(f'Asiento {xx} {yy}',(xx,yy,.79),(.43,.46,.17),fabric,.065)
            cube(f'Respaldo {xx} {yy}',(xx,yy-.16,1.025),(.43,.13,.47),fabric,.055)
            cube(f'Reposacabezas {xx} {yy}',(xx,yy-.13,1.235),(.24,.13,.16),fabric,.04)
    # Steering torus approximately normal to windshield, recessed in cabin.
    bpy.ops.mesh.primitive_torus_add(major_radius=.16,minor_radius=.019,
        major_segments=24,minor_segments=8,location=(-.43,.63,1.02),rotation=(math.radians(68),0,0))
    steering = link(bpy.context.object,'Volante',trim)
    for f in steering.data.polygons:f.use_smooth=True

    # Rubber tori, silver wheel centres, brake discs and five swept spokes.
    for ay in (-1.49, 1.49):
        for s in (-1,1):
            ax=s*.840
            bpy.ops.mesh.primitive_torus_add(major_radius=.268,minor_radius=.077,
                major_segments=48,minor_segments=12,location=(ax,ay,.345),rotation=(0,math.pi/2,0))
            wheel = link(bpy.context.object,f'Neumático {s:+d} {ay}',rubber)
            for f in wheel.data.polygons:f.use_smooth=True
            # subtle rubber microstructure, not large unrealistic bump
            tire_shader=rubber.node_tree.nodes.get('Principled BSDF')
            if 'Tread micro' not in rubber.node_tree.nodes:
                n=rubber.node_tree.nodes.new('ShaderNodeTexNoise');n.name='Tread micro';n.inputs['Scale'].default_value=120
                bump=rubber.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0006
                rubber.node_tree.links.new(n.outputs['Fac'],bump.inputs['Height']);rubber.node_tree.links.new(bump.outputs['Normal'],tire_shader.inputs['Normal'])
            outer=s*.915
            bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.21,depth=.028,location=(s*.879,ay,.345),rotation=(0,math.pi/2,0))
            disc=link(bpy.context.object,f'Disco freno {s:+d} {ay}',brake)
            for f in disc.data.polygons:f.use_smooth=True
            bpy.ops.mesh.primitive_torus_add(major_radius=.204,minor_radius=.017,major_segments=32,minor_segments=6,location=(outer,ay,.345),rotation=(0,math.pi/2,0))
            rim=link(bpy.context.object,f'Aro llanta {s:+d} {ay}',alloy)
            for f in rim.data.polygons:f.use_smooth=True
            bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.055,depth=.032,location=(outer,ay,.345),rotation=(0,math.pi/2,0))
            hub=link(bpy.context.object,f'Buje llanta {s:+d} {ay}',alloy)
            for k in range(5):
                a=2*math.pi*k/5
                py=ay+.128*math.sin(a);pz=.345+.128*math.cos(a)
                spoke=cube(f'Radio llanta {s:+d} {ay} {k}',(outer,py,pz),(.024,.040,.165),alloy,.006)
                spoke.rotation_euler.x=-a
                bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.007,location=(outer+s*.023,ay+.038*math.sin(a),.345+.038*math.cos(a)))
                link(bpy.context.object,f'Tornillo llanta {s:+d} {ay} {k}',alloy)
            # Exterior circular welt preserves readable fender/wheel clearance.
            arc=[]
            for j in range(19):
                a=math.pi*j/18
                arc.append((s*.906,ay+.368*math.cos(a),.345+.368*math.sin(a)))
            line(f'Labio paso rueda {s:+d} {ay}',arc,paint,.008)

    # Headlamps and tail lamps on separate compact fender panels.
    for s in (-1,1):
        lamp=[(s*.26,2.460,.709),(s*.675,2.460,.719),(s*.665,2.460,.819),(s*.26,2.460,.799)]
        panel(f'Faro delantero {s:+d}',lamp,headlight,.009)
        line(f'Firma LED {s:+d}',[(s*.28,2.458,.794),(s*.638,2.458,.809)],led,.009)
        rear=[(s*.31,-2.460,.724),(s*.667,-2.460,.733),(s*.661,-2.460,.824),(s*.31,-2.460,.815)]
        panel(f'Piloto trasero {s:+d}',rear,tail,.009)
        line(f'Detalle óptica trasera {s:+d}',[(s*.34,-2.458,.798),(s*.637,-2.458,.809)],tail,.009)
    cube('Parrilla frontal',(0,2.456,.580),(.74,.012,.158),trim,.027)
    for xx in (-.29,-.145,0,.145,.29):
        cube(f'Lámina parrilla {xx}',(xx,2.465,.58),(.019,.004,.113),alloy,.003)
    cube('Toma de aire inferior',(0,2.456,.410),(1.1,.012,.080),trim,.018)
    cube('Difusor trasero',(0,-2.456,.405),(1.25,.012,.100),trim,.012)
    cube('Panel matrícula sin texto delantero',(0,2.460,.455),(.49,.009,.077),alloy,.004)
    cube('Panel matrícula sin texto trasero',(0,-2.4625,.549),(.49,.009,.082),alloy,.004)
    # Wheel count and explicitly documented visual property metadata.
    parent['neumaticos'] = 4
    parent['acabado_visual'] = 'plata' if silver else 'antracita'
    parent['sin_marca'] = True
    bpy.context.view_layer.update()
    return {'parent':parent,'objects':objects,'bbox_xy_m':tuple(map(float,size_xy)),
            'altura_visual_m':1.45}


if __name__ == '__main__':
    c=bpy.data.collections.new('Test coches')
    bpy.context.scene.collection.children.link(c)
    r=make_car('Coche_01',(5.886335,3.781426),(2.084,4.934),c,{})
    print('Coche:',len(r['objects']),'objetos; centro:',tuple(r['parent'].location))
