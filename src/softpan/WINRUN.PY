"""Bounded emulator runs, shared lease and cleanup of owned processes only."""
from contextlib import contextmanager
from pathlib import Path
import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import time

def inventory():
    if os.name != "nt":
        raise RuntimeError("This runner requires the Windows process inventory")
    class Entry(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD),
                    ("pid", wintypes.DWORD), ("heap", ctypes.c_size_t),
                    ("module", wintypes.DWORD), ("threads", wintypes.DWORD),
                    ("parent", wintypes.DWORD), ("priority", wintypes.LONG),
                    ("flags", wintypes.DWORD), ("name", wintypes.WCHAR * 260)]
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    k.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k.CreateToolhelp32Snapshot(2, 0)
    if h == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    found = []
    try:
        e = Entry()
        e.size = ctypes.sizeof(e)
        ok = k.Process32FirstW(h, ctypes.byref(e))
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
        while ok:
            if any(n in e.name.lower() for n in ("dosbox", "86box", "pcem", "qemu")):
                found.append({"name": e.name, "pid": e.pid})
            ok = k.Process32NextW(h, ctypes.byref(e))
        if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
            raise ctypes.WinError(ctypes.get_last_error())
        return found
    finally:
        k.CloseHandle(h)


class Runner:
    def __init__(self, record, lock=None):
        if lock is None:
            lock = os.environ.get("TANDY_EMULATOR_LOCK")
        if not lock:
            raise RuntimeError("Set TANDY_EMULATOR_LOCK to the existing shared emulator lease")
        self.record, self.lock = Path(record), Path(lock)
        self.state = {"lock": str(self.lock), "children": [], "status": "RUNNING"}

    def save(self):
        self.record.write_bytes((json.dumps(self.state, indent=2) + "\r\n").encode())

    @contextmanager
    def lease(self):
        import msvcrt
        started = time.monotonic()
        self.state["inventory_before"] = inventory()
        if self.state["inventory_before"]:
            self.state.update(status="BLOCKED", reason="conflicting emulator process")
            self.save()
            raise RuntimeError(self.state["reason"])
        # Never create or replace the shared lease. Its owner initialized it.
        with self.lock.open("rb") as fh:
            if not fh.read(1):
                raise RuntimeError("shared lease is empty")
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            self.state["lease_acquired"] = True
            try:
                conflicts = inventory()
                if conflicts:
                    raise RuntimeError("emulator appeared before lease acquisition: " + repr(conflicts))
                yield self
                self.state["status"] = "PASS"
            except BaseException as e:
                self.state.update(status="FAILED", error=repr(e))
                raise
            finally:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                self.state["lease_released"] = True
                self.state["inventory_after"] = inventory()
                self.state["seconds"] = round(time.monotonic() - started, 3)
                self.save()

    def run(self, command, env, path, timeout=120):
        path = Path(path)
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        with path.open("wb") as log:
            proc = subprocess.Popen([str(x) for x in command], env=env, stdout=log,
                                    stderr=subprocess.STDOUT, startupinfo=si,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            item = {"pid": proc.pid, "command": [str(x) for x in command], "bound_seconds": timeout}
            self.state["children"].append(item)
            self.save()
            try:
                deadline = time.monotonic() + timeout
                while proc.poll() is None:
                    if time.monotonic() >= deadline or path.stat().st_size > 16 * 1024 * 1024:
                        raise TimeoutError("owned emulator bound reached")
                    time.sleep(.1)
                item["exit_code"] = proc.returncode
                if proc.returncode:
                    raise RuntimeError("emulator exit " + str(proc.returncode))
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=10)
                    item["watchdog_stopped"] = True
                item["stopped"] = proc.poll() is not None
                self.save()
