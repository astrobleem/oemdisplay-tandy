#!/usr/bin/env python3
"""JRMODE self-test in plain DOS on the emulated PCjr (no Windows).

  python3 src/pcjr/INSTALL/JRMODET.PY --tools <dir with JRMODE.COM> --out <new dir>

For every PCjr BIOS mode m (0 1 2 3 4 5 6 8 9 A) runs 'JRMODE m' (nothing
may change: 'MODE m OK') and 'JRMODE m X' (JRMODE changes one cell itself
after its snapshot: it must report 'MODE m BAD 0001'). This shows JRMODE's
check detects a disturbance in each mode before JRGRTEST relies on it.
Results: <out>/RESULT.JSN. Exit 0 only if all 20 results are as required.
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
J = importlib.machinery.SourceFileLoader("jrdbx", str(HERE / "JRDBX.PY")).load_module()
G = importlib.machinery.SourceFileLoader("jrgrtest", str(HERE / "JRGRTEST.PY")).load_module()


def judge(m, fault, text):
    w = (text or "").split()
    tail_ok = len(w) == 3 + (1 if fault else 0) or (len(w) >= 4 + (1 if fault else 0) and w[-2] == "READ")
    if fault:
        return w[:4] == ["MODE", m, "BAD", "0001"] and tail_ok
    return w[:3] == ["MODE", m, "OK"] and tail_ok


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tools", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    run = a.out.resolve()
    if run.exists():
        raise SystemExit(f"JRMODET: {run} exists")
    (run / "C").mkdir(parents=True)
    shutil.copyfile(a.tools / "JRMODE.COM", run / "C" / "JRMODE.COM")
    res = {**G.S.source_state(),
           "jrmode_sha256": hashlib.sha256((a.tools / "JRMODE.COM").read_bytes()).hexdigest(), "results": {}}
    J.start(run, 1200)
    try:
        for m in G.MODES:
            for fault in (False, True):
                J.text(f"JRMODE {m}{' X' if fault else ''}")
                J.key("Return", wait=8)
                J.key("space", wait=4)
                J.text(f"COPY JRMODE{m}.TXT R{m}{'X' if fault else 'N'}.TXT")
                J.key("Return", wait=2)
    finally:
        J.stop(run)
    ok = True
    for m in G.MODES:
        for fault in (False, True):
            f = run / "C" / f"R{m}{'X' if fault else 'N'}.TXT"
            text = f.read_text(errors="replace").strip() if f.exists() else None
            good = judge(m, fault, text)
            ok = ok and good
            res["results"][f"{m}{' X' if fault else ''}"] = {"file": text, "as_required": good}
    res["verdict"] = "PASS" if ok else "FAIL"
    (run / "RESULT.JSN").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({"verdict": res["verdict"]}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
