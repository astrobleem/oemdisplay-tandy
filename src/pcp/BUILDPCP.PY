#!/usr/bin/env python3
"""Build the proposed Plantronics driver PCP3216.DRV (320x200x16) via BUILD88.

Usage (same pinned inputs as BUILD88; see tools/BUILDDEPS/README.MD):
  python3 src/pcp/BUILDPCP.PY --repo <DEPS.PY display view> \
      --dosbox <dosbox-x> --out <fresh-dir>

Runs the view's own src/tandysw/BUILD88.PY unchanged for profile 320x200x16,
with one interposition: after BUILD88 has staged and ported every source and
before the first DOSBox-X assembly, PCPPATCH.patch_staged() edits the staged
EGA/TSOFT.ASM and EGA/TCURSOR.ASM. BUILD88's own instruction, REP-prefix and
link audits then run on the patched listings. The result is copied to
PCP3216.DRV and summarized in PCPRES.JSON.

A successful build is not runtime acceptance. No package or pin is changed.
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PCPPATCH = importlib.machinery.SourceFileLoader("pcppatch", str(HERE / "PCPPATCH.PY")).load_module()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    tandysw = repo / "src" / "tandysw"
    sys.path.insert(0, str(tandysw))
    b88 = importlib.machinery.SourceFileLoader("build88_pcp", str(tandysw / "BUILD88.PY")).load_module()

    state = {}
    real_prepare = b88.baseline.prepare
    real_run = b88.bounded_run

    def prepare(r, o):
        renderer, resources = real_prepare(r, o)
        state["renderer"] = renderer
        return renderer, resources

    def run(command, env, path, timeout=180):
        if "patched" not in state:
            ega = Path(state["renderer"]) / "EGA"
            edits = PCPPATCH.patch_staged(ega)
            state["patched"] = {k: hashlib.sha256(v.encode("latin-1")).hexdigest()
                                for k, v in edits.items()}
        return real_run(command, env, path, timeout)

    b88.baseline.prepare = prepare
    b88.bounded_run = run
    sys.argv = ["BUILD88.PY", "--repo", str(repo), "--dosbox", str(a.dosbox),
                "--out", str(out), "--mode", "320x200x16"]
    b88.main()
    if "patched" not in state:
        raise SystemExit("BUILDPCP: Plantronics edits were never applied")

    result = json.loads((out / "RESULT.json").read_text())
    built = out / Path(result["mode"]["driver"]).name if isinstance(result.get("mode"), dict) and "driver" in result["mode"] else None
    if built is None or not built.exists():
        drvs = [p for p in out.glob("*.DRV")]
        if len(drvs) != 1:
            raise SystemExit("BUILDPCP: expected exactly one built driver, found %d" % len(drvs))
        built = drvs[0]
    target = out / "PCP3216.DRV"
    shutil.copyfile(built, target)
    data = target.read_bytes()
    summary = {
        "driver": "PCP3216.DRV",
        "built_as": built.name,
        "driver_bytes": len(data),
        "driver_sha256": hashlib.sha256(data).hexdigest(),
        "base": "BUILD88 320x200x16 (TR5) from the supplied view",
        "plantronics_edits_staged_sha256": state["patched"],
        "build88_audits": "see RESULT.json (instruction, REP-prefix, link)",
        "runtime": "NOT_TESTED",
    }
    (out / "PCPRES.JSON").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
