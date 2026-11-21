---
title: Game-mode layouts
---

# Game-mode layouts (Battlefield 6, 4 and 1)

`layouts` writes, for each multiplayer level, what every game mode of it is
played over: the capture points and headquarters, the mode's objectives, each
team's combat area and the spawn points. One file a level,
`<Level>.layouts.json`, beside the level's `.glb`.

```bash
heat3d-battlefield-maps layouts MP_Prison --game "<the Battlefield 4 folder>"
heat3d-battlefield-maps layouts all --game "<the Battlefield 1 folder>"
heat3d-battlefield-maps layouts all --game "<the Battlefield 6 folder>"
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
| `spawns` | `spawn` and `vehicle_spawn` points with team, heading, the capture point or HQ that owns them (`base`, `baseId`, `baseSource`), when they can be used (`rule`), the vehicle (`vehicle`, `vehicleClass`, `vehicleKind`) |

Rush and Breakthrough come in stages: an entry of one stage carries `stage`
(a spawn used in several, `stages`). Capture points and headquarters have an
`id` (`A`, `HQ1`, `HQ2#3` for stage 3). Positions are the level's own
coordinates, the same as its `.glb`.

## Spawns and their flags

Each spawn names its owner by `baseId`, and `baseSource` says how that is known:

| `baseSource` | From |
|---|---|
| `link` | the capture point's or HQ's own spawn lists (its link connections) |
| `channel` | Battlefield 1: the flag's or team's channel (`conquest_flaga_hub`, `conquest_team1_hub`) |
| `prefab` | the spawn sits inside the capture point's prefab |
| `nearest` | none of these: the nearest capture point within 150 m, only in a mode where most spawns are linked |

`rule` says when a spawn can be used: `flag` while its team holds the flag (a
flag spawn with no team: whoever holds it), `hq` always, `stage` in its stage,
`team` always for its team, `free` by anyone (Team Deathmatch's spawns, a gun
emplacement no flag lists).

A soldier spawn that is a vehicle's seat on the deploy screen stands for the
vehicle; a vehicle spawner's alternative spawn points (where the soldier goes
when the vehicle cannot spawn) are not spawns of their own. Spawns left out
are counted in the layout's `spawnsDropped`: a prefab's spare at the level's
origin, a vehicle's alternative point, a shared layer's spawn that only other
modes' flags use. `vehicleKind` is `tank`, `jet`, `helicopter`, `boat`,
`stationary`, `car`, `horse` or `plane`; `vehicleClass` is the spawner's own
name for it (`tank_mbt`, `car_heavy`).

## Battlefield 6

Battlefield 6 builds its modes from "gem" prefabs (`gem_capturepoint`,
`gem_hq`, `gem_vehiclespawner`, `gem_sector`...). Each mode has a layer of its
own under the level's gameplay sub-world (`conquest/conquest0`, `rush/rush0`,
`mp_escalation0`...). The links between them sit in the gameplay sub-world,
and they say which spawns and vehicle spawners belong to which flag and HQ. A
flag's letter is the name of the telemetry area on it (`CQ_FlagC`). Breakthrough's
and Rush's sectors give the stages. Not read yet: an HQ's team, and which
vehicle a spawner spawns.

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
