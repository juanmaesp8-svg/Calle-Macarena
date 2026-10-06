# Calle Macarena nº16 — revisión V2

V2 reconstruye la vivienda con la **planta final del proyecto de obra** y las confirmaciones del usuario para el nuevo trastero. La posición X/Y procede de esa planta; las alturas Z que siguen siendo aplicables proceden de los alzados y secciones del proyecto básico. La escala del modelo es 1:1 en metros.

Esta revisión sustituye la antigua zona de instalaciones y la pérgola/comedor de piscina por el **TRASTERO** representado en la nueva planta. La pérgola antigua no forma parte del resultado V2. Los acabados solicitados son fachada blanca, carpinterías antracita, madera clara vertical pegada a los paños existentes entre cristaleras, solería exterior crema de **90 × 90 cm** y césped **artificial**.

La revisión es independiente e incluye el modelo, controles, fuentes y una primera imagen nueva de Cycles. La coincidencia arquitectónica se evalúa mediante el control V2; no se afirma fidelidad absoluta de datos ausentes o contradictorios. Las galerías, diez renders e informes V1 conservados en el historial no validan ni representan V2.

## Abrir y revisar

Mantener la estructura completa de carpetas al copiar el proyecto.

1. Abrir `../Calle_Macarena_modelo_1a1.blend` con **Blender 4.3.2** o una versión compatible posterior. Es el archivo editable con colecciones, objetos nombrados, materiales PBR, luces y cámaras. Para inspección rápida usar Solid; para valorar materiales y transparencia usar Rendered/Cycles. Los materiales deben revisarse en el archivo V2 regenerado, no en la copia histórica.
2. Importar `../Calle_Macarena_modelo_1a1.glb` mediante `File > Import > glTF 2.0` en Blender o abrirlo en un visor glTF. Facilita revisar geometría y escala; conserva una apariencia más sencilla que los shaders de Blender.
3. Consultar `../control/informe_revision_v2.pdf`, generado al terminar la reconstrucción y el cotejo V2. Ese informe debe acompañar los controles de geometría reales del modelo. Mientras no se haya generado o el control no haya aprobado el modelo, V2 continúa en revisión.

El nombre base del modelo es el mismo que en V1; **la carpeta V2, las fuentes y la revisión registrada en la escena determinan la versión**. El modelo debe mostrar el nuevo trastero y carecer de la pérgola anterior. Los datos de referencia anteriores necesarios para reconstruir se conservan en `../fuentes/datos_v1/`.

## Fuentes y alturas confirmadas

| Información | Fuente aplicable |
|---|---|
| Huellas, paredes, huecos, trastero, piscina, jardín y posiciones X/Y | `../fuentes/planta_final_proyecto_obra.pdf`, página 1; extracción y auditoría vectorial V2 |
| Alturas de la vivienda y elementos que permanecen | `../fuentes/proyecto_basico.pdf`, alzados y secciones; discrepancias identificadas en el control |
| Trastero: cara inferior/superior de forjado | **+3,35 / +3,70 m**, confirmación expresa del usuario |
| Trastero: coronación de peto | **+4,40 m**, confirmación expresa del usuario |
| Puerta interior del trastero: altura | **2,03 m**, confirmación expresa del usuario |
| Portón frontal del trastero: altura | **2,50 m**, confirmación expresa del usuario |
| Acabados V2 | Confirmación del usuario en `../modelo/confirmaciones_usuario_v2.json` |

Las alturas confirmadas del trastero no se atribuyen al PDF de la nueva planta, que no contiene alzados de ese volumen. Los anchos y las posiciones de sus puertas se obtienen de la planta; no se alteran para ajustar una composición visual.

El origen y la transformación de coordenadas están documentados en los JSON de `../modelo/` y en el cotejo V2. X apunta a la derecha de la planta, Y hacia el fondo y Z hacia arriba; Z=0 corresponde al suelo de vivienda. La precisión que permite el dibujo vectorial y la discrepancia entre documentos deben leerse en el informe, aunque los JSON conserven muchos decimales para trazabilidad.

## Reconstrucción reproducible

Requisitos: Blender 4.3.2 con Cycles, Python con las dependencias de `requirements.lock.txt` y los archivos de datos incluidos. Los shaders y HDRIs se cargan localmente; la construcción no descarga recursos nuevos.

Desde la **raíz de la carpeta V2**:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r entrega/requirements.lock.txt
```

La secuencia de reconstrucción V2 es:

```bash
.venv/bin/python modelo/aplicar_revision_v2.py
.venv/bin/python modelo/preparar_superficies.py
blender -b --factory-startup --python-exit-code 1 \
  --python modelo/construir_modelo.py
.venv/bin/python control/verificar_revision_v2.py
```

`aplicar_revision_v2.py` prepara los datos del candidato a partir de la planta final y las confirmaciones; `preparar_superficies.py` triangula las superficies sin sustituir su huella. El constructor guarda los archivos `.blend` y `.glb` de esta carpeta. `--python-exit-code 1` hace que Blender termine con error si falla el script: no basta con que el proceso haya creado un archivo.

La reconstrucción sobrescribe esos dos archivos de trabajo; guardar una copia si se han hecho cambios manuales que se quieran conservar. **No ejecutar `extraer_planta_pdf.py` ni `preparar_datos_alturas.py` heredados de V1 sobre los datos V2:** su flujo original corresponde al proyecto básico anterior y puede restituir la antigua pérgola. La revisión usa el preparador V2 indicado arriba.

Antes de producir renders, comprobar el control nuevo: ortográfica superior y superposición con la planta final, fachadas, sección/niveles y tabla de dimensiones. Corregir las diferencias geométricas antes de valorar el acabado fotográfico. El `informe_control.pdf` y los `control_resultado.json` históricos V1, si permanecen en la carpeta, no sustituyen al control V2.

## Materiales, HDRIs y portabilidad

Los HDRIs fotográficos **Royal Esplanade** y **Venice Sunset** de Poly Haven se utilizan como relleno difuso; su licencia es **CC0 1.0**. Los archivos se conservan en `../assets/hdri/` y se empaquetan en Blender con `image.pack()`. Los rayos de cámara, transmisión y reflexión muestran cielo físico Nishita: no se utiliza una panorámica de otro edificio como fondo arquitectónico del proyecto.

Fuentes de descarga, texto oficial de licencia y SHA-256 están en:

- `../assets/licencias/recursos_materiales_v2.json`.
- `../assets/licencias/polyhaven_cc0_texto_oficial.json`.
- `../analisis_v2/materiales_realismo.md`.

Los acabados de estuco, porcelánico, madera, textiles y césped artificial son shaders procedurales originales a escala métrica. No se atribuyen a texturas fotográficas de terceros. El `.blend` conserva los nodos completos y las microfibras del césped. El GLB conserva el contorno de césped y omite sus microfibras para facilitar la descarga; el `.glb` puede representar estos materiales con colores base y parámetros simplificados porque glTF no reproduce los árboles procedurales de Cycles. Para render final usar Blender.

La iluminación mediterránea y su orientación son decisiones fotográficas. No constituyen un estudio solar fechado/georreferenciado, ya que no se ha confirmado norte geográfico. La luz de día es predominantemente natural; las luminarias exteriores se activan para la vista de tarde.

## Límites del modelo

- La documentación no define profundidad, perfil del vaso ni nivel de agua de piscina con suficiente seguridad. No se presenta un fondo o una profundidad supuesta como medida del proyecto. La superficie de agua se identifica como representación visual.
- El mobiliario interior, tapicerías, vegetación y vehículos son assets de visualización; sus detalles y alturas no acotados no se convierten en arquitectura. Los interiores visibles no acreditan un diseño de ejecución interior.
- No se añaden niveles de drenaje de cubierta, detalles constructivos o alturas de peldaños cuando faltan cotas. Las deducciones que sí se utilizan deben permanecer identificadas en el informe.
- El modelo y el GLB son instrumentos de revisión y visualización, no un levantamiento topográfico ni documentación de ejecución.

## Renders V2

Los renders V2 deben proceder del **mismo `.blend` reconstruido y aprobado por el control V2**, sin regenerar geometría entre cámaras. Los diez PNG antiguos de V1 no se reutilizan ni se presentan como vistas del trastero nuevo.

Después de superar ese control, el flujo de renders utiliza `modelo/renderizar.py`. Una prueba nueva de cámara puede producirse con:

```bash
blender -b Calle_Macarena_modelo_1a1.blend --python-exit-code 1 \
  --python modelo/renderizar.py -- \
  --ids 01 --preview --width 2500 --samples 96
```

La primera imagen entregada usa 256 muestras adaptativas a 2.500 × 1.667 píxeles. Para ampliar la serie se puede usar 384 muestras de día y 512 de tarde, con Cycles, reflejos/transmisión físicos y salida PNG de 16 bits. La resolución mínima inicial es 2500 px en el lado largo. Debe medirse una cámara y revisar el resultado antes de iniciar la serie, porque el coste depende de la máquina y de los materiales visibles. El script de producción determina y registra sus parámetros efectivos.

## OIDN externo, cuando Blender carece del filtro integrado

El Blender del entorno cloud de origen requiere **Open Image Denoise 2.5.1 externo** para el filtrado CPU. El procedimiento usa belleza, albedo y normales en EXR lineal, con gestión de color AgX al generar el PNG. Se documenta en `../herramientas/OIDN_USO.md`; no utiliza desenfoque genérico.

Para preparar el binario oficial en Linux x86_64, desde la raíz V2:

```bash
set -euo pipefail
mkdir -p herramientas
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/RenderKit/oidn/releases/download/v2.5.1/oidn-2.5.1.x86_64.linux.tar.gz \
  -o herramientas/oidn-2.5.1.x86_64.linux.tar.gz
printf '%s\n' \
  '743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6  herramientas/oidn-2.5.1.x86_64.linux.tar.gz' \
  | sha256sum -c -
tar -xzf herramientas/oidn-2.5.1.x86_64.linux.tar.gz -C herramientas
```

Ejecutar la extracción y el filtro únicamente después de que coincida el SHA-256 oficial. Mantener la verificación TLS y no modificar el checksum para hacer pasar una descarga. El script `herramientas/denoise_exr.py` comprueba el archivo oficial antes de procesar los pases. En Windows/macOS se requiere el binario oficial correspondiente o un Blender con OIDN integrado; el paquete Linux anterior no es intercambiable.

No hace falta OIDN para abrir el `.blend`, inspeccionar el `.glb` o revisar geometría.

La entrega registra 189 comprobaciones geométricas superadas y una importación independiente del GLB sin cambios de dimensión. Las discrepancias documentales y los datos sin cota siguen identificados en el informe.

Para renderizar con F12 en una instalación habitual de Blender que incorpore OIDN, activar Render Properties → Sampling → Render → Denoise. El archivo del entorno cloud conserva el filtrado desactivado porque el flujo de entrega utiliza el filtro oficial externo.

El HDRI diurno activo está empaquetado en el modelo. El HDRI de tarde se incluye en `assets/hdri/` y se empaqueta al activar ese modo mediante el script. La exposición diurna final es +0,20 EV; cámara, transmisión y reflejos utilizan cielo físico y los objetos del propio modelo.
