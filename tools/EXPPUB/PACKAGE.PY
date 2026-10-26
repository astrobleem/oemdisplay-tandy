#!/usr/bin/env python3
"""Build/verify the separately published TEXT80 and PCjr experimental packets.

Build:  python3 tools/EXPPUB/PACKAGE.PY --builds /scratch/builds --out NEW
Verify: python3 tools/EXPPUB/PACKAGE.PY --verify NEW
Inputs are explicitly named and SHA-256 pinned in PINS.JSN. No downloads,
emulator launch, Windows media, original DDK or toolchain files are packaged.
"""
import argparse
import hashlib
import importlib.machinery
import io
import json
from pathlib import Path
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STAMP = (2026, 10, 18, 0, 0, 0)
ARCHIVES = {"TEXT80": "TEXT80.ZIP", "PCJR": "PCJRSET.ZIP"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dos(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


def js(value):
    return dos(json.dumps(value, indent=2, sort_keys=True) + "\n")


def specs():
    return json.loads((HERE / "PINS.JSN").read_text())


def extras(kind):
    guide = HERE / "T80INST.TXT" if kind == "TEXT80" else ROOT / "src/pcjr/INSTALL/INSTALL.TXT"
    return {"INSTALL.TXT": guide.read_bytes(),
            "NOTICE.TXT": (HERE / "NOTICE.TXT").read_bytes(),
            "LICENSE.TXT": (ROOT / "experiments/DISPLAY3/LICENSE.TXT").read_bytes(),
            "BUILD.JSN": (HERE / "QUALIFY.JSN").read_bytes()}


def manifest(files):
    return dos("".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items())))


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, STAMP)
            info.create_system = 0
            info.external_attr = 0x20
            z.writestr(info, data)
    return stream.getvalue()


def build(builds, out):
    if out.exists():
        raise ValueError("--out must be new")
    pins = specs()
    # Reuse the merged clean-install builder, including its original pins.
    loader = importlib.machinery.SourceFileLoader("jrpack_public", str(ROOT / "src/pcjr/INSTALL/JRPACK.PY"))
    jrpack = loader.load_module()
    with tempfile.TemporaryDirectory() as t:
        stage = Path(t)
        bin_dir = stage / "BIN"
        bin_dir.mkdir()
        for name, rel in pins["PCJR"]["inputs"].items():
            (bin_dir / name).write_bytes((builds / rel).read_bytes())
        jrpack.build(bin_dir, stage / "PCJREXP")
        packets = {}
        for kind, spec in pins.items():
            files = {}
            for name, expected in spec["payload"].items():
                if kind == "PCJR":
                    data = (stage / "PCJREXP" / name).read_bytes()
                elif name in spec["inputs"]:
                    data = (builds / spec["inputs"][name]).read_bytes()
                else:
                    data = (ROOT / spec["source_files"][name]).read_bytes()
                if sha(data) != expected:
                    raise ValueError(f"{kind}/{name}: payload pin mismatch")
                files[name] = data
            files.update(extras(kind))
            files["SHA256.SUM"] = manifest(files)
            folder = "TEXT80" if kind == "TEXT80" else "PCJREXP"
            packets[kind] = archive({folder + "/" + n: d for n, d in files.items()})
        out.mkdir(parents=True)
        for kind, data in packets.items():
            target = out / kind
            target.mkdir()
            (target / ARCHIVES[kind]).write_bytes(data)
            (target / "SHA256.SUM").write_bytes(manifest({ARCHIVES[kind]: data}))
    verify(out)


def verify(out):
    result = {}
    for kind, spec in specs().items():
        name = ARCHIVES[kind]
        data = (out / kind / name).read_bytes()
        if (out / kind / "SHA256.SUM").read_bytes() != manifest({name: data}):
            raise ValueError(kind + ": archive checksum mismatch")
        prefix = "TEXT80/" if kind == "TEXT80" else "PCJREXP/"
        wanted = set(spec["payload"]) | set(extras(kind)) | {"SHA256.SUM"}
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if len(z.namelist()) != len(wanted) or set(z.namelist()) != {prefix + n for n in wanted}:
                raise ValueError(kind + ": unexpected archive members")
            files = {n[len(prefix):]: z.read(n) for n in z.namelist()}
            for info in z.infolist():
                if info.date_time != STAMP or info.compress_type != zipfile.ZIP_STORED or info.create_system != 0 or \
                        info.external_attr != 0x20 or info.extra or info.comment or info.flag_bits:
                    raise ValueError(kind + ": noncanonical ZIP metadata")
            if z.testzip() is not None:
                raise ValueError(kind + ": ZIP CRC error")
        for n, expected in spec["payload"].items():
            if sha(files[n]) != expected:
                raise ValueError(kind + "/" + n + ": payload pin mismatch")
        for n, expected in extras(kind).items():
            if files[n] != expected:
                raise ValueError(kind + "/" + n + ": guide/evidence mismatch")
        sums = files.pop("SHA256.SUM")
        if sums != manifest(files):
            raise ValueError(kind + ": internal manifest mismatch")
        if "EXPERIMENTAL" not in files["INSTALL.TXT"].decode("ascii"):
            raise ValueError(kind + ": missing experimental label")
        result[kind] = {"file": name, "bytes": len(data), "sha256": sha(data), "members": len(wanted)}
    print(json.dumps(result, indent=2))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--builds", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--verify", type=Path)
    a = ap.parse_args()
    if a.verify:
        verify(a.verify)
    elif a.builds and a.out:
        build(a.builds, a.out)
    else:
        ap.error("use --builds and --out, or --verify")


if __name__ == "__main__":
    main()
