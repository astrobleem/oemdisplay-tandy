"""Publish the exact tested XRSYNC driver in a complete DOS installation kit."""
import argparse
import importlib.util
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
loader = SourceFileLoader("xrpublisher", str(HERE.parent / "XR1PACK" / "PUBLISH.PY"))
spec = importlib.util.spec_from_loader(loader.name, loader)
pub = importlib.util.module_from_spec(spec)
loader.exec_module(pub)
media = SourceFileLoader("xs_media", str(HERE.parent / "XR1PACK/PREPARE.PY")).load_module()
DRIVER = {"bytes": 60800, "sha256":
          "ae2d06f69ff68e64f099c3e0af79028e40e7dca89bd442de23eb18d36be4dca1"}


def collect():
    spec = json.loads((HERE / "PUBLIC.JSN").read_bytes())
    pub.require(spec["schema"] == 2, "Unsupported public manifest")
    entries = {}
    for name, record in spec["files"].items():
        pub.safe_path(name)
        data = pub.read_file(REPO, record["source"])
        pub.require(pub.identity(data) == record.get("source_identity", record["identity"]), "Source pin differs: " + name)
        if record.get("encoding") == "SZDD":
            data = media.expanded_file(data, name)
        pub.require(pub.identity(data) == record["identity"], "Expanded pin differs: " + name)
        entries[name] = data
    pub.require(pub.identity(entries["PAYLOAD/XRSYNC.DRV"]) == DRIVER,
                "Driver differs from the native-qualified candidate")
    public_payload = {n[8:]: pub.identity(d) for n, d in entries.items() if n.startswith("PAYLOAD/")}
    header = (HERE.parent / "DOSINST/XSPINS.H").read_text()
    rows = re.findall(r'{"([^"\n]+)","([0-9a-f]{64})",(\d+)UL,0,0x[0-9a-f]+UL}', header)
    expected = {n: {"bytes": int(size), "sha256": sha} for n, sha, size in rows}
    runtime = {n: pin for n, pin in public_payload.items() if n in expected}
    pub.require(len(expected) == 10 and runtime == expected, "Native runtime inventory differs")
    pub.require(set(public_payload) == set(expected) | {"README.TXT", "NOTICE.TXT", "FONTLIC.TXT", "LOGOLIC.TXT"}, "Payload inventory differs")
    pub.require(not any(n.endswith(".PY") for n in entries), "Consumer kit includes host preparation")
    native = json.loads((HERE.parent / "DOSINST/XSNATIVE.JSN").read_bytes())
    pub.require(pub.identity(entries["XSETUP.EXE"]) == native["binary"], "Native helper differs")
    for name, pin in native["sources"].items():
        pub.require(pub.identity(pub.read_file(HERE.parent / "DOSINST", name)) == pin,
                    "Native build source differs: " + name)
    mz_size(entries["XSETUP.EXE"])
    return entries


def mz_size(data):
    pub.require(len(data) >= 28 and data[:2] == b"MZ", "Native helper is not a DOS EXE")
    last, pages = struct.unpack_from("<HH", data, 2)
    size = pages * 512 - (512 - last if last else 0)
    pub.require(0 < size == len(data), "Native EXE image length differs")
    return size


def build(output, commit):
    pub.require(re.fullmatch(r"[0-9a-f]{40}", commit or ""), "Full source commit required")
    entries = collect()
    archive = pub.zip_bytes(entries)
    pub.check_zip(archive, entries, "XRSYNC.ZIP")
    qualified = json.loads((REPO / "docs/QUAL/DOSINST/XRSYNC.JSN").read_bytes())
    pub.require(qualified["install"]["complete"] and qualified["cold"]["complete"] and
                all(qualified["checks"].values()), "Native qualification incomplete")
    packet = pub.zip_bytes(entries)
    pub.require(qualified["public_assets"]["XRSYNC.ZIP"] == pub.identity(packet) and
                qualified["public_assets"]["XRSYNC.EXE"] == pub.identity(entries["XSETUP.EXE"] + packet),
                "Package differs from native-qualified download")
    report = {"schema": 2, "source_commit": commit, "driver": DRIVER,
              "files": {n: pub.identity(d) for n, d in sorted(entries.items())},
              "includes_supplied_cga_grabber": True, "contains_windows_os_media": False, "physical_qualification": False,
              "runtime_report": "docs/RRSYNC.MD", "runtime_evidence": "docs/rrsync/",
              "native_installation": "docs/QUAL/DOSINST/XRSYNC.JSN",
              "consumer_command": "XRSYNC C:\\WINDOWS"}
    result = {"XRSYNC.EXE": entries["XSETUP.EXE"] + archive, "XRSYNC.ZIP": archive, "README.TXT": entries["README.TXT"],
              "RELEASE.JSON": (json.dumps(report, indent=2) + "\n").replace("\n", "\r\n").encode("ascii")}
    result["SHA256SUMS"] = "".join(pub.digest(d) + "  " + n + "\r\n"
                                    for n, d in sorted(result.items())).encode("ascii")
    if output.exists():
        pub.require({p.name for p in output.iterdir()} == set(result), "Release inventory differs")
        for name, data in result.items():
            pub.require(pub.read_file(output, name) == data, "Release differs: " + name)
    else:
        output.mkdir(parents=True)
        for name, data in result.items():
            (output / name).write_bytes(data)
    print(json.dumps({n: pub.identity(d) for n, d in result.items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    try:
        build(args.out, args.commit)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, "Refused: " + str(exc) + "\n")
