# Calle Macarena nº16

La vivienda se reconstruye en metros, a escala 1:1, desde los vectores de las plantas y el contraste con alzados y secciones del proyecto básico. El informe de control distingue cotas escritas, medidas calculadas y contradicciones documentales. El PDF no define todas las dimensiones: la profundidad del vaso, alturas de peldaños, nivel de agua y algunos niveles de acabado no se presentan como medidas confirmadas. El archivo conserva esa distinción; no se afirma exactitud total de datos que no existen en el proyecto.

El modelo Blender conserva colecciones, nombres, materiales procedurales y cámaras. GLB facilita inspección en otros visores, aunque sus materiales tienen una representación más sencilla que los shaders completos de Blender. Vegetación, coches, mobiliario, luces y paños de madera son accesorios o acabados de visualización identificados por separado.

## Archivos

- `../Calle_Macarena_modelo_1a1.blend`: modelo editable y materiales completos.
- `../Calle_Macarena_modelo_1a1.glb`: exportación para otros visores.
- `../informe_control.pdf`: comparación geométrica con los planos y tabla de dimensiones.
- `../renders/`: diez imágenes originales PNG de 16 bits y registro de cámaras/renderizado. Los EXR lineales permanecen en el entorno de trabajo y no se incluyen en el ZIP; el script de renderizado permite regenerarlos.
- `galeria_renders.pdf`: diez renders, uno por página, una vez completada la serie.
- `galeria.html`: galería sin conexión; pulsar una imagen para ampliar, rueda o botones para zoom y arrastre para desplazamiento.
- `hoja/contacto.jpg`: las diez vistas en una hoja.
- `validacion_entrega.json`: resolución real, hashes de imágenes y comprobación del mismo modelo Blender.

Mantener la estructura de carpetas al copiar la entrega: la galería HTML enlaza directamente los PNG originales en `../renders/`. Funciona sin servicios externos ni conexión.

## Reconstruir y comprobar

Blender 4.3.2, Python, Pillow y ReportLab se utilizaron en esta entrega. La comprobación geométrica emplea además PyMuPDF, Shapely y Matplotlib. Los datos geométricos extraídos están en `../modelo/` y `../geometria_base.json`.

Desde la carpeta raíz del proyecto:

```bash
blender -b --factory-startup --python-exit-code 1 --python modelo/construir_modelo.py
python control/verificar_modelo.py
```

El PDF original se incluye en `../fuentes/proyecto_basico.pdf`, con SHA256 conservado en `geometria_base.json`. Para repetir la comprobación contra el PDF, la ruta `fuente.ruta` de `geometria_base.json` debe apuntar al documento original suministrado. Revisar `informe_control.pdf` y `control/control_resultado.json` antes de renderizar. La reconstrucción vuelve a guardar el `.blend`; una serie completa debe renderizarse a partir de ese mismo archivo y sin regenerarlo entre imágenes.

## OIDN por CPU

El Blender de este entorno no incorpora OpenImageDenoise en su compilación. El posprocesado usa el filtro oficial OIDN 2.5.1 con pases lineales HDR de belleza, albedo y normales, preservando la gestión de color AgX. No aplica desenfoque genérico.

El binario oficial Linux x86_64 puede recuperarse desde:

https://github.com/RenderKit/oidn/releases/download/v2.5.1/oidn-2.5.1.x86_64.linux.tar.gz

SHA256 publicado y comprobado:

`743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6`

```bash
mkdir -p herramientas
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/RenderKit/oidn/releases/download/v2.5.1/oidn-2.5.1.x86_64.linux.tar.gz \
  -o herramientas/oidn-2.5.1.x86_64.linux.tar.gz
printf '%s\n' '743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6  herramientas/oidn-2.5.1.x86_64.linux.tar.gz' | sha256sum -c -
tar -xzf herramientas/oidn-2.5.1.x86_64.linux.tar.gz -C herramientas
```

Extraer y ejecutar únicamente después de que SHA256 coincida. `herramientas/denoise_exr.py` comprueba el archivo oficial antes de cada proceso. Las instrucciones completas y el registro de instalación están en `herramientas/OIDN_USO.md` y `herramientas/oidn_instalacion_verificada.json`. No es necesario incluir el archivo binario OIDN en una entrega de imágenes/modelo.

## Repetir los diez renders

```bash
blender -b Calle_Macarena_modelo_1a1.blend --python-exit-code 1 \
  --python modelo/renderizar.py -- \
  --ids 01,02,03,04,05,06,07,08,09,10 --width 2500 --samples 96
```

El script usa Cycles CPU y OIDN oficial externo. El número de muestras puede aumentarse para nuevos finales. La escena utiliza las mismas geometrías y cámaras guardadas; la vista 10 cambia iluminación para el atardecer. La dirección solar es una configuración de visualización, no un estudio solar fechado y georreferenciado.

La entrega corresponde a la serie inicial solicitada: diez vistas de 2500 × 1667 píxeles. Para repetirla a mayor resolución con el mismo modelo, cambiar por ejemplo a `--width 4000 --samples 256`; esto produce 4000 × 2667 píxeles y conserva las cámaras. Guardar una copia de la carpeta antes de repetir, porque los nombres de salida se reutilizan.

Tras completar los diez PNG:

```bash
python entrega/preparar_entrega.py
```

La preparación valida IDs 01..10, resolución mínima de 2500 px en el lado largo, coincidencia con el registro y el mismo SHA256 del `.blend` para todas las imágenes. Guarda `validacion_entrega.json` y crea las galerías únicamente si esos controles pasan. Nunca modifica los PNG, EXR, el registro de renders o el modelo.


## Dependencias Python y fuente

Puede instalarse el análisis en un entorno virtual local, sin modificar Python del sistema:

```bash
python -m venv .venv
.venv/bin/python -m pip install PyMuPDF Shapely==2.1.2 Matplotlib Pillow ReportLab numpy
.venv/bin/python control/verificar_modelo.py
```

`modelo/preparar_superficies.py` calcula triangulación restringida mediante Shapely2.1. Los JSON de superficies ya se incluyen: `construir_modelo.py` no necesita Shapely en el Python interno de Blender. Los scripts de extracción usan rutas relativas a la entrega. Para reproducir el modelo bastan los JSON y Blender; el PDF se utiliza para revisar y repetir extracciones.

La base del portal y el forjado se han separado en sólidos sin caras exteriores duplicadas: el conjunto mantiene base+3,35m y coronación+4,75m. Los petos superiores empiezan en+3,70m porque los primeros35cm del portal pertenecen al forjado.

Los informes iniciales `informe_geometria.*` correspondían a la fase anterior al modelo. La entrega actual se documenta en `informe_control.pdf`, `tabla_dimensiones_modeladas.csv` y `control/control_resultado.json`.


Para configurar un nuevo entorno Linuxx86_64 con Blender ya disponible, ejecutar `bash entrega/setup_entorno.sh`. Crea únicamente el Python local `.venv`, instala las versiones de `requirements.lock.txt`, verifica el SHA256 de OIDN y ejecuta una prueba real del filtroCPU. `entorno_verificado.json` registra las versiones comprobadas en la nube.

`criterios_de_representacion.json` separa cotas directas, cálculos, deducciones y superficies de visualización. Incluye detalles de carpintería, cotas exteriores de referencia y geometría que no se completa con dimensiones supuestas.
