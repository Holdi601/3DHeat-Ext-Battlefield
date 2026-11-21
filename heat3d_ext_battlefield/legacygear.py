"""
Battlefield 4 and Battlefield 1 vehicles: a catalogue and a local model pack, from the user's own install.

Where they are
--------------
The multiplayer vehicles have superbundles of their own (`MpVehicles`, and in Battlefield 4 one per expansion,
`XP<n>Vehicles`), with their buffers in the chunk tables beside them (`...Chunks`). Each vehicle is a
`VehicleBlueprint` partition whose `VehicleEntityData` holds a tree of components, each with a transform relative
to its parent (Frostbite's linear transform: right, up, forward, translation; row vectors):

- `ChassisComponentData`, `PartComponentData`: pieces of the model; their health states name the part index of the
  composite mesh the piece draws (`HealthStateData.PartIndex`);
- `ChildComponentData` with a `ChildRotationBodyData` (`MovingBody`): a joint turning about its local y
  (`RotationAxis` 1: a turret) or x (0: a gun);
- `TrackWheelComponentData`, `WheelComponentData`: running gear;
- `MeshComponentData`: a mesh, composite (`CompositeMeshAsset`: each vertex names its part in its blend index, and
  lies in that part's own frame) or skinned (the tracks, in bind pose).

So a vertex's place on the vehicle is its part's chain of transforms; the part's place in the tree says whether it
turns with the turret, rises with the gun or is running gear. The frame is Frostbite's (x, y up, z forward; the
viewer's levels use it as is, so x is the vehicle's left), turned to the viewer's figure frame (x forward, y up, z
right): (z, y, -x).

Names are the vehicle's `NameSid` and blueprint bundle (`vehicle_<kind>_<class>_<side>_<name>`); the real vehicle
each stands for is looked up in `REAL`.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np

from .frostbite import UnsupportedFrostbite
from .legacy import LegacyEntry, LegacyInstall, LegacyLevel, read_flat_bundle, read_toc, read_tree
from .legacyebx import Import, Ref, read_partition

#: Real vehicles by the words of their blueprint's name (normalised: letters and digits only), first match wins.
REAL = (
    ("m1abrams|m1a2", "M1A2 SEP", "US"), ("t90", "T-90A", "RU"), ("type99", "Type 99A", "CN"),
    ("lav25", "LAV-25", "US"), ("btr90", "BTR-90", "RU"), ("zbd09", "ZBD-09", "CN"), ("aav7", "AAV-7A1", "US"),
    ("lavad", "LAV-AD", "US"), ("tunguska", "2K22 Tunguska", "RU"), ("pgz95", "PGZ-95", "CN"),
    ("himars", "M142 HIMARS", "US"), ("cougar", "Cougar MRAP", "US"), ("spm3", "SPM-3", "RU"),
    ("zfb05", "ZFB-05", "CN"), ("growler", "Growler ITV", "US"), ("vdvbuggy", "VDV Buggy", "RU"),
    ("lyt2021", "LYT2021", "CN"), ("quadbike", "Quad bike", ""), ("ah1z", "AH-1Z Viper", "US"),
    ("mi28", "Mi-28N", "RU"), ("z10", "Z-10", "CN"), ("venom", "UH-1Y Venom", "US"),
    ("ka60", "Ka-60 Kasatka", "RU"), ("z9", "Z-9", "CN"), ("ah6|littlebird", "AH-6 Little Bird", "US"),
    ("z11", "Z-11W", "CN"), ("f35", "F-35B", "US"), ("pakfa|t50", "Su-57 (T-50)", "RU"), ("j20", "J-20", "CN"),
    ("a10", "A-10C", "US"), ("su25", "Su-25TM", "RU"), ("q5", "Q-5 Fantan", "CN"), ("cb90", "CB90", "US"),
    ("dv15", "DV-15", ""), ("rhib", "RHIB", ""), ("jetski|pwc", "Jet ski", ""), ("tow2", "BGM-71 TOW", "US"),
    ("kornet", "9M133 Kornet", "RU"), ("hj8", "HJ-8", "CN"), ("centurion|cram", "Centurion C-RAM", "US"),
    ("pantsir", "Pantsir-S1", "RU"), ("ld2000", "LD-2000", "CN"), ("ac130|gunship", "AC-130", "US"),
    ("gunshieldtripod|50cal", "M2 Browning", ""), ("m1128|stryker", "M1128 Stryker", "US"),
    ("2s25|sprut", "2S25 Sprut-SD", "RU"), ("zbd05", "ZBD-05", "CN"), ("rawr", "R.A.W.R.", ""), ("dpv", "DPV", "US"),
    ("skidloader", "Skid loader", ""), ("b1lancer", "B-1 Lancer", "US"), ("h6k", "H-6K", "CN"),
    ("klr650|dirtbike", "Kawasaki KLR650", ""), ("hovercraft", "Hovercraft", ""), ("hovertank", "Hover tank", ""),
    ("metalstorm", "Metal Storm", ""), ("snowmobile", "Snowmobile", ""),
    # Battlefield 1
    ("markv", "Mark V", "UK"), ("a7v", "A7V", "DE"), ("ft17", "Renault FT", "FR"), ("stchamond|saintchamond", "Saint-Chamond", "FR"),
    ("char2c", "Char 2C", "FR"), ("rollsroyce", "Rolls-Royce Armoured Car", "UK"), ("ehrhardt", "Ehrhardt E-V/4", "DE"),
    ("romfell", "Romfell", "AH"), ("fiatterni", "Fiat-Terni Tripoli", "IT"), ("piercearrow", "Pierce-Arrow AA lorry", "UK"),
    ("putilov", "Putilov-Garford", "RU"), ("spad", "SPAD S.XIII", "FR"), ("sopwith", "Sopwith Camel", "UK"),
    ("fokkerdr1", "Fokker Dr.I", "DE"), ("albatros", "Albatros D.III", "DE"), ("halberstadt", "Halberstadt CL.II", "DE"),
    ("bristol", "Bristol F.2B", "UK"), ("dh10", "Airco DH.10", "UK"), ("gotha", "Gotha G.IV", "DE"),
    ("caproni", "Caproni Ca.5", "IT"), ("ilyamuromets", "Ilya Muromets", "RU"), ("hansabrandenburg", "Hansa-Brandenburg G.I", "AH"),
    ("rumpler", "Rumpler C.I", "DE"), ("salmson", "Salmson 2", "FR"), ("astratorres", "Astra-Torres airship", "FR"),
    ("zeppelin", "Zeppelin L30", "DE"), ("ironduke", "Iron Duke class battleship", "UK"), ("hmslance", "HMS Lance", "UK"),
    ("itamas|mas15", "MAS 15", "IT"), ("ylighter", "Y-Lighter", "UK"), ("mercedes37", "Mercedes 37/95", "AH"),
    ("benz", "Benz MG carrier", "DE"), ("nsu", "NSU motorcycle", "DE"), ("harleydavidson", "Harley-Davidson 18J", "US"),
    ("dodge", "Dodge Model 30", "US"), ("fk96", "FK 96 field gun", "DE"), ("bl9", "BL 9.2-inch gun", "UK"),
    ("qf1", "QF 1-pounder AA gun", "UK"), ("sk45|coastalcannon", "SK L/45 coastal gun", "DE"), ("dago", "Coastal battery", "RU"),
    ("vickers", "Vickers HMG", "UK"), ("fortressturret", "Fortress turret", "FR"), ("horse", "Horse", ""),
)
NATIONS = {"us": "US", "usa": "US", "ru": "RU", "ch": "CN", "cn": "CN", "uk": "UK", "gbr": "UK", "de": "DE", "ger": "DE",
           "fr": "FR", "fra": "FR", "it": "IT", "ita": "IT", "ot": "OT", "ott": "OT", "ahu": "AH", "aht": "AH"}
#: A blueprint bundle's words -> the viewer's domain and class, first match wins.
KIND = (
    (r"zeppelin_[a-z0-9]*_aa|_aa_|_tank_aa|spaa|ciws|c-ram|pantsir|_qf1", "ground", "spaa"),
    (r"_heli_attack|_ahe_", "air", "heli-attack"), (r"_heli_scout|_heli_trans|_heli_|_lthe", "air", "heli-transport"),
    (r"_jet_stealth|_fjet|_jet_fighter|_air_fighter|_air_scout", "air", "fighter"),
    (r"_jet_attack|_jet_", "air", "attack"),
    (r"_bomber|heavybomber|zeppelin|airship|gunship", "air", "bomber"), (r"_plane|_air_", "air", "fighter"),
    (r"_boat|_fac_|_pwc|_rhib|dreadnaught|dreadnought|_destroyer_|torpedoboat|hovercraft|lighter", "sea", "boat"),
    (r"_tank_mbt|_mbt_|heavytank|_tank_heavy|lighttank|_tank_light|assaulttank|superheavytank|hovertank", "ground", "mbt"),
    (r"_tank_ifv|_ifv_|_apc|_aav", "ground", "ifv"),
    (r"_tank_mlrs|artillery|_arty", "ground", "artillery"), (r"_tank_td|_td_", "ground", "tank-destroyer"),
    (r"_car_|_mrap|_fav|_atv|armoredcar|armoredtruck|transportcar|truck|motorcycle|_bike|snowmobile|skidloader", "ground", "car"),
    (r"_station|_stationary|_static|fieldgun|emplacement|launcher", "ground", "stationary"),
    (r"horse", "ground", "horse"), (r"_bot_|robot", "ground", "car"),
)
#: Blueprints that are not vehicles one rides: guided missiles and drones flown from a launcher or a gunner's seat.
NOT_VEHICLE = re.compile(r"hellfire|agm-|_tv$|missile|_pod$|supplydrop|ucav|eod_bot|_mav$|suav", re.I)
SKIP_MATERIAL = re.compile(r"glass|decal|logo|light|infra|shadow|flir|_lod_|cockpit|interior|pilot|driver|"
                           r"rotorblur|blur|disc|reactive_armor|cage|camonet|camo_net", re.I)
SKIP_TYPES = {
    "EffectComponentData", "CameraComponentData", "UnlockComponentData", "LightComponentData",
    "LensFlareComponentData", "VehicleExitPointComponentData", "StanceFilterComponentData", "CameraComponentSoundData",
    "AlternateCameraViewData", "LocatorComponentData", "SupplySphereComponentData", "SpottingComponentData",
    "PlayerLogoComponentData", "RadarSweepComponentData", "BlockSpottingComponentData", "FlagComponentData",
    "LocalWindForceSphereComponentData", "LockingTargetComponentData", "WeaponComponentData",
}


def _mat(t) -> np.ndarray:
    m = np.eye(4)
    if t is None:
        return m
    a = np.asarray(t, np.float64).reshape(4, 4)
    m[:3, :3] = a[:3, :3]
    m[3, :3] = a[3, :3]
    return m


def to_frame(v: np.ndarray) -> np.ndarray:
    return np.stack([v[:, 2], v[:, 1], -v[:, 0]], 1)


class Vehicles:
    """The vehicle superbundles of an install, opened together, with every chunk table's chunks."""

    def __init__(self, install: LegacyInstall):
        self.install = install
        self.sb = LegacyLevel("vehicles", Path("."))
        names: dict[str, list[Path]] = {}
        for layer in install.layers:
            for toc in sorted(layer.glob("Win32/*.toc")):
                if re.search(r"vehicles", toc.stem, re.I) and toc.with_suffix(".sb").is_file():
                    names.setdefault(toc.stem.lower(), []).append(toc)
        if not names:
            raise UnsupportedFrostbite("no vehicle superbundle (MpVehicles) in this install")
        for tocs in names.values():
            self._open(tocs)
        for layer in install.layers:
            for toc in sorted(layer.glob("Win32/**/*.toc")):
                try:
                    tree = read_toc(toc)
                except (UnsupportedFrostbite, ValueError, OSError):
                    continue
                sb = toc.with_suffix(".sb")
                for c in tree.get("chunks") or []:
                    if not isinstance(c.get("id"), bytes):
                        continue
                    if c.get("sha1"):
                        self.sb.chunks.setdefault(c["id"], LegacyEntry(name="chunk", sha1=c["sha1"]))
                    elif "offset" in c and "size" in c and sb.is_file():
                        # A chunk table not in cas mode: the chunk's stored bytes are in the .sb beside it.
                        at = int(c["offset"])
                        self.sb.chunks.setdefault(c["id"], LegacyEntry(name="chunk", sha1=None, span=(sb, at, at + int(c["size"]))))
        self._parts: dict[str, object] = {}
        self._names: dict[bytes, str] | None = None

    def _open(self, tocs: list[Path]) -> None:
        toc = tocs[0]
        tree = read_toc(toc)
        if not tree.get("cas", False):
            self.install._add_flat(self.sb, tocs, tree)
            return
        sb = toc.with_suffix(".sb").read_bytes()
        base = None
        for bundle in tree.get("bundles", []):
            if bundle.get("base"):
                if base is None:
                    bt = self.install._base_of(toc)
                    if bt is None:
                        continue
                    base = bt.with_suffix(".sb").read_bytes()
                src = base
            else:
                src = sb
            self.install._add_bundle(self.sb, read_tree(src, int(bundle["offset"]), toc.name), str(bundle.get("id", "")))

    def partition(self, name: str):
        key = name.lower()
        if key not in self._parts:
            e = self.sb.ebx.get(key)
            try:
                self._parts[key] = read_partition(self.install.payload(e), key) if e else None
            except (UnsupportedFrostbite, ValueError, IndexError, KeyError, OSError):
                self._parts[key] = None
        return self._parts[key]

    def name_of(self, guid: bytes) -> str | None:
        if self._names is None:
            self._names = {}
            for name, entry in self.sb.ebx.items():
                try:
                    head = self.install.payload(entry)[0x28:0x38]
                except (UnsupportedFrostbite, OSError, ValueError):
                    continue
                self._names.setdefault(head, name)
        return self._names.get(guid)

    def blueprints(self) -> list[str]:
        """Every ebx that is a vehicle blueprint (its first instance a `VehicleBlueprint`)."""
        out = []
        for name in sorted(self.sb.ebx):
            if "vehicles/" not in name or re.search(r"_mesh$|_physics|_win32$|/kitunlock/|_networkregistry|/fx/|sound|/ui/", name):
                continue
            p = self.partition(name)
            if (p is not None and p.primary is not None and p.primary.type == "VehicleBlueprint" and p.of_type("VehicleEntityData")
                    and not NOT_VEHICLE.search(name.rsplit("/", 1)[-1])):
                out.append(name)
            elif p is not None:
                self._parts.pop(name, None)
        return out

    def bundle_of(self, name: str) -> str:
        e = self.sb.ebx.get(name.lower())
        b = e.bundle if e else ""
        return b.rsplit("/", 1)[-1]

    def mesh_geometry(self, mesh_ebx: str, lod_index: int = 0):
        """(sections' (positions, faces, part index per vertex), kind) of a mesh asset's MeshSet res."""
        from .frostbitemesh import decode_sections
        from .legacymesh import inline_buffers, read_meshset

        e = self.sb.res.get(mesh_ebx.lower())
        if e is None:
            raise UnsupportedFrostbite(f"no MeshSet res {mesh_ebx}")
        res = self.install.payload(e)
        mesh = read_meshset(res, self.install.generation, mesh_ebx)
        lod = mesh.lods[min(lod_index, len(mesh.lods) - 1)]
        if lod.chunk == bytes(16):
            buf = inline_buffers(mesh, res, e.res_meta).get(mesh.lods.index(lod))
        else:
            ce = self.sb.chunks.get(lod.chunk) or self.install.any_chunk(lod.chunk)
            buf = self.install.payload(ce) if ce is not None else None
        if buf is None:
            raise UnsupportedFrostbite(f"{mesh_ebx}: its buffers are in no chunk the install has")
        out = []
        for g in decode_sections(lod, buf, mesh_ebx):
            s = lod.sections[g.index]
            part = None
            for usage, _fmt, off, stream in s.elements:
                if usage == 2:  # blend indices: the composite part
                    at = s.vertex_offset + s.vertex_count * sum(s.streams[:stream])
                    stride = s.streams[stream]
                    raw = np.frombuffer(buf, np.uint8, s.vertex_count * stride, at).reshape(-1, stride)
                    part = raw[:, off].astype(np.int64)
                    break
            out.append((np.asarray(g.positions, np.float64), np.asarray(g.faces, np.int64).reshape(-1, 3), part, s.material))
        return out


class _Node:
    __slots__ = ("type", "world", "parent", "axis", "parts", "mesh", "skinned", "kids", "inst", "hidden")

    def __init__(self, type_, world, parent):
        self.type, self.world, self.parent = type_, world, parent
        self.axis = None
        self.parts: list[int] = []
        self.mesh = None
        self.skinned = False
        self.kids: list[_Node] = []
        self.hidden: set[int] = set()


def component_tree(vs: Vehicles, part, ve) -> _Node:
    root = _Node("VehicleEntityData", _mat(ve.get("Transform")), None)

    def mesh_name(value):
        if isinstance(value, Import):
            return vs.name_of(value.partition)
        return None

    if ve.get("Mesh") is not None:
        root.mesh = mesh_name(ve.get("Mesh"))

    def visit(ref, parent: _Node, depth: int):
        x = part.resolve(ref) if isinstance(ref, Ref) else None
        if x is None or not hasattr(x, "type") or x.type in SKIP_TYPES or depth > 40:
            return
        n = _Node(x.type, _mat(x.get("Transform")) @ parent.world, parent)
        if x.type == "ChildComponentData":
            body = part.resolve(x.get("MovingBody")) if isinstance(x.get("MovingBody"), Ref) else None
            if body is not None and getattr(body, "type", "") == "ChildRotationBodyData":
                n.axis = int(body.get("RotationAxis", -1))
        for h in x.get("HealthStates") or []:
            hs = part.resolve(h) if isinstance(h, Ref) else None
            pi = hs.get("PartIndex") if hs is not None and hasattr(hs, "get") else None
            if isinstance(pi, int) and 0 <= pi < 0xFFFF:
                n.parts.append(pi)
        if x.type == "RotorComponentData":
            # The blades (drawn when slow) are this rotor's part; the blur disc (drawn when fast) is left out.
            lo, hi = x.get("LowRpmModel") or {}, x.get("HighRpmModel") or {}
            if isinstance(lo, dict) and isinstance(lo.get("PartIndex"), int) and 0 <= lo["PartIndex"] < 0xFFFF:
                n.parts.append(lo["PartIndex"])
            if isinstance(hi, dict) and isinstance(hi.get("PartIndex"), int) and 0 <= hi["PartIndex"] < 0xFFFF:
                root.hidden.add(hi["PartIndex"])
            n.axis = 10 + int(x.get("RotationAxis", 0))
        if x.type == "MeshComponentData":
            n.mesh = mesh_name(x.get("Mesh"))
            n.skinned = x.get("Skeleton") is not None
        parent.kids.append(n)
        for c in x.get("Components") or []:
            visit(c, n, depth + 1)

    for c in ve.get("Components") or []:
        visit(c, root, 0)
    return root


def _nodes(root: _Node):
    stack = [root]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(n.kids)


def _ancestors(n: _Node):
    while n is not None:
        yield n
        n = n.parent


GEAR = {"TrackWheelComponentData", "WheelComponentData", "TrackComponentData", "TireTrailVehicleComponentData"}


def build_vehicle(vs: Vehicles, name: str, domain: str) -> tuple[dict, dict, list[str]]:
    """({part: (verts, faces)} in the figure frame, pivots, notes) of one blueprint."""
    part = vs.partition(name)
    ve = part.of_type("VehicleEntityData")[0]
    root = component_tree(vs, part, ve)
    nodes = list(_nodes(root))
    part_node: dict[int, _Node] = {}
    for n in nodes:
        for pi in n.parts:
            part_node.setdefault(pi, n)
    notes: list[str] = []
    # Unlockable kits (armour cages, extra plates) are not the vehicle as it spawns.
    # Skinned meshes (tracks) are left out: their bind pose is not where they show; the road wheels are drawn.
    meshes = [n for n in nodes if n.mesh and not n.skinned and not re.search(r"/kits?/|kitunlock|_kit\d", n.mesh)]
    if not meshes:
        raise UnsupportedFrostbite("no mesh component")

    def role(n: _Node | None) -> str:
        r = "hull"
        for a in _ancestors(n):
            if a.type in GEAR:
                return "gear"
        return r

    acc: dict[str, list] = {}
    per_joint: dict[int, int] = {}  # id(yaw/pitch node) -> vertices under it
    joint_of: dict[int, _Node] = {}
    geoms = []
    for mn in meshes:
        try:
            secs = vs.mesh_geometry(mn.mesh)
        except (UnsupportedFrostbite, ValueError, IndexError, KeyError) as e:
            notes.append(f"{mn.mesh}: {e}")
            continue
        for pos, faces, pidx, material in secs:
            if SKIP_MATERIAL.search(material or ""):
                continue
            if pidx is not None and not mn.skinned:
                # Composite: each vertex in its part's frame.
                world = pos.copy()
                owner = np.empty(len(pos), object)
                keep = ~np.isin(pidx, list(root.hidden)) if root.hidden else np.ones(len(pidx), bool)
                faces = faces[keep[faces].all(1)]
                for pi in np.unique(pidx):
                    sel = pidx == pi
                    pn = part_node.get(int(pi))
                    m = pn.world if pn is not None else mn.world
                    world[sel] = pos[sel] @ m[:3, :3] + m[3, :3]
                    owner[sel] = pn if pn is not None else mn
                geoms.append((world, faces, owner))
            else:
                # A skinned mesh (tracks) lies in the model's frame in its bind pose.
                world = pos if mn.skinned else pos @ mn.world[:3, :3] + mn.world[3, :3]
                owner = np.empty(len(pos), object)
                owner[:] = mn
                geoms.append((world, faces, owner))
    if not geoms:
        raise UnsupportedFrostbite("no geometry read: " + "; ".join(notes[:2]))
    # Joints: the yaw joint with the most vertices under it is the turret; the pitch joint under it with the most, the gun.
    for world, faces, owner in geoms:
        for o in set(owner.tolist()):
            cnt = int((owner == o).sum())
            for a in _ancestors(o):
                if a.axis in (0, 1):
                    per_joint[id(a)] = per_joint.get(id(a), 0) + cnt
                    joint_of[id(a)] = a
    yaw = max((joint_of[k] for k in per_joint if joint_of[k].axis == 1), key=lambda j: per_joint[id(j)], default=None)
    pitch = None
    if yaw is not None:
        # The main gun: of the pitch joints on the turret, the one whose geometry reaches furthest forward of its joint
        # (the barrel), not the one with most vertices (a remote weapon station can have more).
        under = [joint_of[k] for k in per_joint if joint_of[k].axis == 0 and yaw in list(_ancestors(joint_of[k]))[1:]]

        def reach(j: _Node) -> float:
            best = 0.0
            for world, _f, owner in geoms:
                sel = np.array([j in list(_ancestors(o)) for o in owner.tolist()]) if len(owner) else np.zeros(0, bool)
                if sel.any():
                    best = max(best, float((world[sel, 2] - j.world[3, 2]).max()))
            return best

        pitch = max(under, key=reach, default=None)
    if domain != "ground":
        yaw = pitch = None
    rotor = None
    if domain == "air":
        rotors = [n for n in nodes if n.type == "RotorComponentData" and n.axis == 11]
        if rotors:
            def spread(r: _Node) -> float:
                ext = 0.0
                for world, _f, owner in geoms:
                    sel = np.array([r in list(_ancestors(o)) for o in owner.tolist()]) if len(owner) else np.zeros(0, bool)
                    if sel.any():
                        d = world[sel] - r.world[3, :3]
                        ext = max(ext, float(np.hypot(d[:, 0], d[:, 2]).max()))
                return ext

            rotor = max(rotors, key=spread)
            if spread(rotor) < 1.0:
                rotor = None
    for world, faces, owner in geoms:
        labels = np.empty(len(world), object)
        cache: dict[int, str] = {}
        for o in set(owner.tolist()):
            if id(o) not in cache:
                anc = list(_ancestors(o))
                if rotor is not None and rotor in anc:
                    cache[id(o)] = "rotor"
                elif pitch is not None and pitch in anc:
                    cache[id(o)] = "gun"
                elif yaw is not None and yaw in anc:
                    cache[id(o)] = "turret"
                else:
                    cache[id(o)] = role(o)
            labels[owner == o] = cache[id(o)]
        if domain == "ground":
            # Track links laid out flat under the vehicle (no part of the tree places them) are left out.
            faces = faces[(world[faces][:, :, 1] > -0.05).any(1)]
        # A triangle goes with its first vertex's part.
        tri_part = labels[faces[:, 0]]
        for p in set(tri_part.tolist()):
            acc.setdefault(p, []).append((world, faces[tri_part == p]))
    from .modelpack import merge

    parts = {}
    for p, items in acc.items():
        v, f = merge(items)
        parts[p] = (to_frame(v), f)
    pivots = {}
    if yaw is not None and "turret" in parts:
        pivots["turret"] = [round(float(x), 4) for x in to_frame(yaw.world[3:4, :3])[0]]
    if pitch is not None and "gun" in parts:
        pivots["gun"] = [round(float(x), 4) for x in to_frame(pitch.world[3:4, :3])[0]]
    if rotor is not None and "rotor" in parts:
        pivots["rotor"] = [round(float(x), 4) for x in to_frame(rotor.world[3:4, :3])[0]]
    return parts, pivots, notes


def describe(vs: Vehicles, name: str) -> dict:
    """The catalogue entry of a blueprint: id, name, class, nation, key, domain."""
    part = vs.partition(name)
    ve = part.of_type("VehicleEntityData")[0]
    sid = str(ve.get("NameSid") or "")
    bundle = vs.bundle_of(name)
    stem = name.rsplit("/", 1)[-1]
    words = (bundle or stem).lower()
    domain, cls = "ground", "vehicle"
    for rx, d, c in KIND:
        if re.search(rx, "_" + words + "_"):
            domain, cls = d, c
            break
    m = re.match(r"vehicle_[a-z]+_[a-z]+_([a-z]{2,3})_", words)
    nation = NATIONS.get(m.group(1), "") if m else ""
    m = re.match(r"([a-z]{2,3})_", stem)
    if not nation and m:
        nation = NATIONS.get(m.group(1), "")
    key, real_nation = "", ""
    for text in (stem, words):
        flat = re.sub(r"[^a-z0-9]", "", text.lower())
        for rx, k, nat in REAL:
            if re.search(rx, flat):
                key, real_nation = k, nat
                break
        if key:
            break
    label = key or re.sub(r"^id_p_vname_|^id_vname_", "", sid.lower()).upper() or stem.upper()
    if re.search(r"night", words):
        label += " (night)"
    return {"id": stem, "kind": "vehicle", "name": label, "class": cls, "nation": nation or real_nation,
            "key": key, "domain": domain, "blueprint": name, "nameSid": sid, "bundle": bundle}


def fingerprint(vs: Vehicles, name: str) -> str:
    e = vs.sb.ebx.get(name.lower())
    return hashlib.sha1(repr((name, e.sha1 if e else None)).encode()).hexdigest()[:16]
