"""Anexa cámaras ortográficas reales de Cycles al control geométrico."""
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'informe_control.pdf';doc=fitz.open(path)
# Repetible: conservar sólo las páginas geométricas originales si había anexo.
for i in range(len(doc)-1,-1,-1):
    if 'ORTOGRAFICAS CYCLES' in doc[i].get_text():doc.delete_page(i)
qa=ROOT/'control/ortograficas'
page=doc.new_page(width=595,height=842)
page.insert_text((45,40),'ORTOGRAFICAS CYCLES - Vista superior',fontsize=15)
page.insert_textbox(fitz.Rect(45,52,550,95),'Cubierta plana y parcela completa. El corte de muros y su superposicion exacta con PDF35 se muestran en las paginas de control precedentes.',fontsize=9)
page.insert_image(fitz.Rect(75,102,520,805),filename=str(qa/'QA00_Planta_superior.png'),keep_proportion=True)
for group in [('QA01_Alzado_puerta_principal.png','QA02_Alzado_lateral_porche.png'),('QA03_Alzado_vial_publico.png','QA04_Alzado_trasero.png')]:
    page=doc.new_page(width=842,height=595)
    page.insert_text((40,34),'ORTOGRAFICAS CYCLES - Alzados del mismo modelo',fontsize=15)
    page.insert_textbox(fitz.Rect(40,45,805,79),'Entorno excluido para cotejar fachadas. No se cambian los volumenes ni huecos. La discrepancia de anchura del cuerpo alto en trasero/seccion3 permanece documentada.',fontsize=9)
    for i,name in enumerate(group):
        y=90+i*247;page.insert_text((40,y+10),name.removesuffix('.png').replace('_',' '),fontsize=10)
        page.insert_image(fitz.Rect(40,y+22,805,y+242),filename=str(qa/name),keep_proportion=True)
tmp=path.with_name('informe_control_nuevo.pdf');doc.save(tmp,garbage=4,deflate=True);doc.close();tmp.replace(path)
print('INFORME_ORTOGRAFICAS_COMPLETO',path)
