"""
What each game mode of a Battlefield 4 or Battlefield 1 level is played
over: capture points and headquarters, objectives (Rush's M-COMs,
Obliteration's bomb sites and the like), each team's combat area, and the
spawn points, a layout per mode, in the level's own coordinates (the same
as the `.glb` the `level` verb writes).

How a mode is put together
--------------------------
A level is a tree of sub-levels (`SubWorldReferenceObjectData` naming a
bundle); a sub-level that belongs to some modes only says which in its
inclusion settings (`EnabledOptions`: `ConquestLarge0`, `RushLarge0`...).
For one mode the reader walks the sub-levels that mode loads, their layers
(`WorldPartData`) and the prefabs placed in them (any reference with a
`Blueprint`), with the transforms composed on the way down.

A prefab is placed once and given its values from outside: the sub-level's
`PropertyConnections` connect a field of its interface (whose values the
sub-level stores, `InterfaceDescriptorData.Fields`) to a field of an object
inside it, the same again one prefab further down. Values are looked up that
way, outermost first: a capture point's radius, a Rush base's objectives'
places (their `BlueprintTransform`). Pointers go the same way through the
`LinkConnections`: a combat area's shape, the spawns a capture point owns.

What is read
------------
- `CapturePointEntityData`: a capture point where it is placed; one with an
  initial owner team is that team's headquarters. Its radius
  (`CaptureRadius`), letter (from its prefab's name or a one-letter value of
  its interface) and name (the localisation id's tail, `ID_CAP_STORAGE` ->
  `Storage`).
- `CombatAreaTriggerEntityData`: each team's combat area, the polygons
  (`VolumeVectorShapeData`) it is linked to. Outside it a team is out of
  bounds.
- `AlternateSpawnEntityData` and `CharacterSpawnReferenceObjectData`:
  soldier spawn points, with their team or, for a capture point's spawns,
  the capture point's letter.
- `VehicleSpawnReferenceObjectData`: vehicle spawns, with the vehicle.
- Objectives: prefabs whose names say what they are (`objective`, `mcom`,
  `bombsite`, `ctf`...), where they are placed.

Rush and Breakthrough come in stages: whatever sits in a layer named for a
stage (`..._base3`) carries that stage, and an objective takes the stage of
the defenders' area it is in.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .frostbite import UnsupportedFrostbite
from .legacyebx import Import, Instance, Partition, Ref, name_hash
from .legacylevel import World, level_root

FORMAT = "3dheat-layouts"


def field_id(name: str) -> int:
    """A field's id in the connections: its name's hash, as a signed 32-bit number."""
    h = name_hash(name.encode())
    return h - (1 << 32) if h >= 1 << 31 else h


F_TRANSFORM = field_id("BlueprintTransform")
F_OWN_TRANSFORM = field_id("Transform")
F_TEAM = field_id("Team")
F_OWNER = field_id("InitialOwnerTeam")
F_RADIUS = field_id("CaptureRadius")
F_ENABLED = field_id("Enabled")
F_CAPTURE_AREA = field_id("CaptureArea")
F_VEHICLE = field_id("Vehicle")
F_ALTERNATIVES = field_id("AlternativeSpawnPoints")

#: A vehicle spawner prefab's name says what it spawns: `spawnerprefab_tank_mbt`, `outpostspawn_jet_attack`.
SPAWNER = re.compile(r"(?:spawnerprefab|outpostspawn|vehiclespawner|spawner)_([a-z0-9]+(?:_[a-z0-9]+)*?)(?:_(?:neutral|us|ru|cn|team\d)|_nongroupable.*|_autogen.*|_win32)*$", re.I)
#: Names that say nothing of the vehicle.
SPAWNER_GENERIC = {"fill", "cycle", "spec", "base", "generic", "logic", "default"}

#: A vehicle's class by the words of its blueprint's name, first match wins.
VEHICLE_WORDS = (
    (r"jet(?!ski)|_f35|_f18|_su\d|_j20|_a10|su25|q5|fighter|attack_jet|stealth", "jet"),
    (r"heli|_ah\d|_z10|_mi\d|_ka\d|_uh\d|venom|littlebird|ah6|z11|_scout", "helicopter"),
    (r"plane|bomber|airship|zeppelin|biplane|aircraft", "plane"),
    (r"boat|rhib|pwc|jetski|ship|destroyer|dv15|patrol", "boat"),
    (r"tank|_mbt|m1a|t90|t\d\d|type99|ft17|mk[ivx]+|a7v|landship|_ht\d|_heavy_tank|_light_tank|ifv|_bmp|_lav|zbd|aa_tank|apc|btr|_m113", "tank"),
    (r"static|_mg|tow|aa_|stationary|mortar|artillery|coastal|gunshield|_aa$|field_gun|fieldgun|_turret|emplacement", "stationary"),
    (r"horse|cavalry", "horse"),
    (r"car|jeep|quad|bike|truck|humvee|vodnik|dpv|mrap|growler|_ltv|motorcycle|armored_car|_ac_", "car"),
)

#: A schematic channel for one capture point (Battlefield 1): `conquest_flage_hub` is E's.
FLAG_HUB = re.compile(r"flag_?([a-z])_hub$", re.I)
#: A team's channel (`conquest_team1_hub`): what it points to is that team's headquarters'.
TEAM_HUB = re.compile(r"team_?(\d)_hub$", re.I)
#: A Breakthrough sector's channel (`breakthrough_sector2_hub`): the spawns of that stage.
SECTOR_HUB = re.compile(r"(?:sector|stage|base)_?(\d+)_hub$", re.I)

#: The modes each kind of objective is played in; a kind not listed is kept in every mode.
KIND_MODES = {
    "mcom": re.compile(r"rush|elimination|defuse", re.I),
    "telegraph": re.compile(r"rush", re.I),
    "bomb_target": re.compile(r"obliteration", re.I),
    "flag": re.compile(r"capturetheflag|ctf", re.I),
    "pigeon": re.compile(r"possession|pigeon", re.I),
}

#: The words a mode's name is made of: a setting whose options have none is not about modes.
MODE_WORDS = re.compile(
    r"conquest|rush|deathmatch|domination|obliteration|elimination|gunmaster|capturetheflag|"
    r"airsuperiority|carrier|chainlink|squad|operation|breakthrough|possession|tugofwar|"
    r"frontline|warpigeon|pigeon|defuse|scavenger|teamdeath|tdm|bfh|heist|bloodmoney|hotwire|"
    r"hostage|crosshair|bounty|shocktroop|incursion|mixed|airassault|assault|warfare",
    re.I,
)

#: Prefabs that are objectives, by what their names say.
OBJECTIVE = re.compile(
    r"(rush_base_objective|rush_objective$|_objective$|mcom|bombsite|bomb_site|bombdropoff|"
    r"ctf_flag|flagbase|ctf_base|satcom|telegraph|pigeon|defuse|carrierassault_.*(silo|target)|"
    r"missile_?silo|arty_target)",
    re.I,
)

#: Prefabs not walked into: vehicles, soldiers, effects, sound, UI, cameras.
NOT_GAMEPLAY = re.compile(
    r"^(vehicles|characters|weapons|fx|sound|ui|audio|music|levels/frontend)/|/(vo_|music|sound|ui_)|"
    r"customcamera|killer_camera|spectator",
    re.I,
)

#: A layer for a Rush or Breakthrough stage: `layer3_rushlarge0_base3`, `..._sector2`.
STAGE = re.compile(r"(?:base|sector|stage|phase)_?(\d+)", re.I)

IDENTITY = np.eye(4)


def _matrix(values) -> np.ndarray | None:
    if values is None:
        return None
    m = np.asarray(values, np.float64)
    if m.size != 16:
        return None
    m = m.reshape(4, 4).copy()
    m[:, 3] = (0, 0, 0, 1)
    return m


def _transform_text(text: str) -> np.ndarray | None:
    """`LinearTransform ((r),(u),(f),(t))` as a 4x4 row-vector matrix."""
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)]
    if len(nums) != 12:
        return None
    m = np.eye(4)
    m[:4, :3] = np.asarray(nums, np.float64).reshape(4, 3)
    return m


def interface_value(text):
    """An interface field's stored value (`Float32 15`, `CString "B"`, `LinearTransform (...)`) as a Python value."""
    if not isinstance(text, str):
        return None
    kind, _, rest = text.partition(" ")
    rest = rest.strip()
    if kind == "LinearTransform":
        return _transform_text(rest)
    if kind == "CString":
        return rest[1:-1] if rest.startswith('"') and rest.endswith('"') else rest
    if kind == "Boolean":
        return rest == "True"
    if kind in ("Float32", "Float64"):
        try:
            return float(rest)
        except ValueError:
            return None
    if kind == "TeamId":
        m = re.search(r"(\d+)", rest)
        return int(m.group(1)) if m else 0
    if kind.startswith(("Int", "Uint")):
        try:
            return int(float(rest))
        except ValueError:
            return None
    return rest


def _key(part: Partition, inst: Instance) -> tuple:
    return (part.guid, inst.guid if inst.guid else inst.index)


def _end(part: Partition, value) -> tuple | None:
    if isinstance(value, Ref):
        return _key(part, part.instances[value.index])
    if isinstance(value, Import):
        return (value.partition, value.instance)
    return None


@dataclass
class Context:
    """One placed blueprint (a sub-level or a prefab): its connections and where it is."""

    part: Partition
    root: Instance
    parent: "Context | None"
    #: The reference that placed it, by key in the parent.
    via: tuple | None
    transform: np.ndarray
    name: str
    stage: int | None = None
    #: Whether the level put it where it is (a spare of a prefab sits at the prefab's own place).
    placed: bool = False
    links: dict = field(default_factory=dict)
    #: The same links by their target: (target, field) -> [(source, field)].
    rlinks: dict = field(default_factory=dict)
    props: dict = field(default_factory=dict)
    iface: tuple | None = None
    defaults: dict = field(default_factory=dict)
    #: The blueprints placed here, by the key of the reference that placed them.
    children: dict = field(default_factory=dict)

    def __post_init__(self):
        for c in self.root.get("LinkConnections") or []:
            s, t = _end(self.part, c.get("Source")), _end(self.part, c.get("Target"))
            if s and t:
                self.links.setdefault((s, c.get("SourceFieldId")), []).append((t, c.get("TargetFieldId")))
                self.rlinks.setdefault((t, c.get("TargetFieldId")), []).append((s, c.get("SourceFieldId")))
        for c in self.root.get("PropertyConnections") or []:
            s, t = _end(self.part, c.get("Source")), _end(self.part, c.get("Target"))
            if s and t:
                self.props[(t, c.get("TargetFieldId"))] = (s, c.get("SourceFieldId"))
        iface = self.root.get("Interface")
        if isinstance(iface, Ref):
            inst = self.part.instances[iface.index]
            self.iface = _key(self.part, inst)
            for f in inst.get("Fields") or []:
                if isinstance(f, dict) and f.get("Value") is not None:
                    self.defaults[f.get("Id")] = interface_value(f.get("Value"))

    @property
    def is_level(self) -> bool:
        return self.root.type in ("SubWorldData", "LevelData", "WorldPartData")

    def interface(self, fid):
        """An interface field's value: from outside where the parent connects it, else stored here."""
        return self.interface_from(fid)[0]

    def interface_from(self, fid):
        """(value, the blueprint it is stored in) of an interface field."""
        if self.parent is not None and self.via is not None:
            got = self.parent.value_from(self.via, fid)
            if got[0] is not None:
                return got
        v = self.defaults.get(fid)
        return (v, self) if v is not None else (None, None)

    def value(self, key: tuple, fid):
        """The value an object here is given for a field from outside, or None."""
        return self.value_from(key, fid)[0]

    def value_from(self, key: tuple, fid):
        src = self.props.get((key, fid))
        if src is None or src[0] != self.iface:
            return (None, None)
        return self.interface_from(src[1])

    def strings(self) -> list[str]:
        """The text values of this blueprint's interface and the ones above it."""
        out = []
        ctx = self
        while ctx is not None:
            out += [v for v in ctx.defaults.values() if isinstance(v, str)]
            ctx = ctx.parent
        return out


@dataclass
class Layout:
    mode: str
    objectives: list = field(default_factory=list)
    zones: list = field(default_factory=list)
    spawns: list = field(default_factory=list)
    #: (context, combat area instance, team) to resolve once everything is walked.
    areas: list = field(default_factory=list)
    #: capture point key -> its record, and (context, key) of each, for the spawns it owns.
    captures: list = field(default_factory=list)
    spawn_at: dict = field(default_factory=dict)
    seen: set = field(default_factory=set)
    shape_stage: dict = field(default_factory=dict)
    #: (context, channel key, letter) of each capture point's schematic channel.
    hubs: list = field(default_factory=list)
    #: vehicle spawner key -> its record; seats (soldier spawns into a vehicle) waiting for theirs.
    vehicle_at: dict = field(default_factory=dict)
    #: (context, key) of each Battlefield 1 team channel, with its team and stage.
    team_hubs: list = field(default_factory=list)
    #: (context, key, stage) of each Battlefield 1 Breakthrough sector channel.
    sector_hubs: list = field(default_factory=list)
    #: (seat, vehicle spawner) pairs of Battlefield 1's deploy entries.
    seat_of: list = field(default_factory=list)
    ids: set = field(default_factory=set)
    #: Spawns left out, by why.
    dropped: dict = field(default_factory=dict)
    #: (context, key) of the sub-level references this mode leaves out.
    excluded: set = field(default_factory=set)
    vehicle_pending: dict = field(default_factory=dict)
    #: (context, key, record) of every spawn, soldier and vehicle, for linking them to what owns them.
    spawn_info: list = field(default_factory=list)


def _pos(m: np.ndarray) -> list[float]:
    return [round(float(v), 2) for v in m[3, :3]]


def _heading(m: np.ndarray) -> float:
    """Degrees from +z towards +x of the forward (third) row."""
    f = m[2, :3]
    return round(math.degrees(math.atan2(float(f[0]), float(f[2]))) % 360.0, 1)


def _letter(blueprint: str, strings: list[str]) -> str:
    m = re.search(r"_([a-h])(?:_short|_long|_var\d*)?$", blueprint, re.I)
    if m:
        return m.group(1).upper()
    for s in strings:
        if re.fullmatch(r"[A-H]", s or ""):
            return s
    return ""


def _nice_name(sid: str) -> str:
    """`ID_CAP_MACHINE_ROOM` -> `Machine Room`."""
    tail = re.sub(r"^(ID_)?(MP_)?(CAP|CP|OBJ|SID|LOC|BASE)_", "", sid or "", flags=re.I)
    tail = re.sub(r"^[A-Z0-9]+_(?=[A-Z])", "", tail) if tail.count("_") > 2 else tail
    return " ".join(w.capitalize() for w in tail.split("_") if w)


class Walker:
    def __init__(self, world: World):
        self.world = world

    # -- the sub-levels and the modes -------------------------------------

    def _settings_modes(self, part: Partition, ref: Instance) -> list[list[str]]:
        """Each inclusion setting's options of a sub-level reference that are about modes."""
        out = []
        settings = part.resolve(ref.get("InclusionSettings"))
        if isinstance(settings, Instance):
            for s in settings.get("Settings") or []:
                s = part.resolve(s)
                if isinstance(s, Instance):
                    opts = [o for o in s.get("EnabledOptions") or [] if isinstance(o, str)]
                    # A setting that enables nothing (a mode left out of this level) includes it in no mode.
                    if not opts or any(MODE_WORDS.search(o) for o in opts):
                        out.append(opts)
        return out

    def modes(self) -> list[str]:
        """Every mode some sub-level of the level is included for."""
        found: list[str] = []
        seen_parts: set[str] = set()

        def visit(name: str, depth: int):
            if depth > 8 or name.lower() in seen_parts:
                return
            seen_parts.add(name.lower())
            part = self.world.partition(name)
            if part is None:
                return
            for inst in part.instances:
                if inst.type == "SubWorldReferenceObjectData" and inst.get("BundleName"):
                    for opts in self._settings_modes(part, inst):
                        for o in opts:
                            if o not in found:
                                found.append(o)
                    visit(inst["BundleName"], depth + 1)

        visit(level_root(self.world), 0)
        return found

    def _included(self, part: Partition, ref: Instance, mode: str) -> bool:
        if ref.get("IsWin32SubLevel", True) is False:
            return False
        return all(mode in opts for opts in self._settings_modes(part, ref))

    # -- one mode -----------------------------------------------------------

    def layout(self, mode: str) -> Layout:
        out = Layout(mode)
        root = self.world.partition(level_root(self.world))
        if root is None or not root.instances:
            raise UnsupportedFrostbite("the level partition does not read")
        ctx = Context(root, root.instances[0], None, None, IDENTITY, "level")
        self._walk_blueprint(ctx, mode, out, 0)
        self._resolve(out)
        return out

    def _objects(self, ctx: Context):
        """
        (partition, instance, transform, stage) of every object a blueprint
        places, its layers' included: what its `Objects` list and every other
        instance of the partition (spawns and shapes that only connections
        point to are in no list).
        """
        def layer(part: Partition, root: Instance, m: np.ndarray, stage, depth: int):
            listed = []
            for item in root.get("Objects") or []:
                got = self.world.resolve(part, item)
                if got:
                    listed.append(got)
            ids = {id(i) for _, i in listed}
            listed += [(part, i) for i in part.instances if i is not root and id(i) not in ids]
            done = set()
            for p, obj in listed:
                if id(obj) in done:
                    continue
                done.add(id(obj))
                if obj.type == "WorldPartReferenceObjectData" and depth < 4:
                    sub = self.world.resolve(p, obj.get("Blueprint"))
                    if sub and sub[0] is not part:
                        t = _matrix(obj.get("BlueprintTransform"))
                        st = STAGE.search(str(sub[1].get("Name") or ""))
                        yield from layer(sub[0], sub[1], (t if t is not None else IDENTITY) @ m,
                                         int(st.group(1)) if st else stage, depth + 1)
                    continue
                yield p, obj, m, stage

        yield from layer(ctx.part, ctx.root, ctx.transform, ctx.stage, 0)

    def _walk_blueprint(self, ctx: Context, mode: str, out: Layout, depth: int) -> None:
        if depth > 10:
            return
        for part, obj, m, stage in self._objects(ctx):
            key = _key(part, obj)
            t = obj.type
            if t == "SubWorldReferenceObjectData":
                if not obj.get("BundleName") or not self._included(part, obj, mode):
                    out.excluded.add((id(ctx), key))
                    continue
                sub = self.world.partition(obj["BundleName"])
                if sub is None or not sub.instances or sub.guid == ctx.part.guid:
                    continue
                own = _matrix(obj.get("BlueprintTransform"))
                child = Context(sub, sub.instances[0], ctx, key, (own if own is not None else IDENTITY) @ m,
                                obj["BundleName"].rsplit("/", 1)[-1])
                ctx.children[key] = child
                self._walk_blueprint(child, mode, out, depth + 1)
                continue
            if t == "AlternateSpawnEntityData":
                if any(t2 == key and sf == F_ALTERNATIVES for (t2, _), srcs in ctx.rlinks.items() for _, sf in srcs):
                    # Where a vehicle spawner puts the soldier when its vehicle cannot spawn: the vehicle's.
                    out.dropped["a vehicle's alternative spawn point"] = out.dropped.get("a vehicle's alternative spawn point", 0) + 1
                    continue
                own = ctx.value(key, F_OWN_TRANSFORM)
                own = own if isinstance(own, np.ndarray) else _matrix(obj.get("Transform"))
                w = (own if own is not None else IDENTITY) @ m
                team = ctx.value(key, F_TEAM)
                team = int(team if team is not None else obj.get("Team", 0) or 0)
                rec = {"type": "spawn", "team": team or None, "position": _pos(w), "heading": _heading(w)}
                if stage is not None:
                    rec["stage"] = stage
                out.spawns.append(rec)
                out.spawn_at[(id(ctx), key)] = rec
                out.spawn_info.append((ctx, key, rec))
                continue
            if t == "CapturePointEntityData":
                self._capture(ctx, key, obj, m, out)
                continue
            if t == "SchematicChannelEntityData":
                channel = obj.get("Channel")
                name = self.world.name_of(channel.partition) if isinstance(channel, Import) else None
                hub = FLAG_HUB.search(name or "")
                if hub:
                    out.hubs.append((ctx, key, hub.group(1).upper()))
                team_hub = TEAM_HUB.search(name or "")
                if team_hub:
                    out.team_hubs.append((ctx, key, int(team_hub.group(1)), stage))
                sector = SECTOR_HUB.search(name or "")
                if sector:
                    out.sector_hubs.append((ctx, key, int(sector.group(1))))
                continue
            if t == "BFSoldierSpawnEntityData":
                # Battlefield 1's deploy-screen entry for a vehicle: what owns it owns the vehicle.
                for target, _ in ctx.links.get((key, F_VEHICLE), []):
                    out.seat_of.append(((id(ctx), key), (id(ctx), target)))
                continue
            if t == "VolumeVectorShapeData":
                if stage is not None:
                    out.shape_stage[key] = stage
                continue
            if t == "CombatAreaTriggerEntityData":
                team = ctx.value(key, F_TEAM)
                team = int(team if team is not None else obj.get("Team", 0) or 0)
                out.areas.append((ctx, key, team, stage))
                continue
            if not t.endswith("ReferenceObjectData") or obj.get("Excluded"):
                continue
            if t in ("VehicleSpawnReferenceObjectData", "CharacterSpawnReferenceObjectData"):
                self._spawner(ctx, part, obj, key, m, stage, out)
                continue
            got = self.world.resolve(part, obj.get("Blueprint"))
            if not got:
                continue
            bp_part, bp = got
            bp_name = str(self.world.name_of(bp_part.guid) or bp.get("Name") or "").lower()
            given, origin = ctx.value_from(key, F_TRANSFORM)
            own = given if isinstance(given, np.ndarray) else _matrix(obj.get("BlueprintTransform"))
            w = (own if own is not None else IDENTITY) @ m
            if isinstance(given, np.ndarray):
                placed = origin is not None and origin.is_level
            else:
                placed = ctx.placed or ctx.is_level
            if NOT_GAMEPLAY.search(bp_name):
                continue
            if OBJECTIVE.search(bp_name) and placed:
                kind, label = objective_kind(bp_name.rsplit("/", 1)[-1])
                if kind == "mcom" and self.world.install.generation == "bf1":
                    kind, label = "telegraph", "Telegraph"
                rec = {"type": "objective", "kind": kind, "name": label, "team": None,
                       "position": _pos(w), "heading": _heading(w), "prefab": bp_name.rsplit("/", 1)[-1]}
                owner = ctx.value(key, F_TEAM)
                named = re.search(r"team_?(\d)", bp_name)
                if isinstance(owner, int) and owner:
                    rec["team"] = owner
                elif named:
                    rec["team"] = int(named.group(1))
                if stage is not None:
                    rec["stage"] = stage
                dedup = ("o", tuple(round(v) for v in rec["position"]))
                if dedup not in out.seen:
                    out.seen.add(dedup)
                    out.objectives.append(rec)
                continue
            if bp.type not in ("SpatialPrefabBlueprint", "LogicPrefabBlueprint", "PrefabBlueprint",
                               "SubWorldData", "WorldPartData"):
                continue
            child = Context(bp_part, bp, ctx, key, w, bp_name, stage, placed)
            ctx.children[key] = child
            self._walk_blueprint(child, mode, out, depth + 1)

    def _spawner(self, ctx: Context, part: Partition, obj: Instance, key, m: np.ndarray, stage, out: Layout) -> None:
        """
        A soldier's or a vehicle's spawn point. A vehicle spawner's vehicle is
        often given from outside (no `Blueprint` of its own): then its kind
        is the spawner prefab's (`spawnerprefab_tank_mbt` -> `tank_mbt`). A
        soldier spawn whose `Vehicle` points to a vehicle spawner is that
        vehicle's seat on the deploy screen: it stands for the vehicle, so
        what owns it (a capture point's links) owns the vehicle.
        """
        given, _ = ctx.value_from(key, F_TRANSFORM)
        own = given if isinstance(given, np.ndarray) else _matrix(obj.get("BlueprintTransform"))
        w = (own if own is not None else IDENTITY) @ m
        team = ctx.value(key, F_TEAM)
        team = int(team if isinstance(team, (int, float)) else obj.get("Team", 0) or 0)
        got = self.world.resolve(part, obj.get("Blueprint")) if obj.get("Blueprint") is not None else None
        bp_name = str(self.world.name_of(got[0].guid) or got[1].get("Name") or "").lower() if got else ""
        here = id(ctx)
        if obj.type == "CharacterSpawnReferenceObjectData":
            seat = [t for t, _ in ctx.links.get((key, F_VEHICLE), []) if (here, t) in out.vehicle_at or self._is_vehicle(ctx, t)]
            if not seat and not any(s == key for s, _ in ctx.links):
                # A soldier spawn with no links of its own beside the one vehicle spawner of its prefab: that vehicle's seat.
                vs = [_key(ctx.part, i) for i in ctx.part.instances if i.type == "VehicleSpawnReferenceObjectData"]
                if len(vs) == 1 and key[0] == ctx.part.guid:
                    seat = vs
            if seat:
                rec = out.vehicle_at.get((here, seat[0]))
                if rec is None:
                    out.vehicle_pending.setdefault((here, seat[0]), []).append(key)
                else:
                    out.spawn_at[(here, key)] = rec
                return
            rec = {"type": "spawn", "team": team or None, "position": _pos(w), "heading": _heading(w)}
        else:
            if got and "vehicles/" not in bp_name:
                return
            rec = {"type": "vehicle_spawn", "team": team or None, "position": _pos(w), "heading": _heading(w)}
            if bp_name:
                rec["vehicle"] = bp_name.rsplit("/", 1)[-1]
            kind = vehicle_class(ctx)
            if kind:
                rec["vehicleClass"] = kind
            what = vehicle_class_of(kind) or vehicle_class_of(bp_name)
            if what:
                rec["vehicleKind"] = what
            out.vehicle_at[(here, key)] = rec
            for seat in out.vehicle_pending.pop((here, key), []):
                out.spawn_at[(here, seat)] = rec
        if stage is not None:
            rec["stage"] = stage
        out.spawns.append(rec)
        out.spawn_at[(here, key)] = rec
        out.spawn_info.append((ctx, key, rec))

    @staticmethod
    def _is_vehicle(ctx: Context, key) -> bool:
        return key[0] == ctx.part.guid and any(
            _key(ctx.part, i) == key and i.type == "VehicleSpawnReferenceObjectData" for i in ctx.part.instances
        )

    def _capture(self, ctx: Context, key, obj: Instance, m: np.ndarray, out: Layout) -> None:
        if not (ctx.placed or ctx.is_level):
            return
        own = ctx.value(key, F_OWN_TRANSFORM)
        own = own if isinstance(own, np.ndarray) else _matrix(obj.get("Transform"))
        w = (own if own is not None else IDENTITY) @ m
        owner = ctx.value(key, F_OWNER)
        owner = int(owner if owner is not None else obj.get("InitialOwnerTeam", 0) or 0)
        radius = None
        # The radius: given from outside to this prefab or one around it, else its own.
        c = ctx
        while c is not None and radius is None:
            got = None
            if c.via is not None and c.parent is not None:
                got = c.parent.value(c.via, F_RADIUS)
            if isinstance(got, (int, float)) and got > 0:
                radius = float(got)
            c = c.parent
        own_r = ctx.value(key, F_RADIUS)
        if radius is None and isinstance(own_r, (int, float)) and own_r > 0:
            radius = float(own_r)
        if radius is None and float(obj.get("CaptureRadius", 0) or 0) > 0:
            radius = float(obj["CaptureRadius"])
        # The prefab that names it: the nearest one above with a capture point's name.
        names = []
        c = ctx
        while c is not None:
            names.append(c.name)
            c = c.parent
        blueprint = next((n for n in names if re.search(r"capture|cp_|_cp|flag|base|hq", n.split("/")[-1])), names[0])
        strings = ctx.strings()
        # A headquarters or a spawn base by its prefab's name; a capture point
        # can start out held (Breakthrough's sectors), and stays a capture point.
        hq = any(re.search(r"(^|[/_])hq|spawn|_base_|base_team|baseteam", n.split("/")[-1]) for n in names[:4])
        if not hq:
            start, owner = owner, 0
        else:
            start = owner
        letter = "" if owner else _letter(blueprint.split("/")[-1].replace("_flagpole", "").replace("_generic", ""), strings)
        if not letter:
            for n in names:
                letter = _letter(n.split("/")[-1], [])
                if letter:
                    break
        given = self._given(ctx)
        sid = next((s for s in given if re.match(r"^ID_(CAP|CP|LOC|OBJ|MP_CAP|BASE)_", s or "", re.I)), "")
        rec = {
            "type": "base" if owner else "capture_zone",
            "team": owner or None,
            "letter": "" if owner else letter,
            "name": "HQ" if owner else (_nice_name(sid) if sid else letter),
            "shape": "cylinder" if radius and radius > 1.5 else "point",
            "position": _pos(w),
        }
        if start and not owner:
            rec["ownerAtStart"] = start
        if radius and radius > 1.5:
            rec["radius"] = round(radius, 2)
            rec["height"] = 0
        if ctx.stage is not None:
            rec["stage"] = ctx.stage
        dedup = ("c", rec["type"], tuple(round(v) for v in rec["position"]))
        if dedup in out.seen:
            return
        out.seen.add(dedup)
        # An id the spawns name their owner by: the letter, `HQ1`, with the stage (`HQ2#3`) where staged.
        ident = rec["letter"] or (f"HQ{owner}" if owner else rec["name"]) or "CP"
        if ctx.stage is not None:
            ident = f"{ident}#{ctx.stage}"
        n, base_id = 1, ident
        while ident in out.ids:
            n += 1
            ident = f"{base_id}-{n}"
        out.ids.add(ident)
        rec = {"id": ident, **rec}
        out.objectives.append(rec)
        out.captures.append((ctx, rec))

    @staticmethod
    def _given(ctx: Context) -> list[str]:
        """The texts given from outside to the prefabs around a capture point, nearest first."""
        out = []
        c = ctx
        while c is not None and c.parent is not None and c.via is not None:
            for (target, fid) in c.parent.props:
                if target == c.via:
                    v = c.parent.value(c.via, fid)
                    if isinstance(v, str):
                        out.append(v)
            c = c.parent
        return out

    # -- the links, once everything is walked --------------------------------

    def _follow(self, ctx: Context, src: tuple, fid, depth: int = 0) -> list[tuple]:
        """
        (context, key) of what a pointer field leads to, out through the
        interfaces it passes: the context tells apart the copies of a prefab
        placed more than once (their objects have the same keys).
        """
        if depth > 12:
            return []
        out = []
        for target, tf in ctx.links.get((src, fid), []):
            if target == ctx.iface:
                # Out through this blueprint's interface: on in the one that placed it.
                if ctx.parent is not None and ctx.via is not None:
                    out += self._follow(ctx.parent, ctx.via, tf, depth + 1)
            elif tf and target in ctx.children:
                # Into a blueprint placed here, through its interface.
                child = ctx.children[target]
                out += self._follow(child, child.iface, tf, depth + 1)
            else:
                out.append((ctx, target))
        return out

    def _all_links(self, ctx: Context, src: tuple) -> list[tuple]:
        out = []
        for (s, fid) in list(ctx.links):
            if s == src:
                out += self._follow(ctx, s, fid)
        return out

    def _shape(self, key: tuple) -> np.ndarray | None:
        name = self.world.name_of(key[0])
        part = self.world.partition(name) if name else None
        if part is None:
            return None
        for inst in part.instances:
            if _key(part, inst) == key and inst.type == "VolumeVectorShapeData":
                pts = inst.get("Points")
                if isinstance(pts, np.ndarray) and pts.size >= 9:
                    return pts.reshape(-1, pts.shape[-1] if pts.ndim == 2 else 4)[:, :3].astype(np.float64)
                if isinstance(pts, list) and len(pts) >= 3:
                    return np.asarray([[p.get("x", 0), p.get("y", 0), p.get("z", 0)] if isinstance(p, dict) else list(p)[:3] for p in pts], np.float64)
        return None

    def _resolve(self, out: Layout) -> None:
        seen_shapes: set = set()
        for ctx, key, team, stage in out.areas:
            for _, target in self._all_links(ctx, key):
                pts = self._shape(target)
                if pts is None:
                    continue
                stage = out.shape_stage.get(target, stage)
                sig = (team, stage, target)
                if sig in seen_shapes:
                    continue
                seen_shapes.add(sig)
                rec = {
                    "type": "play_area",
                    "team": team or None,
                    "shape": "outline",
                    "points": [[round(float(v), 2) for v in p] for p in pts],
                }
                if stage is not None:
                    rec["stage"] = stage
                out.zones.append(rec)
        # Battlefield 1's deploy entries stand for their vehicles.
        for seat, vehicle in out.seat_of:
            if vehicle in out.spawn_at:
                out.spawn_at[seat] = out.spawn_at[vehicle]
        # A vehicle spawner's alternative spawn points (`AlternativeSpawnPoints`) are where it puts the
        # soldier when the vehicle cannot spawn: the vehicle's, not spawns of their own.
        alternates = set()
        for ctx, key, rec in out.spawn_info:
            if rec["type"] != "vehicle_spawn":
                continue
            for tctx, target in self._follow(ctx, key, F_ALTERNATIVES):
                sp = out.spawn_at.get((id(tctx), target))
                if sp is not None and sp is not rec and sp["type"] == "spawn":
                    alternates.add(id(sp))
                    out.spawn_at[(id(tctx), target)] = rec
        if alternates:
            out.spawns = [sp for sp in out.spawns if id(sp) not in alternates]
            out.spawn_info = [i for i in out.spawn_info if id(i[2]) not in alternates]
            out.dropped["a vehicle's alternative spawn point"] = len(alternates)
        # A capture point's spawns: what the prefab placed in the sub-level points to.
        owners: dict[int, dict] = {}
        for ctx, rec in out.captures:
            c = ctx
            while c.parent is not None and c.parent.root.type not in ("SubWorldData", "LevelData"):
                c = c.parent
            if c.parent is None or c.via is None:
                continue
            for tctx, target in self._all_links(c.parent, c.via):
                sp = out.spawn_at.get((id(tctx), target))
                if sp is not None:
                    _own(sp, rec, "link")
            owners[id(c)] = rec
        # A spawn placed inside a capture point's prefab is that capture point's.
        for ctx, key, sp in out.spawn_info:
            if "base" in sp:
                continue
            c = ctx
            while c is not None and id(c) not in owners:
                c = c.parent
            if c is not None:
                _own(sp, owners[id(c)], "prefab")
        # Battlefield 1: each capture point's area is a polygon its letter's
        # channel points to; a capture point in none is a spare one of the prefab.
        letters: dict[str, list] = {}
        for ctx, key, letter in out.hubs:
            for _, target in self._follow(ctx, key, F_CAPTURE_AREA):
                pts = self._shape(target)
                if pts is not None and letter not in letters:
                    letters[letter] = [[round(float(v), 2) for v in p] for p in pts]
        if letters:
            kept = []
            for o in out.objectives:
                if o["type"] != "capture_zone":
                    kept.append(o)
                    continue
                letter = next((l for l, poly in sorted(letters.items()) if _inside(o["position"], poly)), None)
                if letter is None:
                    continue
                o.update(letter=letter, shape="outline", points=letters[letter])
                if o["name"] in ("", o.get("letter")) or len(o["name"]) == 1:
                    o["name"] = letter
                o.pop("radius", None)
                o.pop("height", None)
                if not any(k["type"] == "capture_zone" and k["letter"] == letter for k in kept):
                    kept.append(o)
            out.objectives = kept
        elif self.world.install.generation == "bf1":
            # Without the channels a Battlefield 1 mode has no capture points of its own.
            out.objectives = [o for o in out.objectives if o["type"] != "capture_zone"]
        out.objectives = [
            o for o in out.objectives
            if o["type"] != "objective" or o.get("kind") not in KIND_MODES or KIND_MODES[o["kind"]].search(out.mode)
        ]
        if re.search(r"deathmatch|tdm|gunmaster", out.mode, re.I):
            out.objectives = [o for o in out.objectives if o["type"] != "capture_zone"]
        # A prefab's spare pieces sit at its own place, under the map: lower than
        # every spawn the level placed, they are left out.
        heights = sorted(s["position"][1] for s in out.spawns if s["type"] == "spawn")
        if len(heights) >= 4:
            floor = heights[max(0, len(heights) // 50)] - 25.0
            out.objectives = [o for o in out.objectives if o["position"][1] >= floor]
        # A stage's objectives: the stage of the defenders' area they are in.
        staged = [z for z in out.zones if z.get("stage") is not None]
        for o in out.objectives:
            if o.get("stage") is not None or not staged:
                continue
            for z in sorted(staged, key=lambda z: (z["stage"], -(z["team"] or 0))):
                if _inside(o["position"], z["points"]):
                    o["stage"] = z["stage"]
                    break
        self._channels(out)
        self._other_modes(out)
        _finish_spawns(out)

    @staticmethod
    def _other_modes(out: Layout) -> None:
        """
        A shared layer's spawn that only sub-levels of other modes point to
        (their capture points' spawn lists) is not one of this mode's: left
        out and counted.
        """
        drop = set()
        for ctx, key, sp in out.spawn_info:
            if sp.get("_how"):
                continue
            sources = [src for (t, _), srcs in ctx.rlinks.items() if t == key for src, _ in srcs]
            if sources and all((id(ctx), src) in out.excluded for src in sources):
                drop.add(id(sp))
        if drop:
            out.spawns = [sp for sp in out.spawns if id(sp) not in drop]
            out.dropped["used by other modes only"] = len(drop)

    def _channels(self, out: Layout) -> None:
        """
        Battlefield 1: a flag's channel (`conquest_flaga_hub`) points to the
        spawns the flag gives its holder, a team's (`conquest_team1_hub`) to
        that team's headquarters' spawns.
        """
        letters = {o["letter"]: o for o in out.objectives if o["type"] == "capture_zone" and o.get("letter")}
        for ctx, key, letter in out.hubs:
            owner = letters.get(letter)
            if owner is None:
                continue
            for s, f in list(ctx.links):
                if s != key or f == F_CAPTURE_AREA:
                    continue
                for tctx, target in self._follow(ctx, s, f):
                    sp = out.spawn_at.get((id(tctx), target))
                    if sp is not None:
                        _own(sp, owner, "channel")
        # A sector's channel: the spawns of that stage (one spawn can serve several).
        for ctx, key, stage in out.sector_hubs:
            for s, f in list(ctx.links):
                if s != key:
                    continue
                for tctx, target in self._follow(ctx, s, f):
                    sp = out.spawn_at.get((id(tctx), target))
                    if sp is not None:
                        sp.setdefault("_stages", set()).add(stage)
        for ctx, key, team, stage in out.team_hubs:
            hqs = [o for o in out.objectives if o["type"] == "base" and o.get("team") == team]
            hq = next((o for o in hqs if o.get("stage") == stage), hqs[0] if hqs else None)
            for s, f in list(ctx.links):
                if s != key:
                    continue
                for tctx, target in self._follow(ctx, s, f):
                    sp = out.spawn_at.get((id(tctx), target))
                    if sp is None:
                        continue
                    if hq is not None:
                        _own(sp, hq, "channel")
                    elif not sp.get("team"):
                        sp["team"] = team


#: How a spawn's owner is known, strongest first wins: the game's own links
#: (a capture point's spawn lists, a Battlefield 1 flag's channel), being
#: placed inside the capture point's prefab, then only being nearest.
OWN_RANK = {"link": 3, "channel": 3, "prefab": 2, "nearest": 1}


def _own(spawn: dict, owner: dict, how: str) -> None:
    """Gives a spawn its owner (a capture point or a headquarters record), unless a stronger way already did."""
    was = spawn.get("_how")
    if was is not None and OWN_RANK[was] >= OWN_RANK[how]:
        return
    spawn["_owner"] = owner
    spawn["_how"] = how
    spawn["base"] = True


#: A spawn the game links to nothing is given the nearest capture point only
#: this close (metres), and only in a mode most of whose spawns are linked.
NEAREST_MAX = 150.0
NEAREST_SHARE = 0.5


def _finish_spawns(out: Layout) -> None:
    """
    Each spawn's owner by the id its capture point or headquarters is known
    by (`baseId`), how that is known (`baseSource`), and when it can be
    spawned on (`rule`):

    - `flag`: while the spawn's team holds the capture point;
    - `hq`: always, for the headquarters' team;
    - `stage`: in its stage (Rush, Breakthrough), for its team;
    - `team`: always, for its team (a spawn of no capture point);
    - `free`: anyone's (a mode with no teams' spawns: Team Deathmatch's are free for both).

    Spawns at the level's origin with nothing placing them elsewhere are a
    prefab's spare pieces: they are dropped and counted (`dropped`).
    """
    kept_ids = {id(o) for o in out.objectives}
    owned = [o for o in out.objectives if o["type"] in ("capture_zone", "base")]
    flags = [o for o in owned if o["type"] == "capture_zone"]
    # The ids again, now that Battlefield 1's letters and the stages are known.
    used: set = set()
    for o in owned:
        want = o.get("letter") or (f"HQ{o['team']}" if o["type"] == "base" and o.get("team") else o.get("name")) or "CP"
        if o.get("stage") is not None:
            want = f"{want}#{o['stage']}"
        ident, n = want, 1
        while ident in used:
            n += 1
            ident = f"{want}-{n}"
        used.add(ident)
        o["id"] = ident
    keep = []
    for sp in out.spawns:
        if all(abs(v) < 0.01 for v in sp["position"]):
            out.dropped["at the origin (a prefab's spare)"] = out.dropped.get("at the origin (a prefab's spare)", 0) + 1
            continue
        keep.append(sp)
    out.spawns = keep
    for sp in out.spawns:
        owner = sp.pop("_owner", None)
        how = sp.pop("_how", None)
        sp.pop("base", None)
        if owner is not None and id(owner) in kept_ids:
            sp["_o"], sp["_h"] = owner, how
    linked = sum(1 for sp in out.spawns if "_o" in sp)
    if flags and out.spawns and linked >= NEAREST_SHARE * len(out.spawns):
        for sp in out.spawns:
            # A gun emplacement no capture point lists is anyone's, wherever it stands.
            if "_o" in sp or sp.get("vehicleKind") == "stationary":
                continue
            best, dist = None, NEAREST_MAX
            for o in flags:
                r = float(o.get("radius") or 0)
                d = math.dist((sp["position"][0], sp["position"][2]), (o["position"][0], o["position"][2])) - r
                if d < dist and (o.get("stage") is None or sp.get("stage") in (None, o.get("stage"))):
                    best, dist = o, d
            if best is not None:
                sp["_o"], sp["_h"] = best, "nearest"
    for sp in out.spawns:
        stages = sorted(sp.pop("_stages", ()))
        if stages:
            if sp.get("stage") is None:
                sp["stage"] = stages[0]
                sp["stageSource"] = "channel"
            if len(stages) > 1:
                sp["stages"] = stages
    staged = any(sp.get("stage") is not None for sp in out.spawns) or any(o.get("stage") is not None for o in owned)
    for sp in out.spawns:
        owner = sp.pop("_o", None)
        how = sp.pop("_h", None)
        if owner is not None:
            sp["base"] = owner.get("letter") or owner.get("name") or owner["id"]
            sp["baseId"] = owner["id"]
            sp["baseSource"] = how
            if owner["type"] == "capture_zone":
                sp["rule"] = "flag"
            else:
                sp["rule"] = "stage" if staged and (owner.get("stage") is not None or sp.get("stage") is not None) else "hq"
                if not sp.get("team") and owner.get("team"):
                    sp["team"] = owner["team"]
        elif sp.get("stage") is not None:
            sp["rule"] = "stage"
        else:
            sp["rule"] = "team" if sp.get("team") and sp.get("vehicleKind") != "stationary" else "free"


def vehicle_class_of(name: str) -> str:
    """A vehicle's class (`tank`, `jet`, `boat`...) by the words of a blueprint's or prefab's name; "" for none."""
    n = name.lower().rsplit("/", 1)[-1]
    for pattern, kind in VEHICLE_WORDS:
        if re.search(pattern, n):
            return kind
    return ""


def vehicle_class(ctx: Context) -> str:
    """What a vehicle spawner spawns, by the nearest spawner prefab around it that names it (`car_heavy`), "" for none."""
    c = ctx
    while c is not None:
        m = SPAWNER.search(c.name.rsplit("/", 1)[-1])
        if m and m.group(1).lower() not in SPAWNER_GENERIC:
            return m.group(1).lower()
        c = c.parent
    return ""


def _inside(p, poly, margin: float = 0.0) -> bool:
    """Whether a point is in a polygon (x, z), or within `margin` of its bounds when one is given."""
    x, z = p[0], p[2]
    if margin:
        xs = [q[0] for q in poly]
        zs = [q[2] for q in poly]
        return min(xs) - margin <= x <= max(xs) + margin and min(zs) - margin <= z <= max(zs) + margin
    inside = False
    n = len(poly)
    for i in range(n):
        x1, z1 = poly[i][0], poly[i][2]
        x2, z2 = poly[(i + 1) % n][0], poly[(i + 1) % n][2]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-12) + x1:
            inside = not inside
    return inside


def objective_kind(blueprint: str) -> tuple[str, str]:
    """An objective prefab's kind and what to call it."""
    b = blueprint.lower()
    for pattern, kind, label in (
        (r"rush_base_objective|rush_objective|mcom", "mcom", "M-COM"),
        (r"telegraph", "telegraph", "Telegraph"),
        (r"bombdropoff|bombsite|bomb_site|obliteration.*target", "bomb_target", "Bomb target"),
        (r"ctf|flagbase", "flag", "Flag"),
        (r"pigeon", "pigeon", "Pigeon"),
        (r"satcom", "satcom", "Satcom"),
        (r"silo", "silo", "Missile silo"),
        (r"defuse", "bomb_site", "Bomb site"),
    ):
        if re.search(pattern, b):
            return kind, label
    return "objective", "Objective"


#: What the modes are called in the game's menus.
MODE_NAMES = {
    "conquestlarge0": "Conquest Large", "conquestsmall0": "Conquest", "conquest0": "Conquest",
    "rushlarge0": "Rush", "rush0": "Rush", "teamdeathmatch0": "Team Deathmatch",
    "squaddeathmatch0": "Squad Deathmatch", "domination0": "Domination", "obliteration": "Obliteration",
    "elimination0": "Defuse", "gunmaster0": "Gun Master", "capturetheflag0": "Capture the Flag",
    "airsuperiority0": "Air Superiority", "carrierassaultlarge0": "Carrier Assault Large",
    "carrierassaultsmall0": "Carrier Assault", "chainlink0": "Chain Link", "squadobliteration0": "Squad Obliteration",
    "breakthroughlarge0": "Operations", "breakthrough0": "Breakthrough", "possession0": "War Pigeons",
    "tugofwar0": "Frontlines", "teamdeathmatchc0": "Team Deathmatch", "zonecontrol0": "Domination",
}


def mode_name(mode: str) -> str:
    return MODE_NAMES.get(mode.lower(), re.sub(r"(?<=[a-z])(?=[A-Z])", " ", re.sub(r"\d+$", "", mode)))


def build_layouts(install, level: str, game: str, version: str, log=print) -> dict:
    world = World(install, level)
    walker = Walker(world)
    modes = walker.modes()
    layouts = []
    for mode in modes:
        try:
            lay = walker.layout(mode)
        except (UnsupportedFrostbite, ValueError, IndexError, KeyError) as exc:
            log(f"   {mode}: failed ({exc})")
            continue
        if not (lay.objectives or lay.zones or lay.spawns):
            continue
        layouts.append({
            "id": mode,
            "name": mode_name(mode),
            "mode": mode,
            "objectives": lay.objectives,
            "zones": lay.zones,
            "spawns": lay.spawns,
            **({"spawnsDropped": lay.dropped} if lay.dropped else {}),
        })
        caps = sum(o["type"] == "capture_zone" for o in lay.objectives)
        log(f"   {mode}: {caps} capture points, {len(lay.objectives) - caps} other objectives, "
            f"{len(lay.zones)} areas, {len(lay.spawns)} spawns")
    return {
        "format": FORMAT,
        "version": 1,
        "game": game,
        "level": world.level.name,
        "source": f"heat3d-battlefield-maps {version}",
        "units": "m",
        "up": "y",
        "layouts": layouts,
    }


def write_layouts(doc: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    return out
