# Materiales y luz para la revisión V2

Esta revisión modifica únicamente acabados y parámetros de iluminación. Conserva la API `make_materials()` / `setup_lighting(scene, mode)` y todas las claves V1. No cambia la parcela, huecos, volúmenes, cámaras ni posiciones de luminarias. V1 permanece separado.

## Materiales

| Acabado | Parámetros de V2 | Fuente |
|---|---|---|
| Fachada y cerramientos blancos | Albedo lineal ≈0,75–0,78, casi neutro; roughness variable 0,63–0,82; grano de 0,75 mm y poro de 0,15 mm mediante normal bump, sin desplazar vértices | Shader procedural original; elección de acabado solicitada |
| Carpinterías antracita | Aluminio lacado: capa opaca dieléctrica, no aluminio desnudo; roughness 0,29, micrograno de pintura 45 μm, clearcoat tenue | Shader procedural original |
| Vidrio arquitectónico | Color blanco neutro (1,1,1); transmisión 1; IOR 1,45; roughness 0,009. Sin tinte de color ni absorción beige | Shader físico; el grosor de representación existente no se modifica |
| Solería exterior | **Porcelánico crema claro, paso exacto X/Y 0,90 × 0,90 m; juntas de 3 mm**; relieve visual de junta 1,35 mm, micrograno 0,18 mm, ligera variación de cada baldosa y roughness 0,40–0,58 | Preferencia de acabado. Shader matemático por módulo en metros; no cambia la huella de pavimentos |
| Madera entre cristaleras | Roble claro; veta orientada **Z vertical**; poro 0,35 mm y acabado mate/satinado. Se aplica a los paños ya existentes, sin alterar huecos ni espesor | Shader procedural original; preferencia decorativa |
| Césped artificial | Polímero verde con microvariación de milímetros, sin manchas grandes; microrelieve 3,5 mm, IOR 1,49, sheen leve. Material separado `cesped_fibra` para fibras geométricas opcionales en el mismo jardín | Preferencia expresa de acabado artificial; fibras gestionadas por módulo de vegetación |
| Tapizado | Lino beige neutro; trama tridimensional fina y sheen textil. `tejido_tapizado` / alias `tejido` | Shader procedural original |
| Sábanas | Algodón blanco roto con trama de 0,13 mm, roughness 0,89 | Shader procedural original |
| Piel clara | Albedo neutro, poros de 0,25 mm, roughness 0,50 | Shader procedural original |
| Madera/metal de mobiliario | `madera_mesa`: roble con veta X; `madera_patas`: veta Z; `metal_mobiliario`: negro satinado | Shaders procedurales originales |

Los tamaños de textura son parámetros de visualización. Los valores de bump no constituyen alturas constructivas nuevas. No se presentan los materiales procedurales como texturas fotográficas descargadas.

La dominante cálida de los interiores de V1 también provenía de luminarias con RGB `(1.00, 0.72, 0.46)`, no únicamente del vidrio. V2 mantiene esas luminarias en la misma ubicación: de día usa el 18% de su potencia base y color casi neutro `(1.00, 0.94, 0.86)`; de tarde restituye la potencia base y una luz cálida moderada. Las luminarias exteriores se apagan en fotografías de día y se activan de tarde. Todo ello es iluminación de visualización.

## Recursos fotográficos externos y licencia

Se han obtenido dos HDRIs Radiance fotográficos de 1024 × 512 px y se empaquetan automáticamente con `image.pack()` en Blender:

| Recurso | Original | Espejo público utilizado | Licencia |
|---|---|---|---|
| Royal Esplanade | https://polyhaven.com/a/royal_esplanade | https://raw.githubusercontent.com/mrdoob/three.js/r160/examples/textures/equirectangular/royal_esplanade_1k.hdr | CC0 1.0 |
| Venice Sunset | https://polyhaven.com/a/venice_sunset | https://raw.githubusercontent.com/mrdoob/three.js/r160/examples/textures/equirectangular/venice_sunset_1k.hdr | CC0 1.0 |

Licencia contrastada con el texto oficial de Poly Haven en https://raw.githubusercontent.com/Poly-Haven/polyhaven.com/master/public/locales/en/license.json: “Our assets are all licensed as CC0, which is effectively Public Domain.” El archivo original de ese texto se conserva en `assets/licencias/polyhaven_cc0_texto_oficial.json`; tamaño, fuente y SHA-256 de los HDRIs están en `assets/licencias/recursos_materiales_v2.json`.

Los dominios `api.polyhaven.com`, `polyhaven.com` y `dl.polyhaven.org` devolvieron HTTP 403 del proxy de esta ejecución. Se descargaron las copias públicas anteriores de GitHub con verificación TLS normal. No se desactivó ninguna verificación. Ambos HDRIs se han abierto correctamente en Blender 4.3.2, con radiancia lineal máxima 49.664 y 6.496 respectivamente: son datos de alto rango dinámico, no imágenes LDR renombradas.

No se incorporan texturas PBR de terceros cuya licencia no se haya podido verificar. Los acabados de superficies son procedurales originales y no necesitan conexión de red durante la construcción o el render.

## Iluminación y fotografía

El relleno y las reflexiones utilizan el HDRI real; su disco solar se limita en esa capa para evitar duplicarlo con la lámpara Sun. Un cielo físico Nishita se muestra a los rayos de cámara y de transmisión, por lo que no aparece la arquitectura del emplazamiento fotografiado como fondo. Las reflexiones del HDRI son una referencia ambiental para iluminación, no una reconstrucción de las parcelas vecinas ni prueba del entorno real de Cádiz.

El sol de día tiene elevación 43°, tamaño angular 0,53° y fuerza 3; de tarde 5,5°, tamaño 0,62° y fuerza 1,05. La rotación y elevación de la iluminación son decisiones fotográficas, porque no se ha confirmado norte geográfico ni una fecha de estudio solar. No se declara una simulación solar geolocalizada.

Exposición AgX natural: −0,15 EV de día y +0,25 EV de tarde, contraste Medium High, sin filtros pictóricos. Se conservan reflejos Fresnel, sombras físicas y transmisión real. El HDRI queda empaquetado; si falta el archivo externo y existe la copia empaquetada, se reutiliza esta. Si ambos faltan, el módulo tiene fallback local Nishita.

La configuración de calidad propuesta es Cycles CPU, **384 muestras de día / 512 de tarde**, muestreo adaptativo 0,008, 14 rebotes totales, 5 difusos, 6 brillantes y 12 de transmisión. Se exporta PNG de 16 bits. Para pruebas de encuadre puede reducirse temporalmente a 64–96 muestras; debe medirse una cámara antes de estimar el coste de la serie completa. El denoise requiere el flujo OIDN ya validado si la compilación de Cycles carece del denoiser integrado.

Estas configuraciones aumentan el detalle físico y la consistencia de materiales; el juicio de realismo debe comprobarse mediante renders V2 y no se da por validado solo por cargar los shaders.

## Validación ejecutada

Se ha probado la construcción de materiales y la alternancia día/tarde con Blender 4.3.2 sin guardar o modificar el archivo de arquitectura y sin ejecutar la serie de renders. Se comprobó el vidrio neutro, el paso 0,90 m de solería, la junta 0,003 m y el empaquetado de ambos HDRIs. Los agentes de mobiliario y vegetación disponen de las claves adicionales. No se han editado sus módulos.

Ajuste de la entrega final: exposición diurna +0,20 EV. El HDRI queda reservado al relleno difuso; los reflejos muestran el cielo físico y los objetos del modelo. Se evita introducir la arquitectura de la panorámica de iluminación como si perteneciera al emplazamiento. La imagen inicial entregada usa 256 muestras adaptativas y 2500 × 1667 px.
