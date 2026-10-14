#!/usr/bin/env python3
"""Drive an 86Box 6.0 VM under Xvfb for the PCP3216 Windows tests.

Library and CLI. Nothing is downloaded; paths are explicit.

  python3 src/pcp/PCP86.PY start  --box <86Box AppRun> --roms <rom dir> --vm <vm dir> [--display :79]
  python3 src/pcp/PCP86.PY shot   --vm <vm dir> --name <label> [--out <dir>]
  python3 src/pcp/PCP86.PY prepare --vm <new vm dir> --pristine <PCJSIMG output> \
        --drv <PCP3216.DRV> --tools <dir with PCPID.COM, PCPSHOW.EXE, SHADOW.BIN>
  python3 src/pcp/PCP86.PY stop   --vm <vm dir>

Input: keys go through xdotool (XTEST) to the focused 86Box window. The
mouse does NOT: under Xvfb, 86Box 6.0 reads XTEST pointer motion through
XInput2 (src/qt/xinput2_mouse.cpp), mixing XI_Motion and XI_RawMotion
values, and the guest receives wrong or no motion (MSTEST.COM shows zero
packets for absolute moves). The mouse is a Microsoft serial mouse spoken
byte-exactly by PCPMOUSE.PY on a COM1 passthrough pty instead.

Screenshots use 86Box's own Ctrl+F11 capture (PNG of the scaled emulator
output, not an X11 grab) and are decoded to exact 320x200 pixels by
SHOTDEC.PY, which rejects any capture that is not an exact decode.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import importlib.machinery  # noqa: E402

SHOTDEC = importlib.machinery.SourceFileLoader("shotdec", str(HERE / "SHOTDEC.PY")).load_module()


def xdo(*args):
    subprocess.run(["xdotool", *[str(a) for a in args]], check=True)


def focus():
    """Xvfb has no window manager: give the 86Box main window the keyboard."""
    out = subprocess.run(["xdotool", "search", "--name", " - 86Box [0-9]"],
                         capture_output=True, text=True).stdout.split()
    if not out:
        raise SystemExit("PCP86: 86Box window not found")
    xdo("windowfocus", out[0])
    time.sleep(0.2)


class Box:
    def __init__(self, vm, display=":79", out=None, width=320):
        self.width = width
        self.vm = Path(vm)
        self.display = display
        os.environ["DISPLAY"] = display
        self.out = Path(out) if out else self.vm / "dec"
        self.out.mkdir(parents=True, exist_ok=True)
        self.hx, self.hy = 600, 450
        self.log = []

    # -- screenshots -------------------------------------------------
    def shot(self, name, settle=1.0, decode=True):
        """86Box screenshot. decode=False keeps the 86Box PNG as-is (text
        modes, which are 640 pixels wide and cannot be decoded to 320x200)."""
        time.sleep(settle)
        shots = self.vm / "screenshots"
        before = set(shots.iterdir()) if shots.exists() else set()
        focus()
        xdo("key", "ctrl+F11")
        for _ in range(40):
            time.sleep(0.25)
            new = set(shots.iterdir()) - before if shots.exists() else set()
            if new:
                break
        else:
            raise SystemExit("PCP86: no screenshot appeared")
        src = sorted(new)[-1]
        time.sleep(0.5)
        if not decode:
            import shutil
            shutil.copyfile(src, self.out / (name + ".png"))
            self.log.append({"name": name, "source": src.name, "geometry": "raw 86Box capture"})
            return None
        idx, worst, bad, size, geom = SHOTDEC.decode(str(src), self.width)
        if bad:
            raise SystemExit(f"PCP86: {src.name} did not decode exactly ({bad} samples)")
        SHOTDEC.save(idx, str(self.out / (name + ".png")), self.width)
        self.log.append({"name": name, "source": src.name, "geometry": geom})
        return bytes(idx)

    # -- keyboard ----------------------------------------------------
    def key(self, *keys, wait=1.0):
        focus()
        for k in keys:
            xdo("key", k)
            time.sleep(0.15)
        time.sleep(wait)

    def type(self, text, wait=1.0):
        focus()
        xdo("type", "--delay", 120, text)
        time.sleep(wait)


def find_cursor(frame, ref):
    """Bounding box of pixels that differ between two 320x200 frames."""
    d = [i for i in range(64000) if frame[i] != ref[i]]
    if not d:
        return None
    xs = [i % 320 for i in d]
    ys = [i // 320 for i in d]
    return min(xs), min(ys), max(xs), max(ys)


PRISTINE_SHA = "f55fe24baf83d9557e6c16612fbf8b4af5b175bf6b9b6d876e5784222e117561"
DRV_SHA = "67f8a3d77574f8f78d2751f68b9c303fc59fcacd93325b9aa4aaf10288c7c406"
PART = "@@8704"   # FAT partition offset in the converted PCjs disk (PCJSIMG.PY)

CONFIG_SYS = "files = 30\r\nbuffers = 30\r\n"
AUTOEXEC = ("PATH C:\\;C:\\WINDOWS;C:\\PCP\r\nSET TEMP=C:\\WINDOWS\\TEMP\r\n"
            "CD \\PCP\r\nPCPID\r\nCD \\\r\n")
CFG = """[General]
confirm_exit = 0
confirm_reset = 0
confirm_save = 0
vid_renderer = qt_software
video_filter_method = 0
scale = 3

[Machine]
machine = ibmxt86
cpu_family = 8088
cpu_speed = 4772728
cpu_multi = 1
cpu_use_dynarec = 0
mem_size = 640
time_sync = disabled

[Video]
gfxcard = plantronics

[Input devices]
keyboard_type = keyboard_pc_xt
mouse_type = msserial

[Storage controllers]
hdc_1 = xtide

[PC/XT XTIDE #1]
bios = xt

[Hard disks]
hdd_01_fn = pcp.img
hdd_01_ide_channel = 0:0
hdd_01_parameters = 17, 4, 615, 0, ide
"""


# The driver's colour table (DDK order: index bit 0 red, 1 green, 2 blue,
# 3 intensity) as RGB, i.e. the values Windows itself writes into 4-bit BMPs
# on this driver (see TEST16.BMP). IRGB screen colour c is table index
# drv_index(c), so a DIB with these entries maps to exact device colours.
DRIVER_RGB = [(0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128), (128, 0, 128),
              (0, 128, 128), (128, 128, 128), (64, 64, 64), (255, 0, 0), (0, 255, 0), (255, 255, 0),
              (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)]


def drv_index(c):
    return (c & 8) | ((c >> 2) & 1) | (((c >> 1) & 1) << 1) | ((c & 1) << 2)


def bars_bmp(width, height=200):
    """4-bit BMP: 16 vertical bars, bar c (width/16 pixels) shows IRGB c."""
    import struct
    row = bytearray(width // 2)
    for x in range(width):
        v = drv_index(x * 16 // width)
        row[x // 2] |= v << 4 if x % 2 == 0 else v
    stride = (len(row) + 3) & ~3
    pixels = (bytes(row) + bytes(stride - len(row))) * height
    pal = b"".join(bytes((b, g, r, 0)) for r, g, b in DRIVER_RGB)
    off = 14 + 40 + len(pal)
    return (b"BM" + struct.pack("<IHHI", off + len(pixels), 0, 0, off) +
            struct.pack("<IiiHHIIiiII", 40, width, height, 1, 4, 0, len(pixels), 0, 0, 16, 16) +
            pal + pixels)


def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mt(*args, data=None):
    env = dict(os.environ, MTOOLS_SKIP_CHECK="1")
    r = subprocess.run(list(args), env=env, input=data, capture_output=True)
    if r.returncode:
        raise SystemExit(f"PCP86: {' '.join(args[:2])} failed: {r.stderr.decode(errors='replace')}")
    return r.stdout


def edit(text, old, new):
    if text.count(old) != 1:
        raise SystemExit(f"PCP86: expected exactly one {old!r}")
    return text.replace(old, new)


TARGETS = {
    "pcp": {"drv": "PCP3216.DRV", "sha": DRV_SHA, "dir": "PCP", "id": "PCPID",
            "tools": ("PCPID.COM", "PCPSHOW.EXE", "SHADOW.BIN", "MSTEST.COM")},
    "pc1512": {"drv": "PC1512.DRV", "sha": None, "dir": "P15", "id": "P15ID",
               "tools": ("P15ID.COM", "P15SHOW.COM", "MSTEST.COM")},
    # Experimental 40x25 colour text driver (src/txt40) on an IBM XT with an
    # IBM CGA card; --tv switches the CGA output to composite (a TV set).
    "txt40": {"drv": "TXT40.DRV", "sha": None, "dir": "T40", "id": "T40ID",
              "tools": ("T40ID.COM", "MSTEST.COM")},
    # Experimental Tandy Video II 640x200x16 driver (src/tga2) on 86Box's
    # Tandy 1000 SL/2 with owner-supplied BIOS ROMs. Its "id" step is
    # T2RESV, which must run before Windows (it keeps the page from DOS).
    "tga2": {"drv": "TNDYV2.DRV", "sha": None, "dir": "TV2", "id": "T2RESV",
             "tools": ("T2RESV.COM", "T2SHOW.COM", "MSTEST.COM")},
}
# First-party 8x8 fonts (tools/XTFONTS; distributions/WINXT XT*.FON): the
# fixed-cell system font plus the CGA fixed and OEM fonts.
FONTS8 = {"fonts.fon": "XTTSYS.FON", "fixedfon.fon": "XTCFIX.FON", "oemfonts.fon": "XTCOEM.FON"}
FONT_SHA = {"XTTSYS.FON": "dbc26ad717340070b4da1948d97eb5ba24528e0a5cd0853199884d6cca8d51aa",
            "XTCFIX.FON": "3c02c48996d3f8bc9d5a1825bfee966ca4da97ed3e8331472dc78cbe2a63a971",
            "XTCOEM.FON": "8fc600059c0246a1b43c1af47bef17a34df844b3ae21369ce53b9ecc8ccc3055"}
CGA_CARD = """[Video]
gfxcard = cga

[IBM CGA]
display_type = {display}
composite_type = 1
rgb_type = 0
snow_enabled = 1
double_type = 0
"""
# Amstrad PC1512: 8086 at 8 MHz, its own fixed 640x200x16 video, 640KB.
# Its built-in Amstrad mouse is not used (Windows 3.0 has no driver for it).
PC1512_MACHINE = """[Machine]
machine = pc1512
cpu_family = 8086
cpu_speed = 8000000
cpu_multi = 1
cpu_use_dynarec = 0
mem_size = 640
time_sync = disabled
"""
# Tandy 1000 SL/2: 8086 at 8 MHz, its built-in Video II, 640KB (the BIOS
# reports 624KB). Needs the owner's 8079047.hu1/8079048.hu2 ROMs.
SL2_MACHINE = """[Machine]
machine = tandy1000sl2
cpu_family = 8086
cpu_speed = 8000000
cpu_multi = 1
cpu_use_dynarec = 0
mem_size = 640
time_sync = disabled

[Video]
gfxcard = internal
"""


def prepare(vm, pristine, drv, tools, control_ega=False, mouse="msserial", target="pcp", drv_sha=None,
            fonts=None, grid=0, tv=False, only8=False):
    """Build a private disk from the verified PCjs image plus the test files.

    control_ega: identical machine and disk changes, but an IBM EGA card and
    the install's own Microsoft EGA.DRV, to separate driver faults from
    emulator or harness behaviour.
    fonts: folder with the first-party 8x8 fonts (FONTS8), installed as the
    system, fixed and OEM fonts. grid: WIN.INI GridGranularity (units of 8
    pixels). tv: CGA composite output instead of RGB (txt40 only)."""
    vm.mkdir(parents=True, exist_ok=True)
    img = vm / "pcp.img"
    if img.exists():
        raise SystemExit(f"PCP86: {img} exists; use a fresh VM folder")
    if sha(pristine) != PRISTINE_SHA:
        raise SystemExit("PCP86: pristine image hash mismatch")
    tg = TARGETS[target]
    want = drv_sha or tg["sha"]
    if want is None:
        raise SystemExit("PCP86: --drv-sha is required for target " + target)
    if sha(drv) != want:
        raise SystemExit(f"PCP86: {tg['drv']} hash mismatch")
    import shutil
    shutil.copyfile(pristine, img)
    i = f"{img}{PART}"
    changes = []
    tmp = vm / "prep"
    tmp.mkdir(exist_ok=True)
    (tmp / "CONFIG.SYS").write_bytes(CONFIG_SYS.encode())
    mt("mcopy", "-o", "-i", i, str(tmp / "CONFIG.SYS"), "::/CONFIG.SYS")
    changes.append("CONFIG.SYS: only files=30, buffers=30 (removed HIMEM, SMARTDRV, EGA.SYS: an XT has no XMS and no EGA)")
    autoexec = AUTOEXEC if target == "pcp" else (
        AUTOEXEC.replace("C:\\PCP", "C:\\" + tg["dir"]).replace("CD \\PCP", "CD \\" + tg["dir"])
        .replace("PCPID", tg["id"]))
    (tmp / "AUTOEXEC.BAT").write_bytes(autoexec.encode())
    mt("mcopy", "-o", "-i", i, str(tmp / "AUTOEXEC.BAT"), "::/AUTOEXEC.BAT")
    changes.append(f"AUTOEXEC.BAT: PATH/TEMP as before, run C:\\{tg['dir']}\\{tg['id']}, stay at the DOS prompt (no automatic WIN)")
    ini = mt("mtype", "-i", i, "::/WINDOWS/SYSTEM.INI").decode("latin1")
    if not control_ega:
        ini = edit(ini, "display.drv=ega.drv", "display.drv=" + tg["drv"])
    ini = edit(ini, "[keyboard]\r\nsubtype=\r\ntype=3", "[keyboard]\r\nsubtype=\r\ntype=1")
    if fonts:
        for key, name in FONTS8.items():
            if sha(Path(fonts) / name) != FONT_SHA[name]:
                raise SystemExit("PCP86: font hash mismatch: " + name)
            old = [l for l in ini.split("\r\n") if l.lower().startswith(key + "=")]
            if len(old) != 1:
                raise SystemExit("PCP86: SYSTEM.INI has no single " + key)
            ini = edit(ini, old[0] + "\r\n", key + "=" + name + "\r\n")
            mt("mcopy", "-o", "-i", i, str(Path(fonts) / name), "::/WINDOWS/SYSTEM/" + name)
        changes.append("8x8 fonts: " + ", ".join(f"{k}={v}" for k, v in FONTS8.items()) +
                       " (first-party XT fonts, hashes checked)")
    (tmp / "SYSTEM.INI").write_bytes(ini.encode("latin1"))
    mt("mcopy", "-o", "-i", i, str(tmp / "SYSTEM.INI"), "::/WINDOWS/SYSTEM.INI")
    changes.append(("SYSTEM.INI: display.drv unchanged (ega.drv, CONTROL)" if control_ega else
                    "SYSTEM.INI: display.drv=" + tg["drv"]) + "; [keyboard] type=1 (PC/XT 83-key instead of AT)")
    win = mt("mtype", "-i", i, "::/WINDOWS/WIN.INI").decode("latin1")
    win = edit(win, "swapdisk=\r\n", "swapdisk=\r\nMouseSpeed=0\r\n")
    win = edit(win, "Wallpaper=(None)", "Wallpaper=BARS16.BMP")
    if grid:
        win = edit(win, "GridGranularity=0", f"GridGranularity={grid}")
        changes.append(f"WIN.INI: GridGranularity={grid} (windows snap to {8 * grid}-pixel steps)")
    if only8:
        if not fonts:
            raise SystemExit("PCP86: --only-8x8 needs --fonts")
        head, sep, rest = win.partition("[fonts]\r\n")
        body, nxt, tail = rest.partition("\r\n[")
        gone = [ln for ln in body.split("\r\n") if ln and not ln.startswith(";")]
        if not sep or not gone:
            raise SystemExit("PCP86: WIN.INI has no [fonts] entries to disable")
        body = "\r\n".join(ln if (not ln or ln.startswith(";")) else ";" + ln for ln in body.split("\r\n"))
        win = head + sep + body + nxt + tail
        changes.append("WIN.INI [fonts]: every entry commented out (" + "; ".join(gone) +
                       "), so the font mapper can only choose the 8x8 System and Terminal fonts")
    (tmp / "WIN.INI").write_bytes(win.encode("latin1"))
    mt("mcopy", "-o", "-i", i, str(tmp / "WIN.INI"), "::/WINDOWS/WIN.INI")
    changes.append("WIN.INI: MouseSpeed=0 (no pointer acceleration, so test moves are exact); "
                   "Wallpaper=BARS16.BMP (a full-screen 16-colour bar test image, centred)")
    width = 640 if target in ("pc1512", "tga2") else 320
    (tmp / "BARS16.BMP").write_bytes(bars_bmp(width))
    mt("mcopy", "-o", "-i", i, str(tmp / "BARS16.BMP"), "::/WINDOWS/BARS16.BMP")
    changes.append(f"added WINDOWS/BARS16.BMP: {width}x200 4-bit, 16 bars of {width // 16} pixels, "
                   "palette = the driver's colour table (generated, sha256 " + sha(tmp / "BARS16.BMP") + ")")
    mt("mcopy", "-o", "-i", i, str(drv), "::/WINDOWS/SYSTEM/" + tg["drv"])
    mt("mmd", "-i", i, "::/" + tg["dir"])
    for n in tg["tools"]:
        mt("mcopy", "-o", "-i", i, str(Path(tools) / n), "::/" + tg["dir"] + "/" + n)
    changes.append(f"added WINDOWS/SYSTEM/{tg['drv']} and {tg['dir']}/" + ", ".join(tg["tools"]))
    cfg = CFG.replace("gfxcard = plantronics", "gfxcard = ega") if control_ega else CFG
    if target == "txt40":
        cfg = cfg.replace("[Video]\ngfxcard = plantronics\n", CGA_CARD.replace("\r\n", "\n")
                          .format(display=1 if tv else 0))
    elif tv:
        raise SystemExit("PCP86: --tv needs --target txt40")
    if target == "pc1512":
        a = cfg.index("[Machine]")
        b = cfg.index("[Input devices]")
        cfg = cfg[:a] + PC1512_MACHINE + "\n" + cfg[b:]
    if target == "tga2":
        a = cfg.index("[Machine]")
        b = cfg.index("[Input devices]")
        cfg = cfg[:a] + SL2_MACHINE + "\n" + cfg[b:]
    if mouse == "pty":
        # COM1 -> host pty served by PCPMOUSE.PY; start() fills in the path.
        cfg = cfg.replace("mouse_type = msserial", "mouse_type = none")
        cfg += ("\n[Ports (COM & LPT)]\nserial1_enabled = 1\nserial1_device = serial_passthrough\n"
                "\n[Serial Passthrough (COM) #1]\npath = @PTY@\nreconnect = 1\n")
    else:
        cfg = cfg.replace("mouse_type = msserial", "mouse_type = " + mouse)
    (vm / "86box.cfg").write_text(cfg)
    rec = {"target": target, "pristine_sha256": PRISTINE_SHA, "driver": tg["drv"], "driver_sha256": want,
           "tools": {n: sha(Path(tools) / n) for n in tg["tools"]},
           "control_ega": control_ega, "mouse": mouse, "fonts": fonts and dict(FONT_SHA),
           "grid": grid, "tv": tv, "only_8x8": only8, "changes": changes, "86box_cfg": cfg}
    (vm / "PREP.JSN").write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def proc_identity(pid):
    """(state, start time in clock ticks) from /proc, or None if gone."""
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except OSError:
        return None
    return fields[0], fields[19]


def record_pid(path, pid):
    """Store PID with its kernel start time, so a reused PID is never ours."""
    ident = proc_identity(pid)
    if ident is None:
        raise SystemExit(f"PCP86: process {pid} vanished at start")
    Path(path).write_text(f"{pid} {ident[1]}\n")


def owned_pid(path):
    """The recorded process if it is still that same process and not a
    zombie; None otherwise. A PID file without a start time is rejected."""
    p = Path(path)
    if not p.exists():
        return None
    parts = p.read_text().split()
    if len(parts) != 2:
        return None
    pid, start = int(parts[0]), parts[1]
    ident = proc_identity(pid)
    if ident is None or ident[1] != start or ident[0] == "Z":
        return None
    return pid


def running(vm):
    return owned_pid(Path(vm) / "86box.pid")


def stop(vm, wait=15):
    import signal
    pid = running(vm)
    if pid is None:
        return "not running"
    os.kill(pid, signal.SIGTERM)
    for _ in range(wait * 4):
        time.sleep(0.25)
        if running(vm) is None:
            return "stopped"
    if running(vm) != pid:
        return "stopped"
    os.kill(pid, signal.SIGKILL)
    time.sleep(1)
    if running(vm) is not None:
        raise SystemExit("PCP86: 86Box did not stop")
    return "killed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "start", "shot", "stop"])
    ap.add_argument("--vm", required=True)
    ap.add_argument("--box")
    ap.add_argument("--roms")
    ap.add_argument("--pristine")
    ap.add_argument("--drv")
    ap.add_argument("--tools")
    ap.add_argument("--display", default=":79")
    ap.add_argument("--name", default="shot")
    ap.add_argument("--out")
    ap.add_argument("--control-ega", action="store_true")
    ap.add_argument("--mouse", default="msserial", choices=["msserial", "logibus", "pty"])
    ap.add_argument("--target", default="pcp", choices=sorted(TARGETS))
    ap.add_argument("--drv-sha", help="expected SHA-256 of --drv (required for pc1512, txt40)")
    ap.add_argument("--fonts", help="folder with XTTSYS.FON, XTCFIX.FON, XTCOEM.FON (8x8 fonts)")
    ap.add_argument("--grid", type=int, default=0, help="WIN.INI GridGranularity")
    ap.add_argument("--tv", action="store_true", help="txt40: CGA composite output (a TV)")
    ap.add_argument("--only-8x8", action="store_true",
                    help="comment out WIN.INI [fonts] so all text uses the 8x8 fonts (needs --fonts)")
    a = ap.parse_args()
    os.environ["DISPLAY"] = a.display
    vm = Path(a.vm)
    if a.cmd == "prepare":
        print(json.dumps(prepare(vm, a.pristine, a.drv, a.tools, a.control_ega, a.mouse, a.target, a.drv_sha,
                                 a.fonts, a.grid, a.tv, a.only_8x8), indent=1))
    elif a.cmd == "start":
        if running(vm) is not None:
            raise SystemExit("PCP86: an 86Box instance for this VM is already running")
        env = dict(os.environ, XDG_RUNTIME_DIR=str(vm / "xdg"))
        (vm / "xdg").mkdir(mode=0o700, exist_ok=True)
        cfgp = vm / "86box.cfg"
        text = cfgp.read_text()
        if "@PTY@" in text or "serial_passthrough" in text:
            pty_file = vm / "mouse.pty"
            if not pty_file.exists():
                raise SystemExit("PCP86: start PCPMOUSE.PY serve first (no mouse.pty)")
            import re
            text = re.sub(r"(?m)^path = .*$", "path = " + pty_file.read_text().strip(), text)
            text = text.replace("@PTY@", pty_file.read_text().strip())
            cfgp.write_text(text)
        with open(vm / "stdout.log", "ab") as log:
            p = subprocess.Popen([a.box, "-N", "-R", a.roms, "-P", str(vm), str(vm / "86box.cfg")],
                                 cwd=vm, env=env, stdout=log, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
        record_pid(vm / "86box.pid", p.pid)
        print(f"PCP86: started pid {p.pid}")
    elif a.cmd == "shot":
        b = Box(vm, a.display, a.out)
        b.shot(a.name, settle=0)
        print(json.dumps(b.log[-1]))
    else:
        # Only stop 86Box at the DOS prompt: PC DOS 3.20 has no write cache,
        # so nothing is pending on the disk image.
        print("PCP86: " + stop(vm))
        mp = vm / "mouse.pid"
        pid = owned_pid(mp)
        if pid is not None:
            os.kill(pid, 15)
            print("PCP86: mouse helper stopped")
        elif mp.exists():
            print("PCP86: mouse.pid is stale or reused; nothing signalled")
        if mp.exists():
            mp.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
