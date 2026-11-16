# 3DHeat Battlefield: Battlefield 6 levels as 3D levels

**What is it?** This tool turns a Battlefield 6 level, read from your own
install, into a 3D model you can fly over in the
[3DHeat](https://github.com/Holdi601/3DHeat) viewer: the terrain, every mesh
the level places, the backdrop round the map, and on request the surfaces'
colour maps, the roads and markings baked into the ground, and the surfaces
soldiers walk on.

**Why would I use it?** So heat from your Battlefield 6 matches has the ground
and the buildings under it, in the game's own coordinates.

**Example:** `heat3d-battlefield-maps level <level> -o level.glb --textures` ->
`level.glb`, a few hundred MB.

**Documentation:** [holdi601.github.io/3DHeat-Ext-Battlefield](https://holdi601.github.io/3DHeat-Ext-Battlefield/), a page per
command with step-by-step use and example output. Part of
[3DHeat](https://github.com/Holdi601/3DHeat) ([documentation](https://holdi601.github.io/3DHeat/)).

Each game reader is its own small project with its own licence file, releases
and issue tracker, so it can be installed, updated, maintained - or withdrawn
on a rights holder's request - on its own, without affecting the viewer or the
other tools.

The levels it writes stay on your machine.

## Install

New to the command line? Read [Before you start](https://holdi601.github.io/3DHeat-Ext-Battlefield/before-you-start.html) first.

1. Install Python 3.10 or later, and Battlefield 6 (Steam, the EA app or Epic).
2. `git clone https://github.com/Holdi601/3DHeat-Ext-Battlefield` (or download the
   ZIP) and open a terminal in that folder.
3. Install the command - it brings [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles),
   the library it reads with - and check that the game is found:

```bash
python -m pip install -e .        # installs heat3d-battlefield-maps and GameFiles
heat3d-battlefield-maps levels    # where the game is, and its levels
```

You should see `<n> levels in <the game's folder>` and a line per level.
Without pip, the tool finds GameFiles in `HEAT3D_GAMEFILES`, in `../../gamefiles`
(inside a 3DHeat checkout) or in `../3DHeat-GameFiles`.

## Commands

| Command | Does | Page |
|---|---|---|
| `levels [--install FOLDER]` | where the game is, and every level it ships | [levels and level](https://holdi601.github.io/3DHeat-Ext-Battlefield/level-battlefield.html) |
| `level <level> [-o FILE] [options]` | one level as a `.glb` | [levels and level](https://holdi601.github.io/3DHeat-Ext-Battlefield/level-battlefield.html) |
| `identify <file>` | whether a file is a Frostbite table of contents, and what it holds | [identify](https://holdi601.github.io/3DHeat-Ext-Battlefield/identify.html) |

```bash
heat3d-battlefield-maps level <level> -o level.glb                                   # flat colours
heat3d-battlefield-maps level <level> -o level.glb --textures 512 --ground-texture 0.5 --navmesh
heat3d-battlefield-maps level <level> --textures 256 --detail-budget 3000000 --ground-spacing 8
```

| `level` option | Does |
|---|---|
| `-o`, `--out FILE` | the `.glb` to write (default `<level>.glb`, in `$HEAT3D_LEVELS/<game>/` when that is set) |
| `--install FOLDER` | the game's folder, when it is in no Steam library and not in the EA app's, Origin's or Epic's default folder |
| `--textures [PIXELS]` | each surface's colour map, at most PIXELS a side (512 without a size) |
| `--ground-texture [METRES]` | roads, aprons and markings baked into the ground's colour (0.5 m a pixel without a size) |
| `--navmesh` | the soldiers' walkable surfaces as `nav:walkable` |
| `--ground-spacing METRES` | the heightfield's finest spacing (default 4; 0 leaves it out) |
| `--detail-budget N` | a ceiling on triangles (default: every copy at its coarsest, plus a quarter, at least 1,500,000) |
| `--skip TEXT` | leave out static model groups whose partition name contains TEXT (repeatable) |
| `--by-mesh` | one part per source mesh and material, for finding what a part is |
| `--clamped-uvs` | for a renderer that cannot repeat a texture |

Exit status: 0 done; 1 reading failed; 2 the game, the file, GameFiles or an
Oodle library not found (the message says which, and what to do). Every
option, as the program prints it: [Command reference](https://holdi601.github.io/3DHeat-Ext-Battlefield/cli-reference.html).

3DHeat GameFiles' `levels`, `level` and `identify` run this tool with the same
arguments, so `python -m heat3d_gamefiles level <level>` does the same.

## What comes out, and loading it

One glTF binary in the game's own coordinates: `ground:terrain`,
`ground:terrain backdrop`, `ground:terrain blend`, `structure:<kind>` per kind
of mesh (per colour map with `--textures`), and `nav:walkable` with
`--navmesh`. Load it in the viewer's **Background / level** panel
([loading a level](https://holdi601.github.io/3DHeat/levels.html)).

## Terms

3DHeat Battlefield is not affiliated with or endorsed by Electronic Arts.
Battlefield and related names and trademarks belong to their owners. The tool
reads the files of your own install; nothing of the game is in this repository
or downloaded by it - no game assets, no game code, no DLLs - and nothing
encrypted is opened. Oodle is never bundled, but loaded from the copy the game
ships. The level comes out of your own install and stays on your machine
([Terms and licence](https://holdi601.github.io/3DHeat-Ext-Battlefield/terms.html)).

Rights holders: open an issue at
[github.com/Holdi601/3DHeat-Ext-Battlefield/issues](https://github.com/Holdi601/3DHeat-Ext-Battlefield/issues)
- we respond quickly and remove anything on request.

## Tests

```bash
python -m pip install -e .[test]
python -m pytest
```

On made-up data; the checks against a real install run when Battlefield 6 is
installed and skip otherwise, and never write into the repository.

## Licence

MIT ([`LICENSE`](LICENSE)). Third-party software it uses or loads: [`LICENSES.md`](LICENSES.md).
