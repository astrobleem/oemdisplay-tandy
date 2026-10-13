#!/usr/bin/env python3
"""Host test of T80SET.C (the reversible TEXT80 setup) - no DOS, no emulator.

  python3 src/text80/T80SETT.PY [--ini-dir <dir with a real SYSTEM.INI, WIN.INI>]

Compiles T80SET.C with the host C compiler (a few DOS library names mapped
to POSIX ones, "/" as the path separator) and runs it on synthetic Windows
3.0 INI files (and, with --ini-dir, on copies of real ones, which are not
in the repository). Requires: ON sets exactly the documented [boot] keys,
appends the helper to load= keeping every existing entry (also when load=
is missing or empty, and not twice), only adds the two [fonts] lines;
a second ON is refused; OFF restores both files byte for byte and removes
the backups; ON with no [fonts] section fails and leaves both files
unchanged.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIM = """#include <strings.h>
#include <unistd.h>
#include <ctype.h>
#define strnicmp strncasecmp
#define stricmp strcasecmp
static char *strupr(char *s){char *p=s;for(;*p;p++)*p=toupper((unsigned char)*p);return s;}
"""
SYSTEM = ("[boot]\r\nshell=progman.exe\r\nfixedfon.fon=egafix.fon\r\noemfonts.fon=egaoem.fon\r\n"
          "fonts.fon=egasys.fon\r\ndisplay.drv=ega.drv\r\n\r\n[keyboard]\r\ntype=1\r\n")
FONTS = "[fonts]\r\nHelv 8,10,12,14,18,24 (EGA res)=HELVB.FON\r\nModern=MODERN.FON\r\n"
fails = []


def expect(label, ok):
    print(("ok   " if ok else "FAIL ") + label)
    if not ok:
        fails.append(label)


def ini(load_line):
    return "[windows]\r\n" + load_line + "run=\r\nBeep=yes\r\n\r\n" + FONTS + "\r\n[ports]\r\nCOM1:=9600\r\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ini-dir", type=Path)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "shim.h").write_text(SHIM)
        src = (HERE / "T80SET.C").read_text(errors="replace").replace("#include <io.h>", '#include "shim.h"')
        (t / "t80set.c").write_text(src)
        r = subprocess.run(["cc", "-std=gnu89", '-DSEP="/"', "-Wall", "-o", str(t / "t80set"), str(t / "t80set.c")],
                           capture_output=True, text=True)
        expect("T80SET.C compiles on the host", r.returncode == 0)
        if r.returncode:
            print(r.stderr)
            return 1
        exe = str(t / "t80set")
        cases = [("load= with entries", "load=CLOCK.EXE NOTEPAD.EXE\r\n", "load=CLOCK.EXE NOTEPAD.EXE T80HELP.EXE"),
                 ("empty load=", "load=\r\n", "load=T80HELP.EXE"),
                 ("no load= line", "", "load=T80HELP.EXE"),
                 ("helper already listed", "load=t80help.exe\r\n", "load=t80help.exe")]
        for name, load, want in cases:
            w = t / ("w" + str(len(fails)) + name.replace(" ", "_").replace("=", ""))
            w.mkdir()
            (w / "SYSTEM.INI").write_bytes(SYSTEM.encode())
            (w / "WIN.INI").write_bytes(ini(load).encode())
            s0, w0 = (w / "SYSTEM.INI").read_bytes(), (w / "WIN.INI").read_bytes()
            rc = subprocess.run([exe, "ON", str(w), "TEXT80.DRV", "T80HELP.EXE"], capture_output=True).returncode
            sysi = (w / "SYSTEM.INI").read_bytes().decode()
            wini = (w / "WIN.INI").read_bytes().decode()
            expect(f"{name}: ON succeeds", rc == 0)
            expect(f"{name}: [boot] has TEXT80.DRV and the three 8x8 fonts",
                   all(k in sysi for k in ("display.drv=TEXT80.DRV", "fonts.fon=XTTSYS.FON",
                                           "fixedfon.fon=XTCFIX.FON", "oemfonts.fon=XTCOEM.FON")))
            loads = [ln for ln in wini.split("\r\n") if ln.lower().startswith("load=")]
            expect(f"{name}: load= is exactly '{want}'", loads == [want])
            expect(f"{name}: [fonts] kept every line and gained two",
                   all(ln in wini for ln in FONTS.split("\r\n") if ln) and
                   wini.count("(TEXT80)=") == 2)
            rest0 = [ln for ln in w0.decode().split("\r\n") if not ln.lower().startswith("load=")]
            rest1 = [ln for ln in wini.split("\r\n") if not ln.lower().startswith("load=") and "(TEXT80)=" not in ln]
            expect(f"{name}: every other WIN.INI line unchanged", rest0 == rest1)
            rc2 = subprocess.run([exe, "ON", str(w), "TEXT80.DRV"], capture_output=True).returncode
            expect(f"{name}: a second ON is refused", rc2 == 1)
            rc3 = subprocess.run([exe, "OFF", str(w)], capture_output=True).returncode
            expect(f"{name}: OFF restores both files byte for byte",
                   rc3 == 0 and (w / "SYSTEM.INI").read_bytes() == s0 and (w / "WIN.INI").read_bytes() == w0)
            expect(f"{name}: OFF removes the backups", not (w / "SYSTEM.T80").exists() and not (w / "WIN.T80").exists())
        w = t / "nofonts"
        w.mkdir()
        (w / "SYSTEM.INI").write_bytes(SYSTEM.encode())
        (w / "WIN.INI").write_bytes(b"[windows]\r\nload=\r\n")
        rc = subprocess.run([exe, "ON", str(w), "TEXT80.DRV"], capture_output=True).returncode
        expect("no [fonts] section: ON fails and leaves both files unchanged",
               rc == 1 and (w / "SYSTEM.INI").read_bytes() == SYSTEM.encode() and
               (w / "WIN.INI").read_bytes() == b"[windows]\r\nload=\r\n" and not (w / "SYSTEM.T80").exists())
        if a.ini_dir:
            w = t / "real"
            w.mkdir()
            for n in ("SYSTEM.INI", "WIN.INI"):
                shutil.copyfile(a.ini_dir / n, w / n)
            s0, w0 = (w / "SYSTEM.INI").read_bytes(), (w / "WIN.INI").read_bytes()
            rc = subprocess.run([exe, "ON", str(w), "TEXT80.DRV", "T80HELP.EXE"], capture_output=True).returncode
            rc3 = subprocess.run([exe, "OFF", str(w)], capture_output=True).returncode
            expect("real INI files: ON then OFF restores both byte for byte",
                   rc == 0 and rc3 == 0 and (w / "SYSTEM.INI").read_bytes() == s0 and (w / "WIN.INI").read_bytes() == w0)
    print(f"{len(fails)} failed" if fails else "all passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
