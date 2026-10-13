#!/usr/bin/env python3
"""Build the experimental text-mode drivers via BUILD88 (docs/TEXT80.MD).

  python3 src/text80/BUILDT80.PY --repo <DEPS.PY display view> --dosbox <dosbox-x>
      --out <fresh dir> --variant <name>

Variants (each is BUILD88's own build of a profile, with staged edits applied
after every port step and before the first assembly; BUILD88's instruction,
REP-prefix and link audits then run on the edited listings):
  t40        TXT40 exactly as on ai/txt40-tv (T40PATCH; 320x200x16)
  t40prof    t40 + T80PROF timers/counters (measurement build)
Further variants are added by the TEXT80 work as it lands.
The driver is copied to <out>/<OUTNAME> and summarized in <out>/T80RES.JSON.
A successful build is not runtime acceptance; no package or pin changes.
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(name, path):
    return importlib.machinery.SourceFileLoader(name, str(path)).load_module()


def variants():
    t40 = load("t40patch", ROOT / "txt40" / "T40PATCH.PY")
    prof = load("t80prof", HERE / "T80PROF.PY")
    return {
        "t40": dict(mode="320x200x16", out="TXT40.DRV", edits=[t40.patch_staged]),
        "t40prof": dict(mode="320x200x16", out="T40PROF.DRV", edits=[t40.patch_staged, prof.patch_staged]),
    }


def main():
    vs = variants()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--variant", required=True, choices=sorted(vs))
    a = ap.parse_args()
    v = vs[a.variant]
    repo, out = a.repo.resolve(), a.out.resolve()
    tandysw = repo / "src" / "tandysw"
    sys.path.insert(0, str(tandysw))
    b88 = load("build88_t80", tandysw / "BUILD88.PY")
    state = {}
    real_prepare, real_run = b88.baseline.prepare, b88.bounded_run

    def prepare(r, o):
        renderer, resources = real_prepare(r, o)
        state["renderer"] = renderer
        return renderer, resources

    def run(command, env, path, timeout=180):
        if "patched" not in state:
            ega = Path(state["renderer"]) / "EGA"
            staged = {}
            for edit in v["edits"]:
                for k, t in edit(ega).items():
                    staged[k] = hashlib.sha256(t.encode("latin-1")).hexdigest()
            state["patched"] = staged
        return real_run(command, env, path, timeout)

    b88.baseline.prepare, b88.bounded_run = prepare, run
    sys.argv = ["BUILD88.PY", "--repo", str(repo), "--dosbox", str(a.dosbox), "--out", str(out),
                "--mode", v["mode"]]
    b88.main()
    if "patched" not in state:
        raise SystemExit("BUILDT80: edits were never applied")
    result = json.loads((out / "RESULT.json").read_text())
    if result.get("build") != "PASS":
        raise SystemExit("BUILDT80: build did not report PASS; see RESULT.json")
    drvs = [p for p in out.glob("*.DRV")]
    if len(drvs) != 1:
        raise SystemExit("BUILDT80: expected exactly one built driver, found %d" % len(drvs))
    target = out / v["out"]
    shutil.copyfile(drvs[0], target)
    data = target.read_bytes()
    summary = {"variant": a.variant, "driver": v["out"], "built_as": drvs[0].name, "mode": v["mode"],
               "driver_bytes": len(data), "driver_sha256": hashlib.sha256(data).hexdigest(),
               "edits_staged_sha256": state["patched"],
               "build88_audits": "see RESULT.json (instruction, REP-prefix, link)", "runtime": "NOT_TESTED"}
    (out / "T80RES.JSON").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
