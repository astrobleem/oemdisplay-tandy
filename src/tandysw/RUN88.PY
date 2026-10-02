#!/usr/bin/env python3
"""Run a prepared Windows 3.0 8088 Tandy test guest with safe memory gating."""
from pathlib import Path
import argparse, configparser, hashlib, os, subprocess, tempfile

DRIVER_SHA = "ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee"
RESERVE_SHA = "644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8"

def find(root, relative):
    current = root
    for name in relative.split("/"):
        matches = [p for p in current.iterdir() if p.name.casefold() == name.casefold()]
        if len(matches) != 1:
            raise SystemExit("Missing or ambiguous guest input: " + relative)
        current = matches[0]
    return current

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("guest", type=Path)
    p.add_argument("dosbox", type=Path)
    p.add_argument("--cycles", type=int, default=20000, help="Emulator speed; not cycle-exact hardware timing")
    p.add_argument("--prepare-only", action="store_true", help="Validate inputs and write config without launching")
    p.add_argument("--config", type=Path, help="Output config path; defaults to a new temporary directory")
    a = p.parse_args()
    guest, dosbox = a.guest.resolve(), a.dosbox.resolve()
    if a.cycles < 1 or a.cycles > 1000000:
        raise SystemExit("--cycles must be 1..1000000")
    if any(c in str(guest) for c in '\r\n"'):
        raise SystemExit("Guest path cannot contain quotes or line breaks")
    if not guest.is_dir() or not dosbox.is_file():
        raise SystemExit("Guest directory and DOSBox executable must exist")
    for name, sha in (("WINDOWS/SYSTEM/TANDY88.DRV", DRIVER_SHA), ("RESERVE.COM", RESERVE_SHA)):
        actual = hashlib.sha256(find(guest, name).read_bytes()).hexdigest()
        if actual != sha:
            raise SystemExit("Unverified guest binary: " + name + " SHA256=" + actual)
    ini = configparser.ConfigParser(interpolation=None, strict=False)
    ini.read(find(guest, "WINDOWS/SYSTEM.INI"), encoding="latin1")
    expected = {"display.drv":"tandy88.drv", "fonts.fon":"egasys.fon", "fixedfon.fon":"egafix.fon", "oemfonts.fon":"egaoem.fon"}
    for key, value in expected.items():
        if ini.get("boot", key, fallback="").strip().casefold() != value:
            raise SystemExit("SYSTEM.INI [boot] must set " + key + "=" + value)
    for name in ("EGASYS.FON", "EGAFIX.FON", "EGAOEM.FON"):
        find(guest, "WINDOWS/SYSTEM/" + name)
    cfg = a.config.resolve() if a.config else Path(tempfile.mkdtemp(prefix="tandy88-")) / "TANDY88.CNF"
    if cfg.exists():
        raise SystemExit("Choose a new --config file; existing files are not overwritten")
    cfg.parent.mkdir(parents=True, exist_ok=True)
    text = r"""[sdl]
autolock=false
fullscreen=false
output=surface
windowresolution=original
[dosbox]
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
working directory option=force
working directory default={work}
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed {cycles}
fpu=false
[render]
scaler=none
doublescan=false
aspect=false
[dos]
xms=false
ems=false
umb=false
[mixer]
nosound=true
[serial]
serial1=serialmouse
[autoexec]
@echo off
mount c "{guest}"
c:
config -get cpu cputype
if not "%CONFIG%"=="8086_prefetch" goto cpufail
reserve
if errorlevel 1 goto memfail
set path=C:\WINDOWS;Z:\
set temp=C:\WINDOWS\TEMP
cd windows
win /r
goto finished
:cpufail
echo CPU CHECK FAILED. WINDOWS WAS NOT STARTED.
goto finished
:memfail
echo VIDEO MEMORY RESERVATION FAILED. WINDOWS WAS NOT STARTED.
:finished
""".format(work=cfg.parent, cycles=a.cycles, guest=guest)
    cfg.write_text(text)
    print("Verified guest inputs; configuration:", cfg)
    if not a.prepare_only:
        # Never allow emulator diagnostics to fill the host disk.
        subprocess.run([str(dosbox), "-nopromptfolder", "-conf", str(cfg)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

if __name__ == "__main__":
    main()
