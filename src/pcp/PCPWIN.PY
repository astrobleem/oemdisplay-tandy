#!/usr/bin/env python3
"""Scripted Windows 3.0 session for PCP3216.DRV on an 86Box ColorPlus XT,
or with --width 640 --target pc1512 for PC1512.DRV on 86Box's PC1512.

  python3 src/pcp/PCPWIN.PY --vm <prepared --mouse pty VM> --box <AppRun> --roms <dir>

Runs one complete session and saves exact 320x200 (or 640x200) frames
(SHOTDEC) and raw 86Box captures to <vm>/dec, plus a step log <vm>/RUN.JSN.
It judges nothing itself except whether a palette-arrow pointer landed
(re-sent if not, logged in <vm>/LANDING.JSN); PCPCHK.PY checks the frames
afterwards. Input is byte-exact: keys
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

# Screen layouts, measured from exact frames of each setup. use_width()
# selects one and binds the module names below; 320 is the default.
LAYOUTS = {
    320: dict(  # Plantronics ColorPlus 320x200x16 (PCP3216.DRV)
        PAL_X0=78, PAL_PITCH=17, PAL_Y=(189, 195),
        PALETTE={15: (0, 0), 12: (0, 2), 14: (0, 3), 10: (0, 4), 11: (0, 5), 9: (0, 6), 13: (0, 7),
                 0: (1, 0), 7: (1, 1), 4: (1, 2), 6: (1, 3), 2: (1, 4), 3: (1, 5), 1: (1, 6),
                 5: (1, 7), 8: (1, 9)},
        FILLED_BOX=(24, 117), PARK=(319, 199),
        PM_TITLE=(250, 45),      # Program Manager title bar, clear of the test windows
        NOTEPAD_TITLE=(30, 5),   # full-screen Notepad's title, left of Program Manager
        MENU_FILE=(82, 60), CALC_TITLE=(90, 7), CALC_DRAG=(60, 40),
        CALC_TPL=(2, 1, 170, 9),  # title-bar template inside Calculator at (0,0)
        BOX=(40, 31, 52, 60, 28, 54),  # x0, x step, y0, y step, width, height
        CANVAS=(37, 49, 290, 170), CANVAS_ORIGIN=(36, 48),
        ICON=(100, 140)),        # minimized Program Manager: x < 100, y >= 140
    640: dict(  # Amstrad PC1512 640x200x16 (PC1512.DRV), measured in 86Box
        PAL_X0=152, PAL_PITCH=35, PAL_Y=(186, 193),
        PALETTE={15: (0, 0), 12: (0, 2), 14: (0, 3), 10: (0, 4), 11: (0, 5), 9: (0, 6), 13: (0, 7),
                 0: (1, 0), 7: (1, 1), 4: (1, 2), 6: (1, 3), 2: (1, 4), 3: (1, 5), 1: (1, 6),
                 5: (1, 7), 8: (1, 9)},
        FILLED_BOX=(43, 109), PARK=(639, 199),
        PM_TITLE=(450, 45),      # right of Calculator (x 152-413) on Program Manager's title
        NOTEPAD_TITLE=(500, 5),  # Notepad's title bar, above Program Manager (y >= 36)
        MENU_FILE=(90, 60), CALC_TITLE=(300, 6), CALC_DRAG=(60, 40),
        CALC_TPL=(154, 1, 411, 9),  # Calculator opens at x 152: its title bar rows
        BOX=(80, 64, 45, 62, 56, 54),
        CANVAS=(64, 33, 605, 171), CANVAS_ORIGIN=(64, 33),
        ICON=(180, 160)),        # minimized Program Manager: x < 180, y >= 160
}
WIDTH = 320
LANDING_TRIES = 8     # palette-arrow moves re-sent at most this often
LANDING_WAIT = 20     # seconds between tries


def use_width(width):
    global WIDTH
    if width not in LAYOUTS:
        raise SystemExit(f"PCPWIN: no measured layout for width {width}")
    WIDTH = width
    globals().update(LAYOUTS[width])


use_width(320)


def rect(i):
    """Screen rectangle for colour i: two rows of eight filled boxes, given as
    press point and release point (Paintbrush fills up to, not including,
    the release point)."""
    x0, xs, y0, ys, w, h = BOX
    col, row = i % 8, i // 8
    x = x0 + xs * col
    y = y0 + ys * row
    return x, y, x + w - 1, y + h - 1


class Run:
    TARGETS = {"pcp": ("PCP", "PCPID", "PCPSHOW"), "pc1512": ("P15", "P15ID", "P15SHOW")}

    def __init__(self, vm, box, roms, width=320, display=":79", target="pcp"):
        use_width(width)
        self.tdir, self.tid, self.tshow = self.TARGETS[target]
        self.vm = Path(vm)
        self.width = width
        self.box, self.roms = box, roms
        self.b = P.Box(self.vm, display=display, width=width)
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

    def sync(self, token, timeout=180):
        """Return once PCPMOUSE has sent every earlier command in full."""
        f = self.vm / "mouse.sync"
        if f.exists():
            f.unlink()
        self.m("sync", token)
        for _ in range(timeout * 4):
            if f.exists() and f.read_text().strip() == token:
                return
            time.sleep(0.25)
        raise SystemExit("PCPWIN: mouse helper did not reach sync " + token)

    def home(self):
        self.m("move", -(self.width + 80), -300)
        time.sleep(3)
        self.cx, self.cy = 0, 0

    def to(self, x, y, wait=2.5):
        assert 0 <= x < self.width and 0 <= y <= 199
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

    def frame(self, name):
        from PIL import Image
        with Image.open(self.b.out / (name + ".png")) as im:
            return im.tobytes()

    def wall_glyph(self):
        """Arrow pixels relative to the hotspot, merged from the 16
        wallpaper frames (each bar hides the glyph pixels of its own
        colour); PCPCHK verifies this glyph against the driver resource."""
        wall, w, bar = self.frame("wall_parked"), self.width, self.width // 16
        glyph = {}
        for c in range(16):
            f = self.frame(f"warrow_{c:02d}")
            hx = c * bar + bar // 2
            for i in range(w * 200):
                if f[i] != wall[i] and not (i % w >= w - 4 and i // w >= 196):
                    glyph[(i % w - hx, i // w - 100)] = f[i]
        return [(dx, dy, v) for (dx, dy), v in glyph.items()]

    def landed(self, name, ref, glyph, hx, hy):
        """Frame equals ref with the glyph at (hx, hy); the parked-cursor
        corner is ignored, as in PCPCHK."""
        exp = bytearray(ref)
        for dx, dy, v in glyph:
            x, y = hx + dx, hy + dy
            if 0 <= x < self.width and 0 <= y < 200:
                exp[y * self.width + x] = v
        f = self.frame(name)
        w = self.width
        return all(f[i] == exp[i] for i in range(w * 200)
                   if not (i % w >= w - 4 and i // w >= 196))

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
        self.text("C:\\%s\\%s" % (self.tdir, self.tid))
        self.key("Return", wait=8)
        self.shot(tag + "_dos", decode=False)

    def scenario(self):
        b = self.b
        subprocess.run(["xdotool", "mousemove", "600", "400"])
        self.log("boot")
        # 0. Pre-Windows: identification and colour bars.
        self.text("CD \\" + self.tdir)
        self.key("Return", wait=2)
        self.text(self.tshow)
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

        # 2b. Wallpaper: Program Manager minimized, the BARS16.BMP wallpaper
        #     (16 vertical bars, IRGB 0..15) fills the screen. The arrow is
        #     placed over the middle of every bar, then the mouse drift
        #     trials run over it, then Program Manager is restored.
        self.key("alt+space", wait=5)
        self.key("n", wait=30)
        self.rehome(*PARK, wait=6)
        self.shot("wall_parked")
        bar = self.width // 16
        for c in range(16):
            self.rehome(c * bar + bar // 2, 100, wait=4)
            self.shot(f"warrow_{c:02d}", settle=1)
        # Drift: home, then 40 separate packets of (+5,+3) at a given pacing;
        # the capture waits until PCPMOUSE has sent every byte, then settles.
        trials = [("1200-baud bytes, 20 ms between packets", 7.5, 20),
                  ("1200-baud bytes, 20 ms between packets (repeat)", 7.5, 20),
                  ("30 ms between bytes, 20 ms between packets", 30, 20),
                  ("1200-baud bytes, 300 ms between packets", 7.5, 300)]
        self.drift = []
        for k, (label, bms, gms) in enumerate(trials):
            self.m("pace", 7.5, 20)
            self.home()
            self.m("pace", bms, gms)
            self.m("burst", 40, 5, 3)
            self.sync(f"drift{k}")
            self.m("pace", 7.5, 20)
            self.cx, self.cy = 200, 120
            self.shot(f"drift_{k}", settle=6)
            self.drift.append({"trial": label, "byte_ms": bms, "gap_ms": gms,
                               "packets": 40, "each": [5, 3], "expected_hotspot": [200, 120],
                               "frame": f"drift_{k}"})
        (self.vm / "DRIFT.JSN").write_text(json.dumps(self.drift, indent=1) + "\n")
        self.rehome(*PARK, wait=4)
        self.key("alt+space", wait=5)        # minimized Program Manager's menu
        self.key("r", wait=40)               # Restore
        self.rehome(*PARK, wait=6)
        self.shot("pm_restored")

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
        self.drag(*self.calc_title, self.calc_title[0] + CALC_DRAG[0], self.calc_title[1] + CALC_DRAG[1],
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

        # 5. Arrow cursor over every palette colour. Each frame must show the
        #    arrow (the glyph measured over the wallpaper) exactly at the
        #    hotspot that was sent; if it does not, the pointer did not land
        #    there (see docs/PC1512.MD, "Pointer landing"), so the frame is
        #    kept as arrow_NN_missK, logged, and the move is sent again.
        #    PCPCHK judges only the final frames, with the same strict rule.
        glyph = self.wall_glyph()
        ref = self.frame("pb_drawn")
        self.landing = []
        for c in range(16):
            r, k = PALETTE[c]
            hx, hy = PAL_X0 + PAL_PITCH * k, PAL_Y[r]
            name = f"arrow_{c:02d}"
            for attempt in range(1, LANDING_TRIES + 1):
                self.rehome(hx, hy, wait=4)
                self.shot(name, settle=1)
                if self.landed(name, ref, glyph, hx, hy):
                    break
                miss = f"{name}_miss{attempt}"
                (self.b.out / (name + ".png")).rename(self.b.out / (miss + ".png"))
                self.log("pointer did not land: " + miss, frame=miss, hotspot=[hx, hy])
                time.sleep(LANDING_WAIT)
            self.landing.append({"frame": name, "hotspot": [hx, hy], "attempts": attempt})
        (self.vm / "LANDING.JSN").write_text(json.dumps(self.landing, indent=1) + "\n")
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
    ap.add_argument("--width", type=int, default=320, choices=sorted(LAYOUTS))
    ap.add_argument("--display", default=":79")
    ap.add_argument("--target", default="pcp", choices=["pcp", "pc1512"])
    ap.add_argument("--menu-file", help="x,y of Program Manager's File menu (default: layout)")
    ap.add_argument("--calc-title", help="x,y on Calculator's title bar (default: layout)")
    a = ap.parse_args()
    r = Run(a.vm, a.box, a.roms, a.width, a.display, a.target)
    r.menu_file = tuple(int(v) for v in a.menu_file.split(",")) if a.menu_file else MENU_FILE
    r.calc_title = tuple(int(v) for v in a.calc_title.split(",")) if a.calc_title else CALC_TITLE
    r.scenario()
    return 0


if __name__ == "__main__":
    sys.exit(main())
