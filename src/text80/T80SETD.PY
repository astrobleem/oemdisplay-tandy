#!/usr/bin/env python3
"""The DOS build of T80SET.EXE, run in DOSBox-X on synthetic INI files.

  python3 src/text80/T80SETD.PY --exe <T80SET.EXE> --dosbox <dosbox-x> --out <fresh dir> [--compact]

T80SETT.PY tests the C source compiled on the host; this runs the real
16-bit program (Microsoft C small model, 2 KB stack) under DOS, through
EMULOCK like every emulator run, and checks the files it leaves:
  W1  ON with a helper, then OFF: both files back byte for byte, the
      copies and T80SET.STA gone, exit codes 0;
  W2  load=MYXTPAN.EXE: ON appends XTPAN.EXE, OFF leaves MYXTPAN.EXE;
  W3  T80SET.STA cut to its header: OFF exits 1 and changes nothing;
  W4  T80SET.STA deleted: OFF exits 1 and changes nothing; then RESTORE
      puts the saved files back whole and exits 0;
  W5  (--compact) ON ... /C then OFF: BorderWidth/GridGranularity set,
      then both files back byte for byte.
Exit status 0 only if every check passes.
"""
import argparse
import subprocess
import sys
from pathlib import Path

SYSTEM = (b"[boot]\r\nshell=progman.exe\r\nfixedfon.fon=egafix.fon\r\noemfonts.fon=egaoem.fon\r\n"
          b"fonts.fon=egasys.fon\r\ndisplay.drv=ega.drv\r\n\r\n[keyboard]\r\ntype=1\r\n")


def win(load):
    return (b"[windows]\r\n" + load + b"run=\r\nBeep=yes\r\n\r\n[fonts]\r\nModern=MODERN.FON\r\n"
            b"\r\n[ports]\r\nCOM1:=9600\r\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--dosbox", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--compact", action="store_true")
    a = ap.parse_args()
    out = a.out
    out.mkdir(parents=True)
    (out / "T80SET.EXE").write_bytes(a.exe.read_bytes())
    dirs = {"W1": b"load=CLOCK.EXE\r\n", "W2": b"load=MYXTPAN.EXE\r\n", "W3": b"load=\r\n", "W4": b"load=\r\n"}
    if a.compact:
        dirs["W5"] = b"BorderWidth=3\r\nload=\r\n"
    for d, load in dirs.items():
        (out / d).mkdir()
        (out / d / "SYSTEM.INI").write_bytes(SYSTEM)
        (out / d / "WIN.INI").write_bytes(win(load))
    bat = ["@ECHO OFF", "C:", "CD \\",
           "T80SET ON W1 TEXT80.DRV XTPAN.EXE > R1ON.TXT", "IF ERRORLEVEL 1 COPY T80SET.EXE E1ON.TXT",
           "T80SET OFF W1 > R1OFF.TXT", "IF ERRORLEVEL 1 COPY T80SET.EXE E1OFF.TXT",
           "T80SET ON W2 T80PAN.DRV XTPAN.EXE > R2ON.TXT",
           "COPY W2\\WIN.INI W2ON.INI > NUL",
           "T80SET OFF W2 > R2OFF.TXT", "IF ERRORLEVEL 1 COPY T80SET.EXE E2OFF.TXT",
           "T80SET ON W3 TEXT80.DRV > R3ON.TXT",
           "ECHO T80SET 2 > W3\\T80SET.STA",
           "T80SET OFF W3 > R3OFF.TXT", "IF ERRORLEVEL 1 COPY T80SET.EXE E3OFF.TXT",
           "T80SET ON W4 TEXT80.DRV > R4ON.TXT",
           "DEL W4\\T80SET.STA",
           "T80SET OFF W4 > R4OFF.TXT", "IF ERRORLEVEL 1 COPY T80SET.EXE E4OFF.TXT",
           "COPY W4\\SYSTEM.INI W4SYS.INI > NUL",
           "T80SET RESTORE W4 > R4RES.TXT", "IF ERRORLEVEL 1 COPY T80SET.EXE E4RES.TXT"]
    if a.compact:
        bat += ["T80SET ON W5 T80CMP.DRV /C > R5ON.TXT", "COPY W5\\WIN.INI W5ON.INI > NUL",
                "T80SET OFF W5 > R5OFF.TXT", "IF ERRORLEVEL 1 COPY T80SET.EXE E5OFF.TXT"]
    # (no redirection on an IF line: the shell creates the file whether or
    # not the condition holds; the batch ends DOSBox-X itself)
    bat += ["ECHO DONE > DONE.TXT", "EXIT"]
    (out / "RUN.BAT").write_bytes(("\r\n".join(bat) + "\r\n").encode())
    conf = ("[sdl]\noutput=surface\n[dosbox]\nmachine=cga\nmemsize=1\n[cpu]\ncore=normal\ncputype=8086\n"
            "cycles=max\n[mixer]\nnosound=true\n[speaker]\npcspeaker=false\n[autoexec]\n"
            f"mount c \"{out}\"\nc:\nRUN.BAT\n")
    (out / "RUN.CONF").write_text(conf)
    subprocess.run([a.dosbox, "-nopromptfolder", "-nogui", "-nomenu", "-conf", str(out / "RUN.CONF")],
                   env={"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy", "PATH": "/usr/bin:/bin"},
                   capture_output=True, timeout=600)
    fails = []

    def expect(label, ok):
        print(("ok   " if ok else "FAIL ") + label)
        if not ok:
            fails.append(label)
    f = lambda n: out / n
    names = lambda d: sorted(p.name.upper() for p in (out / d).iterdir())
    expect("the batch ran to the end", f("DONE.TXT").exists())
    expect("W1: ON then OFF exit 0; both files back byte for byte; nothing else left",
           not f("E1ON.TXT").exists() and not f("E1OFF.TXT").exists() and
           f("W1/SYSTEM.INI").read_bytes() == SYSTEM and f("W1/WIN.INI").read_bytes() == win(dirs["W1"]) and
           names("W1") == ["SYSTEM.INI", "WIN.INI"])
    expect("W2: MYXTPAN.EXE is not XTPAN.EXE: ON appends it, OFF removes only it",
           b"load=MYXTPAN.EXE XTPAN.EXE\r\n" in f("W2ON.INI").read_bytes() and not f("E2OFF.TXT").exists() and
           f("W2/WIN.INI").read_bytes() == win(dirs["W2"]))
    expect("W3: T80SET.STA cut to its header: OFF exits 1, changes nothing, keeps the copies",
           f("E3OFF.TXT").exists() and b"TEXT80.DRV" in f("W3/SYSTEM.INI").read_bytes() and
           names("W3") == ["SYSTEM.INI", "SYSTEM.T80", "T80SET.STA", "WIN.INI", "WIN.T80"])
    expect("W4: no T80SET.STA: OFF exits 1 and changes nothing; RESTORE then puts the saved files back whole",
           f("E4OFF.TXT").exists() and b"TEXT80.DRV" in f("W4SYS.INI").read_bytes() and
           b"RESTORE" in f("R4OFF.TXT").read_bytes() and not f("E4RES.TXT").exists() and
           f("W4/SYSTEM.INI").read_bytes() == SYSTEM and names("W4") == ["SYSTEM.INI", "WIN.INI"])
    if a.compact:
        expect("W5: ON /C sets BorderWidth=7 and GridGranularity=1; OFF gives WIN.INI back byte for byte",
               b"BorderWidth=7\r\n" in f("W5ON.INI").read_bytes() and b"GridGranularity=1\r\n" in
               f("W5ON.INI").read_bytes() and not f("E5OFF.TXT").exists() and
               f("W5/WIN.INI").read_bytes() == win(dirs["W5"]))
    for n in sorted(out.glob("R*.TXT")):
        print(f"--- {n.name}: " + n.read_bytes().decode("latin1").strip().replace("\r\n", " | "))
    print(f"{len(fails)} failed" if fails else "all passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
