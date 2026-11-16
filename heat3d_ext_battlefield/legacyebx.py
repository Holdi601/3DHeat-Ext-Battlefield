"""
Partitions (EBX) of the older Frostbite games, Battlefield 4 and Battlefield 1.

Unlike the current form `frostbiteebx` reads, these partitions describe
themselves: each carries the names of its types and fields and the layout of
every type it uses, so a partition reads into named objects without any
outside type library.

Layout
------
A 40-byte header (little-endian; magic 0x0FB2D1CE), the partition's GUID,
then, each section following the last::

    imports         (partition GUID, instance GUID) per external reference
    keywords        NUL-terminated names; fields and types refer to them by
                    a 32-bit hash of the name (h = h * 33 ^ byte, from 5381)
    fields          16 bytes: name hash, type, reference, offset, second offset
    types           16 bytes: name hash, first field, field count, alignment,
                    kind, size, second size
    instance runs   (type, count) pairs: the instances, in payload order
    array runs      12 bytes: offset, count, type   (16-aligned)
    strings         at the header's string offset
    payload         after the strings; the arrays start at the header's
                    array offset into it

The header's string offset and the length after it add up to the size of the
file, and every section's length follows from the counts before it; reading
a partition checks both, so a misread header is caught rather than skipped.

The kind of a field is bits 4-8 of its type word:

    2 a nested value of type `reference`   3 a pointer         4 an array
    7 a string   8 an enumeration (32 bits)  9 a file reference (a string)
    10 bool  11 int8  12 uint8  13 int16  14 uint16  15 int32  16 uint32
    17 int64  18 uint64  19 float  20 double  21 GUID  22 SHA-1
    23 a resource id (64 bits)

A pointer is 32 bits: 0 is none, a set top bit indexes the imports, anything
else is one more than the index of an instance in this partition. The first
`exported` instance runs have each instance preceded by its 16-byte GUID.
Each instance starts at its type's alignment, after its GUID if it has one.
Field offsets count from an eight-byte object header, which a type aligned
to four bytes does not store and any other keeps as padding. An array field holds the index of an
array run; the run's count is also written just before its data.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

import numpy as np

from .frostbite import UnsupportedFrostbite

MAGIC = 0x0FB2D1CE

#: The object header every instance's field offsets count from.
HEADER = 8

K_COMPLEX, K_POINTER, K_ARRAY, K_STRING, K_ENUM, K_FILEREF = 2, 3, 4, 7, 8, 9

#: struct codes for the plain kinds.
_PLAIN = {
    10: "?", 11: "b", 12: "B", 13: "h", 14: "H", 15: "i", 16: "I",
    17: "q", 18: "Q", 19: "f", 20: "d",
}
_SIZES = {K_POINTER: 4, K_ARRAY: 4, K_STRING: 4, K_ENUM: 4, K_FILEREF: 4, 21: 16, 22: 20, 23: 8}
_SIZES.update({k: struct.calcsize("<" + c) for k, c in _PLAIN.items()})


def name_hash(name: bytes) -> int:
    value = 5381
    for byte in name:
        value = ((value * 33) ^ byte) & 0xFFFFFFFF
    return value


@dataclass(frozen=True)
class Import:
    partition: bytes
    instance: bytes


@dataclass
class Instance:
    type: str
    guid: bytes | None
    fields: dict = field(default_factory=dict)
    index: int = 0

    def __getitem__(self, key):
        return self.fields[key]

    def get(self, key, default=None):
        return self.fields.get(key, default)


@dataclass(frozen=True)
class Ref:
    """A pointer to an instance of the same partition, by index."""

    index: int


@dataclass
class Partition:
    guid: bytes
    imports: list[Import]
    instances: list[Instance]

    def of_type(self, *names: str) -> list[Instance]:
        return [i for i in self.instances if i.type in names]

    def resolve(self, value):
        """An internal pointer's instance; anything else as it is."""
        if isinstance(value, Ref):
            return self.instances[value.index]
        return value

    @property
    def primary(self) -> Instance | None:
        return self.instances[0] if self.instances else None


class _Reader:
    def __init__(self, data: bytes, name: str):
        self.d = data
        self.name = name
        if len(data) < 0x40:
            raise UnsupportedFrostbite(f"{name} is too short to be a partition")
        (magic, self.abs_str, length, n_imp, n_inst, self.n_exp, _unk, n_types, n_fields,
         len_names, len_str, n_arr, arr_start) = struct.unpack_from("<IIIIHHHHHHIII", data, 0)
        if magic != MAGIC:
            raise UnsupportedFrostbite(f"{name} has magic 0x{magic:08X}, not an older Frostbite partition")
        if self.abs_str + length != len(data):
            raise UnsupportedFrostbite(f"{name}: the header's lengths do not add up to the file")
        self.guid = data[0x28:0x38]
        at = 0x40
        self.imports = [Import(data[at + i * 32 : at + i * 32 + 16], data[at + i * 32 + 16 : at + i * 32 + 32])
                        for i in range(n_imp)]
        at += n_imp * 32
        names = {name_hash(n): n.decode("latin-1") for n in data[at : at + len_names].split(b"\0") if n}
        at += len_names
        self.fields = []
        for i in range(n_fields):
            h, t, ref, off, _off2 = struct.unpack_from("<IHHII", data, at + i * 16)
            self.fields.append((names.get(h, f"0x{h:08X}"), (t >> 4) & 0x1F, ref, off))
        at += n_fields * 16
        self.types = []
        for i in range(n_types):
            h, first, count, align, t, size, _size2 = struct.unpack_from("<IIBBHHH", data, at + i * 16)
            self.types.append((names.get(h, f"0x{h:08X}"), first, count, max(align, 1), (t >> 4) & 0x1F, size))
        at += n_types * 16
        self.runs = [struct.unpack_from("<HH", data, at + i * 4) for i in range(n_inst)]
        at += n_inst * 4
        at = (at + 15) & ~15
        self.arrays = [struct.unpack_from("<III", data, at + i * 12) for i in range(n_arr)]
        at += n_arr * 12
        at = (at + 15) & ~15
        if at != self.abs_str:
            raise UnsupportedFrostbite(f"{name}: the sections end at {at}, the strings start at {self.abs_str}")
        self.payload = self.abs_str + len_str
        self.array_base = self.payload + arr_start
        self._float_type: dict[int, bool] = {}
        self.count = sum(repeat for _type, repeat in self.runs)

    # -- values --------------------------------------------------------------

    def string(self, offset: int) -> str | None:
        if offset == 0xFFFFFFFF:
            return None
        end = self.d.find(b"\0", self.abs_str + offset, self.payload)
        if end < 0:
            raise UnsupportedFrostbite(f"{self.name}: string offset {offset} is outside the strings")
        at = self.abs_str + offset
        return self.d[at:end].decode("utf-8", "replace")

    def pointer(self, value: int):
        if value == 0:
            return None
        if value & 0x80000000:
            if value & 0x7FFFFFFF >= len(self.imports):
                raise UnsupportedFrostbite(f"{self.name}: import {value & 0x7FFFFFFF} of {len(self.imports)}")
            return self.imports[value & 0x7FFFFFFF]
        if value - 1 >= self.count:
            raise UnsupportedFrostbite(f"{self.name}: pointer to instance {value - 1} of {self.count}")
        return Ref(value - 1)

    def field_size(self, kind: int, ref: int) -> int:
        if kind == K_COMPLEX:
            return self.types[ref][5]
        return _SIZES.get(kind, 4)

    def all_float(self, type_index: int) -> bool:
        """Whether a nested type is floats all the way down (a vector, a transform)."""
        known = self._float_type.get(type_index)
        if known is not None:
            return known
        _name, first, count, _align, _kind, size = self.types[type_index]
        ok = count > 0 and size % 4 == 0
        for name, kind, ref, _off in self.fields[first : first + count]:
            if kind == K_COMPLEX:
                ok = ok and self.all_float(ref)
            elif kind != 19:
                ok = False
        self._float_type[type_index] = ok
        return ok

    def value(self, kind: int, ref: int, at: int):
        d = self.d
        code = _PLAIN.get(kind)
        if code:
            return struct.unpack_from("<" + code, d, at)[0]
        if kind == K_COMPLEX:
            if self.all_float(ref):
                return np.frombuffer(d, "<f4", self.types[ref][5] // 4, at).copy()
            return self.complex(ref, at)
        (word,) = struct.unpack_from("<I", d, at)
        if kind == K_POINTER:
            return self.pointer(word)
        if kind in (K_STRING, K_FILEREF):
            return self.string(word)
        if kind == K_ENUM:
            return word
        if kind == K_ARRAY:
            return self.array(word, ref)
        if kind == 21:
            return d[at : at + 16]
        if kind == 22:
            return d[at : at + 20]
        if kind == 23:
            return struct.unpack_from("<Q", d, at)[0]
        return word

    def complex(self, type_index: int, at: int) -> dict:
        _name, first, count, _align, _kind, _size = self.types[type_index]
        out = {}
        for name, kind, ref, off in self.fields[first : first + count]:
            if kind == 0:
                # The base type's fields sit at the same offsets: read in place.
                if ref < len(self.types) and self.types[ref][4] in (K_COMPLEX, K_POINTER) and name == "$":
                    out.update(self.complex(ref, at))
                continue
            out[name] = self.value(kind, ref, at + off)
        return out

    def array(self, index: int, type_index: int):
        if index >= len(self.arrays):
            return []
        offset, count, _elem = self.arrays[index]
        at = self.array_base + offset
        _name, first, n, _align, _kind, _size = self.types[type_index]
        if not n:
            return []
        _fname, kind, ref, _off = self.fields[first]
        size = self.field_size(kind, ref)
        if kind == K_COMPLEX and self.all_float(ref):
            return np.frombuffer(self.d, "<f4", count * size // 4, at).reshape(count, size // 4).copy()
        code = _PLAIN.get(kind)
        if code and kind != 10:
            return np.frombuffer(self.d, "<" + code, count, at).copy()
        return [self.value(kind, ref, at + i * size) for i in range(count)]

    def instances(self) -> list[Instance]:
        out = []
        end = self.payload
        index = 0
        for run, (type_index, repeat) in enumerate(self.runs):
            name, _first, _count, align, _kind, size = self.types[type_index]
            for _ in range(repeat):
                end = (end + align - 1) // align * align
                guid = None
                if run < self.n_exp:
                    guid = self.d[end : end + 16]
                    end += 16
                # Field offsets count an eight-byte object header. A type
                # aligned to four bytes does not store it; any other stores
                # it (as padding) before its fields.
                base = end - HEADER if align == 4 else end
                out.append(Instance(name, guid, self.complex(type_index, base), index))
                end = base + size
                index += 1
        return out


def read_partition(data: bytes, name: str = "partition") -> Partition:
    reader = _Reader(data, name)
    return Partition(reader.guid, reader.imports, reader.instances())


def partition_guid(data: bytes) -> bytes:
    return data[0x28:0x38]
