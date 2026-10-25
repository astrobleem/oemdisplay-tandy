#!/usr/bin/env python3
"""End-to-end test of the Tandy grabber packet through the normal launcher.

  python3 src/tgrab/TGFLOW.PY kit --vm <new dir> --winxt <STAGE.PY output>
      --pristine <PCJS image> --tools <dir: RESERVE.COM MSTEST.COM XTPAN.EXE
      PANTEST.EXE>                 # base: Windows 3.0 + C:\\WINXT staged
  python3 src/tgrab/TGFLOW.PY install-kit --vm <kit dir>
      # at DOS: C:\\WINXT\\INSTALL (TINST, wave, Windows Setup: Other display
      # C:/WINXT, Tandy EX/HX 320x200 16 colors), then a disk snapshot
  python3 src/tgrab/TGFLOW.PY run --vm <new dir> --kit <kit dir>
      --packet <TGPACK.PY output> --test <dir: TGCLOG.EXE TGFREE.COM TGHIGH.COM>
      [--part all|...]

Emulator evidence only (86Box 6.0, Tandy 1000 HX, src/xtpan/PCP86.PY).
The Windows XT kit is installed by its own DOS installer, the packet by
TGSETUP.EXE from a 720 KB floppy in drive A:, and Windows is started with
C:\\WINXT\\WINXT every time. Test-only additions (never in the packet):
C:\\TGT with TGCLOG.EXE (records every Clipboard change and free memory,
started through WIN.INI load=) and TGFREE.COM / TGHIGH.COM (DOS memory).
Results: <vm>/TGFLOW.JSN, frames <vm>/dec, files <vm>/got.
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
SD = importlib.machinery.SourceFileLoader("shotdec", str(XT / "SHOTDEC.PY")).load_module()

PART = P.PART
BOX = "/home/claude/work/86box/app/AppRun"
ROMS = "/home/claude/work/86box/roms"


def win_to_tandy(i):
    """Windows device index <-> Tandy IRGB: bits 0 and 2 swap."""
    return (i & 10) | ((i & 1) << 2) | ((i & 4) >> 2)


def mt(*a):
    return P.mt(*a)


# -------------------------------------------------------------------- kit --
def kit(a):
    vm = Path(a.vm)
    rec = P.prepare(vm, a.pristine, Path(a.winxt) / "TR53216.DRV", a.tools, mouse="pty", target="xtbase")
    i = f"{vm / 'pcp.img'}{PART}"
    auto = "PATH C:\\;C:\\WINDOWS\r\nSET TEMP=C:\\WINDOWS\\TEMP\r\n"
    (vm / "prep" / "AUTOEXEC.BAT").write_bytes(auto.encode())
    mt("mcopy", "-o", "-i", i, str(vm / "prep" / "AUTOEXEC.BAT"), "::/AUTOEXEC.BAT")
    win = mt("mtype", "-i", i, "::/WINDOWS/WIN.INI").decode("latin1")
    win = P.edit(win, "load=C:\\XTPAN\\XTPAN.EXE\r\n", "load=\r\n")
    (vm / "prep" / "WIN.INI").write_bytes(win.encode("latin1"))
    mt("mcopy", "-o", "-i", i, str(vm / "prep" / "WIN.INI"), "::/WINDOWS/WIN.INI")
    mt("mmd", "-i", i, "::/WINXT")
    for p in sorted(Path(a.winxt).iterdir()):
        mt("mcopy", "-o", "-i", i, str(p), "::/WINXT/" + p.name)
    rec["tgflow_kit"] = {"winxt_staged": {p.name: P.sha(p) for p in sorted(Path(a.winxt).iterdir())},
                         "changes": ["AUTOEXEC.BAT: PATH and TEMP only (no RESERVE; the launcher runs it)",
                                     "WIN.INI: load= empty", "C:\\WINXT: distributions/WINXT STAGE.PY output"]}
    (vm / "PREP.JSN").write_text(json.dumps(rec, indent=1) + "\n")
    print("kit prepared:", vm)


def floppy(vm, files, name="pkt.img"):
    img = Path(vm) / name
    if img.exists():
        img.unlink()
    subprocess.run(["mformat", "-f", "720", "-C", "-i", str(img), "::"], check=True)
    for p in files:
        subprocess.run(["mcopy", "-i", str(img), str(p), "::/" + Path(p).name.upper()], check=True)
    return img


def attach_floppy(vm, img):
    cfg = (Path(vm) / "86box.cfg").read_text()
    if "[Floppy and CD-ROM drives]" in cfg:
        cfg = cfg[:cfg.index("[Floppy and CD-ROM drives]")].rstrip() + "\n"
    cfg += f"\n[Floppy and CD-ROM drives]\nfdd_01_type = 35_2dd\nfdd_01_fn = {img}\n"
    (Path(vm) / "86box.cfg").write_text(cfg)


def start(vm):
    vm = Path(vm)
    subprocess.Popen(["setsid", sys.executable, str(XT / "PCPMOUSE.PY"), "serve", "--vm", str(vm)],
                     stdout=open(vm / "mouse.out", "w"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     env=dict(__import__("os").environ, PCPMOUSE_BYTE_MS="7.5"))
    time.sleep(2)
    subprocess.run([sys.executable, str(XT / "PCP86.PY"), "start", "--box", BOX, "--roms", ROMS, "--vm", str(vm)],
                   check=True)


def stop(vm):
    subprocess.run([sys.executable, str(XT / "PCP86.PY"), "stop", "--vm", str(vm)])


# -------------------------------------------------------------------- run --
MODES = {4: (320, 4), 5: (320, 4), 6: (640, 2), 8: (160, 16), 9: (320, 16), 10: (640, 4)}
PM_PARK = (316, 196)
PB_OUTSIDE = {320: (300, 100), 640: (200, 168), 160: (300, 100)}


def prepare_run(a):
    """Fresh copy of the installed kit, test tools in C:\\TGT, TGCLOG in
    WIN.INI load=, the packet on a 720 KB floppy in drive A:."""
    vm, kitdir = Path(a.vm), Path(a.kit)
    if vm.exists():
        raise SystemExit("TGFLOW: --vm exists")
    vm.mkdir(parents=True)
    shutil.copyfile(kitdir / "kit.img", vm / "pcp.img")
    shutil.copyfile(kitdir / "86box.cfg", vm / "86box.cfg")
    (vm / "prep").mkdir()
    i = f"{vm / 'pcp.img'}{PART}"
    auto = "PATH C:\\;C:\\WINDOWS;C:\\WINXT;C:\\TGT\r\nSET TEMP=C:\\WINDOWS\\TEMP\r\n"
    (vm / "prep" / "AUTOEXEC.BAT").write_bytes(auto.encode())
    mt("mcopy", "-o", "-i", i, str(vm / "prep" / "AUTOEXEC.BAT"), "::/AUTOEXEC.BAT")
    mt("mmd", "-i", i, "::/TGT")
    mt("mmd", "-i", i, "::/TGCLOG")
    test = Path(a.test)
    for n in ("TGCLOG.EXE", "TGFREE.COM", "TGHIGH.COM"):
        mt("mcopy", "-o", "-i", i, str(test / n), "::/TGT/" + n)
    (vm / "prep" / "TGIMG.BMP").write_bytes(T.bmp(T.WINPAL))
    mt("mcopy", "-o", "-i", i, str(vm / "prep" / "TGIMG.BMP"), "::/WINDOWS/TGIMG.BMP")
    win = mt("mtype", "-i", i, "::/WINDOWS/WIN.INI").decode("latin1")
    old = [l for l in win.split("\r\n") if l.lower().startswith("load=")]
    if len(old) != 1:
        raise SystemExit("TGFLOW: WIN.INI has no single load= line")
    win = P.edit(win, old[0] + "\r\n", "load=C:\\TGT\\TGCLOG.EXE\r\n")
    (vm / "prep" / "WIN.INI").write_bytes(win.encode("latin1"))
    mt("mcopy", "-o", "-i", i, str(vm / "prep" / "WIN.INI"), "::/WINDOWS/WIN.INI")
    pkt = Path(a.packet)
    files = [pkt / n for n in ("TGSETUP.EXE", "TGSETUP.LST", "TANDYGR.GR2", "TGCLIP.EXE", "TGMODES.COM",
                               "README.TXT")]
    img = floppy(vm, files)
    attach_floppy(vm, img)
    rec = {"kit_image_sha256": P.sha(kitdir / "kit.img"),
           "packet": {f.name: P.sha(f) for f in files},
           "test_tools": {n: P.sha(test / n) for n in ("TGCLOG.EXE", "TGFREE.COM", "TGHIGH.COM")},
           "changes": ["AUTOEXEC.BAT PATH adds C:\\WINXT and C:\\TGT (the 86Box keyboard map loses backslash and space typed at the DOS prompt)",
                       "C:\\TGT: TGCLOG.EXE, TGFREE.COM, TGHIGH.COM (test only)", "C:\\TGCLOG: log folder",
                       "WIN.INI load=C:\\TGT\\TGCLOG.EXE (test only)", "WINDOWS\\TGIMG.BMP (TGIMG.PY)",
                       "A: 720 KB floppy with the packet"]}
    (vm / "PREP.JSN").write_text(json.dumps(rec, indent=1) + "\n")


class Flow:
    def __init__(self, vm):
        self.vm = Path(vm)
        self.r = W.Run(vm, None, None, width=320, target="pcp")
        self.b = self.r.b
        self.got = self.vm / "got"
        self.got.mkdir(exist_ok=True)
        self.out = {"steps": [], "checks": [], "clips": [], "memory": []}
        self.nclip = 0

    # -- plumbing ------------------------------------------------------------
    def save(self):
        (self.vm / "TGFLOW.JSN").write_text(json.dumps(self.out, indent=1) + "\n")

    def check(self, what, ok, **kw):
        kw.update(check=what, ok=bool(ok))
        self.out["checks"].append(kw)
        self.save()
        print(("PASS " if ok else "FAIL ") + what, flush=True)
        return ok

    def step(self, what):
        self.out["steps"].append({"step": what, "t": round(time.time(), 1)})
        self.save()
        print(what, flush=True)

    def key(self, *k, wait=3):
        self.r.key(*k, wait=wait)

    def text(self, s, wait=1):
        self.r.text(s, wait=wait)

    def dos(self, cmd, wait):
        """At the DOS prompt the 86Box keyboard map loses typed spaces:
        send them as key presses."""
        parts = cmd.split(" ")
        for k, part in enumerate(parts):
            if k:
                self.key("space", wait=0.3)
            if part:
                self.text(part, wait=0.3)
        self.key("Return", wait=wait)

    def shot(self, name, width=320, decode=True, settle=1.5):
        self.b.width = width
        try:
            idx = self.b.shot(name, settle=settle, decode=decode)
        finally:
            self.b.width = 320
        return idx

    def park(self):
        self.r.rehome(*W.PARK, wait=3)

    def run_cmd(self, cmd, wait):
        self.r.run_cmd(cmd, wait=wait)

    def fetch(self, guest, name=None):
        name = name or guest.strip("/").replace("/", "_")
        dst = self.got / name
        if dst.exists():
            dst.unlink()
        p = subprocess.run(["mcopy", "-n", "-i", f"{self.vm / 'pcp.img'}{PART}", "::" + guest, str(dst)],
                           capture_output=True)
        return dst.read_bytes() if p.returncode == 0 and dst.exists() else None

    def log_lines(self):
        data = self.fetch("/TGCLOG/LOG.TXT", "LOG.TXT")
        return data.decode("latin1").splitlines() if data else []

    def clips(self):
        return [l for l in self.log_lines() if l.startswith("CLIP ")]

    def clip_bitmap(self, n):
        """(w, h, planes, bits, rows of device indices) of TGCLOG's Cnnn.BIN"""
        data = self.fetch("/TGCLOG/C%03d.BIN" % n, "C%03d.BIN" % n)
        if not data:
            return None
        w, h, wb, pl, bp = struct.unpack_from("<5H", data, 0)
        base = 10
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

    def dos_free(self):
        data = self.fetch("/TGCLOG/DOS.TXT", "DOS.TXT")
        return [int(l.split("=")[1]) for l in data.decode().splitlines() if l.startswith("DOS free=")] if data else []

    def win_free(self):
        """Last MEM line (free, largest block) of TGCLOG."""
        mem = [l for l in self.log_lines() if l.startswith("MEM ")]
        if not mem:
            return None
        f = dict(kv.split("=") for kv in mem[-1].split()[2:])
        return int(f["free"]), int(f["big"])

    def new_clip(self, before, what, wait=60):
        """Wait for TGCLOG lines after `before`; return the last one with a bitmap."""
        for _ in range(wait // 5):
            c = self.clips()
            if len(c) > before and any("bitmap=none" not in l for l in c[before:]):
                break
            time.sleep(5)
        c = self.clips()
        new = c[before:]
        self.out["clips"].append({"after": what, "lines": new})
        self.save()
        bm = [l for l in new if "bitmap=none" not in l]
        return (int(bm[-1].split()[1]), new) if bm else (None, new)

    # -- DOS side --------------------------------------------------------------
    def tgsetup(self, args="", tag="setup"):
        self.step("A:TGSETUP " + args)
        self.dos("A:", 4)
        self.dos(("TGSETUP " + args).strip(), 90)
        self.shot(tag, decode=False)
        self.dos("C:", 4)
        i = f"{self.vm / 'pcp.img'}{PART}"
        sysini = mt("mtype", "-i", i, "::/WINDOWS/SYSTEM.INI").decode("latin1")
        winini = mt("mtype", "-i", i, "::/WINDOWS/WIN.INI").decode("latin1")
        grab = [l for l in sysini.split("\r\n") if l.lower().startswith("286grabber=")]
        load = [l for l in winini.split("\r\n") if l.lower().startswith("load=")]
        return grab, load

    def launch(self, tag):
        self.step("C:\\WINXT\\WINXT (" + tag + ")")
        self.r.m("ident", "on")            # serial mouse identification for Windows
        self.dos("WINXT", 170)
        self.r.m("ident", "off")
        for _ in range(5):              # Program Manager's old group messages
            self.key("Escape", wait=8)
        self.park()
        px = self.shot(tag + "_desktop")
        return px

    def exit_windows(self, tag):
        self.step("exit Windows (" + tag + ")")
        self.r.click(*W.PM_TITLE, wait=5)
        self.key("alt+F4", wait=8)
        self.key("Return", wait=40)
        self.shot(tag + "_dos", decode=False)

    def dos_tgfree(self, what):
        n = len(self.dos_free())
        self.dos("TGFREE", 8)
        v = self.dos_free()
        val = v[-1] if len(v) > n else None
        self.out["memory"].append({"what": what, "dos_free": val})
        self.save()
        return val

    # -- Windows side ----------------------------------------------------------
    def win_session_free(self, what):
        """TGFREE.COM as a DOS program started from Windows: the memory a
        DOS program gets; then Windows' free memory once it is back."""
        n = len(self.dos_free())
        self.run_cmd("C:\\TGT\\TGFREE.COM", wait=60)
        self.park()
        time.sleep(8)
        v = self.dos_free()
        rec = {"what": what, "dos_free_in_session": v[-1] if len(v) > n else None, "windows": self.win_free()}
        self.out["memory"].append(rec)
        self.save()
        return rec

    def part_text(self, tag):
        self.step("text grab: COMMAND.COM, ECHO, Shift+PRINT, EXIT (" + tag + ")")
        before = len(self.clips())
        self.run_cmd("COMMAND.COM", wait=40)
        self.text("ECHO TANDY GRAB TEST")
        self.key("Return", wait=5)
        self.shot(tag + "_text", decode=False)
        self.key("shift+KP_Multiply", wait=30)
        self.text("EXIT")
        self.key("Return", wait=60)
        self.park()
        self.shot(tag + "_text_back", decode=False)
        c = self.clips()[before:]
        texts = []
        for l in c:
            if "text=yes" in l:
                t = self.fetch("/TGCLOG/C%03d.TXT" % int(l.split()[1]))
                texts.append(t.decode("latin1") if t else "")
        rec = self.win_session_free(tag + ": after the text grab")
        return self.check("%s: after a DOS text grab Windows still answers (File > Run starts another DOS "
                          "program) and the Clipboard holds the ECHO line" % tag,
                          any("TANDY GRAB TEST" in t for t in texts) and rec["dos_free_in_session"] is not None,
                          clip_lines=c, answered=rec["dos_free_in_session"] is not None)

    def grab_mode(self, m, p, switch=False, ref=None):
        w, n = MODES[m]
        name = "m%Xp%d" % (m, p)
        self.step("TGMODES %X %d: Shift+PRINT%s" % (m, p, ", ALT+TAB away and back" if switch else ""))
        before = len(self.clips())
        self.run_cmd("A:TGMODES.COM %X %d" % (m, p), wait=50)
        a = self.shot(name + "_screen", width=w)
        res = {"mode": m, "palette": p}
        res["colours_on_screen"] = len(set(a))
        if switch:
            self.key("alt+Tab", wait=60)
            self.shot(name + "_windows")
            self.key("alt+Tab", wait=60)
            c = self.shot(name + "_back", width=w)
            res["restore_mismatches"] = sum(x != y for x, y in zip(a, c))
            if p == 2:
                res["back_vs_default_mismatches"] = sum(x != y for x, y in zip(ref, c)) if ref else None
        self.key("shift+KP_Multiply", wait=40)
        self.key("space", wait=60)
        self.park()
        k, lines = self.new_clip(before, name)
        res["clip_lines"] = lines
        bm = self.clip_bitmap(k) if k else None
        if bm:
            bw, bh, pl, bp, rows = bm
            res["bitmap"] = [bw, bh, pl, bp]
            if (bw, bh) == (w, 200):
                res["clip_vs_screen_mismatches"] = self.compare(rows, a, w)
                if ref:
                    res["clip_vs_default_mismatches"] = self.compare(rows, ref, w)
        self.out.setdefault("modes", []).append(res)
        self.save()
        ok_size = bm is not None and (bm[0], bm[1]) == (w, 200)
        if p in (0, 1):
            self.check("mode %Xh palette %d: Print Screen puts a %dx200 bitmap on the Clipboard equal to the "
                       "DOS screen in every pixel (%d colours shown)" % (m, p, w, n),
                       ok_size and res.get("clip_vs_screen_mismatches") == 0 and res["colours_on_screen"] == n,
                       **{k_: v for k_, v in res.items() if k_ != "clip_lines"})
            if switch:
                self.check("mode %Xh palette %d: ALT+TAB to Windows and back restores the screen and its "
                           "palette exactly" % (m, p), res["restore_mismatches"] == 0,
                           mismatches=res["restore_mismatches"])
        else:
            self.check("mode %Xh palette 2 (registers written with OUT): the grab shows the BIOS palette "
                       "(equal to the palette-0 screen), not the screen (the registers cannot be read)" % m,
                       ok_size and res.get("clip_vs_default_mismatches") == 0
                       and res.get("clip_vs_screen_mismatches", 0) > 0,
                       **{k_: v for k_, v in res.items() if k_ != "clip_lines"})
            if switch:
                self.check("mode %Xh palette 2: after ALT+TAB back the screen has the BIOS palette again "
                           "(equal to the palette-0 screen)" % m, res.get("back_vs_default_mismatches") == 0,
                           mismatches=res.get("back_vs_default_mismatches"))
        return a, (rows if bm else None)

    def pb_paste_full(self, name, w, screen, corner=False):
        """Paintbrush, its own workflow for a whole picture: Options > Image
        Attributes w x 200 pels, File > New, View > Zoom Out, Edit > Paste,
        a click outside the picture places it, View > Zoom In, Save As."""
        self.step("Paintbrush: Image Attributes %dx200, Zoom Out, Paste, Save As %s" % (w, name))
        self.run_cmd("PBRUSH", wait=70)
        self.key("alt+space", wait=5)
        self.key("x", wait=50)
        self.key("alt+o", wait=8)
        self.key("i", wait=15)
        self.key("alt+h", wait=3)
        self.key("Tab", wait=3)                # the Units buttons: in, cm, pels
        self.key("KP_Down", wait=3)
        self.key("KP_Down", wait=3)
        self.key("alt+w", wait=3)
        self.text(str(w))
        self.key("alt+h", wait=3)
        self.text("200")
        self.shot(name[:-4] + "_attr", decode=False)
        self.key("Return", wait=15)
        self.key("alt+f", wait=8)
        self.key("n", wait=30)
        self.key("n", wait=20)                 # "save changes?" if asked
        self.key("alt+v", wait=8)
        self.key("o", wait=40)
        self.key("alt+e", wait=8)
        self.key("p", wait=60)
        self.park()
        self.shot(name[:-4] + "_hatched")
        self.r.click(*PB_OUTSIDE[w], wait=40)
        self.park()
        self.shot(name[:-4] + "_placed")
        self.key("alt+v", wait=8)
        self.key("i", wait=40)
        self.park()
        self.shot(name[:-4] + "_pasted")
        self.key("alt+f", wait=8)
        self.key("a", wait=12)
        self.text(name)
        self.key("Return", wait=90)
        data = self.fetch("/WINDOWS/" + name, name)
        res = {"file": name}
        ok = False
        if data:
            bw, bh, rows, pal = T.read_bmp(data)
            res["size"] = [bw, bh]
            if (bw, bh) == (w, 200):
                ref = lambda x, y: T.WINPAL[4 * win_to_tandy(screen[y * w + x]):4 * win_to_tandy(screen[y * w + x]) + 3]
                bad = sum(bytes(pal[4 * rows[y][x]:4 * rows[y][x] + 3]) != bytes(ref(x, y))
                          for y in range(200) for x in range(w)
                          if not (corner and x >= 316 and y >= 196))   # the parked pointer
                res["mismatches"] = bad
                ok = bad == 0
        self.key("alt+F4", wait=20)
        self.key("n", wait=10)
        self.park()
        return self.check("Paintbrush pastes the whole %dx200 picture and saves %s with every pixel in the "
                          "reference colour of the screen" % (w, name), ok, **res)

    # -- scenario ----------------------------------------------------------------
    def selftest(self):
        """Host-only: the comparisons must reject a changed pixel and an
        unchanged (previous) Clipboard."""
        screen = bytes([(x // 20) & 15 for y in range(200) for x in range(320)])
        rows = [[win_to_tandy((x // 20) & 15) for x in range(320)] for y in range(200)]
        good = self.compare(rows, screen, 320)
        rows[50][60] ^= 1
        bad = self.compare(rows, screen, 320)
        self.check("self-test: the Clipboard comparison passes an equal bitmap and fails one changed pixel",
                   good == 0 and bad == 1, good=good, bad=bad)

    def part_pb(self):
        """TGIMG.BMP round trip in Paintbrush (Windows to Windows)."""
        import importlib.machinery as m
        S = m.SourceFileLoader("tgsess", str(HERE / "TGSESS.PY")).load_module()
        s = S.Sess.__new__(S.Sess)
        s.vm, s.r, s.got, s.out = self.vm, self.r, self.got, self.out
        s.save = self.save
        s.check, s.step = self.check, self.step
        # only the first half of TGSESS part_win: open, copy, paste, save, reopen
        r = self.r
        s.step("Paintbrush opens TGIMG.BMP")
        s.run_cmd("PBRUSH TGIMG.BMP", wait=70)
        s.key("alt+space", wait=5)
        s.key("x", wait=50)
        s.park()
        px = s.frame("pb_img")
        bad = s.img_on_screen(px, *S.IMG_AT)
        s.check("TGIMG.BMP shown exactly at the canvas origin (all 2,560 pixels, every colour)", not bad,
                mismatches=len(bad))
        r.click(*S.PICK, wait=4)
        r.drag(S.IMG_AT[0], S.IMG_AT[1], S.IMG_AT[0] + 64, S.IMG_AT[1] + 40, wait=8)
        s.key("alt+e", wait=8)
        s.key("c", wait=15)
        s.key("alt+f", wait=8)
        s.key("n", wait=20)
        s.key("n", wait=20)
        s.key("alt+e", wait=8)
        s.key("p", wait=30)
        r.click(250, 150, wait=6)
        s.park()
        px = s.frame("pb_anchored")
        bad = s.img_on_screen(px, *S.IMG_AT)
        s.check("pasted picture anchored at the canvas origin, all pixels and colours exact", not bad,
                mismatches=len(bad))
        s.key("alt+f", wait=8)
        s.key("a", wait=12)
        r.text("PASTE.BMP")
        s.key("Return", wait=60)
        data = s.fetch("/WINDOWS/PASTE.BMP", "PASTE.BMP")
        res = s.bmp_check(data, "PASTE.BMP") if data else {"missing": True}
        s.check("PASTE.BMP: the 64x40 picture at (0,0) with exactly the original colours, the rest white",
                data and res["picture_mismatches"] == 0 and res["rest_white"], **res)
        s.key("alt+F4", wait=20)
        s.run_cmd("PBRUSH PASTE.BMP", wait=70)
        s.key("alt+space", wait=5)
        s.key("x", wait=50)
        s.park()
        px = s.frame("pb_reopened")
        bad = s.img_on_screen(px, *S.IMG_AT)
        s.check("reopened PASTE.BMP shows the picture exactly", not bad, mismatches=len(bad))
        s.key("alt+F4", wait=20)
        s.park()

    def part_winprt(self):
        self.step("Shift+PRINT in Windows, the whole screen pasted and saved")
        self.park()
        before = len(self.clips())
        a = self.shot("winprt_screen")
        self.key("shift+KP_Multiply", wait=40)
        k, lines = self.new_clip(before, "winprt")
        bm = self.clip_bitmap(k) if k else None
        ok = bm is not None and bm[:2] == (320, 200)
        corner = lambda x, y: x >= 316 and y >= 196
        mism = sum(win_to_tandy(bm[4][y][x]) != a[y * 320 + x] for y in range(200) for x in range(320)
                   if not corner(x, y)) if ok else None
        self.check("Windows Print Screen: the Clipboard holds a 320x200 bitmap equal to the screen "
                   "(pointer corner excluded)", ok and mism == 0, mismatches=mism, clip_lines=lines)
        self.pb_paste_full("WINPRT.BMP", 320, a, corner=True)

    def part_modes(self):
        refs = {}
        for m in (4, 5, 6, 8, 9, 10):
            refs[m], _ = self.grab_mode(m, 0)
            a, rows = self.grab_mode(m, 1, switch=m in (4, 6, 9, 10))
            if m == 9:
                self.pb_paste_full("DOS9P1.BMP", 320, a)
            if m == 10:
                self.pb_paste_full("DOSAP1.BMP", 640, a)
        for m in (4, 9):
            self.grab_mode(m, 2, switch=True, ref=refs[m])

    def part_memory(self, tag, n=4):
        self.step("memory: %d DOS sessions from Windows (%s)" % (n, tag))
        self.out.setdefault("memory_note", "windows = [GetFreeSpace(0), GlobalCompact(0)]; the largest block "
                            "moves with compaction, the check uses the free total")
        recs = [self.win_session_free("%s session %d" % (tag, k + 1)) for k in range(n)]
        dos = [r["dos_free_in_session"] for r in recs]
        win = [r["windows"] for r in recs]
        self.check("%s: every DOS session gets the same memory and Windows' free memory is the same after "
                   "each closed session" % tag,
                   None not in dos and len(set(dos)) == 1 and None not in win
                   and len(set(w[0] for w in win)) == 1,
                   dos_free=dos, windows_free=win)
        return dos[0]

    def scenario(self, part):
        self.selftest()
        if part in ("all", "main"):
            grab, load = self.tgsetup()
            self.check("TGSETUP from drive A: selects the grabber and starts TGCLIP from WIN.INI load=",
                       grab == ["286grabber=TANDYGR.GR2"] and len(load) == 1 and "C:\\WINDOWS\\TGCLIP.EXE" in load[0]
                       and "C:\\TGT\\TGCLOG.EXE" in load[0], grabber=grab, load=load)
            d0 = self.dos_tgfree("DOS prompt before Windows")
            self.launch("l1")
            self.part_pb()
            self.part_winprt()
            self.part_modes()
            self.part_text("l1")
            self.out["dos_free_session_tandygr"] = self.part_memory("TANDYGR.GR2")
            self.exit_windows("l1")
            d1 = self.dos_tgfree("DOS prompt after Windows exit 1")
        if part == "fix":
            self.tgsetup()
            self.launch("l1")
            self.part_winprt()
            for m in (9, 10):
                self.grab_mode(m, 0)
                a, rows = self.grab_mode(m, 1, switch=True)
                self.pb_paste_full("DOS%XP1.BMP" % m, MODES[m][0], a)
            self.out["dos_free_session_tandygr"] = self.part_memory("TANDYGR.GR2", n=3)
            self.exit_windows("l1")
            self.dos_tgfree("DOS prompt after Windows exit 1")
        if part in ("all", "relaunch"):
            if part == "relaunch":
                self.tgsetup()
                d1 = self.dos_tgfree("DOS prompt before Windows")
            for k in (2, 3):
                self.launch("l%d" % k)
                self.part_text("l%d" % k)
                self.exit_windows("l%d" % k)
                dk = self.dos_tgfree("DOS prompt after Windows exit %d" % k)
                self.check("launch %d: free DOS memory after Windows exits is the same as after the first "
                           "(nothing accumulates)" % k, dk == d1, first=d1, now=dk)
            for n in (1, 2, 3):
                self.step("TGHIGH %d: a different memory layout below RESERVE" % n)
                self.dos("TGHIGH %d" % n, 8)
                self.launch("h%d" % n)
                self.part_text("h%d" % n)
                self.exit_windows("h%d" % n)
        if part in ("all", "remove"):
            if part == "remove":
                self.tgsetup()
            self.launch("t")
            dt = self.part_memory("TANDYGR.GR2 (control pair)", n=2)
            self.exit_windows("t")
            grab, load = self.tgsetup("/REMOVE", tag="remove")
            self.check("TGSETUP /REMOVE puts CGA.GR2 back and takes TGCLIP out of load=",
                       grab == ["286grabber=CGA.GR2"] and "TGCLIP" not in load[0].upper(), grabber=grab, load=load)
            self.launch("c")
            dc = self.part_memory("CGA.GR2", n=2)
            self.exit_windows("c")
            self.out["dos_free_session"] = {"TANDYGR.GR2": dt, "CGA.GR2": dc}
            self.check("a DOS program started from Windows gets at least as much memory with TANDYGR.GR2 as "
                       "with CGA.GR2", dt is not None and dc is not None and dt >= dc, tandygr=dt, cgagr2=dc)
        ok = all(c["ok"] for c in self.out["checks"])
        self.out["verdict"] = "PASS" if ok else "FAIL"
        self.save()
        print(self.out["verdict"])
        return 0 if ok else 1

    @staticmethod
    def compare(rows, screen, width):
        """Device-index bitmap rows against decoded Tandy screen indices."""
        return sum(win_to_tandy(rows[y][x]) != screen[y * width + x] for y in range(200) for x in range(width))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["kit", "install-kit", "run"])
    ap.add_argument("--vm", required=True)
    ap.add_argument("--winxt")
    ap.add_argument("--pristine")
    ap.add_argument("--tools")
    ap.add_argument("--kit")
    ap.add_argument("--packet")
    ap.add_argument("--test")
    ap.add_argument("--part", default="all")
    a = ap.parse_args()
    if a.cmd == "kit":
        kit(a)
    elif a.cmd == "run":
        prepare_run(a)
        start(a.vm)
        time.sleep(80)
        try:
            rc = Flow(a.vm).scenario(a.part)
        finally:
            stop(a.vm)
        sys.exit(rc)
