#!/usr/bin/env python3
"""Run the PCjr/TGA-II DOS probes headlessly in a supplied DOSBox build.

Usage:
  python3 src/pcjr/JRRUN.PY --emu <dosbox-x|dosbox> --exe <path-to-emulator>
      --machine <pcjr|tandy> --bin <dir with built .COM files>
      --out <new-dir> --cmd JRPROBE.COM [--cmd "JRPROBE.COM /C" ...]

Each --cmd runs in order inside one guest boot from a fresh output folder
(the folder must not exist). Every command's stdout is appended to OUT.TXT
followed by `<NAME> EXIT=<0|1|2|3+>`. --expect NAME=CODE sets the expected
exit code (default 0 for every command; NAME is the stem, e.g. JRGUARD=1).
JRRUN exits 0 only if the emulator exited 0 and every command reported
exactly its expected code; missing or extra results fail. RESULT.JSN
records what happened. Nothing is fetched; the emulator path is explicit.
The CPU core is normal; DOSBox-X also gets cputype=8086_prefetch. This is
emulator evidence only, not a physical PCjr/SL/TL result.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emu", choices=["dosbox", "dosbox-x"], required=True)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--machine", choices=["pcjr", "tandy"], required=True)
    ap.add_argument("--bin", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cmd", action="append", required=True)
    ap.add_argument("--expect", action="append", default=[])
    a = ap.parse_args()
    expect = {c.split()[0].split(".")[0].upper(): "0" for c in a.cmd}
    for item in a.expect:
        name, _, code = item.partition("=")
        if name.upper() not in expect or code not in ("0", "1", "2", "3+"):
            ap.error("bad --expect " + item)
        expect[name.upper()] = code
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in {c.split()[0] for c in a.cmd}:
        shutil.copy2(Path(a.bin) / name, out / name)
    lines = ["[sdl]", "output=surface", "[dosbox]", f"machine={a.machine}",
             "[cpu]", "core=normal", "cycles=3000"]
    if a.emu == "dosbox-x":
        lines.append("cputype=8086_prefetch")
    lines += ["[autoexec]", f"mount c {out}", "c:"]
    for i, name in enumerate(a.cmd):
        stem = name.split()[0].split(".")[0]
        lines += [f"{name} >> OUT.TXT",
                  f"IF ERRORLEVEL 3 GOTO T{i}", f"IF ERRORLEVEL 2 GOTO W{i}",
                  f"IF ERRORLEVEL 1 GOTO F{i}",
                  f"echo {stem} EXIT=0 >> OUT.TXT", f"GOTO D{i}",
                  f":T{i}", f"echo {stem} EXIT=3+ >> OUT.TXT", f"GOTO D{i}",
                  f":W{i}", f"echo {stem} EXIT=2 >> OUT.TXT", f"GOTO D{i}",
                  f":F{i}", f"echo {stem} EXIT=1 >> OUT.TXT", f":D{i}"]
    lines.append("exit")
    conf = out / "RUN.CONF"
    conf.write_text("\r\n".join(lines) + "\r\n")
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    args = [a.exe, "-conf", str(conf)]
    args += ["-nopromptfolder", "-nogui", "-nomenu"] if a.emu == "dosbox-x" else ["-noconsole"]
    with open(out / "HOST.LOG", "wb") as log:
        try:
            rc = subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT,
                                timeout=180).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    import json, re
    text = (out / "OUT.TXT").read_text(errors="replace") if (out / "OUT.TXT").exists() else ""
    got = {}
    for m in re.finditer(r"^(\w+) EXIT=(0|1|2|3\+)\s*$", text, re.M):
        got.setdefault(m.group(1).upper(), []).append(m.group(2))
    problems = []
    if rc != 0:
        problems.append(f"emulator exit {rc}")
    for name, code in expect.items():
        seen = got.get(name, [])
        if seen != [code]:
            problems.append(f"{name}: expected EXIT={code}, saw {seen or 'nothing'}")
    for name in got:
        if name not in expect:
            problems.append(f"unexpected result line for {name}")
    result = {"emulator_exit": rc, "expected": expect, "observed": got,
              "verdict": "PASS" if not problems else "FAIL", "problems": problems}
    (out / "RESULT.JSN").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
