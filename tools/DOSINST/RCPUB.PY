"""Deterministic publisher for the DOS-native rc.8 consumer kit."""
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
ASSETS = ("WINXT.EXE", "WINXT.ZIP", "README.TXT", "RELEASE.JSON", "SHA256SUMS")

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
    pub.require(len(runtime) == 48 and set(runtime) == {n for n in entries if n.startswith("PAYLOAD/")}, "Runtime inventory differs")
    pub.require(set(entries) == set(runtime) | {"PREPXR.EXE", "README.TXT", "NOTICE.TXT", "OWATCOM.TXT", "WHEELLIC.TXT"}, "Consumer archive inventory differs")
    for name, pin in runtime.items():
        pub.require(pub.identity(entries[name]) == pin, "Compiled runtime differs: " + name)
    pub.require(not any(n.endswith(".PY") for n in entries), "Private/host preparation file in consumer kit")
    native = json.loads((HERE / "RCNATIVE.JSN").read_bytes())
    pub.require(pub.identity(entries["PREPXR.EXE"]) == native["binary"], "Native helper differs")
    for name, pin in native["sources"].items():
        pub.require(pub.identity(pub.read_file(HERE, name)) == pin, "Native source differs: " + name)
    for record in native.get("companions", {}).values():
        for key in ("source", "binary"):
            pub.require(pub.identity(pub.read_file(REPO, record[key])) == record[key + "_identity"], "Companion differs: " + record[key])
    helper = entries["PREPXR.EXE"]
    pub.require(helper[:2] == b"MZ" and len(helper) >= 28, "DOS MZ helper required")
    last, pages = struct.unpack_from("<HH", helper, 2)
    pub.require(pages * 512 - (512 - last if last else 0) == len(helper), "Native EXE image length differs")
    return entries

def build(output, commit, verify=False):
    pub.require(re.fullmatch(r"[0-9a-f]{40}", commit or ""), "Full source commit required")
    entries = collect()
    archive = pub.zip_bytes(entries)
    pub.check_zip(archive, entries, "WINXT.ZIP")
    executable = entries["PREPXR.EXE"] + archive
    q = json.loads((REPO / "docs/QUAL/DOSINST/RC8.JSN").read_bytes())
    pub.require(q["status"] == "PASS_NATIVE_AND_HOST" and not q["physical_test"], "Native qualification incomplete")
    for mode in ("fresh", "update"):
        row = q[mode]
        pub.require(row["complete"] and row["owned_stopped"] and row["lease_released"], "Native case incomplete: " + mode)
        pub.require(row["prepared_comparison"]["count"] == (367 if mode == "fresh" else 80) and not row["prepared_comparison"]["different"], "Prepared bytes differ: " + mode)
    pub.require(q["cold"]["complete"] and q["cold"]["owned_stopped"] and q["cold"]["lease_released"], "Cold launch incomplete")
    pub.require(q["public_assets"]["WINXT.ZIP"] == pub.identity(archive) and q["public_assets"]["WINXT.EXE"] == pub.identity(executable), "Package differs from qualified native kit")
    report = {"schema": 1, "tag": "v0.1.0-rc.8-dos.1", "source_commit": commit,
              "native_report": "docs/QUAL/DOSINST/RC8.JSN", "physical_qualification": False,
              "files": {n: pub.identity(d) for n, d in sorted(entries.items())}}
    assets = {"WINXT.EXE": executable, "WINXT.ZIP": archive,
              "README.TXT": entries["README.TXT"], "RELEASE.JSON": pub.json_bytes(report)}
    assets["SHA256SUMS"] = pub.sums_bytes(assets)
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
