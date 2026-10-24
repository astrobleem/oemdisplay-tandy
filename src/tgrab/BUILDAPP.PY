#!/usr/bin/env python3
"""Build TGCLIP.EXE (Clipboard bitmap helper) with the
pinned DOS toolchain (CL /G0 /Gw /AS, LINK4), as examples/MAZE does.

  python3 src/tgrab/BUILDAPP.PY --repo <DEPS.PY view or inputs with BIN, LIB,
      INCLUDE, DDK> --dosbox <dosbox-x> --out <fresh-dir>
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ("TGCLIP.C", "TGCLIP.DEF", "TGCLIP.RSP", "TGCLOG.C", "TGCLOG.DEF", "TGCLOG.RSP", "TGSETUP.C", "BUILDW.BAT")
PRODUCTS = ("TGCLIP.EXE", "TGSETUP.EXE", "TGCLOG.EXE")
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
BUILDW.BAT
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    if out.exists():
        ap.error("--out must be new")
    for n in ("BIN/CL.EXE", "BIN/LINK4.EXE", "BIN/LINK.EXE", "LIB/SLIBCEW.LIB", "LIB/LIBW.LIB", "LIB/SLIBCE.LIB"):
        if not (repo / n).is_file():
            ap.error("missing toolchain input: " + n)
    out.mkdir(parents=True)
    for n in FILES:
        data = (HERE / n).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        (out / n).write_bytes(data)
    (out / "BUILD.CNF").write_text(CONF.format(repo=repo, out=out))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    passed = False
    with (out / "HOST.LOG").open("wb") as log:
        proc = subprocess.Popen([str(a.dosbox.resolve()), "-nopromptfolder", "-conf", str(out / "BUILD.CNF")],
                                stdout=log, stderr=subprocess.STDOUT, env=env)
        deadline = time.monotonic() + 240
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
    if not passed:
        print((out / "BUILD.LOG").read_text(errors="replace") if (out / "BUILD.LOG").exists() else "no BUILD.LOG")
        raise SystemExit("BUILDAPP: build failed; inspect BUILD.LOG and HOST.LOG")
    res = {}
    for n in PRODUCTS:
        b = (out / n).read_bytes()
        res[n] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    res["compiler_flags"] = {"TGCLIP.EXE": "/G0 /Gw /AS /W3 /Od, LINK4", "TGCLOG.EXE": "/G0 /Gw /AS /W3 /Od, LINK4 (test tool)", "TGSETUP.EXE": "/c /AS /G0 /W3 /Ox, LINK SLIBCE (DOS)"}
    res["target"] = "Windows 3.0 real mode / DOS, 8086"
    (out / "RESULT.JSON").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
