---
title: "Accueil"
nav_order: 1
lang: "fr"
source: index.md
source_hash: "33aebf769b1c"
nav_exclude: true
search_exclude: true
permalink: /fr/
---
# 3DHeat Battlefield {#dheat-battlefield}

**Qu'est-ce que c'est ?** Cet outil transforme un niveau de Battlefield 6, lu depuis **votre propre
installation**, en un niveau 3D — une maquette de la carte que vous pouvez survoler — pour le
visualiseur [3DHeat](https://github.com/Holdi601/3DHeat)
([documentation](https://holdi601.github.io/3DHeat/)) : le sol, chaque bâtiment, rocher, arbre et
clôture que le niveau place, sur demande avec leurs couleurs et les surfaces sur lesquelles les soldats
peuvent marcher.

**Pourquoi l'utiliser ?** Pour que la chaleur de vos parties de Battlefield 6 ait le sol et les
bâtiments dessous, dans les coordonnées du jeu : rien à placer ni à mettre à l'échelle dans le visualiseur.

**Exemple :** `heat3d-battlefield-maps level <level> -o level.glb` -> `level.glb`, quelques centaines
de Mo pour un niveau entier. (*Frostbite* est le moteur avec lequel Battlefield est fait.)

## Démarrage rapide {#quick-start}

Vous débutez avec la ligne de commande ? Lisez d'abord [Avant de commencer](before-you-start.md).
Il vous faut Python 3.10 ou plus récent, [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/)
(la bibliothèque avec laquelle cet outil lit) et Battlefield 6 installé. Lancez ces commandes dans le
dossier où vous avez cloné ou décompressé l'outil :

```bash
python -m pip install -e .                                  # installs heat3d-battlefield-maps, and GameFiles with it
heat3d-battlefield-maps levels                              # where the game is, and its levels
heat3d-battlefield-maps level <level> -o level.glb          # one level, flat colours
heat3d-battlefield-maps level <level> -o level.glb --textures --ground-texture   # with colour
```

`levels` commence par une ligne du type `<n> levels in D:\Games\Steam\steamapps\common\Battlefield 6`
et liste un niveau par ligne ; `level` se termine par `-> level.glb (<n> MB)`. Chargez ensuite
`level.glb` dans le panneau **Arrière-plan / niveau** du visualiseur
([charger un niveau](https://holdi601.github.io/3DHeat/levels.html)).

Le niveau est construit à partir des fichiers du jeu : il reste **sur votre machine**, pour le
regarder, et non pour le partager ou le publier ([Règles et licences](terms.md)).

Chaque lecteur de jeu est un petit projet à part, avec son propre fichier de licence, ses propres versions et son propre suivi des tickets : il peut être installé, mis à jour, maintenu - ou retiré à la demande d'un ayant droit - seul, sans toucher au visualiseur ni aux autres outils.

## Pages {#pages}

| Page | Ce qu'elle couvre |
|---|---|
| [Avant de commencer](before-you-start.md) | Python, GameFiles, un terminal, un premier lancement |
| [Niveaux Battlefield 6 : `levels` et `level`](level-battlefield.md) | lister les niveaux, chaque option d'un export, ses parties, les tailles à attendre |
| [Identifier un fichier : `identify`](identify.md) | si un fichier est une table des matières Frostbite, et ce qu'elle contient |
| [Frostbite](reader-frostbite.md) | comment les tables, bundles, maillages, terrains et textures sont lus, et comment chacun a été vérifié |
| [Règles et licences](terms.md) | le jeu d'EA, Oodle, les sources, un projet à part entière |
| [Commandes](../cli-reference.md) | chaque option, générée à partir du code |
| [Maintenance de ces docs](maintaining.md) | la liste de contrôle de chaque version |

## Liens connexes {#related}

- Le visualiseur 3DHeat : [github.com/Holdi601/3DHeat](https://github.com/Holdi601/3DHeat),
  documentation sur [holdi601.github.io/3DHeat](https://holdi601.github.io/3DHeat/).
- [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/) : les lecteurs du moteur et
  l'écrivain glTF sur lesquels cet outil s'appuie ; ses `levels`, `level` et `identify` lancent cet
  outil quand il est installé.

## Les outils 3DHeat {#the-3dheat-tools}

| Outil | Ce qu'il fait | Code | Docs |
|---|---|---|---|
| visualiseur 3DHeat | affiche les données : cartes de chaleur, analyse de course, revue de match | [3DHeat](https://github.com/Holdi601/3DHeat) | [docs](https://holdi601.github.io/3DHeat/) |
| GameFiles | niveaux et parcours tirés des fichiers propres à un jeu | [3DHeat-GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) | [docs](https://holdi601.github.io/3DHeat-GameFiles/) |
| GameCapture | télémétrie de tours, et niveaux reconstruits à partir de vidéos de jeu | [3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture) | [docs](https://holdi601.github.io/3DHeat-GameCapture/) |
| Unreal Exporter | un plugin pour l'éditeur Unreal : un niveau en un seul `.glb` | [3DHeat-UnrealExporter](https://github.com/Holdi601/3DHeat-UnrealExporter) | [docs](https://holdi601.github.io/3DHeat-UnrealExporter/) |
| CS2 | démos et cartes de Counter-Strike 2 | [3DHeat-CS2](https://github.com/Holdi601/3DHeat-CS2) | [docs](https://holdi601.github.io/3DHeat-CS2/) |
| Watcher | enregistre ce que les jeux publient pendant que vous jouez | [3DHeat-Watcher](https://github.com/Holdi601/3DHeat-Watcher) | [docs](https://holdi601.github.io/3DHeat-Watcher/) |
| Ext-WarThunder | replays de War Thunder | [3DHeat-Ext-WarThunder](https://github.com/Holdi601/3DHeat-Ext-WarThunder) | [docs](https://holdi601.github.io/3DHeat-Ext-WarThunder/) |
| Ext-WoT | replays de World of Tanks | [3DHeat-Ext-WoT](https://github.com/Holdi601/3DHeat-Ext-WoT) | [docs](https://holdi601.github.io/3DHeat-Ext-WoT/) |
| Ext-WoWs | replays de World of Warships | [3DHeat-Ext-WoWs](https://github.com/Holdi601/3DHeat-Ext-WoWs) | [docs](https://holdi601.github.io/3DHeat-Ext-WoWs/) |
| Ext-Squad | démos de serveur Squad | [3DHeat-Ext-Squad](https://github.com/Holdi601/3DHeat-Ext-Squad) | [docs](https://holdi601.github.io/3DHeat-Ext-Squad/) |
| Ext-DCS | cartes de DCS World en niveaux 3D | [3DHeat-Ext-DCS](https://github.com/Holdi601/3DHeat-Ext-DCS) | [docs](https://holdi601.github.io/3DHeat-Ext-DCS/) |
| Ext-IL2 | cartes d'IL-2 Sturmovik en niveaux 3D | [3DHeat-Ext-IL2](https://github.com/Holdi601/3DHeat-Ext-IL2) | [docs](https://holdi601.github.io/3DHeat-Ext-IL2/) |
| Ext-Dota | la carte de Dota 2 en niveau 3D | [3DHeat-Ext-Dota](https://github.com/Holdi601/3DHeat-Ext-Dota) | [docs](https://holdi601.github.io/3DHeat-Ext-Dota/) |
| Ext-DotaReplay | replays de Dota 2 en tables | [3DHeat-Ext-DotaReplay](https://github.com/Holdi601/3DHeat-Ext-DotaReplay) | [docs](https://holdi601.github.io/3DHeat-Ext-DotaReplay/) |
| Ext-Riot | replays de League of Legends et VALORANT | [3DHeat-Ext-Riot](https://github.com/Holdi601/3DHeat-Ext-Riot) | [docs](https://holdi601.github.io/3DHeat-Ext-Riot/) |
| Ext-Forza | parcours et voitures de Forza Horizon | [3DHeat-Ext-Forza](https://github.com/Holdi601/3DHeat-Ext-Forza) | [docs](https://holdi601.github.io/3DHeat-Ext-Forza/) |
| Ext-Battlefield | niveaux de Battlefield 6 en niveaux 3D | [3DHeat-Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield) | [docs](https://holdi601.github.io/3DHeat-Ext-Battlefield/) |
| Ext-BeamNG | parcours de BeamNG.drive autour de vos tours | [3DHeat-Ext-BeamNG](https://github.com/Holdi601/3DHeat-Ext-BeamNG) | [docs](https://holdi601.github.io/3DHeat-Ext-BeamNG/) |
| Ext-ACRally | étapes d'Assetto Corsa Rally autour de vos tours | [3DHeat-Ext-ACRally](https://github.com/Holdi601/3DHeat-Ext-ACRally) | [docs](https://holdi601.github.io/3DHeat-Ext-ACRally/) |
| Ext-Reforger | mondes d'Arma Reforger en niveaux 3D | [3DHeat-Ext-Reforger](https://github.com/Holdi601/3DHeat-Ext-Reforger) | [docs](https://holdi601.github.io/3DHeat-Ext-Reforger/) |
| Ext-R6 | replays de Rainbow Six Siege | [3DHeat-Ext-R6](https://github.com/Holdi601/3DHeat-Ext-R6) | [docs](https://holdi601.github.io/3DHeat-Ext-R6/) |
