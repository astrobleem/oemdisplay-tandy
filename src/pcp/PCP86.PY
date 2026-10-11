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
    def __init__(self, vm, display=":79", out=None):
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
        idx, worst, bad, size, geom = SHOTDEC.decode(str(src))
        if bad:
            raise SystemExit(f"PCP86: {src.name} did not decode exactly ({bad} samples)")
        SHOTDEC.save(idx, str(self.out / (name + ".png")))
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


def prepare(vm, pristine, drv, tools, control_ega=False, mouse="msserial"):
    """Build a private disk from the verified PCjs image plus the test files.

    control_ega: identical machine and disk changes, but an IBM EGA card and
    the install's own Microsoft EGA.DRV, to separate driver faults from
    emulator or harness behaviour."""
    vm.mkdir(parents=True, exist_ok=True)
    img = vm / "pcp.img"
    if img.exists():
        raise SystemExit(f"PCP86: {img} exists; use a fresh VM folder")
    if sha(pristine) != PRISTINE_SHA:
        raise SystemExit("PCP86: pristine image hash mismatch")
    if sha(drv) != DRV_SHA:
        raise SystemExit("PCP86: PCP3216.DRV hash mismatch")
    import shutil
    shutil.copyfile(pristine, img)
    i = f"{img}{PART}"
    changes = []
    tmp = vm / "prep"
    tmp.mkdir(exist_ok=True)
    (tmp / "CONFIG.SYS").write_bytes(CONFIG_SYS.encode())
    mt("mcopy", "-o", "-i", i, str(tmp / "CONFIG.SYS"), "::/CONFIG.SYS")
    changes.append("CONFIG.SYS: only files=30, buffers=30 (removed HIMEM, SMARTDRV, EGA.SYS: an XT has no XMS and no EGA)")
    (tmp / "AUTOEXEC.BAT").write_bytes(AUTOEXEC.encode())
    mt("mcopy", "-o", "-i", i, str(tmp / "AUTOEXEC.BAT"), "::/AUTOEXEC.BAT")
    changes.append("AUTOEXEC.BAT: PATH/TEMP as before, run C:\\PCP\\PCPID, stay at the DOS prompt (no automatic WIN)")
    ini = mt("mtype", "-i", i, "::/WINDOWS/SYSTEM.INI").decode("latin1")
    if not control_ega:
        ini = edit(ini, "display.drv=ega.drv", "display.drv=PCP3216.DRV")
    ini = edit(ini, "[keyboard]\r\nsubtype=\r\ntype=3", "[keyboard]\r\nsubtype=\r\ntype=1")
    (tmp / "SYSTEM.INI").write_bytes(ini.encode("latin1"))
    mt("mcopy", "-o", "-i", i, str(tmp / "SYSTEM.INI"), "::/WINDOWS/SYSTEM.INI")
    changes.append(("SYSTEM.INI: display.drv unchanged (ega.drv, CONTROL)" if control_ega else
                    "SYSTEM.INI: display.drv=PCP3216.DRV") + "; [keyboard] type=1 (PC/XT 83-key instead of AT)")
    win = mt("mtype", "-i", i, "::/WINDOWS/WIN.INI").decode("latin1")
    win = edit(win, "swapdisk=\r\n", "swapdisk=\r\nMouseSpeed=0\r\n")
    (tmp / "WIN.INI").write_bytes(win.encode("latin1"))
    mt("mcopy", "-o", "-i", i, str(tmp / "WIN.INI"), "::/WINDOWS/WIN.INI")
    changes.append("WIN.INI: MouseSpeed=0 (no pointer acceleration, so test moves are exact)")
    mt("mcopy", "-o", "-i", i, str(drv), "::/WINDOWS/SYSTEM/PCP3216.DRV")
    mt("mmd", "-i", i, "::/PCP")
    for n in ("PCPID.COM", "PCPSHOW.EXE", "SHADOW.BIN", "MSTEST.COM"):
        mt("mcopy", "-o", "-i", i, str(Path(tools) / n), "::/PCP/" + n)
    changes.append("added WINDOWS/SYSTEM/PCP3216.DRV and PCP/PCPID.COM, PCPSHOW.EXE, SHADOW.BIN, MSTEST.COM")
    cfg = CFG.replace("gfxcard = plantronics", "gfxcard = ega") if control_ega else CFG
    if mouse == "pty":
        # COM1 -> host pty served by PCPMOUSE.PY; start() fills in the path.
        cfg = cfg.replace("mouse_type = msserial", "mouse_type = none")
        cfg += ("\n[Ports (COM & LPT)]\nserial1_enabled = 1\nserial1_device = serial_passthrough\n"
                "\n[Serial Passthrough (COM) #1]\npath = @PTY@\nreconnect = 1\n")
    else:
        cfg = cfg.replace("mouse_type = msserial", "mouse_type = " + mouse)
    (vm / "86box.cfg").write_text(cfg)
    rec = {"pristine_sha256": PRISTINE_SHA, "driver_sha256": DRV_SHA,
           "tools": {n: sha(Path(tools) / n) for n in ("PCPID.COM", "PCPSHOW.EXE", "SHADOW.BIN", "MSTEST.COM")},
           "control_ega": control_ega, "mouse": mouse, "changes": changes, "86box_cfg": cfg}
    (vm / "PREP.JSN").write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def running(vm):
    pf = Path(vm) / "86box.pid"
    if not pf.exists():
        return None
    pid = int(pf.read_text())
    try:
        os.kill(pid, 0)
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except OSError:
        return None
    return None if state == "Z" else pid


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
    a = ap.parse_args()
    os.environ["DISPLAY"] = a.display
    vm = Path(a.vm)
    if a.cmd == "prepare":
        print(json.dumps(prepare(vm, a.pristine, a.drv, a.tools, a.control_ega, a.mouse), indent=1))
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
        (vm / "86box.pid").write_text(str(p.pid))
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
        if mp.exists():
            try:
                os.kill(int(mp.read_text()), 15)
                print("PCP86: mouse helper stopped")
            except OSError:
                pass
            mp.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
