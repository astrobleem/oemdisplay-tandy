#!/usr/bin/env python3
"""Build the experimental text-mode drivers via BUILD88 (docs/TEXT80.MD).

  python3 src/text80/BUILDT80.PY --repo <DEPS.PY display view> --dosbox <dosbox-x>
      --out <fresh dir> --variant <name>

Variants (each is BUILD88's own build of a profile, with staged edits applied
after every port step and before the first assembly; BUILD88's instruction,
REP-prefix and link audits then run on the edited listings):
  t40        TXT40 with this branch's presenter fixes (T40PATCH; 320x200x16)
  t40prof    t40 + T80PROF timers/counters (measurement build)
  t80        TEXT80 80x25 colour text (T80PATCH over the same pipeline; the
             640x200 resources of the 640x200 profiles, hash-checked)
  t80c       t80 with the compact UI profile (T80UI: one-cell window controls)
  t80cprof   t80c + T80PROF
  t80prof    t80 + T80PROF
  t80pan     TEXT80 80x25 over a 640x400 desktop, panned (T80TALL pan)
  t80panprof t80pan + T80PROF
  t80panfail t80pan with GlobalAlloc asked for 7FA00h bytes (fault
             injection: Enable's allocation-failure path; test build only)
  t80vga     TEXT80 VGA 80x50, 640x400 (T80TALL vga)
  t80vgaprof t80vga + T80PROF
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


RES640_SHA = "4bdf9197db27b33dd5859c4198534aa7db6cb2066fe8075caff1899ff25cb312"


def res640(repo, resources):
    """The CGA-resolution resources of MODEPROF's 640x200 profiles: the
    DDK's RC_LOW font resources and 2-pixel vertical borders."""
    mp = load("modeprof_t80", repo / "src" / "tandysw" / "MODEPROF.PY")
    low = repo / "DDK/286/DISPLAY/1PLANE/RC_LOW"
    mp.write(resources / "FONTS.ASM", mp.read(low / "FONTS.ASM").replace(chr(26), ""))
    cfg = mp.read(resources / "CONFIG.ASM")
    mp.write(resources / "CONFIG.ASM", mp.replace(cfg, "\tdw\t1\t\t\t;cxBorder", "\tdw\t2\t\t\t;cxBorder"))


# t80c (compact UI profile): res640 plus T80UI's one-cell window controls
RESC_SHA = "d37e6c7931c974e12e533e8fc9fb70dab4671d2d13f6ca45cf2da24bfda193f2"


def res_compact(repo, resources):
    res640(repo, resources)
    mp = load("modeprof_t80c", repo / "src" / "tandysw" / "MODEPROF.PY")
    load("t80ui", HERE / "T80UI.PY").stage(resources, mp)


def variants():
    prof = load("t80prof", HERE / "T80PROF.PY")
    t40 = lambda e: load("t40patch", ROOT / "txt40" / "T40PATCH.PY").patch_staged(e)
    t80 = lambda e: load("t80patch", HERE / "T80PATCH.PY").patch_staged(e)
    tall = lambda kind: (lambda e: load("t80tall", HERE / "T80TALL.PY").patch_staged(e, kind))
    return {
        "t40": dict(mode="320x200x16", out="TXT40.DRV", edits=[t40]),
        "t40prof": dict(mode="320x200x16", out="T40PROF.DRV", edits=[t40, prof.patch_staged]),
        "t80": dict(mode="320x200x16", out="TEXT80.DRV", edits=[t80], res=res640, res_sha=RES640_SHA),
        "t80c": dict(mode="320x200x16", out="T80CMP.DRV", edits=[t80], res=res_compact, res_sha=RESC_SHA),
        "t80cprof": dict(mode="320x200x16", out="T80PROF.DRV", edits=[t80, prof.patch_staged], res=res_compact,
                         res_sha=RESC_SHA),
        "t80prof": dict(mode="320x200x16", out="T80PROF.DRV", edits=[t80, prof.patch_staged], res=res640,
                        res_sha=RES640_SHA),
        "t80pan": dict(mode="320x200x16", out="T80PAN.DRV", edits=[tall("pan")], res=res640, res_sha=RES640_SHA),
        "t80panprof": dict(mode="320x200x16", out="T80PANP.DRV", edits=[tall("pan"), prof.patch_staged],
                           res=res640, res_sha=RES640_SHA),
        "t80panfail": dict(mode="320x200x16", out="T80PAN.DRV", edits=[tall("panfail")], res=res640,
                           res_sha=RES640_SHA),
        "t80vga": dict(mode="320x200x16", out="T80VGA.DRV", edits=[tall("vga")], res=res640, res_sha=RES640_SHA),
        "t80vgaprof": dict(mode="320x200x16", out="T80VGAP.DRV", edits=[tall("vga"), prof.patch_staged],
                           res=res640, res_sha=RES640_SHA),
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
        if "res" in v:
            v["res"](repo, Path(resources))
            b88.baseline.RESOURCE_SHA = v["res_sha"]     # BUILD88 then asserts it
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
               "resource_sha256": result.get("resource_sha256"),
               "driver_bytes": len(data), "driver_sha256": hashlib.sha256(data).hexdigest(),
               "edits_staged_sha256": state["patched"],
               "build88_audits": "see RESULT.json (instruction, REP-prefix, link)", "runtime": "NOT_TESTED"}
    (out / "T80RES.JSON").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
