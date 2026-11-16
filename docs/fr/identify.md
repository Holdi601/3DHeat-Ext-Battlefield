---
title: "Identifier un fichier : identify"
nav_order: 3
lang: "fr"
source: identify.md
source_hash: "29c92138c83c"
nav_exclude: true
search_exclude: true
---
# Identifier un fichier : `identify` {#identifying-a-file-identify}

```bash
heat3d-battlefield-maps identify <file>
```

indique si un fichier est une table des matières Frostbite (`.toc`) et ce qu'elle contient, en la
lisant plutôt qu'en regardant son nom. Une installation de Battlefield 6 en compte des centaines :
`Data\layout.toc`, la liste des paquets de l'installation, et dans `Data\Win32\` les tables de
superbundles, dont celles d'un niveau.

```text
layout.toc  (<n> bytes)
  Frostbite table of contents, signed
    tree begins at 556
    superbundles <n>
```

La deuxième ligne indique quel en-tête a le fichier (voir
[Frostbite](reader-frostbite.md#the-header-that-looks-encrypted-and-is-not)) ; puis soit le nombre de
ressources que listent ses sections binaires, soit, pour une table écrite en arbre, le nombre de
superbundles qu'elle nomme.

## Tout autre fichier {#anything-else}

Un fichier qui n'est pas une table Frostbite n'affiche rien sur la sortie, la ligne
`not a Battlefield file` sur la sortie d'erreur, et se termine avec 2. C'est sur cela que s'appuie la
commande `identify` de [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/fr/) : pour un
fichier que ses propres lecteurs ne connaissent pas, elle demande à chaque outil de jeu installé à son
tour, et celui qui se termine avec 0 a la réponse.

| Message | Code | Signification |
|---|---|---|
| (la description ci-dessus) | 0 | une table des matières Frostbite |
| `not a Battlefield file` | 2 | tout autre fichier |
| `no such file: <path>` | 2 | le chemin est faux |
| `needs 3DHeat GameFiles: ...` | 2 | voir [Avant de commencer](before-you-start.md) |
