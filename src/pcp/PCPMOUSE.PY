#!/usr/bin/env python3
"""Byte-exact Microsoft serial mouse for an 86Box COM1 passthrough.

  python3 src/pcp/PCPMOUSE.PY serve --vm <vm dir>        (background helper)
  python3 src/pcp/PCPMOUSE.PY send  --vm <vm dir> <command> ...

Why: under Xvfb, 86Box 6.0 reads XTEST pointer input through XInput2 and
mixes absolute and relative values (src/qt/xinput2_mouse.cpp), so injected
host mouse motion reaches the guest wrong or not at all (MSTEST.COM shows
it). Instead, 86Box's "Serial Passthrough (COM)" device connects guest COM1
to a host pty, and this helper speaks the Microsoft 2-button serial mouse
protocol on the pty itself.

serve: opens a pty pair, writes the slave path to <vm>/mouse.pty, and
reads commands, one per line, from the FIFO <vm>/mouse.ctl:
    ident on|off    repeat 'M' every 100 ms (mouse detection) or stop
    move DX DY      exact relative motion, split into packets of +-127
    down | up       left button state
    click           left down then up
    rclick          right down then up
    pace B G        seconds/1000 between bytes (B) and after packets (G)
    burst N DX DY   N separate packets of DX,DY (like a real moving mouse)
    sync TOKEN      write TOKEN to <vm>/mouse.sync once all earlier commands
                    have been sent in full (commands run in order)
    log             append counters to <vm>/mouse.log
A pty carries no DTR/RTS, so the helper cannot see a mouse reset; it
answers detection by repeating 'M'. A lone 'M' is a sync byte without data
bytes, which the protocol discards. Packets are paced at 1200-baud byte
timing (7N1 = 9 bits, 7.5 ms) so the emulated 8250 cannot overrun.
"""
import os
import sys
import threading
import time
from pathlib import Path

# Seconds between bytes. 1200-baud 7N1 is 7.5 ms; PCPMOUSE_BYTE_MS overrides.
BYTE_TIME = float(os.environ.get("PCPMOUSE_BYTE_MS", "7.5")) / 1000.0


def packet(dx, dy, left, right=False):
    dx &= 0xFF
    dy &= 0xFF
    b0 = 0x40 | (0x20 if left else 0) | (0x10 if right else 0) | ((dy >> 6) & 3) << 2 | ((dx >> 6) & 3)
    return bytes([b0, dx & 0x3F, dy & 0x3F])


def split(v):
    out = []
    while v:
        s = max(-127, min(127, v))
        out.append(s)
        v -= s
    return out


def serve(vm):
    # Unix-only: imported here so packet()/split() load on any host.
    import pty
    import select
    import tty
    vm = Path(vm)
    master, slave = pty.openpty()
    tty.setraw(slave)
    name = os.ttyname(slave)
    (vm / "mouse.pty").write_text(name + "\n")
    # PID plus kernel start time (see PCP86.owned_pid): a reused PID is
    # never mistaken for this helper.
    start = Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(")", 1)[1].split()[19]
    (vm / "mouse.pid").write_text(f"{os.getpid()} {start}\n")
    ctl = vm / "mouse.ctl"
    if ctl.exists():
        ctl.unlink()
    os.mkfifo(ctl)
    state = {"ident": False, "left": False, "packets": 0, "bytes_out": 0, "bytes_in": 0,
             "byte_s": BYTE_TIME, "gap_s": 0.02}
    lock = threading.Lock()

    def put(data):
        for b in data:
            os.write(master, bytes([b]))
            state["bytes_out"] += 1
            time.sleep(state["byte_s"])

    def ident_loop():
        while True:
            time.sleep(0.1)
            with lock:
                if state["ident"]:
                    put(b"M")

    def drain_loop():
        while True:
            r, _, _ = select.select([master], [], [], 0.5)
            if r:
                try:
                    state["bytes_in"] += len(os.read(master, 256))
                except OSError:
                    pass

    threading.Thread(target=ident_loop, daemon=True).start()
    threading.Thread(target=drain_loop, daemon=True).start()
    print(f"PCPMOUSE: serving on {name}", flush=True)
    while True:
        with open(ctl) as f:
            for line in f:
                cmd = line.split()
                if not cmd:
                    continue
                with lock:
                    if cmd[0] == "ident":
                        state["ident"] = cmd[1] == "on"
                    elif cmd[0] == "move":
                        dx, dy = int(cmd[1]), int(cmd[2])
                        xs, ys = split(dx), split(dy)
                        n = max(len(xs), len(ys))
                        xs += [0] * (n - len(xs))
                        ys += [0] * (n - len(ys))
                        for a, c in zip(xs, ys):
                            put(packet(a, c, state["left"]))
                            state["packets"] += 1
                            time.sleep(state["gap_s"])
                    elif cmd[0] in ("down", "up", "click"):
                        seq = {"down": [True], "up": [False], "click": [True, False]}[cmd[0]]
                        for st in seq:
                            state["left"] = st
                            put(packet(0, 0, st))
                            state["packets"] += 1
                            time.sleep(0.15)
                    elif cmd[0] == "pace":
                        state["byte_s"] = float(cmd[1]) / 1000.0
                        state["gap_s"] = float(cmd[2]) / 1000.0
                    elif cmd[0] == "burst":
                        n, dx, dy = int(cmd[1]), int(cmd[2]), int(cmd[3])
                        for _ in range(n):
                            put(packet(dx, dy, state["left"]))
                            state["packets"] += 1
                            time.sleep(state["gap_s"])
                    elif cmd[0] == "rclick":
                        for st in (True, False):
                            put(packet(0, 0, state["left"], st))
                            state["packets"] += 1
                            time.sleep(0.15)
                    elif cmd[0] == "sync":
                        # Every earlier command has been sent in full.
                        (vm / "mouse.sync").write_text(cmd[1] + "\n")
                    elif cmd[0] == "log":
                        with open(vm / "mouse.log", "a") as lf:
                            lf.write(" ".join(f"{k}={v}" for k, v in state.items()) + "\n")


def send(vm, words):
    with open(Path(vm) / "mouse.ctl", "w") as f:
        f.write(" ".join(words) + "\n")


def main(argv):
    if len(argv) < 4 or argv[2] != "--vm":
        print(__doc__)
        return 2
    if argv[1] == "serve":
        serve(argv[3])
    elif argv[1] == "send":
        send(argv[3], argv[4:])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
