# Changelog

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
| `identify` | [Identifying a file](docs/identify.md) |
| How the tables, bundles, meshes, terrain, textures and navigation mesh are read and checked | [Frostbite](docs/reader-frostbite.md) |
| EA's game, Oodle, the format sources | [Terms and licence](docs/terms.md) |
| Every option and part name, generated | [Command reference](docs/cli-reference.md) |
| Release checklist for the docs | [Maintaining these docs](docs/maintaining.md) |
