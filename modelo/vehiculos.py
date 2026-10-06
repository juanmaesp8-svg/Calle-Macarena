"""Sedanes procedurales de visualización, editables y sin activos externos.

El PDF sólo determina centro, orientación y caja XY del símbolo de aparcamiento.
La carrocería, los acabados, el habitáculo y la altura de 1,45 m son accesorios
visuales, no información arquitectónica ni un modelo de una marca concreta.
API compatible con la reconstrucción de Calle Macarena, Blender 4.3.
"""
import math
import bpy
from mathutils import Vector

PI = math.pi


def _mat(name, color, rough=.3, metal=0., transmission=0., coat=0., emission=0.):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = rough
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Transmission Weight'].default_value = transmission
    shader.inputs['IOR'].default_value = 1.49
    shader.inputs['Coat Weight'].default_value = coat
    shader.inputs['Coat Roughness'].default_value = .13
    if emission:
        shader.inputs['Emission Color'].default_value = (*color, 1)
        shader.inputs['Emission Strength'].default_value = emission
    material.diffuse_color = (*color, 1)
    material['procedencia'] = 'Material de accesorio visual procedural; sin activos externos'
    return material


def _lerp(a, b, t):
    return a + (b-a)*t


def _smooth_profile(points, t):
    """Monotone cubic Hermite interpolation; no station overshoot or creases."""
    if t <= points[0][0]:
        return points[0][1:]
    if t >= points[-1][0]:
        return points[-1][1:]
    index = next(i for i in range(len(points)-1) if points[i][0] <= t <= points[i+1][0])
    p, q = points[index], points[index+1]
    span = q[0]-p[0]
    f = (t-p[0])/span
    result = []
    for axis in range(1, len(p)):
        def slope(k):
            if k == 0:
                return (points[1][axis]-points[0][axis])/(points[1][0]-points[0][0])
            if k == len(points)-1:
                return (points[-1][axis]-points[-2][axis])/(points[-1][0]-points[-2][0])
            a = (points[k][axis]-points[k-1][axis])/(points[k][0]-points[k-1][0])
            b = (points[k+1][axis]-points[k][axis])/(points[k+1][0]-points[k][0])
            return 0. if a*b <= 0 else 2*a*b/(a+b)
        m, n = slope(index)*span, slope(index+1)*span
        result.append((2*f**3-3*f*f+1)*p[axis]+(f**3-2*f*f+f)*m
                      +(-2*f**3+3*f*f)*q[axis]+(f**3-f*f)*n)
    return tuple(result)


def make_car(name, center_xy, size_xy, collection, mats, z=0):
    """Return a sedan facing +Y with exact requested XY envelope incl. mirrors.

    All components are local to a parent Empty. A canonical 2.084 x 4.934 m
    sedan is scaled in XY only, never translated by changing its component
    geometry. The highest evaluated surface is the cambered roof at 1.45 m.
    Uses no architecture, camera, render, repository or network operations.
    """
    if len(center_xy) != 2 or len(size_xy) != 2 or min(size_xy) <= 0:
        raise ValueError('center_xy and positive size_xy must have two entries')
    if isinstance(collection, str):
        collection = bpy.data.collections.get(collection)
    if collection is None:
        raise ValueError('The target collection must already exist')
    parent = bpy.data.objects.new(name, None)
    collection.objects.link(parent)
    parent.empty_display_type = 'PLAIN_AXES'
    parent.empty_display_size = .35
    parent.location = (float(center_xy[0]), float(center_xy[1]), float(z))
    parent.scale = (float(size_xy[0])/2.084, float(size_xy[1])/4.934, 1.)
    parent['procedencia_xy'] = 'Centro y símbolo de aparcamiento del PDF, eje longitudinal Y'
    parent['altura'] = '1.45 m: accesorio de visualización, no cota del proyecto'
    parent['caja_xy_m'] = list(size_xy)
    parent['frente'] = '+Y'
    parent['sin_marca'] = True
    parent['generador'] = 'sedan_procedural_curvo_v2'
    objects = []
    silver = 'plata' in name.lower() or name.endswith('02') or name.endswith('2')
    paint = mats.get('coche_plata' if silver else 'coche_antracita') or _mat(
        'Coche · pintura plata' if silver else 'Coche · pintura antracita',
        (.39, .425, .46) if silver else (.058, .072, .086), .22, .78, coat=.95)
    rubber = _mat('Coche · caucho microtexturado', (.015, .017, .019), .77)
    trim = _mat('Coche · polímero oscuro', (.013, .016, .019), .42)
    alloy = _mat('Coche · aluminio cepillado', (.34, .37, .40), .23, .96)
    chrome = _mat('Coche · aluminio pulido', (.50, .53, .56), .12, 1.)
    glass = _mat('Coche · vidrio automóvil neutro', (.72, .77, .79), .045, transmission=1.)
    fabric = mats.get('cuero_claro') or mats.get('tejido_tapizado') or mats.get('tejido') or _mat(
        'Coche · tapicería gris cálido', (.105, .09, .078), .88)
    lamp_lens = _mat('Coche · lente óptica clara', (.83, .87, .89), .075, transmission=.75)
    lamp_inside = _mat('Coche · reflector óptico', (.62, .67, .69), .14, .92)
    led = _mat('Coche · LED diurno', (.87, .93, 1.), .16, emission=.18)
    red_lens = _mat('Coche · lente piloto rojo', (.28, .007, .004), .14, transmission=.15, coat=.6)
    brake = _mat('Coche · acero disco', (.13, .14, .15), .4, .82)
    if not rubber.node_tree.nodes.get('Micro relieve caucho'):
        nodes, links = rubber.node_tree.nodes, rubber.node_tree.links
        noise = nodes.new('ShaderNodeTexNoise'); noise.name = 'Micro relieve caucho'
        noise.inputs['Scale'].default_value = 200
        noise.inputs['Detail'].default_value = 2
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .22
        bump.inputs['Distance'].default_value = .00045
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], nodes.get('Principled BSDF').inputs['Normal'])

    def mesh(suffix, vertices, faces, material, smooth=True):
        data = bpy.data.meshes.new(name+' · '+suffix)
        data.from_pydata(vertices, [], faces); data.update()
        obj = bpy.data.objects.new(name+' · '+suffix, data)
        collection.objects.link(obj); obj.parent = parent
        if material: data.materials.append(material)
        for polygon in data.polygons: polygon.use_smooth = smooth
        obj['tipo'] = 'Accesorio de visualización; no elemento arquitectónico'
        objects.append(obj)
        return obj

    def surface(suffix, func, nu, nv, material, thickness=0., flip=False):
        vertices = [func(i/nu, j/nv) for j in range(nv+1) for i in range(nu+1)]
        faces = []
        for j in range(nv):
            for i in range(nu):
                a = j*(nu+1)+i
                face=(a, a+1, a+nu+2, a+nu+1)
                faces.append(tuple(reversed(face)) if flip else face)
        obj = mesh(suffix, vertices, faces, material)
        if thickness:
            mod = obj.modifiers.new('Espesor cerrado', 'SOLIDIFY')
            mod.thickness = thickness; mod.offset = -1.
            mod.use_even_offset = True
        return obj

    def line(suffix, points, material, radius=.004, resolution=1):
        data = bpy.data.curves.new(name+' · '+suffix, 'CURVE')
        data.dimensions = '3D'; data.resolution_u = 1
        data.bevel_depth = radius; data.bevel_resolution = resolution
        data.use_fill_caps = True
        spline = data.splines.new('POLY'); spline.points.add(len(points)-1)
        for point, xyz in zip(spline.points, points): point.co = (*xyz, 1)
        obj = bpy.data.objects.new(name+' · '+suffix, data)
        collection.objects.link(obj); obj.parent = parent; data.materials.append(material)
        obj['tipo'] = 'Accesorio de visualización; no elemento arquitectónico'
        objects.append(obj)
        return obj

    def box(suffix, xyz, dimensions, material, bevel=.012):
        x, y, zz = xyz; a, b, c = [v/2 for v in dimensions]
        vertices = [(x+sx*a,y+sy*b,zz+sz*c) for sz in (-1,1) for sy in (-1,1) for sx in (-1,1)]
        obj = mesh(suffix, vertices, [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],material,False)
        if bevel:
            modifier = obj.modifiers.new('Radio de arista', 'BEVEL')
            modifier.width = bevel; modifier.segments = 2
            normal = obj.modifiers.new('Normales ponderadas', 'WEIGHTED_NORMAL')
            normal.keep_sharp = True
        return obj

    def revolution(suffix, profile, xyz, material, n=64):
        """Surface of revolution about local X; exact profile, editable quads."""
        vertices = []
        for xx, radius in profile:
            vertices += [(xyz[0]+xx,xyz[1]+radius*math.sin(2*PI*j/n),
                          xyz[2]+radius*math.cos(2*PI*j/n)) for j in range(n)]
        faces=[]
        for row in range(len(profile)-1):
            for j in range(n):
                faces.append((row*n+j,(row+1)*n+j,(row+1)*n+(j+1)%n,row*n+(j+1)%n))
        return mesh(suffix,vertices,faces,material)

    # Organic sheet metal: 61 longitudinal stations and 48 smooth transverse
    # superellipse samples, broad hood crown and continuous curved shoulders.
    stations = [(-2.35,.823,.812,.285),(-2.12,.888,.881,.275),(-1.78,.929,.947,.27),
                (-1.28,.935,.962,.27),(-.55,.931,.964,.27),(.55,.931,.972,.27),
                (1.22,.935,.973,.27),(1.75,.915,.929,.275),(2.14,.865,.848,.28),
                (2.35,.809,.802,.29)]
    def section(y): return _smooth_profile(stations,y)
    def cross(y, theta):
        w, top, bottom = section(y); c=(top+bottom)/2; h=(top-bottom)/2
        ss, cc = math.sin(theta), math.cos(theta)
        return (w*math.copysign(abs(ss)**(1/3),ss),y,c+h*math.copysign(abs(cc)**(1/3),cc))
    nr, nt = 61, 48
    vertices = [cross(-2.35+4.70*i/(nr-1),2*PI*j/nt) for i in range(nr) for j in range(nt)]
    faces = []
    for i in range(nr-1):
        for j in range(nt):
            faces.append((i*nt+j,i*nt+(j+1)%nt,(i+1)*nt+(j+1)%nt,(i+1)*nt+j))
    # Convex front/rear fascia close the loft with concentric curved bands.
    for sign, base_row in ((-1,0),(1,(nr-1)*nt)):
        yy=sign*2.35; w,top,bottom=section(yy); center=(top+bottom)/2
        last=[base_row+j for j in range(nt)]
        for radius in (.85,.65,.42,.20):
            ring=[]
            for j in range(nt):
                x,_,zz=cross(yy,2*PI*j/nt)
                ring.append(len(vertices)); vertices.append((radius*x,yy+sign*.117*(1-radius*radius),center+(zz-center)*radius))
            for j in range(nt):
                face=(last[j],last[(j+1)%nt],ring[(j+1)%nt],ring[j])
                faces.append(face if sign==1 else tuple(reversed(face)))
            last=ring
        index=len(vertices); vertices.append((0,sign*2.467,center))
        for j in range(nt):
            face=(last[j],last[(j+1)%nt],index)
            faces.append(face if sign==1 else tuple(reversed(face)))
    body = mesh('Carrocería curva continua',vertices,faces,paint)
    # Explicit wheel openings through both sides; no wheels embedded in boxes.
    for ay in (-1.51,1.46):
        cut=revolution('Cortador temporal paso rueda',[(-1.18,.369),(1.18,.369)],(0,ay,.34),None)
                # Add cylinder caps, outward normals by matching the revolution winding.
        data=cut.data
        vv=[tuple(v.co) for v in data.vertices]
        ff=[tuple(p.vertices) for p in data.polygons]
        ff += [tuple(range(64)),tuple(reversed(range(64,128)))]
        replacement=bpy.data.meshes.new('Cilindro de corte cerrado')
        replacement.from_pydata(vv,[],ff);replacement.update();cut.data=replacement
        modifier=body.modifiers.new('Paso rueda circular exacto','BOOLEAN')
        modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cut
        bpy.context.view_layer.objects.active=body
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        objects.remove(cut);bpy.data.objects.remove(cut,do_unlink=True)
    # Very small crease-free lip. Boolean adds openings; does not facet shoulders.
    bevel=body.modifiers.new('Canto chapa en pasos de rueda','BEVEL')
    bevel.width=.004;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.45
    body['malla_carroceria']='Loft cúbico monótono 61x48; remates convexos y pasos rueda booleanos'
    box('Bajos y umbrales',(0,0,.264),(1.60,3.84,.10),trim,.028)
    def sidepoint(s,y,zz,offset=.001):
        w,top,bottom=section(y);c=(top+bottom)/2;h=(top-bottom)/2
        v=min(.9999,abs((zz-c)/h))
        return (s*(w*(1-v**6)**(1/6)+offset),y,zz)

    # Cambered roof and bent laminated glazing. Glass is a closed thin shell,
    # never a plane through a solid black cabin. All top/bottom edges coincide.
    def roof_y(t): return -.78+1.02*t
    def roof_height(t): return 1.432+.018*math.sin(PI*t)-.004*t
    def roof_width(t): return .705+.006*math.sin(PI*t)+.002*t
    roof=surface('Techo abombado',lambda u,t:((2*u-1)*roof_width(t),roof_y(t),roof_height(t)-.036*(2*u-1)**2),20,16,paint,.023)
    # Roof upper surface reaches 1.45 exactly; smooth interpolation is normalized
    # below together with all accessory components, without changing XY.
    def wind(u,t):
        v=2*u-1;w=_lerp(.707,.853,t);y=_lerp(.24,1.238,t)
        zz=_lerp(1.428,.962,t)+.009*math.sin(PI*t)-_lerp(.036,.023,t)*v*v
        return (v*w,y-.031*(1-v*v)*math.sin(PI*t),zz)
    def rear(u,t):
        v=2*u-1;w=_lerp(.705,.846,t);y=_lerp(-.78,-1.468,t)
        zz=_lerp(1.432,.951,t)+.011*math.sin(PI*t)-_lerp(.036,.018,t)*v*v
        return (v*w,y+.025*(1-v*v)*math.sin(PI*t),zz)
    surface('Parabrisas laminado curvo',wind,20,12,glass,.0055)
    surface('Luneta laminada curva',rear,20,10,glass,.005,flip=True)
    for label,fn in (('parabrisas',wind),('luneta',rear)):
        for edge in (0,1):
            line('Junta '+label+' '+str(edge),[fn(i/20,edge) for i in range(21)],trim,.008)
        for side in (0,1):
            line('Pilar '+label+' '+str(side),[fn(side,i/16) for i in range(17)],paint,.027)
    for s in (-1,1):
        # Four-sided curved side glazing split by an actual B-pillar.
        rear_corners=[(-1.430,.935,.853),(-.205,.941,.858),(-.205,1.410,.714),(-.767,1.395,.705)]
        front_corners=[(-.130,.941,.858),(1.180,.950,.853),(.219,1.392,.708),(-.130,1.410,.714)]
        def glass_patch(corners,u,v):
            a,b,c,d=corners
            yl=_lerp(a[0],d[0],v);yr=_lerp(b[0],c[0],v)
            zz=_lerp(_lerp(a[1],b[1],u),_lerp(d[1],c[1],u),v)
            xx=_lerp(_lerp(a[2],b[2],u),_lerp(d[2],c[2],u),v)+.006*math.sin(PI*u)*math.sin(PI*v)
            return(s*xx,_lerp(yl,yr,u),zz)
        for label,corners in (('trasera',rear_corners),('delantera',front_corners)):
            surface(f'Ventanilla {label} {s:+d}',lambda u,v,c=corners:glass_patch(c,u,v),10,7,glass,.004,flip=(s<0))
            outline=[]
            outline += [glass_patch(corners,i/12,0) for i in range(13)]
            outline += [glass_patch(corners,1,i/8) for i in range(1,9)]
            outline += [glass_patch(corners,1-i/12,1) for i in range(1,13)]
            outline += [glass_patch(corners,0,1-i/8) for i in range(1,9)]
            line(f'Burlete ventana {label} {s:+d}',outline+[outline[0]],trim,.010)
        line(f'Pilar B {s:+d}',[(s*_lerp(.858,.714,i/12),-.167,_lerp(.941,1.411,i/12)) for i in range(13)],trim,.037)
        line(f'Canal techo {s:+d}',[(s*roof_width(i/20),roof_y(i/20),roof_height(i/20)-.036) for i in range(21)],paint,.015)
        belt=[(s*.851,-1.468,.932),(s*.861,-.2,.943),(s*.859,.65,.949),(s*.855,1.238,.939)]
        line(f'Moldura de cintura {s:+d}',belt,chrome,.006)
        # Paint aprons connect glass base to sheet-metal shoulder continuously.
        apron=[(-1.47,.850,.933),(-.20,.858,.941),(.60,.858,.946),(1.24,.853,.939)]
        vv=[];ff=[]
        for k in range(25):
            yy=-1.47+2.71*k/24;xx,zz=_smooth_profile(apron,yy)
            vv.append(sidepoint(s,yy,.881));vv.append((s*xx,yy,zz))
            if k:
                face=(2*k-2,2*k,2*k+1,2*k-1)
                ff.append(face if s>0 else tuple(reversed(face)))
        mesh(f'Hombro bajo cristales {s:+d}',vv,ff,paint)
        for label,path in [('trasera',[(-1.26,.863),(-1.22,.77),(-1.15,.46),(-1.04,.413),(-.20,.413),(-.166,.86)]),
                           ('delantera',[(-.166,.86),(-.18,.46),(-.10,.413),(.995,.413),(1.07,.46),(1.15,.82),(1.11,.87)])]:
            pts=[]
            for a,b in zip(path,path[1:]):
                for j in range(5):
                    yy=_lerp(a[0],b[0],j/5);zz=_lerp(a[1],b[1],j/5)
                    pts.append(sidepoint(s,yy,zz,.002))
            pts.append(sidepoint(s,*path[-1],.002))
            line(f'Junta puerta {label} {s:+d}',pts,trim,.0022,1)
        for yy in (-.77,.62):
            point=sidepoint(s,yy,.836,.008)
            line(f'Tirador enrasado {s:+d} {yy}',[(point[0],yy-.075,.836),(point[0]+s*.010,yy-.055,.841),(point[0]+s*.010,yy+.055,.841),(point[0],yy+.075,.836)],chrome,.010)
        # Mirror envelopes reach +/-1.042 m. Rounded housing stays inside it.
        line(f'Brazo retrovisor {s:+d}',[(s*.850,.77,.979),(s*.926,.81,1.017)],trim,.022)
        # Ellipsoidal housing mesh, local X/Y/Z: convex painted shell plus glass.
        verts=[];faces=[];ns=16
        for j in range(9):
            t=PI*j/8;xx=s*(.980+.062*math.cos(t))
            for k in range(ns):
                a=2*PI*k/ns;verts.append((xx,.834+.119*math.sin(t)*math.cos(a),1.037+.046*math.sin(t)*math.sin(a)))
        for j in range(8):
            for k in range(ns):faces.append((j*ns+k,j*ns+(k+1)%ns,(j+1)*ns+(k+1)%ns,(j+1)*ns+k))
        mesh(f'Retrovisor carcasa {s:+d}',verts,faces,paint)
        surface(f'Retrovisor espejo {s:+d}',lambda u,v:(s*(.949+.066*u),.731-.002*math.sin(PI*u)*math.sin(PI*v),1.017+.038*v),6,3,chrome,.002,flip=(s<0))

    # Recessed four-seat interior with continuous dashboard and seat upholstery.
    box('Suelo habitáculo',(0,-.15,.73),(1.48,2.57,.065),trim,.022)
    box('Bandeja trasera',(0,-1.08,.909),(1.49,.55,.042),trim,.022)
    box('Salpicadero',(0,.967,.934),(1.53,.43,.100),trim,.043)
    box('Consola central',(0,.17,.826),(.24,.80,.18),trim,.025)
    box('Pantalla central',(0,.876,1.005),(.21,.018,.096),trim,.009)
    for yy in (-.83,.18):
        for xx in (-.44,.44):
            box(f'Asiento base {xx} {yy}',(xx,yy,.818),(.445,.50,.16),fabric,.067)
            seat=box(f'Respaldo {xx} {yy}',(xx,yy-.175,1.038),(.455,.154,.43),fabric,.056)
            # Rotate around its actual center; cube vertices are already local.
            center=Vector((xx,yy-.175,1.038))
            for vertex in seat.data.vertices:
                delta=vertex.co-center
                vertex.co=(center.x+delta.x,center.y+delta.y*.987-delta.z*.16,center.z+delta.y*.16+delta.z*.987)
            box(f'Reposacabezas {xx} {yy}',(xx,yy-.204,1.270),(.245,.14,.14),fabric,.037)
            for dx in (-.135,.135):
                line(f'Costura asiento {xx} {yy} {dx}',[(xx+dx,yy-.259,.88),(xx+dx,yy-.287,1.06),(xx+dx,yy-.316,1.18)],trim,.0015,1)
    # Steering toroid and its three spokes, inside the windshield.
    wheel_profile=[(.019*math.sin(2*PI*j/8),.153+.019*math.cos(2*PI*j/8)) for j in range(9)]
    steering=revolution('Aro volante',wheel_profile,(0,0,0),trim,n=32)
    from mathutils import Matrix
    rotation=Matrix.Rotation(math.radians(72),4,'X')@Matrix.Rotation(PI/2,4,'Y')
    for vertex in steering.data.vertices:vertex.co=rotation@vertex.co+Vector((-.44,.692,1.018))
    box('Buje volante',(-.44,.692,1.018),(.073,.035,.077),trim,.022)
    for angle in (PI/2,PI*7/6,PI*11/6):
        end=Vector((-.44+.131*math.cos(angle),.692+.040*math.sin(angle),1.018+.122*math.sin(angle)))
        line(f'Radio volante {angle:.2f}',[(-.44,.692,1.018),end],alloy,.011)

    # Radial tyre mesh: broad real tread, curved sidewalls, recessed channels,
    # rim barrel, bead, ten swept spokes, brake rotor, caliper and five bolts.
    tyre_profile=[(-.111,.237),(-.111,.274),(-.102,.310),(-.082,.333),(-.064,.340),
                  (-.046,.340),(-.043,.335),(-.035,.335),(-.032,.340),
                  (.032,.340),(.035,.335),(.043,.335),(.046,.340),(.064,.340),
                  (.082,.333),(.102,.310),(.111,.274),(.111,.237),(-.111,.237)]
    for ay in (-1.51,1.46):
        for s in (-1,1):
            cx=s*.817
            revolution(f'Neumático perfilado {s:+d} {ay}',tyre_profile,(cx,ay,.34),rubber,n=56)
            outer=s*.929
            revolution(f'Llanta barril {s:+d} {ay}',[(-s*.166,.221),(-s*.161,.231),(-s*.023,.231),(0,.226),(s*.006,.216),(s*.002,.207),(-s*.013,.202)],(outer,ay,.34),alloy)
            revolution(f'Disco freno {s:+d} {ay}',[(-s*.052,0),(-s*.052,.192),(-s*.039,.192),(-s*.039,0)],(outer,ay,.34),brake)
            # Ten swept paired spokes are compact volumetric sculpted plates.
            for j in range(10):
                a=2*PI*j/10;aa=a+(.038 if j%2 else -.038)
                shape=[(.044,aa-.092),(.178,aa+.057),(.219,aa+.041),(.218,aa-.054),(.175,aa-.049),(.056,aa-.170)]
                vv=[]
                for depth in (-.012,.009):
                    vv += [(outer+s*depth,ay+r*math.sin(t),.34+r*math.cos(t)) for r,t in shape]
                nn=len(shape);ff=[tuple(reversed(range(nn))),tuple(range(nn,2*nn))]
                ff +=[(k,(k+1)%nn,(k+1)%nn+nn,k+nn) for k in range(nn)]
                spoke=mesh(f'Radio llanta {s:+d} {ay} {j}',vv,ff,alloy,False)
                bevel=spoke.modifiers.new('Canto fresado','BEVEL');bevel.width=.0015;bevel.segments=2
                normal=spoke.modifiers.new('Normal fresado','WEIGHTED_NORMAL');normal.keep_sharp=True
            revolution(f'Buje llanta {s:+d} {ay}',[(0,0),(0,.052),(s*.021,.054),(s*.025,.044),(s*.025,0)],(outer,ay,.34),alloy,n=32)
            for k in range(5):
                a=2*PI*k/5
                revolution(f'Tornillo {s:+d} {ay} {k}',[(0,0),(0,.008),(s*.008,.008),(s*.009,0)],(outer+s*.025,ay+.035*math.sin(a),.34+.035*math.cos(a)),chrome,n=6)
            box(f'Pinza freno {s:+d} {ay}',(s*.875,ay+.152,.361),(.034,.058,.115),trim,.012)
            for rr in (.279,.300):
                revolution(f'Relieve flanco {s:+d} {ay} {rr}',[(s*.001*math.sin(2*PI*k/6),rr+.001*math.cos(2*PI*k/6)) for k in range(7)],(s*.921,ay,.34),rubber,n=48)
            # Quiet tread sipes, shallow relief on real tread, not tractor lugs.
            for k in range(24):
                a=2*PI*k/24
                points=[]
                for j in range(5):
                    xx=-.068+.136*j/4;theta=a+.020*math.sin(PI*j/4)
                    points.append((cx+xx,ay+.3403*math.sin(theta),.34+.3403*math.cos(theta)))
                line(f'Laminilla caucho {s:+d} {ay} {k}',points,trim,.0007,0)
            arc=[sidepoint(s,ay+.371*math.cos(PI*j/40),.34+.371*math.sin(PI*j/40),.0015) for j in range(41)]
            line(f'Reborde metálico paso rueda {s:+d} {ay}',arc,paint,.003,1)

    # Integrated lights, grille and bumper details follow the convex fascia.
    def fascia(sign,x,zz,offset=.003):
        w,top,bottom=section(sign*2.35);center=(top+bottom)/2;h=(top-bottom)/2
        r=(abs(x/w)**6+abs((zz-center)/h)**6)**(1/6)
        return (x,sign*(2.35+.117*(1-min(1,r*r))+offset),zz)
    for s in (-1,1):
        def lamp_patch(u,v):
            x=s*_lerp(.32,.746,u)
            low=_lerp(.688,.695,u);high=_lerp(.755,.778,u)
            return fascia(1,x,_lerp(low,high,v),.005)
        surface(f'Faro reflector {s:+d}',lamp_patch,12,4,lamp_inside,.006,flip=(s>0))
        surface(f'Faro lente cerrada {s:+d}',lambda u,v:tuple(Vector(lamp_patch(u,v))+Vector((0,.004,0))),12,4,lamp_lens,.004,flip=(s>0))
        outline=[lamp_patch(i/16,0) for i in range(17)]+[lamp_patch(1,i/4) for i in range(1,5)]+[lamp_patch(1-i/16,1) for i in range(1,17)]+[lamp_patch(0,1-i/4) for i in range(1,5)]
        line(f'Junta óptica delantera {s:+d}',outline+[outline[0]],trim,.004,1)
        line(f'Firma LED {s:+d}',[fascia(1,s*_lerp(.344,.724,i/20),_lerp(.747,.768,i/20),.011) for i in range(21)],led,.006,1)
        # Rear optic smoothly wraps convex tail; visibly red, no buried lights.
        surface(f'Piloto rojo {s:+d}',lambda u,v:fascia(-1,s*_lerp(.285,.75,u),_lerp(.693,.771,v)+.012*u,.006),12,4,red_lens,.006,flip=(s<0))
        line(f'Guía óptica trasera {s:+d}',[fascia(-1,s*_lerp(.30,.73,i/20),.748+.012*i/20,.011) for i in range(21)],red_lens,.007,1)
    surface('Parrilla negra convexa',lambda u,v:fascia(1,_lerp(-.29,.29,u),_lerp(.532,.668,v),.004),18,6,trim,.005,flip=True)
    for k in range(4):
        zz=.547+.029*k
        line(f'Lámina parrilla horizontal {k}',[fascia(1,-.274+.548*j/20,zz,.009) for j in range(21)],chrome,.003,1)
    surface('Toma aire inferior',lambda u,v:fascia(1,_lerp(-.57,.57,u),_lerp(.356,.428,v),.004),20,3,trim,.005,flip=True)
    surface('Difusor trasero',lambda u,v:fascia(-1,_lerp(-.62,.62,u),_lerp(.352,.438,v),.004),20,3,trim,.005)
    for sign,zz in ((1,.463),(-1,.55)):
        surface('Matrícula neutra '+str(sign),lambda u,v,si=sign,h=zz:fascia(si,_lerp(-.242,.242,u),h+_lerp(-.039,.039,v),.008),12,3,alloy,.004,flip=(sign>0))
    # Hood and trunk seams follow the crowned body instead of flat black boxes.
    for sign,yy in ((1,1.29),(-1,-1.44)):
        pts=[]
        for j in range(25):
            xx=-.72+1.44*j/24;w,top,bottom=section(yy);h=(top-bottom)/2;c=(top+bottom)/2
            zz=c+h*(1-abs(xx/w)**6)**(1/6)+.0015
            pts.append((xx,yy,zz))
        line('Junta capó' if sign==1 else 'Junta maletero',pts,trim,.0017,1)
    parent['neumaticos']=4
    parent['acabado_visual']='plata' if silver else 'antracita'
    parent['fuentes']='Generación matemática original; sin assets ni logotipos externos'
    # Normalize local evaluated bounds once: exact XY envelope includes the
    # optical skins and mirror extremes. Uniform per-axis change <1% canonical.
    # This is visual accessory calibration, never geometry of the architecture.
    bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    lo=[float('inf')]*3;hi=[float('-inf')]*3
    for obj in objects:
        if obj.type not in {'MESH','CURVE'}: continue
        evaluated=obj.evaluated_get(depsgraph)
        geometry=evaluated.to_mesh()
        for vertex in geometry.vertices:
            for axis in range(3):
                lo[axis]=min(lo[axis],vertex.co[axis]);hi[axis]=max(hi[axis],vertex.co[axis])
        evaluated.to_mesh_clear()
    factors=(2.084/(hi[0]-lo[0]),4.934/(hi[1]-lo[1]),1.45/(hi[2]-lo[2]))
    midpoint=((hi[0]+lo[0])/2,(hi[1]+lo[1])/2,lo[2])
    for obj in objects:
        if obj.type=='MESH':
            for vertex in obj.data.vertices:
                for axis in range(3): vertex.co[axis]=(vertex.co[axis]-midpoint[axis])*factors[axis]
        elif obj.type=='CURVE':
            # Geometry scales via object matrix (including bevel cross-section).
            obj.scale=factors
            obj.location=tuple(-midpoint[axis]*factors[axis] for axis in range(3))
    parent['calibracion_accesorio_xyz']=list(factors)
    parent['altura_visual_m']=1.45
    bpy.context.view_layer.update()
    return {'parent':parent,'objects':objects,'bbox_xy_m':tuple(map(float,size_xy)),'altura_visual_m':1.45}


if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection=bpy.data.collections.new('Test sedán')
    bpy.context.scene.collection.children.link(collection)
    result=make_car('Coche_01',(5.886335,3.781426),(2.084,4.934),collection,{})
    print('Sedán:',len(result['objects']),'objetos; centro:',tuple(result['parent'].location))
