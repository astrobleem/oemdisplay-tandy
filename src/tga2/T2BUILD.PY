#!/usr/bin/env python3
"""Build the experimental Tandy 1000 SL/TL/RL Video II driver TNDYV2.DRV (640x200x16).

Usage (same pinned inputs as BUILD88; see tools/BUILDDEPS/README.MD):
  python3 src/tga2/T2BUILD.PY --repo <DEPS.PY display view> \
      --dosbox <dosbox-x> --out <fresh-dir>

1. Runs the view's BUILD88.PY unchanged for 320x200x16 into OUT/B320 (the
   accepted TANDY88 build; its driver hash is recorded).
2. Runs BUILD88.PY unchanged for 640x200x4 into OUT/B640, so every 640-pixel
   stage and every BUILD88 pin is exercised as-is: geometry, CGA fonts and
   metrics, byte columns, cursor retention, output rows, wide scanlines,
   REP-copy rewriting, resources.
3. One interposition, after all staging and before the first DOSBox-X
   assembly of step 2:
     - the six files MODECOL rewrote for four colours are replaced by their
       320x200x16 stage copies, and MODECOL's TSOFT colour-table sections by
       the 320x200x16 ones (P15PATCH.restore_sixteen): sixteen colours again;
     - T2PATCH edits the staged EGA/TSOFT.ASM, EGA/TCURSOR.ASM and the
       EGA/TSOFT.DEF description for Video II (docs/TGA2.MD).
   This is the PC1512 build (src/pc1512/BUILD15.PY) with T2PATCH in place of
   P15PATCH's hardware edits.
   BUILD88's instruction, REP-prefix and link audits then run on the
   patched listings.
The driver is copied to OUT/TNDYV2.DRV; T2RES.JSON records what was used.
A build is not runtime acceptance.
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P15 = importlib.machinery.SourceFileLoader("p15patch", str(HERE.parent / "pc1512" / "P15PATCH.PY")).load_module()
T2 = importlib.machinery.SourceFileLoader("t2patch", str(HERE / "T2PATCH.PY")).load_module()

DEF_OLD = "Tandy 640x200 4-color software raster"
DEF_NEW = "Tandy Video II 640x200 16-color raster"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tandysw = repo / "src" / "tandysw"

    b320 = out / "B320"
    subprocess.run([sys.executable, str(tandysw / "BUILD88.PY"), "--repo", str(repo),
                    "--dosbox", str(a.dosbox), "--out", str(b320), "--mode", "320x200x16"],
                   check=True, stdout=open(out / "B320.LOG", "w"), stderr=subprocess.STDOUT)
    r320 = json.loads((b320 / "RESULT.json").read_text())
    if r320.get("build") != "PASS":
        raise SystemExit("T2BUILD: 320x200x16 base did not build")
    base = b320 / "renderer"

    sys.path.insert(0, str(tandysw))
    b88 = importlib.machinery.SourceFileLoader("build88_t2", str(tandysw / "BUILD88.PY")).load_module()
    state = {}
    real_prepare = b88.baseline.prepare
    real_run = b88.bounded_run

    def prepare(r, o):
        renderer, resources = real_prepare(r, o)
        state["renderer"] = Path(renderer)
        return renderer, resources

    def run(command, env, path, timeout=180):
        if "patched" not in state:
            ren = state["renderer"]
            restored = {}
            for name in P15.MODECOL_FILES:
                before = (ren / name).read_bytes()
                src = (base / name).read_bytes()
                (ren / name).write_bytes(src)
                restored[name] = {"four_colour_sha256": sha(before), "sixteen_colour_sha256": sha(src)}
            tsoft = ren / "EGA" / "TSOFT.ASM"
            text = P15.restore_sixteen(tsoft.read_bytes().decode("latin-1"),
                                       (base / "EGA" / "TSOFT.ASM").read_bytes().decode("latin-1"))
            tsoft.write_bytes(text.encode("latin-1"))
            edits = T2.patch_staged(ren / "EGA")
            d = ren / "EGA" / "TSOFT.DEF"
            t = d.read_bytes().decode("latin-1")
            if t.count(DEF_OLD) != 1:
                raise SystemExit("T2BUILD: TSOFT.DEF description not found once")
            d.write_bytes(t.replace(DEF_OLD, DEF_NEW).encode("latin-1"))
            state["restored"] = restored
            state["patched"] = {k: sha(v.encode("latin-1")) for k, v in edits.items()}
        return real_run(command, env, path, timeout)

    b88.baseline.prepare = prepare
    b88.bounded_run = run
    b640 = out / "B640"
    sys.argv = ["BUILD88.PY", "--repo", str(repo), "--dosbox", str(a.dosbox),
                "--out", str(b640), "--mode", "640x200x4"]
    b88.main()
    if "patched" not in state:
        raise SystemExit("T2BUILD: interposition did not run")
    r640 = json.loads((b640 / "RESULT.json").read_text())
    if r640.get("build") != "PASS":
        raise SystemExit("T2BUILD: BUILD88 did not report PASS")
    data = (b640 / "TNDY6404.DRV").read_bytes()
    (out / "TNDYV2.DRV").write_bytes(data)
    summary = {
        "driver": "TNDYV2.DRV", "bytes": len(data), "sha256": sha(data),
        "base_320x200x16": {"driver_sha256": r320.get("driver_sha256"),
                            "resource_sha256": r320.get("resource_sha256")},
        "pipeline": "BUILD88 --mode 640x200x4 unchanged; sixteen-colour files/sections restored "
                    "from the 320x200x16 stage; T2PATCH; BUILD88 audits on the patched listings",
        "restored_from_320x200x16": state["restored"],
        "staged_patched_sha256": state["patched"],
        "build88": {k: r640[k] for k in ("build", "runtime", "resource_sha256", "instruction_audit",
                                          "rep_prefix_audit", "link_audit") if k in r640},
        "runtime": "NOT_TESTED by this build",
    }
    (out / "T2RES.JSON").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("driver", "bytes", "sha256")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
