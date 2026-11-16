---
title: Battlefield 4 and Battlefield 1 levels
---

# Battlefield 4 and Battlefield 1 levels

`levels` and `level` also read Battlefield 4 and Battlefield 1. Give the game's
folder with `--game` (or set `HEAT3D_BATTLEFIELD_GAME`); the tool does not look
for these two games by itself.

```bash
heat3d-battlefield-maps levels --game "<the Battlefield 4 folder>"
heat3d-battlefield-maps level MP_Prison --game "<the Battlefield 4 folder>"
heat3d-battlefield-maps level all --game "<the Battlefield 1 folder>" -o levels/battlefield-1
```

- `levels` lists the multiplayer levels, with the layer each comes from
  (`Data`, `Patch`, `Update/<pack>`).
- `level <name>` writes one level as `<Level>.glb`, named as the game names the
  level (`MP_Prison.glb`, `XP1_001.glb`). Without `-o` it goes to
  `$HEAT3D_LEVELS/battlefield-4/` (or `battlefield-1`) when that is set.
- `level all` writes every multiplayer level; `-o` is then a folder. With
  `--order FILE`, the names listed in the file (one a line; the last word of
  each line counts) go first, in that order.
- `--detail-budget N` caps the placed meshes' triangles (default 3,000,000).

Expect 20 to 60 seconds and 100 to 130 MB a level; a level whose meshes keep
their buffers in other parts of the install takes a couple of minutes more
the first time it needs them.

## What is in the file

| Part | What |
|---|---|
| `ground:terrain` | the heightfield: the play area at 1 to 3 m, the rest of the terrain square coarser; coloured by the game's colour map in Battlefield 1, by slope in Battlefield 4 |
| `structure:buildings`, `structure:props`, `structure:rocks`, `structure:trees`, `structure:infrastructure`, `water:water` | every mesh the level places, by what its asset path says it is, in flat colours |

Every part name ends in ` @battlefield-4/<Level>` or ` @battlefield-1/<Level>`.
The 3DHeat viewer reads that: a level loaded once is kept in its level
library, and a table whose `map` column names that level is offered it, and
gets it by itself when no level is loaded.

Positions are the game's own: x and z across, y up, metres. Positions recorded
in the game's coordinates lie on the level as they are. The levels were checked against
recorded positions.

## How it is read

The older Frostbite keeps each level in a superbundle: a `.toc` naming the
bundles and a `.sb` holding them, each bundle a tree listing its partitions
(`ebx`), resources (`res`) and chunks by SHA-1, and `cas.cat` files saying
which `cas_NN.cas` blob holds each hash. Patches ship their own tables;
payloads a patch changed can be stored as an edit of the old ones, which is
applied. Expansion levels of Battlefield 4 keep their bundles whole in the
`.sb`.

- **Partitions** describe themselves: each carries its type and field names,
  so the level's layout reads as named objects (`legacyebx.py`).
- **What is placed**: the walk starts at the level's own partition and follows
  sub-levels, world parts, layers, prefabs and object references, composing
  their transforms; static model groups place most of the scenery
  (`legacylevel.py`).
- **Where a static model group's copies stand**: for most members not in the
  partition but in the group's collision resource, a Havok packfile; its
  static compound shape has a record per copy or per physics part
  (`legacyhavok.py`).
- **Meshes**: the MeshSet layout of each game (`legacymesh.py`); the costliest
  meshes drop to coarser levels of detail until the budget holds, and if even
  the coarsest do not fit, the smallest meshes are left out.
- **Terrain**: the streaming tree's quadtree of height pages
  (`legacyterrain.py`); every page is checked against its neighbours and its
  parent before it is used.

Nothing is decrypted: none of these files is encrypted. The payloads of both
games are LZ4 blocks or stored as they are; no Oodle library is needed.

## What is left out

- Destruction states, vehicles, soldiers, effects, sound and logic.
- Copies of a static model group without collision, where the group keeps
  their transforms nowhere else.
- Battlefield 4 expansion levels: where a patch stores a bundle as an edit,
  the unpatched bundle is read, and meshes whose buffers only the patch has
  are left out.
- Two Battlefield 1 levels have no terrain resource; they are written without
  ground.

This tool is not affiliated with EA or DICE; trademarks belong to their owners.
