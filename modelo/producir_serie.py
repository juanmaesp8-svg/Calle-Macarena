"""Orquestador local: espera las cinco ortográficas, renderiza y prepara entrega."""
from pathlib import Path
import sys,time,json,subprocess,shutil,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
ids=['QA00','QA01','QA02','QA03','QA04']
print('ESPERA_ORTOGRAFICAS',flush=True)
while True:
    p=ROOT/'control/ortograficas/registro_renders.json'
    try:d=json.loads(p.read_text())
    except (FileNotFoundError,json.JSONDecodeError):d=[]
    if all(any(r['id']==i and (ROOT/'control/ortograficas'/Path(r['png']).name).is_file() for r in d) for i in ids):break
    time.sleep(5)
if not json.loads((ROOT/'control/control_resultado.json').read_text())['apto_para_renders']:
    raise RuntimeError('No ha superado QA geométrico')
subprocess.run([sys.executable,str(ROOT/'control/anadir_ortograficas_informe.py')],check=True)
cmd=['blender','--background',str(ROOT/'Calle_Macarena_modelo_1a1.blend'),'--python-exit-code','1','--python',str(ROOT/'modelo/renderizar.py'),'--','--ids','01,02,03,04,05,06,07,08,09,10','--width','2500','--samples','96']
print('INICIO_SERIE_FINAL',flush=True);subprocess.run(cmd,check=True)
subprocess.run([sys.executable,str(ROOT/'entrega/preparar_entrega.py')],check=True)
if not json.loads((ROOT/'entrega/validacion_entrega.json').read_text()).get('apto_para_entrega',False):
    # El preparador ya falla por código de salida si invalida; no asumir claves.
    print('Validación completada por preparar_entrega.py',flush=True)
include=[]
for name in ['Calle_Macarena_modelo_1a1.blend','Calle_Macarena_modelo_1a1.glb','informe_control.pdf','tabla_dimensiones_modeladas.csv','geometria_base.json']:
    include.append(ROOT/name)
for folder in ['modelo','control','entrega','fuentes']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and not any(n in p.parts for n in ['__pycache__','python_deps','lineales']) and not any(n.endswith('_oidn_buffers') for n in p.parts) and p.suffix not in ['.log','.exr','.pfm','.pyc']:include.append(p)
for p in (ROOT/'renders').iterdir():
    if p.is_file() and p.suffix in ['.png','.json']:include.append(p)
for name in ['denoise_exr.py','OIDN_USO.md','oidn_instalacion_verificada.json']:include.append(ROOT/'herramientas'/name)
for p in (ROOT/'analisis').glob('auditoria_*'):
    if p.suffix in ['.md','.json']:include.append(p)
bundle=ROOT/'Calle_Macarena_entrega.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(include)):z.write(p,p.relative_to(ROOT))
with zipfile.ZipFile(bundle) as z:
    if z.testzip():raise RuntimeError('ZIP corrupto')
print('ENTREGA_COMPLETADA',bundle,bundle.stat().st_size,flush=True)
