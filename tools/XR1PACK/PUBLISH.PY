"""Deterministic local publisher for the explicitly scoped XR1/Minesweeper release.

This tool validates only local, hash-pinned files. It never uses the network,
GitHub Actions, an emulator, Windows media discovery, or publication services.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ASSETS = (
    "WINXT-XR1.ZIP", "WINMINE30.ZIP", "START-HERE.TXT", "QUALIFY.JSON",
    "RELEASE.JSON", "SHA256SUMS",
)
BUNDLES = ("WINXT-XR1.ZIP", "WINMINE30.ZIP")
DOCS = ("PREPARE.PY", "INPUTS.JSN", "README.TXT", "NOTICE.TXT", "QUALIFY.JSN",
        "WHEELLIC.TXT", "WHEELPRO.TXT", "OWATCOM.TXT", "PROVENANCE.JSN")
PAYLOAD_COUNT = 47
MINE_COUNT = 6
MINE_PINS = {
    "WINMINE.EXE": "52be8bb486d3bad7809c19efc8a3202ef08a458e250634e392fbd127d4046c8a",
    "WMABT.DLL": "caf0967644eca52d8c69b5bf83696e78ada52995d9a16dfd10b1a86412e0d893",
}
COMMIT_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
PATH_PART_RE = re.compile(r"[A-Za-z0-9_$.-]+\Z")
MAX_SOURCE = 16 * 1024 * 1024


class Refused(ValueError):
    pass


def require(test, message):
    if not test:
        raise Refused(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(data):
    return {"bytes": len(data), "sha256": digest(data)}


def safe_path(name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name,
            "Unsafe path: " + repr(name))
    p = PurePosixPath(name)
    require(not p.is_absolute() and p.as_posix() == name and
            all(part not in ("", ".", "..") and not part.startswith(".") and
                PATH_PART_RE.fullmatch(part) for part in p.parts),
            "Unsafe or noncanonical path: " + name)
    return p


def read_file(root, name):
    rel = safe_path(name)
    root = root.resolve(strict=True)
    path = root.joinpath(*rel.parts)
    require(path.exists() and path.is_file() and not path.is_symlink(),
            "Missing, linked, or nonregular file: " + name)
    try:
        require(os.path.commonpath((str(path.resolve(strict=True)), str(root))) == str(root),
                "Source escaped its root: " + name)
    except ValueError:
        raise Refused("Source escaped its root: " + name)
    require(path.stat().st_size <= MAX_SOURCE, "Oversized source: " + name)
    return path.read_bytes()


def parse_json(data, label):
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Refused("Invalid UTF-8 JSON in " + label) from exc
    require(isinstance(value, dict), "Expected JSON object in " + label)
    return value


def pin_value(value, label):
    if isinstance(value, str):
        require(SHA_RE.fullmatch(value) is not None, "Invalid SHA-256 pin: " + label)
        return value
    require(isinstance(value, dict) and set(value) >= {"sha256"}, "Missing SHA-256 pin: " + label)
    require(SHA_RE.fullmatch(value["sha256"]) is not None, "Invalid SHA-256 pin: " + label)
    return value["sha256"]


def zip_bytes(entries):
    """Create a ZIP with stable ordering, timestamp, attributes, and method."""
    require(entries and len({name.casefold() for name in entries}) == len(entries),
            "Empty or case-ambiguous archive")
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as zf:
        for name in sorted(entries):
            safe_path(name)
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0x20
            info.compress_type = zipfile.ZIP_STORED
            info.flag_bits = 0
            zf.writestr(info, entries[name])
    return buffer.getvalue()


def check_zip(data, expected, label):
    import io
    try:
        zf = zipfile.ZipFile(io.BytesIO(data), "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise Refused("Invalid ZIP: " + label) from exc
    with zf:
        infos = zf.infolist()
        names = [item.filename for item in infos]
        require(names == sorted(expected) and len(names) == len(set(n.casefold() for n in names)),
                "ZIP inventory differs: " + label)
        require(not zf.comment and zf.testzip() is None, "ZIP integrity failure: " + label)
        for item in infos:
            safe_path(item.filename)
            require(item.date_time == (1980, 1, 1, 0, 0, 0) and item.create_system == 0 and
                    item.external_attr == 0x20 and item.compress_type == zipfile.ZIP_STORED and
                    not item.extra and not item.comment and item.flag_bits == 0,
                    "Unexpected ZIP metadata: " + label + "/" + item.filename)
            require(zf.read(item.filename) == expected[item.filename],
                    "ZIP readback differs: " + label + "/" + item.filename)


def source_inventory(root):
    names = set(DOCS)
    for dirname, expected_count in (("PAYLOAD", PAYLOAD_COUNT), ("MINE", MINE_COUNT)):
        folder = root / dirname
        require(folder.is_dir() and not folder.is_symlink(), "Missing source directory: " + dirname)
        children = list(folder.iterdir())
        require(len(children) == expected_count, "Unexpected file count in " + dirname)
        local = set()
        for child in children:
            require(child.is_file() and not child.is_symlink(),
                    "Nested, linked, or non-file source in " + dirname)
            name = dirname + "/" + child.name
            safe_path(name)
            require(child.name.casefold() not in local, "Case-colliding source in " + dirname)
            local.add(child.name.casefold())
            names.add(name)
    return names


def collect(root, commit):
    root = Path(root).resolve(strict=True)
    require(COMMIT_RE.fullmatch(commit or "") is not None, "--commit must be a full Git SHA")
    public_data = read_file(root, "PUBLIC.JSN")
    public = parse_json(public_data, "PUBLIC.JSN")
    require(set(public) == {"schema", "tag", "files", "bundles"} and public["schema"] == 1,
            "Unsupported PUBLIC.JSN schema")
    tag = public["tag"]
    require(isinstance(tag, str) and re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+-[A-Za-z0-9.-]+", tag),
            "Invalid release tag")
    declared = public["files"]
    require(isinstance(declared, dict), "PUBLIC.JSN files must be an object")
    expected_sources = source_inventory(root)
    declared_names = set(declared)
    for name in declared_names:
        safe_path(name)
    require(declared_names == expected_sources, "PUBLIC.JSN source list is not the exact closed input set")

    data_by_source = {}
    source_ids = {}
    for name in sorted(declared):
        pin = declared[name]
        require(isinstance(pin, dict) and set(pin) == {"bytes", "sha256"} and
                isinstance(pin["bytes"], int) and pin["bytes"] >= 0 and
                SHA_RE.fullmatch(pin["sha256"] or "") is not None,
                "Invalid source pin: " + name)
        data = read_file(root, name)
        require(identity(data) == pin, "Source bytes/hash differ from PUBLIC.JSN: " + name)
        data_by_source[name] = data
        source_ids[name] = identity(data)

    inputs = parse_json(data_by_source["INPUTS.JSN"], "INPUTS.JSN")
    require(inputs.get("schema") == 1 and isinstance(inputs.get("files"), list),
            "Unsupported INPUTS.JSN schema")
    banned_names, banned_ids = set(), set()
    for row in inputs["files"]:
        require(isinstance(row, dict) and row.get("origin") in
                ("windows", "generated", "components", "drivers"),
                "Malformed INPUTS.JSN provenance row")
        if row["origin"] not in ("windows", "generated"):
            continue
        path = safe_path(row["path"])
        banned_names.add(path.name.casefold())
        banned_ids.add((row.get("bytes"), row.get("sha256")))

    qdata = data_by_source["QUALIFY.JSN"]
    qualification = parse_json(qdata, "QUALIFY.JSN")
    validate_qualification(root, qualification, data_by_source)
    notice = data_by_source["NOTICE.TXT"].decode("utf-8", errors="strict").casefold()
    require("microsoft" in notice and ("adapt" in notice or "derived" in notice) and
            "hpxy" in notice and "tndyk3" in notice and
            ("no new license" in notice or "does not grant a new license" in notice or
             "no blanket" in notice or "not blanket mit" in notice or "no license grant" in notice or
             "no public redistribution license" in notice),
            "NOTICE.TXT must state the adapted Microsoft provenance and avoid a blanket license grant")

    bundles = public["bundles"]
    require(isinstance(bundles, dict) and set(bundles) == set(BUNDLES),
            "PUBLIC.JSN bundle names are not the closed release allowlist")
    bundle_entries = {}
    used_sources = {name: set() for name in BUNDLES}
    used_destinations = {name: set() for name in BUNDLES}
    for bundle in BUNDLES:
        mapping = bundles[bundle]
        require(isinstance(mapping, dict) and mapping, "Empty bundle map: " + bundle)
        entries = {}
        for archive_path, source_path in mapping.items():
            safe_path(archive_path)
            safe_path(source_path)
            require(source_path in data_by_source, "Bundle references undeclared source: " + source_path)
            fold = archive_path.casefold()
            require(fold not in used_destinations[bundle], "Case-colliding archive path: " + archive_path)
            used_destinations[bundle].add(fold)
            require(source_path not in used_sources[bundle], "Source mapped twice in bundle: " + source_path)
            used_sources[bundle].add(source_path)
            entries[archive_path] = data_by_source[source_path]
            if source_path.startswith("PAYLOAD/"):
                ident = identity(data_by_source[source_path])
                leaf = PurePosixPath(source_path).name
                archive_leaf = PurePosixPath(archive_path).name
                allow_adapted_driver = leaf in ("HPXY.DRV", "TNDYK3.DRV") and archive_leaf == leaf
                require((ident["bytes"], ident["sha256"]) not in banned_ids,
                        "Runtime payload bytes overlap original/generated Windows input: " + leaf)
                require(allow_adapted_driver or
                        (leaf.casefold() not in banned_names and archive_leaf.casefold() not in banned_names),
                        "Runtime payload name overlaps original/generated Windows input: " + leaf)
            elif source_path == "NOTICE.TXT":
                require(bundle == "WINXT-XR1.ZIP", "Notice mapped into an unexpected bundle")
        bundle_entries[bundle] = entries
    require(used_sources["WINXT-XR1.ZIP"] == set(DOCS) | {n for n in declared if n.startswith("PAYLOAD/")},
            "WINXT archive must contain all release docs and exactly the listed runtime payload")
    require(used_sources["WINMINE30.ZIP"] == {n for n in declared if n.startswith("MINE/")},
            "Minesweeper archive must contain exactly the six pinned packet files")
    mine_map = bundles["WINMINE30.ZIP"]
    for basename, allowed_hash in MINE_PINS.items():
        match = [source for archive_path, source in mine_map.items()
                 if PurePosixPath(archive_path).name.upper() == basename]
        require(len(match) == 1 and digest(data_by_source[match[0]]) == allowed_hash,
                "Minesweeper packet mismatch: " + basename)
        require(allowed_hash in json.dumps(qualification["minesweeper"], sort_keys=True).lower(),
                "QUALIFY.JSN does not pin " + basename)

    # Require the adapted drivers and their notice to be delivered together.
    payload_leaves = {PurePosixPath(name).name for name in used_sources["WINXT-XR1.ZIP"]
                      if name.startswith("PAYLOAD/")}
    require({"HPXY.DRV", "TNDYK3.DRV"} <= payload_leaves and "NOTICE.TXT" in used_sources["WINXT-XR1.ZIP"],
            "Adapted display drivers must ship with NOTICE.TXT")

    winzip = zip_bytes(bundle_entries["WINXT-XR1.ZIP"])
    minezip = zip_bytes(bundle_entries["WINMINE30.ZIP"])
    release = {
        "schema": 1,
        "tag": tag,
        "commit": commit.lower(),
        "status": "PASS_HOST_AND_NATIVE",
        "source_fingerprints": {
            "PUBLIC.JSN": identity(public_data),
            "PUBLISH.PY": identity(read_file(root, "PUBLISH.PY")),
            **source_ids,
        },
        "qualification_sha256": digest(qdata),
        "bundles": {"WINXT-XR1.ZIP": identity(winzip), "WINMINE30.ZIP": identity(minezip)},
        "physical_qualification": False,
    }
    release_bytes = json_bytes(release)
    assets = {
        "WINXT-XR1.ZIP": winzip,
        "WINMINE30.ZIP": minezip,
        "START-HERE.TXT": data_by_source["README.TXT"],
        "QUALIFY.JSON": qdata,
        "RELEASE.JSON": release_bytes,
    }
    assets["SHA256SUMS"] = sums_bytes(assets)
    check_zip(assets["WINXT-XR1.ZIP"], bundle_entries["WINXT-XR1.ZIP"], "WINXT-XR1.ZIP")
    check_zip(assets["WINMINE30.ZIP"], bundle_entries["WINMINE30.ZIP"], "WINMINE30.ZIP")
    return assets


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\r\n").encode("ascii")


def sums_bytes(assets):
    lines = [digest(data) + "  " + name for name, data in sorted(assets.items())]
    return ("\r\n".join(lines) + "\r\n").encode("ascii")


def validate_qualification(root, q, source_data):
    require(q.get("schema") == 1 and q.get("status") == "PASS_HOST_AND_NATIVE",
            "Qualification is not PASS_HOST_AND_NATIVE")
    native = q.get("native")
    require(isinstance(native, dict), "Missing native qualification records")
    for case in ("fresh", "update"):
        row = native.get(case)
        require(isinstance(row, dict) and row.get("status") == "PASS" and
                row.get("owned_process_stopped") is True and row.get("lease_released") is True and
                isinstance(row.get("run_id"), str) and bool(row["run_id"]),
                "Native " + case + " qualification or cleanup is incomplete")
    tested = q.get("tested_source_pins")
    require(isinstance(tested, dict) and set(tested) == {"PREPARE.PY", "INPUTS.JSN"},
            "Qualification must pin PREPARE.PY and INPUTS.JSN")
    for name in ("PREPARE.PY", "INPUTS.JSN"):
        actual = digest(source_data[name])
        require(pin_value(tested[name], name) == actual, "Tested source pin differs: " + name)
    runtime = q.get("runtime_pins")
    require(isinstance(runtime, dict), "Missing runtime payload pins")
    payload_sources = [name for name in source_data if name.startswith("PAYLOAD/")]
    require({PurePosixPath(name).name for name in payload_sources} == set(runtime),
            "Runtime pin list differs from the exact PAYLOAD directory")
    for name in payload_sources:
        leaf = PurePosixPath(name).name
        pin = runtime[leaf]
        ident = identity(source_data[name])
        require(pin_value(pin, leaf) == ident["sha256"], "Runtime source pin differs: " + leaf)
        if isinstance(pin, dict) and "bytes" in pin:
            require(pin["bytes"] == ident["bytes"], "Runtime length pin differs: " + leaf)
    mine = q.get("minesweeper")
    require(isinstance(mine, dict) and mine.get("status") in ("PASS", "PASS_HOST", "PASS_HOST_AND_NATIVE"),
            "Minesweeper qualification is missing or failed")
    physical_keys = ("physical_qualification", "physical_hardware_qualified", "physical_qualified")
    present = [key for key in physical_keys if key in q]
    require(len(present) == 1 and q[present[0]] is False,
            "Qualification must explicitly state physical qualification is false")


def verify_dir(directory, expected):
    directory = Path(directory)
    require(directory.is_dir() and not directory.is_symlink(), "Verification path is not a real directory")
    children = list(directory.iterdir())
    names = {p.name for p in children}
    require(names == set(ASSETS) and len(children) == len(ASSETS),
            "Output directory is not the exact six-asset set")
    for p in children:
        require(p.is_file() and not p.is_symlink(), "Output contains a directory or linked asset: " + p.name)
    for name in ASSETS:
        actual = directory.joinpath(name).read_bytes()
        require(actual == expected[name], "Verified asset differs from regenerated bytes: " + name)
    # Re-parse the public release/checksum and independently inspect ZIP metadata/readback.
    release = parse_json((directory / "RELEASE.JSON").read_bytes(), "RELEASE.JSON")
    require(release.get("status") == "PASS_HOST_AND_NATIVE", "Release status changed")
    sums = sums_bytes({name: expected[name] for name in ASSETS if name != "SHA256SUMS"})
    require((directory / "SHA256SUMS").read_bytes() == sums, "SHA256SUMS differs")
    return release


def publish(output, commit, root=HERE):
    output = Path(output).absolute()
    require(not output.exists(), "Refusing to overwrite existing output: " + str(output))
    require(output.parent.is_dir() and not output.parent.is_symlink(), "Output parent must already exist")
    assets = collect(root, commit)  # Complete validation before creating any directory.
    temp = Path(tempfile.mkdtemp(prefix="." + output.name + ".tmp-", dir=str(output.parent)))
    try:
        for name in ASSETS:
            with (temp / name).open("xb") as stream:
                stream.write(assets[name])
        verify_dir(temp, assets)
        require(not output.exists(), "Output appeared during publication")
        os.rename(str(temp), str(output))
        verify_dir(output, assets)
    except Exception:
        if temp.exists():
            shutil.rmtree(str(temp))
        raise
    return {name: identity(assets[name]) for name in ASSETS}


def verify(directory, commit, root=HERE):
    expected = collect(root, commit)
    return verify_dir(directory, expected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--out", type=Path, help="New output directory; existing paths are refused")
    action.add_argument("--verify", type=Path, help="Verify an existing six-asset release directory")
    parser.add_argument("--commit", required=True, help="Full Git commit SHA to bind in RELEASE.JSON")
    args = parser.parse_args(argv)
    try:
        if args.out:
            result = publish(args.out, args.commit)
            print(json.dumps({"status": "PASS_LOCAL_BUILD", "assets": result}, indent=2))
        else:
            release = verify(args.verify, args.commit)
            print(json.dumps({"status": "PASS_LOCAL_VERIFY", "tag": release["tag"],
                              "commit": release["commit"]}, indent=2))
    except (OSError, Refused, KeyError, TypeError) as exc:
        parser.exit(1, "Refused: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
