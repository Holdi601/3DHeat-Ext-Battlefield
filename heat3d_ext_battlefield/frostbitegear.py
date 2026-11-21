"""
Battlefield 6 vehicles: a catalogue and a local model pack, from the user's own install.

The vehicles' art is in the `vehicles` table (`Data/Win32/vehicles.toc`): one skinned MeshSet per vehicle,
`common/hardware/vehicles/<kind>/<name>/art/ob_veh_<kind>_<name>_base_mesh`, in the vehicle's frame and bind pose
(x left, y up, z forward, as the levels use it). The blueprints that would name the joints are in a type library this
reader does not have, so the parts are found from the mesh itself:

- turret: the sections whose material names the turret (`M_Turret`); its yaw pivot the centre of its lowest band;
- gun: of the turret's bones, the one whose vertices reach furthest forward over at least 1.5 m (the barrel); its
  pitch pivot the back of that bone's vertices;
- running gear: materials naming wheels, tyres or tracks;
- rotor: materials naming the main rotor's blades; its pivot their centre.

Glass, interiors, lights, destruction debris and first-person cockpits are left out.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np

BASE = re.compile(r"vehicles/([^/_]+)/([^/]+)/art/ob_veh_[^/]+_base_mesh$")
SKIP = re.compile(r"glass|interior|emissive|light|destruction|ammobelt|ammo_belt|cockpit|decal|1p|shadow|lod|"
                  r"broken|dirt|blur|disc", re.I)
TURRET = re.compile(r"turret", re.I)
GEAR = re.compile(r"wheel|tyre|tire|track", re.I)
ROTOR = re.compile(r"rotorblade|mainrotor|main_rotor|rotor_main", re.I)

#: The real vehicle each stands for, by its folder name.
REAL = {
    "abrams": ("M1A2 SEPv3", "US", "mbt"), "leopard": ("Leopard 2A7", "DE", "mbt"), "bradley": ("M2A4 Bradley", "US", "ifv"),
    "cv90": ("CV90", "SE", "ifv"), "gepard": ("Gepard", "DE", "spaa"), "cheetah": ("Cheetah", "", "spaa"),
    "ah64e": ("AH-64E", "US", "heli-attack"), "ah6m": ("AH-6M Little Bird", "US", "heli-transport"),
    "uh60": ("UH-60M", "US", "heli-transport"), "mh47": ("MH-47G", "US", "heli-transport"),
    "eurocopter": ("Eurocopter", "", "heli-transport"), "trv150": ("TRV-150", "", "heli-transport"),
    "f16": ("F-16C", "US", "fighter"), "f22": ("F-22A", "US", "fighter"), "f14": ("F-14", "US", "fighter"),
    "fa18f": ("F/A-18F", "US", "fighter"), "jas39": ("JAS 39 Gripen", "SE", "fighter"), "su57": ("Su-57", "RU", "fighter"),
    "b1bomber": ("B-1B Lancer", "US", "bomber"), "mq9": ("MQ-9 Reaper", "US", "uav"),
    "cb90": ("CB90", "SE", "boat"), "rhib": ("RHIB", "", "boat"), "himars": ("M142 HIMARS", "US", "artillery"),
    "jltv": ("JLTV", "US", "car"), "marauder": ("Marauder", "ZA", "car"), "vector": ("Vector", "", "car"),
    "flyer60": ("Flyer 60", "US", "car"), "ptv": ("PTV", "", "car"), "quadbike": ("Quad bike", "", "car"),
    "couch": ("Couch", "", "car"), "dirtbike01": ("Dirt bike", "", "car"), "dirtbike02": ("Dirt bike", "", "car"),
    "bgm71tow": ("BGM-71 TOW", "US", "stationary"), "m2mg": ("M2 Browning", "US", "stationary"),
    "gdf009": ("Oerlikon GDF-009", "CH", "spaa"), "phalanx": ("Phalanx CIWS", "US", "spaa"),
    "cws": ("CROWS", "US", "stationary"),
}
DOMAIN = {"airplane": "air", "helicopter": "air", "boat": "sea"}


def to_frame(v: np.ndarray) -> np.ndarray:
    return np.stack([v[:, 2], v[:, 1], -v[:, 0]], 1)


def bf6_vehicles_table(install: Path) -> Path | None:
    p = Path(install) / "Data" / "Win32" / "vehicles.toc"
    return p if p.is_file() else None


def vehicles(cat) -> dict[str, str]:
    """Vehicle id (`<kind>_<name>`) -> its base mesh's res name."""
    out = {}
    for name in sorted(cat.res):
        m = BASE.search(name)
        if m:
            out[f"{m.group(1)}_{m.group(2)}"] = name
    return out


def describe(vid: str, mesh: str) -> dict:
    kind, name = vid.split("_", 1)
    real, nation, cls = REAL.get(name, (name.upper(), "", {"tank": "mbt", "car": "car", "motorcycle": "car",
                                                           "stationary": "stationary"}.get(kind, kind)))
    dom = DOMAIN.get(kind, "ground")
    return {"id": vid, "kind": "vehicle", "name": real, "class": cls, "domain": dom, "nation": nation, "key": real,
            "mesh": mesh}


def build(cat, mesh_name: str, domain: str, cls: str) -> tuple[dict, dict, list[str]]:
    from .frostbitemesh import decode_sections, read_meshset

    e = cat.res[mesh_name]
    res = cat.read(e.location)
    mesh = read_meshset(res, mesh_name)
    lod = mesh.lods[0]
    buf = cat.chunk(lod.chunk)
    groups: dict[str, list] = {"hull": [], "gear": [], "turret": [], "rotor": []}
    turret_bones: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    notes: list[str] = []
    for g in decode_sections(lod, buf, mesh_name):
        s = lod.sections[g.index]
        mat = s.material or ""
        if SKIP.search(mat):
            continue
        v = to_frame(np.asarray(g.positions, np.float64))
        f = np.asarray(g.faces, np.int64).reshape(-1, 3)
        if domain == "ground" and TURRET.search(mat) and cls not in ("car",):
            bones = None
            for usage, _fmt, off, stream in s.elements:
                if usage == 2:
                    at = s.vertex_offset + s.vertex_count * sum(s.streams[:stream])
                    st = s.streams[stream]
                    bones = np.frombuffer(buf, np.uint8, s.vertex_count * st, at).reshape(-1, st)[:, off].astype(np.int64)
                    break
            turret_bones.append((v, f, bones if bones is not None else np.zeros(len(v), np.int64)))
        elif GEAR.search(mat):
            groups["gear"].append((v, f))
        elif domain == "air" and ROTOR.search(mat):
            groups["rotor"].append((v, f))
        else:
            groups["hull"].append((v, f))
    pivots: dict = {}
    gun: list = []
    if turret_bones:
        # Turret-material pieces low on the hull or far from the turret's core (side armour, stowage) stay on the hull.
        cents = np.concatenate([v[f].mean(1) for v, f, _b in turret_bones])
        core = np.median(cents, 0)
        kept = []
        for v, f, bones in turret_bones:
            c = v[f].mean(1)
            on = (c[:, 1] >= core[1] - 0.6) & (np.hypot(c[:, 0] - core[0], c[:, 2] - core[2]) <= 8.0)
            if (~on).any():
                groups["hull"].append((v, f[~on]))
            kept.append((v, f[on], bones))
        turret_bones = [t for t in kept if len(t[1])]
    if turret_bones:
        allv = np.concatenate([v[np.unique(f)] for v, f, _b in turret_bones])
        lo_y = float(np.percentile(allv[:, 1], 5))
        pivots["turret"] = [round(float(np.median(allv[:, 0])), 4), round(lo_y, 4), round(float(np.median(allv[:, 2])), 4)]
        # The barrel: the bone reaching furthest forward, over at least 1.5 m.
        best, barrels = None, []
        for b in np.unique(np.concatenate([t[2] for t in turret_bones])):
            pts = np.concatenate([t[0][np.unique(t[1])][t[2][np.unique(t[1])] == b] for t in turret_bones])
            if len(pts) < 8:
                continue
            ext = pts.max(0) - pts.min(0)
            # A barrel: long and thin (not a bone that carries the whole turret).
            if ext[0] >= 1.5 and ext[0] > 2.2 * max(ext[1], ext[2]):
                barrels.append((b, float(pts[:, 0].max())))
        if barrels:
            best_reach = max(r for _b, r in barrels)
            # Twin guns (an anti-aircraft tank's pair) reach about as far: both rise together.
            best = [b for b, r in barrels if r >= best_reach - 0.6]
        for v, f, bones in turret_bones:
            if best is not None:
                on_gun = np.isin(bones, best)
                tri_gun = on_gun[f[:, 0]]
                gun.append((v, f[tri_gun]))
                groups["turret"].append((v, f[~tri_gun]))
            else:
                groups["turret"].append((v, f))
        if best is not None:
            pts = np.concatenate([t[0][np.unique(t[1])][np.isin(t[2][np.unique(t[1])], best)] for t in turret_bones])
            back = pts[pts[:, 0] < pts[:, 0].min() + 0.3]
            pivots["gun"] = [round(float(back[:, 0].mean()), 4), round(float(np.median(pts[:, 1])), 4),
                             round(float(np.median(pts[:, 2])), 4)]
        else:
            notes.append("no barrel found among the turret's bones: the gun turns with the turret")
    if groups["rotor"]:
        rv = np.concatenate([v[np.unique(f)] for v, f in groups["rotor"]])
        pivots["rotor"] = [round(float(rv[:, 0].mean()), 4), round(float(rv[:, 1].max()), 4), round(float(rv[:, 2].mean()), 4)]
    from .modelpack import merge

    parts = {}
    for name, items in list(groups.items()) + [("gun", gun)]:
        if items:
            v, f = merge(items)
            if len(f):
                parts[name] = (v, f)
    return parts, pivots, notes


def fingerprint(cat, mesh_name: str) -> str:
    e = cat.res[mesh_name]
    return hashlib.sha1(repr((mesh_name, getattr(e, "location", None))).encode()).hexdigest()[:16]
