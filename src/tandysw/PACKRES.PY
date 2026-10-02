#!/usr/bin/env python3
"""Build Win16 resources and attach to an unresourced, linked NE driver.

No third-party modules. Resource payload encodings are checked against the
bundled Microsoft Windows 3.0 CGA/VGA display drivers by TESTRES.PY.
"""
from pathlib import Path
from collections import OrderedDict
import argparse
import os
import re
import struct

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("TANDY_REPO", str(HERE.parents[1]))).resolve()
U16 = lambda b, o: struct.unpack_from("<H", b, o)[0]
U32 = lambda b, o: struct.unpack_from("<I", b, o)[0]
align = lambda n, a: (n + a - 1) // a * a


def resource_records():
    """Yield (type, integer ID, flags, data), with stock OEMBIN aliases."""
    definitions = dict((n, int(v)) for n, v in re.findall(
        r"#define\s+((?:OCR|OIC|OBM)_\w+)\s+(\d+)",
        (ROOT / "DDK/286/INC/WINDOWS.H").read_text()))
    records = []
    image_id = 1
    for line in (HERE / "RC_LOW.RC").read_text().splitlines():
        fields = line.split()
        if len(fields) < 3 or fields[0] not in definitions:
            continue
        name, kind, path = definitions[fields[0]], fields[1], fields[-1]
        data = (HERE / path.upper()).read_bytes()
        flags = 0x1c30 if kind in ("cursor", "icon") else 0x0c30
        if "PRELOAD" in fields:
            flags |= 0x40
        if "FIXED" in fields:
            flags &= ~0x1010
        if kind == "bitmap":
            assert data[:2] == b"BM"
            records.append((2, name, flags, data[14:]))
            continue
        assert kind in ("cursor", "icon")
        zero, filetype, count = struct.unpack_from("<HHH", data)
        assert zero == 0 and filetype == (2 if kind == "cursor" else 1)
        group = bytearray(struct.pack("<HHH", 0, filetype, count))
        for i in range(count):
            w, h, colors, reserved, v1, v2, size, offset = struct.unpack_from(
                "<BBBBHHII", data, 6 + 16 * i)
            dib = data[offset:offset + size]
            assert len(dib) == size and U32(dib, 0) == 40
            planes, bits = struct.unpack_from("<HH", dib, 12)
            if kind == "cursor":
                payload = struct.pack("<HH", v1, v2) + dib
                group.extend(struct.pack("<HHHHIH", U32(dib, 4), U32(dib, 8),
                                         planes, bits, len(payload), image_id))
                typ = 1
            else:
                payload = dib
                group.extend(struct.pack("<BBBBHHIH", w, h, colors, reserved,
                                         planes, bits, size, image_id))
                typ = 3
            records.append((typ, image_id, flags, payload))
            image_id += 1
        records.append((12 if kind == "cursor" else 14, name, flags, bytes(group)))

    # RC3.0 normally maps string types to a high-numbered ordinal and emits a
    # RT_NAMETABLE. Mirror the installed VGA.DRV's exact alias arrangement.
    names = bytearray()
    for ident, text in [(1, b""), (0x8003, b"FONTS"), (2, b"")]:
        body = struct.pack("<HH", 0xf006, ident) + b"OEMBIN\0" + text + b"\0"
        names.extend(struct.pack("<H", len(body) + 2) + body)
    names.extend(b"\0\0")
    records.append((15, 1, 0x1c30, bytes(names)))
    records.extend((0x7006, ident, flags, (HERE / path).read_bytes()) for
                   ident, flags, path in [(1, 0xc70, "CONFIG.BIN"),
                                         (3, 0xc70, "FONTS.BIN"),
                                         (2, 0xc30, "COLORTAB.BIN")])
    order = {t: i for i, t in enumerate([15, 12, 14, 2, 1, 3, 0x7006])}
    return sorted(records, key=lambda r: order[r[0]])


def write_res(records):
    """Windows 16-bit .RES: byte FF+WORD type/id, WORD flags, DWORD size."""
    out = bytearray()
    for typ, name, flags, data in records:
        out.extend(b"\xff" + struct.pack("<H", typ))
        out.extend(b"\xff" + struct.pack("<H", name))
        out.extend(struct.pack("<HI", flags, len(data)) + data)
    return bytes(out)


def read_res(data):
    records = []
    pos = 0
    while pos < len(data):
        assert data[pos] == 0xff and data[pos + 3] == 0xff
        typ, name = U16(data, pos + 1), U16(data, pos + 4)
        flags, size = struct.unpack_from("<HI", data, pos + 6)
        pos += 12
        payload = data[pos:pos + size]
        assert len(payload) == size
        records.append((typ, name, flags, payload))
        pos += size
    return records


def inspect_ne(data):
    assert data[:2] == b"MZ"
    ne = U32(data, 0x3c)
    assert data[ne:ne + 2] == b"NE"
    start = ne + U16(data, ne + 0x24)
    end = ne + U16(data, ne + 0x26)
    if start == end:
        return []
    shift, pos = U16(data, start), start + 2
    records = []
    while U16(data, pos):
        typ, count, reserved = struct.unpack_from("<HHI", data, pos)
        assert typ & 0x8000, "String-type NE input unsupported"
        pos += 8
        for _ in range(count):
            off, size, flags, name, handle, usage = struct.unpack_from("<6H", data, pos)
            assert name & 0x8000, "String-name NE input unsupported"
            pos += 12
            payload = data[off << shift:(off + size) << shift]
            assert len(payload) == size << shift
            records.append((typ & 0x7fff, name & 0x7fff, flags, payload))
    assert pos + 2 <= end
    return records


def attach_ne(original, records):
    """Insert table, preserving all segment payloads and fixups byte-for-byte.

    Only fresh resource-free LINK4 output is accepted. Header insertion is a
    multiple of both segment alignment and 16, then resources append at EOF.
    Never tries to rewrite already-resourced binaries or fast-load images.
    """
    assert original[:2] == b"MZ"
    ne = U32(original, 0x3c)
    assert original[ne:ne + 2] == b"NE"
    resource_start = U16(original, ne + 0x24)
    names_start = U16(original, ne + 0x26)
    assert resource_start == names_start, "Use fresh LINK4 output without resources"
    assert U16(original, ne + 0x38) == U16(original, ne + 0x3a) == 0, "Fast-load input unsupported"
    shift = U16(original, ne + 0x32)
    assert 0 <= shift <= 15
    segment_alignment = 1 << shift
    groups = OrderedDict()
    for record in records:
        groups.setdefault(record[0], []).append(record)
    table_length = 4 + sum(8 + 12 * len(group) for group in groups.values())
    delta = align(table_length, max(16, segment_alignment))
    insertion = ne + resource_start
    out = bytearray(original[:insertion] + bytes(delta) + original[insertion:])
    for field in [0x04, 0x22, 0x26, 0x28, 0x2a]:
        value = U16(original, ne + field)
        if value >= resource_start:
            assert value + delta <= 0xffff
            struct.pack_into("<H", out, ne + field, value + delta)
    nonresident = U32(original, ne + 0x2c)
    if nonresident >= insertion:
        struct.pack_into("<I", out, ne + 0x2c, nonresident + delta)
    segtable = ne + U16(out, ne + 0x22)
    for i in range(U16(out, ne + 0x1c)):
        field = segtable + i * 8
        offset = U16(out, field)
        if offset:
            assert offset * segment_alignment >= insertion
            assert offset + delta // segment_alignment <= 0xffff
            struct.pack_into("<H", out, field, offset + delta // segment_alignment)
    table = bytearray(struct.pack("<H", 4))
    for typ, group in groups.items():
        assert typ < 0x8000
        table.extend(struct.pack("<HHI", typ | 0x8000, len(group), 0))
        for _, name, flags, payload in group:
            assert 0 < len(payload) < 0x10000 and name < 0x8000
            out.extend(bytes(align(len(out), 16) - len(out)))
            offset = len(out)
            out.extend(payload)
            out.extend(bytes(align(len(out), 16) - len(out)))
            assert offset // 16 <= 0xffff
            table.extend(struct.pack("<6H", offset // 16, align(len(payload), 16) // 16,
                                     flags, name | 0x8000, 0, 0))
    table.extend(b"\0\0")
    assert len(table) == table_length
    out[insertion:insertion + table_length] = table
    # Stock Win3.0 display-driver compatibility bits and RC3 version stamp.
    struct.pack_into("<H", out, ne + 0x0c, U16(out, ne + 0x0c) | 0x0300)
    out[ne + 0x37] |= 0x08
    struct.pack_into("<H", out, ne + 0x3e, 0x0300)
    struct.pack_into("<I", out, ne + 0x08, 0)  # no stale NE checksum
    # DOS stub remains a DOS stub: do not make DOS load the appended NE data.
    for wanted, actual in zip(records, inspect_ne(out)):
        assert wanted[:3] == actual[:3]
        assert actual[3][:len(wanted[3])] == wanted[3]
    assert len(inspect_ne(out)) == len(records)
    return bytes(out), delta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("output", nargs="?", default=str(HERE / "TANDY.RES"))
    attach = sub.add_parser("attach")
    attach.add_argument("resources")
    attach.add_argument("input")
    attach.add_argument("output")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("driver")
    args = parser.parse_args()
    if args.command == "build":
        records = resource_records()
        binary = write_res(records)
        assert read_res(binary) == records
        Path(args.output).write_bytes(binary)
        print(f"Wrote {args.output}: {len(records)} records, {len(binary)} bytes")
    elif args.command == "attach":
        records = read_res(Path(args.resources).read_bytes())
        result, delta = attach_ne(Path(args.input).read_bytes(), records)
        Path(args.output).write_bytes(result)
        print(f"Wrote {args.output}: {len(result)} bytes; header grew {delta}; {len(records)} resources")
    else:
        for typ, name, flags, data in inspect_ne(Path(args.driver).read_bytes()):
            print(f"type={typ:#06x} id={name:5} flags={flags:#06x} bytes={len(data)}")


if __name__ == "__main__":
    main()
