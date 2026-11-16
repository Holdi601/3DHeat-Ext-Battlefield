"""
Older Frostbite installs: the superbundle form of Battlefield 4 and Battlefield 1.

Before the binary tables `frostbite` reads, Frostbite described its content in
DbObject trees throughout - the same tagged tree `frostbite.parse_toc` reads -
and kept the bytes in `cas_NN.cas` blobs named by the SHA-1 of what they hold.

The pieces
----------
`<level>.toc`   a signed header (556 bytes) and a tree: the level's bundles,
                each an offset and size into the `.sb` beside it, and whether
                the superbundle is in `cas` mode (every level here is).
`<level>.sb`    the bundles: one tree each, at the offset the toc names, listing
                the bundle's `ebx`, `res` and `chunks` by SHA-1, with their
                stored and original sizes, resource types and metadata.
`cas.cat`       which blob holds a SHA-1: twenty bytes of hash, then offset,
                size and blob number (and, in the later form, a further word
                before the blob number). One per data folder in Battlefield 4;
                one per install package in Battlefield 1.

The first form has no signed header and 32-byte records after sixteen bytes
of `NyanNyan...`; the second has the 556-byte header, the `Nyan` run, two
counts and 36-byte records. Which one a file is follows from its length:
the records fill the file exactly in one reading and not in the other.

Updates
-------
A patch ships its own table of the level. In Battlefield 4 each bundle of it is
flagged: `base` reads the bundle from the base game's superbundle at the
offset given, `delta` reads the patch's own copy (a complete bundle in `cas`
mode), and an unflagged one is new. Battlefield 1's patch table replaces the
base one outright. Either way the entries name hashes, and a hash is the same
bytes whichever `cas.cat` lists it, so every catalogue of the install is
searched.

An entry with `casPatchType` 2 is stored as a difference from an older version:
`baseSha1` names the old payload and `deltaSha1` the edit. See `apply_delta`.

Payloads
--------
The chain of eight-byte-headed blocks `frostbite.decompress_payload` reads;
in both games the blocks are LZ4 or stored. The signed header's magic ends in
01 (Battlefield 1) or 03 (Battlefield 4), and in both the tree follows the 556
bytes in the clear.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .frostbite import T_OBJECT, UnsupportedFrostbite, _Cursor, _read_value, decompress_payload

#: The bytes a signed Frostbite file starts with, and its header's length.
SIGNED_MAGIC = b"\x00\xd1\xce"
SIGNED_HEADER = 556
NYAN = b"Nyan" * 4

#: Game generations this module reads, by what the install holds.
BF4 = "bf4"
BF1 = "bf1"


def strip_signature(data: bytes) -> bytes:
    """A file's contents after its signed header, if it has one."""
    if data[:3] == SIGNED_MAGIC and len(data) >= SIGNED_HEADER:
        return data[SIGNED_HEADER:]
    return data


def read_tree(data: bytes, at: int = 0, name: str = "tree"):
    """One DbObject value starting at `at`."""
    cursor = _Cursor(data, at)
    type_byte = cursor.u8()
    if type_byte & 0x1F not in (T_OBJECT, 0x01):
        raise UnsupportedFrostbite(f"{name}: no DbObject at {at} (type 0x{type_byte:02X})")
    return _read_value(cursor, type_byte & 0x1F)


def read_toc(path: Path):
    return read_tree(strip_signature(path.read_bytes()), 0, path.name)


# ---------------------------------------------------------------------------
# cas.cat


def read_cat(path: Path) -> tuple[np.ndarray, dict[bytes, tuple[bytes, bytes]]]:
    """
    A `cas.cat` as a structured array (sha1, offset, size, cas), and the
    payloads it says are stored as differences: sha1 -> (base sha1, delta sha1).

    Two forms. Sixteen `Nyan` bytes and 32-byte records (hash, offset, size,
    blob), filling the file exactly; or a signed header, the `Nyan` run, two
    counts, that many 36-byte records (a word more before the blob number)
    and that many 60-byte records of three hashes each - a payload, the one
    it was edited from and the edit. The counts have to account for every
    byte of the file, or the file is refused.
    """
    data = strip_signature(path.read_bytes())
    if data[:16] != NYAN:
        raise UnsupportedFrostbite(f"{path} does not start with the catalogue marker")
    body = data[16:]
    patches: dict[bytes, tuple[bytes, bytes]] = {}
    count = width = None
    if len(body) >= 8:
        entries, edits = struct.unpack_from("<II", body, 0)
        if 8 + entries * 36 + edits * 60 == len(body):
            count, width, start = entries, 36, 8
            tail = body[8 + entries * 36 :]
            for i in range(edits):
                row = tail[i * 60 : i * 60 + 60]
                patches[row[:20]] = (row[20:40], row[40:60])
    if count is None:
        if len(body) % 32:
            raise UnsupportedFrostbite(f"{path}: the records do not fill the catalogue in either known form")
        count, width, start = len(body) // 32, 32, 0
    raw = np.frombuffer(body, np.uint8, count * width, start).reshape(count, width)
    out = np.empty(count, CAT_DTYPE)
    out["sha1"] = raw[:, :20].copy().view("S20").ravel()
    words = raw[:, 20:].copy().view("<u4")
    out["offset"], out["size"], out["cas"] = words[:, 0], words[:, 1], words[:, -1]
    out["folder"] = 0
    return out, patches


CAT_DTYPE = np.dtype([("sha1", "S20"), ("offset", "<u4"), ("size", "<u4"), ("cas", "<u4"), ("folder", "<u2")])


class CasStore:
    """Every `cas.cat` of an install, searched by SHA-1."""

    def __init__(self, cats: list[Path]):
        self.folders: list[Path] = []
        tables = []
        #: Payloads stored as an edit of an older one: sha1 -> (base, delta).
        self.patches: dict[bytes, tuple[bytes, bytes]] = {}
        for i, cat in enumerate(cats):
            table, patches = read_cat(cat)
            for key, value in patches.items():
                self.patches.setdefault(key, value)
            table["folder"] = i
            self.folders.append(cat.parent)
            tables.append(table)
        if not tables:
            raise UnsupportedFrostbite("no cas.cat found")
        joined = np.concatenate(tables)
        # Earlier catalogues (the patch) win a tie: stable sort keeps their order.
        order = np.argsort(joined["sha1"], kind="stable")
        self.table = joined[order]
        self.keys = self.table["sha1"]
        self._handles: dict[Path, object] = {}

    def __contains__(self, sha1: bytes) -> bool:
        return self.find(sha1) is not None

    def find(self, sha1: bytes):
        # A fixed-width byte column drops trailing zero bytes: a hash ending
        # in 0x00 is stored, sorted and compared without them.
        key = sha1.rstrip(b"\x00")
        i = int(np.searchsorted(self.keys, np.bytes_(key)))
        if i < len(self.keys) and self.keys[i] == key:
            return self.table[i]
        return None

    def raw(self, sha1: bytes) -> bytes:
        row = self.find(sha1)
        if row is None:
            raise UnsupportedFrostbite(f"payload {sha1.hex()} is in no cas.cat of the install")
        path = self.folders[int(row["folder"])] / f"cas_{int(row['cas']):02d}.cas"
        handle = self._handles.get(path)
        if handle is None:
            handle = self._handles[path] = open(path, "rb")
        handle.seek(int(row["offset"]))
        data = handle.read(int(row["size"]))
        if len(data) != int(row["size"]):
            raise UnsupportedFrostbite(f"{path.name} ends before {sha1.hex()} does")
        return data

    def close(self) -> None:
        for handle in self._handles.values():
            handle.close()
        self._handles.clear()


# ---------------------------------------------------------------------------
# Delta-stored payloads


def _blocks(data: bytes, at: int, count: int, out: bytearray) -> int:
    """Copy `count` whole blocks (header and body) from `data`, return the new offset."""
    for _ in range(count):
        size, method, stored = struct.unpack_from(">IHH", data, at)
        if stored == 0:
            stored = size
        out += data[at : at + 8 + stored]
        at += 8 + stored
    return at


def _one_block(data: bytes, at: int) -> tuple[bytes, int]:
    """One block decompressed, and where the next starts."""
    size, method, stored = struct.unpack_from(">IHH", data, at)
    if stored == 0:
        stored = size
    end = at + 8 + stored
    if size == 0:
        # An empty block: an edit that only removes bytes.
        return b"", end
    return decompress_payload(data[at:end]), end


def _stored(data: bytes) -> bytes:
    """Bytes as one or more uncompressed blocks, so a chain stays a chain."""
    out = bytearray()
    for start in range(0, len(data), 0xFFFF):
        piece = data[start : start + 0xFFFF]
        out += struct.pack(">IHH", len(piece), 0x0070, len(piece)) + piece
    return bytes(out)


def apply_delta(base: bytes, delta: bytes) -> bytes:
    """
    A payload rebuilt from an older one and a difference.

    The difference is a list of instructions, each a big-endian word whose top
    four bits are the kind and whose rest is a count:

        0  copy `count` blocks of the old payload as they are
        1  rewrite one old block: `count` (offset, skip) pairs of 16-bit
           words, each followed by a block of new bytes; old bytes up to
           `offset` are kept, then the new bytes, then `skip` old ones are
           dropped
        2  rewrite one old block from a compact edit: a 16-bit length of the
           rebuilt block and `count` bytes of (offset, skip, length, bytes)
           edits against it
        3  insert `count` blocks of the difference as they are
        4  skip `count` blocks of the old payload

    The result is again a chain of blocks; what was rewritten is stored
    uncompressed.
    """
    out = bytearray()
    b = d = 0
    while d < len(delta):
        (word,) = struct.unpack_from(">I", delta, d)
        d += 4
        kind, count = word >> 28, word & 0x0FFFFFFF
        if kind == 0:
            b = _blocks(base, b, count, out)
        elif kind == 1:
            old, b = _one_block(base, b)
            rebuilt = bytearray()
            kept = 0
            for _ in range(count):
                offset, skip = struct.unpack_from(">HH", delta, d)
                d += 4
                rebuilt += old[kept:offset]
                new, d = _one_block(delta, d)
                rebuilt += new
                kept = offset + skip
            rebuilt += old[kept:]
            out += _stored(bytes(rebuilt))
        elif kind == 2:
            old, b = _one_block(base, b)
            (length,) = struct.unpack_from(">H", delta, d)
            d += 2
            end = d + count
            rebuilt = bytearray()
            kept = 0
            while d < end:
                offset = struct.unpack_from(">H", delta, d)[0]
                skip = delta[d + 2]
                add = delta[d + 3]
                d += 4
                rebuilt += old[kept:offset]
                rebuilt += delta[d : d + add]
                d += add
                kept = offset + skip
            rebuilt += old[kept:]
            if len(rebuilt) != length + 1 and len(rebuilt) != length:
                raise UnsupportedFrostbite(
                    f"a compact edit rebuilt {len(rebuilt)} bytes where it declares {length}"
                )
            out += _stored(bytes(rebuilt))
        elif kind == 3:
            d = _blocks(delta, d, count, out)
        elif kind == 4:
            for _ in range(count):
                b = _one_block_skip(base, b)
        else:
            raise UnsupportedFrostbite(f"difference instruction {kind} is not known")
    return bytes(out)


def _one_block_skip(data: bytes, at: int) -> int:
    size, method, stored = struct.unpack_from(">IHH", data, at)
    return at + 8 + (stored or size)


# ---------------------------------------------------------------------------
# The install


@dataclass
class LegacyEntry:
    """One ebx, res or chunk of a level's bundles."""

    name: str
    sha1: bytes | None
    size: int = 0
    original: int = 0
    patch_type: int = 0
    base_sha1: bytes | None = None
    delta_sha1: bytes | None = None
    res_type: int = 0
    res_meta: bytes = b""
    logical_offset: int = 0
    logical_size: int = 0
    first_mip: int = -1
    bundle: str = ""
    #: For a bundle stored whole in its superbundle: the file and byte range.
    span: tuple | None = None


@dataclass
class LegacyLevel:
    """What one level's superbundle holds, by name and by chunk id."""

    name: str
    toc: Path
    ebx: dict[str, LegacyEntry] = field(default_factory=dict)
    res: dict[str, LegacyEntry] = field(default_factory=dict)
    chunks: dict[bytes, LegacyEntry] = field(default_factory=dict)
    bundles: list[str] = field(default_factory=list)


class LegacyInstall:
    """
    A Battlefield 4 or Battlefield 1 install: its catalogues and levels.

    `root` is the folder holding `Data` (and `Update` or `Patch`).
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        data = self.root / "Data"
        if not (data / "layout.toc").is_file():
            raise UnsupportedFrostbite(f"no Data\\layout.toc in {self.root}")
        if (self.root / "Patch").is_dir() and (data / "Win32" / "installation").is_dir():
            self.generation = BF1
            # Layers, newest first: the patch, then the base game.
            self.layers = [self.root / "Patch", data]
        elif (data / "cas.cat").is_file():
            self.generation = BF4
            update = self.root / "Update"
            packs = sorted(p / "Data" for p in update.iterdir() if (p / "Data").is_dir()) if update.is_dir() else []
            patch = [p for p in packs if p.parent.name.lower() == "patch"]
            self.layers = patch + [p for p in packs if p not in patch] + [data]
        else:
            raise UnsupportedFrostbite(
                f"{self.root} is a Frostbite install of a form this reader does not know"
            )
        self._store: CasStore | None = None
        self._all_chunks: dict[bytes, LegacyEntry] | None = None

    @property
    def store(self) -> CasStore:
        if self._store is None:
            cats = []
            for layer in self.layers:
                cats += sorted(layer.glob("**/cas.cat"))
            self._store = CasStore(cats)
        return self._store

    # -- levels --------------------------------------------------------------

    def level_tocs(self) -> dict[str, list[Path]]:
        """
        Every level table, by level name, newest layer first.

        A level sits in `.../levels/.../<folder>/<name>.toc` beside its `.sb`;
        tables of chunks only (`...LevelsChunks.toc`) are not levels.
        """
        found: dict[str, list[Path]] = {}
        for layer in self.layers:
            for toc in sorted(layer.glob("Win32/**/*.toc")):
                parts = [p.lower() for p in toc.relative_to(layer).parts]
                if "levels" not in parts[:-1] or not toc.with_suffix(".sb").is_file():
                    continue
                found.setdefault(toc.stem.lower(), []).append(toc)
        return found

    def multiplayer_levels(self) -> dict[str, list[Path]]:
        """The levels under an `mp` folder, or named `MP_`/`XP<n>_` (the expansions')."""
        out = {}
        for name, tocs in self.level_tocs().items():
            parts = [p.lower() for p in tocs[0].parts]
            if "sp" in parts or "frontend" in parts or name.startswith(("sp_", "coop_", "frontend")):
                continue
            if "mp" in parts or name.startswith(("mp_", "xp")):
                out[name] = tocs
        return out

    def _base_of(self, toc: Path) -> Path | None:
        """The same table in an older layer: what a patch's `base` bundles point into."""
        for layer in self.layers:
            try:
                rel = None
                for candidate in self.layers:
                    try:
                        rel = toc.relative_to(candidate)
                        break
                    except ValueError:
                        continue
                if rel is None:
                    return None
                other = layer / rel
                if other != toc and other.is_file():
                    if self.layers.index(layer) > self.layers.index(candidate):
                        return other
            except ValueError:
                continue
        # Battlefield 4 expansions keep their base copy in their own pack.
        for layer in self.layers:
            for other in layer.glob(f"Win32/**/{toc.name}"):
                if other != toc and other.with_suffix(".sb").is_file():
                    return other
        return None

    def open_level(self, name: str) -> LegacyLevel:
        tocs = self.level_tocs().get(name.lower())
        if not tocs:
            raise UnsupportedFrostbite(f"no level called {name!r}")
        toc = tocs[0]
        tree = read_toc(toc)
        level = LegacyLevel(str(tree.get("name") or toc.stem).rsplit("/", 1)[-1], toc)
        if not tree.get("cas", False):
            self._add_flat(level, tocs, tree)
            return level
        sb = toc.with_suffix(".sb").read_bytes()
        base_sb = None
        for bundle in tree.get("bundles", []):
            if bundle.get("base"):
                if base_sb is None:
                    base_toc = self._base_of(toc)
                    if base_toc is None:
                        raise UnsupportedFrostbite(f"{toc.name} points at a base table that is not installed")
                    base_sb = base_toc.with_suffix(".sb").read_bytes()
                source = base_sb
            else:
                source = sb
            body = read_tree(source, int(bundle["offset"]), f"{toc.name} {bundle.get('id')}")
            self._add_bundle(level, body, str(bundle.get("id", "")))
        return level

    def _add_flat(self, level: LegacyLevel, tocs: list[Path], tree: dict) -> None:
        """
        A level whose superbundle is not in cas mode: each bundle is stored
        whole in the `.sb`. A patch's bundle marked `base` is read from the
        base superbundle at the offset given; one marked `delta` from the
        base table's bundle of the same name (the patch's edits to it are
        not applied).
        """
        base_bundles = {}
        for toc in tocs[1:]:
            for bundle in read_toc(toc).get("bundles") or []:
                base_bundles.setdefault(str(bundle.get("id", "")).lower(), (toc.with_suffix(".sb"), bundle))
        for bundle in tree.get("bundles") or []:
            key = str(bundle.get("id", "")).lower()
            if bundle.get("delta") or bundle.get("base"):
                if key not in base_bundles:
                    continue
                path, source = base_bundles[key]
                offset = int(bundle["offset"]) if bundle.get("base") else int(source["offset"])
            else:
                path, offset = tocs[0].with_suffix(".sb"), int(bundle["offset"])
            level.bundles.append(key)
            for entry in read_flat_bundle(path, offset, key):
                if entry.res_type == -1:
                    level.ebx.setdefault(entry.name, entry)
                elif entry.name.startswith("chunk:"):
                    level.chunks.setdefault(bytes.fromhex(entry.name[6:]), entry)
                else:
                    level.res.setdefault(entry.name, entry)

    @staticmethod
    def _entry(item: dict, bundle: str) -> LegacyEntry:
        meta = item.get("resMeta") or b""
        return LegacyEntry(
            name=str(item.get("name", "")),
            sha1=item.get("sha1"),
            size=int(item.get("size", 0) or 0),
            original=int(item.get("originalSize", 0) or item.get("logicalSize", 0) or 0),
            patch_type=int(item.get("casPatchType", 0) or 0),
            base_sha1=item.get("baseSha1"),
            delta_sha1=item.get("deltaSha1"),
            res_type=int(item.get("resType", 0) or 0) & 0xFFFFFFFF,
            res_meta=meta if isinstance(meta, bytes) else b"",
            logical_offset=int(item.get("logicalOffset", 0) or 0),
            logical_size=int(item.get("logicalSize", 0) or 0),
            bundle=bundle,
        )

    def _add_bundle(self, level: LegacyLevel, body: dict, bundle: str) -> None:
        level.bundles.append(bundle)
        for item in body.get("ebx", []) or []:
            level.ebx.setdefault(str(item.get("name", "")).lower(), self._entry(item, bundle))
        for item in body.get("res", []) or []:
            level.res.setdefault(str(item.get("name", "")).lower(), self._entry(item, bundle))
        metas = body.get("chunkMeta", []) or []
        for i, item in enumerate(body.get("chunks", []) or []):
            entry = self._entry(item, bundle)
            meta = metas[i].get("meta") if i < len(metas) and isinstance(metas[i], dict) else None
            if isinstance(meta, dict) and "firstMip" in meta:
                entry.first_mip = int(meta["firstMip"])
            guid = item.get("id")
            if isinstance(guid, bytes):
                level.chunks.setdefault(guid, entry)

    # -- chunks of other superbundles ---------------------------------------

    def any_chunk(self, guid: bytes) -> LegacyEntry | None:
        """
        A chunk from any superbundle of the install, newest layer first: a
        level's meshes can keep their buffers in another level's or a shared
        superbundle's bundles. The index is built on the first call.
        """
        if self._all_chunks is None:
            self._all_chunks = {}
            for layer in self.layers:
                for toc in sorted(layer.glob("Win32/**/*.toc")):
                    sb = toc.with_suffix(".sb")
                    if not sb.is_file():
                        continue
                    try:
                        tree = read_toc(toc)
                        if tree.get("cas"):
                            data = sb.read_bytes()
                            for bundle in tree.get("bundles") or []:
                                if bundle.get("base"):
                                    continue
                                body = read_tree(data, int(bundle["offset"]), toc.name)
                                for item in body.get("chunks") or []:
                                    if isinstance(item.get("id"), bytes):
                                        self._all_chunks.setdefault(item["id"], self._entry(item, ""))
                        else:
                            for bundle in tree.get("bundles") or []:
                                if bundle.get("base") or bundle.get("delta"):
                                    continue
                                for entry in read_flat_bundle(sb, int(bundle["offset"])):
                                    if entry.name.startswith("chunk:"):
                                        self._all_chunks.setdefault(bytes.fromhex(entry.name[6:]), entry)
                    except (UnsupportedFrostbite, struct.error, ValueError, KeyError, OSError):
                        continue
        return self._all_chunks.get(guid)

    # -- payloads ------------------------------------------------------------

    def payload(self, entry: LegacyEntry) -> bytes:
        """An entry's bytes, decompressed (and rebuilt, if stored as a difference)."""
        if entry.span is not None:
            path, start, end = entry.span
            with open(path, "rb") as handle:
                handle.seek(start)
                return decompress_payload(handle.read(end - start))
        store = self.store
        if entry.patch_type == 2 and entry.base_sha1 and entry.delta_sha1:
            raw = apply_delta(store.raw(entry.base_sha1), store.raw(entry.delta_sha1))
        elif entry.sha1 not in store and entry.sha1 in store.patches:
            base, delta = store.patches[entry.sha1]
            raw = apply_delta(store.raw(base), store.raw(delta))
        else:
            raw = store.raw(entry.sha1)
        return decompress_payload(raw)


# ---------------------------------------------------------------------------
# Bundles stored whole in a superbundle


def chain_end(data: bytes, at: int, size: int) -> int:
    """Where a chain of blocks that decompresses to `size` bytes ends."""
    got = 0
    while got < size:
        block, _method, stored = struct.unpack_from(">IHH", data, at)
        at += 8 + (stored or block)
        got += block
    return at


def read_flat_bundle(path: Path, at: int, bundle: str = "") -> list[LegacyEntry]:
    """
    The entries of a bundle stored whole in a superbundle that is not in cas
    mode: a big-endian header (its size, a magic word, the entry counts,
    where its names are), a hash per entry, the ebx and res entries (name
    offset, original size), the res types, metadata and ids, the chunk
    entries (GUID, logical offset, logical size), and after the header every
    payload - ebx, then res, then chunks - each a chain of blocks.

    Ebx entries come back with `res_type` -1; chunks named `chunk:<guid>`.
    """
    with open(path, "rb") as handle:
        handle.seek(at)
        head_bytes = handle.read(8)
        size, _magic = struct.unpack(">II", head_bytes)
        handle.seek(at)
        sb = handle.read(size + 4)
    head = 4
    total, n_ebx, n_res, n_chunks, names, _meta, _meta_size = struct.unpack_from(">7I", sb, head + 4)
    p = head + 32 + 20 * total
    entries: list[LegacyEntry] = []

    def name(offset: int) -> str:
        start = head + names + offset
        return sb[start : sb.index(b"\x00", start)].decode("utf-8", "replace").lower()

    for i in range(n_ebx + n_res):
        offset, original = struct.unpack_from(">II", sb, p)
        entries.append(LegacyEntry(name(offset), None, original=original, res_type=-1 if i < n_ebx else 0, bundle=bundle))
        p += 8
    for entry in entries[n_ebx:]:
        entry.res_type = struct.unpack_from(">I", sb, p)[0]
        p += 4
    for entry in entries[n_ebx:]:
        entry.res_meta = sb[p : p + 16]
        p += 16
    p += 8 * n_res
    for _ in range(n_chunks):
        guid = sb[p : p + 16]
        logical_offset, logical_size = struct.unpack_from(">II", sb, p + 16)
        entries.append(LegacyEntry("chunk:" + guid.hex(), None, original=logical_size,
                                   logical_offset=logical_offset, logical_size=logical_size, bundle=bundle))
        p += 24
    # The payloads follow the header; their extent is found by walking them.
    with open(path, "rb") as handle:
        cursor = at + head + size
        for entry in entries:
            if entry.original == 0:
                entry.span = (path, cursor, cursor)
                continue
            handle.seek(cursor)
            got = 0
            start = cursor
            while got < entry.original:
                block, _method, stored = struct.unpack(">IHH", handle.read(8))
                cursor += 8 + (stored or block)
                handle.seek(cursor)
                got += block
            entry.span = (path, start, cursor)
    return entries
