from pathlib import Path
import argparse
import hashlib
import json
import sys
import zipfile
from io import BytesIO

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OUTDIR = REPO / "downloads" / "experimental" / "WINWHL"
ARCHIVE = OUTDIR / "WHEELR1.ZIP"
SUMFILE = OUTDIR / "SHA256.TXT"
MANIFEST = "MANIFEST.SHA256"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def build_bytes():
    pins_raw = (ROOT / "PINS.JSN").read_bytes()
    pins = json.loads(pins_raw.decode("utf-8"))
    if not isinstance(pins, dict) or not pins:
        raise ValueError("PINS.JSN must contain a non-empty path-to-SHA256 map")
    payload = {}
    for rel, expected in sorted(pins.items()):
        path = ROOT / Path(rel)
        data = path.read_bytes()
        actual = sha256(data)
        if actual.lower() != expected.lower():
            raise ValueError(f"pin mismatch: {rel}: {actual} != {expected}")
        payload[rel.replace("\\", "/")] = data
    payload["PINS.JSN"] = pins_raw
    lines = [f"{sha256(data)}  {name}" for name, data in sorted(payload.items())]
    payload[MANIFEST] = ("\r\n".join(lines) + "\r\n").encode("ascii")

    out = BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(f"WHEELBR1/{name}", (2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            info.external_attr = 0o100644 << 16
            info.flag_bits = 0
            zf.writestr(info, data)
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--out", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    data = build_bytes()
    digest = sha256(data)
    if args.verify:
        if not args.out.is_file() or args.out.read_bytes() != data:
            raise SystemExit("WHEELR1.ZIP does not reproduce from pinned inputs")
        expected = f"{digest}  WHEELR1.ZIP\r\n".encode("ascii")
        if not SUMFILE.is_file() or SUMFILE.read_bytes() != expected:
            raise SystemExit("SHA256.TXT does not match reproduced archive")
        print(f"PACKAGE_PASS sha256={digest}")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    SUMFILE.write_bytes(f"{digest}  WHEELR1.ZIP\r\n".encode("ascii"))
    print(f"PACKAGE_BUILT sha256={digest} bytes={len(data)}")


if __name__ == "__main__":
    main()
