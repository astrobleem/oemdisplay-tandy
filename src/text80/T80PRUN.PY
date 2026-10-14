#!/usr/bin/env python3
"""Profiling session for the text-mode drivers in 86Box (no pass/fail checks).

  python3 src/text80/T80PRUN.PY --vm <prepared, started VM at the DOS prompt>
      --font <CGA 8x8 font> --dir T40 [--chars 30] [--note "Hello TV owners 40x25"]

Every step is confirmed on screen (captures decoded to text with T40SHOT)
and retried if a key was lost while Windows was busy redrawing.

Starts Windows 3.0, then through Program Manager's Run dialog:
  1. TPROF TYPE <chars>: per-character driver counters (or wall time only on
     a driver without escape 5450h);
  1b. TPROF LINES <chars>: the same, a letter and Return each time, so the
     edit control scrolls once it is full (per-line counters);
  2. TPROF NOTE 60 <secs>: Notepad started by TPROF; once TPROF logs READY,
     the note text is typed with real keys (xdotool, the emulated keyboard);
     TPROF reads the counters after <secs>.
Captures: desktop, after TYPE, Notepad with the typed line. The guest log
C:\\<dir>\\TPROF.LOG is copied to <vm>/TPROF.LOG; T80PROFX.PY reports it.
"""
import argparse
import importlib.machinery
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PCPWIN = importlib.machinery.SourceFileLoader("pcpwin", str(HERE.parent / "pcp" / "PCPWIN.PY")).load_module()
SHOT = importlib.machinery.SourceFileLoader("t40shot", str(HERE.parent / "txt40" / "T40SHOT.PY")).load_module()
CHK = importlib.machinery.SourceFileLoader("t80chk", str(HERE / "T80CHK.PY")).load_module()
PART = "@@8704"


class Run:
    def __init__(self, vm, tdir, font, snap=False):
        self.snapmode = snap
        self.font = Path(font).read_bytes() if font else None
        self.n = 0
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

    def snaprows(self):
        """--snap: the text buffer via T80SNAP (Scroll Lock), any width."""
        def recs():
            p = subprocess.run(["mtype", "-i", f"{self.vm / 'pcp.img'}{PART}", f"::/{self.tdir}/SNAPS.BIN"],
                               capture_output=True)
            try:
                return CHK.parse(p.stdout) if p.returncode == 0 else []
            except ValueError:
                return []
        n = len(recs())
        subprocess.run(["xdotool", "key", "--delay", "150", "Scroll_Lock"], check=False)
        t0 = time.time()
        while time.time() - t0 < 120:
            r = recs()
            if len(r) > n:
                return CHK.rows(r[-1]["hidden"], r[-1]["cols"])
            time.sleep(3)
        return []

    def rows(self, name="look"):
        if self.snapmode:
            return self.snaprows()
        self.n += 1
        nm = f"{name}_{self.n}"
        self.r.shot(nm, settle=0.5, decode=False)
        try:
            return SHOT.rows(SHOT.decode(self.r.b.out / (nm + ".png")), self.font)
        except SystemExit:
            return []

    def until(self, want, timeout=600, every=10, name="look"):
        """Wait until every string in want is on screen and two captures in
        a row are identical. Returns the rows or None."""
        t0, prev = time.time(), None
        while time.time() - t0 < timeout:
            rows = self.rows(name)
            if prev == rows and all(any(w in row for row in rows) for w in want):
                return rows
            prev = rows
            time.sleep(every)
        self.events.append({"not_seen": list(want), "rows": prev})
        return None

    def runcmd(self, cmd):
        """File > Run in Program Manager, confirmed on screen, retried."""
        r = self.r
        for attempt in range(6):
            r.key("alt+f", wait=10)
            if not self.until(("Run...",), timeout=120, name="menu"):
                r.key("Escape", wait=5)
                r.key("Escape", wait=5)
                continue
            r.key("r", wait=10)
            if not self.until(("Command Line:",), timeout=180, name="run"):
                r.key("Escape", wait=5)
                continue
            r.text(cmd, wait=3)
            r.key("Return", wait=5)
            self.events.append({"run": cmd, "attempt": attempt + 1})
            return True
        self.events.append({"run_failed": cmd})
        return False

    def session(self, chars, note, secs, t80on=False, steps=("type", "lines", "note"), profile=""):
        r = self.r
        if t80on:
            r.text("C:", wait=1)
            r.key("Return", wait=2)
            r.text("CD \\T80", wait=1)
            r.key("Return", wait=2)
            r.text(f"T80ON C:\\WINDOWS {profile}" if profile else "T80ON", wait=1)
            r.key("Return", wait=25)
            r.shot("t80on", settle=1, decode=False)
        r.text("CD \\WINDOWS")
        r.key("Return", wait=2)
        r.m("ident", "on")
        r.text("WIN /R")
        r.key("Return", wait=150)
        r.m("ident", "off")
        for _ in range(6):
            r.key("Escape", wait=12)
        r.home()
        self.until(("Program Manager", "File", "Options"), timeout=900, name="desktop")
        if "metrics" in steps:
            n = len(self.log())
            self.runcmd(f"C:\\{self.tdir}\\TPROF METRICS 90")
            self.wait("WIN progman", n, 1200)
            time.sleep(20)
            rows = self.rows("metrics")
            (self.vm / "METRICS.TXT").write_text("\n".join(rows) + "\n")
            r.shot("metrics", settle=1, decode=False)
        if "nlines" in steps:
            # Notepad maximized, 25 lines typed (so every new line scrolls),
            # then TPROF NLINES 20 from Program Manager
            self.runcmd("NOTEPAD")
            self.until(("Notepad - (untitled)",), timeout=900, name="np")
            for i in range(25):
                r.text("x", wait=1)
                r.key("Return", wait=3)
            r.key("alt+space", wait=8)
            r.key("x", wait=20)
            self.until(("Notepad - (untitled)",), timeout=900, name="max")
            r.key("alt+Escape", wait=10)
            n = len(self.log())
            self.runcmd(f"C:\\{self.tdir}\\TPROF NLINES 20")
            self.wait("NLINES n=", n, 3600)
            rows = self.rows("nlines")
            (self.vm / "NLINES.TXT").write_text("\n".join(rows) + "\n")
        if "type" not in steps:
            (self.vm / "TPROF.LOG").write_text("\n".join(self.log()) + "\n")
            (self.vm / "T80PRUN.JSN").write_text(json.dumps({"events": self.events}, indent=1) + "\n")
            return
        n = len(self.log())
        t0 = time.time()
        self.runcmd(f"C:\\{self.tdir}\\TPROF TYPE {chars}")
        self.wait("TYPE n=", n, 3600)
        self.events.append({"type_wall_s": round(time.time() - t0, 1)})
        r.shot("aftertype", settle=1, decode=False)
        time.sleep(30)
        n = len(self.log())
        t0 = time.time()
        self.runcmd(f"C:\\{self.tdir}\\TPROF LINES {chars}")
        self.wait("LINES n=", n, 3600)
        self.events.append({"lines_wall_s": round(time.time() - t0, 1)})
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
    ap.add_argument("--font", type=Path, help="CGA 8x8 font (40-column screenshots); not with --snap")
    ap.add_argument("--snap", action="store_true", help="read screens from T80SNAP buffers (TEXT80)")
    ap.add_argument("--t80on", action="store_true", help="run T80ON at the DOS prompt first")
    ap.add_argument("--chars", type=int, default=30)
    ap.add_argument("--note", default="Hello TV owners 40x25")
    ap.add_argument("--secs", type=int, default=300)
    ap.add_argument("--metrics-only", action="store_true",
                    help="only TPROF METRICS: system metrics and window/client rectangles, a screen")
    ap.add_argument("--nlines-only", action="store_true",
                    help="only TPROF NLINES 20 into a maximized Notepad holding 25 lines")
    ap.add_argument("--profile", default="", help="T80ON profile argument (e.g. C25)")
    a = ap.parse_args()
    steps = ("metrics",) if a.metrics_only else ("nlines",) if a.nlines_only else ("type", "lines", "note")
    r = Run(a.vm, a.dir, a.font, a.snap)
    r.session(a.chars, a.note, a.secs, a.t80on, steps, a.profile)
    # no pass/fail checks here, but a step that never happened is a failed run
    bad = [e for e in r.events if any(k in e for k in ("timeout", "run_failed", "not_seen"))]
    print(f"T80PRUN: {len(bad)} steps not completed" + (f": {bad}" if bad else ""), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
