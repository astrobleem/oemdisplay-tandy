#!/usr/bin/env python3
"""Build Windows 3.0 test/helper programs of src/text80 (and src/xtpan) with the
pinned DOS toolchain (CL /G0 /Gw /AS /W3 /Od, LINK4), under DOSBox-X.

  python3 src/text80/BUILDAPP.PY --repo <toolchain view: BIN, LIB, INCLUDE, DDK>
      --dosbox <dosbox-x> --out <fresh dir> --app TPROF [--app T80HELP ...]

Each NAME needs NAME.C, NAME.DEF and NAME.RSP in src/text80 (or src/xtpan).
Results: <out>/NAME.EXE and <out>/RESULT.JSON (bytes and SHA-256 of each).
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEARCH = (HERE, HERE.parent / "xtpan")
FLAGS = "/nologo /c /G0 /Gw /AS /W3 /Od"
CONF = """[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=16
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
[mixer]
nosound=true
[midi]
mididevice=none
[autoexec]
@echo off
mount C "{repo}"
mount D "{out}"
D:
BUILD.BAT
"""


def find(name):
    for d in SEARCH:
        if (d / name).is_file():
            return d / name
    raise SystemExit("BUILDAPP: missing " + name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--app", action="append", required=True)
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    if out.exists():
        ap.error("--out must be new")
    for n in ("BIN/CL.EXE", "BIN/LINK4.EXE", "LIB/SLIBCEW.LIB", "LIB/LIBW.LIB"):
        if not (repo / n).is_file():
            ap.error("missing toolchain input: " + n)
    out.mkdir(parents=True)
    bat = ["@ECHO OFF", "PATH=C:\\BIN", "SET INCLUDE=C:\\DDK\\286\\INC;C:\\INCLUDE", "SET LIB=C:\\LIB",
           "ECHO START > BUILD.LOG"]
    for app in a.app:
        for ext in (".C", ".DEF", ".RSP"):
            data = find(app + ext).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            (out / (app + ext)).write_bytes(data)
        bat += [f"CL {FLAGS} {app}.C >> BUILD.LOG", "IF ERRORLEVEL 1 GOTO FAIL",
                f"LINK4 /NOE /NOD @{app}.RSP >> BUILD.LOG", "IF ERRORLEVEL 1 GOTO FAIL"]
    bat += ["ECHO PASS >> BUILD.LOG", "GOTO END", ":FAIL", "ECHO FAIL >> BUILD.LOG", ":END", "EXIT"]
    (out / "BUILD.BAT").write_bytes(("\r\n".join(bat) + "\r\n").encode())
    (out / "BUILD.CNF").write_text(CONF.format(repo=repo, out=out))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    passed = False
    with (out / "HOST.LOG").open("wb") as log:
        proc = subprocess.Popen([str(a.dosbox.resolve()), "-nopromptfolder", "-conf", str(out / "BUILD.CNF")],
                                stdout=log, stderr=subprocess.STDOUT, env=env)
        deadline = time.monotonic() + 300
        try:
            while time.monotonic() < deadline:
                text = (out / "BUILD.LOG").read_text(errors="replace") if (out / "BUILD.LOG").exists() else ""
                if "PASS" in text:
                    passed = True
                    break
                if "FAIL" in text or proc.poll() is not None:
                    break
                time.sleep(0.2)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
    log = (out / "BUILD.LOG").read_text(errors="replace") if (out / "BUILD.LOG").exists() else "no BUILD.LOG"
    if not passed:
        print(log)
        raise SystemExit("BUILDAPP: build failed; inspect BUILD.LOG and HOST.LOG")
    res = {"compiler_flags": FLAGS, "target": "Windows 3.0 real mode, 8086",
           "warnings": [ln.strip() for ln in log.splitlines() if "warning" in ln.lower()]}
    for app in a.app:
        b = (out / (app + ".EXE")).read_bytes()
        res[app + ".EXE"] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    (out / "RESULT.JSON").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
