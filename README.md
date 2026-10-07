# Calle Macarena · interiores y exteriores · V3

Siete vistas nuevas de la misma vivienda: salón, cocina, comedor, terraza, piscina, aparcamiento descubierto y comedor exterior de terraza. La geometría conserva el plano definitivo con trastero y las alturas confirmadas por el usuario.

- [Galería PDF](entrega/galeria_renders.pdf)
- [Galería local con imágenes completas](entrega/galeria.html)
- [Modelo Blender editable](Calle_Macarena_modelo_1a1.blend)
- [Modelo GLB](Calle_Macarena_modelo_1a1.glb)
- [Comparación con los planos y control de alturas](control/informe_revision_v3.pdf)
- [Tabla de dimensiones](tabla_dimensiones_modeladas.csv)
- [Descargar toda la revisión en ZIP](https://github.com/juanmaesp8-svg/Calle-Macarena/archive/refs/heads/codex/renders-v3-interiores-exteriores.zip)

Descarga y extrae el ZIP. Abre `Calle_Macarena_modelo_1a1.blend` en Blender 4.3.2 o compatible. El archivo incluye las texturas empaquetadas y permite editar los objetos y cámaras. El GLB se abre en un visor glTF o se importa en Blender con **File → Import → glTF**; conserva la geometría y materiales simplificados. La galería PDF y las imágenes PNG/JPG se abren directamente. Si estás leyendo este manual desde la portada del repositorio, los archivos de la galería están en la carpeta `entrega`.

La revisión mejora los materiales PBR, el mobiliario y los detalles de la cocina, los tejidos, la vegetación y la iluminación. El exterior mantiene blanco, carpinterías oscuras, madera clara vertical entre cristaleras, césped artificial y porcelánico crema claro con módulo de 90 × 90 cm. Las elecciones de acabados interiores, accesorios, especies vegetales y alturas de muebles son decoración para visualizar, no datos constructivos atribuidos a los planos. Las sillas incluyen la porción que sus símbolos ocultan bajo las mesas sin desplazar su borde visible exterior.

Las comprobaciones geométricas cotejan la planta, las fachadas y las secciones. Una comparación adicional verifica todos los vértices y caras de los 346 objetos arquitectónicos frente al modelo V2 validado. Cada imagen registra el mismo SHA256 del `.blend`, la cámara y los parámetros de Cycles. Las discrepancias documentales quedan en `control/control_resultado.json`; la piscina conserva su contorno y una representación superficial, porque no hay cotas de profundidad. Los fondos de calles son contexto gráfico y no definen anchuras ni parcelas vecinas.

Para reconstruir en Linux, instala Blender 4.3.2 o compatible y ejecuta `bash entrega/setup_entorno_v2.sh`. Antes de calcular nuevas imágenes, instala OIDN siguiendo `herramientas/OIDN_USO.md`. Los datos dimensionales y las mallas preparadas están incluidos, por lo que la reconstrucción visual no necesita trazar los PDFs de nuevo:

```bash
blender -b --factory-startup --python-exit-code 1 --python modelo/construir_modelo.py
.venv/bin/python control/verificar_revision_v2.py
blender -b Calle_Macarena_modelo_1a1.blend --python-exit-code 1 --python control/verificar_revision_visual_v3.py
.venv/bin/python control/verificar_huecos_mesh_v2.py
blender -b Calle_Macarena_modelo_1a1.blend --python-exit-code 1 --python modelo/renderizar.py -- --ids I01,I02,I03,E01,E02,E03,E04 --width 2500 --samples 64 --threshold 0.02
```

El denoising usa Intel Open Image Denoise oficial, con pases lineales de color, albedo y normales. La instalación y el hash del archivo oficial están en `herramientas/denoise_exr.py` y en el manual de herramientas. Los binarios y los buffers temporales se regeneran; la entrega contiene las imágenes finales completas. Las licencias y procedencia de los recursos están en `assets/licencias`.

Las revisiones anteriores siguen disponibles en sus ramas: `codex/descarga-galeria-renders` (V1) y `codex/modelo-v2-trastero` (V2).
