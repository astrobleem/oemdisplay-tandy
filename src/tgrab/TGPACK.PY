#!/usr/bin/env python3
"""Make the TANDYGR test packet: an OEM display disk folder for Windows Setup.

  python3 src/tgrab/TGPACK.PY --grabber <TANDYGR.GR2 from BUILDTG.PY>
      --tools <dir with TGPAT.COM, TGEVEN.COM, TGCLIP.EXE> --out <new dir>

One Setup display choice, "Tandy EX/HX 320x200 16 colors, Tandy grabber
(TEST)": the shipped Windows XT TR53216.DRV, fonts and logo files from
distributions/WINXT (hash-checked against its MANIFEST.SHA), with
TANDYGR.GR2 in place of CGA.GR2. Also TGPAT.COM and TGIMG.BMP for the
checks in README.TXT. Nothing in distributions/WINXT is changed; the packet
needs no Microsoft file. CRLF text, 8.3 names. Writes PACKET.JSN (hashes).
"""
import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WINXT = ROOT / "distributions" / "WINXT"
T = importlib.machinery.SourceFileLoader("tgimg", str(HERE / "TGIMG.PY")).load_module()

FROM_WINXT = ["TR53216.DRV", "XTESYS.FON", "XTEFIX.FON", "XTEOEM.FON", "XTSTATIC.LGO", "WXTSPL01.RLE",
              "RESERVE.COM"]

INF = """; TANDYGR test packet: Windows XT 320x200x16 with the Tandy grabber.
; Windows 3.0 real mode, Tandy 1000 EX/HX. Test candidate, not a release.
[data]
Version = "3.0"
[disks]
a = ., "Windows XT Tandy grabber TEST", OEMSETUP.INF
[display]
TR53216G = a:TR53216.DRV, "Tandy EX/HX 320x200 16 colors, Tandy grabber (TEST)", "133,96,72", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE
[sysfonts]
a:XTESYS.FON, "EGA System Font", "133,96,72"
[fixedfonts]
a:XTEFIX.FON, "EGA Fixed System Font", "133,96,72"
[oemfonts]
a:XTEOEM.FON, "EGA Terminal Font (USA/Europe)", "133,96,72", 1
"""

README = """TANDYGR TEST PACKET - Windows XT 320x200x16: Clipboard and DOS programs
================================================================================

Test candidate for Windows 3.0 real mode on a Tandy 1000 EX/HX. Emulator
evidence only (86Box Tandy 1000 HX); not yet run on real hardware. The
display driver (TR53216.DRV), fonts, logo and RESERVE.COM are the shipped
Windows XT files, byte for byte.

New files:
  TANDYGR.GR2  screen grabber for the Tandy modes. Saves and restores DOS
               programs in modes 8, 9 and 0Ah when you switch away; on
               Print Screen in mode 8 or 9 it writes the screen to
               TANDYGR.BMP in your TEMP directory.
  TGCLIP.EXE   puts that picture on the Clipboard as a bitmap (Windows 3.0
               real mode itself only copies DOS text screens).
  TGEVEN.COM   run after RESERVE: keeps the memory Windows takes ending at
               an even segment. Without it, copying a DOS text screen with
               Print Screen hangs Windows (its heap end marker is overwritten).
  TGSTART.BAT  the Windows XT launcher (C:\\WINXT\\TSTART.BAT) with one added
               step: TGEVEN right after RESERVE.

Install (on an existing Windows XT 320x200x16 installation):
  1. Copy TGEVEN.COM, TGCLIP.EXE and TGSTART.BAT to C:\\WINXT.
  2. Start Windows with C:\\WINXT\\TGSTART (instead of TSTART).
  3. Windows Setup > Options > Change System Settings > Display:
     "Other display (Requires disk ...)", give the folder holding this
     packet, choose "Tandy EX/HX 320x200 16 colors, Tandy grabber (TEST)".
  4. File > Run  C:\\WINXT\\TGCLIP.EXE  once. It adds itself to WIN.INI
     load= and starts with Windows from then on.
  5. Restart Windows with C:\\WINXT\\TGSTART.

Print Screen on a Tandy keyboard is SHIFT + PRINT.
  * In Windows: copies the whole screen as a 320x200 16-colour bitmap.
  * In a full-screen DOS text program: copies the text.
  * In a full-screen DOS program in mode 8 or 9 (160x200 or 320x200 in 16
    colours): copies the picture; after you switch back to Windows the
    Clipboard holds a bitmap (TGCLIP). Other graphics modes are not copied.

Checks:
  * TGIMG.BMP (64x40, all 16 colours): open in Paintbrush, Pick tool, Edit >
    Copy, File > New, Edit > Paste, save, reopen: same picture and colours.
  * TGPAT.COM shows the same picture in BIOS mode 9. ALT+TAB away and back:
    unchanged. SHIFT+PRINT, then SPACE: Paintbrush Edit > Paste pastes it.
"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def crlf(s):
    return s.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grabber", type=Path, required=True)
    ap.add_argument("--tools", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists():
        raise SystemExit(f"TGPACK: {a.out} exists")
    manifest = {}
    for line in (WINXT / "MANIFEST.SHA").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            manifest[parts[1].lstrip("*").upper()] = parts[0].lower()
    a.out.mkdir(parents=True)
    rec = {"files": {}, "from_winxt": {}}
    for n in FROM_WINXT:
        data = (WINXT / n).read_bytes()
        if manifest.get(n) != sha(data):
            raise SystemExit(f"TGPACK: {n} does not match distributions/WINXT/MANIFEST.SHA")
        (a.out / n).write_bytes(data)
        rec["from_winxt"][n] = sha(data)
    shutil.copyfile(a.grabber, a.out / "TANDYGR.GR2")
    for n in ("TGPAT.COM", "TGEVEN.COM", "TGCLIP.EXE"):
        shutil.copyfile(a.tools / n, a.out / n)
    start = (WINXT / "TSTART.BAT").read_bytes().decode("ascii")
    anchor = "%TSRSV%\r\nIF ERRORLEVEL 1 GOTO FAILED\r\n"
    if start.count(anchor) != 1:
        raise SystemExit("TGPACK: TSTART.BAT anchor not found exactly once")
    start = start.replace(anchor, anchor + "REM TANDYGR test: even-ended Windows memory (see README.TXT).\r\n"
                          "%TSHOME%\\TGEVEN.COM\r\nIF ERRORLEVEL 1 GOTO FAILED\r\n")
    (a.out / "TGSTART.BAT").write_bytes(start.encode("ascii"))
    # The palette of the driver's colour table, as Windows writes it in a
    # 4-bit BMP (the same as PCP86.PY's BARS16.BMP).
    pal = bytes.fromhex("00000000000080000080000000808000800000008000800080800000808080004040400"
                        "00000ff0000ff000000ffff00ff000000ff00ff00ffff0000ffffff00")
    (a.out / "TGIMG.BMP").write_bytes(T.bmp(pal))
    (a.out / "OEMSETUP.INF").write_bytes(crlf(INF))
    (a.out / "README.TXT").write_bytes(crlf(README))
    for p in sorted(a.out.iterdir()):
        rec["files"][p.name] = {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
    (a.out / "PACKET.JSN").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
