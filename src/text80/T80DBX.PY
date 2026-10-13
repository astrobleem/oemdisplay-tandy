#!/usr/bin/env python3
"""DOSBox-X machine for the TEXT80 VGA 80x50 session (no VGA ROM is
available to the 86Box set used elsewhere; DOSBox-X's machine=vgaonly has
its own VGA BIOS). Functional evidence only: DOSBox-X does not time an
8088, so no speed figure comes from it.

  used by T80WIN.PY --emulator dosbox --profile vga

The VM is a T80PREP.PY directory (pcp.img, PC DOS 3.20 + Windows 3.0 on a
17-sector, 4-head, 615-cylinder disk). DOSBox-X boots that disk's own DOS
(imgmount + boot), with:
  machine=vgaonly, cputype=8086, core=normal, memsize=1 (640 KB used),
  serial1=serialmouse (Windows' Microsoft serial mouse driver on COM1),
  keyboard input by xdotool on the X display (no window manager: the
  DOSBox-X window is given the focus before each burst).
Captures: ImageMagick 'import' of the DOSBox-X window.
"""
import os
import subprocess
import time
from pathlib import Path

CONF = """[sdl]
output=surface
autolock=false
[dosbox]
machine=vgaonly
memsize=1
captures={vm}/captures
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[speaker]
pcspeaker=false
[serial]
serial1=serialmouse
serial2=disabled
[dos]
xms=false
ems=false
umb=false
[autoexec]
imgmount 2 "{img}" -t hdd -fs none -size 512,17,4,615
boot -l c
"""


def xdo(*args, check=True):
    return subprocess.run(["xdotool", *[str(a) for a in args]], check=check, capture_output=True, text=True)


class DBX:
    """The parts of PCPWIN.Run the TEXT80 sessions use, for DOSBox-X."""

    def __init__(self, vm, dosbox, display=":79"):
        self.vm = Path(vm)
        self.dosbox = dosbox
        os.environ["DISPLAY"] = display
        self.proc = None
        (self.vm / "dec").mkdir(exist_ok=True)

    def start(self):
        conf = self.vm / "DBX.CONF"
        conf.write_text(CONF.format(vm=self.vm, img=self.vm / "pcp.img"))
        env = dict(os.environ, SDL_AUDIODRIVER="dummy")
        self.proc = subprocess.Popen([self.dosbox, "-nopromptfolder", "-nomenu", "-conf", str(conf)],
                                     stdout=open(self.vm / "dosbox.log", "wb"), stderr=subprocess.STDOUT,
                                     env=env, start_new_session=True)
        for _ in range(120):
            if self.window():
                break
            time.sleep(0.5)
        time.sleep(30)                                   # PC DOS boots, AUTOEXEC, prompt

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(20)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def window(self):
        out = xdo("search", "--name", "DOSBox-X", check=False).stdout.split()
        return out[0] if out else None

    def focus(self):
        w = self.window()
        if not w:
            raise SystemExit("T80DBX: DOSBox-X window not found")
        xdo("windowfocus", w, check=False)
        time.sleep(0.2)
        return w

    # -- the PCPWIN.Run interface used by T80WIN ------------------------------
    def key(self, *keys, wait=3):
        self.focus()
        for k in keys:
            xdo("key", k)
            time.sleep(0.15)
        time.sleep(wait)

    def text(self, s, wait=1):
        self.focus()
        xdo("type", "--delay", 120, s)
        time.sleep(wait)

    def shot(self, name, settle=1.0, decode=False):
        time.sleep(settle)
        w = self.focus()
        subprocess.run(["import", "-window", w, str(self.vm / "dec" / (name + ".png"))], check=False)
        return None

    def m(self, *words):
        return None                                      # no scripted mouse here

    def home(self):
        return None

    def rehome(self, x, y, wait=1.5):
        time.sleep(wait)
