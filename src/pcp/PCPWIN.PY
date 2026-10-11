#!/usr/bin/env python3
"""Scripted Windows 3.0 session for PCP3216.DRV on an 86Box ColorPlus XT.

  python3 src/pcp/PCPWIN.PY --vm <prepared --mouse pty VM> --box <AppRun> --roms <dir>

Runs one complete session and saves exact 320x200 frames (SHOTDEC) and raw
86Box captures to <vm>/dec, plus a step log <vm>/RUN.JSN. It judges nothing
itself; PCPCHK.PY checks the frames afterwards. Input is byte-exact: keys
through xdotool, mouse packets through PCPMOUSE.PY on a COM1 pty (one
mickey is one pixel with WIN.INI MouseSpeed=0). Expect about 40 minutes at
4.77 MHz.

Prerequisites: Xvfb on --display (default :79, 1600x1200x24), xdotool,
mtools, the VM from  PCP86.PY prepare --mouse pty, and PCPMOUSE.PY serve
already running for that VM.
"""
import argparse
import importlib.machinery
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader("pcp86", str(HERE / "PCP86.PY")).load_module()

# Maximized Paintbrush layout (measured from an exact frame of this setup).
PAL_X0, PAL_PITCH, PAL_Y = 78, 17, (189, 195)
PALETTE = {15: (0, 0), 12: (0, 2), 14: (0, 3), 10: (0, 4), 11: (0, 5), 9: (0, 6), 13: (0, 7),
           0: (1, 0), 7: (1, 1), 4: (1, 2), 6: (1, 3), 2: (1, 4), 3: (1, 5), 1: (1, 6),
           5: (1, 7), 8: (1, 9)}
FILLED_BOX = (24, 117)
PARK = (319, 199)
PM_TITLE = (250, 45)    # Program Manager title bar, clear of the test windows
NOTEPAD_TITLE = (30, 5) # full-screen Notepad's title, left of Program Manager


def rect(i):
    """Screen rectangle for color i: two rows of eight 28x54 boxes."""
    col, row = i % 8, i // 8
    x0 = 40 + 31 * col
    y0 = 52 + 60 * row
    return x0, y0, x0 + 27, y0 + 53


class Run:
    def __init__(self, vm, box, roms):
        self.vm = Path(vm)
        self.box, self.roms = box, roms
        self.b = P.Box(self.vm)
        self.steps = []
        self.cx = self.cy = None

    def log(self, what, **kw):
        kw.update(step=what, t=round(time.time(), 1))
        self.steps.append(kw)
        (self.vm / "RUN.JSN").write_text(json.dumps(self.steps, indent=1) + "\n")
        print(what, flush=True)

    def m(self, *words):
        subprocess.run([sys.executable, str(HERE / "PCPMOUSE.PY"), "send", "--vm", str(self.vm),
                        *map(str, words)], check=True)

    def home(self):
        self.m("move", -400, -300)
        time.sleep(3)
        self.cx, self.cy = 0, 0

    def to(self, x, y, wait=2.5):
        assert 0 <= x <= 319 and 0 <= y <= 199
        self.m("move", x - self.cx, y - self.cy)
        self.cx, self.cy = x, y
        time.sleep(wait)

    def rehome(self, x, y, wait=1.5):
        """Dead reckoning goes stale whenever Windows or an application
        confines the cursor (title-bar moves, Paintbrush shape drags), so
        every click or drag first pins the cursor at (0,0) again."""
        self.home()
        self.to(x, y, wait=wait)

    def click(self, x, y, wait=4):
        self.rehome(x, y)
        self.m("click")
        time.sleep(wait)

    def rclick(self, x, y, wait=4):
        # Right button: PCPMOUSE only drives the left one, so use a packet
        # with bit 4 set via the raw "rbtn" helper below.
        self.rehome(x, y)
        self.m("rclick")
        time.sleep(wait)

    def drag(self, x0, y0, x1, y1, wait=6, press_wait=1, steps=1):
        """press_wait: a click on an inactive window repaints it before
        Windows starts tracking; at 4.77 MHz that takes seconds, and a
        release that arrives first ends the drag before it begins."""
        self.rehome(x0, y0)
        self.m("down")
        time.sleep(press_wait)
        for k in range(1, steps + 1):
            self.to(x0 + (x1 - x0) * k // steps, y0 + (y1 - y0) * k // steps,
                    wait=2 if steps == 1 else 4)
        self.m("up")
        time.sleep(wait)

    def shot(self, name, settle=2.0, decode=True):
        self.b.shot(name, settle=settle, decode=decode)
        self.log("shot " + name, frame=name, decoded=decode, source=self.b.log[-1]["source"])

    def key(self, *k, wait=3):
        self.b.key(*k, wait=wait)

    def text(self, s, wait=1):
        self.b.type(s, wait=wait)

    def run_cmd(self, cmd, wait):
        # Keystrokes go to the active window: make Program Manager active.
        self.click(*PM_TITLE, wait=5)
        self.key("alt+f", wait=4)
        self.key("r", wait=8)
        self.text(cmd)
        self.key("Return", wait=wait)

    def start_windows(self, tag):
        self.text("CD \\WINDOWS")
        self.key("Return", wait=2)
        self.m("ident", "on")
        self.text("WIN /R")
        self.key("Return", wait=130)
        self.m("ident", "off")
        # Program Manager reports its EGA-era group files as damaged; one
        # Escape per message box. Escape (not Return) so nothing launches.
        for _ in range(6):
            self.key("Escape", wait=8)
        self.rehome(*PARK, wait=6)
        self.shot(tag + "_desktop")

    def exit_windows(self, tag):
        self.click(*PM_TITLE, wait=5)
        self.key("alt+F4", wait=8)
        self.shot(tag + "_exitdlg")
        self.key("Return", wait=30)
        self.text("C:\\PCP\\PCPID")
        self.key("Return", wait=8)
        self.shot(tag + "_dos", decode=False)

    def scenario(self):
        b = self.b
        subprocess.run(["xdotool", "mousemove", "600", "400"])
        self.log("boot")
        # 0. Pre-Windows: identification and colour bars.
        self.text("CD \\PCP")
        self.key("Return", wait=2)
        self.text("PCPSHOW")
        self.key("Return", wait=20)
        self.shot("bars")
        self.key("space", wait=6)
        self.text("CD \\")
        self.key("Return", wait=2)

        # 1. First Windows session.
        self.start_windows("s1")
        # 2. Menus and dialogs, keyboard and mouse.
        self.key("alt+f", wait=6)
        self.shot("menu_file_kbd")
        self.key("Escape", wait=3)
        self.key("Escape", wait=5)
        self.shot("menu_closed")
        self.key("alt+h", wait=5)
        self.key("a", wait=12)
        self.shot("about")
        self.key("Return", wait=8)
        self.to(*PARK, wait=3)
        self.shot("about_closed")
        self.log("mouse: click Program Manager File menu")
        self.click(*self.menu_file, wait=6)
        self.shot("menu_file_mouse")
        self.key("Escape", wait=3)
        self.key("Escape", wait=5)
        self.to(*PARK, wait=3)
        self.shot("menu_mouse_closed")

        # 3. Overlapping windows: Notepad (full screen) under Program Manager
        #    under Calculator; the active Calculator is dragged with the
        #    mouse, then both applications are closed. Calculator's rounded
        #    buttons take tens of seconds to paint at 4.77 MHz, so each step
        #    waits for repainting to finish before the next input.
        self.run_cmd("NOTEPAD", wait=60)
        self.shot("notepad")
        self.key("alt+Tab", wait=20)         # back to Program Manager
        self.key("alt+f", wait=4)
        self.key("r", wait=8)
        self.text("CALC")
        self.key("Return", wait=90)
        self.shot("calc_over_pm_notepad")
        self.log("mouse: drag the active Calculator by its title bar")
        self.drag(*self.calc_title, self.calc_title[0] + 60, self.calc_title[1] + 40,
                  wait=60, press_wait=4, steps=2)
        self.shot("calc_moved")
        self.key("alt+F4", wait=60)          # Calculator (active)
        self.shot("calc_closed")
        self.click(*NOTEPAD_TITLE, wait=30)  # Notepad's title strip above Program Manager
        self.key("alt+F4", wait=40)          # Notepad
        self.rehome(*PARK, wait=6)
        self.shot("overlap_closed")

        # 4. Paintbrush: 16 filled boxes with the mouse.
        self.run_cmd("PBRUSH", wait=60)
        self.key("alt+space", wait=5)
        self.key("x", wait=45)
        self.to(*PARK, wait=4)
        self.shot("pb_empty")
        self.click(*FILLED_BOX, wait=4)
        for c in range(16):
            r, k = PALETTE[c]
            px, py = PAL_X0 + PAL_PITCH * k, PAL_Y[r]
            self.click(px, py, wait=3)        # foreground
            self.rclick(px, py, wait=3)       # background (box border)
            x0, y0, x1, y1 = rect(c)
            self.drag(x0, y0, x1, y1, wait=8)
            self.log(f"box {c}", rect=[x0, y0, x1, y1])
        self.to(*PARK, wait=6)
        self.shot("pb_drawn")

        # 5. Arrow cursor over every palette colour.
        for c in range(16):
            r, k = PALETTE[c]
            self.rehome(PAL_X0 + PAL_PITCH * k, PAL_Y[r], wait=4)
            self.shot(f"arrow_{c:02d}", settle=1)
        self.to(*PARK, wait=4)
        self.shot("arrow_parked")

        # 6. Tool cursor (crosshair) over every box.
        for c in range(16):
            x0, y0, x1, y1 = rect(c)
            self.rehome((x0 + x1) // 2, (y0 + y1) // 2, wait=4)
            self.shot(f"cross_{c:02d}", settle=1)
        self.to(*PARK, wait=4)
        self.shot("cross_parked")

        # 7. Save, close, reopen.
        self.key("alt+f", wait=5)
        self.key("a", wait=12)
        self.shot("saveas_dlg")
        self.text("TEST16.BMP")
        self.key("Return", wait=40)
        self.shot("saved")
        self.key("alt+F4", wait=20)
        self.to(*PARK, wait=4)
        self.shot("pb_closed")
        self.run_cmd("PBRUSH TEST16.BMP", wait=70)
        self.key("alt+space", wait=5)
        self.key("x", wait=50)
        self.to(*PARK, wait=6)
        self.shot("pb_reopened")
        self.key("alt+F4", wait=20)
        self.to(*PARK, wait=6)
        self.shot("pb_closed2")

        # 8. Exit, DOS, second launch, exit.
        self.exit_windows("s1")
        self.start_windows("s2")
        self.exit_windows("s2")
        self.log("done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm", required=True)
    ap.add_argument("--box", required=True)
    ap.add_argument("--roms", required=True)
    ap.add_argument("--menu-file", default="9,40", help="x,y of Program Manager's File menu")
    ap.add_argument("--calc-title", default="120,60", help="x,y on Calculator's title bar")
    a = ap.parse_args()
    r = Run(a.vm, a.box, a.roms)
    r.menu_file = tuple(int(v) for v in a.menu_file.split(","))
    r.calc_title = tuple(int(v) for v in a.calc_title.split(","))
    r.scenario()
    return 0


if __name__ == "__main__":
    sys.exit(main())
