#!/usr/bin/env python3
"""Assemble the IBM PCjr Windows 3.0 install folder (copy it to C:\\PCJREXP).

  python3 src/pcjr/INSTALL/JRPACK.PY --bin <dir> --out <new dir>

--bin   folder with TNDYJR.DRV, JRGUARD.COM and JRWIN.COM (for example the
        unpacked PCJR.ZIP of the experimental-displays-2026-10-12 release)
        and JRGRAB.GR2 (built by BUILDGR.PY). Each must match its pin:
        experiments/DISPLAY3/PINS.JSN and src/pcjr/INSTALL/PINS.JSN.
--out   a new folder; it must not exist.

Every file in the folder is first-party: TNDYJR.DRV, JRGUARD.COM, JRWIN.COM
and JRGRAB.GR2 (this repository), the XT Pixels EGA-aspect fonts
XTESYS/XTEFIX/XTEOEM.FON and the static logo XTSTATIC.LGO + WXTSPL01.RLE
(MIT, distributions/WINXT), OEMSETUP.INF, INSTALL.TXT, the font and logo
licences, and SHA256.SUM. No Microsoft file is needed or written.
Exit 0 on success, 1 on any refusal.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WINXT = ROOT / "distributions" / "WINXT"
RELEASE_PINS = ROOT / "experiments" / "DISPLAY3" / "PINS.JSN"

# First-party payloads taken from distributions/WINXT, by SHA-256.
FIRST_PARTY = {
    "XTESYS.FON": "50af47922fb4df487ecfbfb77a744dbdc315f521365b8fd089a71b6c5c6c6946",
    "XTEFIX.FON": "3c7ac7c82a987d75445f6e3c9e2a9afa650689a20cab573b8f661a37287b142c",
    "XTEOEM.FON": "8fc600059c0246a1b43c1af47bef17a34df844b3ae21369ce53b9ecc8ccc3055",
    "XTSTATIC.LGO": "995d71e3626de64c8fe21bc1f037e0dece0853d4f0d09082bf607b2d237b37ef",
    "WXTSPL01.RLE": "eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c",
    "FONTLIC.TXT": None,
    "LOGOLIC.TXT": None,
}
SELECTOR_MAX = 47          # Windows 3.0 OEM sample: longest Setup description


class Refused(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pins():
    p = json.loads(RELEASE_PINS.read_text())["drivers"]["PCJR"]
    out = {p["file"]: p["sha256"], p["guard"]["file"]: p["guard"]["sha256"],
           p["launcher"]["file"]: p["launcher"]["sha256"]}
    out["JRGRAB.GR2"] = json.loads((HERE / "PINS.JSN").read_text())["JRGRAB.GR2"]["sha256"]
    return out


def check_inf(text, present):
    """CRLF ASCII, one TNDYJR selector that fits Setup, the absolute
    C:\\PCJREXP disk path, and every a: file present in the folder."""
    raw = text.encode("ascii")
    if b"\n" in raw.replace(b"\r\n", b""):
        raise Refused("OEMSETUP.INF must use CRLF only")
    rows = [l for l in text.split("\r\n") if l.startswith("TNDYJR")]
    if len(rows) != 1:
        raise Refused("OEMSETUP.INF must have exactly one TNDYJR row")
    fields = [f.strip() for f in rows[0].split("=", 1)[1].split(",")]
    desc = fields[1].strip('"')
    if not desc.startswith("EXPERIMENTAL") or "PCjr" not in desc or len(desc) > SELECTOR_MAX:
        raise Refused("selector must start EXPERIMENTAL, name the PCjr and fit 47 characters")
    if len(fields) != 11 or fields[0].upper() != "A:TNDYJR.DRV" or fields[2] != '"133' or \
            fields[5].upper() != "A:JRGRAB.GR2":
        raise Refused("unexpected [display] row layout")
    if not re.search(r"(?m)^a = C:\\PCJREXP, ", text):
        raise Refused("[disks] must name the absolute C:\\PCJREXP path")
    named = set(n.upper() for n in re.findall(r"\ba:([A-Z0-9_]+\.[A-Z0-9]+)", text, re.I))
    missing = named - set(present)
    if missing:
        raise Refused("OEMSETUP.INF names files not in the folder: " + ", ".join(sorted(missing)))
    return desc


def build(bin_dir, out):
    if out.exists():
        raise Refused(f"{out} exists; use a new folder")
    files = {}
    for name, want in pins().items():
        p = bin_dir / name
        if not p.is_file() or sha(p.read_bytes()) != want:
            raise Refused(f"{name}: missing or not the pinned build ({want[:8]}...)")
        files[name] = p.read_bytes()
    for name, want in FIRST_PARTY.items():
        data = (WINXT / name).read_bytes()
        if want and sha(data) != want:
            raise Refused(f"{name}: distributions/WINXT copy changed")
        files[name] = data
    files["OEMSETUP.INF"] = (HERE / "OEMSETUP.INF").read_bytes()
    files["INSTALL.TXT"] = (HERE / "INSTALL.TXT").read_bytes()
    desc = check_inf(files["OEMSETUP.INF"].decode("ascii"), files)
    out.mkdir(parents=True)
    for name, data in files.items():
        (out / name).write_bytes(data)
    (out / "SHA256.SUM").write_bytes("".join(f"{sha(files[n])}  {n}\r\n" for n in sorted(files)).encode())
    return desc, sorted(files)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bin", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        desc, names = build(a.bin, a.out)
    except Refused as e:
        print("JRPACK: " + str(e), file=sys.stderr)
        return 1
    print(f"JRPACK: {a.out} ready ({len(names)} files + SHA256.SUM), selector: {desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
