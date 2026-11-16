---
title: "Avant de commencer"
nav_order: 1.5
lang: "fr"
source: before-you-start.md
source_hash: "f55c65c6279e"
nav_exclude: true
search_exclude: true
---
# Avant de commencer {#before-you-start}

Vous débutez avec la ligne de commande ? Cette page vous mène de rien à un premier lancement.
Cela prend une quinzaine de minutes, une seule fois.

## 1. Installer Python {#install-python}

Cet outil demande **Python 3.10 ou plus récent**.

- **Windows :** téléchargez Python sur [python.org/downloads](https://www.python.org/downloads/)
  et lancez l'installateur. Sur son premier écran, cochez **Add python.exe to PATH**
  (ou « Ajouter python.exe au PATH » selon la langue de l'installateur), puis cliquez sur
  **Install Now** (ou « Installer maintenant »).
- **macOS et Linux :** Python 3 est souvent déjà là. Là où ces pages écrivent
  `python`, tapez `python3`. (Battlefield 6 tourne sous Windows ; l'outil lit ses fichiers
  où qu'ils soient.)

## 2. Obtenir cet outil {#get-this-tool}

Ouvrez [github.com/Holdi601/3DHeat-Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield),
cliquez sur le bouton vert **Code**, puis **Download ZIP** (« Télécharger le ZIP »), et décompressez
l'archive dans un dossier de votre choix. Si vous utilisez git : `git clone https://github.com/Holdi601/3DHeat-Ext-Battlefield`.

## 3. 3DHeat GameFiles est fourni avec {#dheat-gamefiles-comes-with-it}

L'outil lit avec [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/)
(son écrivain glTF, la recherche dans les bibliothèques Steam, le chargeur Oodle). L'étape 5 l'installe
pour vous. Sans pip — un dossier téléchargé que vous lancez sur place —, placez GameFiles à côté de cet
outil sous le nom `3DHeat-GameFiles`, ou définissez `HEAT3D_GAMEFILES` vers son dossier ; dans un dépôt
3DHeat (`exporters/ext/battlefield-maps`), il est trouvé tout seul dans `exporters/gamefiles`.

## 4. Ouvrir un terminal dans ce dossier {#open-a-terminal-in-that-folder}

Un terminal est une fenêtre où vous tapez des commandes.

- **Windows :** ouvrez le dossier dans l'Explorateur, cliquez dans la barre d'adresse, tapez
  `powershell` et appuyez sur Entrée. Une fenêtre bleue ou noire s'ouvre, déjà dans ce dossier.
- **macOS :** ouvrez **Terminal**, tapez `cd ` (avec un espace), faites glisser le dossier dans la
  fenêtre et appuyez sur Entrée.

`cd` veut dire « changer de dossier » : `cd C:\Tools\3DHeat-Ext-Battlefield` va dans ce dossier.

## 5. Installer l'outil {#install-the-tool}

Tapez ceci et appuyez sur Entrée :

```bash
python -m pip install -e .
```

Vous devriez voir, à la fin : `Successfully installed heat3d-ext-battlefield-...`
(et `heat3d-gamefiles-...` avec lui).

## 6. Lancer l'outil {#run-it}

```bash
heat3d-battlefield-maps levels
```

Vous devriez voir quelque chose comme :

```text
<n> levels in D:\Games\Steam\steamapps\common\Battlefield 6
  <level>                                    <size>  Data
  ...
```

Suite : [Niveaux Battlefield 6](level-battlefield.md).

## Comment lire les commandes de ces pages {#how-to-read-the-commands-on-these-pages}

| Vous voyez | Cela veut dire |
|---|---|
| `<level>` | un espace réservé : tapez votre propre valeur à la place, sans les `< >` |
| `[--textures [PIXELS]]` | facultatif : laissez-le de côté, ou tapez-le comme indiqué |
| `# a note` | un commentaire pour vous : ne le tapez pas |
| `"C:\My Files\x"` | mettez entre guillemets un chemin qui contient des espaces |

## En cas de problème {#when-something-goes-wrong}

| Le message | Que faire |
|---|---|
| `'python' is not recognized` | Python n'est pas installé, ou la case PATH n'était pas cochée : installez-le à nouveau et cochez-la (ou tapez `py` au lieu de `python`). |
| `'heat3d-battlefield-maps' is not recognized` | Relancez l'étape 5 dans le dossier de l'outil, ou tapez `python -m heat3d_ext_battlefield` au lieu de `heat3d-battlefield-maps` : cela fait la même chose. |
| `needs 3DHeat GameFiles: ...` | L'étape 5 ne l'a pas installé, ou vous lancez le dossier sur place : voir l'étape 3. |
| `no Frostbite game found in ...` | Installez le jeu, ou donnez son dossier : `--install "D:\Games\Battlefield 6"`. |
| `no Oodle library found` | Certaines données sont compressées en Oodle ; le jeu livre la bibliothèque (`oo2core_*.dll`) qui les décode. Définissez `HEAT3D_OODLE` vers ce fichier (voir [Oodle](https://holdi601.github.io/3DHeat-GameFiles/fr/reader-oodle.html)). |
| tout le reste | Lisez la dernière ligne du message, puis ouvrez un ticket (issue) sur GitHub avec cette ligne. |

Chaque commande se termine aussi par un **code de sortie** : 0 veut dire que cela a marché, 2 que
le jeu, le fichier ou GameFiles n'a pas été trouvé, 1 que la lecture a échoué. Pour le voir, tapez
`echo $LASTEXITCODE` dans PowerShell, ou `echo $?` sous macOS et Linux.
