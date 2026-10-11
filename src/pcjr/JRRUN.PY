#!/usr/bin/env python3
"""Run the PCjr/TGA-II DOS probes headlessly in a supplied DOSBox build.

Usage:
  python3 src/pcjr/JRRUN.PY --emu <dosbox-x|dosbox> --exe <path-to-emulator>
      --machine <pcjr|tandy> --bin <dir with built .COM files>
      --out <new-dir> --cmd JRPROBE.COM [--cmd JRGUARD.COM ...]

Each --cmd runs in order inside one guest boot from a fresh output folder
(the folder must not exist). Every command's stdout is appended to OUT.TXT
followed by `<NAME> EXIT=<0|1>`. Guest files (JRPROBE.TXT, *.BIN, ...)
stay in the folder. Nothing is fetched; the emulator path is explicit.
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
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in a.cmd:
        shutil.copy2(Path(a.bin) / name, out / name)
    lines = ["[sdl]", "output=surface", "[dosbox]", f"machine={a.machine}",
             "[cpu]", "core=normal", "cycles=3000"]
    if a.emu == "dosbox-x":
        lines.append("cputype=8086_prefetch")
    lines += ["[autoexec]", f"mount c {out}", "c:"]
    for i, name in enumerate(a.cmd):
        stem = name.split(".")[0]
        lines += [f"{name} >> OUT.TXT",
                  f"IF ERRORLEVEL 1 GOTO F{i}",
                  f"echo {stem} EXIT=0 >> OUT.TXT", f"GOTO D{i}",
                  f":F{i}", f"echo {stem} EXIT=1 >> OUT.TXT", f":D{i}"]
    lines.append("exit")
    conf = out / "RUN.CONF"
    conf.write_text("\r\n".join(lines) + "\r\n")
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    args = [a.exe, "-conf", str(conf)]
    args += ["-nopromptfolder", "-nogui", "-nomenu"] if a.emu == "dosbox-x" else ["-noconsole"]
    with open(out / "HOST.LOG", "wb") as log:
        rc = subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT,
                            timeout=180).returncode
    print(f"JRRUN: emulator exit {rc}; guest output in {out / 'OUT.TXT'}")
    return 0 if (out / "OUT.TXT").exists() else 1


if __name__ == "__main__":
    sys.exit(main())
