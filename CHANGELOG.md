# Changelog

## 0.5.0

- Its own icon: the 3DHeat cube with a text badge for its game (letters in 3DHeat's colours), as the
  program, window, taskbar and docs icon.
- A new window: the 3DHeat look in dark and light (follows the system, switchable), the logo and
  icon, sharp at any display scaling. Four steps: find the game (each requirement with its fix),
  choose (maps ticked when there is something to do, filters, search; jobs with their fields
  inline), work (progress, time left, cancel), done (open in 3DHeat, open the output folder, and
  for a failure what went wrong and what to do, copy details, report a problem).
- No console window on Windows: the program is a window program. From a terminal it still prints
  as before; `heat3d-battlefield-cli.cmd` beside it waits for it in a terminal and passes its exit code.
- The update offer in the same look: Update now / Later / Skip this version, and "Update
  automatically" from the dialog.
- CI draws every page and dialog of the window (on Linux under a virtual display) and checks the
  Windows build is a window program.

## 0.4.0

- A standalone program for Windows (no Python needed), built by CI with a `SHA256SUMS` file. Without arguments
  it opens a window: what is found and what is missing (Battlefield 6, 4 and 1 installs, the Oodle library from
  your own Battlefield 6 install, disk space), the levels folder, each game's levels as new / changed by a game
  update / extracted by an older version / up to date, and extraction of the picked ones one at a time into
  `<levels>/battlefield-6/`, `battlefield-4/` and `battlefield-1/` (the level and its layouts), and updates.
- Each extracted level is recorded in `<levels>/<game>/.heat3d-extract.json` (extractor version, game build,
  size and SHA-256 of its tables), so levels a game update adds or changes are found and only those extracted:
  `status --json`, `extract [--game bf6|bf4|bf1] --new` / `--changed` / `--outdated` / `<level>...`,
  `--progress-json`.
- Updates ask first (update now / later / skip this version) unless automatic updates were chosen
  (`--auto-update`, the window's checkbox, or `HEAT3D_AUTO_UPDATE=1`).
- The standalone program looks for each game by its own folder name in every Steam library and launcher folder,
  so Battlefield 6, 4 and 1 installed side by side are each found.

## 0.3.1

- `models`: Battlefield 4 and 1 vehicles carry their hit regions under a `dm` node: the surface of each
  moving part (hull, turret, gun, rotor) facing each of the blueprint's direction zones (front, rear, left,
  right, top; `<part>_<zone>`, with the zone's health, shield and angle settings), and each destructible
  piece of the model (`piece<index>`, with its health and material).

## 0.3.0

- `layouts` reads Battlefield 6 too: each mode's capture points (lettered,
  with their capture areas), HQs, combat area, Rush's M-COMs, the soldiers'
  spawn points and the vehicle spawners, from the user's own install.
- Every spawn names the capture point or HQ that owns it (`baseId`) and how
  that is known (`baseSource`: the game's links, a Battlefield 1 channel, the
  capture point's prefab, or only the nearest flag), and when it can be used
  (`rule`: `flag`, `hq`, `stage`, `team`, `free`). Capture points and HQs get
  an `id`.
- Vehicle spawns whose vehicle is given from outside (most of Battlefield 4's
  and 1's) are read, with the spawner's class and a vehicle kind; a vehicle's
  seat and alternative spawn points are folded into the vehicle.
- Spawns at the level's origin (a prefab's spare), sub-levels set up for no
  mode, and shared spawns only other modes use are left out and counted
  (`spawnsDropped`). Battlefield 1's flags and HQs own their spawns through
  their channels; Breakthrough's sector channels give stages.
- `catalog`: the vehicles of every Battlefield 6, 4 and 1 installed as `<game>/catalog.json` (name, class, side,
  the real vehicle each stands for), for the viewer's names and order.
- `models`: the same vehicles' models as a local model pack (`model-packs/<game>/`, a `.glb` per vehicle at three
  levels of detail; hull, running gear, turret, gun and rotor as the viewer moves them), drawn by the viewer in
  place of its figures.

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
