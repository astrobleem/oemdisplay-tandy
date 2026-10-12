#!/usr/bin/env python3
"""Run one bounded emulator job under the shared emulator lock (Linux host).

  python3 src/xtpan/EMULOCK.PY --lock <lock file> --seconds N --status <out.json> \
      --purpose <name> -- <command ...>

The Linux counterpart of tools/XTLOGO/RUNCHUNK.PY's rule: take the shared
lock with an immediate non-blocking busy refusal, refuse to start while any
other emulator (86Box, DOSBox, DOSBox-X, PCem) is running, run the command
for at most N seconds (whole process group killed at the bound), stop only
processes this job started, release the lock in finally, and write a
status record (times, exit code, conflicts before/after).
"""
import argparse
import datetime
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

NAMES = ("86box", "dosbox", "pcem")


def conflicts(exclude_pgid=None):
    out = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            comm = (d / "comm").read_text().strip().lower()
            pgid = os.getpgid(int(d.name))
        except (OSError, ProcessLookupError):
            continue
        if any(n in comm for n in NAMES) and pgid != exclude_pgid:
            out.append({"pid": int(d.name), "comm": comm})
    return out


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lock", type=Path, required=True)
    ap.add_argument("--seconds", type=int, required=True)
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--purpose", required=True)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if not cmd or not 5 <= a.seconds <= 7200:
        ap.error("a command and a bound of 5..7200 seconds are required")
    rec = {"purpose": a.purpose, "command": cmd, "bound_seconds": a.seconds, "lock": str(a.lock)}
    fh = open(a.lock, "a+")
    held = False
    proc = None
    t0 = time.monotonic()
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held = True
        except BlockingIOError:
            rec["refused"] = "lock busy"
            return 3
        rec["acquired_utc"] = now()
        rec["conflicts_before"] = conflicts()
        if rec["conflicts_before"]:
            rec["refused"] = "another emulator is running"
            return 3
        proc = subprocess.Popen(cmd, start_new_session=True)
        rec["pid"] = proc.pid
        try:
            rec["exit_code"] = proc.wait(timeout=a.seconds)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            rec["terminated_at_bound"] = True
            rec["exit_code"] = None
        return 0 if rec.get("exit_code") == 0 else 1
    finally:
        if proc is not None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)     # leftovers of this job only
            except (ProcessLookupError, PermissionError):
                pass
        rec["conflicts_after"] = conflicts()
        if held:
            fcntl.flock(fh, fcntl.LOCK_UN)
            rec["released_utc"] = now()
        fh.close()
        rec["seconds"] = round(time.monotonic() - t0, 1)
        a.status.write_text(json.dumps(rec, indent=1) + "\n")
        print(json.dumps({k: rec.get(k) for k in ("purpose", "exit_code", "seconds", "refused")}), flush=True)


if __name__ == "__main__":
    sys.exit(main())
