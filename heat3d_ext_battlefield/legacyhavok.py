"""
Where a static model group's copies stand, from its physics resource.

In Battlefield 4 and Battlefield 1 a static model group's partition lists its
members and how many copies of each there are, but for most members not where
the copies are: the transforms are in the group's collision, a resource of
type HavokPhysicsData (`..._physics_win32`) named by the group's havok asset.
That resource is a short header followed by Havok packfiles (one per pointer
size); the group's collision is the packfile's largest static compound shape,
and its instances are the copies.

A packfile
----------
A 64-byte header (two magic words, the pointer size at byte 16), then section
headers of 48 bytes (with 16 more from file version 11, which also ends the
header with predicate words, their length at byte 62): a 19-byte tag and a
byte, the section's start, and its fixup table offsets, the third of which
is the virtual fixups: (object offset, section, class name offset) triples.
They name every object's class. The local fixups that would say where an
array's data is are not filled in here, so the instance array is found the
way the writer lays it out - after its object - and is only taken when its
records read as transforms (orthonormal rotations, positive scale).

The records
-----------
- Battlefield 4 (`hkpStaticCompoundShape`, 32-bit pointers): 64 bytes; a
  translation, a rotation quaternion and a scale (vec4 each), then the shape,
  two filter words and a user word: `parts per copy << 24 | part index`. The
  part index counts the group's physics parts, which each member numbers
  from its `PhysicsPartRange.First`, `PhysicsPartCountPerInstance` a copy -
  in the levels checked the top byte equals that count on every record.
- Battlefield 1 (`hknpStaticCompoundShape`, 64-bit): 128 bytes; three
  rotation columns and a translation (vec4 each), a scale, then the shape.
  The records are the group's copies in member order: their number equals
  the group's copy count.
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass

import numpy as np

from .frostbite import UnsupportedFrostbite

MAGIC = struct.pack("<II", 0x57E0E057, 0x10C0C010)


@dataclass
class CompoundInstances:
    #: (N, 4, 4) row-vector transforms, Frostbite's layout: rows are the
    #: local x, y and z axes in world space and the translation.
    transforms: np.ndarray
    #: Physics part index of each record, or None when records are copies.
    parts: np.ndarray | None


def _objects(data: bytes, at: int) -> tuple[int, int, list[tuple[int, str]]]:
    """A packfile's pointer size, data start and (offset, class) of every object."""
    pointer = data[at + 16]
    version, sections = struct.unpack_from("<ii", data, at + 12)[0], struct.unpack_from("<i", data, at + 20)[0]
    width = 48 + (16 if version >= 11 else 0)
    head = at + 64
    if version >= 11:
        # Later headers end with predicate words; their length is at 62.
        head += struct.unpack_from("<h", data, at + 62)[0]
    rows = []
    for i in range(sections):
        tag = data[head + i * width : head + i * width + 19].split(b"\x00")[0]
        rows.append((tag, struct.unpack_from("<7i", data, head + i * width + 20)))
    names = {tag: vals for tag, vals in rows}
    if b"__data__" not in names or b"__classnames__" not in names:
        raise UnsupportedFrostbite("a packfile without data or class names")
    start, _local, _global, virtual, exports, _imports, _end = names[b"__data__"]
    classes = at + names[b"__classnames__"][0]
    out = []
    p = at + start + virtual
    stop = at + start + exports
    while p + 12 <= stop:
        offset, _section, name = struct.unpack_from("<iii", data, p)
        p += 12
        if offset < 0:
            break
        end = data.index(b"\x00", classes + name)
        out.append((offset, data[classes + name : end].decode("latin-1")))
    return pointer, at + start, out


def _first_array(data: bytes, at: int, pointer: int, limit: int = 160) -> int:
    """The element count of the first non-empty array in an object's first bytes."""
    words = struct.unpack_from(f"<{limit // 4}I", data, at)
    skip = pointer // 4
    for i in range(skip, len(words) - 1):
        n = words[i]
        if 0 < n < 1 << 24 and words[i + 1] == (n | 0x80000000) and not any(words[i - skip : i]):
            return n
    return 0


def _rotation_ok(rows: np.ndarray) -> bool:
    gram = np.einsum("nij,nkj->nik", rows, rows)
    return bool(np.allclose(gram, np.eye(3), atol=2e-2))


def _quat_rows(q: np.ndarray) -> np.ndarray:
    """Rotation matrices whose rows are the rotated x, y and z axes."""
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    m = np.empty((len(q), 3, 3), np.float64)
    # Columns of the usual matrix, written as rows.
    m[:, 0] = np.stack([1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)], 1)
    m[:, 1] = np.stack([2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)], 1)
    m[:, 2] = np.stack([2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)], 1)
    return m


def _records(data: bytes, start: int, count: int, stride: int, kind: str) -> tuple[np.ndarray, np.ndarray | None] | None:
    if start + count * stride > len(data):
        return None
    raw = np.frombuffer(data, "<f4", count * stride // 4, start).reshape(count, stride // 4).astype(np.float64)
    probe = raw[: min(count, 64)]
    if kind == "hkp":
        q = probe[:, 4:8]
        if not np.allclose(np.linalg.norm(q, axis=1), 1, atol=1e-2) or not (probe[:, 8:11] > 0).all():
            return None
        rot = _quat_rows(raw[:, 4:8]) * raw[:, 8:11, None]
        words = np.frombuffer(data, "<u4", count * stride // 4, start).reshape(count, stride // 4)
        user = words[:, 15] if stride == 64 else words[:, 16]
        out = np.zeros((count, 4, 4))
        out[:, :3, :3] = rot
        out[:, 3, :3] = raw[:, 0:3]
        out[:, 3, 3] = 1
        return out, user
    rows = probe[:, 0:12].reshape(-1, 3, 4)[:, :, :3]
    if not _rotation_ok(rows) or not (probe[:, 16:19] > 0).all():
        return None
    out = np.zeros((count, 4, 4))
    out[:, :3, :3] = raw[:, 0:12].reshape(-1, 3, 4)[:, :, :3] * raw[:, 16:19, None]
    out[:, 3, :3] = raw[:, 12:15]
    out[:, 3, 3] = 1
    return out, None


def compounds(res: bytes, name: str = "physics") -> list[CompoundInstances]:
    """Every static compound shape's instances in a HavokPhysicsData resource, largest first."""
    packs = [m.start() for m in re.finditer(re.escape(MAGIC), res)]
    if not packs:
        raise UnsupportedFrostbite(f"{name}: no Havok packfile")
    # The 32-bit packfile where there is one: the same content, smaller records.
    found = sorted((_objects(res, at) for at in packs), key=lambda o: o[0] != 4)
    for pointer, base, objects in found:
        out = []
        for offset, cls in objects:
            if not cls.endswith("StaticCompoundShape"):
                continue
            n = _first_array(res, base + offset, pointer)
            if not n:
                continue
            kind = "hknp" if cls.startswith("hknp") else "hkp"
            stride = 128 if kind == "hknp" else (64 if pointer == 4 else 80)
            for start in range(base + offset + 16, base + offset + 4096, 16):
                got = _records(res, start, n, stride, kind)
                if got is not None:
                    transforms, user = got
                    parts = (user & 0xFFFFFF).astype(np.int64) if user is not None else None
                    out.append(CompoundInstances(transforms, parts))
                    break
        if out:
            return sorted(out, key=lambda c: -len(c.transforms))
    raise UnsupportedFrostbite(f"{name}: no static compound shape with readable instances")


def group_instances(res: bytes, name: str = "physics") -> CompoundInstances:
    """The largest static compound shape's instances."""
    return compounds(res, name)[0]


def member_transforms(members: list[dict], found) -> list[np.ndarray]:
    """
    Each member's copies' transforms, (k, 4, 4), from a group's compound
    shapes (one, or the list `compounds` gives); a copy without a record (no
    collision) is left out.

    With part indices (Battlefield 4) the largest compound is the group's.
    Without them the group's is the one with a record per copy, or failing
    that a record per physics part; an object's own compound (its convex
    pieces) is smaller or does not match.
    """
    found = found if isinstance(found, list) else [found]
    copies = [int(m.get("InstanceCount", 0) or 0) for m in members]
    per = [int(m.get("PhysicsPartCountPerInstance", 0) or 0) for m in members]
    first = [int(m.get("PhysicsPartRange", {}).get("First", 0) or 0) for m in members]
    for c in found:
        if c.parts is not None:
            return _by_part(c.transforms, {int(p): i for i, p in enumerate(c.parts)}, copies, per, first)
    # A member with no physics parts has no records: the others' copies are
    # the records in order.
    solid = [n if k > 0 else 0 for n, k in zip(copies, per)]
    for counts in (copies, solid):
        for c in found:
            if len(c.transforms) == sum(counts):
                out, at = [], 0
                for n in counts:
                    out.append(c.transforms[at : at + n])
                    at += n
                return out
    total = sum(n * k for n, k in zip(copies, per))
    for c in found:
        if total and len(c.transforms) == total:
            return _by_part(c.transforms, {i: i for i in range(total)}, copies, per, first)
    raise UnsupportedFrostbite(
        f"collision records ({', '.join(str(len(c.transforms)) for c in found[:4])}) match neither "
        f"the {sum(copies)} copies nor the {total} parts"
    )


def _by_part(transforms, where, copies, per, first) -> list[np.ndarray]:
    out = []
    for n, k, f in zip(copies, per, first):
        rows = []
        if k > 0 and f != 0xFFFFFFFF:
            for j in range(n):
                for q in range(k):
                    i = where.get(f + j * k + q)
                    if i is not None:
                        rows.append(transforms[i])
                        break
        out.append(np.array(rows).reshape(-1, 4, 4))
    return out
