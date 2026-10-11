#!/usr/bin/env python3
"""Build the PCjr / TGA-II DOS probes with the pinned MASM 5.10 toolchain.

Usage:
  python3 src/pcjr/BUILDCOM.PY --deps <DEPS.PY materialized inputs> \
      --dosbox <dosbox-x> --out <fresh-dir>

Assembles each source with BIN/MASM.EXE, links with BIN/LINK.EXE and
converts with DDK/TOOLS/EXE2BIN.EXE inside DOSBox-X, as RESERVE.PY does for
RESERVE.COM. Fails unless every module reports exactly 0 severe errors, no
LINK/EXE2BIN error appears and every .COM exists. BUILD.JSN records sizes
and SHA-256. The toolchain copies are removed from the output afterwards.
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

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ["src/pcjr/JRPROBE.ASM", "src/pcjr/JRGUARD.ASM", "src/pcjr/JRFREET.ASM",
           "src/pcjr/JRHOLDT.ASM", "src/tga2/T2PROBE.ASM"]
TOOLS = {"MASM.EXE": "BIN/MASM.EXE", "LINK.EXE": "BIN/LINK.EXE",
         "EXE2BIN.EXE": "DDK/TOOLS/EXE2BIN.EXE"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deps", type=Path, required=True)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    names = []
    for src in SOURCES:
        shutil.copyfile(ROOT / src, out / Path(src).name)
        names.append(Path(src).stem)
    for dst, rel in TOOLS.items():
        shutil.copyfile(a.deps / rel, out / dst)
    bat = "@ECHO OFF\r\n"
    for n in names:
        bat += (f"MASM {n}.ASM,{n}.OBJ,{n}.LST; >> BUILD.LOG\r\n"
                f"LINK {n}.OBJ,{n}.EXE,{n}.MAP; >> BUILD.LOG\r\n"
                f"EXE2BIN {n}.EXE {n}.COM >> BUILD.LOG\r\n")
    bat += "EXIT\r\n"
    (out / "BUILD.BAT").write_bytes(bat.encode("ascii"))
    conf = ("[sdl]\noutput=surface\n[dosbox]\nmachine=tandy\n[cpu]\ncore=normal\n"
            "cputype=8086_prefetch\ncycles=fixed 200000\n[mixer]\nnosound=true\n"
            f"[autoexec]\nmount c \"{out}\"\nc:\nBUILD.BAT\nexit\n")
    (out / "RUN.CONF").write_text(conf)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    with open(out / "HOST.LOG", "wb") as log:
        try:
            rc = subprocess.run([str(a.dosbox), "-nopromptfolder", "-nogui", "-nomenu", "-conf",
                                 str(out / "RUN.CONF")], env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=300).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    for dst in TOOLS:
        (out / dst).unlink()
    log = (out / "BUILD.LOG").read_text(errors="replace") if (out / "BUILD.LOG").exists() else ""
    severe = re.findall(r"(\d+)\s+Severe\s+Errors", log)
    problems = []
    if rc != 0:
        problems.append(f"emulator exit {rc}")
    if severe != ["0"] * len(names):
        problems.append(f"MASM severe-error counts {severe}, expected {len(names)} zeros")
    if re.search(r"error [AL]\d+|fatal error|cannot be converted|file not found", log, re.I):
        problems.append("LINK/EXE2BIN error in BUILD.LOG")
    built = {}
    for n in names:
        com = out / (n + ".COM")
        if not com.is_file() or com.stat().st_size == 0:
            problems.append(n + ".COM missing")
            continue
        data = com.read_bytes()
        built[n + ".COM"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    result = {"toolchain": "pinned MASM 5.10 / LINK / DDK EXE2BIN in DOSBox-X",
              "built": built, "verdict": "PASS" if not problems else "FAIL",
              "problems": problems}
    (out / "BUILD.JSN").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
