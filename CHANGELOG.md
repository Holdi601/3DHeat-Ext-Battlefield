# Changelog

## 0.2.1

- Battlefield 4 and Battlefield 1: `layouts <level>|all --game <folder>` writes
  what each game mode of a level is played over as `<Level>.layouts.json`
  beside the level: capture points and headquarters (letter, name, radius or
  polygon), the mode's objectives (M-COMs, telegraphs, bomb targets...), each
  team's combat area, and the soldier and vehicle spawns with the capture point
  that owns them; Rush and Breakthrough by stage. The 3DHeat viewer draws the
  layout of the data's mode on the level.

## 0.2.0

- Battlefield 4 and Battlefield 1: `levels --game <folder>` lists their
  multiplayer levels and `level <level>` (or `all`) writes each as
  `<Level>.glb` - terrain (coloured by the game's colour map in Battlefield 1),
  every placed mesh in flat colours by kind, decimated to a triangle budget.
  New readers for the older superbundle form, its self-describing partitions,
  patched payloads, the meshes and terrain of both games, and the static
  model groups' copies from their collision. Part names end in
  ` @battlefield-4/<Level>` so the viewer can match a level to tables on it.
- `--game` is another name for `--install`; `HEAT3D_BATTLEFIELD_GAME` gives
  the folder when neither is given.
- Installs with one line and no Git: `pip install` of the release's zip, which
  brings GameFiles from its own release zip. A pip install knows its version
  and updates itself with pip when a newer release is out.
- README: a quick start for new users.

## 0.1.0

- First version, moved out of 3DHeat GameFiles with its history (GameFiles'
  `levels`, `level` and the Frostbite part of `identify` now run this tool):
  a whole Battlefield 6 level from your own install as a 3DHeat level - the
  terrain heightfield and backdrop, every mesh the static model groups place
  and the objects placed one by one, on request the colour maps, the terrain
  decals baked into the ground and the soldiers' navigation mesh. The same
  options and defaults as in GameFiles.
- The game is also found in the EA app's, Origin's and the Epic Games
  launcher's default folders, not only in Steam libraries.
- `identify <file>`: a Frostbite table of contents described, exit 2 and
  `not a Battlefield file` for anything else.
- A missing Oodle library is one message and exit 2 rather than a traceback.

## Docs

Where each feature is documented
([holdi601.github.io/3DHeat-Ext-Battlefield](https://holdi601.github.io/3DHeat-Ext-Battlefield/)):

| Feature | Page |
|---|---|
| Installing, GameFiles, a first run | [Before you start](docs/before-you-start.md) |
| Listing levels and exporting one (`levels`, `level` and every option), where the game is found, sizes, parts | [Battlefield 6 levels](docs/level-battlefield.md) |
| Battlefield 4 and Battlefield 1 levels | [Battlefield 4 and Battlefield 1 levels](docs/level-battlefield-older.md) |
| Game-mode layouts (`layouts`) | [Game-mode layouts](docs/layouts.md) |
| `identify` | [Identifying a file](docs/identify.md) |
| How the tables, bundles, meshes, terrain, textures and navigation mesh are read and checked | [Frostbite](docs/reader-frostbite.md) |
| EA's game, Oodle, the format sources | [Terms and licence](docs/terms.md) |
| Every option and part name, generated | [Command reference](docs/cli-reference.md) |
| Release checklist for the docs | [Maintaining these docs](docs/maintaining.md) |
