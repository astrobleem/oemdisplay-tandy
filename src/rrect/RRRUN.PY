#!/usr/bin/env python3
"""Run RRBENCH on a prepared 86Box Tandy 1000 HX VM and collect its output.

  python3 src/xtpan/PCP86.PY prepare --target rrect --vm <new vm> --pristine <img> \\
      --drv <TR53216-variant.DRV> --drv-sha <sha> --tools <dir: RESERVE.COM MSTEST.COM RRBENCH.EXE>
  python3 src/rrect/RRRUN.PY --vm <vm> --box <86Box AppRun> --roms <rom dir> --out <new dir>

Test configuration made here, before the first start: SYSTEM.INI
shell=C:\\RRECT\\RRBENCH.EXE, so Windows runs only the probe (no Program
Manager or its message boxes over the drawing) and returns to DOS when the
probe ends. AUTOEXEC.BAT (from prepare) runs RESERVE and stays at the
prompt; this script types WIN /R. Polls C:\\RRBENCH.LOG with mtype until
COMPLETE=1, waits for the DOS prompt, stops 86Box and copies RRBENCH.LOG,
RBnn.BIN and TRnn.BIN to --out with RRRUN.JSN (hashes, timing, the VM's
PREP.JSN). Run it under src/xtpan/EMULOCK.PY. Exit 0 only on COMPLETE=1.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PCP86 = ROOT / "src" / "xtpan" / "PCP86.PY"
PART = "@@8704"


def mt(vm, *args, data=None):
    env = dict(os.environ, MTOOLS_SKIP_CHECK="1")
    r = subprocess.run([args[0], "-i", f"{vm / 'pcp.img'}{PART}", *args[1:]], env=env, input=data,
                       capture_output=True)
    return r


def log_lines(vm):
    r = mt(vm, "mtype", "::/RRBENCH.LOG")
    return r.stdout.decode("latin-1").replace("\r", "").split("\n") if r.returncode == 0 else []


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vm", type=Path, required=True)
    ap.add_argument("--box", required=True)
    ap.add_argument("--roms", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--display", default=":79")
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args(argv)
    vm, out = a.vm.resolve(), a.out.resolve()
    if out.exists():
        raise SystemExit(f"RRRUN: {out} exists")
    if (vm / "RRRUN.STARTED").exists():
        raise SystemExit("RRRUN: this VM was already used; prepare a fresh one")
    os.environ["DISPLAY"] = a.display
    ini = mt(vm, "mtype", "::/WINDOWS/SYSTEM.INI").stdout.decode("latin-1")
    shells = [l for l in ini.split("\r\n") if l.lower().startswith("shell=")]
    if len(shells) != 1:
        raise SystemExit("RRRUN: SYSTEM.INI has no single shell=")
    ini = ini.replace(shells[0] + "\r\n", "shell=C:\\RRECT\\RRBENCH.EXE\r\n")
    tmp = vm / "prep" / "SYSTEM.RR"
    tmp.write_bytes(ini.encode("latin-1"))
    if mt(vm, "mcopy", "-o", str(tmp), "::/WINDOWS/SYSTEM.INI").returncode:
        raise SystemExit("RRRUN: could not write SYSTEM.INI")
    (vm / "RRRUN.STARTED").write_text(time.strftime("%Y-%m-%dT%H:%M:%S") + "\n")
    subprocess.run([sys.executable, str(PCP86), "start", "--vm", str(vm), "--box", a.box, "--roms", a.roms,
                    "--display", a.display], check=True)
    sys.path.insert(0, str(PCP86.parent))
    import importlib.machinery
    box = importlib.machinery.SourceFileLoader("pcp86rr", str(PCP86)).load_module()
    res = {"vm": vm.name, "test_configuration": "SYSTEM.INI shell=C:\\RRECT\\RRBENCH.EXE (set by RRRUN)"}
    t_start = time.time()
    try:
        time.sleep(30)                                    # DOS boot, RESERVE
        box.focus()
        box.xdo("type", "--delay", 150, "WIN /R")
        box.xdo("key", "Return")
        t_win = time.time()
        done = False
        while time.time() - t_win < a.timeout:
            lines = log_lines(vm)
            if "COMPLETE=1" in lines:
                done = True
                break
            time.sleep(10)
        res["complete"] = done
        res["host_seconds_win_to_complete"] = round(time.time() - t_win, 1)
        time.sleep(45)                                    # Windows exits with its shell
    finally:
        subprocess.run([sys.executable, str(PCP86), "stop", "--vm", str(vm)])
    out.mkdir(parents=True)
    listing = mt(vm, "mdir", "-b", "::/").stdout.decode("latin-1").split()
    got = {}
    for name in sorted(n.split("/")[-1].upper() for n in listing):
        if name == "RRBENCH.LOG" or re.fullmatch(r"(RB|TR)\d\d\.BIN", name):
            mt(vm, "mcopy", "-o", "::/" + name, str(out / name))
            got[name] = hashlib.sha256((out / name).read_bytes()).hexdigest()
    res["files"] = got
    res["prep"] = json.loads((vm / "PREP.JSN").read_text())
    res["prep"].pop("86box_cfg", None)
    (out / "RRRUN.JSN").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({"complete": res["complete"], "files": len(got)}))
    return 0 if res["complete"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
