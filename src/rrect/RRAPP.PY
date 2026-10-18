#!/usr/bin/env python3
"""Build RRBENCH.EXE with the pinned Microsoft C 6 / LINK4 in DOSBox-X.

  python3 src/rrect/RRAPP.PY --repo <DEPS.PY display view> --dosbox <dosbox-x> --out <fresh dir>

The view supplies C:\\BIN, C:\\LIB and C:\\DDK\\286\\INC (WINDOWS.H); nothing
of it is copied. The sources are copied to <out> (mounted as D:), BUILD.BAT
runs there, and BUILD.LOG must show no compiler or linker error.
Writes <out>/RRAPP.JSN with the source and EXE hashes.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ("RRBENCH.C", "RRBENCH.DEF", "RRBENCH.RSP", "BUILD.BAT")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    out = a.out.resolve()
    if out.exists():
        raise SystemExit(f"RRAPP: {out} exists")
    out.mkdir(parents=True)
    for n in SOURCES:
        shutil.copyfile(HERE / n, out / n)
    cfg = out / "BUILD.CNF"
    cfg.write_text("[sdl]\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=16\n[cpu]\ncore=normal\n"
                   "cputype=8086_prefetch\ncycles=fixed 200000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\n"
                   f'mount C "{a.repo.resolve()}"\nmount D "{out}"\nD:\nBUILD.BAT\n')
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    subprocess.run([str(a.dosbox), "-nopromptfolder", "-conf", str(cfg)], env=env, timeout=300,
                   stdout=open(out / "host.log", "wb"), stderr=subprocess.STDOUT)
    log = (out / "BUILD.LOG").read_text(errors="replace") if (out / "BUILD.LOG").exists() else ""
    exe = out / "RRBENCH.EXE"
    if not exe.exists() or re.search(r"error [CLU]\d+|fatal error", log, re.I):
        print(log)
        raise SystemExit("RRAPP: build failed; see " + str(out / "BUILD.LOG"))
    res = {"sources_sha256": {n: sha(HERE / n) for n in SOURCES}, "exe": "RRBENCH.EXE",
           "exe_bytes": exe.stat().st_size, "exe_sha256": sha(exe),
           "warnings": re.findall(r"warning [CL]\d+[^\r\n]*", log)}
    (out / "RRAPP.JSN").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("exe_bytes", "exe_sha256", "warnings")}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
