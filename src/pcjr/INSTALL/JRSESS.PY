#!/usr/bin/env python3
"""Clean Windows 3.0 install and scripted session on an emulated IBM PCjr.

  python3 src/pcjr/INSTALL/JRSESS.PY --packet <JRPACK folder> --win30 <folder> \
      --tools <dir with JRHOLDT.COM> --out <new dir>

--packet  the folder made by JRPACK.PY (becomes C:\\PCJREXP)
--win30   the files of the five Windows 3.0 1.2 MB disks in one folder
          (private test media; becomes C:\\WIN30SRC; nothing is committed)
--tools   JRHOLDT.COM (BUILDCOM.PY; emulator-only negative-test tool)

Emulator evidence only (JRDBX.PY: DOSBox-X machine=pcjr, its own DOS).
Everything a user would type is typed into the guest; nothing in C:\\WINDOWS
is edited from the host. Steps:

 A. Install: JRGUARD; SETUP from C:\\WIN30SRC; Display = Other, path
    C:\\PCJREXP, "EXPERIMENTAL IBM PCjr 320x200 16 colors"; Keyboard = PC/XT
    (84 keys); Network = none; the three optional procedures unticked;
    CONFIG.SYS/AUTOEXEC.BAT changes declined; Return to DOS.
 B. The install as Setup left it: drivers, grabber, fonts and WIN.COM
    hashes; SYSTEM.INI [boot]; keyboard type 1; fresh groups; Program
    Manager's saved window and every group window on the 320x200 screen.
 C. Session 1 through C:\\PCJREXP\\JRWIN: desktop; keyboard menu open and
    exact restore; mouse to an exact point and a click opening the same
    menu; Notepad typing saved to C:\\KBD.TXT (byte-exact); Paintbrush box
    drawn with the mouse, saved, closed, reopened through File > Open
    (canvas identical, BMP equals the screen); COMMAND.COM started, a line
    written to C:\\DOSAPP.TXT, Alt+Tab to Windows and back (screen restored
    exactly), EXIT back to an identical desktop; Exit Windows.
 D. Session 2 through JRWIN: desktop identical to session 1's; exit.
 E. Refusal: JRHOLDT keeps the page as an ordinary resident program, then
    JRWIN must refuse and not start Windows.
Each JRWIN return is logged to C:\\JRLOG.TXT with DOS IF ERRORLEVEL.
Results: <out>/RESULT.JSN; captures <out>/raw, exact frames <out>/dec.
Exit 0 only if every check passes.
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import struct
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
J = importlib.machinery.SourceFileLoader("jrdbx", str(HERE / "JRDBX.PY")).load_module()

KBD_TEXT = "PCjr keyboard: ABC xyz 0123456789 ,./;'[]-= !@#$%&*()_+ C:\\WINDOWS"
PM_FILE = (51, 45)                  # Program Manager's File menu (fresh install)
PB_BOX_TOOL = (23, 116)             # Paintbrush filled-box tool, maximized
PB_COLOUR12 = (112, 189)            # palette: light red (IRGB 12)
PB_DRAG = ((100, 70), (160, 110))   # box press and release points
PB_CANVAS = (36, 48, 297, 172)      # visible canvas, screen pixels
PB_ORIGIN = (36, 48)                # BMP (0,0) on screen
PARK = (319, 199)


class Run:
    def __init__(self, out):
        self.out = out
        self.c = out / "C"
        self.checks = []
        self.x = self.y = None

    # -- recording -----------------------------------------------------------
    def check(self, name, ok, **detail):
        self.checks.append(dict(check=name, result="PASS" if ok else "FAIL", **detail))
        print(("ok   " if ok else "FAIL ") + name, flush=True)
        return ok

    def shot(self, name, settle=1.5):
        J.shot(self.out, name, settle=settle)
        data, bad = J.decode(self.out / "raw" / (name + ".png"))
        if data and not bad:
            J.save_frame(self.out, name, data)
            return data
        return None

    def settled(self, name, tries=10):
        """Capture until two successive frames agree: serial mouse packets
        reach the guest in order but later than the host sends them."""
        prev = None
        for i in range(tries):
            cur = self.shot(name)
            if cur is not None and cur == prev:
                return cur
            prev = cur
            time.sleep(2)
        return prev

    def raw(self, name):
        from PIL import Image
        with Image.open(self.out / "raw" / (name + ".png")) as im:
            return im.convert("RGB").tobytes()

    # -- input ---------------------------------------------------------------
    def m(self, *words):
        J.mouse(self.out, *words)

    def sync(self, timeout=120):
        token = f"t{time.time():.3f}"
        f = self.out / "mouse.sync"
        if f.exists():
            f.unlink()
        self.m("sync", token)
        for _ in range(timeout * 4):
            if f.exists() and f.read_text().strip() == token:
                return
            time.sleep(0.25)
        raise SystemExit("JRSESS: mouse helper did not finish")

    def home(self):
        self.m("move", -400, -300)
        self.sync()
        time.sleep(1)
        self.x, self.y = 0, 0

    def to(self, x, y, wait=1.5):
        self.m("move", x - self.x, y - self.y)
        self.sync()
        self.x, self.y = x, y
        time.sleep(wait)

    def click(self, x, y, wait=3):
        self.home()
        self.to(x, y)
        self.m("click")
        self.sync()
        time.sleep(wait)

    def run_cmd(self, cmd, wait):
        J.key("alt+f", wait=2)
        J.key("r", wait=3)
        J.text(cmd)
        J.key("Return", wait=wait)

    def dos(self, line, wait=2):
        J.text(line)
        J.key("Return", wait=wait)

    def log_rc(self, label):
        self.dos(f"IF ERRORLEVEL 1 ECHO {label} RC=NONZERO>>C:\\JRLOG.TXT")
        self.dos(f"IF NOT ERRORLEVEL 1 ECHO {label} RC=0>>C:\\JRLOG.TXT")

    def start_windows(self):
        self.m("ident", "on")                          # mouse detection answers 'M'
        self.dos("C:\\PCJREXP\\JRWIN", wait=45)
        self.m("ident", "off")
        self.m("step", 2)                              # no Windows acceleration
        self.x = self.y = None

    def exit_windows(self, label):
        J.key("alt+F4", wait=4)
        J.key("Return", wait=14)
        self.log_rc(label)


def diff(a, b):
    return [i for i in range(64000) if a[i] != b[i]]


def bbox(d):
    if not d:
        return None
    xs = [i % 320 for i in d]
    ys = [i // 320 for i in d]
    return [min(xs), min(ys), max(xs), max(ys)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ini(path):
    out, sec = {}, None
    for line in Path(path).read_bytes().decode("latin-1").splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            sec = line[1:-1].lower()
        elif "=" in line and sec:
            k, v = line.split("=", 1)
            out.setdefault(sec, {})[k.strip().lower()] = v.strip()
    return out


def group_rect(path):
    """rcNormal of a Windows 3.0 .GRP file (PMCC header)."""
    data = Path(path).read_bytes()
    if data[:4] != b"PMCC":
        return None
    return list(struct.unpack_from("<4h", data, 10))


def install(r):
    J.text("C:\\PCJREXP\\JRGUARD")
    J.key("Return", wait=3)
    r.log_rc("GUARD")
    r.shot("a00_guard")
    r.dos("CD \\WIN30SRC")
    r.dos("SETUP", wait=8)
    r.shot("a01_welcome")
    J.key("Return", wait=4)                          # welcome
    J.key("Return", wait=6)                          # C:\WINDOWS
    r.shot("a02_detected")
    J.key(*["Up"] * 6, wait=1)
    J.key("Return", wait=3)                          # Display
    J.key(*["Down"] * 20, wait=1)
    J.key("Return", wait=3)                          # Other
    J.key("BackSpace", "BackSpace", "BackSpace", wait=0.5)
    J.text("C:\\PCJREXP")
    J.key("Return", wait=4)
    r.shot("a03_selector")
    J.key("Return", wait=5)                          # the PCjr selector
    J.key(*["Up"] * 4, wait=1)
    J.key("Return", wait=3)                          # Keyboard
    J.key(*["Down"] * 12, wait=1)
    J.key("Up", wait=0.5)
    J.key("Return", wait=3)                          # PC/XT - Type keyboard (84 keys)
    J.key("Up", wait=0.5)
    J.key("Return", wait=3)                          # Network
    J.key(*["Down"] * 20, wait=1)
    J.key("Up", "Up", "Up", wait=0.5)
    J.key("Return", wait=3)                          # No Network Installed
    r.shot("a04_list")
    J.key("Return", wait=75)                         # copy files, graphical phase
    r.shot("a05_options")
    J.key("alt+p", wait=2)
    J.key("alt+a", wait=2)
    J.key("alt+d", wait=2)
    r.shot("a06_unticked")
    J.key("Return", wait=60)
    r.shot("a07_config")
    J.key("Down", "Down", wait=1)
    J.key("Return", wait=8)                          # make the modifications later
    J.key("alt+d", wait=40)                          # Don't Save
    r.shot("a08_done")
    J.key("alt+d", wait=12)                          # Return to DOS
    r.shot("a09_dos")


def check_install(r, packet):
    w = r.c / "WINDOWS"
    s = ini(w / "SYSTEM.INI")
    boot = s.get("boot", {})
    want = {"display.drv": "TNDYJR.DRV", "286grabber": "JRGRAB.GR2", "fonts.fon": "XTESYS.FON",
            "fixedfon.fon": "XTEFIX.FON", "oemfonts.fon": "XTEOEM.FON", "keyboard.drv": "keyboard.drv",
            "mouse.drv": "mouse.drv"}
    got = {k: boot.get(k) for k in want}
    r.check("system_ini_display_grabber_fonts", got == want, got=got)
    r.check("system_ini_keyboard_type_1", s.get("keyboard", {}).get("type") == "1",
            keyboard=s.get("keyboard"))
    r.check("setup_description_names_pcjr",
            s.get("boot.description", {}).get("display.drv") == "EXPERIMENTAL IBM PCjr 320x200 16 colors",
            got=s.get("boot.description", {}).get("display.drv"))
    files = {"TNDYJR.DRV": "SYSTEM", "JRGRAB.GR2": "SYSTEM", "XTESYS.FON": "SYSTEM",
             "XTEFIX.FON": "SYSTEM", "XTEOEM.FON": "SYSTEM"}
    same = {n: (w / d / n).exists() and sha(w / d / n) == sha(packet / n) for n, d in files.items()}
    r.check("installed_files_equal_packet", all(same.values()), files=same)
    winsize = (w / "WIN.COM").stat().st_size
    r.check("win_com_built_with_static_logo", winsize == 7879, bytes=winsize, sha256=sha(w / "WIN.COM"))
    no_msfiles = [n for n in ("CGA.GR2", "CGA.DRV", "CGASYS.FON", "EGA.DRV") if (w / "SYSTEM" / n).exists()]
    r.check("no_cga_ega_display_files_installed", not no_msfiles, found=no_msfiles)
    pm = ini(w / "PROGMAN.INI")
    win = [int(v) for v in pm.get("settings", {}).get("window", "0 0 0 0 0").split()[:4]]
    r.check("progman_window_on_screen", 0 <= win[0] < win[2] <= 320 and 0 <= win[1] < win[3] <= 200,
            window=win)
    groups = {v.split("\\")[-1]: group_rect(r.c / v[3:].replace("\\", "/")) for k, v in pm.get("groups", {}).items()}
    cw, ch = win[2] - win[0], win[3] - win[1]
    ok = len(groups) == 3 and all(g and 0 <= g[0] < g[2] <= cw and 0 <= g[1] < g[3] <= ch for g in groups.values())
    r.check("fresh_groups_inside_program_manager", ok, groups=groups, progman_size=[cw, ch])
    r.check("config_autoexec_untouched", not (r.c / "CONFIG.SYS").exists() and not (r.c / "AUTOEXEC.BAT").exists())
    return {"system_ini_boot": boot, "keyboard": s.get("keyboard"), "progman": pm,
            "groups": groups, "win_com_sha256": sha(w / "WIN.COM")}


def session1(r):
    r.start_windows()
    d1 = r.shot("s1_desktop")
    r.check("s1_desktop_exact_frame", d1 is not None)
    # keyboard: menu opens, closes, desktop exact
    J.key("alt+f", wait=3)
    mk = r.shot("s1_menu_kbd")
    J.key("Escape", "Escape", wait=3)
    mc = r.shot("s1_menu_kbd_closed")
    opened = diff(mk, d1) if mk and d1 else []
    r.check("keyboard_menu_opens_and_restores", len(opened) >= 1000 and mc == d1,
            opened_pixels=len(opened), opened_box=bbox(opened))
    # mouse: exact point, click opens the same menu
    r.home()
    r.to(*PM_FILE, wait=2)
    pf = r.settled("s1_pointer_file")
    # Windows starts with the pointer at the screen centre; look only left of it.
    near = [i for i in (diff(pf, d1) if pf and d1 else []) if i % 320 < 140]
    box = bbox(near)
    r.m("click")
    r.sync()
    time.sleep(3)
    mm = r.settled("s1_menu_mouse")
    same_menu = [i for i in diff(mm, mk)] if mm and mk else None
    r.check("mouse_reaches_point_and_click_opens_menu",
            box is not None and box[0] >= PM_FILE[0] - 1 and box[1] >= PM_FILE[1] - 1 and
            box[0] <= PM_FILE[0] + 1 and box[1] <= PM_FILE[1] + 1 and same_menu is not None and
            len(same_menu) < 200,
            pointer_box=box, menu_differs_from_keyboard_menu=len(same_menu or []),
            note="the two menus may differ only by the pointer")
    J.key("Escape", "Escape", wait=3)
    r.to(*PARK, wait=2)
    p0 = r.settled("s1_parked")
    r.check("parked_desktop_exact_frame", p0 is not None)
    # keyboard text end to end: Notepad -> C:\KBD.TXT
    r.run_cmd("NOTEPAD", wait=15)
    J.text(KBD_TEXT, wait=2)
    r.shot("s1_notepad")
    J.key("alt+f", wait=2)
    J.key("a", wait=4)
    J.text("C:\\KBD.TXT")
    J.key("Return", wait=6)
    J.key("alt+F4", wait=6)
    kb = (r.c / "KBD.TXT").read_bytes() if (r.c / "KBD.TXT").exists() else b""
    r.check("keyboard_text_saved_exactly", kb.rstrip(b"\r\n") == KBD_TEXT.encode("ascii"),
            expected=KBD_TEXT, got=kb.decode("latin-1"))
    nc = r.shot("s1_notepad_closed")
    r.check("notepad_closed_desktop_exact", nc == p0, differing=len(diff(nc, p0)) if nc and p0 else None)
    # Paintbrush: draw with the mouse, save, close, reopen
    r.run_cmd("PBRUSH", wait=20)
    J.key("alt+space", wait=2)
    J.key("x", wait=12)
    r.click(*PB_BOX_TOOL)
    r.click(*PB_COLOUR12)
    r.home()
    r.to(*PB_DRAG[0])
    r.m("down")
    r.sync()
    time.sleep(1)
    r.to(*PB_DRAG[1])
    r.m("up")
    r.sync()
    time.sleep(3)
    r.to(*PARK, wait=2)
    pb = r.settled("s1_pb_drawn")
    J.key("alt+f", wait=2)
    J.key("a", wait=4)
    J.text("C:\\JRTEST.BMP")
    J.key("Return", wait=10)
    J.key("alt+F4", wait=8)
    r.run_cmd("PBRUSH", wait=20)
    J.key("alt+space", wait=2)
    J.key("x", wait=12)
    J.key("alt+f", wait=2)
    J.key("o", wait=5)
    J.text("C:\\JRTEST.BMP")
    J.key("Return", wait=15)
    pr = r.shot("s1_pb_reopened")
    x0, y0, x1, y1 = PB_CANVAS
    cd = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
          if not pb or not pr or pb[y * 320 + x] != pr[y * 320 + x]]
    r.check("reopened_canvas_identical", pb is not None and pr is not None and not cd,
            differing=len(cd), first=cd[:3])
    r.check_bmp(pb)
    J.key("alt+F4", wait=8)
    pc = r.shot("s1_pb_closed")
    r.check("paintbrush_closed_desktop_exact", pc == p0, differing=len(diff(pc, p0)) if pc and p0 else None)
    # DOS program: start, write, switch away and back, exit
    r.run_cmd("COMMAND.COM", wait=12)
    r.dos("ECHO PCjr DOS app> C:\\DOSAPP.TXT", wait=3)
    r.dos("ECHO PCjr grabber test 0123456789", wait=3)
    r.shot("s1_dos_text")
    J.key("alt+Tab", wait=12)
    aw = r.shot("s1_dos_away")
    J.key("alt+Tab", wait=12)
    r.shot("s1_dos_back")
    r.check("dos_switch_away_shows_windows", aw is not None)
    r.check("dos_screen_restored_exactly", r.raw("s1_dos_text") == r.raw("s1_dos_back"))
    r.dos("EXIT", wait=14)
    dr = r.shot("s1_dos_returned")
    r.check("dos_exit_desktop_exact", dr == p0, differing=len(diff(dr, p0)) if dr and p0 else None)
    da = (r.c / "DOSAPP.TXT").read_bytes() if (r.c / "DOSAPP.TXT").exists() else b""
    r.check("dos_program_wrote_file", da.rstrip(b"\r\n") == b"PCjr DOS app", got=da.decode("latin-1"))
    r.exit_windows("WIN1")
    r.shot("s1_exit_dos")
    return d1


def check_bmp(r, screen):
    from PIL import Image
    p = r.c / "JRTEST.BMP"
    if not p.exists() or not screen:
        return r.check("saved_bmp_matches_screen", False, error="no BMP or no frame")
    with Image.open(p) as bmp:
        idx = bmp.load()
        w, h = bmp.size
        irgb = lambda v: ((v >> 3) & 1) << 3 | (v & 1) << 2 | ((v >> 1) & 1) << 1 | ((v >> 2) & 1)
        ox, oy = PB_ORIGIN
        x0, y0, x1, y1 = PB_CANVAS
        bad = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
               if not (0 <= x - ox < w and 0 <= y - oy < h) or irgb(idx[x - ox, y - oy]) != screen[y * 320 + x]]
        # The light red pixels must form one solid rectangle inside the drag.
        (bx0, by0), (bx1, by1) = PB_DRAG
        red = [(x + ox, y + oy) for y in range(h) for x in range(w) if irgb(idx[x, y]) == 12]
        box = bbox([y * 320 + x for x, y in red])
        box_ok = bool(red) and box[0] >= bx0 - 3 and box[1] >= by0 - 3 and box[2] <= bx1 + 3 and \
            box[3] <= by1 + 3 and (box[2] - box[0]) * (box[3] - box[1]) >= 1000 and \
            len(red) == (box[2] - box[0] + 1) * (box[3] - box[1] + 1)
        return r.check("saved_bmp_matches_screen", not bad and box_ok, bmp_size=[w, h],
                       mismatches=len(bad), first=bad[:3], solid_light_red_box=box, box_ok=box_ok)


Run.check_bmp = check_bmp


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packet", type=Path, required=True)
    ap.add_argument("--win30", type=Path, required=True)
    ap.add_argument("--tools", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    out = a.out.resolve()
    if out.exists():
        raise SystemExit(f"JRSESS: {out} exists")
    r = Run(out)
    (out / "C").mkdir(parents=True)
    shutil.copytree(a.packet, r.c / "PCJREXP")
    shutil.copytree(a.win30, r.c / "WIN30SRC")
    shutil.copyfile(a.tools / "JRHOLDT.COM", r.c / "JRHOLDT.COM")
    res = {"packet_sha256": {p.name: sha(p) for p in sorted(a.packet.iterdir())}}
    J.start(out, 3600)
    try:
        install(r)
        res["install"] = check_install(r, a.packet)
        d1 = session1(r)
        r.start_windows()
        d2 = r.shot("s2_desktop")
        r.check("second_guarded_launch_desktop_identical", d2 is not None and d2 == d1,
                differing=len(diff(d2, d1)) if d2 and d1 else None)
        r.exit_windows("WIN2")
        r.shot("s2_exit_dos")
        r.dos("C:\\JRHOLDT.COM", wait=3)
        r.dos("C:\\PCJREXP\\JRWIN", wait=10)
        r.log_rc("HELD")
        r.shot("e_refused")
    finally:
        J.stop(out)
    log = (r.c / "JRLOG.TXT").read_text(errors="replace").split() if (r.c / "JRLOG.TXT").exists() else []
    lines = [l for l in (r.c / "JRLOG.TXT").read_text(errors="replace").splitlines() if l.strip()] \
        if (r.c / "JRLOG.TXT").exists() else []
    r.check("jrlog_guard_and_launch_results",
            lines == ["GUARD RC=0", "WIN1 RC=0", "WIN2 RC=0", "HELD RC=NONZERO"], lines=lines)
    r.check("refused_launch_did_not_start_windows", J.decode(out / "raw" / "e_refused.png")[0] is None,
            note="the capture is still a text screen")
    res["checks"] = r.checks
    res["passed"] = sum(c["result"] == "PASS" for c in r.checks)
    res["failed"] = sum(c["result"] == "FAIL" for c in r.checks)
    res["verdict"] = "PASS" if not res["failed"] else "FAIL"
    for n in ("KBD.TXT", "DOSAPP.TXT", "JRLOG.TXT", "JRTEST.BMP"):
        if (r.c / n).exists():
            shutil.copyfile(r.c / n, out / n)
    (out / "RESULT.JSN").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("verdict", "passed", "failed")}))
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
