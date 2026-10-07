# Texturas fotográficas V3

Mapas ambientCG de Lennart Demes, CC0, procedentes del espejo público Papyszoo/CC0-Public-Domain-Textures fijado al commit fcc4ff97a5a843dc2e242ec9e195389bc46ed7d2. Se conservan los mapas originales KTX2 y los PNG decodificados sin remuestreo a 512 × 512 px. Colores sRGB; altura/rugosidad/normal como datos lineales. Procedencia, roles y SHA256 en `../licencias/texturas_fotograficas_v3.json`; licencia en `../licencias/ambientcg_mirror_CC0.txt`.

Conversión: KTX-Software oficial 4.4.2, `ktx extract --transcode rgba8 archivo.ktx2 archivo.png`. Herramienta de conversión temporal; el proyecto y los renders usan PNG empaquetados y no necesitan instalar KTX.

Se utilizan Wood058 (veta madera), Fabric040 (estructura de lino, retintada a los colores elegidos), Plaster001 (estuco blanco) y Marble015 (estructura mineral fina retintada a porcelánico crema/cuazo). Wood046 y las normales se conservan como variantes PBR disponibles. Las texturas describen acabados, sin cambiar geometría ni superficies del plano.

Fachada madera: veta vertical Z, juntas solo de sombreado cada 0,12 m (1,6 mm). Porcelánico exterior: módulo exacto 0,90 × 0,90 m y junta 3 mm, independiente de la estructura fotográfica. Lino: repetición 0,16 m y microrelieve de normal 0,22 mm. Césped artificial conserva su superficie/microfibras V2. Agua: únicamente plano de superficie, ondas de normal 1,1 mm + 0,16 mm, sin afirmar profundidad ni construir fondo.

Luz de día: altura solar visual 28°, rotación 105° en coordenadas de escena, en sentido horario desde +Y. Nishita y Sun explícito comparten la misma dirección (+X, −Y). La luz baja de mañana entra por debajo del porche y permite leer el interior sin modificar la arquitectura; no es un estudio solar georreferenciado.

Vidrio: cámara/reflexión/refracción usan Principled transparente, IOR 1,52 y rugosidad 0,006. Para la prueba de sombra solar directa (Is Shadow Ray) se aplica transmisión recta neutra 0,96 por cara: 0,9216 para las dos caras de la placa. Es una aproximación radiativa de vidrio claro de caras paralelas que permite recibir luz solar física sin caústicas refractivas costosas; no añade luces ni cambia ventanas. Esta transmitancia es una hipótesis material de visualización, no un producto de vidrio especificado en el PDF.
