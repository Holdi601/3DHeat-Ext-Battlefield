"""
The Battlefield 4 / Battlefield 1 readers, on synthetic bytes built to the
layouts their docstrings describe. No game file is used.
"""

import struct
import zlib

import numpy as np
import pytest

from heat3d_ext_battlefield.frostbite import UnsupportedFrostbite, decompress_payload
from heat3d_ext_battlefield.legacy import CasStore, apply_delta, read_cat, strip_signature
from heat3d_ext_battlefield.legacyebx import HEADER, Import, Ref, name_hash, read_partition
from heat3d_ext_battlefield.legacyhavok import CompoundInstances, _quat_rows, member_transforms
from heat3d_ext_battlefield.legacymesh import read_meshset
from heat3d_ext_battlefield.frostbitemesh import decode_sections


# --- cas.cat -----------------------------------------------------------------


def test_cat_short_form(tmp_path):
    rows = [(bytes([i]) * 20, 100 * i, 10 + i, 1) for i in range(1, 4)]
    path = tmp_path / "cas.cat"
    path.write_bytes(b"Nyan" * 4 + b"".join(h + struct.pack("<III", o, s, c) for h, o, s, c in rows))
    table, patches = read_cat(path)
    assert len(table) == 3 and not patches
    assert table["offset"].tolist() == [100, 200, 300] and table["cas"].tolist() == [1, 1, 1]


def test_cat_long_form_with_edits(tmp_path):
    entries = [(b"\x07" * 19 + b"\x00", 5, 6, 0, 2)]
    edits = [(b"\x01" * 20, b"\x02" * 20, b"\x03" * 20)]
    body = b"Nyan" * 4 + struct.pack("<II", len(entries), len(edits))
    body += b"".join(h + struct.pack("<IIII", o, s, z, c) for h, o, s, z, c in entries)
    body += b"".join(a + b + c for a, b, c in edits)
    path = tmp_path / "cas.cat"
    path.write_bytes(b"\x00\xd1\xce\x01" + bytes(552) + body)
    table, patches = read_cat(path)
    assert table["size"].tolist() == [6] and table["cas"].tolist() == [2]
    assert patches == {b"\x01" * 20: (b"\x02" * 20, b"\x03" * 20)}


def test_hash_ending_in_zero_is_found(tmp_path):
    folder = tmp_path / "a"
    folder.mkdir()
    sha = b"\x09" * 19 + b"\x00"
    (folder / "cas.cat").write_bytes(b"Nyan" * 4 + sha + struct.pack("<III", 0, 3, 1))
    (folder / "cas_01.cas").write_bytes(b"abc")
    store = CasStore([folder / "cas.cat"])
    assert store.raw(sha) == b"abc"
    store.close()


def test_signature_is_stripped():
    assert strip_signature(b"\x00\xd1\xce\x03" + bytes(552) + b"tree") == b"tree"
    assert strip_signature(b"plain") == b"plain"


# --- payloads stored as a difference -------------------------------------------


def stored(data: bytes) -> bytes:
    return struct.pack(">IHH", len(data), 0x0070, len(data)) + data


def zblock(data: bytes) -> bytes:
    packed = zlib.compress(data)
    return struct.pack(">IHH", len(data), 0x0270, len(packed)) + packed


def test_delta_copy_insert_skip_and_rewrite():
    base = stored(b"AAAA") + zblock(b"BBBB") + stored(b"CCCC") + stored(b"0123456789")
    delta = struct.pack(">I", 0 << 28 | 1)  # keep AAAA
    delta += struct.pack(">I", 3 << 28 | 1) + stored(b"new!")  # insert a block
    delta += struct.pack(">I", 4 << 28 | 1)  # drop BBBB
    delta += struct.pack(">I", 0 << 28 | 1)  # keep CCCC
    # Rewrite 0123456789: at 2 drop 3 bytes and put "xy"; at 8 drop nothing, put "Z".
    delta += struct.pack(">I", 1 << 28 | 2)
    delta += struct.pack(">HH", 2, 3) + stored(b"xy") + struct.pack(">HH", 8, 0) + stored(b"Z")
    out = decompress_payload(apply_delta(base, delta))
    assert out == b"AAAA" + b"new!" + b"CCCC" + b"01xy567Z89"


def test_delta_unknown_instruction_is_refused():
    with pytest.raises(UnsupportedFrostbite):
        apply_delta(stored(b"x"), struct.pack(">I", 9 << 28))


# --- partitions ------------------------------------------------------------------


def partition_bytes() -> bytes:
    """One type with a string, a float, an int32 and a pointer; two instances, one import."""
    names = [b"Thing", b"Name", b"Value", b"Count", b"Other"]
    keywords = b"".join(n + b"\x00" for n in names)
    fields = [(b"Name", 7, 8), (b"Value", 19, 12), (b"Count", 15, 16), (b"Other", 3, 20)]
    sections = keywords
    sections += b"".join(struct.pack("<IHHII", name_hash(n), k << 4, 0, off, 0) for n, k, off in fields)
    sections += struct.pack("<IIBBHHH", name_hash(b"Thing"), 0, len(fields), 4, 3 << 4, 24, 0)
    sections += struct.pack("<HH", 0, 2)  # two instances of type 0
    imports = b"F" * 16 + b"I" * 16
    body = imports + sections
    abs_str = (0x40 + len(body) + 15) & ~15
    strings = b"hello\x00\x00\x00"
    # The run is exported: each instance's GUID, then its fields (a type
    # aligned to four does not store the eight-byte object header).
    payload = b"G" * 16 + struct.pack("<IfiI", 0, 1.5, 7, 2)
    payload += b"H" * 16 + struct.pack("<IfiI", 0xFFFFFFFF, -2.0, 3, 0x80000000)
    header = struct.pack(
        "<IIIIHHHHHHIII", 0x0FB2D1CE, abs_str, len(strings) + len(payload), 1, 1, 1, 0, 1,
        len(fields), len(keywords), len(strings), 0, len(payload),
    )
    data = header + b"P" * 16
    data += bytes(0x40 - len(data)) + body
    data += bytes(abs_str - len(data))
    return data + strings + payload


def test_partition_reads_named_fields():
    part = read_partition(partition_bytes())
    assert part.guid == b"P" * 16
    assert [i.type for i in part.instances] == ["Thing", "Thing"]
    a, b = part.instances
    assert a.guid == b"G" * 16 and b.guid == b"H" * 16
    assert a["Name"] == "hello" and a["Value"] == 1.5 and a["Count"] == 7
    assert a["Other"] == Ref(1) and part.resolve(a["Other"]) is b
    assert b["Name"] is None and b["Value"] == -2.0
    assert b["Other"] == Import(b"F" * 16, b"I" * 16)
    assert HEADER == 8


def test_partition_with_wrong_lengths_is_refused():
    data = bytearray(partition_bytes())
    struct.pack_into("<I", data, 8, 3)
    with pytest.raises(UnsupportedFrostbite):
        read_partition(bytes(data))


# --- static model group copies from collision --------------------------------------


def test_quaternion_rows_are_rotated_axes():
    half = np.sqrt(0.5)
    rows = _quat_rows(np.array([[0.0, half, 0.0, half]]))[0]  # 90 degrees about y
    assert np.allclose(rows, [[0, 0, -1], [0, 1, 0], [1, 0, 0]], atol=1e-9)


def test_copies_by_part_index():
    transforms = np.stack([np.eye(4) * 1, np.eye(4) * 2, np.eye(4) * 3])
    found = CompoundInstances(transforms, np.array([0, 3, 4]))
    members = [
        {"InstanceCount": 2, "PhysicsPartCountPerInstance": 1, "PhysicsPartRange": {"First": 0}},
        {"InstanceCount": 2, "PhysicsPartCountPerInstance": 2, "PhysicsPartRange": {"First": 2}},
    ]
    out = member_transforms(members, found)
    assert [len(o) for o in out] == [1, 2]  # the first member's second copy has no collision
    assert out[1][0][0, 0] == 2 and out[1][1][0, 0] == 3


def test_copies_in_order_skipping_members_without_parts():
    transforms = np.stack([np.eye(4) * (i + 1) for i in range(3)])
    members = [
        {"InstanceCount": 2, "PhysicsPartCountPerInstance": 1},
        {"InstanceCount": 4, "PhysicsPartCountPerInstance": 0},
        {"InstanceCount": 1, "PhysicsPartCountPerInstance": 3},
    ]
    out = member_transforms(members, [CompoundInstances(np.zeros((1, 4, 4)), None), CompoundInstances(transforms, None)])
    assert [len(o) for o in out] == [2, 0, 1] and out[2][0][0, 0] == 3


def test_unmatched_records_are_refused():
    with pytest.raises(UnsupportedFrostbite):
        member_transforms([{"InstanceCount": 5, "PhysicsPartCountPerInstance": 1}], CompoundInstances(np.zeros((2, 4, 4)), None))


# --- meshes ------------------------------------------------------------------------------


def bf4_mesh() -> tuple[bytes, bytes]:
    """A one-triangle mesh in the Battlefield 4 layout, and its buffers."""
    res = bytearray(0x200)
    struct.pack_into("<8f", res, 0, 0, 0, 0, 0, 1, 1, 0, 0)
    struct.pack_into("<q", res, 0x20, 0x70)  # the one level of detail
    lod = 0x70
    struct.pack_into("<Iq", res, lod + 0x08, 1, 0x110)
    struct.pack_into("<iq", res, lod + 0x14, 1, 0x1F0)  # opaque: section 0
    res[0x1F0] = 0
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], "<f2")
    vertex = np.zeros((3, 8), np.uint8)
    vertex[:, :6] = positions.view(np.uint8).reshape(3, 6)
    vertices = vertex.tobytes()
    indices = struct.pack("<3H", 0, 1, 2)
    struct.pack_into("<II", res, lod + 0x4C, len(indices), len(vertices))
    res[lod + 0x58 : lod + 0x68] = b"C" * 16
    s = 0x110
    struct.pack_into("<q", res, s + 0x08, 0x1E0)
    res[0x1E0:0x1E4] = b"mat\x00"
    struct.pack_into("<4I", res, s + 0x14, 1, 0, 0, 3)
    res[s + 0x24], res[s + 0x25] = 8, 3
    res[s + 0x30 : s + 0x34] = bytes([1, 7, 0, 0])  # position, three halves, offset 0
    res[s + 0x70] = 8
    res[s + 0x78], res[s + 0x79] = 1, 1
    return bytes(res), vertices + indices


def test_mesh_layout_bf4():
    res, buffers = bf4_mesh()
    mesh = read_meshset(res, "bf4")
    lod = mesh.lods[0]
    assert lod.chunk == b"C" * 16 and lod.drawn == {0} and lod.sections[0].material == "mat"
    (section,) = decode_sections(lod, buffers)
    assert section.faces.tolist() == [[0, 1, 2]]
    assert np.allclose(section.positions[1], [1, 0, 0])


def test_mesh_with_wrong_streams_is_refused():
    res, _ = bf4_mesh()
    res = bytearray(res)
    res[0x110 + 0x70] = 12
    with pytest.raises(UnsupportedFrostbite):
        read_meshset(bytes(res), "bf4")
