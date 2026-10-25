"""Private current FullXT replay; requires an explicit parent lease handoff.

Uses an existing emulator and only this directory's privately cloned images.
No Windows Setup/media gathering is repeated. No publication is performed.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import msvcrt
import os
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [r"C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local", r"E:\DOSMCP\mcp-server"]
from pyfatfs.PyFatFS import PyFatFS
from src.gdbclient import GdbClient
from src.headless_input import HeadlessCtl

EXE = Path(r"C:\Users\chad\Documents\Codex\2026-10-16\task-10\EMU-STOS1\fixed\86Box.exe")
LEASE = Path(r"C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock")

def ident(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def save(path, value):
    path.write_bytes((json.dumps(value, indent=2) + "\n").replace("\n", "\r\n").encode())

def inventory():
    command = "@(Get-Process -Name dosbox*,86Box,TRACEIO,FIXBOX,pcem,tandybox -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path) | ConvertTo-Json -Compress"
    run = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True, text=True, check=True)
    assert not run.stderr.strip(), run.stderr
    found = json.loads(run.stdout) if run.stdout.strip() else []
    return [found] if isinstance(found, dict) else found

def compare_outputs(fs, mode):
    record = json.loads((HERE / "ORACLE.JSON").read_bytes())[mode]
    different = []
    for name, pin in record["files"].items():
        if not fs.exists(name) or not fs.isfile(name) or ident(fs.readbytes(name)) != pin:
            different.append(name)
    return {"count": len(record["files"]), "different": different}

def installed(fs):
    payload = HERE / "PACKET/WINXT"
    paths = {
        "SOUND.DRV": "WINDOWS/SYSTEM/SOUND.DRV",
        "TSHELL.EXE": "WINDOWS/TSHELL.EXE",
        "TSINPUT.DLL": "WINDOWS/TSINPUT.DLL",
        "TCHIME.EXE": "WINXT/TCHIME.EXE",
        "XPCHIME.EXE": "WINXT/XPCHIME.EXE",
        "TEXIT.EXE": "WINXT/TEXIT.EXE",
        "TP.EXE": "WINXT/TP.EXE",
        "FIXXT.EXE": "WINXT/FIXXT.EXE",
        "XTCLEAN.COM": "WINDOWS/XTCLEAN.COM",
        "HPXY.DRV": "WINDOWS/SYSTEM/HPXY.DRV",
        "TNDYK3.DRV": "WINDOWS/SYSTEM/TNDYK3.DRV",
        "WHEEL.DRV": "WINDOWS/SYSTEM/WHEEL.DRV",
    }
    return {name: {"path": path, "identity": ident(fs.readbytes(path)) if fs.exists(path) and fs.isfile(path) else None, "matches_packet": fs.exists(path) and fs.isfile(path) and fs.readbytes(path) == (payload / name).read_bytes()} for name, path in paths.items()}

def run(out, handoff):
    assert handoff == "root-direct-handoff", "Explicit parent handoff required"
    assert out.parent == HERE and out.name in ("FRESH", "UPDATE", "NEGATIVE", "COLD"), "Only prepared private fixtures are allowed"
    assert not (out / "RESULT.JSON").exists(), "Raw receipt already exists; never overwrite"
    fixture = json.loads((out / "CHECKPOINT.JSON").read_bytes())
    bound = fixture["bound_seconds"]
    assert 60 <= bound <= 1500
    mode = fixture["mode"]
    result = {"schema": 1, "complete": False, "mode": mode, "archive": fixture["archive"], "bound_seconds": bound, "helper": fixture["helper"], "public_assets": fixture["public_assets"], "physical_test": False, "actions": [], "scope": fixture.get("fresh_scope"), "controller": ident(Path(__file__).read_bytes()), "owned_stopped": False, "lease_released": False}
    g = ctl = proc = log = lease = None
    locked = False
    started = time.monotonic()
    try:
        initial = inventory()
        result["process_inventory_before"] = initial
        assert not initial, "Another emulator is active; do not disturb it"
        lease = LEASE.open("rb")
        lease.seek(0)
        msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
        locked = True
        result["lease_acquired"] = True
        assert not inventory(), "Another emulator started before shared lease was acquired"
        for port in (12345, 12346):
            with socket.socket() as test:
                assert test.connect_ex(("127.0.0.1", port)) != 0, "Control port already occupied"
        with PyFatFS(str(out / "DISK.IMG"), offset=17408, read_only=True) as fs:
            assert ident(fs.readbytes(fixture.get("setup_path","SETUP.EXE"))) == fixture["helper"], "Staged Setup differs"
            assert not fs.exists("DONE.TXT"), "Stale completion marker"
            sentinel_before = ident(fs.readbytes("WINXT/KEEP.ME")) if fs.exists("WINXT/KEEP.ME") and fs.isfile("WINXT/KEEP.ME") else None
            if mode in ("update", "cold"):
                assert sentinel_before == ident(b"Unrelated user sentinel; preserve exactly.\r\n"), "Managed preservation sentinel missing or changed before run"
            result["managed_sentinel_before"] = sentinel_before
        result["emulator"] = {"path": str(EXE), "identity": ident(EXE.read_bytes())}
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"
        # The existing emulator's runtime DLL search is process-local only.
        env["PATH"] = r"C:\msys64\ucrt64\bin;" + env.get("PATH", "")
        log = (out / "HOST.LOG").open("wb")
        proc = subprocess.Popen([str(EXE), "-P", str(out), "-R", r"E:\x86box\roms", "-N"], cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
        result["pid"] = proc.pid
        started = time.monotonic()
        print("Owned current FullXT", mode, "PID", proc.pid, "bound", bound, flush=True)
        while time.monotonic() - started < 30:
            assert proc.poll() is None, "Owned emulator exited during startup"
            try:
                g = GdbClient(timeout=3)
                g.connect()
                ctl = HeadlessCtl("127.0.0.1", 12346)
                break
            except OSError:
                if g:
                    g.close()
                g = None
                time.sleep(.3)
        assert g and ctl, "Existing emulator control unavailable"
        def snap(name):
            data = base64.b64decode(ctl.capture_frame_png_b64())
            (out / (name + ".PNG")).write_bytes(data)
            return ident(data)
        gui_since = None
        prepared = mode == "cold"
        last_progress = ""
        last_heartbeat = -60
        text_previous = ""
        screenshots = 0
        while time.monotonic() - started < bound:
            assert proc.poll() is None, "Owned emulator exited"
            g.run_while(lambda: None, settle_seconds=2, start_delay=.01)
            elapsed = round(time.monotonic() - started, 1)
            video = g.read_memory(0x449, 1)[0]
            screen = g.read_memory(0xb8000, 4000)[::2].decode("cp437", errors="replace")
            if screen != text_previous and screenshots < 100:
                screenshots += 1
                (out / ("TEXT%03d.TXT" % screenshots)).write_text(screen, encoding="utf-8")
                (out / "SCREEN.TXT").write_text(screen, encoding="utf-8")
                text_previous = screen
            with PyFatFS(str(out / "DISK.IMG"), offset=17408, read_only=True) as fs:
                guest_log = "COLD.LOG" if mode == "cold" else "BAD.LOG" if mode == "negative" else "PREP.LOG"
                body = fs.readbytes(guest_log).decode("latin1") if fs.exists(guest_log) else ""
                progress = body.splitlines()[-1] if body.splitlines() else screen[-160:]
                save(out / "LIVE.JSON", {"seconds": elapsed, "mode": video, "progress": progress, "screen_tail": screen[-500:]})
                if progress != last_progress or elapsed - last_heartbeat >= 30:
                    print(elapsed, "mode", video, progress, flush=True)
                    last_progress = progress
                    last_heartbeat = elapsed
                if "REFUSED:" in body and mode != "negative":
                    result["error"] = "Native helper refused; inspect PREP.LOG"
                    result["capture"] = snap("REFUSED")
                    break
                if mode == "negative" and fs.exists("DONE.TXT"):
                    logs = {name:fs.readbytes(name).decode("latin1") for name in ("MISSING.LOG","BAD.LOG")}
                    for name,content in logs.items():(out/name).write_bytes(content.encode("latin1"))
                    before=json.loads((out/"BEFORE.JSON").read_bytes())
                    after={p:ident(fs.readbytes(p)) for p in fs.walk.files("WINDOWS")}
                    result["checks"]={
                      "missing_folder_refused": "Directory missing or not readable." in logs["MISSING.LOG"],
                      "archive_not_used_as_fallback": "Complete native" not in logs["MISSING.LOG"] and fs.exists("BARE/WINXT.ZIP"),
                      "same_length_runtime_corruption_refused": "File size/CRC differs from release." in logs["BAD.LOG"] and "TP.EXE" in logs["BAD.LOG"],
                      "windows_unchanged": before==after,
                      "setup_entry_withheld": not fs.exists("SETUPXT.BAT"),
                      "no_incomplete_outputs": not [p for p in fs.walk.files("WINXT") if p.endswith(".NEW")],
                    }
                    result["returned_to_dos"] = True
                    result["complete"] = all(result["checks"].values())
                    result["capture"] = snap("RESULT")
                    break
                if fs.exists("DONE.TXT"):
                    result["returned_to_dos"] = True
                    result["error"] = "Installer returned before normal desktop"
                    result["capture"] = snap("RETURNED")
                    break
                expected_line = "Complete native XR1 %s preparation: %d verified files." % (mode, 370 if mode == "fresh" else 83)
                if mode in ("fresh", "update") and expected_line in body and not prepared:
                    prepared = True
                    result["preparation_seconds_including_boot"] = elapsed
                    print("CURRENT PREPARATION COMPLETE", mode, elapsed, flush=True)
                ready = "Owned entries and cheap payload samples match." in body and "RESERVE:" in body if mode == "cold" else "Windows XT is ready. Starting the desktop." in body
                if prepared and ready and video == 9:
                    if gui_since is None:
                        gui_since = elapsed
                    if elapsed - gui_since >= 60:
                        comparison = compare_outputs(fs, "fresh" if mode == "fresh" else "update")
                        records = installed(fs)
                        sentinel_after = ident(fs.readbytes("WINXT/KEEP.ME")) if fs.exists("WINXT/KEEP.ME") and fs.isfile("WINXT/KEEP.ME") else None
                        result.update({"prepared_comparison": comparison, "installed_files": records, "desktop_mode": video, "graphics_observation_seconds": 60, "normal_desktop_visual_review_required": True, "dos_version": fs.readbytes("DOSVER.TXT").decode("latin1"), "system_ini": fs.readbytes("WINDOWS/SYSTEM.INI").decode("latin1"), "boot_files_unchanged": {name: hashlib.sha256(fs.readbytes(name)).hexdigest() == value for name, value in json.loads((out / "BOOT.JSON").read_bytes()).items()}, "staging_temps": [p for p in fs.walk.files("WINXT") if p.endswith(".NEW")], "installed_wrapper_matches_source": fs.readbytes("WINDOWS/XTCLEAN.COM") == fs.readbytes("WINXT/FILES/XTCLEAN.COM"), "managed_sentinel_after": sentinel_after, "managed_sentinel_preserved": sentinel_after == sentinel_before, "sound_shadow_absent": not fs.exists("WINDOWS/SOUND.DRV"), "capture": snap("DESKTOP")})
                        if mode == "fresh":
                            result["native_crc_scope"] = {"expanded_streams": 284, "all_preflight_and_output_checks_completed": True, "same_run_roles": ["fresh", "native_valid_inputs"], "Windows_Setup_repeated": False}
                        result["complete"] = not comparison["different"] and all(row["matches_packet"] for row in records.values()) and all(result["boot_files_unchanged"].values()) and not result["staging_temps"] and result["installed_wrapper_matches_source"] and result["managed_sentinel_preserved"] and result["sound_shadow_absent"]
                        if not result["complete"]:
                            result["error"] = "Postlaunch current output/runtime preservation check failed"
                        break
                else:
                    # Require one continuously observed graphics interval;
                    # disconnected sightings never accumulate to sixty seconds.
                    gui_since = None
                if "Welcome to Microsoft Windows" in screen or "System Information" in screen:
                    result["capture"] = snap("UNEXPECTED_SETUP")
                    raise RuntimeError("Existing installed OS unexpectedly entered Windows Setup; do not repeat Setup")
        else:
            raise TimeoutError("Private FullXT %s bound%dseconds exceeded" % (mode, bound))
    except BaseException as exc:
        result["complete"] = False
        result["error"] = repr(exc)
    finally:
        if ctl:
            ctl.close()
        if g:
            g.close()
        if proc and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
        result["owned_stopped"] = proc is None or proc.poll() is not None
        if log:
            log.close()
        result["seconds"] = round(time.monotonic() - started, 1)
        if lease and locked:
            lease.seek(0)
            msvcrt.locking(lease.fileno(), msvcrt.LK_UNLCK, 1)
            result["lease_released"] = True
        if lease:
            lease.close()
        # Read finished guest logs only after the owned emulator stopped.
        if proc:
            try:
                with PyFatFS(str(out / "DISK.IMG"), offset=17408, read_only=True) as fs:
                    for name in ("PREP.LOG", "COLD.LOG", "BAD.LOG", "MISSING.LOG"):
                        if fs.exists(name) and fs.isfile(name):
                            (out / name).write_bytes(fs.readbytes(name))
            except BaseException as exc:
                result["complete"] = False
                result["evidence_readback_error"] = repr(exc)
        save(out / "RESULT.JSON", result)
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result["complete"] else 1

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("FRESH", "UPDATE", "NEGATIVE", "COLD"))
    parser.add_argument("--lease-handoff", required=True, choices=("root-direct-handoff",))
    args = parser.parse_args()
    return run(HERE / args.case, args.lease_handoff)

if __name__ == "__main__":
    raise SystemExit(main())
