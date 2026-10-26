#!/usr/bin/env python3
"""DOSBox-X IBM PCjr machine for the Windows 3.0 install tests (emulator only).

  python3 src/pcjr/INSTALL/JRDBX.PY start --run <dir> [--seconds N]
  python3 src/pcjr/INSTALL/JRDBX.PY key|text|shot|mouse|stop --run <dir> ...

<run>/C is the guest's drive C: (a host folder), <run>/A.IMG, if present,
is drive A:. The machine: DOSBox-X machine=pcjr, memsizekb=640, 8086 with
prefetch queue, normal core, cycles fixed 200000 (functional evidence only:
no PCjr timing, video-memory contention or speed is modelled or claimed),
DOSBox-X's own DOS (it keeps the PCjr video page at 1800h-1FFFh in a
DOS-owned block, which JRGUARD accepts), no XMS/EMS/UMB, no sound.
COM1 is directserial on the pty of src/pcp/PCPMOUSE.PY, which speaks the
Microsoft serial mouse protocol byte-exactly (one mickey = one pixel with
WIN.INI MouseSpeed=0). Keys go through xdotool to the DOSBox-X window;
captures are ImageMagick 'import' of that window (no guest input), decoded
by decode() to exact 320x200 IRGB frames.

start runs DOSBox-X under src/xtpan/EMULOCK.PY (one emulator at a time) in
the background and returns once the window exists; stop ends it.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MOUSE = ROOT / "src" / "pcp" / "PCPMOUSE.PY"
EMULOCK = ROOT / "src" / "xtpan" / "EMULOCK.PY"
LOCK = os.environ.get("JR_EMULOCK", "/home/claude/work/EMU.LOCK")
DOSBOX = os.environ.get("JR_DOSBOX", "/usr/bin/dosbox-x")

CONF = """[sdl]
output=surface
autolock=false
[dosbox]
machine=pcjr
memsizekb=640
captures={run}/captures
[render]
aspect=false
scaler=normal2x
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
[mixer]
nosound=true
[speaker]
pcspeaker=false
tandy=off
[serial]
serial1=directserial realport:{pty}
serial2=disabled
[dos]
xms=false
ems=false
umb=false
[autoexec]
mount c "{run}/C"
{amount}c:
"""

# DOSBox-X's PCjr/CGA RGB for IRGB 0-15.
PAL = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0),
       (170, 170, 170), (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85),
       (255, 85, 255), (255, 255, 85), (255, 255, 255)]


def xdo(*args, check=True):
    return subprocess.run(["xdotool", *[str(a) for a in args]], check=check, capture_output=True, text=True)


def window():
    out = xdo("search", "--name", "DOSBox-X", check=False).stdout.split()
    return out[0] if out else None


def display_alive():
    return subprocess.run(["xdotool", "getdisplaygeometry"], capture_output=True).returncode == 0


def focus():
    w = window()
    if not w:
        raise SystemExit("JRDBX: DOSBox-X window not found" +
                         ("" if display_alive() else f" (X display {os.environ.get('DISPLAY')} is gone)"))
    xdo("windowfocus", w, check=False)
    time.sleep(0.2)
    return w


def start(run, seconds=3600):
    run = Path(run).resolve()
    if not display_alive():
        raise SystemExit(f"JRDBX: X display {os.environ.get('DISPLAY')} is not running")
    if window():
        raise SystemExit("JRDBX: a DOSBox-X window already exists")
    (run / "captures").mkdir(parents=True, exist_ok=True)
    (run / "dec").mkdir(exist_ok=True)
    subprocess.Popen([sys.executable, str(MOUSE), "serve", "--vm", str(run)],
                     stdout=open(run / "mouse.out", "ab"), stderr=subprocess.STDOUT,
                     stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(40):
        if (run / "mouse.pty").exists():
            break
        time.sleep(0.25)
    pty = (run / "mouse.pty").read_text().strip()
    amount = f'imgmount a "{run}/A.IMG" -t floppy\n' if (run / "A.IMG").exists() else ""
    (run / "RUN.CONF").write_text(CONF.format(run=run, pty=pty[len("/dev/"):], amount=amount))
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    p = subprocess.Popen([sys.executable, str(EMULOCK), "--lock", LOCK, "--seconds", str(seconds),
                          "--status", str(run / "EMULOCK.JSN"), "--purpose", "pcjr-install " + run.name, "--",
                          DOSBOX, "-nopromptfolder", "-nomenu", "-conf", str(run / "RUN.CONF")],
                         stdout=open(run / "dosbox.log", "ab"), stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, env=env, start_new_session=True)
    (run / "emulock.pid").write_text(str(p.pid))
    for _ in range(120):
        if window():
            break
        if p.poll() is not None:
            raise SystemExit("JRDBX: emulator did not start; see dosbox.log / EMULOCK.JSN")
        time.sleep(0.5)
    time.sleep(4)


def stop(run):
    run = Path(run)
    w = window()
    if w:
        # EMULOCK starts DOSBox-X in its own session; end that session and let
        # EMULOCK record the exit and release the lock itself.
        pid = int(xdo("getwindowpid", w).stdout.strip())
        for sig in (signal.SIGTERM, signal.SIGKILL):    # DOSBox-X may ignore SIGTERM
            try:
                os.killpg(os.getpgid(pid), sig)
            except ProcessLookupError:
                break
            for _ in range(60):
                if not window():
                    break
                time.sleep(0.25)
            if not window():
                break
    pidf = run / "emulock.pid"
    if pidf.exists():
        pid = int(pidf.read_text())
        for _ in range(60):
            if not Path(f"/proc/{pid}").exists() or "Z" in Path(f"/proc/{pid}/stat").read_text().split()[2]:
                break
            time.sleep(0.25)
        pidf.unlink()
    mp = run / "mouse.pid"
    if mp.exists():
        try:
            os.kill(int(mp.read_text().split()[0]), signal.SIGTERM)
        except (ProcessLookupError, ValueError):
            pass
        mp.unlink()


def key(*keys, wait=1.0):
    focus()
    for k in keys:
        xdo("key", k)
        time.sleep(0.2)
    time.sleep(wait)


def text(s, wait=1.0):
    focus()
    xdo("type", "--delay", 120, s)
    time.sleep(wait)


def mouse(run, *words):
    subprocess.run([sys.executable, str(MOUSE), "send", "--vm", str(run), *map(str, words)], check=True)


def shot(run, name, settle=1.0):
    """Raw capture of the DOSBox-X window to <run>/raw/<name>.png."""
    time.sleep(settle)
    w = focus()
    d = Path(run) / "raw"
    d.mkdir(exist_ok=True)
    out = d / (name + ".png")
    subprocess.run(["import", "-window", w, str(out)], check=True)
    return out


def decode(path):
    """Exact 320x200 IRGB frame from a 640x400 capture of a 320x200 mode:
    every logical pixel is a 2x2 block of one palette colour. Returns
    (bytes, problems); problems lists blocks that are not uniform or not a
    palette colour (a text-mode or mid-redraw capture fails here)."""
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        if im.size != (640, 400):
            return None, [f"size {im.size}"]
        px = im.load()
    out, bad = bytearray(64000), []
    index = {c: i for i, c in enumerate(PAL)}
    for y in range(200):
        for x in range(320):
            c = px[2 * x, 2 * y]
            if not (px[2 * x + 1, 2 * y] == px[2 * x, 2 * y + 1] == px[2 * x + 1, 2 * y + 1] == c) or c not in index:
                bad.append((x, y, c))
                continue
            out[y * 320 + x] = index[c]
    return bytes(out), bad[:20] + ([f"... {len(bad)} in all"] if len(bad) > 20 else [])


def save_frame(run, name, data):
    from PIL import Image
    im = Image.frombytes("P", (320, 200), data)
    im.putpalette([v for c in PAL for v in c])
    p = Path(run) / "dec" / (name + ".png")
    im.save(p)
    return p


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["start", "stop", "key", "text", "shot", "mouse", "decode"])
    ap.add_argument("--run", required=True)
    ap.add_argument("--seconds", type=int, default=3600)
    ap.add_argument("--wait", type=float, default=1.0)
    ap.add_argument("args", nargs="*")
    a = ap.parse_args(argv)
    os.environ.setdefault("DISPLAY", ":79")
    if a.cmd == "start":
        start(a.run, a.seconds)
    elif a.cmd == "stop":
        stop(a.run)
    elif a.cmd == "key":
        key(*a.args, wait=a.wait)
    elif a.cmd == "text":
        text(" ".join(a.args), wait=a.wait)
    elif a.cmd == "mouse":
        mouse(a.run, *a.args)
    elif a.cmd == "shot":
        print(shot(a.run, a.args[0], settle=a.wait))
    elif a.cmd == "decode":
        data, bad = decode(a.args[0])
        print(json.dumps({"exact": not bad, "problems": [str(b) for b in bad]}))
        if data and not bad and len(a.args) > 1:
            print(save_frame(a.run, a.args[1], data))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
