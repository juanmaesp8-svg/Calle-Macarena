# Denoising físico de Cycles CPU con OIDN

El Blender4.3.2 de este entorno no incluye OpenImageDenoise integrado. Se usa el algoritmo oficial OIDN2.5.1 por CPU, descargado desde su publicación de RenderKit y verificado contra SHA256 publicado.

Archivo: `oidn-2.5.1.x86_64.linux.tar.gz`

SHA256: `743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6`

Fuente: https://github.com/RenderKit/oidn/releases/tag/v2.5.1

## Preparar pases en Blender

`scene.cycles.use_denoising = False`

`scene.view_layers[0].cycles.denoising_store_passes = True`

En el compositor, conectar salidas `Image`, `Denoising Albedo` y `Denoising Normal` del nodo Render Layers a tres nodos File Output en `OPEN_EXR`, RGB, profundidad32bits. Todas las salidas deben tener idénticas dimensiones, sin aplicar AgX/exposición ni convertir normales a0..1. Los nodos File Output añaden número de frame, por ejemplo `beauty_0001.exr`. Guardar el blend con sus ajustes AgX/look/exposición antes del posprocesado.

## Procesar el render

```bash
blender -b escena.blend --python herramientas/denoise_exr.py -- \
  --beauty beauty_0001.exr \
  --albedo albedo_0001.exr \
  --normal normal_0001.exr \
  --output render_limpio.exr --png render_limpio.png \
  --threads 4 --prefilter-aux
```

También puede importarse el módulo dentro de Blender y llamarse `denoise_files(beauty, albedo, normal, output_exr, output_png, threads=4, prefilter_aux=True, scene=bpy.context.scene)`.

Se convierten EXR lineales a PFM (formato flotante aceptado por el binario de ejemplo oficial); se prefiltran auxiliares y se ejecuta filtro RT HDR con calidadhigh y guías de color/normal. El renderbeauty nunca se recorta ni se convierte a sRGB. Solo se limita el albedo auxiliar a reflectancia0..1 cuando muestras MonteCarlo puntuales exceden ese rango; el porcentaje afectado queda registrado. PNG16bits recibe únicamente la transformación de color del scene cargado. No se aplica desenfoque.

El `.oidn.json` registra comandos, SHA256 verificado, rangos, guías, tiempos y ajustes de exposición. El EXR resultante se vuelve a leer para comprobar que conserva los valores de salida OIDN. No se declara éxito por la sola existencia de un archivo.

Los buffers PFM quedan en `<nombre>_oidn_buffers/` para trazabilidad; pueden eliminarse después de comprobar el EXR y PNG. Los albedos/normales no se reinterpretan como imágenes fotográficas.
