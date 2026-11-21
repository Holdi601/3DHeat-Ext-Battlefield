---
title: Game-mode layouts
---

# Game-mode layouts (Battlefield 4 and Battlefield 1)

`layouts` writes, for each multiplayer level, what every game mode of it is
played over: the capture points and headquarters, the mode's objectives, each
team's combat area and the spawn points. One file a level,
`<Level>.layouts.json`, beside the level's `.glb`.

```bash
heat3d-battlefield-maps layouts MP_Prison --game "<the Battlefield 4 folder>"
heat3d-battlefield-maps layouts all --game "<the Battlefield 1 folder>"
heat3d-battlefield-maps layouts all --game "<the Battlefield 4 folder>" -o levels/battlefield-4
```

Without `-o` the files go to `$HEAT3D_LEVELS/battlefield-4/` (or
`battlefield-1`) when that is set, where `level` puts the levels. A level takes
one to ten seconds.

## What is in the file

```json
{ "format": "3dheat-layouts", "version": 1, "game": "battlefield-4", "level": "MP_Prison",
  "units": "m", "up": "y",
  "layouts": [ { "id": "ConquestLarge0", "name": "Conquest Large", "mode": "ConquestLarge0",
                 "objectives": [...], "zones": [...], "spawns": [...] } ] }
```

One layout for each mode the level is set up for, named as the game names the
mode (`ConquestLarge0`, `RushLarge0`, `Domination0`, `Obliteration`,
`Breakthrough0`, `Possession0`...), with the name the game's menus give it.

| Kind | Entries |
|---|---|
| `objectives` | `capture_zone` (letter, name, position, `radius` or an outline of `points`, `ownerAtStart` for a point that starts held), `base` (a team's headquarters or spawn base), `objective` with a `kind`: `mcom`, `telegraph`, `bomb_target`, `flag`, `pigeon`... |
| `zones` | `play_area`: a team's combat area as a polygon (`points`); outside it the team is out of bounds |
| `spawns` | `spawn` and `vehicle_spawn` points with team, heading, the capture point (`base`) that owns them, the vehicle |

Rush and Breakthrough come in stages: an entry of one stage carries `stage`.
Positions are the level's own coordinates, the same as its `.glb`.

## In the viewer

The 3DHeat viewer draws the layout of the mode the loaded data is played in
(a `mode` column, or the match's mode) on the level, in the **Objectives**
panel: capture zones in their owner's colour, each team's play area faintly
filled in its colour, out of bounds hatched, spawns and objectives, each kind
on its own toggle, and a **Layout** choice to show another mode or one stage.
Run from a checkout, the viewer finds the file beside the level in the levels
folder by itself; otherwise pick the `.layouts.json` with the data.

## How it is read

A level is a tree of sub-levels; a sub-level that belongs to some modes only
says which in its inclusion settings. For one mode the reader walks the
sub-levels that mode loads, their layers and the prefabs placed in them, the
transforms composed on the way down. A prefab placed once gets its values from
outside, through the sub-level's interface and its property and link
connections; the reader follows those the same way, so a capture point's
radius, the place of each Rush objective and the shape each team's combat area
is linked to come out as the level sets them. Pieces of a prefab the level
never placed (spare stages of a mode) are left out.

Battlefield 1's capture areas are polygons, found through each capture point's
channel (`flag<letter>_hub`). Breakthrough's sector capture points are not all
found yet.
