---
title: "Mantener estos documentos"
nav_order: 91
lang: "es"
source: maintaining.md
source_hash: "6c87ae3635d6"
nav_exclude: true
search_exclude: true
---
# Mantener estos documentos {#maintaining-these-docs}

Una lista de comprobación para cada versión, para que las páginas nunca se queden atrás respecto al código.

1. **Regenerar la referencia.** `python tools/gen_docs_reference.py` reescribe
   [Referencia de comandos](../cli-reference.md) a partir del propio `--help` del programa y de sus columnas de salida. `python tools/gen_docs_reference.py --check` termina con 1 cuando la página guardada está desactualizada.
2. **Listar lo que cambió.** `git log v<VERSION>..HEAD --oneline`, donde
   `<VERSION>` es la última versión publicada (el archivo `VERSION` en la publicación). Dale a cada nueva función, opción y columna de salida un lugar en una página, y una fila en la sección **Docs** de [`CHANGELOG.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/CHANGELOG.md).
3. **Revisión independiente.** Alguien que no escribió las páginas lee el
   README y cada página cambiada, con las imágenes incluidas, tres veces: como principiante que nunca ha usado una terminal, como niño de 8 años, y como experto que comprueba cada opción contra `--help`. Los ejemplos usan solo nombres y números inventados.
4. **Corregir** todo lo que encuentre la revisión.
5. **Traducciones.** Cada página traducida registra el hash de la página en inglés de la que se hizo. Vuelve a traducir las páginas cuyo original en inglés cambió,
   y luego revisa cada idioma: texto claro, etiquetas correctas en los diagramas y las mismas palabras que la interfaz traducida del visor de 3DHeat.
6. **Ejecutar las pruebas** (`pytest`).
7. **Subir los cambios** (push) solo con el visto bueno del propietario.

## Traducciones: los comandos {#translations-the-commands}

El sitio se traducirá a los 40 idiomas del visor de 3DHeat (hasta ahora: las dos páginas que venían de
3DHeat GameFiles, en 18 idiomas): el inglés está en
`docs/`, cada otro idioma en `docs/<lang>/` con los mismos nombres de archivo. `tools/docs_i18n.py` lleva la contabilidad:

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Traduce solo lo que lista `todo`: mantén el Markdown, los enlaces, el código y los nombres de archivos y columnas tal cual,
traduce los títulos y las descripciones de las imágenes, y usa las propias palabras del visor de 3DHeat para sus botones
y paneles (su `src/i18n/locales/<lang>/`). Las páginas de referencia generadas y las imágenes de terminal se quedan en inglés. En el sitio, una traducción desactualizada lo dice y enlaza la página en inglés; una que falta usa el inglés. El menú de idiomas del encabezado y la redirección de la página de inicio según el idioma del navegador vienen de `docs/_includes/`.

## Las imágenes {#the-pictures}

`docs/assets/img/level-steps.svg` lo dibujó `tools/docs_diagrams.py` de 3DHeat GameFiles
cuando estas páginas formaban parte de GameFiles. Cámbialo a mano (es SVG plano), luego ejecuta
`svg-strings`, traduce las nuevas etiquetas en `docs/assets/i18n/svg/<lang>.json` y ejecuta `svg-build`.
