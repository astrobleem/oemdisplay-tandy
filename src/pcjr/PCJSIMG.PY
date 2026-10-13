#!/usr/bin/env python3
"""Convert a PCjs JSON hard-disk image to a raw sector image.

Usage:
  python3 src/pcjr/PCJSIMG.PY <disk.json> <out.img>

PCjs stores a disk as cylinders -> heads -> sectors, each sector as signed
little-endian 32-bit words; a short word list repeats its last word to the
sector length. The output is a plain CHS-ordered image that mtools or an
emulator can read. This tool contains and downloads no media. Keep the
input, the output and anything extracted from them outside this repository.
"""
import json
import struct
import sys
from pathlib import Path


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(argv[1]), Path(argv[2])
    if dst.exists():
        raise SystemExit("PCJSIMG: refusing to overwrite " + str(dst))
    disk = json.loads(src.read_text())
    out = bytearray()
    heads = len(disk[0])
    spt = len(disk[0][0])
    for cyl in disk:
        if len(cyl) != heads:
            raise SystemExit("PCJSIMG: inconsistent head count")
        for head in cyl:
            sectors = sorted(head, key=lambda s: s["sector"])
            if [s["sector"] for s in sectors] != list(range(1, spt + 1)):
                raise SystemExit("PCJSIMG: unexpected sector numbering")
            for s in sectors:
                length = s.get("length", 512)
                raw = b"".join(struct.pack("<i", w) for w in s.get("data", []))
                fill = raw[-4:] if raw else b"\0\0\0\0"
                while len(raw) < length:
                    raw += fill
                out += raw[:length]
    if out[510:512] != b"\x55\xaa":
        raise SystemExit("PCJSIMG: no boot signature in sector 0")
    dst.write_bytes(out)
    print(f"PCJSIMG: {len(disk)} cylinders x {heads} heads x {spt} sectors, {len(out)} bytes")
    for i in range(4):
        e = out[446 + 16 * i:462 + 16 * i]
        if e[4]:
            lba = struct.unpack("<I", e[8:12])[0]
            print(f"  partition {i + 1}: type {e[4]:02X}h, start LBA {lba} (byte offset {lba * 512})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
