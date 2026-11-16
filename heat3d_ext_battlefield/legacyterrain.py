"""
The terrain heightfield of a Battlefield 4 or Battlefield 1 level.

The older Frostbite keeps a level's terrain the way the later one does (see
`frostbiteterrain`): one **TerrainStreamingTree** resource and the chunks its
quadtree of streaming nodes names. The details differ; each one below was
measured on shipped levels and checked against something independent of it.

The resource
------------
::

    header          34 bytes, little-endian: the node count (u32) at 21, the
                    samples a side of a height page (u32) at 31
    raster trees    from 34, ended by a 0xFF byte; the heightfield's header
                    comes first: the height range (f32) at 47 and the
                    terrain's bounding box (x, y, z min, then max; six f32)
                    at 108
    streaming nodes the quadtree, depth first, to the last byte

The raster trees in between are not read: their length fields do not chain
the way the later layout's do. The quadtree is found from the back instead:
the one offset after a 0xFF byte from which it parses to the last byte with
the declared node count. Its records are the later layout's::

    u32 size, GUID                   its chunk (all zero: none)
    u8 has-second [u32 size, GUID]   an optional second chunk
    u8 flags, u8 has-children        then four children: (0,0), (1,0), (1,1), (0,1)

The flags do not say which chunks hold heights here (most nodes with heights
have flags 0). Chunks are in the level's bundles or, mostly, in the shared
chunk tables (`...Chunks*.toc`, by hash or by offset into the `.sb` beside
them); `ChunkTable` reads those, newest layer first.

The height page
---------------
The first `S x S` little-endian 16-bit words of a node's chunk, row by row,
height = word x range / 65,535 metres, no offset. `S` is a power of two plus
a border on each side and one: 69, 133 and 261 with a border of 2, 265 with
a border of 4. Columns run along world x and rows along world z from the
node's low corner; sample `border + k` is `k` sample steps into the node.
Measured on the 63 multiplayer levels with a terrain of the two games (34
and 29; two more have none):

- neighbouring pages share their `2 x border + 1` edge lines exactly: 86,683
  of 86,730 lines (the other 47 in 12 levels);
- every page taken equals its parent at every second sample in its quadrant,
  outside holes (9,517 pages); this fixes the border, the stride and the
  child order;
- the lowest decoded height equals the box's lowest y within 0.01 m in 60
  levels and within 0.25 m in the other three;
- of the eight ways the square could lie on the world (two axes, two signs
  each), only x along x and z along z, unflipped, puts the spawn points on it.
  On six levels examined in detail (three of each game) 91 to 100 % of
  spawn points are within 0.5 m of the surface in the four open ones,
  median 0.01 to 0.02 m, where every other way gives at most 36 % and
  medians of 1 to 37 m. In two built-up levels most spawns are indoors or on
  structures above or inside the terrain (median 9 and 38 m), and the
  orientation still wins: 14 and 25 % on the surface against at most 3 %.
  Over all levels with spawn points found, the median spawn is within
  0.1 m of the surface in 43 of 50.

Which chunks hold a page does not follow from the records, and a chunk's
length alone does not settle it. A chunk long enough is taken when its
samples equal the page above it (at every `2**k`-th sample for a page `k`
levels up); one with no page above it when a child agrees with it, or,
having no child page, when an edge of it equals a neighbour's. The chunks
this rejects (822 of 10,339 checked) are colour and mask data: in the ones
inspected nearly every sample differs.

Holes
-----
Where a level's declared lowest point is above word 0, word 0 marks a cut
out of the terrain (tunnels, bunkers): a child's samples are 0 exactly where
the samples it disagrees with its parent on lie, and nowhere else in the
levels checked. `read_heightfield` gives NaN there by default.

The colormap
------------
In Battlefield 1 a chunk's last 67,600 bytes are its node's colormap: BC3,
260 x 260 texels (256 and a border of two), rows along z, columns along x;
nodes without heights below the finest height pages carry a chunk of
exactly that page. Evidence: the border texels equal the neighbour's edge
texels (mean difference 0.0 over 746 shared edges of one level), and a page
halved matches its parent's quadrant (mean 2.45 of 255) where the seven other
orientations give 15 to 30. In Battlefield 4 the same bytes read so agree
with nothing (the candidates decode to flat grey or noise) and no colour is
read.

Superbundles not in cas mode
----------------------------
Some expansion levels of Battlefield 4 keep their bundles whole in the
superbundle; `FlatLevel` reads those. A patch's bundle stored as a
difference is read from its unpatched copy (the terrain chunks still come
from the newest chunk tables).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .frostbite import UnsupportedFrostbite, decompress_payload
from .legacy import LegacyInstall, apply_delta, read_toc

#: The res type of a terrain's streaming tree, as bundle manifests give it.
STREAMING_TREE = 0x22FE8AC8

#: Fixed places in the resource, from its first byte.
NODE_COUNT_AT = 21
SAMPLES_AT = 31
HEIGHT_RANGE_AT = 47
BOX_AT = 108
#: The raster trees start here; their end is marked by a 0xFF byte.
TREES_AT = 34
END = 0xFF

#: Samples a height page may have outside its node on each side, measured:
#: 2 on pages of 69, 133 and 261 samples, 4 on pages of 265.
BORDERS = (2, 4)
#: The share of a page's samples that must equal its parent's.
AGREEMENT = 0.9
#: The word of a cut-out sample (a hole in the terrain), in levels whose
#: declared lowest point is above it.
HOLE = 0


@dataclass
class Node:
    depth: int
    ix: int
    iz: int
    size: int
    chunk: bytes
    flags: int
    second: bytes | None = None


@dataclass
class LegacyTerrainTree:
    samples: int
    height_range: float
    #: x0, z0, x1, z1 of the terrain square, in world metres.
    square: tuple[float, float, float, float]
    #: Lowest and highest terrain height the resource declares, metres.
    heights: tuple[float, float]
    nodes: list[Node] = field(default_factory=list)
    #: Where the node quadtree starts in the resource.
    quadtree_at: int = 0
    border: int = 2

    @property
    def stride(self) -> int:
        return self.samples - 2 * self.border - 1

    @property
    def side(self) -> float:
        return self.square[2] - self.square[0]

    @property
    def has_holes(self) -> bool:
        """Whether word 0 marks holes: true when the lowest point is above it."""
        return self.heights[0] * 65535.0 / self.height_range >= 0.5


def _parse_nodes(res: bytes, at: int) -> tuple[int, list[Node]]:
    nodes: list[Node] = []

    def node(at: int, depth: int, ix: int, iz: int) -> int:
        size = struct.unpack_from("<I", res, at)[0]
        chunk = res[at + 4 : at + 20]
        at += 20
        second = None
        if res[at] == 1:
            second = res[at + 5 : at + 21]
            at += 21
        elif res[at] == 0:
            at += 1
        else:
            raise ValueError
        flags, children = res[at], res[at + 1]
        if children > 1 or depth > 16:
            raise ValueError
        at += 2
        nodes.append(Node(depth, ix, iz, size, chunk, flags, second))
        if children:
            for dx, dz in ((0, 0), (1, 0), (1, 1), (0, 1)):
                at = node(at, depth + 1, 2 * ix + dx, 2 * iz + dz)
        return at

    return node(at, 0, 0, 0), nodes


def read_tree(res: bytes, name: str = "terrain") -> LegacyTerrainTree:
    """The heightfield's parameters and the streaming quadtree of a terrain."""
    if len(res) < BOX_AT + 24:
        raise UnsupportedFrostbite(f"{name}: too short for a terrain streaming tree")
    (count,) = struct.unpack_from("<I", res, NODE_COUNT_AT)
    (samples,) = struct.unpack_from("<I", res, SAMPLES_AT)
    (height_range,) = struct.unpack_from("<f", res, HEIGHT_RANGE_AT)
    box = struct.unpack_from("<6f", res, BOX_AT)
    side = box[3] - box[0]
    border = next((b for b in BORDERS if samples - 2 * b - 1 > 0 and not (samples - 2 * b - 2) & (samples - 2 * b - 1)), None)
    if border is None:
        raise UnsupportedFrostbite(f"{name}: {samples} samples a side is not a power of two plus a border")
    if not (height_range > 0 and side > 0 and abs((box[5] - box[2]) - side) < 1e-3):
        raise UnsupportedFrostbite(f"{name}: the heightfield header does not hold a square and a height range")

    # The quadtree runs to the last byte and follows the raster trees' end
    # marker. Searched from the back: the one start after a 0xFF byte from
    # which it parses to the end with the declared node count.
    for at in range(len(res) - 23, TREES_AT, -1):
        if res[at - 1] != END:
            continue
        try:
            end, nodes = _parse_nodes(res, at)
        except (ValueError, struct.error, IndexError, RecursionError):
            continue
        if end == len(res) and len(nodes) == count:
            break
    else:
        raise UnsupportedFrostbite(f"{name}: no node quadtree of {count} nodes ends the resource")
    return LegacyTerrainTree(
        samples, height_range, (box[0], box[2], box[3], box[5]), (box[1], box[4]), nodes, at, border
    )


# ---------------------------------------------------------------------------
# Finding the bytes


def _cas_raw(store, sha1: bytes) -> bytes | None:
    """A payload by hash, also when the hash ends in zero bytes."""
    keys = store.keys
    i = int(np.searchsorted(keys, np.bytes_(sha1)))
    # The table's fixed-width hashes lose trailing zero bytes; compare likewise.
    if i < len(keys) and keys[i] == sha1.rstrip(b"\x00"):
        row = store.table[i]
        path = store.folders[int(row["folder"])] / f"cas_{int(row['cas']):02d}.cas"
        with open(path, "rb") as handle:
            handle.seek(int(row["offset"]))
            return handle.read(int(row["size"]))
    return None


def _by_hash(install: LegacyInstall, sha1: bytes) -> bytes | None:
    store = install.store
    raw = _cas_raw(store, sha1)
    if raw is not None:
        return decompress_payload(raw)
    if sha1 in store.patches:
        base, delta = store.patches[sha1]
        base_raw, delta_raw = _cas_raw(store, base), _cas_raw(store, delta)
        if base_raw is not None and delta_raw is not None:
            return decompress_payload(apply_delta(base_raw, delta_raw))
    return None


def _chain_end(data: bytes, at: int, size: int) -> int:
    """Where a chain of blocks that decompresses to `size` bytes ends."""
    got = 0
    while got < size:
        block, _method, stored = struct.unpack_from(">IHH", data, at)
        at += 8 + (stored or block)
        got += block
    return at


class ChunkTable:
    """
    Every chunk the install's chunk tables list (the `...Chunks*.toc` files),
    newest layer first. A row names its chunk by hash (cas tables) or by an
    offset and size into the `.sb` beside the table.
    """

    def __init__(self, install: LegacyInstall):
        self.install = install
        self.rows: dict[bytes, list[tuple]] = {}
        for layer in install.layers:
            for toc in sorted(layer.glob("Win32/**/*.toc")):
                if "chunks" not in toc.stem.lower():
                    continue
                for item in read_toc(toc).get("chunks") or []:
                    if not isinstance(item, dict) or not isinstance(item.get("id"), bytes):
                        continue
                    if "sha1" in item:
                        row = ("sha1", item["sha1"])
                    else:
                        row = ("sb", toc.with_suffix(".sb"), int(item["offset"]), int(item["size"]))
                    self.rows.setdefault(item["id"], []).append(row)

    def __contains__(self, guid: bytes) -> bool:
        return guid in self.rows

    def get(self, guid: bytes) -> bytes | None:
        for row in self.rows.get(guid, ()):
            if row[0] == "sha1":
                data = _by_hash(self.install, row[1])
                if data is not None:
                    return data
                continue
            with open(row[1], "rb") as handle:
                handle.seek(row[2])
                return decompress_payload(handle.read(row[3]))
        return None


def chunk_table(install: LegacyInstall) -> ChunkTable:
    table = getattr(install, "_terrain_chunk_table", None)
    if table is None:
        table = ChunkTable(install)
        install._terrain_chunk_table = table
    return table


def read_binary_bundle(sb: bytes, at: int) -> dict:
    """
    A bundle stored whole in a superbundle that is not in cas mode: a
    big-endian header (its size, a magic word, the entry counts, where its
    names and metadata are), the entries' hashes, the ebx and res entries
    (name offset, size; then the res types, metadata and ids), the chunk
    entries, and after the header every payload, ebx then res then chunks,
    each a chain of blocks. Returns name -> payload getter for ebx and res.
    """
    size, _magic = struct.unpack_from(">II", sb, at)
    head = at + 4
    total, n_ebx, n_res, n_chunks, names, _meta, _meta_size = struct.unpack_from(">7I", sb, head + 4)
    p = head + 32 + 20 * total

    def name(offset: int) -> str:
        start = head + names + offset
        return sb[start : sb.index(b"\x00", start)].decode("utf-8", "replace").lower()

    entries = []
    for _ in range(n_ebx + n_res):
        offset, original = struct.unpack_from(">II", sb, p)
        entries.append([name(offset), original, 0])
        p += 8
    for entry in entries[n_ebx:]:
        entry[2] = struct.unpack_from(">I", sb, p)[0]
        p += 4
    at = head + size
    ebx: dict[str, bytes] = {}
    res: dict[str, tuple[int, bytes]] = {}
    for i, (key, original, kind) in enumerate(entries):
        end = _chain_end(sb, at, original)
        if i < n_ebx:
            ebx[key] = (at, end)
        else:
            res[key] = (kind, (at, end))
        at = end
    return {"ebx": ebx, "res": res}


class FlatLevel:
    """
    A level whose superbundle is not in cas mode (an expansion level of
    Battlefield 4): its bundles' ebx and res, read from the superbundle. A
    patch table's bundle marked `base` is read from the base superbundle at
    the offset given; one marked `delta` is read whole from the base table's
    bundle of the same name (so a patch's edits to it are not applied).
    """

    def __init__(self, install: LegacyInstall, name: str):
        tocs = install.level_tocs().get(name.lower())
        if not tocs:
            raise UnsupportedFrostbite(f"no level called {name!r}")
        self.ebx: dict[str, tuple[Path, tuple[int, int]]] = {}
        self.res: dict[str, tuple[int, Path, tuple[int, int]]] = {}
        newest = read_toc(tocs[0])
        bases = [(t, read_toc(t)) for t in tocs[1:]]
        base_bundles = {}
        for toc, tree in bases:
            for bundle in tree.get("bundles") or []:
                base_bundles.setdefault(str(bundle.get("id", "")).lower(), (toc.with_suffix(".sb"), bundle))
        cache: dict[Path, bytes] = {}

        def sb_of(path: Path) -> bytes:
            if path not in cache:
                cache[path] = path.read_bytes()
            return cache[path]

        for bundle in newest.get("bundles") or []:
            key = str(bundle.get("id", "")).lower()
            if bundle.get("delta") or bundle.get("base"):
                if key not in base_bundles:
                    continue
                path, source = base_bundles[key]
                offset = int(bundle["offset"]) if bundle.get("base") else int(source["offset"])
            else:
                path, offset = tocs[0].with_suffix(".sb"), int(bundle["offset"])
            body = read_binary_bundle(sb_of(path), offset)
            for n, span in body["ebx"].items():
                self.ebx.setdefault(n, (path, span))
            for n, (kind, span) in body["res"].items():
                self.res.setdefault(n, (kind, path, span))
        self._cache = cache

    def payload(self, path: Path, span: tuple[int, int]) -> bytes:
        return decompress_payload(self._cache[path][span[0] : span[1]])


def _streaming_tree(install: LegacyInstall, level: str) -> tuple[bytes, dict]:
    """The level's terrain streaming tree and the chunks its own bundles carry."""
    try:
        lv = install.open_level(level)
    except UnsupportedFrostbite as exc:
        if "cas mode" not in str(exc):
            raise
        flat = FlatLevel(install, level)
        trees = sorted(n for n, (kind, _p, _s) in flat.res.items() if kind == STREAMING_TREE)
        if not trees:
            raise UnsupportedFrostbite(f"{level}: no terrain streaming tree") from exc
        _kind, path, span = flat.res[trees[0]]
        return flat.payload(path, span), {}
    trees = sorted(n for n, e in lv.res.items() if e.res_type == STREAMING_TREE)
    if not trees:
        raise UnsupportedFrostbite(f"{level}: no terrain streaming tree")
    return install.payload(lv.res[trees[0]]), lv.chunks


# ---------------------------------------------------------------------------
# Height pages


def height_page(tree: LegacyTerrainTree, chunk: bytes) -> np.ndarray:
    """The raw words of a chunk's height page, (samples, samples), rows along z."""
    n = tree.samples
    return np.frombuffer(chunk, dtype="<u2", count=n * n).reshape(n, n)


@dataclass
class Pages:
    """A terrain's height pages that passed the checks, and the evidence."""

    tree: LegacyTerrainTree
    #: (depth, ix, iz) -> raw words.
    pages: dict[tuple[int, int, int], np.ndarray]
    #: Chunks that hold a page by length but contradict their parent.
    rejected: int = 0
    #: Pages checked against their parent: every second sample that is not a
    #: hole equal, at least `AGREEMENT` of them equal, and how many checked.
    #: The levels checked have no page in the second group.
    parent_agree: tuple[int, int, int] = (0, 0, 0)
    #: Shared border lines between same-depth neighbours: exact, compared.
    border_agree: tuple[int, int] = (0, 0)
    #: Pages with no page above them, accepted on their children or neighbours.
    roots: int = 0
    missing_chunks: int = 0


def _agreement(tree: LegacyTerrainTree, page: np.ndarray, above: np.ndarray, key, up: int) -> float:
    """The share of a page's samples equal to those of the page `up` levels above it."""
    _d, ix, iz = key
    b, t = tree.border, tree.stride
    step, part = 1 << up, tree.stride >> up
    r0 = b + part * (iz & (step - 1))
    c0 = b + part * (ix & (step - 1))
    mine = page[b : b + t + 1 : step, b : b + t + 1 : step]
    same = mine == above[r0 : r0 + part + 1, c0 : c0 + part + 1]
    if tree.has_holes:
        same = same[mine != HOLE]
    return float(np.mean(same)) if same.size else 0.0


def _shares_edge(tree: LegacyTerrainTree, page: np.ndarray, key, pages: dict) -> bool:
    """Whether a page's edge line equals that of a same-depth neighbour."""
    d, ix, iz = key
    b, t = tree.border, tree.stride
    for (dx, dz), axis in (((1, 0), 1), ((-1, 0), 1), ((0, 1), 0), ((0, -1), 0)):
        other = pages.get((d, ix + dx, iz + dz))
        if other is None:
            continue
        mine, theirs = (b + t, b) if dx + dz > 0 else (b, b + t)
        if np.array_equal(np.take(page, mine, axis=axis), np.take(other, theirs, axis=axis)):
            return True
    return False


def _border_lines(tree: LegacyTerrainTree, pages: dict) -> tuple[int, int]:
    exact = compared = 0
    b, t = tree.border, tree.stride
    for (d, ix, iz), a in pages.items():
        for other, axis in (((d, ix + 1, iz), 1), ((d, ix, iz + 1), 0)):
            c = pages.get(other)
            if c is None:
                continue
            for k in range(-b, b + 1):
                compared += 1
                exact += np.array_equal(np.take(a, b + t + k, axis=axis), np.take(c, b + k, axis=axis))
    return exact, compared


def read_pages(install: LegacyInstall, level: str) -> Pages:
    """
    The level's height pages, each checked against the page above it: a
    chunk long enough to hold a page is taken only if at least `AGREEMENT` of
    its every-second samples equal its parent's page there (all of them, but
    for pages edited after their parent was made). A page with no page above it is taken
    if a child agrees with it, or, having no child page, if an edge of it
    equals a neighbour's. Pages below a rejected one are checked against the
    nearest page above them, at every 2**k-th sample.
    """
    res, own = _streaming_tree(install, level)
    tree = read_tree(res, level)
    table = chunk_table(install)
    need = tree.samples * tree.samples * 2
    candidates: dict[tuple[int, int, int], np.ndarray] = {}
    missing = 0
    for node in tree.nodes:
        if not any(node.chunk) or node.size < need:
            continue
        data = table.get(node.chunk) if node.chunk in table else None
        if data is None and node.chunk in own:
            data = install.payload(own[node.chunk])
        if data is None:
            missing += 1
            continue
        if len(data) >= need:
            candidates[(node.depth, node.ix, node.iz)] = height_page(tree, data)

    pages: dict[tuple[int, int, int], np.ndarray] = {}
    pending: dict[tuple[int, int, int], np.ndarray] = {}
    rejected = exact = near = checked = roots = 0
    for key in sorted(candidates):
        d, ix, iz = key
        up = next((k for k in range(1, d + 1) if (d - k, ix >> k, iz >> k) in pages), 0)
        page = candidates[key]
        if up:
            checked += 1
            share = _agreement(tree, page, pages[(d - up, ix >> up, iz >> up)], key, up)
            if share >= AGREEMENT:
                exact += share == 1.0
                near += share < 1.0
                pages[key] = page
            else:
                rejected += 1
            continue
        kids = [(d + 1, 2 * ix + a, 2 * iz + b) for a in (0, 1) for b in (0, 1)]
        kids = [k for k in kids if k in candidates]
        if any(_agreement(tree, candidates[k], page, k, 1) >= AGREEMENT for k in kids):
            pages[key] = page
            roots += 1
        elif not kids:
            pending[key] = page
        else:
            rejected += 1
    # A page with nothing above or below it to check against is taken when an
    # edge of it equals a neighbour's.
    while pending:
        taken = [k for k, page in pending.items() if _shares_edge(tree, page, k, {**pages, **pending})]
        rejected += len(pending) - len(taken)
        for k in taken:
            pages[k] = pending[k]
            roots += 1
        break
    if not pages:
        raise UnsupportedFrostbite(f"{level}: no streaming node carries a height page")
    return Pages(tree, pages, rejected, (exact, near, checked), _border_lines(tree, pages), roots, missing)


# ---------------------------------------------------------------------------
# The grid


def _sample(page: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Bilinear samples of a page at fractional (column u, row v)."""
    n = page.shape[0]
    u0 = np.clip(np.floor(u).astype(np.int64), 0, n - 2)
    v0 = np.clip(np.floor(v).astype(np.int64), 0, n - 2)
    fu = (u - u0)[None, :]
    fv = (v - v0)[:, None]
    p = page.astype(np.float64)
    a = p[np.ix_(v0, u0)]
    b = p[np.ix_(v0, u0 + 1)]
    c = p[np.ix_(v0 + 1, u0)]
    e = p[np.ix_(v0 + 1, u0 + 1)]
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + e * fu) * fv


def heightfield_from_pages(found: Pages, max_size: int = 4096, holes: bool = True):
    """See `read_heightfield`."""
    tree = found.tree
    x0, z0, _x1, _z1 = tree.square
    side = tree.side
    finest = max(d for d, _ix, _iz in found.pages)
    spacing = side / (1 << finest) / tree.stride
    while side / spacing > max_size:
        spacing *= 2
    n = int(round(side / spacing))
    grid = np.full((n, n), np.nan, dtype=np.float32)
    scale = tree.height_range / 65535.0
    for key in sorted(found.pages):
        d, ix, iz = key
        span = side / (1 << d)
        cell = span / tree.stride
        lo_c = int(np.ceil(ix * span / spacing - 1e-9))
        hi_c = min(n - 1, int(np.floor((ix + 1) * span / spacing + 1e-9)))
        lo_r = int(np.ceil(iz * span / spacing - 1e-9))
        hi_r = min(n - 1, int(np.floor((iz + 1) * span / spacing + 1e-9)))
        if hi_c < lo_c or hi_r < lo_r:
            continue
        u = tree.border + (np.arange(lo_c, hi_c + 1) * spacing - ix * span) / cell
        v = tree.border + (np.arange(lo_r, hi_r + 1) * spacing - iz * span) / cell
        page = found.pages[key]
        values = _sample(page, u, v) * scale
        if tree.has_holes:
            # A sample touched by a hole sample is a hole.
            cut = _sample((page == HOLE).astype(np.float32), u, v) > 0
            if holes:
                values[cut] = np.nan
            else:
                values[cut] = grid[lo_r : hi_r + 1, lo_c : hi_c + 1][cut]
        grid[lo_r : hi_r + 1, lo_c : hi_c + 1] = values
    return grid, x0, z0, spacing


def read_heightfield(install: LegacyInstall, level: str, max_size: int = 4096, holes: bool = True):
    """
    A level's terrain as one grid: `(heights, x0, z0, spacing)`.

    `heights[r, c]` is the height in metres (y up) at world x = x0 + c *
    spacing, z = z0 + r * spacing; rows run along z, columns along x. The grid
    spans the terrain square from its low corner, `side / spacing` samples a
    side (the far edge's samples are left out). Each sample comes from the
    finest verified page that covers it; `spacing` is that page's sample
    distance, doubled until a side has at most `max_size` samples. NaN where
    no page covers the square, and in holes (`holes=False` keeps the next
    coarser page's height there instead).
    """
    return heightfield_from_pages(read_pages(install, level), max_size, holes)


def height_at(grid: np.ndarray, x0: float, z0: float, spacing: float, x, z) -> np.ndarray:
    """Bilinear heights of a `read_heightfield` grid at world (x, z); NaN outside."""
    x = np.asarray(x, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    u = (x - x0) / spacing
    v = (z - z0) / spacing
    n_r, n_c = grid.shape
    inside = (u >= 0) & (v >= 0) & (u <= n_c - 1) & (v <= n_r - 1)
    u0 = np.clip(np.floor(u).astype(np.int64), 0, n_c - 2)
    v0 = np.clip(np.floor(v).astype(np.int64), 0, n_r - 2)
    fu, fv = u - u0, v - v0
    g = grid.astype(np.float64)
    h = (g[v0, u0] * (1 - fu) + g[v0, u0 + 1] * fu) * (1 - fv) + (g[v0 + 1, u0] * (1 - fu) + g[v0 + 1, u0 + 1] * fu) * fv
    return np.where(inside, h, np.nan)


# ---------------------------------------------------------------------------
# The colormap (Battlefield 1)

#: A colormap page: BC3 (DXT5), 260 x 260 texels, the node's 256 and a border
#: of two, 67,600 bytes; the last bytes of its node's chunk, or the whole chunk.
COLOUR_SIDE = 260
COLOUR_BORDER = 2
COLOUR_BYTES = (COLOUR_SIDE // 4) ** 2 * 16
#: Mean difference (0..255) under which two pages are taken to agree: on a
#: shared edge (the borders are copies of the neighbour's texels) and between
#: a page halved and its parent's quadrant. Pages that are colormaps meet
#: these at 0 to 1 and 2 to 8; other bytes read as one at 37 and more.
SEAM_AGREES = 1.0
PARENT_AGREES = 8.0


def _bc3_rgb(data: bytes, side: int) -> np.ndarray:
    """The colour of a BC3 image, (side, side, 3) uint8; alpha is ignored."""
    blocks = np.frombuffer(data, dtype=np.uint8).reshape(-1, 16)[:, 8:]
    ends = blocks[:, :4].copy().view("<u2")
    bits = blocks[:, 4:].copy().view("<u4")[:, 0]

    def rgb565(c):
        c = c.astype(np.int32)
        return np.stack([(c >> 11 & 31) * 255 // 31, (c >> 5 & 63) * 255 // 63, (c & 31) * 255 // 31], -1)

    c0, c1 = rgb565(ends[:, 0]), rgb565(ends[:, 1])
    palette = np.stack([c0, c1, (2 * c0 + c1) // 3, (c0 + 2 * c1) // 3], 1)
    index = (bits[:, None] >> (2 * np.arange(16, dtype=np.uint32))) & 3
    texels = np.take_along_axis(palette, index[:, :, None].astype(np.int64), 1)
    n = side // 4
    return texels.reshape(n, n, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(side, side, 3).astype(np.uint8)


def _colour_agrees(pages: dict, key) -> bool:
    d, ix, iz = key
    a = pages[key].astype(np.float32)
    b, n = COLOUR_BORDER, COLOUR_SIDE - 2 * COLOUR_BORDER
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        other = pages.get((d, ix + dx, iz + dz))
        if other is None:
            continue
        lo, hi = (a, other.astype(np.float32)) if dx + dz > 0 else (other.astype(np.float32), a)
        if dx:
            edge = np.abs(lo[b : b + n, n : n + b] - hi[b : b + n, 0:b]).mean()
        else:
            edge = np.abs(lo[n : n + b, b : b + n] - hi[0:b, b : b + n]).mean()
        if edge <= SEAM_AGREES:
            return True
    h = n // 2

    def halved_matches(child, ckey, parent):
        q = parent[b:-b, b:-b][h * (ckey[2] & 1) : h * (ckey[2] & 1) + h, h * (ckey[1] & 1) : h * (ckey[1] & 1) + h]
        small = child[b:-b, b:-b].astype(np.float32).reshape(h, 2, h, 2, 3).mean((1, 3))
        return np.abs(small - q).mean() <= PARENT_AGREES

    parent = pages.get((d - 1, ix >> 1, iz >> 1))
    if parent is not None and halved_matches(a, key, parent.astype(np.float32)):
        return True
    kids = [(d + 1, 2 * ix + p, 2 * iz + q) for p in (0, 1) for q in (0, 1)]
    return any(k in pages and halved_matches(pages[k], k, a) for k in kids)


def read_colormap(install: LegacyInstall, level: str, max_size: int = 4096):
    """
    The terrain's colormap as one image, `(rgb, x0, z0, spacing)`, or None
    when the level's chunks carry none in the form described above (the
    Battlefield 4 levels checked have none: their chunks' last bytes, read
    so, agree with nothing). A chunk's last 67,600 bytes are taken for its
    node's colormap page when they agree with a neighbour's page on their
    shared edge, or with the page above or below them; see `SEAM_AGREES`.

    `rgb[r, c]` (uint8) is the colour of the texel centred on world x = x0 +
    (c + 0.5) * spacing, z = z0 + (r + 0.5) * spacing, rows along z. Finer
    pages over coarser ones; pages coarser than `spacing` are repeated,
    finer ones averaged; zero where no page covers the square.
    """
    res, own = _streaming_tree(install, level)
    tree = read_tree(res, level)
    table = chunk_table(install)
    found: dict[tuple[int, int, int], np.ndarray] = {}
    for node in tree.nodes:
        if not any(node.chunk) or node.size < COLOUR_BYTES:
            continue
        data = table.get(node.chunk) if node.chunk in table else None
        if data is None and node.chunk in own:
            data = install.payload(own[node.chunk])
        if data is None or len(data) < COLOUR_BYTES:
            continue
        found[(node.depth, node.ix, node.iz)] = _bc3_rgb(data[-COLOUR_BYTES:], COLOUR_SIDE)
    found = {k: v for k, v in found.items() if _colour_agrees(found, k)}
    if not found:
        return None
    x0, z0, _x1, _z1 = tree.square
    side = tree.side
    inner = COLOUR_SIDE - 2 * COLOUR_BORDER
    finest = max(d for d, _ix, _iz in found)
    spacing = side / (1 << finest) / inner
    while side / spacing > max_size:
        spacing *= 2
    n = int(round(side / spacing))
    image = np.zeros((n, n, 3), dtype=np.uint8)
    for key in sorted(found):
        d, ix, iz = key
        page = found[key][COLOUR_BORDER:-COLOUR_BORDER, COLOUR_BORDER:-COLOUR_BORDER]
        cells = int(round(side / (1 << d) / spacing))
        if cells < inner:
            f = inner // cells
            page = page.reshape(cells, f, cells, f, 3).mean((1, 3)).round().astype(np.uint8)
        elif cells > inner:
            f = cells // inner
            page = page.repeat(f, 0).repeat(f, 1)
        image[iz * cells : (iz + 1) * cells, ix * cells : (ix + 1) * cells] = page
    return image, x0, z0, spacing
