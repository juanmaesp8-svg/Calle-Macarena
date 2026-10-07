"""Prepara una copia pública completa de V3 en un worktree aislado, sin publicar."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--destino',required=True,type=Path)
target=parser.parse_args().destino.resolve()
assert target!=ROOT.resolve() and target.is_dir() and (target/'.git').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
qa=json.loads((ROOT/'control/control_resultado.json').read_text())
visual=json.loads((ROOT/'control/control_revision_visual_v3.json').read_text())
gallery=json.loads((ROOT/'entrega/galeria_v3.json').read_text())
assert qa['apto_para_renders'] and visual['valido']
assert gallery['modelo_sha256']==qa['modelo_sha256']==visual['modelo_sha256']==sha(ROOT/'Calle_Macarena_modelo_1a1.blend')
assert len(gallery['vistas'])==7
files=[ROOT/x for x in ['Calle_Macarena_modelo_1a1.blend','Calle_Macarena_modelo_1a1.glb','geometria_base.json','tabla_dimensiones_modeladas.csv']]
excluded_names={'extraer_planta_pdf.py','preparar_datos_alturas.py','anadir_ortograficas_informe.py','setup_entorno.sh','pagina_1.png','pagina_1.txt','preparar_entrega_v2.py','copiar_revision_v2.py','galeria_renders_v1.pdf','resumen_control_v2.pdf','informe_revision_v2.pdf','LEEME_V2.md','producir_serie.py','guardar_iluminacion_v2.py','completar_mediciones_tendedero.py','BMW_Mike_Pan_origen.blend','CarConcept.glb','CarConcept.glb.metadata.json','CarConcept_README_origen.md','CarConcept_vista_origen.jpg','Ferrari_458_Italia.glb','Ferrari_458_Italia.glb.metadata.json','CC-BY-4.0_legal.txt','BMW_M6_README_origen.md'}
for group in ['fuentes','assets','analisis_v2','modelo','control','entrega']:
    for p in (ROOT/group).rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if any(v in {'__pycache__','python_deps','hoja','borradores'} for v in rel.parts):continue
        if p.suffix in {'.log','.pyc','.pfm','.blend1'}:continue
        if p.name in excluded_names or 'registro_v2_' in p.name:continue
        if p.name in {'bmw_m6_extended.gltf','bmw_m6.bin','BMW_M6_vista_origen.png','BMW_M6_PBRT_origen.png','BMW_inspeccion_fuente.json'}:continue
        files.append(p)
files.extend(p for p in (ROOT/'herramientas').glob('*') if p.is_file() and p.suffix in {'.py','.md','.json'})
files.extend(p for p in (ROOT/'renders').glob('*') if p.is_file() and p.suffix in {'.png','.jpg','.json'})
manifest=[]
for p in sorted(set(files)):
    rel=p.relative_to(ROOT)
    assert p.stat().st_size<100_000_000,f'Archivo demasiado grande para GitHub: {rel}'
    destination=target/rel
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,destination)
    manifest.append({'archivo':str(rel),'bytes':p.stat().st_size,'sha256':sha(p)})
readme=(ROOT/'entrega/LEEME_V3.md').read_text()
readme=readme.replace('(galeria_renders.pdf)','(entrega/galeria_renders.pdf)').replace('(galeria.html)','(entrega/galeria.html)').replace('(../','(')
(target/'README.md').write_text(readme)
(target/'MANIFIESTO_ENTREGA_V3.json').write_text(json.dumps({'revision':'V3_interiores_exteriores','modelo_sha256':qa['modelo_sha256'],'controles_geometricos':qa['total_controles'],'arquitectura_objetos_sin_cambios':visual['arquitectura_objetos_comparados'],'vistas':gallery['vistas'],'archivos':manifest},ensure_ascii=False,indent=2))
print('COPIA_V3',len(manifest),'archivos;',sum(v['bytes'] for v in manifest),'bytes')
