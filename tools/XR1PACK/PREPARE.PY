"""Prepare the exact current XR1 installation from local, verified inputs.

This host-only tool never downloads, accepts licenses, launches a guest or
writes a card. Its output contains owned Windows files and remains private.
The supplied adapted drivers retain their separate provenance and notices.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct

HERE = Path(__file__).resolve().parent
DOS_PART = re.compile(r"[A-Z0-9_$]{1,8}(?:\.[A-Z0-9_$]{1,3})?\Z")


class Refused(ValueError):
    pass


def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def exact(data, pin, label):
    if identity(data) != {k: pin[k] for k in ("bytes", "sha256")}:
        raise Refused("Exact qualified length/hash mismatch: " + label)
    return data


def inside(path, root):
    try:
        return os.path.normcase(os.path.commonpath([str(path), str(root)])) == os.path.normcase(str(root))
    except ValueError:
        return False


def safe_relative(name):
    p = PurePosixPath(name)
    if p.is_absolute() or p.as_posix() != name or not p.parts:
        raise Refused("Unsafe manifest path: " + name)
    if any(not DOS_PART.fullmatch(part) for part in p.parts):
        raise Refused("Noncanonical DOS manifest path: " + name)
    return p


def expanded_file(data, name):
    """Bounded mode-A decoder adapted from this repository's STAGE.PY."""
    signature = b"SZDD\x88\xf0\x27\x33"
    if not data.startswith(signature):
        if len(data) > 1024 * 1024:
            raise Refused(name + ": input exceeds 1 MiB")
        return data
    if len(data) < 14 or data[8] != ord("A"):
        raise Refused(name + ": unsupported/truncated SZDD header")
    expected = struct.unpack_from("<I", data, 10)[0]
    if not 1 <= expected <= 1024 * 1024:
        raise Refused(name + ": invalid expanded size")
    ring = bytearray(b" " * 4096)
    cursor, pos = 4080, 14
    result = bytearray()
    while len(result) < expected:
        if pos >= len(data):
            raise Refused(name + ": truncated SZDD flags")
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(result) == expected:
                break
            if flags & (1 << bit):
                if pos >= len(data):
                    raise Refused(name + ": truncated SZDD literal")
                value = data[pos]
                pos += 1
                result.append(value)
                ring[cursor] = value
                cursor = (cursor + 1) & 4095
            else:
                if pos + 2 > len(data):
                    raise Refused(name + ": truncated SZDD reference")
                offset = data[pos] | ((data[pos + 1] & 0xf0) << 4)
                length = (data[pos + 1] & 0x0f) + 3
                pos += 2
                if len(result) + length > expected:
                    raise Refused(name + ": SZDD reference exceeds declared size")
                for index in range(length):
                    value = ring[(offset + index) & 4095]
                    result.append(value)
                    ring[cursor] = value
                    cursor = (cursor + 1) & 4095
    if pos != len(data):
        raise Refused(name + ": extra SZDD stream data")
    return bytes(result)


class Inputs:
    def __init__(self, roots):
        self.roots = {}
        self.index = {}
        self.used = {}
        for kind, root in roots.items():
            root = root.resolve(strict=True)
            if not root.is_dir():
                raise Refused("Input directory missing: " + kind)
            index = {}
            for p in root.iterdir():
                name = p.name.upper()
                if name in index:
                    raise Refused("Case-ambiguous input: " + kind + "/" + name)
                index[name] = p
            self.roots[kind], self.index[kind] = root, index

    def read(self, kind, name, pin):
        if not DOS_PART.fullmatch(name):
            raise Refused("Unsafe input filename: " + name)
        options = [name]
        if kind == "windows":
            options += [name[:-1] + "_", name[:-1] + "$"]
        found = []
        for option in dict.fromkeys(options):
            p = self.index[kind].get(option)
            if p is None:
                continue
            if p.is_symlink() or not p.is_file() or not inside(p.resolve(), self.roots[kind]):
                raise Refused("Linked/nonregular input: " + kind + "/" + option)
            if p.stat().st_size > 1024 * 1024:
                raise Refused("Oversized input: " + kind + "/" + option)
            data = p.read_bytes()
            if kind == "windows":
                data = expanded_file(data, option)
            if identity(data) == {k: pin[k] for k in ("bytes", "sha256")}:
                found.append((p, data))
        if not found:
            raise Refused("Missing or different qualified input: " + kind + "/" + name)
        # Multiple differently named copies are allowed only when all copies
        # resolve to the exact same pinned content. No unverified copy is used.
        p, data = found[0]
        self.used[kind + "/" + name] = {"source_name": p.name, **identity(data)}
        return data


def setup_inf(original, recipe):
    exact(original, recipe["input"], "original Windows SETUP.INF")
    out = bytearray()
    end = 0
    for op in recipe["operations"]:
        if set(op) == {"copy"}:
            start, stop = op["copy"]
            if not (isinstance(start, int) and isinstance(stop, int) and end <= start < stop <= len(original)):
                raise Refused("Invalid Setup transformation copy range")
            out.extend(original[start:stop])
            end = stop
        elif set(op) == {"insert"}:
            out.extend(op["insert"].encode("ascii"))
        else:
            raise Refused("Invalid Setup transformation operation")
    # CPSET accepts repeated DOS EOF markers followed only by CR/LF.
    # The original media contains seven markers; padding must precede all.
    eof = False
    for value in out:
        if value == 26:
            eof = True
            continue
        if eof and value not in (13, 10):
            raise Refused("Generated Setup text follows DOS EOF")
        if value == 0 or (value < 32 and value not in (9, 10, 13)):
            raise Refused("Generated Setup contains invalid text controls")
    return exact(bytes(out), recipe["output"], "locally generated SETUP.INF")


def prepare(windows, components, drivers, output, mode, manifest=None):
    manifest = manifest or json.loads((HERE / "INPUTS.JSN").read_text(encoding="utf-8"))
    if manifest["schema"] != 1 or manifest["profile"] != "XR1":
        raise Refused("Unsupported preparation manifest")
    if mode not in ("fresh", "update"):
        raise Refused("Unsupported preparation mode")
    inputs = Inputs({"windows": windows, "components": components, "drivers": drivers})
    target = output.resolve()
    if target.exists():
        raise Refused("Output must be a new directory")
    for root in inputs.roots.values():
        if inside(target, root) or inside(root, target):
            raise Refused("Input and output directories must be separate")
    recipe = manifest["setup_recipe"]
    generated = {
        "SETUP.INF": setup_inf(inputs.read("windows", "SETUP.INF", recipe["input"]), recipe)
    }
    cnf = inputs.read("windows", "WIN.CNF", manifest["win_cnf"])
    generated["CNF.PIN"] = cnf
    generated["XTTEST.COM"] = cnf + inputs.read("components", "XTLOGO.LGO", manifest["xtlogo"])
    payload = {}
    seen = set()
    for record in manifest["files"]:
        rel = safe_relative(record["path"])
        if record["path"] in seen:
            raise Refused("Duplicate output path: " + record["path"])
        seen.add(record["path"])
        if mode == "update" and rel.parts[0] == "W30":
            continue
        origin = record["origin"]
        if origin == "generated":
            data = generated[rel.name]
        elif origin in ("windows", "components", "drivers"):
            data = inputs.read(origin, rel.name, record)
        else:
            raise Refused("Unknown input origin")
        payload[record["path"]] = exact(data, record, record["path"])
    if len(payload) != manifest["output_counts"][mode]:
        raise Refused("Unexpected output file count")
    # Every input, transformation and final hash is checked before creation.
    target.mkdir(parents=True, exist_ok=False)
    try:
        croot = target / "DOS-CROOT"
        croot.mkdir()
        for name, data in payload.items():
            p = croot.joinpath(*PurePosixPath(name).parts)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("xb") as f:
                f.write(data)
        for name, data in payload.items():
            exact((croot / name).read_bytes(), identity(data), name)
        result = {
            "status": "PASS_HOST_XR1_PREPARATION",
            "mode": mode,
            "profile": "XR1",
            "files": {name: identity(data) for name, data in payload.items()},
            "input_files": inputs.used,
            "contains_owned_windows_bytes": True,
            "redistributable_output": False,
            "adapted_drivers": ["HPXY.DRV", "TNDYK3.DRV"],
            "new_native_test": False,
            "CF_access": False,
        }
        with (target / "PREPARE.JSN").open("x", encoding="utf-8", newline="") as f:
            f.write(json.dumps(result, indent=2).replace("\n", "\r\n") + "\r\n")
        return result
    except Exception as e:
        raise Refused("Preparation failed after output creation; preserve the partial directory for inspection: " + str(target)) from e


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--windows-media", required=True, type=Path, help="Merged owned Windows 3.0 source folder; exact supported bytes, expanded or SZDD")
    ap.add_argument("--components", default=HERE / "PAYLOAD", type=Path, help="Supplied flat XR1 payload directory; default is PAYLOAD beside this tool")
    ap.add_argument("--drivers", type=Path, help="Optional separate directory for the exact adapted drivers; default is the supplied payload")
    ap.add_argument("--mode", required=True, choices=("fresh", "update"))
    ap.add_argument("--out", required=True, type=Path, help="New private preparation directory")
    args = ap.parse_args()
    try:
        result = prepare(args.windows_media, args.components, args.drivers or args.components, args.out, args.mode)
        print(json.dumps({k: v for k, v in result.items() if k not in ("files", "input_files")}, indent=2))
    except (OSError, ValueError, KeyError) as e:
        ap.exit(1, "Refused: " + str(e) + "\n")


if __name__ == "__main__":
    main()
