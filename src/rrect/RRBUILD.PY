#!/usr/bin/env python3
"""Build a TR5 driver variant for the RoundRect investigation (src/rrect).

  python3 src/rrect/RRBUILD.PY --repo <DEPS.PY display view> --dosbox <dosbox-x> \\
      --out <fresh dir> --mode 320x200x16 --variant baseline|trace|noflush|nodraw|candidate|candidate-trace

Runs the view's BUILD88.PY unchanged; for any variant other than baseline,
RRPATCH edits are applied to the staged EGA/TSOFT.ASM (and only there)
after all staging and before the first assembly, so BUILD88's instruction,
REP-prefix and link audits run on the patched listings. 'baseline' must
reproduce the accepted TR5 driver (docs/TRIAL5/BUILDS.JSN).
Writes <out>/RRBUILD.JSN and <out>/<ALIAS>.DRV. A build is not runtime
acceptance; 'trace' builds are test instruments and must never ship.
"""
import argparse
import hashlib
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader("rrpatch", str(HERE / "RRPATCH.PY")).load_module()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def edits_for(variant):
    if variant == "baseline":
        return []
    if variant == "trace":
        return [P.patch_trace]
    if variant == "noflush":
        return [P.patch_noflush]
    if variant == "nodraw":
        return [P.patch_nodraw]
    if variant == "candidate":
        return [P.patch_candidate]
    if variant == "candidate-trace":
        return [P.patch_candidate, P.patch_trace]
    raise SystemExit("RRBUILD: unknown variant " + variant)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", required=True)
    ap.add_argument("--variant", required=True)
    a = ap.parse_args(argv)
    repo, out = a.repo.resolve(), a.out.resolve()
    if out.exists():
        raise SystemExit(f"RRBUILD: {out} exists")
    edits = edits_for(a.variant)
    tandysw = repo / "src" / "tandysw"
    sys.path.insert(0, str(tandysw))
    b88 = importlib.machinery.SourceFileLoader("build88_rr", str(tandysw / "BUILD88.PY")).load_module()
    state = {}
    real_prepare = b88.baseline.prepare
    real_run = b88.bounded_run

    def prepare(r, o):
        renderer, resources = real_prepare(r, o)
        state["renderer"] = Path(renderer)
        return renderer, resources

    def run(command, env, path, timeout=180):
        if "patched" not in state:
            tsoft = state["renderer"] / "EGA" / "TSOFT.ASM"
            before = tsoft.read_bytes()
            text = before.decode("latin-1")
            for fn in edits:
                text = fn(text)
            if "\n" in text.replace("\r\n", ""):
                raise SystemExit("RRBUILD: bare LF in patched TSOFT.ASM")
            tsoft.write_bytes(text.encode("latin-1"))
            state["patched"] = {"staged_tsoft_before_sha256": sha(before),
                                "staged_tsoft_after_sha256": sha(text.encode("latin-1"))}
        return real_run(command, env, path, timeout)

    b88.baseline.prepare = prepare
    b88.bounded_run = run
    sys.argv = ["BUILD88.PY", "--repo", str(repo), "--dosbox", str(a.dosbox), "--out", str(out),
                "--mode", a.mode]
    b88.main()
    if "patched" not in state:
        raise SystemExit("RRBUILD: interposition did not run")
    res = json.loads((out / "RESULT.json").read_text())
    if res.get("build") != "PASS":
        raise SystemExit("RRBUILD: BUILD88 did not report PASS")
    drv = next(out.glob("*.DRV"))
    data = drv.read_bytes()
    summary = {"variant": a.variant, "mode": a.mode, "driver_file": drv.name, "bytes": len(data),
               "sha256": sha(data), **state["patched"],
               "build88": {k: res[k] for k in ("build", "instruction_audit", "rep_prefix_audit", "link_audit",
                                                "resource_sha256") if k in res},
               "runtime": "NOT_TESTED by this build"}
    (out / "RRBUILD.JSN").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("variant", "mode", "bytes", "sha256")}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
