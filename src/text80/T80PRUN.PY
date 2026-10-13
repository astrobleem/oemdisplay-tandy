#!/usr/bin/env python3
"""Profiling session for the text-mode drivers in 86Box (no pass/fail checks).

  python3 src/text80/T80PRUN.PY --vm <prepared, started VM at the DOS prompt>
      --dir T40 [--chars 30] [--note "Hello TV owners 40x25"]

Starts Windows 3.0, then through Program Manager's Run dialog:
  1. TPROF TYPE <chars>: per-character driver counters (or wall time only on
     a driver without escape 5450h);
  2. TPROF NOTE 60 <secs>: Notepad started by TPROF; once TPROF logs READY,
     the note text is typed with real keys (xdotool, the emulated keyboard);
     TPROF reads the counters after <secs>.
Captures: desktop, after TYPE, Notepad with the typed line. The guest log
C:\<dir>\TPROF.LOG is copied to <vm>/TPROF.LOG; T80PROFX.PY reports it.
"""
import argparse
import importlib.machinery
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PCPWIN = importlib.machinery.SourceFileLoader("pcpwin", str(HERE.parent / "pcp" / "PCPWIN.PY")).load_module()
PART = "@@8704"


class Run:
    def __init__(self, vm, tdir):
        self.vm = Path(vm)
        self.tdir = tdir
        self.r = PCPWIN.Run(vm, None, None, width=320, target="pcp")
        self.r.tdir, self.r.tid = tdir, "T40ID"
        self.events = []

    def log(self):
        p = subprocess.run(["mtype", "-i", f"{self.vm / 'pcp.img'}{PART}", f"::/{self.tdir}/TPROF.LOG"],
                           capture_output=True)
        return [ln for ln in p.stdout.decode("latin-1").replace("\r", "").split("\n") if ln]

    def wait(self, prefix, start, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            for ln in self.log()[start:]:
                if ln.startswith(prefix):
                    self.events.append({"line": ln, "after_s": round(time.time() - t0, 1)})
                    return ln
            time.sleep(5)
        self.events.append({"timeout": prefix, "after_s": timeout})
        return None

    def runcmd(self, cmd):
        r = self.r
        r.key("alt+f", wait=8)
        r.key("r", wait=15)
        r.text(cmd)
        r.key("Return", wait=5)

    def session(self, chars, note, secs):
        r = self.r
        r.text("CD \\WINDOWS")
        r.key("Return", wait=2)
        r.m("ident", "on")
        r.text("WIN /R")
        r.key("Return", wait=150)
        r.m("ident", "off")
        for _ in range(6):
            r.key("Escape", wait=12)
        r.home()
        time.sleep(60)
        r.shot("desktop", settle=1, decode=False)
        n = len(self.log())
        t0 = time.time()
        self.runcmd(f"C:\\{self.tdir}\\TPROF TYPE {chars}")
        self.wait("TYPE n=", n, 3600)
        self.events.append({"type_wall_s": round(time.time() - t0, 1)})
        r.shot("aftertype", settle=1, decode=False)
        time.sleep(30)
        n = len(self.log())
        self.runcmd(f"C:\\{self.tdir}\\TPROF NOTE 60 {secs}")
        if self.wait("READY", n, 600):
            t1 = time.time()
            r.text(note, wait=2)
            self.events.append({"typed": note, "typing_s": round(time.time() - t1, 1)})
        self.wait("NOTE ms=", n, secs + 600)
        r.shot("notepad", settle=1, decode=False)
        (self.vm / "TPROF.LOG").write_text("\n".join(self.log()) + "\n")
        (self.vm / "T80PRUN.JSN").write_text(json.dumps({"events": self.events}, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vm", required=True)
    ap.add_argument("--dir", default="T40")
    ap.add_argument("--chars", type=int, default=30)
    ap.add_argument("--note", default="Hello TV owners 40x25")
    ap.add_argument("--secs", type=int, default=300)
    a = ap.parse_args()
    Run(a.vm, a.dir).session(a.chars, a.note, a.secs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
