"""Huecos: mide dinteles/jambas Blender frente a fuente vectorial y Z previa."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=json.loads((ROOT/'control/mediciones_mesh_real.json').read_text())
A=json.loads((ROOT/'analisis_v2/auditoria_planta_final.json').read_text())
Z=json.loads((ROOT/'fuentes/datos_v1/datos_alturas.json').read_text())
U=json.loads((ROOT/'modelo/confirmaciones_usuario_v2.json').read_text())['confirmaciones_usuario']
O={o['nombre']:o for o in R['objetos']};old={o['nombre']:o for o in Z['huecos_exteriores']}
result=[]
source=[]
for h in A['huecos_exteriores_compartidos_v1']:
 z=old[h['nombre']]
 source.append({'nombre':h['nombre'],'bbox':h['bbox_xy_m_registro_parcela'],'alto':z['z_dintel_m']-z['z_antepecho_m'],'z0':z['z_antepecho_m'],'z1':z['z_dintel_m'],'ancho_nominal':z['ancho_documental_m'],'fuente_z':z['fuente_z']})
source += [{'nombre':'P_porton_trastero_sur','bbox':[4.826,7.8877,8.8265,8.1377],'alto':U['porton_frontal_trastero_alto_m'],'z0':0,'z1':U['porton_frontal_trastero_alto_m'],'ancho_nominal':None,'fuente_z':'Confirmación usuario'},
 {'nombre':'P_interior_trastero_norte','bbox':[7.3025,12.0777,8.2625,12.42695],'alto':U['puerta_interior_trastero_alto_m'],'z0':0,'z1':U['puerta_interior_trastero_alto_m'],'ancho_nominal':.96,'fuente_z':'Confirmación usuario'}]
for h in source:
 name=h['nombre'];d=O[name+'_dintel'];b=d['bbox_xyz'];actual=[b[0],b[1],b[3],b[4]]
 errs=[abs(a-c) for a,c in zip(actual,h['bbox'])]+[abs(b[2]-h['z1'])]
 if name!='P_interior_trastero_norte':
  jamb=O[name+'_jamba1']['bbox_xyz'];errs += [abs(jamb[2]-h['z0']),abs(jamb[5]-h['z1'])]
  height=jamb[5]-jamb[2]
 else:
  leaf=O[name+'_hoja']['bbox_xyz'];height=leaf[5]-leaf[2];errs += [abs(height-h['alto'])]
 width=max(b[3]-b[0],b[4]-b[1])
 result.append({'nombre':name,'ancho_nominal_m':h['ancho_nominal'],'ancho_real_m':width,'alto_real_m':height,'bbox_real_xyz_dintel':b,'fuente_z':h['fuente_z'],'error_max_m':max(errs),'valido':max(errs)<1e-5})
valid=all(v['valido'] for v in result)
(ROOT/'control/huecos_mesh_v2.json').write_text(json.dumps({'revision':'V2','valido':valid,'modelo_sha256':hashlib.sha256((ROOT/'Calle_Macarena_modelo_1a1.blend').read_bytes()).hexdigest(),'huecos':result},ensure_ascii=False,indent=2))
print('HUECOS_MESH_V2',len(result),'verificados; válido',valid,'error',max(v['error_max_m'] for v in result))
if not valid:sys.exit(1)
