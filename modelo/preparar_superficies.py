"""Operaciones 2D previas al mesh; conserva polígonos y huecos de la fuente."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python_deps'))
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union, triangulate
from shapely import constrained_delaunay_triangles

P=json.loads((ROOT/'datos_planta.json').read_text())
H=json.loads((ROOT/'datos_alturas.json').read_text())
def poly(v): return Polygon(v)
parcela=poly(P['parcela']['points_xy_m'])
casa=poly(P['huella_vivienda']['points_xy_m'])
piscina=poly(P['piscina']['poligono_xy_m'])
grasspolys=[poly(g['poligono_xy_m']) for g in P['cesped_patches']]
for g in P.get('cesped_bajo_mobiliario_deducido',[]):
    if isinstance(g,dict): grasspolys.append(poly(g['poligono_xy_m']))
    else: grasspolys.append(poly(g))
cesped=unary_union(grasspolys).intersection(parcela).difference(casa.union(piscina))
# Las máscaras del jardín y las líneas de solería determinan el suelo exterior.
pavimento=parcela.difference(unary_union([cesped,casa,piscina]))
panos=[]
for pa in H['cubierta']['panos']:
    v=pa.get('contorno_visible',pa.get('exterior'))
    panos.append(poly(v['vertices_xy_m']))
cubierta=unary_union(panos+[casa])
# Cara exterior de vallas en el lindero; espesor deducido del muro del tendedero.
# El contorno PARCELA no contiene el eje de una valla. La deducción se declara.
width=.1524
outer=P['parcela']['points_xy_m'];inner=list(parcela.buffer(-width,join_style=2).exterior.coords)[:-1]
q=[min(inner,key=lambda p:(p[0]-v[0])**2+(p[1]-v[1])**2) for v in outer]
tendedero=unary_union([poly(v) for wall in P['tendedero'] for v in wall['poligonos_xy_m']])
fences=[]
for i in range(len(outer)):
    if i==8:continue # Frente modelado desde accesos y esquema, no cerrar portones.
    geometry=Polygon([outer[i],outer[(i+1)%len(outer)],q[(i+1)%len(outer)],q[i]]).intersection(parcela).difference(tendedero).buffer(0)
    assert geometry.difference(parcela).area<1e-9
    fences.append((i,geometry))

def serialize(geometry):
    if geometry.is_empty:return []
    polygons=list(geometry.geoms) if isinstance(geometry,MultiPolygon) else [geometry]
    result=[]
    for pg in polygons:
        if not isinstance(pg,Polygon):continue
        pg=orient(pg,sign=1.0)
        assert pg.is_valid,'Contorno inválido; no se corrige silenciosamente'
        vertices=[]; faces=[]; indices={}
        def vertex(xy):
            key=tuple(round(v,8) for v in xy)
            if key not in indices:indices[key]=len(vertices);vertices.append(list(key))
            return indices[key]
        rings=[list(pg.exterior.coords)[:-1]]+[list(i.coords)[:-1] for i in pg.interiors]
        rings_idx=[[vertex(xy) for xy in ring] for ring in rings]
        total=0
        for tr in constrained_delaunay_triangles(pg).geoms:
            if pg.covers(tr.representative_point()):
                # Delaunay puede cubrir un borde no convexo; el área fuera debe ser nula.
                if tr.difference(pg).area>1e-9:continue
                xy=list(orient(tr,sign=1).exterior.coords)[:-1]
                faces.append([vertex(p) for p in xy]);total+=tr.area
        assert abs(total-pg.area)<1e-6,(total,pg.area)
        result.append({'vertices_xy':vertices,'caras':faces,'anillos':rings_idx,'area_m2':pg.area})
    return result

data={
    'parcela':serialize(parcela),
    'suelo_vivienda':serialize(casa),
    'cesped':serialize(cesped),
    'pavimentos':serialize(pavimento),
    'cubierta':serialize(cubierta),
    'piscina':serialize(piscina),
    'cerramiento_linderos':[{'indice_lindero':i,'partes':serialize(g)} for i,g in fences],
    'criterio_cerramiento':'Exterior sobre lindero; espesor0,1524m hacia dentro deducido del único detalle en tendedero. Espesor en restantes tramos no es cota directa. Restar muros de tendedero para evitar caras duplicadas.',
    'areas':{'parcela':parcela.area,'vivienda':casa.area,'cesped':cesped.area,'pavimentos':pavimento.area,'piscina':piscina.area},
    'criterio':'Polígonos del PDF; continuidad bajo las dos tumbonas es inferencia gráfica registrada. Ningún ajuste para imponer superficies de tabla.',
}
(ROOT/'superficies_mesh.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('Superficies trianguladas con huecos:',data['areas'])
