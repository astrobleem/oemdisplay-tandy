#!/usr/bin/env python3
"""Collect the fill-row batching evidence into docs/rrbatch (no binaries).

  python3 src/rrect/RRBEVID.PY --work <dir with out5_*, e_*, b_candidate, b0> --docs docs/rrbatch

Baseline is PR #151's candidate driver (b_candidate); the unchanged TR5
driver (b0) is the exactness reference. Copies each run's RRBENCH.LOG and
RRRUN.JSN (SHA-256 of every RBnn/RVnn frame dump and TRnn trace; the dumps
are not committed); RRBUILD.JSN per build; RRCMP of TR5 vs #151 and vs the
batch driver, #151 vs batch, batch-trace and every mutant (JSON, text,
difference PNGs); RRTRACE of the batch-trace run; the 86Box screenshots
under 8.3 names, a #151/batch Calculator montage and a decoded contact sheet
of the batch run's 14 per-call frames. Never copies a driver, a Microsoft
binary or a disk image.
"""
import argparse
import hashlib
import importlib.machinery
import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = importlib.machinery.SourceFileLoader("rrcmp", str(HERE / "RRCMP.PY")).load_module()
T = importlib.machinery.SourceFileLoader("rrtrace", str(HERE / "RRTRACE.PY")).load_module()

RUNS = {"tr5": "TR5", "cand": "CAND", "batch": "BATCH", "batch-trace": "BTR", "mut-noend": "MNOEND",
        "mut-short": "MSHORT", "mut-early": "MEARLY", "shots_cand": "SHOTCAND", "shots_batch": "SHOTBAT"}
BUILDS = {"b0": "TR5", "b_candidate": "CAND", "e_batch": "BATCH", "e_batch-trace": "BTR",
          "e_mut-noend": "MNOEND", "e_mut-short": "MSHORT", "e_mut-early": "MEARLY"}
# (reference, candidate, tag, expect equal)
PAIRS = (("tr5", "cand", "TR5C", True), ("tr5", "batch", "TR5B", True), ("cand", "batch", "BATCH", True),
         ("cand", "batch-trace", "BTR", True), ("shots_cand", "shots_batch", "SHOT", True),
         ("cand", "mut-noend", "MNOEND", False), ("cand", "mut-short", "MSHORT", False),
         ("cand", "mut-early", "MEARLY", False))
SHOTS = ("CALC_004", "CALC_012", "CALC_END", "REVER_END", "PBRUS_END")


def short(name):
    return name.replace("CALC_", "C").replace("_END", "E").replace("REVER", "REV").replace("PBRUS", "PBR")


def build_summary(w, b):
    if (w / b / "RRBUILD.JSN").exists():
        return json.loads((w / b / "RRBUILD.JSN").read_text())
    res = json.loads((w / b / "RESULT.json").read_text())               # TR5: BUILD88.PY run directly
    data = (w / b / "TANDY88.DRV").read_bytes()
    return {"variant": "baseline (BUILD88.PY, no RRPATCH edits)", "mode": "320x200x16", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "build88": {k: res[k] for k in ("build", "instruction_audit", "rep_prefix_audit", "link_audit",
                                             "resource_sha256") if k in res}}


def segments(w, b):
    out = {}
    for line in (w / b / "renderer" / "EGA" / "TSOFT.MAP").read_text(errors="replace").splitlines():
        p = line.split()
        if len(p) == 4 and p[2] in ("_TEXT", "_DATA") and p[3] in ("CODE", "DATA"):
            out[p[2]] = int(p[1].rstrip("H"), 16)
    return out


def montage(w, docs, ms):
    from PIL import Image, ImageDraw
    W, H, pad, top = 320, 200, 8, 22
    cols = ("CALC_004", "CALC_012", "CALC_END")
    im = Image.new("RGB", (len(cols) * (W + pad) + 80, 2 * (H + top) + pad), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for r, (run, label) in enumerate((("shots_cand", "#151"), ("shots_batch", "batch"))):
        y = r * (H + top + pad)
        d.text((4, y + top + H // 2), label, fill=(0, 0, 0))
        for c, n in enumerate(cols):
            x = 80 + c * (W + pad)
            cap = (f"finished; first repaint took {ms[run] / 1000:.1f} s" if n == "CALC_END"
                   else f"{int(n[-3:])} s after the repaint starts")
            if n != "CALC_END" and int(n[-3:]) * 1000 > ms[run]:
                # The first repaint had already finished; this capture shows the second one.
                d.text((x, y + 6), cap + f": first repaint done at {ms[run] / 1000:.1f} s", fill=(0, 0, 0))
                d.rectangle((x, y + top, x + W - 1, y + top + H - 1), outline=(160, 160, 160))
                continue
            d.text((x, y + 6), cap, fill=(0, 0, 0))
            im.paste(Image.open(w / f"out5_{run}" / "SHOTS" / f"{n}.png").convert("RGB"), (x, y + top))
    im.save(docs / "TIMELINE.PNG")


def steps_sheet(w, docs, run, count):
    """Decoded B800h frames after each visible_steps call (VRAM dumps, not 86Box captures)."""
    from PIL import Image, ImageDraw
    W, H, pad, top, per = 320, 200, 6, 16, 7
    rows = (count + per - 1) // per
    im = Image.new("RGB", (per * (W + pad), rows * (H + top + pad)), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for k in range(1, count + 1):
        px = C.pixels((w / f"out5_{run}" / f"RV{k:02d}.BIN").read_bytes())
        one = Image.new("RGB", (W, H))
        one.putdata([C.IRGB[c] for c in px])
        x, y = ((k - 1) % per) * (W + pad), ((k - 1) // per) * (H + top + pad)
        d.text((x, y + 2), f"after call {k}", fill=(0, 0, 0))
        im.paste(one, (x, y + top))
    im.save(docs / "STEPS.PNG")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--docs", type=Path, required=True)
    a = ap.parse_args(argv)
    w, docs = a.work.resolve(), a.docs.resolve()
    docs.mkdir(parents=True, exist_ok=True)
    for run, tag in RUNS.items():
        dst = docs / tag
        dst.mkdir(exist_ok=True)
        for f in ("RRBENCH.LOG", "RRRUN.JSN"):
            shutil.copyfile(w / f"out5_{run}" / f, dst / f)
    for b, tag in BUILDS.items():
        (docs / f"B_{tag}.JSN").write_text(json.dumps(build_summary(w, b), indent=1) + "\n")
    cost = {"320x200x16": {"cand": {"bytes": build_summary(w, "b_candidate")["bytes"], **segments(w, "b_candidate")},
                           "batch": {"bytes": build_summary(w, "e_batch")["bytes"], **segments(w, "e_batch")}}}
    for m in ("640x200x4", "160x200x16", "320x200x4", "640x200x2"):
        cost[m] = {"cand": json.loads((w / f"bm_{m}_candidate" / "RRBUILD.JSN").read_text())["bytes"],
                   "batch": json.loads((w / f"em_{m}_batch" / "RRBUILD.JSN").read_text())["bytes"]}
    (docs / "COST.JSN").write_text(json.dumps(cost, indent=1) + "\n")
    results = {}
    for ref, cand, tag, want in PAIRS:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = C.main([str(w / f"out5_{ref}"), str(w / f"out5_{cand}"), "--json", str(docs / f"C_{tag}.JSN")]
                        + ([] if want else ["--png", str(docs / f"D_{tag}")]))
        (docs / f"C_{tag}.TXT").write_text(buf.getvalue())
        results[tag] = {"exit": rc, "expected": 0 if want else 1}
    buf = io.StringIO()
    with redirect_stdout(buf):
        T.main([str(w / "out5_batch-trace")])
    (docs / "TR_BATCH.TXT").write_text(buf.getvalue())
    shots = docs / "SHOTS"
    shots.mkdir(exist_ok=True)
    for run, tag in (("shots_cand", "C"), ("shots_batch", "B")):
        for n in SHOTS:
            shutil.copyfile(w / f"out5_{run}" / "SHOTS" / f"{n}.png", shots / f"{tag}{short(n)}.PNG")
    from PIL import Image
    same = {n: Image.open(shots / f"C{short(n)}.PNG").convert("RGB").tobytes()
            == Image.open(shots / f"B{short(n)}.PNG").convert("RGB").tobytes() for n in SHOTS if n.endswith("END")}
    ms = {r: [v for v in C.stages((w / f"out5_{r}" / "RRBENCH.LOG").read_text()).values()
              if v.get("name") == "calc"][0]["repaint_ms"][0] for r in ("shots_cand", "shots_batch")}
    montage(w, docs, ms)
    steps_sheet(w, docs, "batch", 14)
    summary = {"rrcmp": results, "final_screenshots_identical": same}
    (docs / "SUMMARY.JSN").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary))
    ok = all(r["exit"] == r["expected"] for r in results.values()) and all(same.values())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
