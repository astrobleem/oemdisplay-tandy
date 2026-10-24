#!/usr/bin/env python3
"""Clipboard and grabber session for the Tandy 320x200x16 profile (86Box HX).

  python3 src/tgrab/TGSESS.PY prepare --vm <new dir> --pristine <PCJSIMG image>
      --drv <TR53216.DRV> --grabber <GR2> --tools <dir: RESERVE.COM MSTEST.COM
      XTPAN.EXE PANTEST.EXE TGPAT.COM> [--no-reserve] [--display-drv CGA.DRV]
  python3 src/tgrab/TGSESS.PY run --vm <prepared, started VM at the DOS prompt>
      [--part all|dos9|text]

Emulator evidence only (86Box 6.0 Tandy 1000 HX, src/xtpan/PCP86.PY; start
the VM and PCPMOUSE.PY serve first, as for XPWIN.PY). Keys go in through
xdotool, the mouse through PCPMOUSE.PY (exact mickeys), files come back with
mtools while the guest runs. On the HX keyboard, Print Screen is Shift +
PRINT (scan code 37h with Shift held); 86Box sends that for Shift+KP_Multiply.

Parts:
  win   Paintbrush opens TGIMG.BMP (64x40, all 16 colours, see TGIMG.PY);
        the Pick tool selects it, Edit > Copy, File > New, Edit > Paste,
        File > Save As PASTE.BMP, close, reopen. Then Shift+PRINT copies the
        Windows screen; Clipboard (CLIPBRD) saves it as C:\\SCREEN.CLP;
        Paintbrush File > New, Edit > Paste, Save As SCREEN.BMP.
  dos9  TGPAT.COM (BIOS mode 9 test picture) from File > Run; Alt+Tab to
        Windows and back; Shift+PRINT in mode 9; Space ends it; Clipboard
        saves C:\\AFTER9.CLP.
  text  COMMAND.COM, an ECHO line, Shift+PRINT, EXIT, then Clipboard;
        records whether Windows answers again and what the Clipboard holds.
Results: <vm>/TGSESS.JSN (steps, checks), frames <vm>/dec, files <vm>/got.
"""
import argparse
import importlib.machinery
import json
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
XT = HERE.parent / "xtpan"
P = importlib.machinery.SourceFileLoader("pcp86", str(XT / "PCP86.PY")).load_module()
W = importlib.machinery.SourceFileLoader("pcpwin", str(XT / "PCPWIN.PY")).load_module()
T = importlib.machinery.SourceFileLoader("tgimg", str(HERE / "TGIMG.PY")).load_module()

PART = P.PART
IMG_AT = (36, 48)        # Paintbrush canvas origin, maximized, 320x200 (PCPWIN CANVAS_ORIGIN)
PICK = (23, 53)          # Paintbrush Pick (rectangle) tool
SCISSORS = (9, 53)       # another tool: selecting it anchors a pasted object
PAT_AT = (128, 80)       # where TGPAT.COM draws the picture in mode 9
PARK = W.PARK


def win_to_tandy(i):
    """Windows device-bitmap colour index (EGA order: bit 0 blue... but the
    driver's palette lists red first) to the Tandy IRGB index on screen:
    bits 0 and 2 swap (index 1 is dark red in BMPs, IRGB 4 on screen)."""
    return (i & 10) | ((i & 1) << 2) | ((i & 4) >> 2)


# ---------------------------------------------------------------- prepare --
def prepare(a):
    vm = Path(a.vm)
    rec = P.prepare(vm, a.pristine, a.drv, a.tools, mouse="pty", target="xtbase")
    i = f"{vm / 'pcp.img'}{PART}"
    gr = Path(a.grabber)
    ini = P.mt("mtype", "-i", i, "::/WINDOWS/SYSTEM.INI").decode("latin1")
    ini = P.edit(ini, "286grabber=egacolor.gr2", "286grabber=" + gr.name.upper())
    changes = [f"SYSTEM.INI: 286grabber={gr.name.upper()} (sha256 {P.sha(gr)})"]
    if a.display_drv:
        src = Path(a.display_drv)
        ini = P.edit(ini, "display.drv=TR53216.DRV", "display.drv=" + src.name.upper())
        P.mt("mcopy", "-o", "-i", i, str(src), "::/WINDOWS/SYSTEM/" + src.name.upper())
        changes.append(f"SYSTEM.INI: display.drv={src.name.upper()} (CONTROL, sha256 {P.sha(src)})")
    (vm / "prep" / "SYSTEM.INI").write_bytes(ini.encode("latin1"))
    P.mt("mcopy", "-o", "-i", i, str(vm / "prep" / "SYSTEM.INI"), "::/WINDOWS/SYSTEM.INI")
    P.mt("mcopy", "-o", "-i", i, str(gr), "::/WINDOWS/SYSTEM/" + gr.name.upper())
    P.mt("mcopy", "-o", "-i", i, str(Path(a.tools) / "TGPAT.COM"), "::/XTPAN/TGPAT.COM")
    bars = vm / "prep" / "BARS16.BMP"
    (vm / "prep" / "TGIMG.BMP").write_bytes(T.bmp(T.read_bmp(bars.read_bytes())[3]))
    P.mt("mcopy", "-o", "-i", i, str(vm / "prep" / "TGIMG.BMP"), "::/WINDOWS/TGIMG.BMP")
    changes.append("added XTPAN/TGPAT.COM (sha256 %s) and WINDOWS/TGIMG.BMP (TGIMG.PY, palette of BARS16.BMP)"
                   % P.sha(Path(a.tools) / "TGPAT.COM"))
    if a.no_reserve:
        auto = P.mt("mtype", "-i", i, "::/AUTOEXEC.BAT").decode("latin1")
        auto = P.edit(auto, "RESERVE\r\n", "")
        (vm / "prep" / "AUTOEXEC.BAT").write_bytes(auto.encode("latin1"))
        P.mt("mcopy", "-o", "-i", i, str(vm / "prep" / "AUTOEXEC.BAT"), "::/AUTOEXEC.BAT")
        changes.append("AUTOEXEC.BAT: RESERVE removed (CONTROL only; TR53216 needs it)")
    rec["tgsess"] = {"grabber": gr.name.upper(), "grabber_sha256": P.sha(gr), "changes": changes}
    (vm / "PREP.JSN").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec["tgsess"], indent=1))


# -------------------------------------------------------------------- run --
class Sess:
    def __init__(self, vm):
        self.vm = Path(vm)
        self.r = W.Run(vm, None, None, width=320, target="pcp")
        self.got = self.vm / "got"
        self.got.mkdir(exist_ok=True)
        self.out = {"steps": [], "checks": []}

    def save(self):
        (self.vm / "TGSESS.JSN").write_text(json.dumps(self.out, indent=1) + "\n")

    def check(self, what, ok, **kw):
        kw.update(check=what, ok=bool(ok))
        self.out["checks"].append(kw)
        self.save()
        print(("PASS " if ok else "FAIL ") + what, flush=True)

    def step(self, what):
        self.out["steps"].append({"step": what, "t": round(time.time(), 1)})
        self.save()
        print(what, flush=True)

    def frame(self, name, decode=True, settle=1.5):
        self.r.shot(name, settle=settle, decode=decode)
        if decode:
            from PIL import Image
            with Image.open(self.vm / "dec" / (name + ".png")) as im:
                return im.load()

    def fetch(self, guest, name):
        dst = self.got / name
        if dst.exists():
            dst.unlink()
        p = subprocess.run(["mcopy", "-n", "-i", f"{self.vm / 'pcp.img'}{PART}", "::" + guest, str(dst)],
                           capture_output=True)
        return dst.read_bytes() if p.returncode == 0 and dst.exists() else None

    def key(self, *k, wait=3):
        self.r.key(*k, wait=wait)

    def park(self):
        self.r.rehome(*PARK, wait=3)

    def run_cmd(self, cmd, wait):
        self.r.run_cmd(cmd, wait=wait)

    @staticmethod
    def corner(x, y):
        """The parked pointer's corner, excluded as in PCPCHK."""
        return x >= 316 and y >= 196

    # -- picture checks ------------------------------------------------------
    def img_on_screen(self, px, x0, y0):
        P_ = T.pixels()
        bad = [(x, y) for y in range(40) for x in range(64)
               if px[x0 + x, y0 + y] != win_to_tandy(P_[y][x])]
        return bad

    def bmp_check(self, data, name):
        w, h, rows, pal = T.read_bmp(data)
        _, _, ref, rpal = T.read_bmp(T.bmp(pal))
        rgb = lambda p, i: p[4 * i:4 * i + 3]
        bad = sum(rgb(pal, rows[y][x]) != rgb(rpal, ref[y][x]) for y in range(40) for x in range(64))
        white = all(rgb(pal, rows[y][x]) == b"\xff\xff\xff" for y in range(h) for x in range(w)
                    if x >= 64 or y >= 40)
        return {"file": name, "width": w, "height": h, "picture_mismatches": bad, "rest_white": white}

    def clp_bitmap(self, data):
        """(width, height, planes, bits/pixel, rows of colour indices) of the
        CF_BITMAP in a Windows 3.0 .CLP file, or None."""
        fid, n = struct.unpack_from("<HH", data, 0)
        if fid != 0xC350:
            return None
        for k in range(n):
            fmt, ln, off = struct.unpack_from("<HII", data, 4 + 89 * k)
            if fmt != 2:
                continue
            _, w, h, wb, pl, bp = struct.unpack_from("<hhhhBB", data, off)
            base = off + 14
            rows = []
            for y in range(h):
                row = []
                for x in range(w):
                    v = 0
                    for p in range(pl):
                        if data[base + (y * pl + p) * wb + x // 8] >> (7 - x % 8) & 1:
                            v |= 1 << p
                    row.append(v)
                rows.append(row)
            return w, h, pl, bp, rows
        return None

    # -- parts ---------------------------------------------------------------
    def part_win(self):
        r = self.r
        self.step("Paintbrush opens TGIMG.BMP")
        self.run_cmd("PBRUSH TGIMG.BMP", wait=70)
        self.key("alt+space", wait=5)
        self.key("x", wait=50)
        self.park()
        px = self.frame("pb_img")
        bad = self.img_on_screen(px, *IMG_AT)
        self.check("TGIMG.BMP shown exactly at the canvas origin (all 2,560 pixels, every colour)",
                   not bad, mismatches=len(bad), at=list(IMG_AT))
        self.step("Pick tool selects the picture; Edit > Copy")
        r.click(*PICK, wait=4)
        r.drag(IMG_AT[0], IMG_AT[1], IMG_AT[0] + 64, IMG_AT[1] + 40, wait=8)
        self.park()
        self.frame("pb_selected")
        self.key("alt+e", wait=5)
        self.frame("pb_editmenu")
        self.key("c", wait=15)
        self.step("File > New, Edit > Paste")
        self.key("alt+f", wait=5)
        self.key("n", wait=20)
        self.key("n", wait=20)        # "Save current image?" if Paintbrush asks (selection marks it)
        self.park()
        self.frame("pb_new")
        self.key("alt+e", wait=5)
        self.key("p", wait=30)
        self.park()
        self.frame("pb_pasted")
        r.click(250, 150, wait=6)     # outside the pasted object: anchor it
        self.park()
        px = self.frame("pb_anchored")
        bad = self.img_on_screen(px, *IMG_AT)
        self.check("pasted picture anchored at the canvas origin, all pixels and colours exact",
                   not bad, mismatches=len(bad))
        self.step("File > Save As PASTE.BMP")
        self.key("alt+f", wait=5)
        self.key("a", wait=12)
        r.text("PASTE.BMP")
        self.key("Return", wait=60)
        self.frame("pb_saved")
        data = self.fetch("/WINDOWS/PASTE.BMP", "PASTE.BMP")
        res = self.bmp_check(data, "PASTE.BMP") if data else {"file": "PASTE.BMP", "missing": True}
        self.check("PASTE.BMP: the 64x40 picture at (0,0) with exactly the original colours, the rest white",
                   data and res["picture_mismatches"] == 0 and res["rest_white"], **res)
        self.step("close, reopen PASTE.BMP")
        self.key("alt+F4", wait=20)
        self.run_cmd("PBRUSH PASTE.BMP", wait=70)
        self.key("alt+space", wait=5)
        self.key("x", wait=50)
        self.park()
        px = self.frame("pb_reopened")
        bad = self.img_on_screen(px, *IMG_AT)
        self.check("reopened PASTE.BMP shows the picture exactly", not bad, mismatches=len(bad))

        self.step("Shift+PRINT: Windows screen to the Clipboard")
        src = self.frame("cap_source")
        self.key("shift+KP_Multiply", wait=40)
        self.step("Clipboard: File > Save As C:\\SCREEN.CLP")
        self.key("alt+F4", wait=20)              # Paintbrush (unchanged file)
        self.run_cmd("CLIPBRD", wait=40)
        self.frame("clipbrd_screen")
        self.key("alt+f", wait=5)
        self.key("a", wait=12)
        r.text("C:\\SCREEN.CLP")
        self.key("Return", wait=60)
        data = self.fetch("/SCREEN.CLP", "SCREEN.CLP")
        bm = self.clp_bitmap(data) if data else None
        if bm:
            w, h, pl, bp, rows = bm
            bad = [(x, y) for y in range(200) for x in range(320)
                   if not self.corner(x, y) and win_to_tandy(rows[y][x]) != src[x, y]] if (w, h) == (320, 200) else ["size"]
            self.check("Clipboard bitmap is 320x200, 4 planes x 1 bit, equal to the screen (pointer corner excluded)",
                       (w, h, pl, bp) == (320, 200, 4, 1) and not bad,
                       width=w, height=h, planes=pl, bits=bp, mismatches=len(bad))
        else:
            self.check("Clipboard bitmap saved in SCREEN.CLP", False, missing=data is None)
        self.key("alt+F4", wait=15)
        self.step("Paintbrush: File > New, Edit > Paste the screen, Save As SCREEN.BMP")
        self.run_cmd("PBRUSH", wait=70)
        self.key("alt+space", wait=5)
        self.key("x", wait=50)
        self.key("alt+e", wait=5)
        self.key("p", wait=40)
        self.park()
        self.frame("pb_screen_pasted")
        r.click(*SCISSORS, wait=8)
        self.key("alt+f", wait=5)
        self.key("a", wait=12)
        r.text("SCREEN.BMP")
        self.key("Return", wait=60)
        data = self.fetch("/WINDOWS/SCREEN.BMP", "SCREEN.BMP")
        if data:
            w, h, rows, pal = T.read_bmp(data)
            same = lambda x, y: x < 320 and y < 200 and win_to_tandy(rows[y][x]) == src[x, y]
            ww = next((x for x in range(w) if not same(x, 0)), w)
            hh = next((y for y in range(h) if not all(same(x, y) for x in range(ww))), h)
            rest = all(rows[y][x] == 15 for y in range(h) for x in range(w) if x >= ww or y >= hh)
            self.check("SCREEN.BMP: the pasted screen equals the captured screen pixel for pixel in the "
                       "part Paintbrush pastes (its drawing area); the rest of the canvas stays white",
                       ww >= 250 and hh >= 100 and rest, bmp_size=[w, h], exact_region=[ww, hh], rest_white=rest)
        else:
            self.check("SCREEN.BMP saved", False)
        self.key("alt+F4", wait=20)
        self.park()

    def part_dos9(self):
        r = self.r
        self.step("TGPAT.COM (BIOS mode 9) from File > Run")
        self.run_cmd("C:\\XTPAN\\TGPAT.COM", wait=30)
        a = self.frame("dos9_before")
        ref = [[T.f(x, y) for x in range(64)] for y in range(40)]
        bad = [(x, y) for y in range(200) for x in range(320)
               if a[x, y] != (ref[y - PAT_AT[1]][x - PAT_AT[0]]
                              if PAT_AT[0] <= x < PAT_AT[0] + 64 and PAT_AT[1] <= y < PAT_AT[1] + 40 else 0)]
        self.check("TGPAT mode-9 picture on screen exactly", not bad, mismatches=len(bad))
        self.step("Alt+Tab to Windows")
        self.key("alt+Tab", wait=60)
        self.frame("dos9_switched")
        self.step("Alt+Tab back to TGPAT")
        self.key("alt+Tab", wait=60)
        c = self.frame("dos9_after")
        bad = [(x, y) for y in range(200) for x in range(320) if a[x, y] != c[x, y]]
        self.check("after switching away and back the mode-9 screen is restored exactly (64,000 pixels)",
                   not bad, mismatches=len(bad))
        self.step("Shift+PRINT in mode 9, then Space ends TGPAT")
        self.key("shift+KP_Multiply", wait=30)
        self.frame("dos9_printed")
        self.key("space", wait=60)
        self.park()
        self.frame("dos9_ended")
        self.run_cmd("CLIPBRD", wait=40)
        self.frame("dos9_clipbrd")
        self.key("alt+f", wait=5)
        self.key("a", wait=12)
        r.text("C:\\AFTER9.CLP")
        self.key("Return", wait=60)
        before = (self.got / "SCREEN.CLP").read_bytes() if (self.got / "SCREEN.CLP").exists() else None
        after = self.fetch("/AFTER9.CLP", "AFTER9.CLP")
        self.check("a mode-9 Print Screen leaves the Clipboard as it was (Windows 3.0 real mode grabs text screens only)",
                   after is not None and (before is None or after == before),
                   unchanged=before is not None and after == before, compared=before is not None)
        self.key("alt+F4", wait=15)
        self.park()

    def part_text(self):
        r = self.r
        self.step("COMMAND.COM, ECHO, Shift+PRINT, EXIT")
        self.run_cmd("COMMAND.COM", wait=30)
        r.text("ECHO TANDY GRAB TEST")
        self.key("Return", wait=5)
        self.frame("text_screen", decode=False)
        self.key("shift+KP_Multiply", wait=30)
        r.text("EXIT")
        self.key("Return", wait=60)
        self.park()
        self.frame("text_back", decode=False)
        self.run_cmd("CLIPBRD", wait=60)
        self.frame("text_clipbrd", decode=False)
        self.key("alt+f", wait=5)
        self.key("a", wait=12)
        r.text("C:\\TEXT.CLP")
        self.key("Return", wait=60)
        self.frame("text_saved", decode=False)
        data = self.fetch("/TEXT.CLP", "TEXT.CLP")
        self.check("after the DOS text grab Windows still answers and the Clipboard holds the ECHO line "
                   "(saved as C:\\TEXT.CLP)", data is not None and b"TANDY GRAB TEST" in data,
                   saved=data is not None)

    def run(self, part):
        self.r.start_windows("start")
        if part in ("all", "win"):
            self.part_win()
        if part in ("all", "dos9"):
            self.part_dos9()
        if part == "text":
            self.part_text()
        ok = all(c["ok"] for c in self.out["checks"])
        self.out["verdict"] = "PASS" if ok else "FAIL"
        self.save()
        print(self.out["verdict"])
        return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prepare", "run"])
    ap.add_argument("--vm", required=True)
    ap.add_argument("--pristine")
    ap.add_argument("--drv")
    ap.add_argument("--grabber")
    ap.add_argument("--tools")
    ap.add_argument("--no-reserve", action="store_true")
    ap.add_argument("--display-drv")
    ap.add_argument("--part", default="all", choices=["all", "win", "dos9", "text"])
    a = ap.parse_args()
    if a.cmd == "prepare":
        prepare(a)
        return 0
    return Sess(a.vm).run(a.part)


if __name__ == "__main__":
    sys.exit(main())
