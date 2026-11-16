---
title: "Antes de empezar"
nav_order: 1.5
lang: "es"
source: before-you-start.md
source_hash: "f55c65c6279e"
nav_exclude: true
search_exclude: true
---
# Antes de empezar {#before-you-start}

¿Nunca has usado la línea de comandos? Esta página te lleva de cero a una primera ejecución.
Tarda unos quince minutos, una sola vez.

## 1. Instalar Python {#install-python}

Esta herramienta necesita **Python 3.10 o posterior**.

- **Windows:** descarga Python desde [python.org/downloads](https://www.python.org/downloads/)
  y ejecuta el instalador. En su primera pantalla, marca **Add python.exe to PATH**
  y luego haz clic en **Install Now**.
- **macOS y Linux:** Python 3 suele estar ya instalado. Donde estas páginas dicen
  `python`, escribe `python3`. (Battlefield 6 se ejecuta en Windows; la herramienta
  lee sus archivos estén donde estén.)

## 2. Obtener esta herramienta {#get-this-tool}

Abre [github.com/Holdi601/3DHeat-Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield), haz clic en el botón verde
**Code** y luego en **Download ZIP**, y descomprímelo en una carpeta de tu elección. Si usas git:
`git clone https://github.com/Holdi601/3DHeat-Ext-Battlefield`.

## 3. 3DHeat GameFiles viene incluido {#dheat-gamefiles-comes-with-it}

La herramienta lee con [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/)
(su escritor glTF, la búsqueda de bibliotecas de Steam, el cargador de Oodle). El paso 5 lo
instala por ti. Sin pip (una carpeta descargada que ejecutas en su sitio), pon GameFiles
junto a esta herramienta como `3DHeat-GameFiles`, o define `HEAT3D_GAMEFILES` con su
carpeta; dentro de un clon de 3DHeat (`exporters/ext/battlefield-maps`) se encuentra
en `exporters/gamefiles` por sí solo.

## 4. Abrir una terminal en esa carpeta {#open-a-terminal-in-that-folder}

Una terminal es una ventana donde escribes comandos.

- **Windows:** abre la carpeta en el Explorador, haz clic en la barra de direcciones, escribe
  `powershell` y pulsa Intro. Se abre una ventana azul o negra, ya en esa carpeta.
- **macOS:** abre **Terminal**, escribe `cd ` (con un espacio), arrastra la carpeta a
  la ventana y pulsa Intro.

`cd` significa "cambiar de carpeta": `cd C:\Tools\3DHeat-Ext-Battlefield` va a esa carpeta.

## 5. Instalar la herramienta {#install-the-tool}

Escribe esto y pulsa Intro:

```bash
python -m pip install -e .
```

Al final deberías ver: `Successfully installed heat3d-ext-battlefield-...`
(y `heat3d-gamefiles-...` con él).

## 6. Ejecutarla {#run-it}

```bash
heat3d-battlefield-maps levels
```

Deberías ver algo como:

```text
<n> levels in D:\Games\Steam\steamapps\common\Battlefield 6
  <level>                                    <size>  Data
  ...
```

Siguiente: [Niveles de Battlefield 6](level-battlefield.md).

## Cómo leer los comandos de estas páginas {#how-to-read-the-commands-on-these-pages}

| Ves | Significa |
|---|---|
| `<level>` | un marcador: escribe tu propio valor en su lugar, sin los `< >` |
| `[--textures [PIXELS]]` | opcional: déjalo fuera, o escríbelo tal como aparece |
| `# a note` | un comentario para ti: no lo escribas |
| `"C:\My Files\x"` | pon entre comillas una ruta que tiene espacios |

## Cuando algo sale mal {#when-something-goes-wrong}

| El mensaje | Qué hacer |
|---|---|
| `'python' is not recognized` | Python no está instalado, o no se marcó la casilla PATH: instálalo de nuevo y márcala (o escribe `py` en lugar de `python`). |
| `'heat3d-battlefield-maps' is not recognized` | Ejecuta el paso 5 otra vez en la carpeta de la herramienta, o escribe `python -m heat3d_ext_battlefield` en lugar de `heat3d-battlefield-maps`: hace lo mismo. |
| `needs 3DHeat GameFiles: ...` | El paso 5 no lo instaló, o ejecutas la carpeta en su sitio: mira el paso 3. |
| `no Frostbite game found in ...` | Instala el juego, o indica su carpeta: `--install "D:\Games\Battlefield 6"`. |
| `no Oodle library found` | Parte de los datos están comprimidos con Oodle; el juego trae la biblioteca (`oo2core_*.dll`) que los descomprime. Define `HEAT3D_OODLE` con ese archivo (mira [Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html)). |
| cualquier otro | Lee la última línea del mensaje y abre una incidencia en GitHub con ella. |

Cada comando también termina con un **código de salida**: 0 significa que funcionó, 2 que no se encontró
el juego, el archivo o GameFiles, y 1 que la lectura falló. Para verlo, escribe `echo $LASTEXITCODE` en PowerShell o `echo $?` en macOS y Linux.
