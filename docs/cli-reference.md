---
title: Command reference
nav_order: 90
---

# Command reference

Generated from the code by `tools/gen_docs_reference.py`: do not edit by hand.
The other pages explain each command step by step.

## `heat3d-battlefield-maps`

```text
usage: heat3d-battlefield-maps [-h] [--version] {levels,level,identify} ...

Battlefield 6 levels (Frostbite) from your own install into 3DHeat levels.

positional arguments:
  {levels,level,identify}
    levels              list the levels of an installed Frostbite game
    level               export a Frostbite level: its terrain backdrop and placed
                        meshes
    identify            say whether a file is a Frostbite table of contents, and what
                        it holds

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

It reads the files of your own install; the levels it writes stay on your machine.
```

## `levels`

```text
usage: heat3d-battlefield-maps levels [-h] [--install INSTALL]

options:
  -h, --help            show this help message and exit
  --install, --game INSTALL
                        the game's folder (or set HEAT3D_BATTLEFIELD_GAME); needed for
                        Battlefield 4 and 1
```

## `level`

```text
usage: heat3d-battlefield-maps level [-h] [-o OUT] [--install INSTALL]
                                     [--detail-budget DETAIL_BUDGET]
                                     [--textures [PIXELS]] [--ground-texture [METRES]]
                                     [--navmesh] [--by-mesh] [--clamped-uvs]
                                     [--ground-spacing METRES] [--order FILE]
                                     [--skip TEXT]
                                     level

positional arguments:
  level                 the level's name as `levels` lists it, or its .toc; `all` for
                        every multiplayer level of Battlefield 4 or 1

options:
  -h, --help            show this help message and exit
  -o, --out OUT         the .glb (default: <level>.glb, in $HEAT3D_LEVELS/<game> when
                        that is set)
  --install, --game INSTALL
                        the game's folder (or set HEAT3D_BATTLEFIELD_GAME); needed for
                        Battlefield 4 and 1
  --detail-budget DETAIL_BUDGET
                        a ceiling on triangles; the costliest meshes drop to coarser
                        levels of detail until it fits (default: every copy at its
                        coarsest, plus a quarter, at least 1,500,000; the terrain
                        stays at full detail)
  --textures [PIXELS]   write each surface's colour map, no larger than PIXELS a side
                        (default 512 when given without a size); without it, flat
                        colours
  --ground-texture [METRES]
                        bake the terrain decals (roads, aprons, markings) into the
                        ground's colour, METRES a pixel (default 0.5 when given
                        without a size), in tiles of at most 4096 pixels
  --navmesh             add the soldiers' walkable surfaces from the level's
                        navigation mesh as the part nav:walkable
  --by-mesh             for finding what a part is: one part per source mesh and
                        material, named '<part> | <mesh> | <material>' (a much larger
                        file)
  --clamped-uvs         for a renderer that cannot repeat a texture: cut every
                        textured triangle into pieces with UVs inside 0..1, and draw
                        the ones that would need more than 4 pieces in their texture's
                        average colour (default: UVs as the game has them, with a
                        repeating sampler)
  --ground-spacing METRES
                        the terrain heightfield's finest spacing (default 4; 0 leaves
                        it out)
  --order FILE          with `all` (Battlefield 4 and 1): a file of level names, one a
                        line, to export first in that order
  --skip TEXT           leave out static model groups whose partition name contains
                        TEXT (repeatable)
```

## `identify`

```text
usage: heat3d-battlefield-maps identify [-h] path

positional arguments:
  path

options:
  -h, --help  show this help message and exit
```

## Output

### `.glb` parts

`ground:terrain` (the heightfield; `ground:terrain x<x> z<z>` per tile with `--ground-texture`), `ground:terrain backdrop`, `ground:terrain blend`; per kind of mesh `water:water`, `structure:trees`, `structure:rocks`, `structure:buildings`, `structure:infrastructure`, else `structure:props` (with `--textures`, one part per colour map: `<kind> <texture>`); `<part> (destructible)` for what a match can destroy; `nav:walkable` with `--navmesh`; `<part> (average colour)` with `--clamped-uvs`; `<part> | <mesh> | <material>` with `--by-mesh`.

`asset.generator`: `heat3d_gamefiles` (the glTF writer of 3DHeat GameFiles).
