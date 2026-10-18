#!/usr/bin/env python3
"""Collect RoundRect investigation evidence into docs/rrect (no binaries).

  python3 src/rrect/RREVID.PY --work <dir with out3_*, b*, app3> --docs docs/rrect

Copies, per run, RRBENCH.LOG and RRRUN.JSN (which holds the SHA-256 of every
RBnn.BIN frame dump and TRnn.BIN trace; the dumps themselves are not
committed); RRBUILD.JSN per driver build (hashes and audits; no .DRV);
reruns RRCMP for base vs every other run (JSON + difference PNGs) and
RRTRACE for the trace runs; copies the 86Box screenshots under 8.3 names
and builds a baseline/candidate Calculator timeline montage. Never copies a
driver, a Microsoft binary or a disk image.
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

RUNS = {"base": "BASE", "candidate": "CAND", "mut-lastrow": "MLAST", "mut-firstrow": "MFIRST",
        "mut-scanskip": "MSCAN", "candidate-trace": "CANDTR", "shots_base": "SHOTBASE",
        "shots_candidate": "SHOTCAND"}
BUILDS = {"b0": "BASE", "b_candidate": "CAND", "b_candidate-trace": "CANDTR", "b_mut-lastrow": "MLAST",
          "b_mut-firstrow": "MFIRST", "b_mut-scanskip": "MSCAN", "b_trace": "TRACE",
          "b_noflush": "NOFL", "b_nodraw": "NODRAW"}
ABLATIONS = {"out_base": "A_BASE", "out_trace": "A_TRACE", "out_noflush": "A_NOFL", "out_nodraw": "A_NODRW"}
SHOTS = ("CALC_004", "CALC_012", "CALC_030", "CALC_060", "CALC_095", "CALC_END", "REVER_END", "PBRUS_END")


def short(name):
    return name.replace("CALC_", "C").replace("_END", "E").replace("REVER", "REV").replace("PBRUS", "PBR")


def montage(work, docs, cand_ms):
    """Calculator's first timed repaint, captured at fixed host times. The
    candidate finishes that repaint before the 30 s capture (and then starts
    the second and third), so its later cells say when it finished."""
    from PIL import Image, ImageDraw
    cols = ("CALC_004", "CALC_012", "CALC_030", "CALC_060", "CALC_095", "CALC_END")
    W, H, pad, top = 320, 200, 8, 22
    im = Image.new("RGB", (len(cols) * (W + pad) + 80, 2 * (H + top) + pad), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for r, (run, label) in enumerate((("shots_base", "unchanged"), ("shots_candidate", "candidate"))):
        y = r * (H + top + pad)
        d.text((4, y + top + H // 2), label, fill=(0, 0, 0))
        for c, n in enumerate(cols):
            x = 80 + c * (W + pad)
            src = n
            if n == "CALC_END":
                cap = "finished (after three repaints)"
            else:
                cap = f"{int(n[-3:])} s after the repaint starts"
                if run == "shots_candidate" and int(n[-3:]) * 1000 > cand_ms:
                    src, cap = None, cap + f": done at {cand_ms / 1000:.1f} s"
            d.text((x, y + 6), cap, fill=(0, 0, 0))
            if src:
                im.paste(Image.open(work / f"out3_{run}" / "SHOTS" / f"{src}.png").convert("RGB"), (x, y + top))
            else:
                d.rectangle((x, y + top, x + W - 1, y + top + H - 1), outline=(160, 160, 160))
    im.save(docs / "TIMELINE.PNG")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--docs", type=Path, required=True)
    a = ap.parse_args(argv)
    w, docs = a.work.resolve(), a.docs.resolve()
    docs.mkdir(parents=True, exist_ok=True)
    for run, tag in {**{f"out3_{k}": v for k, v in RUNS.items()}, **ABLATIONS}.items():
        dst = docs / tag
        dst.mkdir(exist_ok=True)
        for f in ("RRBENCH.LOG", "RRRUN.JSN"):
            shutil.copyfile(w / run / f, dst / f)
    for b, tag in BUILDS.items():
        if (w / b / "RRBUILD.JSN").exists():
            shutil.copyfile(w / b / "RRBUILD.JSN", docs / f"B_{tag}.JSN")
            continue
        res = json.loads((w / b / "RESULT.json").read_text())           # baseline: BUILD88.PY run directly
        data = (w / b / "TANDY88.DRV").read_bytes()
        s = {"variant": "baseline (BUILD88.PY, no RRPATCH edits)", "mode": "320x200x16", "bytes": len(data),
             "sha256": hashlib.sha256(data).hexdigest(),
             "build88": {k: res[k] for k in ("build", "instruction_audit", "rep_prefix_audit", "link_audit",
                                              "resource_sha256") if k in res}}
        (docs / f"B_{tag}.JSN").write_text(json.dumps(s, indent=1) + "\n")
    sizes = {}
    for m in ("640x200x4", "160x200x16", "320x200x4", "640x200x2"):
        sizes[m] = {v: json.loads((w / f"bm_{m}_{v}" / "RRBUILD.JSN").read_text())
                    for v in ("baseline", "candidate")}
    (docs / "PROFILES.JSN").write_text(json.dumps(
        {m: {v: {k: s[k] for k in ("bytes", "sha256", "staged_tsoft_after_sha256")} for v, s in r.items()}
         for m, r in sizes.items()}, indent=1) + "\n")
    results = {}
    for run, tag in RUNS.items():
        if run == "base" or run.startswith("shots"):
            continue
        png = docs / f"D_{tag}"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = C.main([str(w / "out3_base"), str(w / f"out3_{run}"), "--json", str(docs / f"C_{tag}.JSN")]
                        + (["--png", str(png)] if run.startswith("mut") else []))
        (docs / f"C_{tag}.TXT").write_text(buf.getvalue())
        results[run] = rc
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = C.main([str(w / "out_base"), str(w / "out_trace")])
    (docs / "C_TRACE.TXT").write_text(buf.getvalue())
    results["v1 trace"] = rc
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = C.main([str(w / "out3_shots_base"), str(w / "out3_shots_candidate"), "--json", str(docs / "C_SHOT.JSN")])
    (docs / "C_SHOT.TXT").write_text(buf.getvalue())
    results["screenshot runs"] = rc
    for run, tag in (("out_trace", "TR_BASE"), ("out3_candidate-trace", "TR_CAND")):
        buf = io.StringIO()
        with redirect_stdout(buf):
            T.main([str(w / run)])
        (docs / f"{tag}.TXT").write_text(buf.getvalue())
    shots = docs / "SHOTS"
    shots.mkdir(exist_ok=True)
    for run, tag in (("shots_base", "B"), ("shots_candidate", "C")):
        for n in SHOTS:
            shutil.copyfile(w / f"out3_{run}" / "SHOTS" / f"{n}.png", shots / f"{tag}{short(n)}.PNG")
    from PIL import Image
    same = {n: Image.open(shots / f"B{short(n)}.PNG").convert("RGB").tobytes()
            == Image.open(shots / f"C{short(n)}.PNG").convert("RGB").tobytes() for n in SHOTS if n.endswith("END")}
    cms = C.stages((w / "out3_shots_candidate" / "RRBENCH.LOG").read_text())
    cms = [v for v in cms.values() if v.get("name") == "calc"][0]["repaint_ms"][0]
    montage(w, docs, cms)
    summary = {"rrcmp_exit_codes_vs_base": results, "final_screenshots_identical": same}
    (docs / "SUMMARY.JSN").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary))
    ok = (results["candidate"] == 0 and results["candidate-trace"] == 0 and results["v1 trace"] == 0
          and results["screenshot runs"] == 0
          and all(results[m] == 1 for m in results if m.startswith("mut")) and all(same.values()))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
