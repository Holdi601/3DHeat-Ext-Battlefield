# Third-party licences

This tool is MIT licensed ([`LICENSE`](LICENSE)). What it uses or loads, and
under which licence; each package's own source is what counts, not this file.

| Software | Licence | How it is used |
|---|---|---|
| 3DHeat GameFiles (`heat3d-gamefiles`) | MIT | a dependency, installed by pip: the glTF writer, the Steam library search, the detail budget, the levels folder and the Oodle loader |
| numpy | BSD-3-Clause | a dependency: mesh, terrain and navigation mesh decoding |
| Pillow | MIT-CMU (HPND) | a dependency: block-compressed textures, the baked ground colour |
| lz4 | BSD-3-Clause | a dependency: LZ4 blocks in the game's payloads |
| zstandard | BSD-3-Clause | a dependency: zstd blocks in the game's payloads |
| pytest | MIT | development only: the tests |
| Oodle (`oo2core_*.dll`, RAD Game Tools, now Epic) | proprietary | **never bundled**: some of the game's data is Oodle-compressed, and there is no redistributable build. GameFiles' `oodle.py` loads a library already on the machine - the one the game ships, or the copy `HEAT3D_OODLE` points at; none of it is in this repository |

The licences were read off the package metadata in September 2026. Where a
component's terms changed after that, the source is what counts.

## The format, and where it was learned

Frostbite's `.toc`, bundles and EBX are undocumented file formats. None of the
readers here is derived from another project's source.

The Frostbite readers (`frostbitebundle.py`, `frostbiteebx.py`,
`frostbitemesh.py`, `frostbitelevel.py`) were worked out from Battlefield 6's
own files. Public descriptions of older Frostbite versions served as a map of
what to look for and supplied field names, and nothing more: the FrostyToolsuite
modding tools (github.com/CadeEvs/FrostyToolsuite and its forks, CC BY-NC-ND 4.0;
the newer FrostyToolsuite/FrostyToolsuite, GPL-3.0) for the binary bundle
manifest, the RIFF EBX chunk layout and the MeshSet structure; a format note
for Need for Speed Heat (github.com/cmprssd/nfsh, GPL-3.0) for the vertex-stream
order and the terrain quadtree's child order; and Mattias Widmark's GDC 2012 talk
"Terrain in Battlefield 3". No code from any of them is in this repository, and
every offset the readers use was measured on the shipped files, which is why
they differ from all of those sources. None of those licences is compatible
with copying into an MIT repository, and none was copied.

The game's own type library sits in its initial file system, which is
encrypted. It is not read: no key is recovered or used, and the few types the
level export needs were laid out from the data instead.

## The game's files

Battlefield 6 belongs to Electronic Arts. This tool is not affiliated with or
endorsed by Electronic Arts; Battlefield and related names and trademarks
belong to their owners. This repository holds no file of the game and no level
made from one; the tool reads the copy the user installed, on the user's
machine, and the level it writes stays there. See
[Terms and licence](https://holdi601.github.io/3DHeat-Ext-Battlefield/terms.html).
