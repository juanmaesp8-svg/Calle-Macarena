"""Detalle decorativo de exteriores, sin modificar la geometría arquitectónica.

API: aplicar_exteriores(scene) se ejecuta sobre el modelo V2 reconstruido.
Los contornos y centros del mobiliario proceden de datos_mobiliario.json.
El fondo oculto bajo tablero de las sillas se reconstruye como accesorio.
La geometría es procedural original. El lino comparte el mapa fotográfico
Fabric040 CC0 de assets/texturas/ambientcg y sus archivos de procedencia.
"""
from pathlib import Path
import hashlib
import json
import math
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vegetacion_mobiliario as furniture
import vegetacion_v2 as vegetation

ROOT = Path(__file__).resolve().parents[1]
NOTE = 'V3 accesorio decorativo original; no constituye información constructiva del PDF.'
LOUNGER_SOURCE = [
    {'nombre':'Tumbona_piscina_01', 'tipo':'tumbona_exterior', 'seqno_pdf_final':1115,
     'bbox_pdf_pt':[315.44000244140625,676.0,353.239990234375,690.1600341796875],
     'bbox_xy_m':[11.772900129191083,4.241798191324873,13.77314948323568,4.991100000000003]},
    {'nombre':'Tumbona_piscina_02', 'tipo':'tumbona_exterior', 'seqno_pdf_final':1117,
     'bbox_pdf_pt':[315.44000244140625,694.239990234375,353.239990234375,708.4000244140625],
     'bbox_xy_m':[11.772900129191083,3.2765987080891956,13.77314948323568,4.025900516764326]},
]


def _mat(name, color, roughness=.5, metallic=0):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    mat['procedencia'] = NOTE
    return mat


def _materials():
    fabric = _mat('V3 exterior · lino técnico greige', (.42, .383, .322), .86)
    if not fabric.node_tree.nodes.get('Trama técnica original'):
        nodes, links = fabric.node_tree.nodes, fabric.node_tree.links
        shader = nodes.get('Principled BSDF')
        shader.inputs['Sheen Weight'].default_value = .2
        shader.inputs['Sheen Roughness'].default_value = .72
        tex = nodes.new('ShaderNodeTexCoord')
        wave = nodes.new('ShaderNodeTexWave'); wave.name = 'Trama técnica original'
        wave.wave_type = 'BANDS'; wave.bands_direction = 'DIAGONAL'
        wave.inputs['Scale'].default_value = 780
        wave.inputs['Distortion'].default_value = 1.1
        links.new(tex.outputs['Object'], wave.inputs['Vector'])
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 3100
        noise.inputs['Detail'].default_value = 2
        links.new(tex.outputs['Object'], noise.inputs['Vector'])
        multiply = nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
        links.new(wave.outputs['Color'], multiply.inputs[0])
        links.new(noise.outputs['Fac'], multiply.inputs[1])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .32
        bump.inputs['Distance'].default_value = .00012
        links.new(multiply.outputs[0], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    rope = _mat('V3 exterior · cuerda trenzada arena', (.23, .185, .132), .74)
    if not rope.node_tree.nodes.get('Microfibra cuerda'):
        nodes, links = rope.node_tree.nodes, rope.node_tree.links
        shader = nodes.get('Principled BSDF')
        noise = nodes.new('ShaderNodeTexNoise'); noise.name = 'Microfibra cuerda'
        noise.inputs['Scale'].default_value = 2400
        noise.inputs['Detail'].default_value = 3
        bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .23
        bump.inputs['Distance'].default_value = .00013
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    metal = _mat('V3 exterior · aluminio grafito satinado', (.028, .031, .032), .38, .12)
    stone = _mat('V3 exterior · piedra porcelánica mesa crema', (.55, .50, .41), .44)
    if not stone.node_tree.nodes.get('Poro mesa piedra'):
        nodes, links = stone.node_tree.nodes, stone.node_tree.links
        noise = nodes.new('ShaderNodeTexNoise'); noise.name = 'Poro mesa piedra'
        noise.inputs['Scale'].default_value = 220
        noise.inputs['Detail'].default_value = 4
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (.47, .43, .36, 1)
        ramp.color_ramp.elements[1].color = (.59, .55, .47, 1)
        links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], nodes.get('Principled BSDF').inputs['Base Color'])
        bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .12
        bump.inputs['Distance'].default_value = .00008
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], nodes.get('Principled BSDF').inputs['Normal'])
    # El helper conserva el tinte pero incorpora altura/rugosidad fotográfica
    # Fabric040 CC0 a escala métrica; los archivos se empaquetan en el blend.
    from materiales import aplicar_lino_fotografico
    aplicar_lino_fotografico(fabric, color=(.42, .383, .322), escala_m=.16)
    return {'fabric': fabric, 'rope': rope, 'metal': metal, 'stone': stone}


def _delete_asset(name):
    obj = bpy.data.objects.get(name)
    if not obj:
        return
    descendants = list(obj.children_recursive)
    for child in reversed(descendants):
        data = child.data if child.type in {'MESH', 'CURVE'} else None
        bpy.data.objects.remove(child, do_unlink=True)
        if data and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
    data = obj.data if obj.type in {'MESH', 'CURVE'} else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if data and data.users == 0 and isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)


def _rod(name, a, b, radius, col, parent, mat, sides=10):
    return furniture._rod(name, a, b, radius, radius, col, parent, mat, sides=sides)


def _weave_back(name, width, y, z0, z1, col, parent, mats):
    """Cuerda continua con leve ondulación de trenzado; huecos reales, sin alpha."""
    result = []
    count = max(12, round(width/.025))
    for i in range(count):
        x = (-.5+(i+.5)/count)*width
        points = []
        for j in range(9):
            t = j/8
            points.append((x, y+.015*math.sin(math.pi*t)+.0016*math.sin(t*math.pi*12+i*.7), z0+(z1-z0)*t))
        result.append(furniture._curve(name+f' · cuerda vertical {i:02d}', points, col, parent, mats['rope'], .0041))
    for i in range(5):
        z = z0+(z1-z0)*(i+.5)/5
        points = [(width*(-.5+j/32), y+.003*math.cos(j*math.pi*.75), z) for j in range(33)]
        result.append(furniture._curve(name+f' · enlace tejido {i}', points, col, parent, mats['rope'], .0032))
    return result


def _lounge(item, col, mats, target):
    name = item['nombre']
    _delete_asset(name)
    center = item['centro_xy_m']; size = item['tamano_bbox_xy_m']
    sofa = item['tipo'].startswith('sofa_3')
    if sofa:
        yaw = math.pi/2
        sx, sy = size[1], size[0]
    else:
        # Los símbolos fijan contorno; la orientación del respaldo es decorativa.
        # Las dos filas de butacas se orientan a la mesa sin cambiar su huella.
        yaw = 0 if center[1] > target[1] else math.pi
        sx, sy = size
    parent = furniture._parent(name, (*center, 0), col)
    parent['procedencia'] = NOTE
    parent['fuente_xy'] = 'Huella y centro datos_mobiliario.json; planta final'
    result = [parent]
    w, d = sx*.89, sy*.88
    for ix in (-1, 1):
        for iy in (-1, 1):
            result.append(_rod(name+' · pata tubular', (ix*w*.49, iy*d*.47, .005), (ix*w*.46, iy*d*.44, .36), .011, col, parent, mats['metal']))
    for iy in (-1, 1):
        result.append(_rod(name+' · travesaño asiento', (-w*.47, iy*d*.43, .34), (w*.47, iy*d*.43, .34), .013, col, parent, mats['metal']))
    for ix in (-1, 1):
        x = ix*w*.49
        result.append(_rod(name+' · montante respaldo', (x, d*.43, .29), (x, d*.49, .77), .013, col, parent, mats['metal']))
        result.append(_rod(name+' · apoyabrazo abierto', (x, -d*.40, .58), (x, d*.47, .60), .012, col, parent, mats['metal']))
        result.append(_rod(name+' · apoyo brazo', (x, -d*.40, .35), (x, -d*.40, .58), .010, col, parent, mats['metal']))
    result.append(_rod(name+' · marco superior respaldo', (-w*.49, d*.49, .77), (w*.49, d*.49, .77), .013, col, parent, mats['metal']))
    result.extend(_weave_back(name, w*.95, d*.47, .39, .76, col, parent, mats))
    seats = 3 if sofa else 1
    padw = w*.91/seats
    for i in range(seats):
        x = (i-(seats-1)/2)*padw
        result.extend(furniture._upholstered(name+f' · cojín asiento {i+1}', (x, -d*.04, .412), (padw-.018, d*.95, .107), col, parent, mats['fabric'], fullness=.24, wrinkles=.0018))
        result.extend(furniture._upholstered(name+f' · cojín lumbar {i+1}', (x, d*.305, .621), (padw-.02, .108, .286), col, parent, mats['fabric'], rotation=(math.radians(-8), 0, math.radians((i%3-1)*1.3)), fullness=.37, wrinkles=.0023))
    if sofa:
        for sign in (-1, 1):
            result.extend(furniture._upholstered(name+f' · almohadón suelto {sign}', (sign*w*.33, -d*.08, .584), (.31, .13, .29), col, parent, mats['fabric'], rotation=(math.radians(-16), math.radians(sign*13), math.radians(sign*6)), fullness=.49, wrinkles=.0027))
    furniture._fit_xy(parent, result, (sx, sy))
    parent.rotation_euler.z = yaw
    parent['altura_asset_m'] = .785
    parent['envolvente_xy_m'] = list(size)
    parent['detalle_visual'] = 'Aluminio tubular, cuerda tejida geométrica, cojines finos con costuras; huella del plano.'
    return result


def _dining_chair(item, table, col, mats):
    name = item['nombre']; _delete_asset(name)
    b = item['bbox_xy_m']; center = list(item['centro_xy_m'])
    visible = item['tamano_bbox_xy_m']
    if '_izq_' in name:
        yaw = math.pi/2
        width = visible[1]; depth = .515
        center[0] = b[0]+depth/2
    elif '_der_' in name:
        yaw = -math.pi/2
        width = visible[1]; depth = .515
        center[0] = b[2]-depth/2
    elif '_norte' in name:
        yaw = 0
        width = visible[0]; depth = .515
        center[1] = b[3]-depth/2
    else:
        yaw = math.pi
        width = visible[0]; depth = .515
        center[1] = b[1]+depth/2
    parent = furniture._parent(name, (*center, 0), col)
    result = [parent]
    w, d = width*.91, depth*.93
    for ix in (-1, 1):
        for iy in (-1, 1):
            result.append(_rod(name+' · pata tubular', (ix*w*.45, iy*d*.45, 0), (ix*w*.43, iy*d*.39, .438), .009, col, parent, mats['metal']))
    for ix in (-1, 1):
        x = ix*w*.47
        result.append(_rod(name+' · respaldo estructural', (x, d*.39, .36), (x, d*.49, .825), .010, col, parent, mats['metal']))
    result.append(_rod(name+' · marco superior', (-w*.47, d*.49, .825), (w*.47, d*.49, .825), .010, col, parent, mats['metal']))
    result.extend(_weave_back(name, w*.89, d*.45, .47, .807, col, parent, mats))
    result.extend(furniture._upholstered(name+' · asiento técnico', (0, -d*.035, .465), (w*.98, d*.97, .073), col, parent, mats['fabric'], fullness=.28, wrinkles=.0015))
    furniture._fit_xy(parent, result, (width, depth))
    parent.rotation_euler.z = yaw
    parent['procedencia'] = NOTE
    parent['borde_visible_pdf_bbox_xy_m'] = b
    parent['fondo_completo_asset_m'] = depth
    parent['criterio_fondo'] = 'Glifo de silla sólo visible fuera del tablero. Se completa parte oculta bajo la mesa; borde exterior y eje transversal del PDF invariables.'
    parent['altura_asset_m'] = .835
    return result


def _table(item, col, mats):
    name = item['nombre']; _delete_asset(name)
    center = item['centro_xy_m']; size = item['tamano_bbox_xy_m']
    sx, sy = size
    height = .75 if item['tipo'].startswith('mesa_comedor') else .385
    parent = furniture._parent(name, (*center, 0), col)
    result = [parent]
    result.append(furniture._box(name+' · porcelánico macizo canto redondeado', (0, 0, height-.018), (sx, sy, .036), col, parent, mats['stone'], .006))
    for ix in (-1, 1):
        for iy in (-1, 1):
            a = (ix*sx*.39, iy*sy*.38, 0)
            z = (ix*sx*.35, iy*sy*.34, height-.036)
            result.append(_rod(name+' · pata de aluminio', a, z, .016 if height>.5 else .013, col, parent, mats['metal']))
    furniture._fit_xy(parent, result, size)
    parent['fuente_xy'] = 'Contorno y centro planta final; no se mueve la mesa.'
    parent['altura_asset_m'] = height
    return result


def _lounger(item, col, mats):
    """Tumbona del símbolo PDF final; el respaldo elevado sólo es decorativo."""
    name = item['nombre']; _delete_asset(name)
    b = item['bbox_xy_m']
    center = ((b[0]+b[2])/2, (b[1]+b[3])/2)
    sx, sy = b[2]-b[0], b[3]-b[1]
    parent = furniture._parent(name, (*center, -.15), col)
    parent['procedencia'] = NOTE
    parent['fuente_xy'] = 'Planta final, página1; relleno gris mobiliario seqno'+str(item['seqno_pdf_final'])
    parent['bbox_pdf_pt_final'] = item['bbox_pdf_pt']
    parent['bbox_xy_m_final'] = b
    parent['criterio_z'] = 'Asiento a0.30m y respaldo reclinado decorativos; no son cotas arquitectónicas.'
    result = [parent]
    d, w = sx*.97, sy*.91
    # Marco de aluminio tubular fino: eje longitudinal X, idéntico al símbolo.
    for side in (-1, 1):
        y = side*w/2
        result.append(_rod(name+' · bastidor longitudinal', (-d/2,y,.255), (d/2,y,.255), .013, col, parent, mats['metal']))
        for end in (-1, 1):
            x = end*d*.38
            result.append(_rod(name+' · apoyo inclinado', (x*1.04,y,.0), (x,y,.255), .012, col, parent, mats['metal']))
    for end in (-1, 1):
        x = end*d/2
        result.append(_rod(name+' · bastidor transversal', (x,-w/2,.255), (x,w/2,.255), .013, col, parent, mats['metal']))
    result.extend(furniture._upholstered(name+' · cojín de asiento', (d*.19,0,.302), (d*.61,w*.97,.06), col, parent, mats['fabric'], fullness=.22, wrinkles=.0012))
    tilt = math.radians(22)
    back_length = d*.405
    result.extend(furniture._upholstered(name+' · respaldo reclinable', (-d*.28,0,.434), (back_length,w*.97,.052), col, parent, mats['fabric'], rotation=(0,tilt,0), fullness=.23, wrinkles=.0016))
    for side in (-1, 1):
        y = side*w*.48
        result.append(_rod(name+' · soporte respaldo', (-d*.105,y,.285), (-d*.475,y,.572), .010, col, parent, mats['metal']))
        result.append(_rod(name+' · ajuste respaldo', (-d*.37,y,.26), (-d*.34,y,.46), .0075, col, parent, mats['metal']))
    # Cojín cervical pequeño, dentro de la misma huella en planta.
    result.extend(furniture._upholstered(name+' · cojín cervical', (-d*.422,0,.56), (.21,w*.82,.084), col, parent, mats['fabric'], rotation=(0,tilt,0), fullness=.40, wrinkles=.0019))
    furniture._fit_xy(parent, result, (sx,sy))
    parent['altura_asiento_asset_m'] = .30
    parent['altura_respaldo_asset_aprox_m'] = .64
    return result


def _leaf_materials():
    mats = []
    for i in range(5):
        factor = .87+i*.072
        front = (.044*factor, .119*factor, .027*factor)
        back = (.086*factor, .173*factor, .045*factor)
        mat = _mat(f'V3 botánica · Phoenix pinna {i+1}', front, .52)
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        shader = nodes.get('Principled BSDF')
        if not nodes.get('Haz y envés naturales'):
            geo = nodes.new('ShaderNodeNewGeometry')
            mix = nodes.new('ShaderNodeMixRGB'); mix.name = 'Haz y envés naturales'
            mix.inputs[1].default_value = (*front, 1)
            mix.inputs[2].default_value = (*back, 1)
            links.new(geo.outputs['Backfacing'], mix.inputs[0])
            links.new(mix.outputs['Color'], shader.inputs['Base Color'])
            shader.inputs['Coat Weight'].default_value = .045
            shader.inputs['Coat Roughness'].default_value = .34
            noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 65
            tex = nodes.new('ShaderNodeTexCoord'); links.new(tex.outputs['UV'], noise.inputs['Vector'])
            bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .17
            bump.inputs['Distance'].default_value = .000075
            links.new(noise.outputs['Fac'], bump.inputs['Height']); links.new(bump.outputs['Normal'], shader.inputs['Normal'])
            thin = nodes.new('ShaderNodeBsdfTranslucent'); links.new(mix.outputs['Color'], thin.inputs['Color'])
            blend = nodes.new('ShaderNodeMixShader'); blend.inputs[0].default_value = .10
            links.new(shader.outputs[0], blend.inputs[1]); links.new(thin.outputs[0], blend.inputs[2])
            links.new(blend.outputs[0], nodes.get('Material Output').inputs['Surface'])
        mats.append(mat)
    return mats


def _palm(name, xy, height, col):
    _delete_asset(name)
    rng = random.Random(int(hashlib.sha256((name+'V3').encode()).hexdigest()[:8], 16))
    root = vegetation._parent(name, xy, col)
    radius = vegetation._radius(name, height, .485)
    root['altura_asset_m'] = height
    root['radio_asset_m'] = radius
    root['especie_visual'] = 'Phoenix ornamental; corona pinnada natural sin lanzas planas sobredimensionadas'
    root['criterio_envolvente'] = 'Misma raíz, altura y radio V2; forma botánica decorativa.'
    result = [root]
    stem_height = height*.66
    trunk, trunk_faces = [], []
    centers = [(height*.003*math.sin(i/52*2.2), height*.004*(i/52)**2, stem_height*i/52) for i in range(53)]
    nominal_r = min(.30, height*.053)
    vegetation._tube(trunk, trunk_faces, centers, [nominal_r*(1.08-i/52*.15) for i in range(53)], 40, .026)
    result.append(vegetation._mesh(name+' · estípite natural V3', trunk, trunk_faces, col, root, [vegetation._bark('palmera')]))
    leafv, leaff, idx, uv = [], [], [], []
    rachv, rachf = [], []
    # Espaciado angular asimétrico y tres edades con distinto descenso.
    layers = [(18, (.355, .43), (.12, .19), (.075, .13)),
              (17, (.30, .40), (.02, .095), (.135, .19)),
              (12, (.15, .29), (-.13, -.04), (.16, .22))]
    for generation, (count, lengths, drops, rises) in enumerate(layers):
        for n in range(count):
            angle = n*math.pi*(3-math.sqrt(5))+generation*.48+rng.uniform(-.18, .18)
            radial = Vector((math.cos(angle), math.sin(angle), 0))
            side = Vector((-math.sin(angle), math.cos(angle), 0))
            length, drop, rise = [height*rng.uniform(*v) for v in (lengths, drops, rises)]
            drift = height*rng.uniform(-.029, .029)
            crown = Vector((centers[-1][0], centers[-1][1], stem_height+rng.uniform(-.025, .04)))
            def axis(t):
                p = crown+radial*(nominal_r*.3+length*t)+side*(drift*math.sin(math.pi*t))
                p.z += rise*math.sin(math.pi*t)-drop*t
                return p
            line = [axis(k/19) for k in range(20)]
            vegetation._tube(rachv, rachf, line, [height*.0038*(1-k/19*.955) for k in range(20)], 6)
            pairs = 46 if generation<2 else 34
            for pair in range(pairs):
                t = .10+pair/(pairs-1)*.85
                e = math.sin(math.pi*t)**.76
                lengthp = height*(.008+.108*e)*rng.uniform(.84, 1.12)
                for sign in (-1, 1):
                    start = axis(max(.085, min(.969, t+rng.uniform(-.008, .008))))
                    end = start+side*sign*lengthp+radial*lengthp*rng.uniform(.24, .46)
                    end.z -= lengthp*(.15+t*.45+rng.uniform(-.10, .10))
                    normal = Vector((radial.x*.28, radial.y*.28, 1))+side*rng.uniform(-.38, .38)
                    width = height*.0096*(.86-.29*t)*rng.uniform(.86, 1.12)
                    vegetation._leaf(leafv, leaff, idx, uv, start, end, width, rng.randrange(5), normal, -lengthp*.04, 4, .24)
            vegetation._leaf(leafv, leaff, idx, uv, axis(.94), axis(1.02), height*.006, rng.randrange(5), (0, 0, 1), -.01, 4, .24)
    leafmats = _leaf_materials()
    result.append(vegetation._mesh(name+' · raquis naturales V3', rachv, rachf, col, root, leafmats[:1]))
    result.append(vegetation._mesh(name+' · pinnas anchas con nervadura V3', leafv, leaff, col, root, leafmats, idx, uv))
    root['frondas'] = sum(layer[0] for layer in layers)
    vegetation._fit(result, height, radius)
    return result


def _vehicle_materials():
    """Pintura real con capa transparente; sin cambiar vértices de los coches."""
    changed = []
    for mat in list(bpy.data.materials):
        if not mat.use_nodes or not ('pintura' in mat.name.lower() and 'coche' in mat.name.lower()):
            continue
        shader = mat.node_tree.nodes.get('Principled BSDF')
        if not shader:
            continue
        shader.inputs['Coat Weight'].default_value = 1
        shader.inputs['Coat Roughness'].default_value = .075
        shader.inputs['Roughness'].default_value = .245
        shader.inputs['Metallic'].default_value = .68
        if not mat.node_tree.nodes.get('V3 escama metálica micrométrica'):
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            noise = nodes.new('ShaderNodeTexNoise'); noise.name = 'V3 escama metálica micrométrica'
            noise.inputs['Scale'].default_value = 6900
            noise.inputs['Detail'].default_value = 2
            bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .12
            bump.inputs['Distance'].default_value = .000012
            links.new(noise.outputs['Fac'], bump.inputs['Height'])
            links.new(bump.outputs['Normal'], shader.inputs['Normal'])
        changed.append(mat.name)
    # Dos acabados de visualización; el símbolo PDF no determina colores.
    second = bpy.data.objects.get('Vehiculo_02_posicion_plano')
    template = bpy.data.materials.get('Coche · pintura antracita')
    if second and template:
        silver = bpy.data.materials.get('V3 coche · pintura plata perlada')
        if not silver:
            silver = template.copy()
            silver.name = 'V3 coche · pintura plata perlada'
            shader = silver.node_tree.nodes.get('Principled BSDF')
            shader.inputs['Base Color'].default_value = (.43, .465, .50, 1)
            shader.inputs['Metallic'].default_value = .74
            silver.diffuse_color = (.43, .465, .50, 1)
            silver['procedencia'] = NOTE+' Color de vehículo no definido por el plano.'
        for ob in second.children_recursive:
            if ob.type != 'MESH':
                continue
            for slot in ob.material_slots:
                if slot.material == template:
                    slot.material = silver
        changed.append(silver.name)
    return changed


def _architecture_identity(scene):
    cats = {'parcela', 'muro_vivienda', 'tendedero', 'forjado', 'peto', 'marquesina', 'pavimento', 'jardin', 'piscina', 'suelo_vivienda', 'cielorraso', 'carpinteria', 'vidrio', 'cerramiento', 'puerta_peatonal', 'porton_vehiculos', 'rejilla'}
    rows = []
    for ob in sorted(scene.objects, key=lambda v: v.name):
        if ob.type == 'MESH' and ob.get('categoria') in cats:
            rows.append([ob.name, list(ob.matrix_world), [list(v.co) for v in ob.data.vertices], [list(p.vertices) for p in ob.data.polygons]])
    payload = json.dumps(rows, default=lambda v:list(v), separators=(',', ':')).encode()
    return hashlib.sha256(payload).hexdigest(), len(rows)


def _asset_bbox(name):
    root = bpy.data.objects[name]
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    points = []
    for obj in root.children_recursive:
        if obj.type not in {'MESH', 'CURVE'}:
            continue
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        points.extend(evaluated.matrix_world@v.co for v in mesh.vertices)
        evaluated.to_mesh_clear()
    return [min(v[i] for v in points) for i in range(3)]+[max(v[i] for v in points) for i in range(3)]


def _mesh_curves(names):
    """El GLB selecciona mallas; conservar también cuerdas y vivos de cojines."""
    curves = []
    for name in names:
        root = bpy.data.objects[name]
        curves.extend(ob for ob in root.children_recursive if ob.type=='CURVE')
    if not curves:
        return 0
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    for ob in curves:
        ob.select_set(True)
        ob['detalle_origen'] = 'Curva procedural de cuerda/costura convertida a malla para portabilidad GLB; generador reproducible en exteriores_v3.py.'
    bpy.context.view_layer.objects.active = curves[0]
    bpy.ops.object.convert(target='MESH')
    return len(curves)


def aplicar_exteriores(scene=None):
    """Actualiza decorado y devuelve informe; valida arquitectura intacta."""
    scene = scene or bpy.context.scene
    before, count = _architecture_identity(scene)
    data = json.loads((ROOT/'modelo/datos_mobiliario.json').read_text())
    col = bpy.data.collections.get('Mobiliario')
    jardin = bpy.data.collections.get('Jardin')
    mats = _materials()
    changed = []
    interpreted = []
    measures = []
    for item in data['objetos']:
        if 'terraza' not in item['nombre']:
            continue
        typ = item['tipo']
        if typ.startswith('sofa_3') or typ == 'butaca_exterior':
            target = (12.63015, 26.660475 if 'dormitorios' in item['nombre'] else 15.071725)
            _lounge(item, col, mats, target)
        elif typ == 'silla_comedor':
            _dining_chair(item, None, col, mats)
            interpreted.append({'nombre':item['nombre'], 'bbox_visible_xy_m':item['bbox_xy_m'], 'fondo_completo_m':.515})
        elif typ.startswith('mesa_comedor') or typ == 'mesa_baja_exterior':
            _table(item, col, mats)
        else:
            continue
        changed.append(item['nombre'])
        actual = _asset_bbox(item['nombre'])
        expected = item['bbox_xy_m']
        if typ == 'silla_comedor':
            # Verificar borde exterior y ambos extremos del eje transversal.
            if '_izq_' in item['nombre']:
                errors = [abs(actual[0]-expected[0]), abs(actual[1]-expected[1]), abs(actual[4]-expected[3])]
            elif '_der_' in item['nombre']:
                errors = [abs(actual[3]-expected[2]), abs(actual[1]-expected[1]), abs(actual[4]-expected[3])]
            elif '_norte' in item['nombre']:
                errors = [abs(actual[4]-expected[3]), abs(actual[0]-expected[0]), abs(actual[3]-expected[2])]
            else:
                errors = [abs(actual[1]-expected[1]), abs(actual[0]-expected[0]), abs(actual[3]-expected[2])]
        else:
            errors = [abs(a-b) for a,b in zip([actual[0],actual[1],actual[3],actual[4]],expected)]
        if max(errors) > .00002:
            raise RuntimeError(f'Asset exterior desplazado: {item["nombre"]}, error {max(errors)} m.')
        measures.append({'nombre':item['nombre'], 'bbox_real_xyz_m':actual, 'bbox_pdf_xy_m':expected, 'error_contorno_o_borde_visible_max_m':max(errors)})
    # Estos dos símbolos existen en la planta final y faltaban en F42.
    # Se verificaron contra get_drawings() del PDFfinal, seqno1115/1117;
    # el SHA evita reutilizar sus coordenadas sobre otro documento.
    source_sha = hashlib.sha256((ROOT/'fuentes/planta_final_proyecto_obra.pdf').read_bytes()).hexdigest()
    if source_sha != '556b057350ec6b0a4050dfbf0cf104c35ca5ed48d0e8bf22b2b19c107f403995':
        raise RuntimeError('PDF final distinto: revisar posiciones de tumbonas antes de añadirlas.')
    for item in LOUNGER_SOURCE:
        _lounger(item, col, mats)
        changed.append(item['nombre'])
        actual = _asset_bbox(item['nombre'])
        expected = item['bbox_xy_m']
        error = max(abs(a-b) for a,b in zip([actual[0],actual[1],actual[3],actual[4]],expected))
        if error>.00002:
            raise RuntimeError(f'Tumbona desplazada: {item["nombre"]}, error {error} m.')
        measures.append({'nombre':item['nombre'],'bbox_real_xyz_m':actual,'bbox_pdf_xy_m':expected,'seqno_pdf_final':item['seqno_pdf_final'],'error_contorno_o_borde_visible_max_m':error})
    for name, xy, height in [('Palmera_frente', (17.15, 2.9), 4.9), ('Palmera_jardin_lateral', (15.22, 23.2), 4.25)]:
        _palm(name, xy, height, jardin)
    vehicle_mats = _vehicle_materials()
    curves_converted = _mesh_curves(changed)
    bpy.context.view_layer.update()
    after, count_after = _architecture_identity(scene)
    if before != after or count != count_after:
        raise RuntimeError('La revisión decorativa alteró una malla arquitectónica.')
    report = {
        'revision_visual':'V3', 'unidades':'m', 'modulo':'modelo/exteriores_v3.py',
        'objetos_mobiliario_recreados':changed,
        'sillas_parte_oculta_bajo_tablero':interpreted,
        'mediciones_mobiliario_real':measures,
        'criterio_sillas':'Borde exterior y eje transversal PDF invariantes. Glifo representa parte visible; fondo decorativo completo 0.515 m hacia debajo del tablero.',
        'materiales_coche_afinados':vehicle_mats,
        'curvas_de_cuerda_y_costura_convertidas_malla_para_glb':curves_converted,
        'tumbonas_fuente_planta_final':LOUNGER_SOURCE,
        'palmeras':[{'nombre':'Palmera_frente','raiz_xy_m':[17.15,2.9],'altura_asset_m':4.9},{'nombre':'Palmera_jardin_lateral','raiz_xy_m':[15.22,23.2],'altura_asset_m':4.25}],
        'assets_externos':[{'asset':'Fabric040','autor':'ambientCG / Lennart Demes','licencia':'CC0','carpeta':'assets/texturas/ambientcg/Fabric040','procedencia_y_sha256':'assets/licencias'}],
        'licencia_assets':'Geometría y shaders originales procedurales; mapas fotográficos de lino Fabric040 CC0 compartidos con materiales.py.',
        'arquitectura_objetos_comprobados':count,
        'arquitectura_sha256_antes':before, 'arquitectura_sha256_despues':after,
        'arquitectura_invariable':before==after,
        'piscina':'No se modifica su geometría ni se añade profundidad/fondo. Shader gestionado por materiales.py.'
    }
    (ROOT/'modelo/exteriores_v3.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    scene['exteriores_v3'] = 'Mobiliario outdoor con cuerda y aluminio, cojines con costura, palmeras pinnadas naturales; arquitectura invariable.'
    print('EXTERIORES_V3',len(changed),'muebles;',count,'mallas arquitectónicas sin cambios',flush=True)
    return report


if __name__ == '__main__':
    aplicar_exteriores()
