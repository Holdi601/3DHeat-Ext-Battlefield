"""
What each game mode of a Battlefield 6 level is played over: capture
points and headquarters, each team's combat area, the soldiers' spawn
points and the vehicle spawners, a layout per mode, in the level's own
frame (the same as the `.glb` the `level` verb writes).

How a Battlefield 6 mode is put together
----------------------------------------
Battlefield 6 builds its modes from "gems", prefabs of the shared game-mode
kit (`game/glaciermp/gamemodes/_shared/gems/...`): `gem_capturepoint`,
`gem_hq`, `gem_vehiclespawner`, `gem_sector`, `gem_specialcombatarea`,
`gem_telemetryarea` and more. Each mode has one layer of its own under the
level's gameplay sub-world (`_layers_gameplay/conquest/conquest0`,
`.../rush/rush0`, `.../mp_escalation0`...) holding

- the gem references, each a transform (+32) and the gem it places (an
  import at +112),
- the spawn points, a transform (+32) and nothing else of note, and
- the shapes (an array of points, sixteen bytes each, behind a pointer at
  +32), the capture and combat areas.

None of them says what it belongs to. The level's gameplay sub-world
(`_layers_gameplay/gameplay`) does, in its link connections (24 bytes each:
source and target pointers, the source's and the target's field ids):

    capture point  0x28e44180 -> spawn point        team 1's spawns at the flag
                   0x28e44183 -> spawn point        team 2's
                   0xc838813a -> vehicle spawner    the flag's vehicles
                   0x3ca9ebf6 -> shape              the capture area
    headquarters   0xdcf5607c -> spawn point        the headquarters' spawns
                   0xc838813a -> vehicle spawner    its vehicles
    sector         0xc838813a -> capture point, headquarters
    combat area    0xa77cd52 -> shape               the play area
    telemetry area 0x31fb3b9f -> (the sub-world, the hash of a name)   `CQ_FlagA`, `BT_FlagB2`

The two spawn-list ids differ only in their last character's bits ('1' and
'2' hash three apart), which is how they are told apart. The field ids are
the names' hashes, but the names are not in the files; the meanings above
were read off the data: what each field points to, in every level read.

A capture point's letter is the name of the telemetry area at it (the
telemetry area named `CQ_FlagC` sits on flag C), the mode's own first,
another mode's on the same spot next (Operations has none of its own). A
headquarters' team is not in what is read: it is left unset.

This reads Battlefield 6's files as the user's install has them, without
the game's type library (`frostbiteebx`); a game update that changes a
layout makes this find less, and it says so.
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field

import numpy as np

from .frostbite import UnsupportedFrostbite
from .frostbiteebx import Partition, partition_guid, read_partition
from .legacyebx import name_hash
from .legacylayouts import FORMAT, _finish_spawns

#: Where a reference's transform and the blueprint it places are.
TRANSFORM_AT = 32
BLUEPRINT_AT = 112
#: A spawn point: 144 bytes, its transform at +32, nothing pointing out.
SPAWN_SIZE = 144
#: A shape: a pointer at +32 to its points, sixteen bytes each (x, y, z, w).
SHAPE_POINTS_AT = 32

#: The link connection arrays: their hash in the partition's array table, and the size of one.
LINK_ARRAY_HASH = 658967178
LINK_SIZE = 24

F_TEAM1_SPAWNS = 0x28E44180
F_TEAM2_SPAWNS = 0x28E44183
F_HQ_SPAWNS = 0xDCF5607C
F_OWNS = 0xC838813A
F_CAPTURE_AREA = 0x3CA9EBF6
F_HQ_AREA = 0xB545C66B
#: The combat area everyone plays in. Two more fields (0x285c8441, 0x285c8442)
#: point to one small shape together in the levels read, not a team's area:
#: what they mean is not known, so they are not read.
F_COMBAT_AREA = 0xA77CD52
F_SECTOR_AREA = 0x95A790AE
F_TELEMETRY = 0x31FB3B9F

#: Gems that spawn a vehicle, and its kind where the gem says (a vehicle spawner's vehicle is not read).
VEHICLE_GEMS = {"gem_vehiclespawner": "", "gem_stationaryspawner": "stationary"}

#: A mode's own layer under the gameplay sub-world: `conquest/conquest0`, `mp_escalation0`.
MODE_LAYER = re.compile(r"_layers_gameplay/(?:[a-z0-9_]+/)?((?:mp_)?[a-z0-9_]+?)0$")

#: What the modes are called in the game's menus.
MODE_NAMES = {
    "conquest": "Conquest", "breakthrough": "Breakthrough", "rush": "Rush", "mp_escalation": "Escalation",
    "mp_domination": "Domination", "mp_koth": "King of the Hill", "mp_teamdm": "Team Deathmatch",
    "mp_squaddm": "Squad Deathmatch", "mp_strikepoint": "Strikepoint", "mp_payload": "Payload",
    "mp_operations": "Operations", "customportal": "Portal", "freeroam": "Free Roam",
}

#: A telemetry area's name: the mode's prefix, then what it marks (`CQ_FlagA`, `BT_FlagB2`, `RUSH_MCOM_A1`).
TELEMETRY_NAME = re.compile(r"^[A-Z]+_(?:Flag|Sector|MCOM_?)([A-Z]\d?)$")


@dataclass
class Thing:
    kind: str
    at: int
    matrix: np.ndarray
    gem: str = ""

    @property
    def position(self) -> list[float]:
        return [round(float(v), 2) for v in self.matrix[3, :3]]

    @property
    def heading(self) -> float:
        f = self.matrix[2, :3]
        return round(math.degrees(math.atan2(float(f[0]), float(f[2]))) % 360.0, 1)


def _matrix(data: bytes, at: int) -> np.ndarray | None:
    rows = np.frombuffer(data, dtype="<f4", count=16, offset=at).reshape(4, 4).astype(np.float64)
    if not np.all(np.isfinite(rows)):
        return None
    r = rows[:3, :3]
    if not np.all(np.abs(np.linalg.norm(r, axis=1) - 1.0) < 0.05) or abs(abs(np.linalg.det(r)) - 1.0) > 0.1:
        return None
    m = np.eye(4)
    m[:, :3] = rows[:, :3]
    return m


class Bf6Level:
    """One level's catalogue, with the partitions a layout needs read once."""

    def __init__(self, catalogue, prefix: str):
        self.cat = catalogue
        self.prefix = prefix
        self._parts: dict[str, Partition | None] = {}
        self._guids: dict[bytes, str] | None = None

    def partition(self, name: str) -> Partition | None:
        if name not in self._parts:
            entry = self.cat.ebx.get(name)
            part = None
            if entry is not None:
                try:
                    part = read_partition(self.cat.read(entry.location), name)
                except UnsupportedFrostbite:
                    part = None
            self._parts[name] = part
        return self._parts[name]

    def names(self) -> dict[bytes, str]:
        """GUID -> name of the level's own partitions and the game-mode kit's: all an import here can name."""
        if self._guids is None:
            self._guids = {}
            for name, entry in self.cat.ebx.items():
                if not (name.startswith(self.prefix) or "/gamemodes/" in name):
                    continue
                try:
                    self._guids[partition_guid(self.cat.read(entry.location))] = name
                except (UnsupportedFrostbite, OSError, ValueError):
                    continue
        return self._guids

    def mode_layers(self) -> dict[str, str]:
        """mode id -> its layer's partition name."""
        out = {}
        for name in sorted(self.cat.ebx):
            if not name.startswith(self.prefix):
                continue
            m = MODE_LAYER.search(name[len(self.prefix) - 1:])
            if m and not name.endswith("_schematic"):
                out.setdefault(m.group(1), name)
        return out


def _instances(part: Partition):
    inst = sorted(part.instances)
    return inst, dict(zip(inst, inst[1:] + [len(part.data)]))


def read_layer(level: Bf6Level, name: str) -> dict[bytes, Thing]:
    """A mode layer's gem references, spawn points and shapes, by instance GUID."""
    part = level.partition(name)
    if part is None:
        return {}
    names = level.names()
    inst, ends = _instances(part)
    out: dict[bytes, Thing] = {}
    for a in inst:
        size = ends[a] - a
        guid = part.data[a - 16:a] if a >= 16 else b""
        if size >= BLUEPRINT_AT + 8 and (a + BLUEPRINT_AT) in part.import_offsets:
            what, index = part.pointer(a + BLUEPRINT_AT)
            gem = names.get(part.imports[index][0], "") if what == "import" else ""
            m = _matrix(part.data, a + TRANSFORM_AT)
            if gem and m is not None:
                out[guid] = Thing("gem", a, m, gem.rsplit("/", 1)[-1])
            continue
        if size == SPAWN_SIZE and not any(a <= p < a + size for p in part.pointers | part.import_offsets):
            m = _matrix(part.data, a + TRANSFORM_AT)
            if m is not None:
                out[guid] = Thing("spawn", a, m)
            continue
        if size >= SHAPE_POINTS_AT + 8 and (a + SHAPE_POINTS_AT) in part.pointers:
            arr = part.array_at(a + SHAPE_POINTS_AT)
            if arr is not None and arr.count >= 3:
                pts = np.frombuffer(part.data, dtype="<f4", count=4 * arr.count, offset=arr.offset).reshape(-1, 4)
                if np.all(np.isfinite(pts)):
                    t = Thing("shape", a, np.eye(4))
                    t.points = [[round(float(v), 2) for v in p[:3]] for p in pts]  # type: ignore[attr-defined]
                    out[guid] = t
    return out


def links(level: Bf6Level) -> list[tuple[tuple, int, tuple, int]]:
    """The gameplay sub-world's link connections: ((partition, instance) or ("local", offset), field) pairs."""
    gp = level.partition(level.prefix + "_layers_gameplay/gameplay")
    if gp is None:
        raise UnsupportedFrostbite("the level has no gameplay sub-world (`_layers_gameplay/gameplay`)")
    out = []
    for arr in gp.arrays:
        if arr.hash != LINK_ARRAY_HASH:
            continue
        for i in range(arr.count):
            o = arr.offset + LINK_SIZE * i

            def end(p):
                if p in gp.import_offsets:
                    what, index = gp.pointer(p)
                    if what == "import":
                        return gp.imports[index]
                (rel,) = struct.unpack_from("<i", gp.data, p)
                return ("local", p + rel)

            sf, tf = struct.unpack_from("<II", gp.data, o + 16)
            out.append((end(o), sf, end(o + 8), tf))
    return out


def gameplay_strings(level: Bf6Level) -> dict[int, str]:
    """The gameplay sub-world's names by their hash: a telemetry area's field id is its name's."""
    gp = level.partition(level.prefix + "_layers_gameplay/gameplay")
    if gp is None:
        return {}
    found = set(m.group(1).decode() for m in re.finditer(rb"([A-Za-z][A-Za-z0-9_]{1,40})\x00", gp.data))
    return {name_hash(s.encode()): s for s in found}


def build_mode(level: Bf6Level, mode: str, layer: str, all_links, strings, other_telemetry=()) -> dict | None:
    part = level.partition(layer)
    if part is None:
        return None
    things = read_layer(level, layer)
    if not things:
        return None
    me = part.guid

    def mine(end):
        return things.get(end[1]) if isinstance(end, tuple) and len(end) == 2 and end[0] == me else None

    caps = {g: t for g, t in things.items() if t.kind == "gem" and t.gem == "gem_capturepoint"}
    hqs = {g: t for g, t in things.items() if t.kind == "gem" and t.gem == "gem_hq"}
    spawners = {g: t for g, t in things.items() if t.kind == "gem" and t.gem in VEHICLE_GEMS}
    spawn_points = {g: t for g, t in things.items() if t.kind == "spawn"}
    # Who points to what: (source thing, field, target thing).
    edges = []
    telemetry: list[tuple[list, str]] = []
    for s, sf, t, tf in all_links:
        src = mine(s)
        if src is None:
            continue
        if src.kind == "gem" and src.gem == "gem_telemetryarea" and sf == F_TELEMETRY and tf in strings:
            telemetry.append((src.position, strings[tf]))
            continue
        dst = mine(t)
        if dst is not None:
            edges.append((src, sf, dst))
    objectives: list[dict] = []
    zones: list[dict] = []
    rec_of: dict[int, dict] = {}
    def letter_at(t: Thing) -> str:
        """The name of the telemetry area on a thing: this mode's within 60 m, else any mode's within 20 m."""
        for areas, reach in ((telemetry, 60.0), (other_telemetry, 20.0)):
            letter, best = "", reach
            for pos, nm in areas:
                m = TELEMETRY_NAME.match(nm)
                d = math.dist(pos, t.position)
                if m and d < best:
                    letter, best = m.group(1), d
            if letter:
                return letter
        return ""

    # Capture points, lettered by the telemetry area on them.
    for g, t in caps.items():
        letter = letter_at(t)
        rec = {"type": "capture_zone", "team": None, "letter": letter, "name": letter, "shape": "point",
               "position": t.position}
        for src, sf, dst in edges:
            if src is t and sf == F_CAPTURE_AREA and dst.kind == "shape":
                rec.update(shape="outline", points=dst.points)  # type: ignore[attr-defined]
                break
        objectives.append(rec)
        rec_of[id(t)] = rec
    # Combat areas, each team's or everyone's.
    seen_shapes = set()
    for src, sf, dst in edges:
        if src.kind == "gem" and src.gem == "gem_specialcombatarea" and sf == F_COMBAT_AREA and dst.kind == "shape":
            if id(dst) in seen_shapes:
                continue
            seen_shapes.add(id(dst))
            zones.append({"type": "play_area", "team": None, "shape": "outline", "points": dst.points})  # type: ignore[attr-defined]
    for g, t in hqs.items():
        rec = {"type": "base", "team": None, "letter": "", "name": "HQ", "shape": "point", "position": t.position}
        objectives.append(rec)
        rec_of[id(t)] = rec
    # Rush's M-COMs, lettered as the flags are (`RUSH_MCOM_B2`).
    for g, t in things.items():
        if t.kind == "gem" and t.gem == "gem_objective_mcom":
            letter = letter_at(t)
            rec = {"type": "objective", "kind": "mcom", "name": f"M-COM {letter}".strip(), "letter": letter, "team": None,
                   "position": t.position, "heading": t.heading, "prefab": t.gem}
            objectives.append(rec)
            rec_of[id(t)] = rec
    # Sectors (Breakthrough, Rush): a stage each, in the order of their flags' letters.
    sectors: dict[int, list[Thing]] = {}
    for src, sf, dst in edges:
        if src.kind == "gem" and src.gem == "gem_sector" and sf == F_OWNS and id(dst) in rec_of:
            sectors.setdefault(id(src), []).append(dst)
    if len(sectors) > 1:
        order = sorted(sectors.values(), key=lambda owned: min((rec_of[id(o)].get("letter") or "~") for o in owned))
        for stage, owned in enumerate(order, 1):
            for o in owned:
                rec_of[id(o)]["stage"] = stage
    # Spawns: whose list each is on, and the vehicle spawners each owns.
    spawns: list[dict] = []
    spawn_rec: dict[int, dict] = {}
    for g, t in list(spawn_points.items()) + list(spawners.items()):
        rec = {"type": "vehicle_spawn" if t.kind == "gem" else "spawn", "team": None,
               "position": t.position, "heading": t.heading}
        if t.kind == "gem":
            rec["vehicleClass"] = t.gem.replace("gem_", "")
            if VEHICLE_GEMS[t.gem]:
                rec["vehicleKind"] = VEHICLE_GEMS[t.gem]
        spawns.append(rec)
        spawn_rec[id(t)] = rec
    for src, sf, dst in edges:
        owner = rec_of.get(id(src))
        sp = spawn_rec.get(id(dst))
        if owner is None or sp is None:
            continue
        if dst.kind == "spawn" and sf not in (F_TEAM1_SPAWNS, F_TEAM2_SPAWNS, F_HQ_SPAWNS):
            continue
        if dst.kind == "gem" and sf != F_OWNS:
            continue
        if "_owner" not in sp:
            sp["_owner"], sp["_how"] = owner, "link"
        if sf == F_TEAM1_SPAWNS:
            sp["team"] = 1
        elif sf == F_TEAM2_SPAWNS:
            sp["team"] = 2 if sp.get("team") is None else sp["team"]
        elif owner.get("team") and not sp.get("team"):
            sp["team"] = owner["team"]
        if owner.get("stage") is not None and sp.get("stage") is None:
            sp["stage"] = owner["stage"]
    # A spawn on both teams' lists of a flag is whoever holds it: no team of its own.
    for src, sf, dst in edges:
        sp = spawn_rec.get(id(dst))
        if sp is not None and sf in (F_TEAM1_SPAWNS, F_TEAM2_SPAWNS):
            sp.setdefault("_lists", set()).add(sf)
    for sp in spawns:
        if len(sp.pop("_lists", ())) > 1:
            sp["team"] = None
    if not (objectives or zones or spawns):
        return None
    lay = _Shim(mode, objectives, zones, spawns)
    _finish(lay)
    return {
        "id": f"{mode}0",
        "name": MODE_NAMES.get(mode, mode.replace("mp_", "").replace("_", " ").title()),
        "mode": f"{mode}0",
        "objectives": lay.objectives,
        "zones": lay.zones,
        "spawns": lay.spawns,
        **({"spawnsDropped": lay.dropped} if lay.dropped else {}),
    }


@dataclass
class _Shim:
    """The parts of a legacy `Layout` that `_finish_spawns` reads."""

    mode: str
    objectives: list
    zones: list
    spawns: list
    dropped: dict = field(default_factory=dict)


def _finish(lay: _Shim) -> None:
    for o in lay.objectives:
        o.setdefault("id", "")
    for sp in lay.spawns:
        if "_owner" in sp:
            sp["base"] = True
    _finish_spawns(lay)  # type: ignore[arg-type]
    # Stable ids first in the records, as the legacy layouts have them.
    lay.objectives = [{"id": o.pop("id"), **o} for o in lay.objectives]


def build_layouts(catalogue, prefix: str, level_name: str, game: str, version: str, log=print) -> dict:
    level = Bf6Level(catalogue, prefix)
    all_links = links(level)
    strings = gameplay_strings(level)
    # Every mode's telemetry areas: a mode without its own letters its flags by another's on the same spot.
    everyone = []
    for layer in level.mode_layers().values():
        part = level.partition(layer)
        if part is None:
            continue
        things = read_layer(level, layer)
        for s, sf, t, tf in all_links:
            if sf == F_TELEMETRY and tf in strings and isinstance(s, tuple) and s[0] == part.guid:
                th = things.get(s[1])
                if th is not None:
                    everyone.append((th.position, strings[tf]))
    layouts = []
    for mode, layer in level.mode_layers().items():
        try:
            lay = build_mode(level, mode, layer, all_links, strings, everyone)
        except (UnsupportedFrostbite, ValueError, IndexError, KeyError, struct.error) as exc:
            log(f"   {mode}: failed ({exc})")
            continue
        if lay is None:
            continue
        caps = sum(o["type"] == "capture_zone" for o in lay["objectives"])
        linked = sum(1 for s in lay["spawns"] if s.get("baseSource") == "link")
        log(f"   {lay['mode']}: {caps} capture points, {len(lay['zones'])} areas, {len(lay['spawns'])} spawns "
            f"({linked} linked)")
        layouts.append(lay)
    return {
        "format": FORMAT,
        "version": 1,
        "game": game,
        "level": level_name,
        "source": f"heat3d-battlefield-maps {version}",
        "units": "m",
        "up": "y",
        "layouts": layouts,
    }
