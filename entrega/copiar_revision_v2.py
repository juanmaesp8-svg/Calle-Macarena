"""Copia una entrega validada a una carpeta de publicación; no hace git push."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--destino',required=True,type=Path);args=parser.parse_args()
target=args.destino.resolve()
assert target!=ROOT.resolve() and target.is_dir() and (target/'.git').exists(),'Usar un worktree aislado ya creado'
qa=json.loads((ROOT/'control/control_resultado.json').read_text())
assert qa['version']==2 and qa['apto_para_renders']
assert (ROOT/'entrega/galeria_renders.pdf').is_file(),'Preparar entrega antes de copiar'
files=[]
rootfiles=['Calle_Macarena_modelo_1a1.blend','Calle_Macarena_modelo_1a1.glb','geometria_base.json','tabla_dimensiones_modeladas.csv']
files += [ROOT/x for x in rootfiles]
groups=['fuentes','assets','analisis_v2','modelo','control','entrega']
for group in groups:
 for p in (ROOT/group).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(ROOT)
  if any(v in {'__pycache__','python_deps','hoja'} for v in rel.parts):continue
  if p.suffix in {'.log','.pyc','.pfm','.blend1'}:continue
  if group=='modelo' and p.name in {'extraer_planta_pdf.py','preparar_datos_alturas.py'}:continue
  if group=='control' and p.name in {'anadir_ortograficas_informe.py'}:continue
  if group=='entrega' and p.name in {'setup_entorno.sh'}:continue
  if group=='analisis_v2' and p.name in {'pagina_1.png','pagina_1.txt'}:continue
  if 'registro_v2_' in p.name:continue
  files.append(p)
files += [p for p in (ROOT/'herramientas').glob('*') if p.is_file() and p.suffix in {'.py','.md','.json'}]
files += [p for p in (ROOT/'renders').glob('*') if p.is_file() and p.suffix in {'.png','.jpg','.exr','.json'}]
manifest=[]
for p in sorted(set(files)):
 rel=p.relative_to(ROOT)
 assert p.stat().st_size<100_000_000,f'Archivo supera límite de blob GitHub: {rel}'
 dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 manifest.append({'archivo':str(rel),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
readme='''# Calle Macarena · revisión V2\n\nModelo 1:1 conforme a la planta final con trastero, alturas confirmadas, césped artificial, solería crema de 90 × 90 cm y madera vertical entre cristaleras.\n\n- [Primera vista exterior PDF](entrega/galeria_renders.pdf)\n- [Imagen PNG 2500px](renders/05_Piscina_hacia_vivienda.png)\n- [Blender editable](Calle_Macarena_modelo_1a1.blend)\n- [GLB](Calle_Macarena_modelo_1a1.glb)\n- [Cotejo de planta, fachadas y alturas](control/informe_revision_v2.pdf)\n- [Dimensiones y fuentes](tabla_dimensiones_modeladas.csv)\n- [Cómo abrir y reconstruir](entrega/LEEME_V2.md)\n\nDescargar todo: [ZIP de esta revisión](https://github.com/juanmaesp8-svg/Calle-Macarena/archive/refs/heads/codex/modelo-v2-trastero.zip). Extraer el ZIP y abrir el `.blend` con Blender 4.3.2 o compatible; importar el `.glb` con File→Import→glTF.\n\n189 comprobaciones geométricas superadas. Los datos sin cota y discrepancias quedan documentados. El `.blend` incluye shaders y microfibras; el GLB facilita inspeccionar geometría y conserva materiales simplificados. Los fondos de calles son contexto gráfico; no se han añadido dimensiones de parcelas vecinas.\n\nEsta revisión contiene una primera vista Cycles nueva. Las diez imágenes anteriores corresponden a V1 y se conservan en la rama `codex/descarga-galeria-renders`. Los EXR limpios se incluyen; buffers de cálculo, dependencias instaladas y binarios OIDN se regeneran según el manual.\n'''
(target/'README.md').write_text(readme)
(target/'MANIFIESTO_ENTREGA_V2.json').write_text(json.dumps({'revision':'V2','modelo_sha256':qa['modelo_sha256'],'controles_geometricos':qa['total_controles'],'archivos':manifest},ensure_ascii=False,indent=2))
print('COPIA_V2',len(manifest),'archivos;',sum(v['bytes'] for v in manifest),'bytes')
