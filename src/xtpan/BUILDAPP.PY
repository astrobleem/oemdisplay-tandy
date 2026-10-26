#!/usr/bin/env python3
"""Build XTPAN.EXE (panning helper) and PANTEST.EXE (test fixture) with the
pinned DOS toolchain (CL /G0 /Gw /AS, LINK4), as examples/MAZE does.

  python3 src/xtpan/BUILDAPP.PY --repo <DEPS.PY view or inputs with BIN, LIB,
      INCLUDE, DDK> --dosbox <dosbox-x> --out <fresh-dir>
"""
import argparse
import hashlib
import importlib.machinery
import json
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ("XTPAN.C", "XTPAN.DEF", "XTPAN.RSP", "PANTEST.C", "PANTEST.DEF", "PANTEST.RSP", "BUILD.BAT")
PANUI_FILES = ("PANSET.C", "PANSET.H", "PANDLG.C", "PANDLG.H")
CONF = """[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=1
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
[dos]
xms=false
ems=false
umb=false
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--placement", type=Path, default=HERE.parent / "wdesk/PLACE",
                    help="explicit libwintandy/libtandywin/PLACE source directory")
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    if out.exists():
        ap.error("--out must be new")
    for n in ("BIN/CL.EXE", "BIN/LINK4.EXE", "LIB/SLIBCEW.LIB", "LIB/LIBW.LIB"):
        if not (repo / n).is_file():
            ap.error("missing toolchain input: " + n)
    for n in ("WTPLACE.C", "WTPLACE.H"):
        if not (a.placement / n).is_file():
            ap.error("missing placement source: " + n)
    out.mkdir(parents=True)
    for n in FILES:
        data = (HERE / n).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        (out / n).write_bytes(data)
    for n in PANUI_FILES:
        data = (HERE.parent / "panui" / n).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        (out / n).write_bytes(data)
    for n in ("WDCORE.C", "WDCORE.H", "WDWIN.C", "WDWIN.H"):
        shutil.copyfile(HERE.parent / "wdesk" / n, out / n)
    for n in ("WTPLACE.C", "WTPLACE.H"):
        shutil.copyfile(a.placement / n, out / n)
    (out / "BUILD.CNF").write_text(CONF.format(repo=repo, out=out))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    module = importlib.machinery.SourceFileLoader(
        'xt_run', str(HERE.parent / 'softpan' / 'WINRUN.PY')).load_module()
    runner = module.Runner(out / 'LEASE.JSON')
    with runner.lease():
        runner.run([a.dosbox.resolve(), '-nopromptfolder', '-conf', out / 'BUILD.CNF'],
                   env, out / 'HOST.LOG', timeout=240)
    text = (out / "BUILD.LOG").read_text(errors="replace") if (out / "BUILD.LOG").exists() else ""
    if "PASS" not in text or "FAIL" in text or "error " in text.lower():
        print((out / "BUILD.LOG").read_text(errors="replace") if (out / "BUILD.LOG").exists() else "no BUILD.LOG")
        raise SystemExit("BUILDAPP: build failed; inspect BUILD.LOG and HOST.LOG")
    res = {}
    for n in ("XTPAN.EXE", "PANTEST.EXE"):
        b = (out / n).read_bytes()
        res[n] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    res["compiler_flags"] = "/nologo /c /G0 /Gw /AS /W3 /Od"
    res["target"] = "Windows 3.0 real mode, 8086"
    (out / "RESULT.JSON").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
