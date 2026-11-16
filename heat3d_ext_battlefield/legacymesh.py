"""
MeshSet resources of Battlefield 4 and Battlefield 1.

The same pieces as the later form `frostbitemesh` reads - a header, levels of
detail, sections with a vertex declaration, the buffers in a chunk named by
GUID - without the leading record sizes, and with each game's own offsets.
Both were read off the bytes of shipped meshes and checked on every mesh of
a level: a section's streams add up to its stride, its primitive type is a
triangle list, the sections' indices follow each other (each section's first
index is the sum of the triangles before it, times three), the vertex
offsets likewise in bytes, and the buffer sizes the level of detail declares
are exactly what its sections use.

    header      bounding box (two vec4), then the levels of detail's i64
                offsets: six slots (Battlefield 4) or seven (Battlefield 1)
    level       +0x08 section count, +0x0C i64 offset of the sections, then
                (count, i64 offset) section-index lists by draw category,
                opaque first and transparent second; then the index and
                vertex buffer sizes and the chunk GUID:
                    BF4  +0x4C, +0x50, +0x58      BF1  +0x58, +0x5C, +0x64
    section     material name (i64 offset), triangles, first index, vertex
                offset (bytes), vertex count, stride and primitive bytes, the
                sixteen (usage, format, offset, stream) elements, stream
                strides, element and stream counts:
                    BF4  192 bytes: +0x08, +0x14.., +0x24, +0x30, +0x70, +0x78
                    BF1  304 bytes: +0x10, +0x20.., +0x30, +0x4C, +0x8C, +0x9C

The index width is what the buffer size and the index count give (two or four
bytes; Battlefield 1 pads the buffer a little). The vertex formats are the later form's: positions are three halves
(format 7) or four (format 8) or floats.
"""

from __future__ import annotations

import struct

import numpy as np

from .frostbite import UnsupportedFrostbite
from .frostbitemesh import Lod, MeshSet, Section, _cstring

LAYOUTS = {
    "bf4": dict(slots=6, index_bytes=0x4C, vertex_bytes=0x50, guid=0x58, section=0xC0,
                material=0x08, counts=0x14, stride=0x24, elements=0x30, streams=0x70, sizes=0x78),
    "bf1": dict(slots=7, index_bytes=0x58, vertex_bytes=0x5C, guid=0x64, section=0x130,
                material=0x10, counts=0x20, stride=0x30, elements=0x4C, streams=0x8C, sizes=0x9C),
}

#: Index formats as `frostbitemesh.INDEX_FORMATS` names them, by width.
_INDEX_FORMAT = {2: 0x21, 4: 0x2E}


def read_meshset(res: bytes, generation: str, name: str = "mesh") -> MeshSet:
    lay = LAYOUTS[generation]
    if len(res) < 0x20 + 8 * lay["slots"]:
        raise UnsupportedFrostbite(f"{name}: too short for a MeshSet")
    box = np.frombuffer(res, "<f4", 8, 0).reshape(2, 4)[:, :3]
    offsets = [v for v in struct.unpack_from(f"<{lay['slots']}q", res, 0x20) if 0 < v < len(res)]
    if not offsets:
        raise UnsupportedFrostbite(f"{name}: no level of detail")
    lods = []
    for at in offsets:
        n_sections, sections_at = struct.unpack_from("<Iq", res, at + 0x08)
        if not 0 < n_sections < 256 or sections_at + n_sections * lay["section"] > len(res):
            raise UnsupportedFrostbite(f"{name}: a section table does not fit the res")
        index_bytes = struct.unpack_from("<I", res, at + lay["index_bytes"])[0]
        vertex_bytes = struct.unpack_from("<I", res, at + lay["vertex_bytes"])[0]
        guid = res[at + lay["guid"] : at + lay["guid"] + 16]
        drawn: set[int] = set()
        for category in (0, 1):
            listed, where = struct.unpack_from("<iq", res, at + 0x14 + 12 * category)
            if 0 < listed and 0 <= where and where + listed <= len(res):
                drawn.update(res[where : where + listed])
        sections = []
        for k in range(n_sections):
            s = sections_at + k * lay["section"]
            triangles, first, vertex_offset, vertices = struct.unpack_from("<4I", res, s + lay["counts"])
            stride, primitive = res[s + lay["stride"]], res[s + lay["stride"] + 1]
            if primitive != 3:
                raise UnsupportedFrostbite(f"{name}: primitive type {primitive} is not a triangle list")
            n_elements, n_streams = res[s + lay["sizes"]], res[s + lay["sizes"] + 1]
            elements = [tuple(res[s + lay["elements"] + 4 * i : s + lay["elements"] + 4 * i + 4])
                        for i in range(min(n_elements, 16))]
            streams = [res[s + lay["streams"] + i] for i in range(min(n_streams, 8))]
            if sum(streams) != stride:
                raise UnsupportedFrostbite(f"{name}: streams add up to {sum(streams)}, not the stride {stride}")
            (material_at,) = struct.unpack_from("<q", res, s + lay["material"])
            sections.append(Section(_cstring(res, material_at), stride, triangles, first,
                                    vertex_offset, vertices, elements, streams))
        indices = sum(3 * s.triangles for s in sections)
        # Battlefield 1 pads the index buffer (to eight bytes, and between sections).
        width = next((w for w in (2, 4) if w * indices <= index_bytes < w * indices + 16 * len(sections) + 16), 0) if indices else 2
        if width not in _INDEX_FORMAT:
            raise UnsupportedFrostbite(f"{name}: {index_bytes} index bytes for {indices} indices")
        lods.append(Lod(guid, _INDEX_FORMAT[width], index_bytes, vertex_bytes, sections, drawn))
    return MeshSet(name=name, kind="rigid", low=box[0].copy(), high=box[1].copy(), lods=lods)


def inline_buffers(mesh: MeshSet, res: bytes, meta: bytes) -> dict[int, bytes]:
    """
    The buffers of levels of detail stored in the res itself (chunk GUID all
    zero), by level index. The res metadata's first two words are where
    those bytes start and how many there are (the header and they fill the
    res exactly); each such level takes its vertex and index bytes in turn.
    """
    if len(meta) < 8:
        return {}
    start, size = struct.unpack_from("<II", meta, 0)
    if start + size != len(res):
        return {}
    out = {}
    at = start
    for i, lod in enumerate(mesh.lods):
        if lod.chunk == bytes(16):
            need = lod.vertex_bytes + lod.index_bytes
            if at + need > len(res):
                break
            out[i] = res[at : at + need]
            at += need
    return out
