"""Publish the exact tested XRSYNC driver in a deterministic own-media kit."""
import argparse
import importlib.util
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
loader = SourceFileLoader("xrpublisher", str(HERE.parent / "XR1PACK" / "PUBLISH.PY"))
spec = importlib.util.spec_from_loader(loader.name, loader)
pub = importlib.util.module_from_spec(spec)
loader.exec_module(pub)
DRIVER = {"bytes": 60800, "sha256":
          "ae2d06f69ff68e64f099c3e0af79028e40e7dca89bd442de23eb18d36be4dca1"}


def collect():
    spec = json.loads((HERE / "PUBLIC.JSN").read_bytes())
    pub.require(spec["schema"] == 1, "Unsupported public manifest")
    entries = {}
    for name, record in spec["files"].items():
        pub.safe_path(name)
        data = pub.read_file(REPO, record["source"])
        pub.require(pub.identity(data) == record["identity"], "Source pin differs: " + name)
        entries[name] = data
    pub.require(pub.identity(entries["PAYLOAD/XRSYNC.DRV"]) == DRIVER,
                "Driver differs from the native-qualified candidate")
    public_payload = {n[8:]: pub.identity(d) for n, d in entries.items() if n.startswith("PAYLOAD/")}
    inputs = json.loads(entries["INPUTS.JSN"])
    pub.require(inputs["payload"] == public_payload, "Prepared runtime inventory differs")
    pub.require("CGA.GR2" not in public_payload, "Owned grabber cannot be public")
    return entries


def build(output, commit):
    pub.require(re.fullmatch(r"[0-9a-f]{40}", commit or ""), "Full source commit required")
    entries = collect()
    archive = pub.zip_bytes(entries)
    pub.check_zip(archive, entries, "XRSYNC.ZIP")
    report = {"schema": 1, "source_commit": commit, "driver": DRIVER,
              "files": {n: pub.identity(d) for n, d in sorted(entries.items())},
              "contains_owned_windows_bytes": False, "physical_qualification": False,
              "runtime_report": "docs/RRSYNC.MD", "runtime_evidence": "docs/rrsync/"}
    result = {"XRSYNC.ZIP": archive, "README.TXT": entries["README.TXT"],
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
