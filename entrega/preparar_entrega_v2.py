"""Prepara la entrega V2 revisable, sin publicar ni mezclar la galería V1."""
import json,hashlib,csv,shutil,sys
from pathlib import Path
import fitz
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'entrega';E.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
qc=json.loads((ROOT/'control/control_resultado.json').read_text())
assert qc['version']==2 and qc['apto_para_renders'] and qc['fallos']==0
model=ROOT/'Calle_Macarena_modelo_1a1.blend';assert qc['modelo_sha256']==sha(model)
registry=json.loads((ROOT/'renders/registro_renders.json').read_text())
photo=next(v for v in registry if v['id']=='05')
assert photo['modelo_sha256']==sha(model) and max(photo['resolucion'])>=2500
png=ROOT/'renders/05_Piscina_hacia_vivienda.png'
with Image.open(png) as im:
 assert im.size==(2500,1667)
 rgb=im.convert('RGB');rgb.save(ROOT/'renders/05_Piscina_hacia_vivienda.jpg',quality=96,subsampling=0)
 # Histograma sólo detecta errores de archivo/vacío, no acredita estética.
 assert max(rgb.getextrema()[0])-min(rgb.getextrema()[0])>80
W,H=landscape(A4)
one=E/'galeria_renders.pdf';c=canvas.Canvas(str(one),pagesize=(W,H))
c.setTitle('Calle Macarena — V2 — primera vista exterior')
c.setFont('Helvetica-Bold',17);c.drawString(28,H-32,'Calle Macarena · V2 · planta final con trastero')
c.drawImage(str(ROOT/'renders/05_Piscina_hacia_vivienda.jpg'),28,55,width=W-56,height=H-108,preserveAspectRatio=True,anchor='c')
c.setFont('Helvetica',9);c.drawString(28,28,'Cycles · 2500 × 1667 px · mismo modelo 1:1 · césped artificial · porcelánico crema 90 × 90 cm')
c.showPage();c.save()
# Portada del control identifica el dictamen numérico y las fuentes Z.
cover=E/'resumen_control_v2.pdf';c=canvas.Canvas(str(cover),pagesize=A4)
w,h=A4;c.setTitle('Control geométrico Calle Macarena V2')
c.setFont('Helvetica-Bold',19);c.drawString(36,h-50,'Control geométrico · revisión V2')
c.setFont('Helvetica',11)
lines=[f"{qc['total_controles']} comprobaciones superadas; {qc['fallos']} fallos.",
 'Planta final: PLANTA DIST. PROY.OBRA.pdf, página 1.',
 'Alturas de vivienda: alzados y secciones del proyecto básico.',
 'Alturas del trastero y puertas: confirmación expresa del usuario.',
 'Escala: 1:1, metros. No se fuerzan las áreas rotuladas.',
 'Comparación vectorial: cuantización máxima local 6,35 mm.',
 'Cotas nominales nuevas: precisión numérica de verificación 0,01 mm.',
 'El informe detalla diferencias entre trazado, cotas y superficies.',
 '',
 'Trastero interior: 7,15 × 3,94 m; profundidad exterior 4,19 m.',
 'Piscina: 3,50 × 5,00 m; no se inventa profundidad ni vaso.',
 'Forjado trastero: +3,35 / +3,70 m. Peto: +4,40 m.',
 'Puerta interior: 2,03 m de alto. Portón: 2,50 m de alto.',
 'Se mantienen las alturas diferenciadas del cuerpo existente.',
 '',
 'Geometría real medida desde los vértices de Blender.',
 'GLB importado independientemente: dimensiones conservadas.',
 'Mobiliario, vegetación y luminarias son visualización decorativa.',
 'Consultar las discrepancias documentales en control_resultado.json.',
 '',
 'SHA256 modelo editable:',sha(model)]
y=h-85
for line in lines:
 c.setFont('Helvetica',8 if len(line)>80 else 11);c.drawString(36,y,line);y-=23
c.showPage();c.save()
report=fitz.open(cover)
visual=ROOT/'control/visual_v2/laminas/informe_visual_v2.pdf'
with fitz.open(visual) as source:report.insert_pdf(source)
report.save(ROOT/'control/informe_revision_v2.pdf',garbage=4,deflate=True)
report.close()
hm=json.loads((ROOT/'control/huecos_mesh_v2.json').read_text())
assert hm['valido'] and hm['modelo_sha256']==sha(model)
with (ROOT/'control/dimensiones_principales_v2.csv').open() as f:dimrows=list(csv.reader(f))
for h in hm['huecos']:
 dimrows += [[h['nombre']+' · ancho',h['ancho_nominal_m'],h['ancho_real_m'],'m','Hueco vectorial PDFfinal; medida real de dintel'],[h['nombre']+' · alto','',h['alto_real_m'],'m',h['fuente_z']]]
with (ROOT/'tabla_dimensiones_modeladas.csv').open('w',newline='') as f:csv.writer(f).writerows(dimrows)
geometry={'revision':'V2','unidades':'m','planta_final_sha256':qc['fuente_sha256'],'datos_xy':'modelo/datos_planta.json','datos_z':'modelo/datos_alturas.json','confirmaciones_usuario':'modelo/confirmaciones_usuario_v2.json','mediciones_reales':'control/mediciones_mesh_real.json','control':'control/control_resultado.json','estado':'Verificado dentro de precisión y discrepancias documentadas'}
(ROOT/'geometria_base.json').write_text(json.dumps(geometry,ensure_ascii=False,indent=2))
html='''<!doctype html><html lang="es"><meta charset="utf-8"><title>Calle Macarena V2</title><style>body{font:16px system-ui;max-width:1100px;margin:35px auto;padding:20px;background:#faf9f6;color:#222}img{width:100%}a{color:#395d67}</style><h1>Calle Macarena · V2</h1><p>Planta final con trastero. Modelo a escala 1:1; Cycles, 2500 × 1667 píxeles.</p><img src="../renders/05_Piscina_hacia_vivienda.jpg" alt="Vista desde piscina hacia la vivienda revisada"><p><a href="../Calle_Macarena_modelo_1a1.blend">Modelo Blender</a> · <a href="../Calle_Macarena_modelo_1a1.glb">Modelo GLB</a> · <a href="../control/informe_revision_v2.pdf">Control de planta y alturas</a> · <a href="../tabla_dimensiones_modeladas.csv">Dimensiones</a></p></html>'''
(E/'galeria.html').write_text(html)
print('ENTREGA_V2_PREPARADA',qc['total_controles'],'controles; primera imagen',photo['resolucion'])
