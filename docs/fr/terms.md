---
title: "Règles et licences"
nav_order: 8
lang: "fr"
source: terms.md
source_hash: "50d8b31139d6"
nav_exclude: true
search_exclude: true
---
# Règles et licences {#terms-and-licence}

## Le jeu d'EA {#eas-game}

Battlefield 6 et ses niveaux appartiennent à Electronic Arts. 3DHeat Battlefield n'est ni affilié à
Electronic Arts ni soutenu par Electronic Arts. Battlefield ainsi que les noms et marques associés
appartiennent à leurs propriétaires.

Cet outil n'embarque rien du jeu et ne télécharge rien : ni ressources du jeu, ni code du jeu, ni DLL.
Il lit les fichiers de la copie **que vous** avez installée, sur votre machine, en dehors du jeu. Il ne
modifie rien dans le jeu, ne tourne pas à côté de lui et ne parle à aucun serveur.

Le niveau qu'il écrit reste sur votre machine : gardez les fichiers `.glb` exportés, et les textures
qu'ils contiennent, pour votre propre analyse, et ne publiez, ne partagez ni ne vendez les niveaux,
modèles ou textures exportés. Le `.gitignore` du dépôt garde les fichiers de jeu et les exports hors du
contrôle de version, par type de fichier.

Chaque lecteur de jeu est un petit projet à part, avec son propre fichier de licence, ses propres versions et son propre suivi des tickets : il peut être installé, mis à jour, maintenu - ou retiré à la demande d'un ayant droit - seul, sans toucher au visualiseur ni aux autres outils.

Ayants droit : ouvrez un ticket sur [github.com/Holdi601/3DHeat-Ext-Battlefield/issues](https://github.com/Holdi601/3DHeat-Ext-Battlefield/issues) - nous répondons rapidement et retirons tout ce qui est demandé.

## Rien de chiffré n'est ouvert {#nothing-encrypted-is-opened}

- **Pas de clés : aucune livrée, aucune récupérée.** Rien ne cherche une clé dans un exécutable, et rien
  ne lit la mémoire d'un autre processus.
- **L'obfuscation non plus n'est pas implémentée.** Les tables Frostbite obfusquées par XOR sont
  détectées et refusées : aucun fichier disponible n'utilise cette forme et il n'y aurait rien pour
  vérifier une implémentation.
- **Les fichiers chiffrés restent fermés.** Le système de fichiers initial de Battlefield 6, qui contient
  la bibliothèque de types du jeu, est chiffré et n'est pas lu. L'export de niveau travaille à partir des
  fichiers qui ne sont pas chiffrés, et établit les deux types dont il a besoin à partir des données.
- **Rien n'est injecté dans un processus de jeu.** L'outil ne lit que des fichiers sur le
  disque.

## Oodle est trouvé, pas embarqué {#oodle-is-found-not-bundled}

Une partie des données du jeu est compressée en Oodle. Oodle (RAD Game Tools, désormais Epic) est
propriétaire et n'a pas de version redistribuable. `oo2core_*.dll` est concédée sous licence au produit
qui la livre. Cet outil n'en embarque donc jamais : `oodle.py` de 3DHeat GameFiles charge une bibliothèque
déjà présente sur la machine — celle que livre le jeu, ou la copie que `HEAT3D_OODLE` désigne — plutôt
que d'en transporter une. Voir [Oodle](https://holdi601.github.io/3DHeat-GameFiles/fr/reader-oodle.html).

## Le format lui-même {#the-format-itself}

Les `.toc`, bundles, partitions EBX, MeshSet et terrains de Frostbite ne sont pas documentés. Les lecteurs d'ici ont été mis au point à partir des
propres fichiers de Battlefield 6. Des descriptions publiques d'anciennes versions de Frostbite (les outils
de modding Frosty, une note sur le format de Need for Speed Heat, une conférence GDC) ont fourni des noms
de champs et une carte de ce qu'il faut chercher. Aucun code n'a été repris de l'une d'elles ; chaque
décalage a été mesuré sur les fichiers (les sources et leurs licences :
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md)).

## Licence et sources {#licence-and-sources}

MIT ([`LICENSE`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSE)) : utilisez-le,
modifiez-le, distribuez-le, à des fins commerciales ou non. Il s'appuie sur
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (MIT) et demande numpy (BSD-3-Clause),
Pillow (MIT-CMU), lz4 et zstandard (BSD-3-Clause) ; les tests demandent pytest (MIT). Voir
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md).
