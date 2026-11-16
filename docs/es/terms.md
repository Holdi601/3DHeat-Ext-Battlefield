---
title: "Condiciones y licencias"
nav_order: 8
lang: "es"
source: terms.md
source_hash: "50d8b31139d6"
nav_exclude: true
search_exclude: true
---
# Condiciones y licencias {#terms-and-licence}

## El juego de EA {#ea-s-game}

Battlefield 6 y sus niveles pertenecen a Electronic Arts. 3DHeat Battlefield no está afiliado a Electronic Arts ni cuenta con su respaldo. Battlefield y los nombres y marcas relacionados pertenecen a sus titulares.

Esta herramienta no incluye nada del juego ni descarga nada: ni recursos del juego, ni código del juego, ni DLL. Lee
los archivos de la copia que **tú** instalaste, en tu equipo, fuera del juego. No cambia nada en el juego, no se ejecuta junto a él y no se comunica con ningún servidor.

El nivel que escribe se queda en tu equipo: guarda los `.glb` exportados, y las texturas que contienen,
para tu propio análisis, y no publiques, compartas ni vendas los niveles, modelos ni texturas exportados. El `.gitignore` del repositorio mantiene los archivos del juego y las exportaciones fuera del control de versiones, por tipo de archivo.

Cada lector de juego es un pequeño proyecto propio, con su propio archivo de licencia, sus propias versiones y su propio gestor de incidencias, de modo que puede instalarse, actualizarse, mantenerse - o retirarse a petición de un titular de derechos - por separado, sin afectar al visor ni a las demás herramientas.

Titulares de derechos: abran una incidencia en [github.com/Holdi601/3DHeat-Ext-Battlefield/issues](https://github.com/Holdi601/3DHeat-Ext-Battlefield/issues); respondemos rápido y retiramos lo que se nos pida.

## Nada cifrado se abre {#nothing-encrypted-is-opened}

- **Sin claves: ninguna incluida, ninguna recuperada.** Nada busca una clave dentro de un ejecutable, y nada lee la memoria de otro proceso.
- **La ofuscación tampoco está implementada.** Las tablas de Frostbite ofuscadas con XOR se detectan y se rechazan: ningún archivo disponible usa esa forma y no habría nada con que comprobar una implementación.
- **Los archivos cifrados siguen cerrados.** El sistema de archivos inicial de Battlefield 6, que guarda la biblioteca de tipos del juego, está cifrado y no se lee. La exportación del nivel trabaja con los archivos que no están cifrados, y construye los dos tipos que necesita a partir de los datos.
- **Nada se inyecta en el proceso de un juego.** La herramienta solo lee archivos del disco.

## Oodle se encuentra, no se incluye {#oodle-is-found-not-bundled}

Parte de los datos del juego están comprimidos con Oodle. Oodle (RAD Game Tools, ahora Epic)
es propietario y no tiene una versión redistribuible. `oo2core_*.dll` está licenciado al producto que lo incluye.
Por eso esta herramienta nunca lo incluye: `oodle.py` de 3DHeat GameFiles carga una biblioteca que ya está en la máquina (la que trae el juego, o la copia a la que apunta `HEAT3D_OODLE`) en lugar de llevar una propia. Mira [Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html).

## El formato en sí {#the-format-itself}

Los `.toc`, paquetes, particiones EBX, MeshSet y el terreno de Frostbite no están documentados. Los lectores de aquí se diseñaron a partir de los propios archivos de Battlefield 6. Las descripciones públicas de versiones anteriores de Frostbite (las herramientas de modding Frosty, una nota de formato de Need for Speed Heat, una charla de GDC) aportaron nombres de campos y un mapa de lo que buscar. No se tomó código de ninguna de ellas; cada desplazamiento se midió en los archivos (las fuentes y sus licencias están en
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md)).

## Licencia y fuentes {#licence-and-sources}

MIT ([`LICENSE`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSE)): úsalo, cámbialo, distribúyelo, con fines comerciales o no. Se apoya en
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (MIT) y necesita
numpy (BSD-3-Clause), Pillow (MIT-CMU), lz4 y zstandard (BSD-3-Clause); las pruebas necesitan pytest (MIT). Mira
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md).
