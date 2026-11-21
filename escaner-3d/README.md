# Escáner 3D de Objetos

Página web que convierte un objeto en un modelo 3D usando la cámara.

**Cómo funciona:** el objeto gira una vuelta frente a la cámara quieta. En cada toma se recorta su silueta,
y con todas las siluetas se talla un volumen (técnica *visual hull*). Luego se arma la superficie y se pinta
con el color de las tomas. Todo corre en el navegador, nada se sube a ningún servidor.

## Uso
1. Abre `index.html` en Chrome (o la versión publicada en claude.ai).
2. Captura: cámara en vivo (captura primero el fondo vacío), graba un video desde el teléfono o sube un video / fotos en orden.
3. Ajusta la sensibilidad hasta que solo el objeto quede en rojo.
4. Pulsa **Generar 3D**, pon la altura real en cm y descarga el `.zip` con `modelo.obj` (con color) y `modelo.stl` (impresión 3D).

## Límites
- Las partes hundidas (el interior de una taza) quedan rellenas: el método solo ve contornos.
- Objetos brillantes, transparentes o del mismo color que el fondo salen mal.
- Si el modelo sale espejado o retorcido, marca "Giró a la izquierda".
