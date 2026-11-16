---
title: "Identificar un archivo: identify"
nav_order: 3
lang: "es"
source: identify.md
source_hash: "29c92138c83c"
nav_exclude: true
search_exclude: true
---
# Identificar un archivo: `identify` {#identifying-a-file-identify}

```bash
heat3d-battlefield-maps identify <file>
```

indica si un archivo es una tabla de contenido de Frostbite (`.toc`) y qué contiene, leyéndolo en lugar de fijarse en su nombre. Una instalación de Battlefield 6 tiene cientos de ellas: `Data\layout.toc`, la lista de paquetes de la instalación, y bajo `Data\Win32\` las tablas de superpaquetes, entre ellas las de un nivel.

```text
layout.toc  (<n> bytes)
  Frostbite table of contents, signed
    tree begins at 556
    superbundles <n>
```

La segunda línea dice qué cabecera tiene el archivo (mira [Frostbite](reader-frostbite.md#the-header-that-looks-encrypted-and-is-not));
luego, o bien el número de activos que listan sus secciones binarias, o, en una tabla escrita como árbol, el número de superpaquetes que nombra.

## Cualquier otra cosa {#anything-else}

Un archivo que no es una tabla de Frostbite no imprime nada en la salida estándar, imprime la línea
`not a Battlefield file` en la salida de error y termina con 2. Eso es lo que usa el propio
`identify` de [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/): para un archivo que sus propios lectores no conocen,
pregunta a cada herramienta de juego instalada por turnos, y la que termina con 0 tiene la respuesta.

| Mensaje | Salida | Significado |
|---|---|---|
| (la descripción de arriba) | 0 | una tabla de contenido de Frostbite |
| `not a Battlefield file` | 2 | cualquier otro archivo |
| `no such file: <path>` | 2 | la ruta es incorrecta |
| `needs 3DHeat GameFiles: ...` | 2 | mira [Antes de empezar](before-you-start.md) |
