#!/usr/bin/env python3
"""Scripted 86Box qualification of TEXT80 (80x25 colour text, no panning).

  python3 src/text80/T80WIN.PY --vm <VM from T80PREP.PY, started, at the DOS prompt>
      [--prof] [--skip-rollback]

Everything is checked on exact text cells: T80SNAP.EXE (on load=) appends
the text buffer to C:\\T80\\SNAPS.BIN whenever Scroll Lock is pressed, once
with the pointer hidden and once shown (T80CHK.PY). 86Box captures are kept
as pictures. Steps (each check waits until two snapshots in a row are
identical and the wanted text is there):
  T80ON at the DOS prompt; Windows starts in 80x25 (BIOS columns 80);
  desktop text; pointer = exactly the hot spot cell XOR 77h, at two places;
  File menu, closed = desktop again (identical cells); Run dialog;
  Notepad: a typed line in exact cells and colours; text selection
  (selected cells change colour, characters stay); Edit menu, closed =
  Notepad again; 30 lines typed so the window scrolls; Notepad dragged by
  its title with the mouse; two overlapping windows (Notepad and Program
  Manager) brought to front in turn; exit to DOS and relaunch = the same
  desktop; T80OFF and Windows again with the previous driver (40 columns).
--prof: the driver is a T80PROF build; TPROF NOTE records typing time.
--profile pan: T80ON ... PAN (T80PAN.DRV, 640x400 desktop, 25 of 50 rows
shown, XTPAN.EXE helper) and the panning steps instead of 4-10: Alt+PgDn
pans in whole text rows and the screen rows are exactly the logical rows
seen before (overlap compared cell for cell), Alt+PgUp restores the desktop
identically, repeated pans, the Run dialog (centred on the 400-row desktop)
brought wholly into view by the helper, the pointer footprint while panned,
Notepad moved below the viewport, typed into while not shown (offscreen
drawing) and revealed by a pan with no repaint; pan times from the helper
log (C:\\T80\\XTPAN.LOG).
Results: <vm>/T80WIN.JSN.
"""
import argparse
import importlib.machinery
import json
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PCPWIN = importlib.machinery.SourceFileLoader("pcpwin", str(HERE.parent / "pcp" / "PCPWIN.PY")).load_module()
CHK = importlib.machinery.SourceFileLoader("t80chk", str(HERE / "T80CHK.PY")).load_module()
PART = "@@8704"


class Session:
    def __init__(self, vm, prof):
        self.vm = Path(vm)
        self.prof = prof
        self.r = PCPWIN.Run(vm, None, None, width=640, target="pcp")
        self.r.tdir, self.r.tid = "T80", "T40ID"
        self.checks, self.recs, self.timing = [], {}, {}
        self.width = 640

    # -- guest files ---------------------------------------------------------
    def read(self, name):
        p = subprocess.run(["mtype", "-i", f"{self.vm / 'pcp.img'}{PART}", name], capture_output=True)
        return p.stdout if p.returncode == 0 else b""

    def snaps(self):
        try:
            return CHK.parse(self.read("::/T80/SNAPS.BIN"))
        except ValueError:
            return []

    def check(self, what, ok, **kw):
        self.checks.append(dict(check=what, result="PASS" if ok else "FAIL", **kw))
        print(("PASS " if ok else "FAIL ") + what, flush=True)
        (self.vm / "T80WIN.JSN").write_text(json.dumps(self.result(), indent=1) + "\n")

    def result(self):
        return {"checks": self.checks, "timing_s": self.timing,
                "passed": sum(c["result"] == "PASS" for c in self.checks),
                "failed": sum(c["result"] == "FAIL" for c in self.checks)}

    # -- snapshots -----------------------------------------------------------
    def snap(self, timeout=120):
        n = len(self.snaps())
        subprocess.run(["xdotool", "key", "--delay", "150", "Scroll_Lock"], check=False,
                       env=dict(__import__("os").environ, DISPLAY=":79"))
        t0 = time.time()
        while time.time() - t0 < timeout:
            s = self.snaps()
            if len(s) > n:
                return s[-1]
            time.sleep(3)
        return None

    def settle(self, name, want=(), timeout=900, every=6):
        """Snapshot until two in a row have identical cells (pointer hidden)
        and every wanted string is on screen."""
        t0, prev = time.time(), None
        while time.time() - t0 < timeout:
            rec = self.snap()
            if rec is not None:
                shown = all(CHK.find(rec["hidden"], rec["cols"], w) for w in want)
                if prev is not None and prev["hidden"] == rec["hidden"] and shown:
                    self.recs[name] = rec
                    self.timing[name] = round(time.time() - t0, 1)
                    self.r.shot(name, settle=0.5, decode=False)
                    (self.vm / (name + ".txt")).write_text("\n".join(CHK.rows(rec["hidden"], rec["cols"])) + "\n")
                    return rec
                prev = rec
            time.sleep(every)
        self.check(f"{name}: screen settles with {list(want)} within {timeout} s", False,
                   last=CHK.rows(prev["hidden"], prev["cols"]) if prev else None)
        self.recs[name] = prev
        return prev

    def expect(self, name, *strings):
        rec = self.recs.get(name)
        for s in strings:
            hits = CHK.find(rec["hidden"], rec["cols"], s) if rec else []
            self.check(f"{name}: shows '{s}'", bool(hits), at=hits[:3])

    def identical(self, a, b, what, allow=()):
        ra, rb = self.recs.get(a), self.recs.get(b)
        diff = CHK.same(ra["hidden"], rb["hidden"], allow) if ra and rb else ["missing"]
        self.check(what, diff == [], differing_cells=diff[:20])

    def cursor(self, name):
        rec = self.recs.get(name)
        ok, det = CHK.cursor(rec) if rec else (False, {})
        self.check(f"{name}: the pointer is exactly the hot spot's cell, attribute XOR 77h "
                   f"(pointer {rec and (rec['x'], rec['y'])})", ok, **det)

    # -- input ---------------------------------------------------------------
    def key(self, k, wait=4):
        self.r.key(k, wait=wait)

    def text(self, s, wait=2):
        self.r.text(s, wait=wait)

    def to(self, x, y, wait=3):
        self.r.rehome(x, y, wait=wait)

    def runcmd(self, cmd):
        for attempt in range(5):
            self.key("alt+f", 8)
            if not self.settle(f"runmenu{attempt}", ("Run...",), timeout=240):
                self.key("Escape", 4)
                self.key("Escape", 4)
                continue
            self.key("r", 8)
            if self.settle(f"rundlg{attempt}", ("Command Line:",), timeout=300):
                self.text(cmd, 3)
                self.key("Return", 5)
                return True
            self.key("Escape", 4)
        return False

    def start_windows(self, tag, want):
        self.text("C:", 1)
        self.key("Return", 2)
        self.text("CD \\WINDOWS", 1)
        self.key("Return", 2)
        self.r.m("ident", "on")
        self.text("WIN /R", 1)
        self.key("Return", 150)
        self.r.m("ident", "off")
        for _ in range(6):
            self.key("Escape", 10)
        self.r.home()
        return self.settle(tag, want, timeout=1800)

    # -- the session ---------------------------------------------------------
    def pan(self, key, name, want=()):
        """A pan key held 150 ms like a person presses it (the helper polls
        every 55 ms; XPWIN.PY pankey)."""
        PCPWIN.P.focus()
        subprocess.run(["xdotool", "keydown", key], check=False, env=dict(__import__("os").environ, DISPLAY=":79"))
        time.sleep(0.15)
        subprocess.run(["xdotool", "keyup", key], check=False, env=dict(__import__("os").environ, DISPLAY=":79"))
        time.sleep(8)
        return self.settle(name, want)

    def run_pan(self, rollback=True):
        r = self.r
        self.text("C:", 1)
        self.key("Return", 2)
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80ON C:\\WINDOWS PAN", 1)
        self.key("Return", 25)
        r.shot("t80on", settle=1, decode=False)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        winini = self.read("::/WINDOWS/WIN.INI").decode("latin1")
        load = [ln for ln in winini.split("\r\n") if ln.lower().startswith("load=")]
        self.check("T80ON PAN: display.drv=T80PAN.DRV, originals saved, load= keeps T80SNAP and gains XTPAN.EXE",
                   "display.drv=T80PAN.DRV" in sysini and bool(self.read("::/WINDOWS/SYSTEM.T80")) and
                   len(load) == 1 and "T80SNAP.EXE" in load[0].upper() and "XTPAN.EXE" in load[0].upper(),
                   load=load)
        desk = ("Program Manager", "File", "Options", "Window", "Help")
        rec = self.start_windows("desktop", desk)
        self.check("Windows runs in 80x25 text over the 640x400 desktop, top 0",
                   bool(rec) and rec["cols"] == 80 and rec["rows"] == 25 and rec["top"] == 0,
                   top=rec and rec["top"])
        self.expect("desktop", *desk)
        r.home()
        self.settle("desk0")
        # pan down: Step 50 from 0 rounds up to 56 (7 text rows)
        t0 = time.time()
        d1 = self.pan("alt+Next", "pan_down1")
        self.timing["pan_down1_settled"] = round(time.time() - t0, 1)
        d0 = self.recs.get("desk0")
        ok = bool(d1 and d0) and d1["top"] == 56
        if ok:
            ok = d1["hidden"][:18 * 80] == d0["hidden"][7 * 80:25 * 80]
        self.check("Alt+PgDn: top 56 (whole text rows); screen rows 0-17 are exactly rows 7-24 seen before",
                   ok, top=d1 and d1["top"])
        u1 = self.pan("alt+Prior", "pan_up1")
        self.check("Alt+PgUp: top 0 and every cell as before the pan",
                   bool(u1 and d0) and u1["top"] == 0 and u1["hidden"] == d0["hidden"], top=u1 and u1["top"])
        # repeated pans: down to the bottom and back, every screen consistent
        tops, ok = [], True
        prev = d0
        for i in range(5):
            rec = self.pan("alt+Next", f"pan_rep{i}")
            if not rec:
                ok = False
                break
            tops.append(rec["top"])
            dy = (rec["top"] - prev["top"]) // 8
            if rec["top"] % 8 or not 0 <= dy <= 25:
                ok = False
            elif dy < 25 and rec["hidden"][:(25 - dy) * 80] != prev["hidden"][dy * 80:]:
                ok = False
            prev = rec
        self.check("repeated Alt+PgDn: whole text rows, each screen continues the previous one exactly, "
                   "stops at the last row (top 200)", ok and tops[-1:] == [200], tops=tops)
        self.cursor_at("panned_pointer", 300, 330)
        rec = self.pan("alt+F9", "pan_top")
        self.check("Alt+F9: back to top 0, every cell as on the desktop",
                   bool(rec) and rec["top"] == 0 and rec["hidden"] == d0["hidden"])
        # the Run dialog is centred on the 400-row desktop: the helper brings
        # it wholly into view
        self.key("alt+f", 8)
        self.key("r", 8)
        run = ("Command Line:", "Run Minimized", "OK", "Cancel")
        rd = self.settle("rundlg", run, timeout=600)
        self.check("Run dialog: shown whole after the helper's follow pan (top a multiple of 8)",
                   bool(rd) and rd["top"] % 8 == 0 and all(CHK.find(rd["hidden"], 80, s) for s in run),
                   top=rd and rd["top"])
        self.key("Escape", 6)
        self.pan("alt+F9", "after_run")
        # Notepad below the viewport, typed into while not shown
        self.free_memory("before_notepad")
        self.type_speed("edit")
        self.type_speed("edit", mode="LINES")
        self.runcmd("NOTEPAD")
        self.settle("notepad0", ("Notepad - (untitled)",), timeout=1200)
        self.key("alt+space", 4)
        self.key("m", 4)
        for _ in range(28):
            self.key("Down", 0.5)
        self.key("Return", 8)
        self.pan("alt+F9", "np_moved_top0")
        line = "typed while not shown"
        t0 = time.time()
        self.text(line, 2)
        self.timing["offscreen_typing_s"] = round(time.time() - t0, 1)
        hid = self.settle("offscreen_typed")
        self.check("offscreen typing: the screen (top 0) does not show the typed line",
                   bool(hid) and hid["top"] == 0 and not CHK.find(hid["hidden"], 80, line))
        for i in range(5):
            rec = self.pan("alt+Next", f"reveal{i}", ())
            if rec and CHK.find(rec["hidden"], 80, line):
                break
        self.check("pan reveals the line typed while it was not shown (drawn offscreen, no repaint)",
                   bool(rec) and bool(CHK.find(rec["hidden"], 80, line)), top=rec and rec["top"])
        if rec:
            hits = CHK.find(rec["hidden"], 80, line)
            if hits:
                rr, cc = hits[0]
                attrs = {(w >> 8) if (w & 0xFF) != 0x20 else ((w >> 8) & 0xF0) | 0x0 for w in CHK.cells_at(rec["hidden"], 80, rr, cc, len(line))}
                self.check("revealed line: one colour pair, black on white (F0h)", attrs <= {0xF0},
                           attrs=sorted(hex(a) for a in attrs))
        log = self.read("::/T80/XTPAN.LOG").decode("latin1")
        (self.vm / "XTPAN.LOG").write_text(log)
        pans = [ln for ln in log.splitlines() if ln.startswith("PAN ")]
        self.timing["helper_pans"] = pans
        self.check("helper log: pans recorded with their times", bool(pans), pans=len(pans))
        # exit, relaunch, rollback
        self.key("alt+F4", 8)
        self.settle("savequery", ("No",), timeout=600)
        self.key("n", 10)
        self.pan("alt+F9", "before_exit")
        self.key("alt+F4", 8)
        self.wait_shot("exitdlg", 90)
        self.key("Return", 60)
        self.start_windows("desktop2", desk)
        r.home()
        self.settle("desk2")
        self.identical("desk0", "desk2", "relaunch: the desktop is identical to the first launch")
        if not rollback:
            return
        self.key("alt+F4", 8)
        self.wait_shot("exitdlg2", 90)
        self.key("Return", 60)
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80OFF", 1)
        self.key("Return", 25)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        winini = self.read("::/WINDOWS/WIN.INI").decode("latin1")
        self.check("T80OFF: SYSTEM.INI and WIN.INI restored (no T80PAN.DRV, no XTPAN.EXE on load=)",
                   "T80PAN" not in sysini.upper() and "XTPAN.EXE" not in winini.upper() and
                   not self.read("::/WINDOWS/SYSTEM.T80"))
        rec = self.start_windows("rolledback", ("Program Manager",))
        self.check("rollback: Windows starts with the previous driver (BIOS columns no longer 80)",
                   bool(rec) and rec["cols"] != 80, cols=rec and rec["cols"])

    def run_allocfail(self, rollback=True):
        """T80PAN.DRV built with the allocation fault injected (BUILDT80
        t80panfail): Enable's GlobalAlloc fails on every machine. Windows
        must not start in a broken state: back at a usable DOS prompt, then
        T80OFF and Windows with the previous driver."""
        r = self.r
        self.text("C:", 1)
        self.key("Return", 2)
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80ON C:\\WINDOWS PAN", 1)
        self.key("Return", 25)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        self.check("T80ON PAN (fault-injected driver): display.drv=T80PAN.DRV", "display.drv=T80PAN.DRV" in sysini)
        self.text("CD \\WINDOWS", 1)
        self.key("Return", 2)
        self.text("WIN /R", 1)
        self.key("Return", 240)
        r.shot("allocfail_after_win", settle=1, decode=False)
        for _ in range(3):
            self.key("Escape", 5)
            self.key("Return", 10)
        r.shot("allocfail_keys", settle=1, decode=False)
        self.text("ECHO ALIVE> C:\\T80\\ALIVE.TXT", 1)
        self.key("Return", 15)
        alive = self.read("::/T80/ALIVE.TXT")
        self.check("allocation failure: Windows does not start and the DOS prompt is usable (a command ran)",
                   alive.strip() == b"ALIVE", got=alive[:20].decode("latin1"))
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80OFF", 1)
        self.key("Return", 25)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        self.check("T80OFF after the failure: SYSTEM.INI restored", "T80PAN" not in sysini.upper()
                   and not self.read("::/WINDOWS/SYSTEM.T80"))
        rec = self.start_windows("rolledback", ("Program Manager",))
        self.check("rollback: Windows starts with the previous driver (BIOS columns no longer 80)",
                   bool(rec) and rec["cols"] != 80, cols=rec and rec["cols"])

    def run_vga(self, rollback=True):
        """VGA 80x50 (T80VGA.DRV) in DOSBox-X (machine=vgaonly): all 50 rows
        of the 640x400 desktop shown. Keyboard-driven; the pointer is
        checked wherever it is."""
        r = self.r
        self.text("C:", 1)
        self.key("Return", 2)
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80ON C:\\WINDOWS VGA", 1)
        self.key("Return", 15)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        self.check("T80ON VGA: display.drv=T80VGA.DRV, originals saved",
                   "display.drv=T80VGA.DRV" in sysini and bool(self.read("::/WINDOWS/SYSTEM.T80")))
        desk = ("Program Manager", "File", "Options", "Window", "Help")
        rec = self.start_windows("desktop", desk)
        self.check("Windows runs in VGA 80x50 text (BIOS columns 80, rows 50)",
                   bool(rec) and rec["cols"] == 80 and rec["rows"] == 50, rows=rec and rec["rows"])
        self.expect("desktop", *desk)
        self.cursor("desktop")
        self.key("alt+f", 8)
        menu = ("New...", "Open", "Move...", "Copy...", "Delete", "Properties...", "Run...", "Exit Windows...")
        self.settle("filemenu", menu)
        self.expect("filemenu", *menu)
        self.key("Escape", 4)
        self.key("Escape", 4)
        self.settle("menuclosed")
        self.identical("desktop", "menuclosed", "File menu closed: every cell as on the desktop before")
        self.key("alt+f", 8)
        self.key("r", 8)
        run = ("Run", "Command Line:", "Run Minimized", "OK", "Cancel")
        rd = self.settle("rundlg", run)
        self.expect("rundlg", *run)
        if rd:
            rows = [h[0] for s in run for h in CHK.find(rd["hidden"], 80, s)]
            self.timing["rundlg_text_rows"] = sorted(set(rows))     # where Windows put it (informational)
        self.key("Escape", 6)
        self.free_memory("before_notepad")
        self.type_speed("edit")
        self.type_speed("edit", mode="LINES")
        self.runcmd("NOTEPAD")
        self.settle("notepad0", ("Notepad - (untitled)",), timeout=1200)
        line = "Hello from VGA 80x50 text mode!"
        self.text(line, 2)
        rec = self.settle("notepad", ("Notepad - (untitled)", line), timeout=1200)
        self.expect("notepad", "Notepad - (untitled)", line)
        if rec:
            hits = CHK.find(rec["hidden"], 80, line)
            if hits:
                rr, cc = hits[0]
                attrs = {(w >> 8) if (w & 0xFF) != 0x20 else ((w >> 8) & 0xF0) | 0x0 for w in CHK.cells_at(rec["hidden"], 80, rr, cc, len(line))}
                self.check("notepad: the typed line is one colour pair, black on white (F0h)",
                           attrs <= {0xF0}, attrs=sorted(hex(a) for a in attrs))
        self.key("shift+Home", 6)
        sel = self.settle("selected", (line,))
        if rec and sel:
            hits = CHK.find(rec["hidden"], 80, line)
            if hits:
                rr, cc = hits[0]
                before = CHK.cells_at(rec["hidden"], 80, rr, cc, len(line))
                after = CHK.cells_at(sel["hidden"], 80, rr, cc, len(line))
                self.check("selection: the selected cells keep their characters and all change colour",
                           all((a & 0xFF) == (b & 0xFF) and (a >> 8) != (b >> 8) for a, b in zip(before, after)))
        self.key("End", 6)
        for i in range(1, 51):
            self.key("Return", 0.5)
            self.text(f"line {i:02d}", 0.5)
        sc = self.settle("scrolled", ("line 50",), timeout=2400)
        rows = CHK.rows(sc["hidden"], 80) if sc else []
        self.check("scrolling: the last line is visible and the first typed line has scrolled away",
                   bool(sc) and any("line 50" in rw for rw in rows) and not any(line in rw for rw in rows))
        self.key("alt+Escape", 8)
        pm = self.settle("pmfront", ("Program Manager",))
        self.key("alt+Escape", 8)
        np = self.settle("npfront", ("Notepad - (untitled)",))
        self.check("overlap: switching windows changes which one is on top (cells differ), and back",
                   bool(pm and np) and pm["hidden"] != np["hidden"])
        self.key("alt+F4", 8)
        self.settle("savequery", ("No",), timeout=600)
        self.key("n", 10)
        self.key("alt+F4", 8)
        self.wait_shot("exitdlg", 90)
        self.key("Return", 30)
        r.shot("dos_after", settle=1)
        self.start_windows("desktop2", desk)
        self.identical("desktop", "desktop2", "relaunch: the desktop is identical to the first launch")
        if not rollback:
            return
        self.key("alt+F4", 8)
        self.wait_shot("exitdlg2", 90)
        self.key("Return", 30)
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80OFF", 1)
        self.key("Return", 15)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        self.check("T80OFF: SYSTEM.INI no longer names T80VGA.DRV and the backups are gone",
                   "T80VGA" not in sysini.upper() and not self.read("::/WINDOWS/SYSTEM.T80"))
        rec = self.start_windows("rolledback", ("Program Manager",))
        self.check("rollback: Windows starts with the previous driver (BIOS columns no longer 80)",
                   bool(rec) and rec["cols"] != 80, cols=rec and rec["cols"])

    def type_speed(self, tag, n=30, mode="TYPE"):
        """TPROF TYPE n: n characters into a visible edit control, one
        WM_CHAR at a time, every resulting message processed; wall time
        from GetCurrentTime (no per-character logging without the
        profiling escape)."""
        before = self.read("::/T80/TPROF.LOG").decode("latin1")
        self.runcmd(f"C:\\T80\\TPROF {mode} {n}")
        t0 = time.time()
        while time.time() - t0 < 1800:
            new = self.read("::/T80/TPROF.LOG").decode("latin1")[len(before):]
            m = re.search(mode + r" n=(\d+) ms=(\d+)", new)
            if m:
                ms = int(m.group(2))
                self.timing[f"{mode.lower()}_ms_each_{tag}"] = round(ms / int(m.group(1)), 1)
                self.check(f"TPROF {mode} {n} ({tag}): {ms} ms, {ms / int(m.group(1)):.0f} ms each", True)
                time.sleep(10)
                return ms
            time.sleep(5)
        self.check(f"TPROF {mode} {n} ({tag}) finished", False)
        return None

    def wait_shot(self, name, secs):
        """The end-session dialog is system modal: T80SNAP gets no timer
        messages while it is up, so it is only captured as a picture."""
        time.sleep(secs)
        self.r.shot(name, settle=1, decode=False)

    def free_memory(self, tag):
        """TPROF IDLE 1 logs Windows' free memory (GetFreeSpace) on its
        START line; a driver without the profiling escape logs only that."""
        before = self.read("::/T80/TPROF.LOG").decode("latin1")
        self.runcmd("C:\\T80\\TPROF IDLE 1")
        t0 = time.time()
        while time.time() - t0 < 600:
            log = self.read("::/T80/TPROF.LOG").decode("latin1")
            new = log[len(before):]
            m = re.search(r"START cmd=IDLE 1 prof=(\d) free=(\d+)", new)
            if m and "END" in new[m.end():]:
                self.timing["free_bytes_" + tag] = int(m.group(2))
                self.check(f"free memory recorded ({tag}): {m.group(2)} bytes", True)
                return int(m.group(2))
            time.sleep(5)
        self.check(f"free memory recorded ({tag})", False)
        return None

    def cursor_at(self, name, x, y):
        """Pointer to logical (x, y) on the 640x400 desktop: pinned at (0, 0)
        first (PCPWIN's own moves are limited to 200 rows)."""
        self.r.m("move", -(self.width + 80), -480)
        time.sleep(3)
        self.r.m("move", x, y)
        time.sleep(5)
        self.settle(name)
        self.cursor(name)

    def run(self, rollback=True):
        r = self.r
        # 1. set up from the DOS prompt
        self.text("C:", 1)
        self.key("Return", 2)
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80ON", 1)
        self.key("Return", 25)
        r.shot("t80on", settle=1, decode=False)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        winini = self.read("::/WINDOWS/WIN.INI").decode("latin1")
        self.check("T80ON: display.drv=TEXT80.DRV and the 8x8 fonts set; originals saved",
                   "display.drv=TEXT80.DRV" in sysini and "fonts.fon=XTTSYS.FON" in sysini and
                   bool(self.read("::/WINDOWS/SYSTEM.T80")) and bool(self.read("::/WINDOWS/WIN.T80")))
        load = [ln for ln in winini.split("\r\n") if ln.lower().startswith("load=")]
        self.check("T80ON: load= keeps its entry (T80SNAP); [fonts] gained the two 8x8 faces",
                   len(load) == 1 and "T80SNAP.EXE" in load[0].upper() and
                   winini.count("(TEXT80)=") == 2, load=load)
        # 2. Windows in 80x25
        desk = ("Program Manager", "File", "Options", "Window", "Help")
        rec = self.start_windows("desktop", desk)
        self.check("Windows runs in 80x25 text (BIOS columns 80, rows 25)",
                   bool(rec) and rec["cols"] == 80 and rec["rows"] == 25)
        self.expect("desktop", *desk)
        # 3. pointer footprint, two places
        for name, (x, y) in (("pointer_a", (300, 150)), ("pointer_b", (37, 77))):
            self.to(x, y, 4)
            self.settle(name)
            self.cursor(name)
        r.home()
        # 4. File menu
        self.key("alt+f", 8)
        menu = ("New...", "Open", "Move...", "Copy...", "Delete", "Properties...", "Run...", "Exit Windows...")
        self.settle("filemenu", menu)
        self.expect("filemenu", *menu)
        self.key("Escape", 4)
        self.key("Escape", 4)
        self.settle("menuclosed")
        self.identical("desktop", "menuclosed", "File menu closed: every cell as on the desktop before")
        # 5. Run dialog, Notepad, typing
        self.key("alt+f", 8)
        self.key("r", 8)
        run = ("Run", "Command Line:", "Run Minimized", "OK", "Cancel")
        self.settle("rundlg", run)
        self.expect("rundlg", *run)
        self.key("Escape", 6)
        line = "Hello from 80x25 text mode!"
        if self.prof:
            self.runcmd("C:\\T80\\TPROF NOTE 90 240")
        else:
            self.free_memory("before_notepad")
            self.type_speed("edit")
            self.type_speed("edit", mode="LINES")
            self.runcmd("NOTEPAD")
        self.settle("notepad0", ("Notepad - (untitled)",), timeout=1200)
        if self.prof:
            t0 = time.time()
            while time.time() - t0 < 600 and b"READY" not in self.read("::/T80/TPROF.LOG"):
                time.sleep(5)
        t0 = time.time()
        self.text(line, 2)
        rec = self.settle("notepad", ("Notepad - (untitled)", line), timeout=1200)
        self.timing["typed_line_until_settled"] = round(time.time() - t0, 1)
        self.expect("notepad", "Notepad - (untitled)", "File", "Edit", "Search", "Help", line)
        if rec:
            hits = CHK.find(rec["hidden"], 80, line)
            if hits:
                rr, cc = hits[0]
                attrs = {(w >> 8) if (w & 0xFF) != 0x20 else ((w >> 8) & 0xF0) | 0x0 for w in CHK.cells_at(rec["hidden"], 80, rr, cc, len(line))}
                self.check("notepad: the typed line is one colour pair, black on white (F0h)",
                           attrs <= {0xF0}, attrs=sorted(hex(a) for a in attrs), at=[rr, cc])
        # 6. selection, by a mouse drag over the line (on the XT keyboard
        # 86Box delivers Shift+Home as a plain Home: no selection)
        hits0 = CHK.find(rec["hidden"], 80, line) if rec else []
        if hits0:
            rr0, cc0 = hits0[0]
            r.rehome(8 * cc0 + 1, 8 * rr0 + 3, 2)
            r.m("down")
            time.sleep(2)
            r.m("move", 8 * len(line) - 2, 0)
            time.sleep(3)
            r.m("up")
            time.sleep(4)
            r.home()
        sel = self.settle("selected", (line,))
        if rec and sel:
            hits = CHK.find(rec["hidden"], 80, line)
            if hits:
                rr, cc = hits[0]
                before = CHK.cells_at(rec["hidden"], 80, rr, cc, len(line))
                after = CHK.cells_at(sel["hidden"], 80, rr, cc, len(line))
                self.check("selection: the selected cells keep their characters and all change colour",
                           all((a & 0xFF) == (b & 0xFF) and (a >> 8) != (b >> 8) for a, b in zip(before, after)),
                           before=hex(before[0]), after=hex(after[0]))
        self.key("End", 6)
        self.settle("unselected", (line,))
        # 7. Edit menu
        self.key("alt+e", 8)
        edit = ("Undo", "Cut", "Copy", "Paste", "Delete", "Select All", "Time/Date", "Word Wrap")
        self.settle("editmenu", edit)
        self.expect("editmenu", *edit)
        self.key("Escape", 4)
        self.key("Escape", 4)
        self.settle("editclosed", (line,))
        caret = set()
        if rec:
            hits = CHK.find(rec["hidden"], 80, line)
            if hits:
                rr, cc = hits[0]
                caret = {(rr + d, cc + len(line)) for d in (-1, 0, 1)}
        self.identical("unselected", "editclosed", "Edit menu closed: every cell as before (caret cells apart)",
                       allow=caret)
        # 8. scrolling: 30 numbered lines
        for i in range(1, 31):
            self.key("Return", 1)
            self.text(f"line {i:02d}", 1)
            if i % 5 == 0:                       # keep the keyboard queue short
                self.settle(f"lines{i}", (f"line {i:02d}",), timeout=900)
        sc = self.settle("scrolled", ("line 30",), timeout=2400)
        rows = CHK.rows(sc["hidden"], 80) if sc else []
        self.check("scrolling: the last line is visible and the first typed line has scrolled away",
                   bool(sc) and any("line 30" in rw for rw in rows) and not any(line in rw for rw in rows))
        # 9. drag Notepad by its title bar with the mouse
        if sc:
            t = CHK.find(sc["hidden"], 80, "Notepad - (untitled)")
            if t:
                tr, tc = t[0]
                x, y = 8 * (tc + 2) + 3, 8 * tr + 3
                r.rehome(x, y, 2)
                r.m("down")
                time.sleep(2)
                r.m("move", 0, 24)
                time.sleep(3)
                r.m("move", -40, 0)
                time.sleep(3)
                r.m("up")
                time.sleep(5)
                mv = self.settle("dragged", ("Notepad - (untitled)",), timeout=1200)
                t2 = CHK.find(mv["hidden"], 80, "Notepad - (untitled)") if mv else []
                # GridGranularity=1 snaps the window's left edge to 8 pixels,
                # so a 40-pixel drag moves it 4 or 5 cells
                self.check("drag: the title moved 3 cell rows down and 4-5 cell columns left (8-pixel grid)",
                           bool(t2) and t2[0][0] == tr + 3 and tc - 5 <= t2[0][1] <= tc - 4,
                           before=[tr, tc], after=t2[:1])
        # 10. overlapping windows: Program Manager to the front, then Notepad
        self.key("alt+Escape", 8)
        pm = self.settle("pmfront", ("Program Manager",))
        self.key("alt+Escape", 8)
        np = self.settle("npfront", ("Notepad - (untitled)",))
        self.check("overlap: switching windows changes which one is on top (cells differ), and back",
                   bool(pm and np) and pm["hidden"] != np["hidden"] and
                   bool(CHK.find(pm["hidden"], 80, "Program Manager")) and
                   bool(CHK.find(np["hidden"], 80, "Notepad - (untitled)")))
        # 11. exit and relaunch
        self.key("alt+F4", 8)
        self.settle("savequery", ("No",), timeout=600)
        self.key("n", 10)
        self.key("alt+F4", 8)
        self.wait_shot("exitdlg", 90)
        self.key("Return", 60)
        r.shot("dos_after", settle=1, decode=False)
        self.start_windows("desktop2", desk)
        self.identical("desktop", "desktop2", "relaunch: the desktop is identical to the first launch")
        if not rollback:
            return
        # 12. rollback from DOS: T80OFF, then Windows with the previous driver
        self.key("alt+F4", 8)
        self.wait_shot("exitdlg2", 90)
        self.key("Return", 60)
        self.text("CD \\T80", 1)
        self.key("Return", 2)
        self.text("T80OFF", 1)
        self.key("Return", 25)
        r.shot("t80off", settle=1, decode=False)
        sysini = self.read("::/WINDOWS/SYSTEM.INI").decode("latin1")
        self.check("T80OFF: SYSTEM.INI no longer names TEXT80.DRV and the backups are gone",
                   "TEXT80" not in sysini.upper() and not self.read("::/WINDOWS/SYSTEM.T80"))
        rec = self.start_windows("rolledback", ("Program Manager",))
        self.check("rollback: Windows starts with the previous driver (BIOS columns no longer 80)",
                   bool(rec) and rec["cols"] != 80, cols=rec and rec["cols"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vm", required=True)
    ap.add_argument("--prof", action="store_true")
    ap.add_argument("--skip-rollback", action="store_true")
    ap.add_argument("--profile", choices=("25", "pan", "allocfail", "vga"), default="25")
    ap.add_argument("--emulator", choices=("86box", "dosbox"), default="86box",
                    help="dosbox: DOSBox-X machine=vgaonly (T80DBX.PY), started and stopped here")
    ap.add_argument("--dosbox", default="/usr/bin/dosbox-x")
    a = ap.parse_args()
    s = Session(a.vm, a.prof)
    dbx = None
    if a.emulator == "dosbox":
        DBXM = importlib.machinery.SourceFileLoader("t80dbx", str(HERE / "T80DBX.PY")).load_module()
        dbx = DBXM.DBX(a.vm, a.dosbox)
        s.r = dbx
        dbx.start()
    try:
        {"pan": s.run_pan, "allocfail": s.run_allocfail, "vga": s.run_vga}.get(a.profile, s.run)(
            rollback=not a.skip_rollback)
    finally:
        if dbx:
            dbx.stop()
        (s.vm / "T80WIN.JSN").write_text(json.dumps(s.result(), indent=1) + "\n")
        (s.vm / "SNAPS.BIN").write_bytes(s.read("::/T80/SNAPS.BIN"))
        if a.prof:
            (s.vm / "TPROF.LOG").write_bytes(s.read("::/T80/TPROF.LOG"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
