---
title: Terms and licence
nav_order: 8
---

# Terms and licence

## EA's game

Battlefield 6 and its levels belong to Electronic Arts. 3DHeat Battlefield is
not affiliated with or endorsed by Electronic Arts. Battlefield and related
names and trademarks belong to their owners.

This tool ships nothing of the game and downloads nothing: no game assets, no
game code, no DLLs. It reads the files of the copy **you** installed, on your
machine, outside the game. It changes nothing in the game, does not run
alongside it and talks to no server.

The level it writes stays on your machine: keep exported `.glb` files, and the
textures inside them, for your own analysis, and please do not publish, share
or sell exported levels, models or textures. The repository's `.gitignore`
keeps game files and exports out of version control by file type.

Each game reader is its own small project with its own licence file, releases
and issue tracker, so it can be installed, updated, maintained - or withdrawn
on a rights holder's request - on its own, without affecting the viewer or the
other tools.

Rights holders: open an issue at
[github.com/Holdi601/3DHeat-Ext-Battlefield/issues](https://github.com/Holdi601/3DHeat-Ext-Battlefield/issues)
- we respond quickly and remove anything on request.

## Nothing encrypted is opened

- **No keys: none shipped, none recovered.** Nothing searches an executable for
  a key, and nothing reads another process's memory.
- **Obfuscation is not implemented either.** Frostbite's XOR-obfuscated tables
  are detected and declined: no file on hand uses that form, and there would be
  nothing to check an implementation against.
- **Encrypted files stay closed.** Battlefield 6's initial file system, which
  holds the game's type library, is encrypted and is not read. The level export
  works from the files that are not encrypted, and lays out the two types it
  needs from the data.
- **Nothing injects into a game process.** The tool only reads files on disk.

## Oodle is found, not bundled

Some of the game's data is Oodle-compressed. Oodle (RAD Game Tools, now Epic)
is proprietary and has no redistributable build. `oo2core_*.dll` is licensed to
the product that ships it. This tool therefore never bundles it: 3DHeat
GameFiles' `oodle.py` loads a library already on the machine - the one the game
ships, or the copy `HEAT3D_OODLE` points at - rather than carrying one. See
[Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html).

## The format itself

Frostbite's `.toc`, bundles, EBX partitions, MeshSets and terrain are
undocumented. The readers
here were worked out from Battlefield 6's own files. Public descriptions of
older Frostbite versions (the Frosty modding tools, a Need for Speed Heat
format note, a GDC talk) supplied field names and a map of what to look for.
No code was taken from any of them; every offset was measured on the files
(the sources and their licences:
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md)).

## Licence and sources

MIT ([`LICENSE`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSE)):
use it, change it, ship it, commercially or not. It builds on
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (MIT) and needs
numpy (BSD-3-Clause), Pillow (MIT-CMU), lz4 and zstandard (BSD-3-Clause); the
tests need pytest (MIT). See
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md).
