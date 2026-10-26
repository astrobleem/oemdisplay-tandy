"""Bounded local queue for existing builders; retain their actual lease guard."""
import msvcrt
from pathlib import Path
import runpy
import sys
import time

original = msvcrt.locking
opened = Path.open
seconds = int(sys.argv.pop(1)) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 180
deadline = time.monotonic() + seconds


class LeaseRead:
    def __init__(self, f):
        self.f = f
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.f.close()
    def __getattr__(self, name):
        return getattr(self.f, name)
    def read(self, count):
        # RUNDOS checks the existing marker before trying its real byte lock.
        while True:
            try:
                return self.f.read(count)
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)


def queue_open(path, *args, **kw):
    f = opened(path, *args, **kw)
    if str(path).lower() == r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock'.lower():
        print('Waiting for shared emulator lease, at most %d seconds' % seconds, flush=True)
        return LeaseRead(f)
    return f


def queued(fd, mode, count):
    if mode != msvcrt.LK_NBLCK:
        return original(fd, mode, count)
    while True:
        try:
            return original(fd, mode, count)
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.1)


msvcrt.locking = queued
Path.open = queue_open
target = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(target, run_name='__main__')
