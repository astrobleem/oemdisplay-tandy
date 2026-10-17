#!/usr/bin/env python3
"""Convert PCjs diskette JSON to raw images, verified against PCjs's own hash.

  python3 src/pcjr/INSTALL/PCJSFLP.PY <disk.json>... --out <new dir>

PCjs diskette JSON (pcjs-diskettes, format "CHS") stores cylinders -> heads ->
sectors {c, h, s, l, d}: d is the sector as signed little-endian 32-bit
words, and a short list repeats its last word to the sector length l. The
JSON's imageInfo.hash is the MD5 of the original raw image, so every
converted image is checked against it; any mismatch is refused and nothing
is written for that run. Each image <name>.IMG is written with SHA-256 and
MD5 in <out>/MEDIA.JSN. This tool contains and downloads no media; keep the
inputs and outputs outside this repository.
Exit 0 when every image matches, 1 otherwise.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


class Refused(Exception):
    pass


def convert(disk):
    info = disk.get("imageInfo", {})
    if info.get("type") != "CHS":
        raise Refused("not a PCjs CHS diskette image")
    out = bytearray()
    for cyl in disk["diskData"]:
        for head in cyl:
            for s in sorted(head, key=lambda s: s["s"]):
                length = s.get("l", 512)
                raw = b"".join(struct.pack("<i", w) for w in s.get("d", []))
                fill = raw[-4:] if raw else b"\0\0\0\0"
                while len(raw) < length:
                    raw += fill
                out += raw[:length]
    if info.get("diskSize") and len(out) != info["diskSize"]:
        raise Refused(f"{len(out)} bytes, imageInfo.diskSize says {info['diskSize']}")
    md5 = hashlib.md5(out).hexdigest()
    if md5 != info.get("hash"):
        raise Refused(f"MD5 {md5} does not match imageInfo.hash {info.get('hash')}")
    return bytes(out)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists():
        print(f"PCJSFLP: {a.out} exists; use a new folder", file=sys.stderr)
        return 1
    images, record = {}, {}
    try:
        for p in a.json:
            data = p.read_bytes()
            img = convert(json.loads(data))
            name = p.stem.upper() + ".IMG"
            images[name] = img
            record[name] = {"source": p.name, "source_sha256": hashlib.sha256(data).hexdigest(),
                            "bytes": len(img), "md5": hashlib.md5(img).hexdigest(),
                            "sha256": hashlib.sha256(img).hexdigest()}
    except (Refused, KeyError, ValueError) as e:
        print(f"PCJSFLP: {p.name}: {e}", file=sys.stderr)
        return 1
    a.out.mkdir(parents=True)
    for name, img in images.items():
        (a.out / name).write_bytes(img)
    (a.out / "MEDIA.JSN").write_text(json.dumps(record, indent=1) + "\n")
    for name, r in record.items():
        print(f"PCJSFLP: {name} {r['sha256']} (MD5 matches PCjs)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
