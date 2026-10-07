"""Genera la galería de siete vistas y el informe de una única escena validada."""
import csv
import hashlib
import html
import json
from pathlib import Path
import fitz
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'entrega'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
titles={'I01':'Salón','I02':'Cocina','I03':'Comedor','E01':'Terraza · vista longitudinal','E02':'Piscina y vivienda','E03':'Aparcamiento descubierto','E04':'Terraza · comedor exterior'}
model_hash=sha(ROOT/'Calle_Macarena_modelo_1a1.blend')
qc=json.loads((ROOT/'control/control_resultado.json').read_text())
visual=json.loads((ROOT/'control/control_revision_visual_v3.json').read_text())
assert qc['apto_para_renders'] and qc['fallos']==0 and visual['valido']
assert qc['modelo_sha256']==visual['modelo_sha256']==model_hash
ortho_registry=json.loads((ROOT/'control/visual_v2/ortograficas/registro_v2.json').read_text())
assert ortho_registry['fuentes']['modelo_sha256']==model_hash,'Regenerar las láminas del modelo final'
for view in ortho_registry['vistas']:
    assert sha(ROOT/view['png'])==view['png_sha256'],'Imagen ortográfica distinta de su registro'
registry=json.loads((ROOT/'renders/registro_renders.json').read_text())
byid={v['id']:v for v in registry}
assert set(byid)==set(titles),'La galería requiere exclusivamente las siete vistas nuevas'
W,H=landscape(A4)
c=canvas.Canvas(str(E/'galeria_renders.pdf'),pagesize=(W,H))
c.setTitle('Calle Macarena · interiores y exteriores · V3')
gallery=[]
for ident,title in titles.items():
    item=byid[ident]
    assert item['modelo_sha256']==model_hash and max(item['resolucion'])>=2500
    png=ROOT/'renders'/(item['nombre']+'.png')
    jpg=png.with_suffix('.jpg')
    with Image.open(png) as image:
        assert list(image.size)==item['resolucion']
        rgb=image.convert('RGB')
        assert max(rgb.getextrema()[0])-min(rgb.getextrema()[0])>80
        rgb.save(jpg,quality=96,subsampling=0)
    c.setFont('Helvetica-Bold',17)
    c.drawString(28,H-32,'Calle Macarena · '+title)
    c.drawImage(str(jpg),28,55,width=W-56,height=H-108,preserveAspectRatio=True,anchor='c')
    c.setFont('Helvetica',9)
    c.drawString(28,28,f"Revisión V3 · modelo 1:1 · {item['resolucion'][0]} × {item['resolucion'][1]} px")
    c.showPage()
    gallery.append({'id':ident,'titulo':title,'png':str(png.relative_to(ROOT)),'jpg':str(jpg.relative_to(ROOT)),'sha256_png':sha(png),'sha256_jpg':sha(jpg),'resolucion':item['resolucion']})
c.save()

cover=E/'resumen_control_v3.pdf'
c=canvas.Canvas(str(cover),pagesize=A4)
w,h=A4
c.setTitle('Calle Macarena · control de la revisión visual V3')
c.setFont('Helvetica-Bold',18)
c.drawString(36,h-50,'Revisión visual V3 · control de geometría')
lines=[f"{qc['total_controles']} comprobaciones de planta y alturas; {qc['fallos']} fallos.",
       f"{visual['arquitectura_objetos_comparados']} objetos arquitectónicos comparados con V2.",
       f"Diferencia máxima de coordenada: {visual['maxima_diferencia_coordenada_m']:.9f} m.",
       'Las siete imágenes proceden del mismo archivo Blender.',
       '',
       'Planta: versión final PLANTA DIST. PROY.OBRA.pdf, página 1.',
       'Vivienda: alturas del proyecto básico, alzados y secciones.',
       'Trastero: forjado +3,35/+3,70 m y peto +4,40 m, confirmados.',
       'Puerta interior 2,03 m; portón 2,50 m, confirmados por el usuario.',
       'No se modifica la parcela, el jardín, la piscina ni los huecos.',
       '',
       'Acabado exterior: blanco, madera vertical clara y carpintería oscura.',
       'Porcelánico exterior crema claro, módulo 90 × 90 cm; césped artificial.',
       'Se detallan muebles, tejidos, cocina, vegetación y materiales.',
       'Los acabados interiores, accesorios y alturas de muebles son visuales;',
       'no constituyen una definición constructiva del proyecto.',
       'Las sillas recuperan la porción oculta bajo las mesas del plano.',
       'La piscina conserva su perímetro, sin inventar cotas de profundidad.',
       '',
       'Las páginas siguientes cotejan la geometría con los planos originales.',
       'Consultar las discrepancias de origen en control_resultado.json.',
       '',
       'SHA256 del modelo de todas las vistas:',model_hash]
y=h-85
for line in lines:
    c.setFont('Helvetica',8 if len(line)>80 else 10)
    c.drawString(36,y,line)
    y-=23
c.showPage();c.save()
report=fitz.open(cover)
with fitz.open(ROOT/'control/visual_v2/laminas/informe_visual_v2.pdf') as source:
    report.insert_pdf(source)
report.save(ROOT/'control/informe_revision_v3.pdf',garbage=4,deflate=True)
report.close()

hm=json.loads((ROOT/'control/huecos_mesh_v2.json').read_text())
assert hm['valido'] and hm['modelo_sha256']==model_hash
with (ROOT/'control/dimensiones_principales_v2.csv').open() as f:rows=list(csv.reader(f))
for opening in hm['huecos']:
    rows.extend([[opening['nombre']+' · ancho',opening['ancho_nominal_m'],opening['ancho_real_m'],'m','PDF final; medida real del mesh'],[opening['nombre']+' · alto','',opening['alto_real_m'],'m',opening['fuente_z']]])
with (ROOT/'tabla_dimensiones_modeladas.csv').open('w',newline='') as f:csv.writer(f).writerows(rows)
(ROOT/'geometria_base.json').write_text(json.dumps({'revision_geometrica':'V2_planta_final_trastero','revision_visual':'V3_interiores_exteriores','unidades':'m','modelo_sha256':model_hash,'planta_final_sha256':qc['fuente_sha256'],'datos_xy':'modelo/datos_planta.json','datos_z':'modelo/datos_alturas.json','confirmaciones_usuario':'modelo/confirmaciones_usuario_v2.json','mediciones_reales':'control/mediciones_mesh_real.json','control_geometrico':'control/control_resultado.json','control_identidad_visual':'control/control_revision_visual_v3.json'},ensure_ascii=False,indent=2))
(E/'galeria_v3.json').write_text(json.dumps({'revision':'V3','modelo_sha256':model_hash,'vistas':gallery},ensure_ascii=False,indent=2))
cards=''.join(f'<figure><h2>{html.escape(v["titulo"])}</h2><a href="../{v["png"]}"><img src="../{v["jpg"]}" alt="{html.escape(v["titulo"])}"></a><figcaption><a download href="../{v["png"]}">PNG completo</a> · <a download href="../{v["jpg"]}">JPG</a></figcaption></figure>' for v in gallery)
(E/'galeria.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Calle Macarena · V3</title><style>body{font:16px system-ui;max-width:1150px;margin:30px auto;padding:20px;background:#faf9f6;color:#252525}img{width:100%;display:block}figure{margin:45px 0}a{color:#345b64}</style><h1>Calle Macarena · interiores y exteriores</h1><p>Siete vistas de la misma vivienda, conforme al plano definitivo con trastero.</p><p><a href="galeria_renders.pdf">Galería PDF</a> · <a href="../Calle_Macarena_modelo_1a1.blend">Blender</a> · <a href="../Calle_Macarena_modelo_1a1.glb">GLB</a> · <a href="../control/informe_revision_v3.pdf">Control geométrico</a></p>'+cards+'</html>')
print('ENTREGA_V3_PREPARADA',len(gallery),'vistas,',qc['total_controles'],'controles, SHA',model_hash)
