#!/usr/bin/env python3
"""Host test of T80SET.C (the reversible TEXT80 setup) - no DOS, no emulator.

  python3 src/text80/T80SETT.PY [--ini-dir <dir with a real SYSTEM.INI, WIN.INI>]

Compiles T80SET.C with the host C compiler as C89 (a few DOS library names
mapped to POSIX ones, "/" as the path separator, and a fault-injection shim
around rename() and fopen() for writing) and runs it on synthetic Windows
3.0 INI files (and, with --ini-dir, on copies of real ones, which are not
in the repository). Requires:
- ON sets exactly the documented [boot] keys (a key that already has the
  value is left byte for byte), appends the helper to load= keeping every
  existing entry (also when load= is missing or empty, and not twice), only
  adds the two [fonts] lines; a second ON is refused;
- OFF with nothing changed since ON gives both files back byte for byte and
  removes T80SET.STA and the copies;
- OFF keeps every change made since ON (new sections and lines, other
  values changed, a [fonts] line added) and undoes only ON's lines; a line
  ON set and changed since (display.drv) is left as it is;
- ON or OFF whose file replacement fails at any rename, or whose writing
  fails at any file, exits 1 with both live files exactly as before and no
  T8N/T8O, copies or T80SET.STA left (for ON); when putting things back
  fails too, no file is lost: every live file is there or its .T8O is, and
  the copies are kept;
- RESTORE puts the saved copies back whole; OFF with T80SET.STA missing,
  truncated (only its header, no END line, a change line cut short) exits 1
  and changes nothing, keeping the copies; a complete record of no changes
  (END 0) is accepted;
- the helper is a whole load= entry: MYXTPAN.EXE or XTPAN.EXEC are not
  XTPAN.EXE, on ON or on OFF;
- ON with no [fonts] section fails and leaves both files unchanged.
Exit status 1 if any check fails.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIM = r"""#include <strings.h>
#include <unistd.h>
#include <ctype.h>
#include <stdlib.h>
#define strnicmp strncasecmp
#define stricmp strcasecmp
static char *strupr(char *s){char *p=s;for(;*p;p++)*p=toupper((unsigned char)*p);return s;}
/* fault injection: T80FAULT_RENAME=n[,m] fails the n-th (and m-th) rename;
   T80FAULT_WOPEN=n fails the n-th fopen for writing */
static int t80_count(const char *var, int k)
{
    const char *v = getenv(var);
    int n = 0, m = 0;
    if (!v) return 0;
    n = atoi(v);
    if (strchr(v, ',')) m = atoi(strchr(v, ',') + 1);
    return k == n || k == m;
}
static int t80_rename(const char *a, const char *b)
{
    static int k;
    if (t80_count("T80FAULT_RENAME", ++k)) return -1;
    return rename(a, b);
}
static FILE *t80_fopen(const char *p, const char *mode)
{
    static int k;
    if (mode[0] == 'w' && t80_count("T80FAULT_WOPEN", ++k)) return NULL;
    return fopen(p, mode);
}
#define rename t80_rename
#define fopen t80_fopen
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


class Box:
    def __init__(self, root, name, win, system=SYSTEM):
        self.w = root / name
        self.w.mkdir()
        (self.w / "SYSTEM.INI").write_bytes(system.encode())
        (self.w / "WIN.INI").write_bytes(win.encode())

    def files(self):
        return sorted(p.name for p in self.w.iterdir())

    def read(self, n):
        return (self.w / n).read_bytes()

    def snap(self):
        return {n: self.read(n) for n in self.files()}


def run(exe, *args, env=None):
    return subprocess.run([exe, *[str(a) for a in args]], capture_output=True, text=True,
                          env=dict(os.environ, **(env or {})))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ini-dir", type=Path)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "shim.h").write_text(SHIM)
        src = (HERE / "T80SET.C").read_text(errors="replace").replace("#include <io.h>", '#include "shim.h"')
        (t / "t80set.c").write_text(src)
        r = subprocess.run(["cc", "-std=c89", "-pedantic", '-DSEP="/"', "-Wall", "-Wno-long-long",
                            "-Wframe-larger-than=400", "-o", str(t / "t80set"), str(t / "t80set.c")],
                           capture_output=True, text=True)
        expect("T80SET.C compiles on the host as C89", r.returncode == 0)
        # the DOS build has a 2 KB stack (a 300-byte local in a nested call
        # overflowed it in 86Box: run-time error R6000): no function may keep
        # more than 400 bytes on the stack
        expect("no function's stack frame is over 400 bytes", "frame size" not in r.stderr)
        if r.returncode:
            print(r.stderr)
            return 1
        exe = str(t / "t80set")
        cases = [("load= with entries", "load=CLOCK.EXE NOTEPAD.EXE\r\n", "load=CLOCK.EXE NOTEPAD.EXE T80HELP.EXE"),
                 ("empty load=", "load=\r\n", "load=T80HELP.EXE"),
                 ("no load= line", "", "load=T80HELP.EXE"),
                 ("helper already listed", "load=t80help.exe\r\n", "load=t80help.exe")]
        for i, (name, load, want) in enumerate(cases):
            b = Box(t, f"c{i}", ini(load))
            s0, w0 = b.read("SYSTEM.INI"), b.read("WIN.INI")
            rc = run(exe, "ON", b.w, "TEXT80.DRV", "T80HELP.EXE").returncode
            sysi, wini = b.read("SYSTEM.INI").decode(), b.read("WIN.INI").decode()
            expect(f"{name}: ON succeeds", rc == 0)
            expect(f"{name}: [boot] has TEXT80.DRV and the three 8x8 fonts",
                   all(k in sysi for k in ("display.drv=TEXT80.DRV", "fonts.fon=XTTSYS.FON",
                                           "fixedfon.fon=XTCFIX.FON", "oemfonts.fon=XTCOEM.FON")))
            loads = [ln for ln in wini.split("\r\n") if ln.lower().startswith("load=")]
            expect(f"{name}: load= is exactly '{want}'", loads == [want])
            expect(f"{name}: [fonts] kept every line and gained two",
                   all(ln in wini for ln in FONTS.split("\r\n") if ln) and wini.count("(TEXT80)=") == 2)
            rest0 = [ln for ln in w0.decode().split("\r\n") if not ln.lower().startswith("load=")]
            rest1 = [ln for ln in wini.split("\r\n") if not ln.lower().startswith("load=") and "(TEXT80)=" not in ln]
            expect(f"{name}: every other WIN.INI line unchanged", rest0 == rest1)
            expect(f"{name}: ON leaves exactly SYSTEM.T80, WIN.T80 and T80SET.STA beside the INI files",
                   b.files() == ["SYSTEM.INI", "SYSTEM.T80", "T80SET.STA", "WIN.INI", "WIN.T80"])
            expect(f"{name}: a second ON is refused", run(exe, "ON", b.w, "TEXT80.DRV").returncode == 1)
            rc3 = run(exe, "OFF", b.w).returncode
            expect(f"{name}: OFF with nothing changed gives both files back byte for byte",
                   rc3 == 0 and b.read("SYSTEM.INI") == s0 and b.read("WIN.INI") == w0)
            expect(f"{name}: OFF removes the copies and T80SET.STA", b.files() == ["SYSTEM.INI", "WIN.INI"])

        # a key that already has ON's value is left byte for byte
        sysv = SYSTEM.replace("fonts.fon=egasys.fon", "fonts.fon = xttsys.fon")
        b = Box(t, "samevalue", ini("load=\r\n"), sysv)
        run(exe, "ON", b.w, "TEXT80.DRV")
        expect("a key already at ON's value is left as it was (spacing, case)",
               "fonts.fon = xttsys.fon\r\n" in b.read("SYSTEM.INI").decode())
        expect("... and OFF still gives SYSTEM.INI back byte for byte",
               run(exe, "OFF", b.w).returncode == 0 and b.read("SYSTEM.INI") == sysv.encode())

        # OFF keeps what changed since ON
        b = Box(t, "since", ini("load=CLOCK.EXE\r\n"))
        s0, w0 = b.read("SYSTEM.INI").decode(), b.read("WIN.INI").decode()
        run(exe, "ON", b.w, "T80PAN.DRV", "XTPAN.EXE")
        sysi, wini = b.read("SYSTEM.INI").decode(), b.read("WIN.INI").decode()
        sysi = sysi.replace("shell=progman.exe", "shell=progman.exe\r\nmouse.drv=mouse.drv")
        wini = wini.replace("Beep=yes", "Beep=no").replace("Modern=MODERN.FON", "Modern=MODERN.FON\r\nRoman=ROMAN.FON")
        wini = wini.replace("load=CLOCK.EXE XTPAN.EXE", "load=CLOCK.EXE XTPAN.EXE NOTEPAD.EXE")
        wini += "[Notepad]\r\nszTrailer=Page &p\r\n"
        (b.w / "SYSTEM.INI").write_bytes(sysi.encode())
        (b.w / "WIN.INI").write_bytes(wini.encode())
        rc = run(exe, "OFF", b.w).returncode
        want_s = s0.replace("shell=progman.exe", "shell=progman.exe\r\nmouse.drv=mouse.drv")
        want_w = (w0.replace("Beep=yes", "Beep=no").replace("Modern=MODERN.FON", "Modern=MODERN.FON\r\nRoman=ROMAN.FON")
                  .replace("load=CLOCK.EXE", "load=CLOCK.EXE NOTEPAD.EXE") + "[Notepad]\r\nszTrailer=Page &p\r\n")
        expect("OFF after other changes: succeeds", rc == 0)
        expect("OFF after other changes: SYSTEM.INI is the original plus the line added since",
               b.read("SYSTEM.INI").decode() == want_s)
        expect("OFF after other changes: WIN.INI keeps Beep=no, Roman, NOTEPAD.EXE on load= and [Notepad]; "
               "XTPAN.EXE and the two faces are gone", b.read("WIN.INI").decode() == want_w)

        # a line ON set and changed since stays as the user left it
        b = Box(t, "changed", ini("load=\r\n"))
        run(exe, "ON", b.w, "TEXT80.DRV")
        (b.w / "SYSTEM.INI").write_bytes(b.read("SYSTEM.INI").replace(b"display.drv=TEXT80.DRV", b"display.drv=vga.drv"))
        r = run(exe, "OFF", b.w)
        s = b.read("SYSTEM.INI").decode()
        expect("display.drv changed since ON: OFF leaves it, says so, and undoes the fonts",
               r.returncode == 0 and "display.drv=vga.drv" in s and "fonts.fon=egasys.fon" in s and
               "XTTSYS" not in s and "changed since ON" in r.stdout)

        # failures while replacing the files: ON
        for k in range(1, 5):
            b = Box(t, f"onfail{k}", ini("load=CLOCK.EXE\r\n"))
            before = b.snap()
            r = run(exe, "ON", b.w, "TEXT80.DRV", "T80HELP.EXE", env={"T80FAULT_RENAME": str(k)})
            expect(f"ON, rename {k} fails: exit 1, both files and the folder exactly as before",
                   r.returncode == 1 and b.snap() == before)
        for k in range(1, 6):                     # ON writes 5 files: T8N x2, T80 x2, STA
            b = Box(t, f"onwfail{k}", ini("load=CLOCK.EXE\r\n"))
            before = b.snap()
            r = run(exe, "ON", b.w, "TEXT80.DRV", "T80HELP.EXE", env={"T80FAULT_WOPEN": str(k)})
            expect(f"ON, writing file {k} fails: exit 1, the folder exactly as before",
                   r.returncode == 1 and b.snap() == before)
        # ... and putting back fails too: nothing lost, copies kept
        for k in range(2, 5):
            b = Box(t, f"onfail2_{k}", ini("load=CLOCK.EXE\r\n"))
            s0, w0 = b.read("SYSTEM.INI"), b.read("WIN.INI")
            r = run(exe, "ON", b.w, "TEXT80.DRV", env={"T80FAULT_RENAME": f"{k},{k + 1}"})
            names = b.files()
            have = lambda n, o: (n in names) or (o in names)
            expect(f"ON, rename {k} and the first undo fail: exit 1, no file lost, the copies kept and named",
                   r.returncode == 1 and have("SYSTEM.INI", "SYSTEM.T8O") and have("WIN.INI", "WIN.T8O") and
                   b.read("SYSTEM.T80") == s0 and b.read("WIN.T80") == w0 and "SYSTEM.T80" in r.stdout)

        # failures: OFF
        for k in range(1, 5):
            b = Box(t, f"offfail{k}", ini("load=CLOCK.EXE\r\n"))
            run(exe, "ON", b.w, "TEXT80.DRV", "T80HELP.EXE")
            before = b.snap()
            r = run(exe, "OFF", b.w, env={"T80FAULT_RENAME": str(k)})
            expect(f"OFF, rename {k} fails: exit 1, everything as before OFF (still set up)",
                   r.returncode == 1 and b.snap() == before)
            expect(f"OFF, rename {k} failed: a second OFF then works",
                   run(exe, "OFF", b.w).returncode == 0 and b.files() == ["SYSTEM.INI", "WIN.INI"])
        for k in range(1, 3):
            b = Box(t, f"offwfail{k}", ini("load=CLOCK.EXE\r\n"))
            run(exe, "ON", b.w, "TEXT80.DRV", "T80HELP.EXE")
            before = b.snap()
            r = run(exe, "OFF", b.w, env={"T80FAULT_WOPEN": str(k)})
            expect(f"OFF, writing file {k} fails: exit 1, everything as before OFF",
                   r.returncode == 1 and b.snap() == before)

        # RESTORE, and OFF for a set-up without T80SET.STA (an earlier T80SET)
        b = Box(t, "restore", ini("load=CLOCK.EXE\r\n"))
        s0, w0 = b.read("SYSTEM.INI"), b.read("WIN.INI")
        run(exe, "ON", b.w, "TEXT80.DRV")
        (b.w / "WIN.INI").write_bytes(b.read("WIN.INI") + b"[x]\r\ny=1\r\n")
        expect("RESTORE: both files back whole, copies and T80SET.STA removed",
               run(exe, "RESTORE", b.w).returncode == 0 and b.read("SYSTEM.INI") == s0 and
               b.read("WIN.INI") == w0 and b.files() == ["SYSTEM.INI", "WIN.INI"])
        b = Box(t, "nosta", ini("load=CLOCK.EXE\r\n"))
        run(exe, "ON", b.w, "TEXT80.DRV")
        (b.w / "T80SET.STA").unlink()
        before = b.snap()
        r = run(exe, "OFF", b.w)
        expect("OFF without T80SET.STA: exit 1, nothing changed, the copies kept, points to RESTORE",
               r.returncode == 1 and b.snap() == before and "RESTORE" in r.stdout)
        for name, cut in (("only its header", lambda s: s.split(b"\r\n")[0] + b"\r\n"),
                          ("without its END line", lambda s: s[:s.rindex(b"END ")] if b"END " in s else s),
                          ("a change line cut short", lambda s: s[:s.index(b"\t", s.index(b"\r\n") + 2) + 1])):
            b = Box(t, "sta_" + name.replace(" ", "_"), ini("load=CLOCK.EXE\r\n"))
            run(exe, "ON", b.w, "TEXT80.DRV", "T80HELP.EXE")
            (b.w / "T80SET.STA").write_bytes(cut(b.read("T80SET.STA")))
            before = b.snap()
            r = run(exe, "OFF", b.w)
            expect(f"T80SET.STA truncated to {name}: OFF exits 1, nothing changed, the copies and the record kept",
                   r.returncode == 1 and b.snap() == before)
        b = Box(t, "nochange", ini("load=CLOCK.EXE\r\n"), SYSTEM.replace("display.drv=ega.drv", "display.drv=TEXT80.DRV")
                .replace("egasys", "XTTSYS").replace("egafix", "XTCFIX").replace("egaoem", "XTCOEM"))
        (b.w / "WIN.INI").write_bytes(b.read("WIN.INI").replace(b"Modern=MODERN.FON", b"Modern=MODERN.FON\r\n"
                                      b"Helv 8x8 (TEXT80)=T80HELV.FON\r\nCourier 8x8 (TEXT80)=T80COUR.FON"))
        s0, w0 = b.read("SYSTEM.INI"), b.read("WIN.INI")
        rc = run(exe, "ON", b.w, "TEXT80.DRV").returncode
        expect("ON with everything already set: a complete record of no changes (END 0)",
               rc == 0 and b.read("T80SET.STA").endswith(b"END 0\r\n"))
        expect("... and OFF accepts it and leaves both files as they were",
               run(exe, "OFF", b.w).returncode == 0 and b.read("SYSTEM.INI") == s0 and b.read("WIN.INI") == w0)

        # the helper is a whole load= entry, not a substring
        for name, load, want in (("MYXTPAN.EXE listed", "load=MYXTPAN.EXE\r\n", "load=MYXTPAN.EXE XTPAN.EXE"),
                                 ("XTPAN.EXEC listed", "load=XTPAN.EXEC CLOCK.EXE\r\n",
                                  "load=XTPAN.EXEC CLOCK.EXE XTPAN.EXE"),
                                 ("XTPAN.EXE listed, other case", "load=CLOCK.EXE xtpan.exe\r\n",
                                  "load=CLOCK.EXE xtpan.exe")):
            b = Box(t, "helper_" + name.replace(" ", "_").replace(",", ""), ini(load))
            w0 = b.read("WIN.INI")
            run(exe, "ON", b.w, "T80PAN.DRV", "XTPAN.EXE")
            loads = [ln for ln in b.read("WIN.INI").decode().split("\r\n") if ln.lower().startswith("load=")]
            expect(f"{name}: ON gives '{want}'", loads == [want])
            rc = run(exe, "OFF", b.w).returncode
            expect(f"{name}: OFF gives WIN.INI back byte for byte", rc == 0 and b.read("WIN.INI") == w0)
        b = Box(t, "helper_since", ini("load=CLOCK.EXE\r\n"))
        run(exe, "ON", b.w, "T80PAN.DRV", "XTPAN.EXE")
        (b.w / "WIN.INI").write_bytes(b.read("WIN.INI").replace(b"load=CLOCK.EXE XTPAN.EXE",
                                                                b"load=MYXTPAN.EXE CLOCK.EXE XTPAN.EXE"))
        run(exe, "OFF", b.w)
        expect("MYXTPAN.EXE added before XTPAN.EXE since ON: OFF removes only XTPAN.EXE",
               b"load=MYXTPAN.EXE CLOCK.EXE\r\n" in b.read("WIN.INI"))

        b = Box(t, "nofonts", "[windows]\r\nload=\r\n")
        rc = run(exe, "ON", b.w, "TEXT80.DRV").returncode
        expect("no [fonts] section: ON fails and leaves the folder unchanged",
               rc == 1 and b.read("SYSTEM.INI") == SYSTEM.encode() and
               b.read("WIN.INI") == b"[windows]\r\nload=\r\n" and b.files() == ["SYSTEM.INI", "WIN.INI"])
        if a.ini_dir:
            w = t / "real"
            w.mkdir()
            for n in ("SYSTEM.INI", "WIN.INI"):
                shutil.copyfile(a.ini_dir / n, w / n)
            s0, w0 = (w / "SYSTEM.INI").read_bytes(), (w / "WIN.INI").read_bytes()
            rc = run(exe, "ON", w, "TEXT80.DRV", "T80HELP.EXE").returncode
            rc3 = run(exe, "OFF", w).returncode
            expect("real INI files: ON then OFF gives both back byte for byte",
                   rc == 0 and rc3 == 0 and (w / "SYSTEM.INI").read_bytes() == s0 and (w / "WIN.INI").read_bytes() == w0)
    print(f"{len(fails)} failed" if fails else "all passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
