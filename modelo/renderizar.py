"""Render Cycles del mismo .blend, con OIDN oficial externo en HDR lineal.
blender -b Calle_Macarena_modelo_1a1.blend --python-exit-code 1 --python modelo/renderizar.py -- --ids 01,02 --width 2500 --samples 96
"""
from pathlib import Path
import sys,json,argparse,time,hashlib
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'modelo'));sys.path.insert(0,str(ROOT/'herramientas'))
from materiales import setup_lighting
from denoise_exr import denoise_files
parser=argparse.ArgumentParser()
parser.add_argument('--ids',default='01');parser.add_argument('--width',type=int,default=2500)
parser.add_argument('--samples',type=int,default=96);parser.add_argument('--qa',action='store_true')
parser.add_argument('--preview',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
scene=bpy.context.scene
if not args.qa:
    result=json.loads((ROOT/'control/control_resultado.json').read_text())
    if not result['apto_para_renders'] or result.get('version')!=2:raise RuntimeError('Control geométrico V2 no superado')
output=ROOT/('control/ortograficas' if args.qa else 'previsualizaciones' if args.preview else 'renders')
output.mkdir(parents=True,exist_ok=True)
manifest_path=output/'registro_renders.json'
manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
initial_hidden={o.name:o.hide_render for o in scene.objects}
source_hash=hashlib.sha256((ROOT/'Calle_Macarena_modelo_1a1.blend').read_bytes()).hexdigest()
for ident in args.ids.split(','):
    for ob in scene.objects:
        if ob.name in initial_hidden:ob.hide_render=initial_hidden[ob.name]
    camera=next(o for o in scene.objects if o.type=='CAMERA' and o.name.startswith(ident+'_'))
    scene.camera=camera
    mode='sunset' if ident=='10' else 'day'
    setup_lighting(scene,mode)
    for ob in scene.objects:
        if ob.type=='LIGHT' and ob.name.startswith('Luz_exterior_'):
            ob.data.energy=18 if mode=='sunset' else 0
    scene.cycles.use_denoising=False;scene.cycles.device='CPU'
    scene.render.threads_mode='FIXED';scene.render.threads=5
    scene.cycles.samples=args.samples;scene.cycles.adaptive_min_samples=16
    scene.cycles.adaptive_threshold=.008 if not args.preview else .025
    scene.cycles.max_bounces=14;scene.cycles.diffuse_bounces=5;scene.cycles.glossy_bounces=6
    scene.cycles.caustics_reflective=False;scene.cycles.caustics_refractive=False
    scene.cycles.transmission_bounces=12
    scene.view_layers[0].cycles.denoising_store_passes=True
    scene.render.use_persistent_data=True
    scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width*2/3)
    if args.qa:
        x,y=camera['resolucion_px'];scene.render.resolution_x=x;scene.render.resolution_y=y
        camera.data.sensor_fit='HORIZONTAL'
        # Exclusión de entorno sólo en la sesión analítica: el archivo principal no cambia.
        visible={'Vivienda','Trastero','Cubierta','Porches','Carpinterias'}
        if ident=='QA00':visible|={'Parcela','Piscina','Pavimentos','Cerramiento_exterior','Aparcamiento','Jardin'}
        for ob in scene.objects:
            if ob.type=='MESH' and not any(c.name in visible for c in ob.users_collection):ob.hide_render=True
        scene.render.film_transparent=False
        # Fondo uniforme para facilitar comparación y evitar alfa perdida en RGB.
        scene.world.node_tree.nodes.clear()
        bg=scene.world.node_tree.nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.7
        out=scene.world.node_tree.nodes.new('ShaderNodeOutputWorld');scene.world.node_tree.links.new(bg.outputs[0],out.inputs['Surface'])
    else:scene.render.film_transparent=False
    scene.render.resolution_percentage=100
    scene.use_nodes=True;nt=scene.node_tree;nt.nodes.clear()
    render=nt.nodes.new('CompositorNodeRLayers')
    raw=output/'lineales'/ident;raw.mkdir(parents=True,exist_ok=True)
    rawpaths={}
    for key,socket in [('beauty','Image'),('albedo','Denoising Albedo'),('normal','Denoising Normal')]:
        file=nt.nodes.new('CompositorNodeOutputFile');file.base_path=str(raw)
        file.format.file_format='OPEN_EXR';file.format.color_mode='RGB';file.format.color_depth='32';file.format.exr_codec='ZIP'
        file.file_slots[0].path=key+'_';nt.links.new(render.outputs[socket],file.inputs[0]);rawpaths[key]=raw/(key+'_0001.exr')
    print('INICIO_RENDER',ident,scene.render.resolution_x,scene.render.resolution_y,flush=True)
    start=time.monotonic();bpy.ops.render.render()
    render_seconds=time.monotonic()-start
    stem=camera.name
    info=denoise_files(rawpaths['beauty'],rawpaths['albedo'],rawpaths['normal'],output/(stem+'.exr'),output/(stem+'.png'),threads=5,prefilter_aux=True,scene=scene)
    item={'id':ident,'nombre':stem,'motor':'Cycles CPU','modelo_sha256':source_hash,'resolucion':[scene.render.resolution_x,scene.render.resolution_y],
          'samples_max':args.samples,'muestreo_adaptativo':scene.cycles.adaptive_threshold,'camara_posicion_m':list(camera.location),'camara_rotacion_radianes':list(camera.rotation_euler),
          'focal_mm':camera.data.lens,'tipo':camera.data.type,'shift_y':camera.data.shift_y,'iluminacion':mode,'segundos_cycles':round(render_seconds,2),
          'png':str(output/(stem+'.png')),'exr':str(output/(stem+'.exr')),'denoise':info['algorithm']}
    manifest=[m for m in manifest if m['id']!=ident]+[item]
    manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print('RENDER_TERMINADO',ident,round(render_seconds,2),flush=True)
    # Liberar imágenes auxiliares; el .blend original permanece sin cambios.
print('SERIE_COMPLETADA',len(args.ids.split(',')),flush=True)
