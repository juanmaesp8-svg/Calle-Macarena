"""Real OIDN CPU denoising for Blender builds without built-in OpenImageDenoise.

Run with Blender Python, retaining its scene/display/color management:
 blender -b scene.blend --python denoise_exr.py -- --beauty beauty.exr \\
   --albedo albedo.exr --normal normal.exr --output clean.exr --png clean.png \\
   --threads 4 --prefilter-aux

Guides are Cycles Denoising Albedo/Normal passes, not shaded color previews.
All filtering is on scene-linear HDR floats. Display AgX is applied only when
saving PNG, using the loaded scene's exposure and look. No generic blur.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess
import sys
import time
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'oidn-2.5.1.x86_64.linux.tar.gz'
BINARY = ROOT / 'oidn-2.5.1.x86_64.linux' / 'bin' / 'oidnDenoise'
PUBLISHED_SHA256 = '743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6'
OFFICIAL_URL = 'https://github.com/RenderKit/oidn/releases/download/v2.5.1/oidn-2.5.1.x86_64.linux.tar.gz'


def verify_install():
    h = hashlib.sha256()
    with ARCHIVE.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    if h.hexdigest() != PUBLISHED_SHA256:
        raise RuntimeError('OIDN archive differs from published official digest; refusing execution')
    if not BINARY.is_file():
        raise FileNotFoundError(BINARY)
    return h.hexdigest()


def _load_exr(path):
    image = bpy.data.images.load(str(Path(path).resolve()), check_existing=False)
    try:
        if image.size[0] < 1 or image.size[1] < 1:
            raise ValueError('Invalid image dimensions: ' + str(path))
        w, h = image.size
        # Float EXR loads in the scene's linear working color space. Never
        # reinterpret linear HDR as sRGB and never clamp its beauty values.
        channels = image.channels
        data = np.empty(w*h*channels, dtype=np.float32)
        image.pixels.foreach_get(data)
        data = data.reshape(h, w, channels)
        if channels < 3:
            data = np.repeat(data[..., :1], 3, axis=2)
        else:
            data = data[..., :3].copy()
        if not np.all(np.isfinite(data)):
            raise ValueError('Input contains NaN/Inf: ' + str(path))
        return data, {'width':w, 'height':h, 'source_colorspace':image.colorspace_settings.name}
    finally:
        bpy.data.images.remove(image)


def _write_pfm(path, data):
    h, w, channels = data.shape
    if channels != 3:
        raise ValueError('PFM needs RGB float3')
    # Both bpy image pixels and PFM scanlines are bottom-to-top, so no flip.
    with Path(path).open('wb') as fh:
        fh.write(f'PF\n{w} {h}\n-1.0\n'.encode('ascii'))
        fh.write(np.ascontiguousarray(data, dtype='<f4').tobytes())


def _read_pfm(path):
    with Path(path).open('rb') as fh:
        if fh.readline().strip() != b'PF':
            raise ValueError('Not RGB PFM: ' + str(path))
        line = fh.readline()
        while line.startswith(b'#'):
            line = fh.readline()
        w, h = map(int, line.split())
        scale = float(fh.readline())
        dtype = '<f4' if scale < 0 else '>f4'
        data = np.frombuffer(fh.read(), dtype=dtype).astype(np.float32).reshape(h,w,3)
        if not np.all(np.isfinite(data)):
            raise ValueError('OIDN output contains NaN/Inf')
        return data


def _save_outputs(data, exr_path, png_path=None, scene=None):
    scene = scene or bpy.context.scene
    h, w, _ = data.shape
    image = bpy.data.images.new('OIDN clean linear HDR', width=w, height=h,
                               alpha=True, float_buffer=True)
    # Set the color space before assigning pixels: changing it afterwards
    # can invalidate generated Blender image buffers and write a black image.
    image.colorspace_settings.name = 'Linear Rec.709'
    pixels = np.ones((h,w,4), dtype=np.float32)
    pixels[...,:3] = data
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    settings = scene.render.image_settings
    old = {k:getattr(settings,k) for k in ('file_format','color_mode','color_depth')}
    try:
        settings.file_format = 'OPEN_EXR'
        settings.color_mode = 'RGB'
        settings.color_depth = '32'
        image.save_render(str(Path(exr_path).resolve()), scene=scene)
        persisted,_ = _load_exr(exr_path)
        if not np.allclose(persisted,data,atol=1e-5,rtol=1e-5):
            raise RuntimeError('Saved linear EXR differs from OIDN output; refusing PNG export')
        del persisted
        if png_path:
            settings.file_format = 'PNG'
            settings.color_mode = 'RGB'
            settings.color_depth = '16'
            image.save_render(str(Path(png_path).resolve()), scene=scene)
    finally:
        for k,v in old.items():
            setattr(settings,k,v)
        bpy.data.images.remove(image)


def denoise_files(beauty, albedo, normal, output_exr, output_png=None,
                  threads=4, prefilter_aux=False, scene=None):
    """Return verified execution metadata; auxiliary paths may both be None."""
    verified = verify_install()
    output_exr = Path(output_exr).resolve()
    output_exr.parent.mkdir(parents=True, exist_ok=True)
    work = output_exr.parent / (output_exr.stem + '_oidn_buffers')
    work.mkdir(exist_ok=True)
    beauty_data, source = _load_exr(beauty)
    _write_pfm(work/'beauty.pfm', beauty_data)
    del beauty_data
    commands = []
    guides = []
    guide_preparation = {}
    for flag, infile, key in [('--alb',albedo,'albedo'),('--nrm',normal,'normal')]:
        if infile is None:
            continue
        data, guide_source = _load_exr(infile)
        if (guide_source['width'],guide_source['height']) != (source['width'],source['height']):
            raise ValueError('Guide dimensions differ from beauty')
        guide_preparation[key] = {'input_min':float(data.min()),'input_max':float(data.max())}
        if key == 'albedo':
            # Low-sample Cycles Denoising Albedo can have rare Monte Carlo
            # excursions above reflectance 1 (not beauty exposure). OIDN's
            # albedo contract is 0..1. Clip only this auxiliary feature, record
            # affected fraction, and preserve beauty HDR without clamping.
            guide_preparation[key]['fraction_clipped_to_reflectance_range'] = float(np.mean((data<0)|(data>1)))
            data = np.clip(data,0.0,1.0)
        elif data.min() < -1.001 or data.max() > 1.001:
            raise ValueError('Normal guide should contain signed vectors -1..1')
        path = work/(key+'.pfm')
        _write_pfm(path,data)
        del data
        if prefilter_aux:
            out = work/(key+'_clean.pfm')
            cmd = [str(BINARY),'--device','cpu',flag,str(path),'--quality','high',
                   '--threads',str(threads),'--affinity','0','-o',str(out)]
            subprocess.run(cmd,check=True)
            commands.append(cmd)
            path = out
        guides.extend([flag,str(path)])
    cmd = [str(BINARY),'--device','cpu','--hdr',str(work/'beauty.pfm'),*guides,
           '--quality','high','--threads',str(threads),'--affinity','0',
           '-o',str(work/'clean.pfm')]
    if prefilter_aux and guides:
        cmd.append('--clean_aux')
    start = time.monotonic()
    subprocess.run(cmd,check=True)
    commands.append(cmd)
    data = _read_pfm(work/'clean.pfm')
    _save_outputs(data,output_exr,output_png,scene)
    metadata = {'algorithm':'Intel Open Image Denoise 2.5.1 RT, CPU, quality high',
                'official_archive':OFFICIAL_URL,'verified_sha256':verified,
                'working_space':'scene-linear HDR; unmodified exposure; no blur',
                'source':source,'beauty':str(beauty),'albedo':str(albedo),
                'normal':str(normal),'prefilter_aux':prefilter_aux,'guide_preparation':guide_preparation,
                'output_exr':str(output_exr),'output_png':str(output_png),
                'commands':commands,'seconds_main_filter':round(time.monotonic()-start,3),
                'minimum_linear_output':float(data.min()),'maximum_linear_output':float(data.max()),
                'png_color_management':{'view_transform':(scene or bpy.context.scene).view_settings.view_transform,
                                        'look':(scene or bpy.context.scene).view_settings.look,
                                        'exposure':(scene or bpy.context.scene).view_settings.exposure}}
    output_exr.with_suffix('.oidn.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n')
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--beauty',required=True)
    parser.add_argument('--albedo')
    parser.add_argument('--normal')
    parser.add_argument('--output',required=True)
    parser.add_argument('--png')
    parser.add_argument('--threads',type=int,default=4)
    parser.add_argument('--prefilter-aux',action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    print(json.dumps(denoise_files(args.beauty,args.albedo,args.normal,args.output,args.png,
                                  args.threads,args.prefilter_aux),indent=2))


if __name__ == '__main__':
    main()
