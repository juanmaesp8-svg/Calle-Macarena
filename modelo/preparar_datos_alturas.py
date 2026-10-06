from pathlib import Path
import json, math
ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT/'modelo'
plant = json.loads((MODEL/'datos_planta.json').read_text())
F = plant['factor_m_por_pt']
O = plant['origen_pdf_pt']
def xy(p): return [round((p[0]-O[0])*F,6), round((O[1]-p[1])*F,6)]
def polygon(points): return {'vertices_pdf_pt':points,'vertices_xy_m':[xy(p) for p in points]}
def bbox_xy(b):
 p0,p1=xy([b[0],b[3]]),xy([b[2],b[1]])
 return p0+p1
D = {
 'version':1,
 'estado':'Geometría derivada del PDF para modelo reproducible; no levantamiento ni proyecto de ejecución. Se procede tras instrucción de continuar utilizando únicamente el PDF, con discrepancias documentadas.',
 'unidades':'metros, escala1:1',
 'origen_pdf_pt':O,
 'factor_m_por_pt':F,
 'ejes':'X derecha en planta; Y hacia lindero trasero; Z vertical; sin orientación solar georreferenciada',
 'regla':'XY de plantas35/37; Z de alzados38/secciones39; si hay conflicto se mantiene XY de planta y Z más consistentemente repetida. No forzar superficies declaradas.',
 'precision':'Cuantización vectorial habitual0,12pt≈6,35mm; cifras largas conservan trazabilidad, no certifican precisión milimétrica.',
 'niveles':{
  'suelo_vivienda_m':0.0,'jardin_m':-0.15,'forjado_inferior_m':3.35,'forjado_superior_m':3.70,
  'forjado_canto_m':0.35,'cielorraso_m':3.20,
  'peto_bajo_coronacion_m':4.40,'peto_alto_coronacion_m':5.10,
  'portal_entrada_base_m':3.35,'portal_entrada_coronacion_m':4.75,
  'pergola_viga_inferior_m':2.50,'pergola_viga_superior_m':2.85
 },
 'fuente_niveles':{
  'directas':['suelo0,00,jardín−0,15,forjado3,35/3,70: rotulación PDF38/39'],
  'calculadas':['cielorraso3,20: y134,44 respecto194,92 en sección1; y439,12 respecto499,60 en sección3',
                'petoalto5,10: principal y98,56, suelo194,92; lateral y418,00,suelo514,48',
                'petobajo4,40: principal y111,76, suelo194,92; lateral y431,32,suelo514,48',
                'portal4,75/3,35: principal y105,16/131,56,suelo194,92; sec3 y409,84/436,24,suelo499,60; sec4 y555,28/581,80,suelo645,04',
                'pérgola2,50/2,85: sec1 y147,64/141,04,suelo194,92; alzado vial306,64/300,04,suelo353,92']
 },
 'huecos_exteriores':[],
 'cubierta':{},
 'pergola':{
  'anchura_completa_m':5.0165,'largo_completo_planta_m':4.191,
  'luz_transversal_planta_m':4.4196,'luz_transversal_alzado_m':4.41325,
  'luz_longitudinal_planta_m':3.94335,'luz_longitudinal_seccion_m':3.937,
  'cara_inferior_vigas_m':2.5,'cara_superior_vigas_m':2.85,
  'estado':'Anchura completa y luz reconciliadas; diferencias≤6,35mm en dibujo.',
  'evidencia':'Planta35: x312,08–406,88; apoyo derecho395,60–406,88. AlzadoVIAL: x491,84–586,64; apoyo575,24–586,64. Largo y542,08–621,28; cara interior apoyo616,60.'
 },
 'cerramiento':{},
 'puerta_peatonal_parcela':{},
 'incertidumbres':[],
}
# Z preferred from the consistent elevations, preserving all plan XY.
H={
'V_bano1_norte':(1.0,2.5,[633.20,614.56,652.16,642.88],'trasero',1.00,1.50),
'V_despacho_oeste':(.9,2.5,[408.32,147.64,427.28,177.88],'principal',1.00,1.50),
'V_bano2_oeste':(1.0,2.5,[466.88,147.64,482.00,176.08],'principal',.80,1.50),
'V_lavadero_oeste':(1.0,2.5,[519.32,147.64,530.72,176.08],'principal',.60,1.50),
'P_lavadero_oeste':(0.0,2.5,[540.92,147.64,559.04,194.92],'principal',None,None),
'V_aseo_oeste':(1.0,2.5,[567.92,147.64,583.04,176.08],'principal',.80,1.50),
'P_principal_oeste':(0.0,2.5,[607.28,147.64,632.60,194.92],'principal',None,None),
'V_salon_oeste':(.9,2.5,[660.56,147.64,698.36,177.88],'principal',2.00,1.60),
'V_dormitorio1_este':(.9,2.5,[812.36,467.20,850.16,497.44],'lateral_porche',2.00,1.60),
'V_dormitorio1_sur':(0.0,2.5,[592.28,306.64,620.60,353.92],'vial',1.50,2.50),
'V_dormitorio2_este':(0.0,2.5,[751.16,467.20,779.60,514.48],'lateral_porche',1.50,2.50),
'V_dormitorio3_este':(0.0,2.5,[669.68,467.20,698.12,514.48],'lateral_porche',1.50,2.50),
'V_cocina_este':(0.0,2.5,[564.08,467.20,642.20,514.48],'lateral_porche',4.13,2.50),
'V_salon_este':(0.0,2.5,[455.60,467.20,557.48,514.48],'lateral_porche',5.39,2.05),
'P_instalaciones_sur':(0.0,2.5,[461.72,306.64,491.84,353.92],'vial',None,None),
}
for h in plant['huecos_exteriores']:
 r=dict(h); n=r['nombre']; a,z,b,elev,wa,ha=H[n]
 r.update({'z_antepecho_m':a,'z_dintel_m':z,'alto_modelado_m':round(z-a,6),
           'ancho_modelado_m':h['ancho_grafico_m'],'ancho_documental_m':wa,'alto_memoria_m':ha,
           'bbox_alzado_pdf_pt':b,'alzado_fuente':elev,
           'normal_exterior_xy':{'N':[0,1],'S':[0,-1],'E':[1,0],'W':[-1,0]}[h['fachada_local']],
           'fuente_z':'PDF38 alzados; medidas gráficas calculadas, nominales contrastadas con memoria19/20.'})
 if n=='V_despacho_oeste':r['discrepancia']='Modelo alto1,60 y antepecho0,90 conforme alzado/sec2; memoriaV4 alto1,50.'
 if n=='V_salon_este':r['discrepancia']='Modelo alto2,50 conforme alzado/sec1 y superficie13,47m²; memoriaV7 alto2,05.'
 if n=='P_instalaciones_sur':r['discrepancia']='Planta apertura1,33985m; alzado1,59385m hasta esquina exterior, incorporando~0,25m de muro. Se conserva plantaXY.'
 if n=='P_lavadero_oeste':r['discrepancia']='Ancho planta0,9652m frente alzado0,95885m; cuantización6,35mm.'
 if n=='V_dormitorio1_sur':r['nota']='Hueco perpendicular real del dormitorio1; alzado vial lo muestra en profundidad detrás de pérgola. No duplicarlo como hueco frontal de salón.'
 D['huecos_exteriores'].append(r)
# Roof rectangles come from explicit outer/inner lines of P37, not an envelope extrusion.
central_outer=[[323.84,169.96],[406.88,169.96],[406.88,542.08],[323.84,542.08]]
central_inner=[[326.60,172.72],[404.12,172.72],[404.12,539.32],[326.60,539.32]]
portal_outer=[[247.28,416.44],[373.52,416.44],[373.52,557.20],[247.28,557.20]]
portal_inner=[[250.04,419.32],[370.64,419.32],[370.64,554.44],[250.04,554.44]]
portal_visible=[[247.28,416.44],[323.84,416.44],[323.84,542.08],[373.52,542.08],[373.52,557.20],[247.28,557.20]]
low_visible=[[262.4,122.44],[453.2,122.44],[453.2,197.32],[406.88,197.32],[406.88,169.96],[323.84,169.96],[323.84,416.44],[262.4,416.44]]
install_visible=[[262.4,557.2],[312.08,557.2],[312.08,621.28],[262.4,621.28]]
D['cubierta']={
 'pagina_planta_pdf':37,'registro_con_planta35':'Mismo XY; desplazamiento−1,68pt corresponde sólo página36, NO aplicarlo a37.',
 'forjado_base_m':3.35,'forjado_superior_m':3.70,
 'criterio':'Forjado sigue huella real de cerramientos y vuelo del portal; sobre él existen paños de peto a diferentes alturas. No crear caja única de5,10m ni rellenar porche abierto. Las diagonales/flechas corresponden al drenaje de cubierta plana.',
 'panos':[
 {'nombre':'Pano_central_alto','coronacion_m':5.10,'base_peto_m':3.70,'exterior':polygon(central_outer),'interior':polygon(central_inner),'regla':'Anillo rectangularalto; XY de cubierta prevalece frente ancho discordante de trasero/sec3.'},
 {'nombre':'Pano_trasero_D1_y_banda_banos','coronacion_m':4.40,'base_peto_m':3.70,'contorno_visible':polygon(low_visible),'regla':'Paño inferior continuo alaD1 y banda oeste; el centralalto superpuesto ocupa el recorte interior.'},
 {'nombre':'Pano_portal_entrada_con_vuelo','coronacion_m':4.75,'base_peto_m':3.35,'exterior':polygon(portal_outer),'interior':polygon(portal_inner),'contorno_visible':polygon(portal_visible),'regla':'Recortar por centralalto; parte que vuela0,80m es abierta por debajo, no recinto cerrado hasta suelo.'},
 {'nombre':'Pano_instalaciones_bajo','coronacion_m':4.40,'base_peto_m':3.70,'contorno_visible':polygon(install_visible),'regla':'Contorno visible empieza y557,20 por oclusión del portal; recinto instalaciones empieza y542,08.'}
 ],
 'petos_tramos':[],
 'acabado_grava':{'espesor_memoria_m':.05,'z_real_cara_superior_m':None,'pendiente_porcentaje':None,
  'representacion_recomendada':'Superficie/material de grava referida a planta de cubierta, sin resolver espesor acumulado ni pendientes no acotadas. Si se visualiza sobre cara3,70 del forjado, registrar que es plano de referencia y no cota de acabado certificada.',
  'prohibido':'No inventar cotas de cumbreras de drenaje, pendiente ni paquete constructivo para obtenerZ acabado.'}
}
# Exact bars correspond to visible paired outer/inner vector contours, clipped at higher roof.
BARS=[
 ('Peto_central_N',[323.84,169.96,406.88,172.72],3.70,5.10),
 ('Peto_central_E',[404.12,172.72,406.88,539.32],3.70,5.10),
 ('Peto_central_S',[323.84,539.32,406.88,542.08],3.70,5.10),
 ('Peto_central_W',[323.84,172.72,326.60,539.32],3.70,5.10),
 ('Peto_bajo_W_trasero',[262.40,122.44,265.16,416.44],3.70,4.40),
 ('Peto_bajo_N',[265.16,122.44,450.44,125.32],3.70,4.40),
 ('Peto_bajo_E_D1',[450.44,122.44,453.20,197.32],3.70,4.40),
 ('Peto_bajo_S_D1',[406.88,194.44,450.44,197.32],3.70,4.40),
 ('Peto_bajo_W_instalaciones',[262.40,557.20,265.16,621.28],3.70,4.40),
 ('Peto_bajo_S_instalaciones',[265.16,618.40,309.32,621.28],3.70,4.40),
 ('Peto_bajo_E_instalaciones',[309.32,557.20,312.08,621.28],3.70,4.40),
 ('Peto_portal_W',[247.28,416.44,250.04,557.20],3.35,4.75),
 ('Peto_portal_N_visible',[250.04,416.44,323.84,419.32],3.35,4.75),
 ('Peto_portal_S',[250.04,554.44,370.64,557.20],3.35,4.75),
 ('Peto_portal_E_visible',[370.64,542.08,373.52,557.20],3.35,4.75),
]
for n,b,z0,z1 in BARS:
 D['cubierta']['petos_tramos'].append({'nombre':n,'bbox_pdf_pt':b,'bbox_xy_m':bbox_xy(b),'z_base_m':z0,'z_coronacion_m':z1,'fuente':'Líneas dobles exteriores/interiores de PDF37, capa000SECCIÓN, emparejadas conZ de PDF38/39.'})
# Retain side-specific evidence; no claim that unrecorded corner transitions are solved.
D['cubierta']['marquesina_terraza_derivada']={
 'nombre':'Marquesina_terraza_sobre_salon_y_cocina',
 'bbox_pdf35_pt':[406.88,335.68,449.36,542.08],
 'bbox_xy_m':bbox_xy([406.88,335.68,449.36,542.08]),
 'z_inferior_m':3.35,'z_superior_m':3.55,'canto_m':.20,
 'largo_m':206.4*F,'profundidad_vuelo_m':42.48*F,
 'fuente_longitud':'ALZADO LATERAL PORCHE PDF38 x449,00–655,40;y447,40–451,12. Suelo514,48=>Z3,54965/3,3528m. x449 se registra con testeroY542,08 de planta35.',
 'fuente_profundidad':'ALZADO VIAL PDF38 franja x586,64–629,12;y286,84–290,56. x586,64 corresponde a fachadaX406,88; vuelo42,48pt=>2,2479m.',
 'fuente_seccion':'SECCION4 PDF39 vuelo x585,32–627,80;y577,96–581,80; suelo645,04. Dirección X invertida, cara fachada627,80 correspondeX406,88 y extremo585,32=>X449,36. Canto≈0,20m y vuelo2,2479m.',
 'registro_xy':'Alzado lateral: v_planta=542,08−(x_alzado−449,00). Alzado vial: u_planta=x_alzado−179,76. ResultadoX406,88–449,36/Y335,68–542,08.',
 'criterio':'Voladizo superficial horizontal; no pilares ni recinto debajo. Dos alzados y sección4 respaldan profundidad2,25m y canto0,20m. Se diferencia del portal/pañoentrada y de pérgola.',
 'discrepancia':'El contorno proyectado de esta marquesina no aparece en cubierta37. XY se deriva de dos proyecciones ortográficas registradas a caras inequívocas de planta35; no se presenta como cota directa de planta.'
}
D['cerramiento']={
 'z_base_referencia_jardin_m':-.15,
 'evidencia_lateral_oeste':{'altura_desde_jardin_m':1.8,'z_coronacion_m':1.65,'fuente':'ALZADO PUERTA PRINCIPAL: suelo194,92; jardín197,80; postecoronación163,72; altura(197,80−163,72)×F=1,803m.'},
 'evidencia_lateral_este':{'altura_desde_jardin_m':2.0,'z_coronacion_m':1.85,'fuente':'ALZADO LATERAL PORCHE: suelo514,48; jardín517,24; coronación479,44; altura(517,24−479,44)×F=2,00025m.'},
 'evidencia_frontal_esquema':{'altura_m':2.0,'z_absoluto_m':None,'fuente':'Cerramiento exterior PDF38: y715,36–753,16 =2,00025m; sin rotulación de cotaZ.'},
 'evidencia_trasero':{'altura_desde_jardin_m':2.0,'z_coronacion_m':1.85,'fuente':'ALZADO TRASERO: derecha y626,80; jardín664,60 =2,00025m; poste izquierdo parcial y636,52 no define inequívocamente muro entero.'},
 'criterio_modelo':'Asignar alturas laterales por su vista correspondiente si se visualizan los linderos; frontal/trasero2,00m apoyados en datumjardín−0,15 es interpretación explícita. Conservar quiebrosXY y reconocer encuentros de alturas distintos no detallados.',
 'estado':'Perfil topográfico/encuentros no acotados; no convertir en dato directo ni inventar pendiente del terreno.'
}
base=json.loads((ROOT/'geometria_base.json').read_text())
gate=base['accesos']['pedestrian_gate_plan03']
pts=gate['leaf_endpoint_pdf_pt']
# Gate drawn in P36. Register its Y to P35 by +1.68pt, preserving actual hinge.
reg=[[p[0],p[1]+1.68] for p in pts]
D['puerta_peatonal_parcela']={
 'fuente_xy_pdf':36,'hoja_pdf36_pt':pts,'registro_y_a_pdf35_pt':1.68,
 'hoja_registrada_pdf35_pt':reg,'hoja_xy_m':[xy(p) for p in reg],
 'bisagra_pdf35_pt':reg[1],'bisagra_xy_m':xy(reg[1]),
 'longitud_modelada_hoja_m':gate['graphic_leaf_length_m'],
 'normal_vial_desde_parcela':'La hoja gira en lindero frontal inclinado; utilizar dirección de lindero del polígono de parcela, no ejeX global.',
 'alto_representacion_m':2.0,'z_base_representacion_m':-.15,'z_superior_representacion_m':1.85,
 'discrepancia':'Hoja planta0,820m frente hoja candidata del alzado1,162m. La planta determinaXY y tamaño; no trasladar el paneloscuro completo3,45m como hueco.',
 'estado':'Elección explícita de planta para mantener posición y anchura; altura proviene esquema de cerramiento2,00m.'
}
D['incertidumbres']=[
 {'id':'V7_alto','modelado':'2,50m','alternativa_pdf':'Memoria2,05m','criterio':'Alzado lateral/sec1 y superficie13,47m² coinciden2,50.'},
 {'id':'Despacho_alto','modelado':'1,60m con antepecho0,90m','alternativa_pdf':'MemoriaV4alto1,50m','criterio':'Alzado principal/sec2 prevalecen gráficamente.'},
 {'id':'Portal_alturas','modelado':'Base3,35/coronación4,75m','alternativa_pdf':'Sección2base3,70/coronación4,90m','criterio':'Principal/sec3/sec4 coincidentes.'},
 {'id':'Central_ancho_transversal','modelado':'X323,84–406,88pt de cubierta37:4,39420m','alternativa_pdf':'Trasero/sec3 muestran98,28pt=5,20065m y bordeoccidentalX308,72pt en lugar323,84; diferencia0,80m','criterio':'XY de cubierta37 coincide con vial/sec4; trasero/sec3 conservados como residualdocumental.'},
 {'id':'Instalaciones_puerta_ancho','modelado':'1,33985m en planta','alternativa_pdf':'1,59385m en alzado vial','criterio':'Conservar separación de muros y huecoXY; alzado aparenta incorporar pared lateral.'},
 {'id':'Peatonal_ancho','modelado':'0,820355m planta36','alternativa_pdf':'1,162m en alzado','criterio':'Planta gobiernaXY y ancho de hoja.'},
 {'id':'Cerramiento','modelado':'Oeste1,80m y este2,00m desde jardín según sus alzados','alternativa_pdf':'Encuentros y perfilZ no especificados','criterio':'Conservar evidencia por fachada y declararinterpretación enfrente/trasero.'},
 {'id':'Cubierta_acabado_Z','modelado':'Material/superficie de referencia; no asignar acabado real','alternativa_pdf':'Memoriagrava5cm, paquete no suficientemente acotado','criterio':'Z3,70 es cara superiorforjado; no afirmar cota real de grava.'},
 {'id':'Marquesina_terraza_omitida_en_cubierta','modelado':'Canto0,20m y vuelo2,2479m sobre salón/cocina según2alzados y sección4','alternativa_pdf':'Planta cubierta37 no muestra contornoX406,88–449,36/Y335,68–542,08','criterio':'Derivación cruzada de proyecciones registradas; conservar como elemento inferido documentalmente, no dato directo de planta.'}
]
D['incertidumbres'].append({'id':'Cerramiento_espesor','modelado':'0,1524m hacia interior, exterior en lindero','alternativa_pdf':'Sólo el tendedero dibuja espesor real x205,64–208,52pt; otroslinderos carecen de doblecara','criterio':'Extrapolar detalle de tendedero al cerramiento; deducción explícita, sin centrar valla ni invadir fuera del polígono.'})
D['cerramiento']['criterio_espesor']='Exterior sobrelindero;0.1524m hacia dentro deducido de tendedero, no cota verificada en otros tramos.'
(MODEL/'datos_alturas.json').write_text(json.dumps(D,ensure_ascii=False,indent=2))
print('Wrote datos_alturas.json:',len(D['huecos_exteriores']),'huecos,',len(D['cubierta']['petos_tramos']),'tramos petos;',len(D['incertidumbres']),'residuales documentales.')
