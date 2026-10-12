#!/usr/bin/env python3
"""Scripted 86Box qualification of the XTPAN panned desktop (Tandy 1000 HX).

  python3 src/xtpan/XPWIN.PY --vm <prepared, started VM at the DOS prompt>
      [--base]   (the same machine with the shipped TR53216.DRV: memory,
                  drawing speed and the "before" pictures only)

Keys and mouse go in through xdotool and the PCPMOUSE serial mouse (exact
mickeys, MouseSpeed=0, so the logical pointer position is known). Checks
read what Windows reports, from the log files PANTEST.EXE and XTPAN.EXE
write on the guest disk (read with mtools while the guest runs), and
decode captures to exact pixels (PANCHK.PY). Results: <vm>/XPWIN.JSN.
"""
import argparse
import importlib.machinery
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PCPWIN = importlib.machinery.SourceFileLoader("pcpwin", str(HERE / "PCPWIN.PY")).load_module()
PANCHK = importlib.machinery.SourceFileLoader("panchk", str(HERE / "PANCHK.PY")).load_module()
PART = "@@8704"
PTR = (16, 20)          # pointer box checked as "pointer", width x height from the hot spot


class Session:
    def __init__(self, vm, base, measure_only=False):
        self.vm = Path(vm)
        self.base = base
        self.measure_only = measure_only
        self.r = PCPWIN.Run(vm, None, None, width=320, target="pcp")
        self.r.tdir, self.r.tid = "XTPAN", "RESERVE"
        self.checks = []
        self.measure = {}
        self.map = {}
        self.x = self.y = 0

    # -- guest logs --------------------------------------------------------
    def log(self, name="PANTEST.LOG"):
        p = subprocess.run(["mtype", "-i", f"{self.vm / 'pcp.img'}{PART}", "::/XTPAN/" + name],
                           capture_output=True)
        if p.returncode != 0:
            return []
        # complete lines only: a trailing newline must not count as a line
        return [ln for ln in p.stdout.decode("latin-1").replace("\r", "").split("\n") if ln]

    def wait_line(self, regex, start, timeout=60, name="PANTEST.LOG"):
        """First line after index start matching regex (re.Match), or None."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            lines = self.log(name)
            for ln in lines[start:]:
                m = re.search(regex, ln)
                if m:
                    return m
            time.sleep(2)
        return None

    def check(self, what, ok, **kw):
        self.checks.append(dict(check=what, result="PASS" if ok else "FAIL", **kw))
        print(("PASS " if ok else "FAIL ") + what, flush=True)
        (self.vm / "XPWIN.JSN").write_text(json.dumps(self.result(), indent=1) + "\n")

    def result(self):
        return {"driver": "TR53216.DRV" if self.base else "XTPAN.DRV", "checks": self.checks,
                "measurements": self.measure,
                "passed": sum(c["result"] == "PASS" for c in self.checks),
                "failed": sum(c["result"] == "FAIL" for c in self.checks)}

    # -- input -------------------------------------------------------------
    def home(self):
        """Pointer to logical (0,0); the helper then shows the top."""
        self.r.m("move", -400, -480)
        time.sleep(4)
        self.x = self.y = 0

    def to(self, x, y, wait=2.5):
        self.r.m("move", x - self.x, y - self.y)
        self.x, self.y = x, y
        time.sleep(wait)

    def click(self, wait=4):
        self.r.m("click")
        time.sleep(wait)

    def key(self, *k, wait=3):
        self.r.key(*k, wait=wait)

    def run(self, cmd, wait=40):
        self.key("alt+f", wait=5)
        self.key("r", wait=10)
        self.r.text(cmd)
        self.key("Return", wait=wait)

    # -- pattern checks ----------------------------------------------------
    def where(self):
        """(x, y, top, off) logged by PANTEST PATTERN on the P key."""
        n = len(self.log())
        self.key("p", wait=3)
        m = self.wait_line(r"CURSOR x=(-?\d+) y=(-?\d+) top=(-?\d+) off=(-?\d+)", n, 30)
        return tuple(int(v) for v in m.groups()) if m else None

    def pattern(self, name, pointer_check=True):
        """Capture and check the pattern exactly, the pointer box apart; and
        that everything differing is inside the pointer box at its video row."""
        w = self.where()
        if w is None:
            self.check(f"{name}: PANTEST reports pointer and viewport", False)
            return None
        x, y, top, off = w
        self.r.shot(name, settle=1.5, decode=False)
        cap = self.r.b.out / (name + ".png")
        vy = y - top
        box = (x, vy, x + PTR[0], vy + PTR[1])
        try:
            res = PANCHK.check(cap, top, off, [box], self.map)
        except SystemExit as e:           # capture not decodable: a failed check, not the end
            res = {"verdict": "FAIL", "error": str(e)}
        if res.get("verdict") == "PASS":
            self.map = res["map"]
        self.check(f"{name}: all video rows equal logical rows {top}..{top + 199} of the pattern "
                   f"(off {off}), pointer box apart", res.get("verdict") == "PASS",
                   pixels=res.get("pixels_checked"), mismatches=res.get("mismatches"),
                   first=res.get("first_mismatch"), pointer=[x, y], top=top)
        if pointer_check and 0 <= vy < 200:
            try:
                full = PANCHK.check(cap, top, off, [], self.map)
            except SystemExit:
                full = {"mismatches": 0}
            inside = full.get("mismatches", 0) - res.get("mismatches", 0)
            self.check(f"{name}: pointer drawn at its logical position, video row {vy} "
                       f"({inside} pointer pixels, none elsewhere)",
                       res.get("mismatches") == 0 and inside > 0)
        return w

    def pans(self, start):
        return [ln for ln in self.log("XTPAN.LOG")[start:] if ln.startswith("PAN ")]

    # -- the session ---------------------------------------------------------
    def windows(self):
        r = self.r
        r.text("CD \\WINDOWS")
        r.key("Return", wait=2)
        r.m("ident", "on")
        r.text("WIN /R")
        r.key("Return", wait=120)
        r.m("ident", "off")
        r.shot("groupmsg", settle=1, decode=False)
        for _ in range(6):
            self.key("Escape", wait=10)
        self.home()

    def scenario(self):
        self.windows()
        if self.base:
            return self.base_scenario()
        if self.measure_only:
            return self.measure_scenario()
        start = self.log("XTPAN.LOG")
        self.check("helper started with the XTPAN driver", any(l.startswith("START top=") for l in start),
                   log=start[:2])

        # A. pattern, keyboard pans, dwell, outside, hit tests, scroll, repeats
        self.run("C:\\XTPAN\\PANTEST PATTERN", wait=60)
        self.home()
        self.to(40, 60)
        self.pattern("pat_top0")
        p0 = len(self.log("XTPAN.LOG"))
        for _ in range(4):
            self.key("alt+shift+Next", wait=6)
        self.check("keyboard: four Alt+Shift+PgDn give four pans of 50 rows",
                   [l.split()[1:3] for l in self.pans(p0)] == [["0", "50"], ["50", "100"], ["100", "150"],
                                                               ["150", "200"]], log=self.pans(p0))
        w = self.pattern("pat_key200")
        if w:
            self.x, self.y = w[0], w[1]
        p0 = len(self.log("XTPAN.LOG"))
        self.key("alt+shift+Prior", wait=6)
        self.pattern("pat_key150")
        self.key("alt+shift+F9", wait=6)
        self.pattern("pat_keytop")
        self.check("keyboard: Alt+Shift+PgUp then Alt+Shift+F9 go to 150 then 0",
                   [l.split()[1:3] for l in self.pans(p0)] == [["200", "150"], ["150", "0"]], log=self.pans(p0))

        # edge dwell: a brief touch of the bottom edge does not pan, a rest does
        self.home()
        self.to(100, 150)
        p0 = len(self.log("XTPAN.LOG"))
        self.r.m("move", 0, 48)          # to row 198, in the 3-row edge band
        self.r.m("move", 0, -48)         # and straight back (one serial burst)
        time.sleep(4)
        self.check("dwell: touching the bottom edge briefly does not pan", self.pans(p0) == [],
                   log=self.pans(p0))
        self.to(100, 198, wait=4)
        pl = self.pans(p0)
        self.check("dwell: resting in the bottom edge band pans one step (0 -> 50)",
                   len(pl) >= 1 and pl[0].split()[1:4] == ["0", "50", "dwell-down"], log=pl)
        self.to(100, 150, wait=3)
        self.pattern("pat_dwell50")
        # outside: a fast move far below the viewport pans at once to show it
        p0 = len(self.log("XTPAN.LOG"))
        self.to(100, 330, wait=4)
        pl = self.pans(p0)
        # the 180-row move arrives as two serial packets, so one or two pans
        self.check("outside: pointer moved to row 330 is shown at once (viewport 150..349), no dwell",
                   1 <= len(pl) <= 2 and all(l.split()[3] == "outside" for l in pl) and pl[-1].split()[2] == "150",
                   log=pl)
        self.pattern("pat_out150")

        # hit tests: clicks report the logical point under the drawn pointer
        for (cx, cy) in ((20, 160), (300, 345), (150, 300)):
            n = len(self.log())
            self.home()
            self.to(cx, cy, wait=4)
            self.click(wait=3)
            m = self.wait_line(r"CLICK x=(-?\d+) y=(-?\d+) cursor=(-?\d+),(-?\d+) top=(-?\d+)", n, 30)
            got = tuple(int(v) for v in m.groups()) if m else None
            ok = bool(got) and got[0] == cx and got[1] == cy and got[4] <= cy < got[4] + 200
            self.check(f"click at logical ({cx},{cy}) is reported there, inside the viewport", ok, got=got)

        # screen-to-screen copies across the boundary: ScrollWindow
        self.home()
        self.to(40, 60)
        for _ in range(3):
            self.key("s", wait=8)
        self.pattern("pat_scroll_top0")
        for _ in range(4):
            self.key("alt+shift+Next", wait=6)
        self.pattern("pat_scroll_top200")

        # repeated panning
        p0 = len(self.log("XTPAN.LOG"))
        for i in range(10):
            self.key("alt+shift+Prior" if i % 2 == 0 else "alt+shift+Next", wait=5)
        self.check("repeated: ten alternating pans all happen", len(self.pans(p0)) == 10, log=self.pans(p0))
        self.pattern("pat_repeat")
        self.key("alt+shift+F9", wait=6)
        self.pattern("pat_repeat_top")
        self.key("q", wait=8)

        # B. tall dialog: the bottom button is reached and clicked
        self.home()
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST DIALOG", wait=50)
        m = self.wait_line(r"DLGITEM Bottom rect=(-?\d+),(-?\d+),(-?\d+),(-?\d+)", n, 60)
        md = self.wait_line(r"DIALOG rect=(-?\d+),(-?\d+),(-?\d+),(-?\d+)", n, 5)
        if md:
            d = [int(v) for v in md.groups()]
            self.check(f"tall dialog is taller than the screen ({d[3] - d[1]} rows)", d[3] - d[1] > 200, rect=d)
        if m:
            b = [int(v) for v in m.groups()]
            self.r.shot("dlg_shown", settle=1, decode=False)
            self.home()
            bx, by = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
            self.to(bx, by, wait=5)
            self.r.shot("dlg_bottom", settle=1, decode=False)
            n2 = len(self.log())
            self.click(wait=5)
            mb = self.wait_line(r"BUTTON Bottom rect=.* top=(-?\d+)", n2, 30)
            self.check(f"tall dialog: its Bottom button at rows {b[1]}..{b[3]} is clicked after panning",
                       mb is not None and int(mb.group(1)) <= by < int(mb.group(1)) + 200,
                       button=b, line=mb.group(0) if mb else None)
        else:
            self.check("tall dialog: button geometry logged", False)

        # C. overlapping windows across row 200
        self.home()
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST OVERLAP", wait=50)
        for name, (cx, cy) in (("A", (40, 260)), ("B", (260, 310)), ("A", (60, 150))):
            k = len(self.log())
            self.home()                   # a follow pan may have moved the pointer
            self.to(cx, cy, wait=4)
            self.click(wait=6)
            mc = self.wait_line(r"CLICK (\w) x=(-?\d+) y=(-?\d+)", k, 30)
            self.check(f"overlap: click at ({cx},{cy}) reaches window {name}",
                       mc is not None and mc.group(1) == name and int(mc.group(2)) == cx and int(mc.group(3)) == cy,
                       line=mc.group(0) if mc else None)
            self.r.shot(f"overlap_{name}_{cy}", settle=1, decode=False)
        self.key("alt+F4", wait=8)       # A is active and is the main window: both close

        # D. dragging a window across the viewport boundary
        self.home()
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST MOVE", wait=50)
        p0 = len(self.log("XTPAN.LOG"))
        self.home()
        self.to(120, 146, wait=4)
        self.r.m("down")
        time.sleep(2)
        for yy in (180, 220, 260, 296):
            self.to(120, yy, wait=4)
        self.r.m("up")
        time.sleep(8)
        mv = [ln for ln in self.log()[n:] if ln.startswith("MOVE ")]
        last = re.search(r"window=(-?\d+),(-?\d+)", mv[-1]) if mv else None
        self.check("drag: window caption dragged from row 146 to row 296 ends 150 rows lower",
                   bool(last) and int(last.group(2)) == 140 + 150, moves=mv[-3:])
        self.check("drag: the viewport followed during the drag", len(self.pans(p0)) > 0, log=self.pans(p0))
        self.r.shot("drag_after", settle=1, decode=False)
        self.key("alt+F4", wait=8)

        # E. menu below row 200
        self.home()
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST MENU", wait=50)
        mw = self.wait_line(r"MENUWIN rect=(-?\d+),(-?\d+),(-?\d+),(-?\d+) client=(-?\d+),(-?\d+)", n, 60)
        mm = self.wait_line(r"cymenu=(\d+)", n, 5)
        if mw and mm:
            left, cyc = int(mw.group(1)), int(mw.group(6))
            cym = int(mm.group(1))
            self.home()
            self.to(left + 20, cyc - cym // 2, wait=4)
            self.click(wait=6)
            self.r.shot("menu_open", settle=1, decode=False)
            k = len(self.log())
            self.to(left + 20, cyc + cym * 3 + cym // 2, wait=4)     # fourth item, Delta
            self.click(wait=6)
            mc = self.wait_line(r"COMMAND (\d+) top=(-?\d+)", k, 30)
            self.check("menu below 200: clicking its fourth item (Delta) gives command 204",
                       mc is not None and mc.group(1) == "204", line=mc.group(0) if mc else None)
        else:
            self.check("menu below 200: geometry logged", False)
        self.key("alt+F4", wait=8)

        # F. text selection across the boundary
        self.home()
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST EDIT", wait=60)
        me = self.wait_line(r"EDITORG x=(-?\d+) y=(-?\d+)", n, 60)
        mt = self.wait_line(r"tmheight=(\d+) tmextlead=(\d+)", n, 5)
        if me and mt:
            ox, oy = int(me.group(1)), int(me.group(2))
            lh = int(mt.group(1)) + int(mt.group(2))
            y1 = oy + lh * 1 + lh // 2           # line 2
            y2 = oy + lh * 17 + lh // 2          # line 18
            self.home()
            self.to(ox + 2, y1, wait=4)
            self.r.m("down")
            time.sleep(2)
            for yy in range(y1 + 40, y2, 40):
                self.to(ox + 40, yy, wait=4)
            self.to(ox + 40, y2, wait=4)
            self.r.m("up")
            time.sleep(6)
            self.wait_line(r"SELECT \d+ (?!9 )\d+", n, 30)
            sel = [ln for ln in self.log()[n:] if ln.startswith("SELECT ")]
            ms = re.search(r"SELECT (\d+) (\d+)", sel[-1]) if sel else None
            ok = bool(ms) and int(ms.group(1)) == 9 and int(ms.group(2)) // 9 + 1 == 18
            self.check(f"selection: dragging from line 2 (row {y1}) to line 18 (row {y2}) selects lines 2-18",
                       ok, selects=sel[-2:])
        else:
            self.check("selection: geometry logged", False)
        self.key("alt+F4", wait=8)

        # G. measurements, then exit and relaunch
        self.measurements()
        self.exit_relaunch()

    def measurements(self):
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST PANBENCH", wait=150)
        pb = [ln for ln in self.log()[n:] if ln.startswith("PANBENCH")]
        self.measure["panbench"] = pb
        self.bench()

    def bench(self):
        n = len(self.log())
        self.home()
        self.run("C:\\XTPAN\\PANTEST BENCH", wait=120)
        lines = self.log()[n:]
        self.measure["bench"] = [ln for ln in lines if ln.startswith("BENCH")]
        self.measure["free"] = [ln for ln in lines if ln.startswith("START")]

    def exit_relaunch(self):
        r = self.r
        self.home()
        self.key("alt+F4", wait=8)       # Program Manager is active again
        r.shot("exitdlg", settle=1, decode=False)
        self.key("Return", wait=40)
        r.shot("dos_after", settle=1, decode=False)
        self.windows()
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST PATTERN", wait=60)
        self.home()
        self.to(40, 60)
        self.pattern("relaunch_top0")
        self.key("alt+shift+Next", wait=6)
        self.key("alt+shift+Next", wait=6)
        self.pattern("relaunch_top100")
        self.key("q", wait=6)

    def measure_scenario(self):
        """Memory and drawing only (for the helper-disabled run)."""
        self.bench()
        self.check("measure: benchmark ran", bool(self.measure.get("bench")), bench=self.measure.get("bench"))
        self.measure["xtpan_log_head"] = self.log("XTPAN.LOG")[:3]

    def base_scenario(self):
        r = self.r
        n = len(self.log())
        self.run("C:\\XTPAN\\PANTEST DIALOG", wait=50)
        m = self.wait_line(r"DLGITEM Bottom rect=(-?\d+),(-?\d+),(-?\d+),(-?\d+)", n, 60)
        r.shot("before_dialog", settle=1, decode=False)
        if m:
            b = [int(v) for v in m.groups()]
            self.check(f"before: the tall dialog's Bottom button lies at rows {b[1]}..{b[3]}, below the "
                       "200-row screen", b[1] >= 200, button=b)
        # the keyboard still reaches it: Tab to Bottom, Space
        n = len(self.log())
        self.key("Tab", wait=3)
        self.key("space", wait=6)
        mb = self.wait_line(r"BUTTON Bottom", n, 30)
        self.check("before: the Bottom button is reachable by keyboard only (Tab, Space)", mb is not None)
        self.bench()
        self.check("before: benchmark ran", bool(self.measure.get("bench")), bench=self.measure.get("bench"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm", required=True)
    ap.add_argument("--base", action="store_true")
    ap.add_argument("--measure", action="store_true", help="memory and drawing only")
    a = ap.parse_args()
    s = Session(a.vm, a.base, a.measure)
    try:
        s.scenario()
    finally:
        s.measure["xtpan_log"] = s.log("XTPAN.LOG")
        s.measure["pantest_log"] = s.log()
        (Path(a.vm) / "XPWIN.JSN").write_text(json.dumps(s.result(), indent=1) + "\n")
        print(json.dumps({k: v for k, v in s.result().items() if k in ("passed", "failed")}))
    return 0 if all(c["result"] == "PASS" for c in s.checks) else 1


if __name__ == "__main__":
    sys.exit(main())
