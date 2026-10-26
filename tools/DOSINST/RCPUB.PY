"""Deterministic expanded Windows XT installer and ordinary OEM source."""
import argparse
import importlib.machinery
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
pub = importlib.machinery.SourceFileLoader("xr1_native_helpers", str(HERE.parent / "XR1PACK/PUBLISH.PY")).load_module()
media = importlib.machinery.SourceFileLoader("xr1_native_media", str(HERE.parent / "XR1PACK/PREPARE.PY")).load_module()
ASSETS = ("WINXT.ZIP", "WINXTSRC.ZIP", "WINXT.JSN", "WINXT.SHA")

def check_inputs(recipe, header, records, qualified):
    rows = re.findall(r'{"([^"\n]+)","([^"\n]+)",(\d+)UL,(\d+)}', recipe)
    crcs = re.findall(r'0x([0-9a-f]{8})UL, /\* ([^*]+) \*/', header)
    pub.require(len(rows) == len(crcs) == 369, "Windows input CRC inventory differs")
    required = set()
    for (path, source, size, kind), (crc, comment) in zip(rows, crcs):
        pub.require(comment == path, "Windows CRC recipe ordering differs: " + path)
        name = path.replace("\\\\", "/")
        if kind != "1":
            pub.require(crc == "00000000", "Unexpected Windows input CRC: " + name)
            continue
        required.add(name)
        row = records[name]
        pub.require(row["bytes"] == int(size) and row["crc32"] == crc,
                    "Windows input CRC pin differs: " + name)
        pub.require({k: row[k] for k in ("bytes", "sha256")} ==
                    {k: qualified[name][k] for k in ("bytes", "sha256")},
                    "Windows input differs from qualified media: " + name)
    pub.require(set(records) == required, "Windows input pin closure differs")

def collect():
    spec = json.loads((HERE / "RCPUBLIC.JSN").read_bytes())
    pub.require(spec["schema"] == 1, "Unsupported native rc.8 manifest")
    entries = {}
    for name, pin in spec["files"].items():
        pub.safe_path(name)
        data = pub.read_file(REPO, pin["source"])
        pub.require(pub.identity(data) == pin.get("source_identity", pin["identity"]), "Source pin differs: " + name)
        if pin.get("encoding") == "SZDD":
            data = media.expanded_file(data, name)
        pub.require(pub.identity(data) == pin["identity"], "Expanded source differs: " + name)
        entries[name] = data
    header = (HERE / "XR1PINS.H").read_text()
    rows = re.findall(r'{"([^"\n]+)","([0-9a-f]{64})",(\d+)UL,0,0x[0-9a-f]+UL}', header)
    runtime = {"PAYLOAD/" + name: {"bytes": int(size), "sha256": sha} for name, sha, size in rows}
    pub.require(len(runtime) == 49 and set(runtime) == {n for n in entries if n.startswith("PAYLOAD/")}, "Runtime inventory differs")
    pub.require(set(entries) == set(runtime) | {"PREPXR.EXE", "README.TXT", "NOTICE.TXT", "OWATCOM.TXT", "WHEELLIC.TXT", "SOUNDID.JSN", "SOUNDSRC.ZIP", "SOUNDLIC.TXT"}, "Consumer archive inventory differs")
    for name, pin in runtime.items():
        pub.require(pub.identity(entries[name]) == pin, "Compiled runtime differs: " + name)
    pub.require(not any(n.endswith(".PY") for n in entries), "Private/host preparation file in consumer kit")
    check_inputs((HERE / "XRFILES.H").read_text(), (HERE / "XRINPUT.H").read_text(),
                 json.loads((HERE / "XRINPUT.JSN").read_bytes()),
                 {row["path"]: row for row in json.loads((HERE.parent / "XR1PACK/INPUTS.JSN").read_bytes())["files"]})
    pub.validate_sound(entries)
    native = json.loads((HERE / "RCNATIVE.JSN").read_bytes())
    pub.require(pub.identity(entries["PREPXR.EXE"]) == native["binary"], "Native helper differs")
    for name, pin in native["sources"].items():
        pub.require(pub.identity(pub.read_file(HERE, name)) == pin, "Native source differs: " + name)
    for record in native.get("companions", {}).values():
        for key in ("source", "binary"):
            pub.require(pub.identity(pub.read_file(REPO, record[key])) == record[key + "_identity"], "Companion differs: " + record[key])
        for path, pin in record.get("source_dependencies", {}).items():
            pub.require(pub.identity(pub.read_file(REPO, path)) == pin,
                        "Companion source dependency differs: " + path)
        if "build_record" in record:
            pub.require(pub.identity(pub.read_file(REPO, record["build_record"])) ==
                        record["build_record_identity"], "Companion build record differs")
    helper = entries["PREPXR.EXE"]
    pub.require(helper[:2] == b"MZ" and len(helper) >= 28, "DOS MZ helper required")
    last, pages = struct.unpack_from("<HH", helper, 2)
    pub.require(pages * 512 - (512 - last if last else 0) == len(helper), "Native EXE image length differs")
    return entries

def qualified_core(entries):
    # Retain the prior native receipt as an exact runtime/transaction baseline.
    # It is evidence, not another current consumer installation format.
    archive = pub.zip_bytes(entries)
    executable = entries["PREPXR.EXE"] + archive
    q = json.loads((REPO / "docs/QUAL/DOSINST/RC8.JSN").read_bytes())
    pub.require(q["status"] == "PASS_NATIVE_AND_HOST" and not q["physical_test"], "Native qualification incomplete")
    for mode in ("fresh", "update"):
        row = q[mode]
        pub.require(row["complete"] and not row.get("error") and row["owned_stopped"] and row["lease_released"], "Native case incomplete: " + mode)
        pub.require(row["prepared_comparison"]["count"] == (369 if mode == "fresh" else 82) and not row["prepared_comparison"]["different"], "Prepared bytes differ: " + mode)
    pub.require(q["cold"]["complete"] and not q["cold"].get("error") and q["cold"]["owned_stopped"] and q["cold"]["lease_released"], "Cold launch incomplete")
    validation = q["input_validation"]
    pub.require(validation["helper"] == pub.identity(entries["PREPXR.EXE"]), "Input checks used a different helper")
    for name in ("native_corruption", "native_valid_inputs"):
        case = validation[name]
        pub.require(case["complete"] and not case.get("error") and case["owned_stopped"] and case["lease_released"],
                    "Native input validation incomplete: " + name)
    pub.require(validation["native_valid_inputs"]["prepared_comparison"] == {"count": 369, "different": []},
                "CRC-validated fresh outputs differ")
    pub.require(q["public_assets"]["WINXT.ZIP"] == pub.identity(archive) and q["public_assets"]["WINXT.EXE"] == pub.identity(executable), "Package differs from qualified native kit")
    return entries

def expanded_entries():
    core = qualified_core(collect())
    panui = importlib.machinery.SourceFileLoader(
        "current_panui_inputs", str(HERE / "PANUI.PY")).load_module()
    core = dict(core)
    core.update({"PAYLOAD/" + n: b for n, b in panui.runtimes().items()})
    native = json.loads((HERE / "SETNAT.JSN").read_bytes())
    helper = pub.read_file(HERE, "BIN/SETUP.EXE")
    pub.require(pub.identity(helper) == native["binary"], "Expanded Setup binary differs")
    for name, pin in native["sources"].items():
        pub.require(pub.identity(pub.read_file(HERE, name)) == pin, "Expanded Setup source differs: " + name)
    last, pages = struct.unpack_from("<HH", helper, 2)
    pub.require(helper[:2] == b"MZ" and pages * 512 - (512 - last if last else 0) == len(helper),
                "Setup must be a plain DOS executable without an appended archive")
    entries = {"SETUP.EXE": helper, "README.TXT": pub.read_file(HERE, "INSTALL.TXT")}
    entries.update({"WINXT/" + n[8:]: body for n, body in core.items() if n.startswith("PAYLOAD/")})
    # Keep the legacy full Setup metadata as a separate native-input alias.
    # Ordinary Windows Setup reads the movable OEM descriptor directly.
    entries["WINXT/HPXY.INF"] = entries.pop("WINXT/OEMSETUP.INF")
    entries["WINXT/OEMSETUP.INF"] = pub.read_file(HERE.parent / "XROEM", "OEMSETUP.INF")
    generator = importlib.machinery.SourceFileLoader("expanded_setup_aliases", str(HERE / "MAKESET.PY")).load_module()
    for name, body in generator.generate().items():
        pub.require(pub.read_file(HERE, name) == body, "Expanded input alias differs: " + name)
    for name in ("NOTICE.TXT", "OWATCOM.TXT", "WHEELLIC.TXT", "SOUNDID.JSN", "SOUNDLIC.TXT"):
        entries["WINXT/" + name] = core[name]
    for name in ("DISPLAY.BAT", "DISPWIN.BAT", "DISPLAY.TXT"):
        entries["WINXT/" + name] = pub.read_file(HERE.parent / "XROEM", name)
    pub.require({n.split('/')[0] for n in entries} == {"SETUP.EXE", "README.TXT", "WINXT"}, "Installer root layout differs")
    pub.require(not any(n.endswith((".ZIP", ".PY")) for n in entries), "Nested archive/host tool in expanded installer")
    descriptor = entries["WINXT/OEMSETUP.INF"].decode("ascii")
    pub.require(not re.search(r"[A-Za-z]:[\\/]", descriptor), "Ordinary OEM source must not hardcode an extraction directory")
    referenced = re.findall(r"[aA]:([A-Za-z0-9_.]+)", descriptor)
    pub.require(referenced and all("WINXT/" + n.upper() in entries for n in referenced),
                "Ordinary OEM source references missing support files")
    for name in entries:
        pub.safe_path(name)
        pub.require(all(media.DOS_PART.fullmatch(p) for p in name.split('/')), "Non-DOS installer filename: " + name)
    return entries

def expanded_qualification(entries, archive):
    q = json.loads((REPO / "docs/QUAL/DOSINST/EXPAND.JSN").read_bytes())
    if q["archive"] != pub.identity(archive):
        try:
            panui = importlib.machinery.SourceFileLoader(
                "current_panui_package", str(HERE / "PANUI.PY")).load_module()
            return panui.qualify(entries, archive, q)
        except FileNotFoundError as exc:
            raise ValueError("Current panning package qualification missing") from exc
    pub.require(q["status"] == "PASS_EXPANDED_NATIVE" and q["physical_test"] is False,
                "Expanded installer qualification incomplete")
    pub.require(q["archive"] == pub.identity(archive), "Expanded archive differs from native test input")
    pub.require(q["files"] == {n: pub.identity(b) for n, b in sorted(entries.items())},
                "Expanded members differ from native input")
    for name in ("fresh", "update", "drivers_only"):
        case = q[name]
        pub.require(case["complete"] and not case.get("error") and case["owned_stopped"] and case["lease_released"],
                    "Expanded native case incomplete: " + name)
        pub.require(case["archive"] == q["archive"], "Different archive tested: " + name)
        if name != "drivers_only":
            pub.require(case["helper"] == pub.identity(entries["SETUP.EXE"]), "Different Setup tested: " + name)
            pub.require(case["prepared_comparison"] == {"count": 370 if name == "fresh" else 83, "different": []},
                        "Expanded prepared files differ: " + name)
    evidence_root = REPO / "docs/QUAL/DOSINST"
    required = {"EXUP.LOG", "EXUP.PNG", "EXMISS.LOG", "EXBAD.LOG", "EXBAD.PNG", "EXCASE.JSN", "EXFRESH.LOG", "EXFRESH.PNG"}
    pub.require(required <= set(q["evidence"]), "Expanded raw evidence inventory incomplete")
    for name, pin in q["evidence"].items():
        pub.safe_path(name)
        pub.require(pub.identity(pub.read_file(evidence_root, name)) == pin, "Expanded evidence differs: " + name)
    oem_root = HERE.parent / "XROEM"
    oem = json.loads(pub.read_file(oem_root, "NATIVE.JSN"))
    pub.require(oem["complete"] and oem["packet"] == q["archive"] and
                oem["members"] == q["files"] and all(oem["checks"].values()), "Ordinary OEM qualification differs")
    for name, pin in oem["sources"].items():
        pub.require(pub.identity(entries["WINXT/" + name]) == pin, "Ordinary OEM source differs: " + name)
    for name, pin in oem["evidence"].items():
        pub.safe_path(name)
        pub.require(pub.identity(pub.read_file(oem_root / "QA", name)) == pin, "Ordinary OEM evidence differs: " + name)
    driver = q["drivers_only"]
    pub.require(driver["custom_setup_executed"] is False and driver["descriptor_unchanged"] is True,
                "Drivers-only case depended on custom preparation")
    pub.require(driver["alternate_source"].upper().rstrip("\\") != "C:\\WINXT",
                "Alternate ordinary OEM extraction path was not tested")
    pub.require(q["negative"]["helper"] == pub.identity(entries["SETUP.EXE"]) and
                q["negative"]["archive"] == q["archive"], "Different expanded negative case input")
    pub.require(q["negative"]["complete"] and q["negative"]["owned_stopped"] and q["negative"]["lease_released"],
                "Expanded negative cases incomplete")
    return q

def build(output, commit, verify=False):
    pub.require(re.fullmatch(r"[0-9a-f]{40}", commit or ""), "Full source commit required")
    entries = expanded_entries()
    archive = pub.zip_bytes(entries)
    pub.check_zip(archive, entries, "WINXT.ZIP")
    qualification = expanded_qualification(entries, archive)
    # Complete corresponding SOUND source is a separate developer asset;
    # the consumer tree contains only expanded runtime, notices and licences.
    source = pub.read_file(REPO, "tools/XR1PACK/SOUNDSRC.ZIP")
    report = {"schema": 2, "tag": "windows-xt", "source_commit": commit,
              "native_report": ("docs/QUAL/HPXY/PACKAGE.JSN" if
                                qualification["status"] == "PASS_CANONICAL_HPXY_PACKAGE" else
                                "docs/QUAL/WDESK/PACKAGE.JSN" if
                                qualification["status"] == "PASS_NATIVE_PACKAGE" else
                                "docs/QUAL/DOSINST/EXPAND.JSN"), "physical_qualification": False,
              "archive": pub.identity(archive), "sound_source": pub.identity(source),
              "files": {n: pub.identity(d) for n, d in sorted(entries.items())}}
    assets = {"WINXT.ZIP": archive, "WINXTSRC.ZIP": source, "WINXT.JSN": pub.json_bytes(report)}
    assets["WINXT.SHA"] = pub.sums_bytes(assets)
    if output.exists():
        pub.require({p.name for p in output.iterdir()} == set(ASSETS), "Release inventory differs")
        for name, data in assets.items():
            pub.require(pub.read_file(output, name) == data, "Release differs: " + name)
    else:
        pub.require(not verify, "Verification directory missing")
        output.mkdir(parents=True)
        for name, data in assets.items():
            (output / name).write_bytes(data)
    return {n: pub.identity(d) for n, d in assets.items()}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--out", type=Path)
    action.add_argument("--verify", type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.verify or args.out, args.commit, bool(args.verify)), indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, "Refused: " + str(exc) + "\n")

if __name__ == "__main__":
    main()
