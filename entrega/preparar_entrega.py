#!/usr/bin/env python3
"""Validate the final ten renders and produce offline presentation artifacts.

Run only after the 10 final renders are complete:
    python entrega/preparar_entrega.py

Never modifies any individual PNG, EXR, .blend or rendering registry.
No ZIP or binary dependencies are bundled by this script.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import math
import re
import sys
import io
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
EXPECTED = [f'{i:02d}' for i in range(1,11)]
VIEWS = {
 '01':'Vista aérea oblicua de la parcela',
 '02':'Vista desde el vial público',
 '03':'Vista desde el aparcamiento',
 '04':'Entrada principal',
 '05':'Piscina hacia vivienda',
 '06':'Terraza hacia piscina',
 '07':'Fachada de salón, cocina y terraza',
 '08':'Porche y comedor exterior',
 '09':'Esquina del jardín',
 '10':'Vista al atardecer',
}


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as fh:
        for block in iter(lambda:fh.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def validate(root, minimum=2500):
    renders=root/'renders'
    delivery=root/'entrega'
    delivery.mkdir(parents=True,exist_ok=True)
    report={'apto_para_entrega':False,'minimo_lado_largo_px':minimum,
            'ids_requeridos':EXPECTED,'errores':[],'imagenes':[],
            'regla':'La resolución y el hash común verifican la serie, no convierten cotas ausentes del PDF en medidas confirmadas.'}
    rows=[]
    errors=report['errores']
    registry_path=renders/'registro_renders.json'
    if not registry_path.is_file():
        errors.append('Falta renders/registro_renders.json.')
        registry=[]
    else:
        try:
            registry=json.loads(registry_path.read_text())
            if not isinstance(registry,list) or not all(isinstance(v,dict) for v in registry):
                errors.append('El registro debe ser una lista de objetos.')
                registry=[]
        except (OSError,ValueError) as exc:
            errors.append('No se puede leer el registro: '+str(exc))
            registry=[]
    ids=[str(v.get('id','')) for v in registry]
    if sorted(ids)!=EXPECTED:
        errors.append('El registro debe contener exactamente los IDs01..10, una sola vez; encontrados: '+', '.join(ids))
    registry_by_id={str(v.get('id','')):v for v in registry}
    common_hashes=[]
    for ident in EXPECTED:
        pngs=sorted(renders.glob(ident+'_*.png'))
        if len(pngs)!=1:
            errors.append(f'{ident}: se necesita exactamente un PNG final; encontrados {len(pngs)}.')
            continue
        path=pngs[0]
        rec=registry_by_id.get(ident,{})
        info={'id':ident,'vista':VIEWS[ident],'png':str(path.relative_to(root))}
        try:
            with Image.open(path) as im:
                width,height=im.size
                format_name=im.format
                im.verify()
            if format_name!='PNG':
                errors.append(f'{ident}: el archivo no es un PNG válido.')
            if max(width,height)<minimum:
                errors.append(f'{ident}: {width}×{height}px no alcanza {minimum}px en lado largo.')
            if list(rec.get('resolucion',[]))!=[width,height]:
                errors.append(f'{ident}: resolución del registro no coincide con el PNG real.')
            registered_png=rec.get('png')
            if not registered_png:
                errors.append(f'{ident}: falta ruta PNG en el registro.')
            else:
                rp=Path(registered_png)
                if rp.is_absolute():
                    # El registro conserva la ruta histórica del equipo de render.
                    # La entrega mantiene todos los originales en renders/.
                    rp=renders/rp.name
                else:
                    rp=root/rp
                if rp.resolve()!=path.resolve():
                    errors.append(f'{ident}: registro apunta a un PNG distinto.')
            model_hash=str(rec.get('modelo_sha256',''))
            if re.fullmatch(r'[0-9a-f]{64}',model_hash) is None:
                errors.append(f'{ident}: modelo_sha256 falta o no es SHA256 válido.')
            else:
                common_hashes.append(model_hash)
            focal=float(rec.get('focal_mm',0))
            if not math.isfinite(focal) or focal<=0:
                errors.append(f'{ident}: falta focal válida.')
            if rec.get('motor')!='Cycles CPU':
                errors.append(f'{ident}: motor registrado distinto de Cycles CPU.')
            info.update(resolucion_px=[width,height],sha256_png=sha256(path),
                        modelo_sha256=model_hash,focal_mm=focal,
                        motor=rec.get('motor'),denoise=rec.get('denoise'),
                        iluminacion=rec.get('iluminacion'))
            rows.append({'id':ident,'path':path,'vista':VIEWS[ident],
                         'width':width,'height':height,'focal':focal,'registry':rec})
        except (OSError,ValueError,TypeError) as exc:
            errors.append(f'{ident}: no se puede validar PNG/registro: {exc}')
        report['imagenes'].append(info)
    hash_set=sorted(set(common_hashes))
    report['hashes_blend_en_registro']=hash_set
    report['todos_renders_mismo_modelo']=len(common_hashes)==10 and len(hash_set)==1
    if not report['todos_renders_mismo_modelo']:
        errors.append('Las diez imágenes deben registrar el mismo SHA256 de Blender.')
    blend=root/'Calle_Macarena_modelo_1a1.blend'
    if blend.is_file():
        actual_hash=sha256(blend)
        report['sha256_blend_entregado']=actual_hash
        report['registro_coincide_blend_entregado']=hash_set==[actual_hash] and len(common_hashes)==10
        if not report['registro_coincide_blend_entregado']:
            errors.append('El SHA256 del .blend entregado no coincide con la serie completa.')
    else:
        report['registro_coincide_blend_entregado']=False
        errors.append('Falta Calle_Macarena_modelo_1a1.blend.')
    report['apto_para_entrega']=not errors and len(rows)==10
    (delivery/'validacion_entrega.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report,rows


def caption(row):
    return f"{row['id']} · {row['vista']} · {row['focal']:g} mm · {row['width']} × {row['height']} px"


def make_pdf(rows,delivery):
    path=delivery/'galeria_renders.pdf'
    w,h=landscape(A4)
    pdf=canvas.Canvas(str(path),pagesize=(w,h),pageCompression=1)
    pdf.setTitle('Calle Macarena nº16 · Galería de renders exteriores')
    pdf.setAuthor('Reconstrucción del proyecto básico')
    margin=12
    footer=30
    for row in rows:
        pdf.bookmarkPage(row['id'])
        pdf.addOutlineEntry(row['vista'],row['id'],0)
        avail_w=w-2*margin
        avail_h=h-margin-footer
        scale=min(avail_w/row['width'],avail_h/row['height'])
        iw=row['width']*scale
        ih=row['height']*scale
        x=(w-iw)/2
        y=footer+(avail_h-ih)/2
        # Copia JPEG de presentación dentro del PDF; el PNG16 original queda intacto.
        buffer=io.BytesIO()
        with Image.open(row['path']) as source:
            source.convert('RGB').save(buffer,format='JPEG',quality=97,subsampling=0,optimize=True)
        buffer.seek(0)
        pdf.drawImage(ImageReader(buffer),x,y,width=iw,height=ih,
                      preserveAspectRatio=True,mask='auto')
        pdf.setFillColorRGB(.23,.25,.27)
        text=caption(row)
        size=9.0
        while pdf.stringWidth(text,'Helvetica',size)>w-2*margin and size>6:
            size-=.25
        pdf.setFont('Helvetica',size)
        pdf.drawCentredString(w/2,12,text)
        pdf.showPage()
    pdf.save()
    return path


def make_contact(rows,delivery):
    # This is a separate derivative sheet. Original PNGs are read only.
    out=delivery/'hoja'/'contacto.jpg'
    out.parent.mkdir(exist_ok=True)
    tw,th=900,600
    gap,margin,label=24,32,42
    cols,number_rows=2,5
    width=cols*tw+(cols-1)*gap+2*margin
    height=number_rows*(th+label)+(number_rows-1)*gap+2*margin
    sheet=Image.new('RGB',(width,height),'#ffffff')
    draw=ImageDraw.Draw(sheet)
    try:
        font=ImageFont.truetype('DejaVuSans.ttf',22)
    except OSError:
        font=ImageFont.load_default()
    for i,row in enumerate(rows):
        x=margin+(i%cols)*(tw+gap)
        y=margin+(i//cols)*(th+label+gap)
        with Image.open(row['path']) as im:
            thumb=im.convert('RGB')
            thumb.thumbnail((tw,th),Image.Resampling.LANCZOS)
            sheet.paste(thumb,(x+(tw-thumb.width)//2,y+(th-thumb.height)//2))
        text=caption(row)
        if draw.textbbox((0,0),text,font=font)[2]>tw:
            text=f"{row['id']} · {row['vista']} · {row['focal']:g} mm"
        draw.text((x+6,y+th+10),text,font=font,fill='#30383c')
    sheet.save(out,quality=94,subsampling=0,optimize=True)
    return out


def make_html(rows,delivery):
    cards=[]
    for row in rows:
        relative=Path('..')/'renders'/row['path'].name
        url=quote(relative.as_posix())
        text=html.escape(caption(row))
        short=html.escape(row['vista'])
        cards.append(f'''<figure>
<a class="open-image" href="{url}" data-caption="{text}"><img src="{url}" alt="{short}" loading="lazy" width="{row['width']}" height="{row['height']}"></a>
<figcaption>{text}</figcaption></figure>''')
    page='''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Calle Macarena nº16 · Renders exteriores</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f3ef;color:#202c31;font-family:system-ui,-apple-system,sans-serif}header{padding:36px max(24px,4vw) 20px}h1{margin:0 0 8px;font-size:clamp(24px,4vw,38px);font-weight:500}header p{margin:0;color:#59646a;line-height:1.5}nav{display:flex;gap:18px;flex-wrap:wrap;margin-top:18px}a{color:inherit;text-underline-offset:4px}.gallery{padding:18px max(24px,4vw) 38px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}figure{margin:0;background:white;border-radius:3px;overflow:hidden}figure img{display:block;width:100%;height:auto;aspect-ratio:3/2;object-fit:contain;cursor:zoom-in;background:#eef0ef}figcaption{padding:13px 16px;font-size:13px;line-height:1.5}dialog{width:96vw;max-width:none;height:94vh;max-height:none;border:0;padding:0;background:#11171b;color:white;border-radius:5px}dialog::backdrop{background:#000b}.tools{height:64px;display:flex;align-items:center;gap:10px;padding:12px 18px;background:#172127}.tools button,.tools a{background:#2a373f;color:white;padding:8px 13px;border:0;border-radius:3px;text-decoration:none;font:inherit;cursor:pointer}.tools button:focus-visible,.tools a:focus-visible{outline:2px solid white}.tools .close{margin-left:auto}.stage{position:relative;height:calc(100% - 108px);overflow:hidden;display:flex;align-items:center;justify-content:center;cursor:grab}.stage img{max-width:100%;max-height:100%;width:auto;height:auto;transform-origin:center;user-select:none;touch-action:none}.stage:active{cursor:grabbing}#image-caption{height:44px;margin:0;padding:12px 18px;color:#d6dce0;font-size:13px;line-height:20px}footer{padding:0 max(24px,4vw) 32px;color:#69757a;font-size:13px}@media(max-width:700px){.gallery{grid-template-columns:1fr;padding:12px 16px;gap:18px}header{padding:24px 16px}.tools{gap:6px;padding:10px;font-size:13px}.tools button,.tools a{padding:8px}.tools .original{display:none}#image-caption{font-size:11px;padding:12px 10px}}
</style></head><body>
<header><h1>Calle Macarena nº16</h1><p>Diez vistas exteriores del mismo modelo 3D.</p>
<nav><a href="galeria_renders.pdf">Galería PDF</a><a href="hoja/contacto.jpg">Hoja de contacto</a><a href="../Calle_Macarena_modelo_1a1.blend">Modelo Blender</a><a href="../Calle_Macarena_modelo_1a1.glb">Modelo GLB</a><a href="../informe_control.pdf">Control geométrico</a></nav></header>
<main class="gallery">CARDS</main>
<footer>Reconstrucción desde el proyecto básico disponible. El informe de control identifica las medidas obtenidas, discrepancias y datos no definidos, incluida la profundidad de piscina.</footer>
<dialog id="viewer" aria-label="Vista ampliada"><div class="tools"><button id="prev" title="Vista anterior" aria-label="Vista anterior">←</button><button id="next" title="Vista siguiente" aria-label="Vista siguiente">→</button><button id="minus" aria-label="Alejar">−</button><button id="plus" aria-label="Acercar">+</button><button id="fit">Ajustar</button><a class="original" id="original" target="_blank" rel="noopener">Abrir original</a><button class="close" id="close">Cerrar</button></div><div class="stage" id="stage"><img id="large-image" alt=""></div><p id="image-caption"></p></dialog>
<script>
const links=[...document.querySelectorAll('.open-image')], viewer=document.querySelector('#viewer'), photo=document.querySelector('#large-image'), stage=document.querySelector('#stage');
let current=0,zoom=1,panX=0,panY=0,drag=null;
function transform(){photo.style.transform=`translate(${panX}px,${panY}px) scale(${zoom})`;}
function reset(){zoom=1;panX=0;panY=0;transform();}
function show(index){current=(index+links.length)%links.length;const item=links[current];photo.src=item.getAttribute('href');photo.alt=item.dataset.caption;document.querySelector('#image-caption').textContent=item.dataset.caption;document.querySelector('#original').href=item.href;reset();if(!viewer.open)viewer.showModal();}
function changeZoom(factor){zoom=Math.max(1,Math.min(5,zoom*factor));if(zoom===1){panX=0;panY=0;}transform();}
links.forEach((a,i)=>a.addEventListener('click',e=>{if(!viewer.showModal)return;e.preventDefault();show(i);}));
document.querySelector('#close').onclick=()=>viewer.close();document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);document.querySelector('#plus').onclick=()=>changeZoom(1.3);document.querySelector('#minus').onclick=()=>changeZoom(1/1.3);document.querySelector('#fit').onclick=reset;
stage.addEventListener('wheel',e=>{e.preventDefault();changeZoom(e.deltaY<0?1.1:1/1.1);},{passive:false});
stage.addEventListener('pointerdown',e=>{if(zoom===1)return;drag={x:e.clientX,y:e.clientY,px:panX,py:panY};stage.setPointerCapture(e.pointerId);});stage.addEventListener('pointermove',e=>{if(!drag)return;panX=drag.px+e.clientX-drag.x;panY=drag.py+e.clientY-drag.y;transform();});stage.addEventListener('pointerup',()=>drag=null);stage.addEventListener('pointercancel',()=>drag=null);photo.addEventListener('dragstart',e=>e.preventDefault());
viewer.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')show(current-1);if(e.key==='ArrowRight')show(current+1);if(e.key==='+')changeZoom(1.3);if(e.key==='-')changeZoom(1/1.3);if(e.key==='0')reset();});
</script></body></html>'''.replace('CARDS','\n'.join(cards))
    path=delivery/'galeria.html'
    path.write_text(page,encoding='utf-8')
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT_DEFAULT)
    parser.add_argument('--minimum',type=int,default=2500)
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    if args.minimum<2500:
        parser.error('El mínimo de entrega no puede ser inferior a 2500px en el lado largo.')
    root=args.root.resolve()
    report,rows=validate(root,args.minimum)
    if not report['apto_para_entrega']:
        for error in report['errores']:
            print('ERROR:',error,file=sys.stderr)
        print('Validación fallida; no se generan galerías.',file=sys.stderr)
        return 1
    if not args.check_only:
        delivery=root/'entrega'
        outputs=[make_pdf(rows,delivery),make_contact(rows,delivery),make_html(rows,delivery)]
        report['archivos_presentacion']=[{'ruta':str(p.relative_to(root)),
                                         'sha256':sha256(p),'bytes':p.stat().st_size} for p in outputs]
        report['paginas_galeria_pdf']=len(rows)
        report['miniaturas_contacto']=len(rows)
        (delivery/'validacion_entrega.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        for path in outputs:
            print(path)
    print('VALIDADO:10 PNG finales, resolución mínima cumplida, mismo .blend verificado.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
