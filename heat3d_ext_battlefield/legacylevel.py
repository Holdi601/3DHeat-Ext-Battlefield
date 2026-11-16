"""
A Battlefield 4 or Battlefield 1 multiplayer level as one 3DHeat level.

What is placed
--------------
The walk starts at the level's own partition (its `LevelData`) and follows
what the game loads for the PC:

- `SubWorldReferenceObjectData`: a sub-level, by its bundle name, unless it
  is flagged as not for the PC (`IsWin32SubLevel`);
- anything with `Objects` (sub-levels, world parts, layers, prefabs) and
  anything with a `Blueprint` and a `BlueprintTransform` (references to
  world parts, layers, objects, prefabs), the transform composed on the way
  down; references flagged `Excluded` are not followed, nor effects,
  vehicles, soldiers, sound or logic;
- `StaticModelEntityData`: its mesh, at its own transform;
- `StaticModelGroupEntityData`: each member's mesh at each copy. A member's
  copies are in its `InstanceTransforms` when they are there; for most they
  are not, and they come from the group's collision (`legacyhavok`).

The game mode's own sub-level (the largest conquest one there is) is walked
too, for what that mode adds to the map.

Detail
------
Every placed mesh starts at its finest level of detail; while the triangles
of all copies exceed the budget, the mesh whose copies cost most drops one
level. If the coarsest levels still do not fit, the smallest meshes are left
out, smallest first. The terrain (`legacyterrain`) is two grids: the play area - the
placed copies' extent and a margin - at up to `FINE` samples a side, and the
whole square around it coarser, with the play area cut out of it.

Parts carry flat colours by what the mesh's path says it is (the names
`frostbitelevel.category` gives), and the ground its colour map where the
game has one (Battlefield 1) or a tint by slope. Every part's name ends in
` @<game>/<level>` (`ground:terrain @battlefield-1/MP_Amiens`), which is how
the viewer knows the map; the file's `asset.extras` say the same.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .frostbite import UnsupportedFrostbite
from .frostbitelevel import CINEMATIC, COLOURS, EFFECTS, LARGEST, LIGHTING, category
from .legacy import LegacyInstall
from .legacyebx import Import, Partition, Ref, read_partition

MESHSET = 0x49B156D4

#: Reference types whose blueprints are not scenery.
NOT_SCENERY = re.compile(
    r"^(Effect|Sound|Vehicle|Character|Soldier|Logic|VisualEnvironment|Camera|UI|Light|"
    r"Interactive|Spawn|AlternateSpawn|Ant|Gameplay|Squad|Player|Weapon|Projectile)",
)

#: Meshes that are not the map's surfaces: front-end and calibration
#: scenery, cloud cards and sky domes, heat-haze planes, objective lights.
NOT_SURFACE = re.compile(
    r"(^|/)levels/frontend/|(^|/)ui_|calibration|cloud|skydome|sky_dome|heatplane|heathaze|"
    r"capturelight|bomblight|lightshaft|godray",
    re.I,
)

#: A sub-level's names as the game modes call them; the first found is walked.
MODE_SUBLEVELS = ("conquestlarge0", "conquestlarge", "conquest0", "conquest", "conquestlarge1")

#: The terrain: samples a side for the play area and for the whole square.
FINE = 768
COARSE = 384
#: Metres added round the placed copies' extent for the fine terrain.
MARGIN = 150.0

#: Default triangle budget for the placed meshes.
BUDGET = 3_000_000


def _matrix(values) -> np.ndarray:
    m = np.asarray(values, np.float64).reshape(4, 4).copy()
    m[:, 3] = (0, 0, 0, 1)
    return m


@dataclass
class Placed:
    #: Mesh partition name -> list of (4, 4) row-vector transforms.
    meshes: dict[str, list[np.ndarray]] = field(default_factory=dict)
    groups: int = 0
    group_copies: int = 0
    group_missing: int = 0
    notes: list[str] = field(default_factory=list)

    def add(self, mesh: str, rows) -> None:
        self.meshes.setdefault(mesh, []).extend(np.asarray(rows).reshape(-1, 4, 4))


class World:
    """A level's partitions, by name and by GUID, read as they are needed."""

    def __init__(self, install: LegacyInstall, level: str):
        self.install = install
        self.level = install.open_level(level)
        self._parts: dict[str, Partition | None] = {}
        self._names: dict[bytes, str] | None = None
        self._guids: dict[str, dict[bytes, object]] = {}

    def partition(self, name: str) -> Partition | None:
        key = name.lower()
        if key not in self._parts:
            entry = self.level.ebx.get(key)
            part = None
            if entry is not None:
                try:
                    part = read_partition(self.install.payload(entry), key)
                except (UnsupportedFrostbite, ValueError, IndexError, KeyError, OSError):
                    part = None
            self._parts[key] = part
        return self._parts[key]

    def name_of(self, guid: bytes) -> str | None:
        if self._names is None:
            self._names = {}
            for name, entry in self.level.ebx.items():
                try:
                    head = self.install.payload(entry)[0x28:0x38]
                except (UnsupportedFrostbite, OSError, ValueError):
                    continue
                self._names.setdefault(head, name)
        return self._names.get(guid)

    def resolve(self, part: Partition, value):
        """(partition, instance) a pointer leads to, or None."""
        if isinstance(value, Ref):
            return part, part.instances[value.index]
        if isinstance(value, Import):
            name = self.name_of(value.partition)
            other = self.partition(name) if name else None
            if other is None:
                return None
            table = self._guids.get(name)
            if table is None:
                table = self._guids[name] = {i.guid: i for i in other.instances if i.guid}
            inst = table.get(value.instance)
            return (other, inst) if inst is not None else None
        return None


def _asset_name(world: World, part: Partition, value) -> str | None:
    found = world.resolve(part, value)
    if found is None:
        return None
    name = found[1].get("Name")
    return name.lower() if isinstance(name, str) else None


def _havok_name(world: World, part: Partition, smg) -> str | None:
    """The group's havok asset, found within a few pointers of the group."""
    seen = set()
    queue = [(part, smg, 0)]
    while queue:
        p, inst, depth = queue.pop(0)
        if id(inst) in seen or depth > 3:
            continue
        seen.add(id(inst))
        if inst.type == "GroupHavokAsset" and isinstance(inst.get("Name"), str):
            return inst["Name"].lower()
        for key, value in inst.fields.items():
            items = value if isinstance(value, list) else [value]
            for item in items:
                if isinstance(item, (Ref, Import)):
                    got = world.resolve(p, item)
                    if got:
                        queue.append((got[0], got[1], depth + 1))
    return None


def _group(world: World, part: Partition, smg, parent: np.ndarray, placed: Placed) -> None:
    from .legacyhavok import compounds, member_transforms

    members = smg.get("MemberDatas") or []
    own = smg.get("Transform")
    base = _matrix(own) @ parent if own is not None and len(own) == 16 else parent
    havok = None
    placed.groups += 1
    for k, member in enumerate(members):
        mesh = _asset_name(world, part, member.get("MeshAsset"))
        if mesh is None:
            got = world.resolve(part, member.get("MemberType"))
            if got:
                mesh = _asset_name(world, got[0], got[1].get("Mesh"))
        count = int(member.get("InstanceCount", 0) or 0)
        rows = member.get("InstanceTransforms")
        if isinstance(rows, np.ndarray) and len(rows) == count and count:
            transforms = rows.reshape(-1, 4, 4).astype(np.float64)
            transforms[:, :, 3] = (0, 0, 0, 1)
        else:
            if havok is None:
                name = _havok_name(world, part, smg)
                entry = world.level.res.get(name) if name else None
                try:
                    found = compounds(world.install.payload(entry), name) if entry else None
                    havok = member_transforms(members, found) if found else []
                except UnsupportedFrostbite as exc:
                    placed.notes.append(f"{part_name(part)}: {exc}")
                    havok = []
            transforms = havok[k] if k < len(havok) else np.zeros((0, 4, 4))
        placed.group_copies += count
        placed.group_missing += count - len(transforms)
        if mesh and len(transforms):
            placed.add(mesh, transforms @ base)


def part_name(part: Partition) -> str:
    return getattr(part, "name", "") or part.guid.hex()


def walk(world: World, root_name: str) -> Placed:
    placed = Placed()
    visited: set[tuple[int, int]] = set()

    def visit(part: Partition, inst, parent: np.ndarray, depth: int) -> None:
        if inst is None or depth > 40:
            return
        key = (id(inst), hash(parent.round(3).tobytes()))
        if key in visited:
            return
        visited.add(key)
        t = inst.type
        if t == "StaticModelGroupEntityData":
            _group(world, part, inst, parent, placed)
            return
        if t == "StaticModelEntityData":
            mesh = _asset_name(world, part, inst.get("Mesh"))
            own = inst.get("Transform")
            m = _matrix(own) @ parent if own is not None and len(own) == 16 else parent
            if mesh:
                placed.add(mesh, m)
            return
        if t == "SubWorldReferenceObjectData":
            if inst.get("IsWin32SubLevel", True) is False or not inst.get("BundleName"):
                return
            sub = world.partition(inst["BundleName"])
            if sub is not None and sub.instances:
                visit(sub, sub.instances[0], _matrix(inst["BlueprintTransform"]) @ parent, depth + 1)
            return
        if t.endswith("ReferenceObjectData") and "Blueprint" in inst.fields:
            if inst.get("Excluded") or NOT_SCENERY.match(t):
                return
            got = world.resolve(part, inst.get("Blueprint"))
            if got:
                transform = inst.get("BlueprintTransform")
                m = _matrix(transform) @ parent if transform is not None else parent
                visit(got[0], got[1], m, depth + 1)
            return
        if NOT_SCENERY.match(t):
            return
        for name in ("Object",):
            if isinstance(inst.get(name), (Ref, Import)):
                got = world.resolve(part, inst[name])
                if got:
                    visit(got[0], got[1], parent, depth + 1)
        objects = inst.get("Objects")
        if isinstance(objects, list):
            for item in objects:
                got = world.resolve(part, item)
                if got:
                    visit(got[0], got[1], parent, depth + 1)

    prefix = root_name.rsplit("/", 1)[0] + "/"
    root = world.partition(root_name)
    if root is None:
        raise UnsupportedFrostbite(f"the level partition {root_name} does not read")
    identity = np.eye(4)
    visit(root, root.instances[0], identity, 0)
    for mode in MODE_SUBLEVELS:
        sub = world.partition(prefix + mode)
        if sub is not None and sub.instances:
            visit(sub, sub.instances[0], identity, 0)
            placed.notes.append(f"mode sub-level {mode}")
            break
    return placed


def level_root(world: World) -> str:
    """
    The level's own partition (its `LevelData`): `<folder>/<name>`, where the
    folder is the one the table sits in and the name the table's
    (`levels/mp/mp_prison/mp_prison`; an expansion level's folder can be
    named otherwise than its table, `.../mp_subway/xp0_metro`).
    """
    name = str(world.level.name).lower()
    folder = world.level.toc.parent.name.lower()
    for candidate in sorted(world.level.ebx):
        parts = candidate.split("/")
        if len(parts) >= 3 and "levels" in parts and parts[-2] == folder and parts[-1] in (name, folder):
            return candidate
    raise UnsupportedFrostbite(f"no level partition named {world.level.name}")


# ---------------------------------------------------------------------------
# Meshes


@dataclass
class MeshInfo:
    name: str
    mesh: object
    res: bytes
    meta: bytes
    #: Drawn triangles per level of detail.
    triangles: list[int]


def _load_meshes(world: World, names, report) -> dict[str, MeshInfo]:
    from .legacymesh import read_meshset

    out = {}
    for name in names:
        entry = world.level.res.get(name)
        if entry is None or entry.res_type != MESHSET:
            report["no mesh res"] = report.get("no mesh res", 0) + 1
            continue
        try:
            res = world.install.payload(entry)
            mesh = read_meshset(res, world.install.generation, name)
        except (UnsupportedFrostbite, ValueError, IndexError) as exc:
            report[f"unread mesh: {str(exc)[-50:]}"] = report.get(f"unread mesh: {str(exc)[-50:]}", 0) + 1
            continue
        size = np.abs(mesh.high - mesh.low).max()
        if not np.isfinite(size) or size > LARGEST:
            report["mesh box too large"] = report.get("mesh box too large", 0) + 1
            continue
        out[name] = MeshInfo(name, mesh, res, entry.res_meta, [lod.triangles for lod in mesh.lods])
    return out


def _choose(meshes: dict[str, MeshInfo], copies: dict[str, int], budget: int) -> dict[str, int]:
    level = {n: 0 for n in meshes}
    total = sum(meshes[n].triangles[0] * copies[n] for n in meshes)
    import heapq

    heap = [(-meshes[n].triangles[0] * copies[n], n) for n in meshes]
    heapq.heapify(heap)
    while total > budget and heap:
        cost, n = heapq.heappop(heap)
        info = meshes[n]
        if level[n] + 1 >= len(info.triangles):
            continue
        before = info.triangles[level[n]] * copies[n]
        level[n] += 1
        after = info.triangles[level[n]] * copies[n]
        total += after - before
        heapq.heappush(heap, (-after, n))
    # Still over: the smallest meshes go first; a heatmap's context is the
    # buildings and the ground, not the cans on a table.
    if total > budget:
        for n in sorted(meshes, key=lambda n: float(np.linalg.norm(meshes[n].mesh.high - meshes[n].mesh.low))):
            if total <= budget:
                break
            total -= meshes[n].triangles[level[n]] * copies[n]
            level[n] = -1
    return level


def _geometry(world: World, info: MeshInfo, index: int, chunks):
    from .frostbitemesh import decode_sections
    from .legacymesh import inline_buffers

    lod = info.mesh.lods[index]
    if lod.chunk == bytes(16):
        buffers = inline_buffers(info.mesh, info.res, info.meta).get(index)
    elif lod.chunk in world.level.chunks:
        buffers = world.install.payload(world.level.chunks[lod.chunk])
    else:
        buffers = chunks.get(lod.chunk)
        if buffers is None:
            elsewhere = world.install.any_chunk(lod.chunk)
            if elsewhere is not None:
                try:
                    buffers = world.install.payload(elsewhere)
                except UnsupportedFrostbite:
                    buffers = None
    if buffers is None:
        raise UnsupportedFrostbite("its buffers are in no chunk the install has")
    return decode_sections(lod, buffers, info.name)


# ---------------------------------------------------------------------------
# Terrain


def _grid_faces(rows: int, cols: int, valid: np.ndarray) -> np.ndarray:
    """Two triangles per grid cell whose four corners are all valid."""
    r, c = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = r * cols + c
    ok = valid[:-1, :-1] & valid[1:, :-1] & valid[:-1, 1:] & valid[1:, 1:]
    a = a[ok]
    b, d, e = a + 1, a + cols, a + cols + 1
    return np.concatenate([np.stack([a, d, b], 1), np.stack([b, d, e], 1)])


def _resample(grid: np.ndarray, factor: int) -> np.ndarray:
    return grid[::factor, ::factor]


def _ground_colours(points: np.ndarray, normals_y: np.ndarray, colour_map) -> np.ndarray:
    base = np.array(COLOURS["ground:terrain"], np.float32)
    rock = np.array((0.47, 0.46, 0.44), np.float32)
    steep = np.clip((0.85 - normals_y) / 0.3, 0, 1)[:, None]
    out = base * (1 - steep) + rock * steep
    if colour_map is not None:
        from .legacyterrain import height_at

        rgb, x0, z0, spacing = colour_map
        cols = []
        for ch in range(3):
            cols.append(height_at(rgb[:, :, ch].astype(np.float32), x0, z0, spacing, points[:, 0], points[:, 2]))
        sampled = np.stack(cols, 1) / 255.0
        have = np.isfinite(sampled).all(1)
        out[have] = sampled[have]
    return out.astype(np.float32)


def _normals_y(heights: np.ndarray, spacing: float) -> np.ndarray:
    gz, gx = np.gradient(np.nan_to_num(heights, nan=np.nanmean(heights)), spacing)
    return 1.0 / np.sqrt(1 + gx * gx + gz * gz)


def terrain(install, level: str, play: tuple[float, float, float, float] | None, report):
    """(points, faces, colours) of the ground, or None when the level has no terrain."""
    from .legacyterrain import read_colormap, read_heightfield

    try:
        heights, x0, z0, spacing = read_heightfield(install, level, max_size=4096)
    except UnsupportedFrostbite as exc:
        report["terrain"] = f"none ({exc})"
        return None
    try:
        colour_map = read_colormap(install, level, max_size=4096)
    except (UnsupportedFrostbite, ValueError, IndexError):
        colour_map = None
    rows, cols = heights.shape
    pieces = []
    # The whole square, coarse.
    # The play area's step first, then the whole square's as a multiple of
    # it, so the fine grid's edge lies on the coarse grid's lines.
    fine_step = 1
    if play is not None:
        extent = max(play[2] - play[0], play[3] - play[1]) / spacing
        fine_step = max(1, int(np.ceil(extent / FINE)))
    step = max(1, int(np.ceil(max(rows, cols) / COARSE)))
    step = max(fine_step, int(np.ceil(step / fine_step)) * fine_step)
    coarse = _resample(heights, step)
    cr, cc = coarse.shape
    cs = spacing * step
    valid = np.isfinite(coarse)
    cut = None
    if play is not None:
        ax0, az0, ax1, az1 = play
        c0, c1 = int(np.floor((ax0 - x0) / cs)), int(np.ceil((ax1 - x0) / cs))
        r0, r1 = int(np.floor((az0 - z0) / cs)), int(np.ceil((az1 - z0) / cs))
        c0, r0 = max(c0, 0), max(r0, 0)
        c1, r1 = min(c1, cc - 1), min(r1, cr - 1)
        if c1 > c0 and r1 > r0:
            cut = (r0, r1, c0, c1)
    xs = x0 + np.arange(cc) * cs
    zs = z0 + np.arange(cr) * cs
    gx, gz = np.meshgrid(xs, zs)
    faces = _grid_faces(cr, cc, valid)
    if cut is not None:
        r0, r1, c0, c1 = cut
        fr = (faces[:, 0] // cc)
        fc = (faces[:, 0] % cc)
        inside = (fr >= r0) & (fr < r1) & (fc >= c0) & (fc < c1)
        faces = faces[~inside]
    pts = np.stack([gx.ravel(), np.nan_to_num(coarse).ravel(), gz.ravel()], 1)
    pieces.append((pts, faces, _normals_y(coarse, cs).ravel()))
    detail = f"{cr}x{cc} at {cs:g} m"
    if cut is not None:
        r0, r1, c0, c1 = cut
        fr0, fr1, fc0, fc1 = r0 * step, r1 * step, c0 * step, c1 * step
        sub = heights[fr0 : fr1 + 1 : fine_step, fc0 : fc1 + 1 : fine_step]
        sr, sc = sub.shape
        fs = spacing * fine_step
        gx, gz = np.meshgrid(x0 + fc0 * spacing + np.arange(sc) * fs, z0 + fr0 * spacing + np.arange(sr) * fs)
        pts = np.stack([gx.ravel(), np.nan_to_num(sub).ravel(), gz.ravel()], 1)
        pieces.append((pts, _grid_faces(sr, sc, np.isfinite(sub)), _normals_y(sub, fs).ravel()))
        detail += f", play area {sr}x{sc} at {fs:g} m"
    points, faces_all, ny = [], [], []
    base = 0
    for pts, f, n in pieces:
        used, local = np.unique(f, return_inverse=True)
        points.append(pts[used])
        faces_all.append(local.reshape(-1, 3) + base)
        ny.append(n[used])
        base += len(used)
    points = np.concatenate(points).astype(np.float32)
    colours = _ground_colours(points, np.concatenate(ny), colour_map)
    report["terrain"] = detail + (", colour map" if colour_map is not None else ", tinted by slope")
    return points, np.concatenate(faces_all), colours, (heights, x0, z0, spacing)


# ---------------------------------------------------------------------------
# The whole level


@dataclass
class LegacyLevelModel:
    name: str
    points: list = field(default_factory=list)
    colours: list = field(default_factory=list)
    parts: dict[str, list] = field(default_factory=dict)
    count: int = 0
    report: dict = field(default_factory=dict)
    heightfield: tuple | None = None

    def add(self, part: str, points: np.ndarray, faces: np.ndarray, colour) -> None:
        self.points.append(points.astype(np.float32))
        c = np.empty((len(points), 3), np.float32)
        c[:] = colour
        self.colours.append(c if np.ndim(colour) == 1 else colour.astype(np.float32))
        self.parts.setdefault(part, []).append(faces + self.count)
        self.count += len(points)

    def triangles(self) -> int:
        return sum(len(f) for faces in self.parts.values() for f in faces)


def build_legacy_level(install: str | Path | LegacyInstall, level: str, budget: int = BUDGET, log=print) -> LegacyLevelModel:
    from .frostbitelevel import place
    from .legacyterrain import chunk_table

    game = install if isinstance(install, LegacyInstall) else LegacyInstall(install)
    world = World(game, level)
    root_name = level_root(world)
    root = world.partition(root_name)
    # The table's name, in the level's own spelling where that is the same name.
    own = str(root.instances[0].get("Name") or "").replace("\\", "/").rsplit("/", 1)[-1] if root else ""
    display = own if own.lower() == str(world.level.name).lower() else str(world.level.name)
    model = LegacyLevelModel(display)
    report = model.report
    placed = walk(world, root_name)
    keep = {n: v for n, v in placed.meshes.items()
            if not (EFFECTS.search(n) or CINEMATIC.search(n) or LIGHTING.search(n) or NOT_SURFACE.search(n))}
    report["placed meshes"] = len(keep)
    report["placed copies"] = sum(len(v) for v in keep.values())
    report["group copies"] = f"{placed.group_copies - placed.group_missing} of {placed.group_copies} in {placed.groups} groups"
    for note in placed.notes[:20]:
        log(f"  note: {note}")
    meshes = _load_meshes(world, keep, report)
    # Copies with a vanishing scale are not drawn.
    copies = {}
    for n in meshes:
        rows = np.array(keep[n])
        det = np.abs(np.linalg.det(rows[:, :3, :3]))
        keep[n] = rows[det > 1e-6]
        copies[n] = len(keep[n])
    chosen = _choose(meshes, copies, budget)
    chunks = chunk_table(game)
    origins = []
    for n, info in sorted(meshes.items()):
        if not copies[n]:
            continue
        index = chosen[n]
        if index < 0:
            report["left out for the budget"] = report.get("left out for the budget", 0) + 1
            continue
        while True:
            try:
                sections = _geometry(world, info, index, chunks)
                break
            except UnsupportedFrostbite as exc:
                if index + 1 < len(info.mesh.lods):
                    index += 1
                    continue
                report[f"unread: {str(exc)[-60:]}"] = report.get(f"unread: {str(exc)[-60:]}", 0) + 1
                sections = []
                break
        if not sections:
            continue
        rows = keep[n]
        origins.append(rows[:, 3, :3])
        part = category(n, [s.material for s in sections])
        colour = np.array(COLOURS.get(part, COLOURS["structure:props"]), np.float32)
        pts = np.concatenate([s.positions for s in sections])
        faces, base = [], 0
        for s in sections:
            faces.append(s.faces + base)
            base += len(s.positions)
        faces = np.concatenate(faces)
        world_pts = place(pts, rows)
        k = len(pts)
        all_faces = (faces[None, :, :] + (np.arange(len(rows)) * k)[:, None, None]).reshape(-1, 3)
        # A mirrored copy (negative determinant) turns its triangles over.
        flip = np.linalg.det(rows[:, :3, :3]) < 0
        if flip.any():
            per = len(faces)
            mask = np.repeat(flip, per)
            all_faces[mask] = all_faces[mask][:, ::-1]
        model.add(part, world_pts, all_faces, colour)
    if origins:
        o = np.concatenate(origins)
        lo = np.percentile(o[:, [0, 2]], 1, axis=0) - MARGIN
        hi = np.percentile(o[:, [0, 2]], 99, axis=0) + MARGIN
        play = (lo[0], lo[1], hi[0], hi[1])
    else:
        play = None
    ground = terrain(game, level, play, report)
    if ground is not None:
        points, faces, colours, heightfield = ground
        model.add("ground:terrain", points, faces, colours)
        model.heightfield = heightfield
    report["triangles"] = model.triangles()
    return model


def write_legacy_level(model: LegacyLevelModel, out: str | Path, game: str) -> Path:
    from heat3d_gamefiles.glb import Part, write_glb

    if not model.parts:
        raise UnsupportedFrostbite("nothing was placed and there is no terrain")
    parts = []
    for name in sorted(model.parts, key=lambda n: (not n.startswith("ground"), n)):
        # The game and level ride on every part's name, so a viewer can tell
        # which map a loaded model is (`structure:buildings @battlefield-4/MP_Prison`).
        parts.append(Part(name=f"{name} @{game}/{model.name}", faces=np.concatenate(model.parts[name])))
    return write_glb(
        out,
        np.concatenate(model.points),
        parts=parts,
        colours=np.concatenate(model.colours),
        extras={"game": game, "level": model.name, "source": "heat3d-battlefield-maps"},
    )
