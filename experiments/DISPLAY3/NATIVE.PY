#!/usr/bin/env python3
"""Native DISPLAY3 qualification backend, called only by NATIVE.PS1.
MIT, Copyright (c) 2026 Windows XT contributors.

The PowerShell wrapper owns the shared lock and total deadline. All guests
use fresh task-owned directories, never installed/CF Windows. Source is
unchanged; rebuilt driver hashes must match every accepted pin exactly.
"""
import argparse
import hashlib
import importlib.machinery
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / "PINS.JSN").read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text(path, value):
    Path(path).write_bytes(value.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))


def run(command, log, timeout=180):
    print("RUN " + str(log), flush=True)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYTHONDONTWRITEBYTECODE="1")
    with Path(log).open("wb") as handle:
        subprocess.run(list(map(str, command)), env=env, stdout=handle,
                       stderr=subprocess.STDOUT, timeout=timeout, check=True)


def config(root, machine, commands, extra=""):
    path = root / "RUN.CNF"
    value = ("[sdl]\noutput=surface\n[dosbox]\nmachine=" + machine +
        "\nmemsizekb=640\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n"
        "[mixer]\nnosound=true\n[midi]\nmididevice=none\n[dos]\nxms=false\nems=false\numb=false\n"
        "[autoexec]\n@echo off\nmount c \"" + str(root) + "\"\n" + extra + "\nc:\n" + commands + "\nexit\n")
    text(path, value)
    return path


def dosbox(exe, cfg, log, timeout=90):
    run([exe, "-nopromptfolder", "-nogui", "-nomenu", "-conf", cfg], log, timeout)


def fake_source(marker, code, check_windows=False):
    checks = ""
    if check_windows:
        checks = """
    cmp byte ptr ds:[80h],3
    je a1
    jmp bad
a1: cmp word ptr ds:[81h],2F20h
    je a2
    jmp bad
a2: cmp byte ptr ds:[83h],'R'
    je a3
    jmp bad
a3: mov ah,19h
    int 21h
    cmp al,2
    je a4
    jmp bad
a4: mov si,OFFSET cwd
    mov dl,0
    mov ah,47h
    int 21h
    jnc a5
    jmp bad
a5: mov si,OFFSET cwd
    mov di,OFFSET expected
    mov cx,8
a6: lodsb
    cmp al,[di]
    je a7
    jmp bad
a7: inc di
    loop a6
"""
    return (".8086\nCODE SEGMENT PARA PUBLIC 'CODE'\nASSUME CS:CODE,DS:CODE\nORG 100h\nstart:\n"
        "    mov ax,cs\n    mov ds,ax\n" + checks + """
    mov dx,OFFSET trace
    mov ax,3D02h
    int 21h
    jnc opened
    mov dx,OFFSET trace
    xor cx,cx
    mov ah,3Ch
    int 21h
    jc bad
opened:
    mov bx,ax
    xor cx,cx
    xor dx,dx
    mov ax,4202h
    int 21h
    mov dx,OFFSET mark
    mov cx,1
    mov ah,40h
    int 21h
    mov ah,3Eh
    int 21h
""" + f"    mov ax,4C{code:02X}h\n    int 21h\n" + """
bad: mov ax,4C63h
    int 21h
trace db 'C:\TRACE.TXT',0
""" + f"mark db '{marker}'\n" + "cwd db 64 dup(0)\nexpected db 'WINDOWS',0\nCODE ENDS\nEND start\n")


def compile_exit(exe, view, out):
    out.mkdir()
    shutil.copyfile(HERE / "JREXIT.C", out / "JREXIT.C")
    text(out / "JREXIT.DEF", "NAME JREXIT\nEXETYPE WINDOWS\nCODE PRELOAD MOVEABLE DISCARDABLE\n"
         "DATA PRELOAD MOVEABLE MULTIPLE\nHEAPSIZE 2048\nSTACKSIZE 4096\n")
    text(out / "JREXIT.RSP", "JREXIT.OBJ\nJREXIT.EXE\nJREXIT.MAP\nC:\LIB\SLIBCEW.LIB C:\LIB\LIBW.LIB\nJREXIT.DEF\n")
    text(out / "BUILD.BAT", "@ECHO OFF\nSET PATH=C:\\BIN\nSET INCLUDE=C:\\DDK\\286\\INC;C:\\INCLUDE\n"
         "SET LIB=C:\LIB\nCL /nologo /c /G0 /Gw /AS /W3 /Od JREXIT.C > BUILD.LOG\n"
         "IF ERRORLEVEL 1 GOTO FAILED\nLINK4 /NOE /NOD @JREXIT.RSP >> BUILD.LOG\n"
         "IF ERRORLEVEL 1 GOTO FAILED\nECHO PASS>STATUS.TXT\nGOTO DONE\n:FAILED\nECHO FAIL>STATUS.TXT\n:DONE\nEXIT\n")
    cfg = config(out, "tandy", "r:\nBUILD.BAT", 'mount r "' + str(out) + '"\n')
    # Compiler sees the pinned view at C:, work at R:.
    value = cfg.read_text().replace('mount c "' + str(out) + '"', 'mount c "' + str(view) + '"')
    text(cfg, value)
    dosbox(exe, cfg, out / "HOST.LOG")
    if (out / "STATUS.TXT").read_text().strip() != "PASS":
        raise ValueError("Win16 exit-helper compiler/link failure")
    # Host-only resource attachment from the established driver packer.
    pack = importlib.machinery.SourceFileLoader("native_packres", str(view / "src/tandysw/PACKRES.PY")).load_module()
    records = [(6, 1, 0x1030, bytes([0, 13]) + b"DISPLAY3 EXIT" + bytes(14))]
    data, delta = pack.attach_ne((out / "JREXIT.EXE").read_bytes(), records)
    (out / "JREXIT.EXE").write_bytes(data)
    ne = struct.unpack_from("<I", data, 0x3c)[0]
    if data[ne:ne+2] != b"NE" or struct.unpack_from("<H", data, ne+0x3e)[0] != 0x0300:
        raise ValueError("Win16 helper expected-version mismatch")
    return out / "JREXIT.EXE"


def fixture_case(exe, out, binaries, guard, win, expected_code, machine="pcjr", foreign="D", cycles=1):
    out.mkdir()
    (out / "PCJREXP").mkdir()
    (out / "WINDOWS").mkdir()
    (out / "FOREIGN").mkdir()
    drive = out / "D_DRIVE"
    (drive / "FOREIGN").mkdir(parents=True)
    shutil.copyfile(binaries / "JRWIN.COM", out / "PCJREXP/JRWIN.COM")
    if guard:
        shutil.copyfile(guard, out / "PCJREXP/JRGUARD.COM")
    if win:
        shutil.copyfile(win, out / "WINDOWS/WIN.COM")
    calls = ""
    for _ in range(cycles):
        calls += ("C:\PCJREXP\JRWIN.COM\n" + f"IF ERRORLEVEL {expected_code+1} GOTO FAILED\n"
                  + (f"IF NOT ERRORLEVEL {expected_code} GOTO FAILED\n" if expected_code else ""))
    text(out / "CASE.BAT", "@ECHO OFF\n" + calls + "CD > C:\CWD.TXT\nECHO PASS>C:\CASE.TXT\n"
         "GOTO DONE\n:FAILED\nECHO FAIL>C:\CASE.TXT\n:DONE\nEXIT\n")
    commands = foreign.lower() + ":\nCD \FOREIGN\nC:\CASE.BAT"
    cfg = config(out, machine, commands, 'mount d "' + str(drive) + '"')
    dosbox(exe, cfg, out / "HOST.LOG", 30)
    if (out / "CASE.TXT").read_text().strip() != "PASS":
        raise ValueError("launcher status failed: " + out.name)
    trace = (out / "TRACE.TXT").read_text() if (out / "TRACE.TXT").exists() else ""
    cwd = (out / "CWD.TXT").read_text().strip()
    return dict(name=out.name, verdict="PASS", trace=trace, cwd=cwd, expected_exit=expected_code)


def ini_setting(value, section, key, replacement):
    active, count, lines = "", 0, []
    for line in value.splitlines():
        match = re.fullmatch(r"\s*\[([^]]+)\]\s*", line)
        if match:
            active = match.group(1).lower()
        if active == section.lower() and re.match(r"(?i)^\s*" + re.escape(key) + "\s*=", line):
            line, count = key + "=" + replacement, count + 1
        lines.append(line)
    if count != 1:
        raise ValueError("private fixture INI key not unique in section: " + section + "/" + key)
    return "\n".join(lines) + "\n"


def windows_cycles(exe, out, template, binaries, helper):
    out.mkdir()
    shutil.copytree(template, out / "WINDOWS")
    (out / "PCJREXP").mkdir()
    for name in ("JRGUARD.COM", "JRWIN.COM"):
        shutil.copyfile(binaries / name, out / "PCJREXP" / name)
    shutil.copyfile(binaries / "TNDYJR.DRV", out / "WINDOWS/SYSTEM/TNDYJR.DRV")
    shutil.copyfile(helper, out / "WINDOWS/JREXIT.EXE")
    ini = out / "WINDOWS/SYSTEM.INI"
    value = ini.read_text()
    changes = {"display.drv": "TNDYJR.DRV", "fonts.fon": "EGASYS.FON", "fixedfon.fon": "EGAFIX.FON",
               "oemfonts.fon": "EGAOEM.FON", "286grabber": "CGA.GR2", "mouse.drv": "MOUSE.DRV", "sound.drv": "SOUND.DRV"}
    for key, val in changes.items():
        value = ini_setting(value, "boot", key, val)
    text(ini, value)
    winini = out / "WINDOWS/WIN.INI"
    value = winini.read_text()
    value = ini_setting(value, "windows", "load", "C:\\WINDOWS\\JREXIT.EXE")
    value = ini_setting(value, "windows", "run", "")
    text(winini, value)
    # Empty groups avoid unrelated AT/EGA saved-group geometry prompts.
    text(out / "WINDOWS/PROGMAN.INI", "[Settings]\nWindow=0 0 320 200 1\n[Groups]\n")
    text(out / "CYCLE.BAT", "@ECHO OFF\nSET PATH=C:\WINDOWS\nC:\PCJREXP\JRWIN.COM\n"
         "IF ERRORLEVEL 1 GOTO FAILED\nECHO FIRST_RETURN=0>C:\CYCLE.TXT\n"
         "C:\PCJREXP\JRWIN.COM\nIF ERRORLEVEL 1 GOTO FAILED\nECHO SECOND_RETURN=0>>C:\CYCLE.TXT\n"
         "ECHO PASS>>C:\CYCLE.TXT\nGOTO DONE\n:FAILED\nECHO FAIL>>C:\CYCLE.TXT\n:DONE\nEXIT\n")
    cfg = config(out, "pcjr", "CD \PCJREXP\nC:\CYCLE.BAT")
    dosbox(exe, cfg, out / "HOST.LOG", 75)
    result = (out / "CYCLE.TXT").read_text()
    observed = (out / "JREXIT.LOG").read_text()
    if result.count("RETURN=0") != 2 or "FAIL" in result or observed.count("width=320 height=200 colors=16") != 2 or observed.count("WINDOWS_VERSION=3.0") != 2 or "EXIT_REFUSED" in observed:
        raise ValueError("real Windows guarded cycles did not qualify")
    return dict(cycles=2, normal_returns=result.splitlines(), observations=observed.splitlines(),
                scope="Owned Windows 3.0 clone, normalized EGA fonts/CGA grabber, standard mouse/sound, empty groups; caps/normal exit only, not a new full GDI or DOS-box oracle.")


def main():
    ap = argparse.ArgumentParser()
    for name in ("view", "runtime-repo", "deps", "dosbox", "out", "windows-template"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--reuse-native", type=Path)
    a = ap.parse_args()
    if not os.environ.get("DISPLAY3_LEASE_HELD"):
        raise SystemExit("Run only through the allocated NATIVE.PS1 wrapper")
    head = subprocess.check_output(["git", "-C", str(a.runtime_repo), "rev-parse", "HEAD"]).decode().strip()
    if head != PINS["runtime_source_commit"]:
        raise ValueError("experimental builder source head mismatch")
    subprocess.run(["git", "-C", str(a.runtime_repo), "diff", "--exit-code", "HEAD", "--",
                    "src/pc1512", "src/pcp", "src/pcjr"], check=True)
    a.out.mkdir(parents=True, exist_ok=False)
    binary = a.out / "BIN"
    binary.mkdir()
    built = {}
    for key, script, folder, report, field in (
        ("PC1512", "src/pc1512/BUILD15.PY", "P15", "P15RES.JSON", "staged_patched_sha256"),
        ("PCP3216", "src/pcp/BUILDPCP.PY", "PCP", "PCPRES.JSON", "plantronics_edits_staged_sha256"),
        ("PCJR", "src/pcjr/BUILDJR.PY", "PCJR", "JRRESULT.JSON", "pcjr_edits_staged_sha256")):
        dest = (a.reuse_native or a.out) / folder
        if not a.reuse_native:
            run([sys.executable, "-B", a.runtime_repo / script, "--repo", a.view, "--dosbox", a.dosbox, "--out", dest], a.out / (folder + ".LOG"))
        pin = PINS["drivers"][key]
        p = dest / pin["file"]
        if p.stat().st_size != pin["bytes"] or sha(p) != pin["sha256"]:
            raise ValueError("rebuilt driver differs from accepted pin: " + key)
        data = json.loads((dest / report).read_bytes())
        if data[field] != pin["staged"]:
            raise ValueError("staged source identity mismatch: " + key)
        shutil.copyfile(p, binary / p.name)
        built[key] = dict(bytes=p.stat().st_size, sha256=sha(p), staged_source_match=True)
        print("PIN MATCH " + key + " " + sha(p), flush=True)
    sources = a.out / "FAKES"
    sources.mkdir()
    paths = [a.runtime_repo / "src/pcjr/JRGUARD.ASM", HERE / "JRWIN.ASM"]
    for code in (0, 1, 2, 7, 128):
        p = sources / ("G" + str(code) + ".ASM")
        text(p, fake_source("G", code))
        paths.append(p)
    for code in (0, 7):
        p = sources / ("W" + str(code) + ".ASM")
        text(p, fake_source("W", code, True))
        paths.append(p)
    com = (a.reuse_native or a.out) / "COM"
    command = [sys.executable, "-B", a.runtime_repo / "src/pcjr/BUILDCOM.PY", "--deps", a.deps,
               "--dosbox", a.dosbox, "--out", com]
    for p in paths:
        command.extend(["--src", p])
    if a.reuse_native:
        if (com / "JRWIN.ASM").read_bytes() != (HERE / "JRWIN.ASM").read_bytes():
            raise ValueError("reused launcher source changed")
        prior = json.loads((com / "BUILD.JSN").read_bytes())
        if prior["verdict"] != "PASS" or any(sha(com / name) != pin["sha256"]
                or (com / name).stat().st_size != pin["bytes"] for name, pin in prior["built"].items()):
            raise ValueError("reused COM build identity mismatch")
    else:
        run(command, a.out / "COM.LOG")
    for name in ("JRGUARD.COM", "JRWIN.COM"):
        shutil.copyfile(com / name, binary / name)
    guard = PINS["drivers"]["PCJR"]["guard"]
    if sha(binary / "JRGUARD.COM") != guard["sha256"] or (binary / "JRGUARD.COM").stat().st_size != guard["bytes"]:
        raise ValueError("rebuilt guard pin mismatch")
    print("PIN MATCH JRGUARD; JRWIN built " + sha(binary / "JRWIN.COM"), flush=True)
    cases = []
    for code in (0, 1, 2, 7, 128):
        for foreign in ("C", "D"):
            row = fixture_case(a.dosbox, a.out / ("CASE" + str(code) + foreign), binary,
                               com / ("G" + str(code) + ".COM"), com / "W0.COM", code, foreign=foreign)
            if row["trace"] != ("GW" if code == 0 else "G"):
                raise ValueError("guard did not precede/block Windows: " + row["name"])
            cases.append(row)
    row = fixture_case(a.dosbox, a.out / "RELAUNCH", binary, com / "G0.COM", com / "W0.COM", 0, cycles=2)
    if row["trace"] != "GWGW":
        raise ValueError("relaunch skipped guard")
    cases.append(row)
    cases.append(fixture_case(a.dosbox, a.out / "WINERR", binary, com / "G0.COM", com / "W7.COM", 7))
    cases.append(fixture_case(a.dosbox, a.out / "NOGUARD", binary, None, com / "W0.COM", 1))
    cases.append(fixture_case(a.dosbox, a.out / "NOWIN", binary, com / "G0.COM", None, 1))
    positive = fixture_case(a.dosbox, a.out / "REALGUARD", binary, binary / "JRGUARD.COM", com / "W0.COM", 0)
    if positive["trace"] != "W":
        raise ValueError("actual guard positive did not start stub Windows")
    negative = fixture_case(a.dosbox, a.out / "WRONGMODEL", binary, binary / "JRGUARD.COM", com / "W0.COM", 1, machine="tandy")
    if negative["trace"]:
        raise ValueError("actual guard started Windows on non-PCjr")
    helper = compile_exit(a.dosbox, a.view, a.out / "WINHELP")
    real = windows_cycles(a.dosbox, a.out / "WINDOWS", a.windows_template, binary, helper)
    result = dict(verdict="PASS", drivers=built, launcher_sha256=sha(binary / "JRWIN.COM"),
                  launcher_source_sha256=sha(HERE / "JRWIN.ASM"), native_cases=cases,
                  actual_guard_positive=positive, actual_guard_negative=negative,
                  real_windows_cycles=real["cycles"], windows=real, emulator_sha256=sha(a.dosbox),
                  physical_hardware_qualified=False, reused_verified_native_builds=bool(a.reuse_native),
                  elapsed_seconds=round(time.monotonic() - START, 2))
    (a.out / "NATIVE.JSN").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1), flush=True)


START = time.monotonic()
if __name__ == "__main__":
    main()
