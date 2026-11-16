---
title: "Condiciones y licencias"
nav_order: 8
lang: "es"
source: terms.md
source_hash: "81e5e54e5585"
nav_exclude: true
search_exclude: true
---
# Condiciones y licencias {#terms-and-licence}

Esta página es un registro de lo que dicen las licencias, no asesoramiento jurídico.

## El juego de EA {#ea-s-game}

Battlefield 6 y sus niveles pertenecen a Electronic Arts, que no respalda este proyecto. Esta herramienta no incluye nada del juego ni descarga nada: lee
los archivos de la copia que **tú** instalaste, en tu equipo, fuera del juego. No cambia nada en el juego, no se ejecuta junto a él y no se comunica con ningún servidor.

Lo que le indiques sigue siendo tu responsabilidad. Los juegos tienen sus propias condiciones de licencia, y los contratos de licencia de usuario final (EULA) suelen prohibir la ingeniería inversa. Son contratos exigibles, y la obligación recae en quien ejecuta la herramienta. Usarla es tu decisión, bajo las condiciones que aceptaste para el juego y la tienda donde lo compraste (el Acuerdo de Usuario de EA, y el de Steam, el de la aplicación de EA o el de Epic).

El nivel que escribe es contenido de la empresa editora del juego: guarda los `.glb` exportados, y las texturas que contienen,
para tu propio análisis. No publiques, compartas ni vendas los niveles, modelos ni texturas exportados. El `.gitignore` del repositorio mantiene los archivos del juego y las exportaciones fuera del control de versiones, por tipo de archivo.

Por eso es un paquete aparte: si EA alguna vez pide que se retire, se retira solo, y el visor, GameFiles y las demás herramientas se quedan.

## Nada cifrado se abre {#nothing-encrypted-is-opened}

- **Sin claves: ninguna incluida, ninguna recuperada.** Nada busca una clave dentro de un ejecutable, y nada lee la memoria de otro proceso.
- **La ofuscación tampoco está implementada.** Las tablas de Frostbite ofuscadas con XOR guardan su clave en el propio archivo, así que son ofuscación y no un control de acceso. Aun así se detectan y se rechazan, porque ningún archivo disponible usa esa forma y no habría nada con que comprobar una implementación.
- **Los archivos cifrados siguen cerrados.** El sistema de archivos inicial de Battlefield 6, que guarda la biblioteca de tipos del juego, está cifrado y no se lee. La exportación del nivel trabaja con los archivos que no están cifrados, y construye los dos tipos que necesita a partir de los datos.
- **Nada se inyecta en el proceso de un juego.** Inyectar código en un título con sistema anticheat pone en riesgo la cuenta de quien lo ejecuta.

## Oodle se encuentra, no se incluye {#oodle-is-found-not-bundled}

Parte de los datos del juego están comprimidos con Oodle. Oodle (RAD Game Tools, ahora Epic)
es propietario y no tiene una versión redistribuible. `oo2core_*.dll` está licenciado al producto que lo incluye.
Por eso esta herramienta nunca lo incluye: `oodle.py` de 3DHeat GameFiles carga una biblioteca que ya está en la máquina (la que trae el juego, o la copia a la que apunta `HEAT3D_OODLE`) en lugar de llevar una propia. Mira [Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html).

## El formato en sí {#the-format-itself}

Los `.toc`, paquetes, particiones EBX, MeshSet y el terreno de Frostbite no están documentados. Leerlos es ingeniería inversa de un contenedor. Los lectores de aquí se diseñaron a partir de los propios archivos de Battlefield 6. Las descripciones públicas de versiones anteriores de Frostbite (las herramientas de modding Frosty, una nota de formato de Need for Speed Heat, una charla de GDC) aportaron nombres de campos y un mapa de lo que buscar. No se tomó código de ninguna de ellas; cada desplazamiento se midió en los archivos (las fuentes y sus licencias están en
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md)).

## Licencia y fuentes {#licence-and-sources}

MIT ([`LICENSE`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSE)): úsalo, cámbialo, distribúyelo, con fines comerciales o no. Se apoya en
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (MIT) y necesita
numpy (BSD-3-Clause), Pillow (MIT-CMU), lz4 y zstandard (BSD-3-Clause); las pruebas necesitan pytest (MIT). Mira
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md).
