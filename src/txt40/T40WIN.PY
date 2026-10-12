#!/usr/bin/env python3
"""Scripted 86Box qualification of TXT40.DRV (IBM XT, IBM CGA, Windows 3.0).

  python3 src/txt40/T40WIN.PY --vm <prepared and started VM> --font <CGA font>
      [--tv]

The VM is prepared by src/pcp/PCP86.PY (--target txt40 --fonts ... --grid 1
--only-8x8 --mouse pty, plus --tv for a composite monitor) and started with
the PCPMOUSE pty helper, at the DOS prompt. Keys and mouse go in through
xdotool and the serial mouse; screens come back as 86Box screenshots.

RGB runs: every capture is decoded exactly (SHOTDEC) and read back as
40x25 text (T40SHOT); each step waits until two captures in a row are
identical ("settled") and records how long that took. Checks:
  desktop text, File menu text, menu closed = desktop again (identical),
  Run dialog text, Notepad title/menus/typed line, Edit menu text and
  closed = Notepad again, Notepad moved by keyboard keeps its text,
  mouse cursor = exactly the hot spot's cell with attribute XOR 77h,
  exit to DOS (T40ID reads the mode back), second launch = first desktop.
--tv runs the same steps on composite output and only keeps the pictures
(composite colour artifacts cannot be decoded back to cells).
Writes <vm>/T40WIN.JSN.
"""
import argparse
import importlib.machinery
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PCPWIN = importlib.machinery.SourceFileLoader("pcpwin", str(HERE.parent / "pcp" / "PCPWIN.PY")).load_module()
SHOT = importlib.machinery.SourceFileLoader("t40shot", str(HERE / "T40SHOT.PY")).load_module()


class Session:
    def __init__(self, vm, font, tv):
        self.r = PCPWIN.Run(vm, None, None, width=320, target="pcp")
        self.r.tdir, self.r.tid = "T40", "T40ID"
        self.vm = Path(vm)
        self.font = font
        self.tv = tv
        self.checks = []
        self.frames = {}
        self.timing = {}

    def raw(self, name):
        self.r.shot(name, settle=0.5, decode=False)
        return self.r.b.out / (name + ".png")

    def settle(self, name, timeout=240, every=8):
        """Capture until two captures in a row are identical."""
        t0 = time.time()
        prev = None
        n = 0
        while True:
            n += 1
            path = self.raw(f"{name}" if self.tv else f"{name}_{n}")
            if self.tv:
                return None
            frame = SHOT.decode(path)
            if prev is not None and frame == prev:
                self.frames[name] = frame
                self.timing[name] = round(time.time() - t0, 1)
                (self.r.b.out / f"{name}_{n}.png").rename(self.r.b.out / f"{name}.png")
                return frame
            prev = frame
            if time.time() - t0 > timeout:
                self.check(f"{name}: screen settles within {timeout} s", False)
                self.frames[name] = frame
                return frame
            time.sleep(every)

    def check(self, what, ok, **kw):
        self.checks.append(dict(check=what, result="PASS" if ok else "FAIL", **kw))
        print(("PASS " if ok else "FAIL ") + what, flush=True)

    def expect(self, name, *strings):
        if self.tv:
            return
        rows = SHOT.rows(self.frames[name], self.font)
        (self.r.b.out / (name + ".txt")).write_text("\n".join(rows) + "\n")
        for s in strings:
            self.check(f"{name}: shows '{s}'", any(s in row for row in rows))

    def same(self, a, b, what):
        if not self.tv:
            self.check(what, self.frames[a] == self.frames[b])

    def cursor(self, a, b, ca, cb):
        """Frames a and b differ exactly in cells ca and cb, each by XOR 77h."""
        if self.tv:
            return
        fa, fb = self.frames[a], self.frames[b]
        diff = set()
        for i in range(64000):
            if fa[i] != fb[i]:
                diff.add(((i // 320) >> 3, (i % 320) >> 3))
        ok = diff == {ca, cb}
        for (cy, cx) in (ca, cb):
            for r in range(8):
                for c in range(8):
                    i = (8 * cy + r) * 320 + 8 * cx + c
                    ok = ok and fa[i] == fb[i] ^ 7
        self.check(f"mouse cursor: only cells {ca} and {cb} change, each by attribute XOR 77h", ok,
                   changed_cells=sorted(diff))

    def run(self):
        r = self.r
        r.text("CD \\WINDOWS")
        r.key("Return", wait=2)
        r.m("ident", "on")
        r.text("WIN /R")
        r.key("Return", wait=120)
        r.m("ident", "off")
        for _ in range(6):            # damaged EGA-era group files: one message each
            r.key("Escape", wait=10)
        r.home()
        self.settle("desktop", timeout=400)
        self.expect("desktop", "Program Manager", "File", "Options", "Window", "Help")

        r.key("alt+f", wait=5)
        self.settle("filemenu")
        self.expect("filemenu", "New...", "Open", "Move...", "Copy...", "Delete", "Properties...",
                    "Run...", "Exit Windows...")
        r.key("Escape", wait=3)
        r.key("Escape", wait=3)
        self.settle("menuclosed")
        self.same("desktop", "menuclosed", "File menu closed: screen identical to the desktop before")

        # mouse cursor on the wallpaper (colour bars, bottom left)
        r.to(4, 180, wait=3)
        self.settle("cursor_a")
        r.to(44, 180, wait=3)
        self.settle("cursor_b")
        self.cursor("cursor_a", "cursor_b", (22, 0), (22, 5))
        r.home()

        r.key("alt+f", wait=5)
        r.key("r", wait=8)
        self.settle("rundlg")
        self.expect("rundlg", "Run", "Command Line:", "Run Minimized", "OK", "Cancel")
        r.text("NOTEPAD")
        r.key("Return", wait=40)
        self.settle("notepad0", timeout=400)
        r.text("Hello TV owners! 40x25", wait=4)
        self.settle("notepad", timeout=400)
        self.expect("notepad", "Notepad - (untitled)", "File", "Edit", "Search", "Help",
                    "Hello TV owners! 40x25")
        r.key("alt+e", wait=5)
        self.settle("editmenu")
        self.expect("editmenu", "Undo", "Cut", "Copy", "Paste", "Delete", "Select All",
                    "Time/Date", "Word Wrap")
        r.key("Escape", wait=3)
        r.key("Escape", wait=3)
        self.settle("editclosed")
        self.same("notepad", "editclosed", "Edit menu closed: screen identical to Notepad before")

        # keyboard move: screen-to-screen BitBlt carries the text hints along
        r.key("alt+space", wait=4)
        r.key("m", wait=3)
        r.key("Down", "Down", "Down", "Down", "Right", "Right", "Right", "Right", wait=3)
        r.key("Return", wait=20)
        self.settle("moved", timeout=400)
        self.expect("moved", "Notepad - (untitled)", "Hello TV owners! 40x25")
        if not self.tv:
            self.check("moved: Notepad is somewhere else",
                       self.frames["moved"] != self.frames["notepad"])

        r.key("alt+F4", wait=6)
        r.key("n", wait=20)
        self.settle("closed", timeout=400)
        r.click(*PCPWIN.PM_TITLE, wait=6)
        r.key("alt+F4", wait=8)
        self.settle("exitdlg")
        self.expect("exitdlg", "This will end your Windows session.")
        r.key("Return", wait=40)
        r.text("C:\\T40\\T40ID")
        r.key("Return", wait=10)
        self.raw("dos_after")

        r.text("CD \\WINDOWS")
        r.key("Return", wait=2)
        r.m("ident", "on")
        r.text("WIN /R")
        r.key("Return", wait=120)
        r.m("ident", "off")
        for _ in range(6):
            r.key("Escape", wait=10)
        r.home()
        self.settle("desktop2", timeout=400)
        self.same("desktop", "desktop2", "second launch: desktop identical to the first")
        r.click(*PCPWIN.PM_TITLE, wait=6)
        r.key("alt+F4", wait=8)
        r.key("Return", wait=40)
        r.text("C:\\T40\\T40ID")
        r.key("Return", wait=10)
        self.raw("dos_end")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm", required=True)
    ap.add_argument("--font", type=Path)
    ap.add_argument("--tv", action="store_true")
    a = ap.parse_args()
    font = a.font.read_bytes() if a.font else None
    if not a.tv and (font is None or len(font) != 2048):
        raise SystemExit("T40WIN: RGB runs need --font (2048-byte CGA font)")
    s = Session(a.vm, font, a.tv)
    try:
        s.run()
    finally:
        res = {"tv": a.tv, "checks": s.checks, "settle_seconds": s.timing,
               "passed": sum(c["result"] == "PASS" for c in s.checks),
               "failed": sum(c["result"] == "FAIL" for c in s.checks)}
        (Path(a.vm) / "T40WIN.JSN").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "checks"}, indent=1))
    return 0 if all(c["result"] == "PASS" for c in s.checks) else 1


if __name__ == "__main__":
    sys.exit(main())
