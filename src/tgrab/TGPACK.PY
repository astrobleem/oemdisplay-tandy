#!/usr/bin/env python3
"""Make the TANDYGR test packet: a folder (or 720 KB floppy) for plain DOS.

  python3 src/tgrab/TGPACK.PY --grabber <TANDYGR.GR2 from BUILDTG.PY>
      --apps <BUILDAPP.PY output: TGSETUP.EXE, TGCLIP.EXE>
      --tools <BUILDCOM.PY output with TGMODES.COM> --out <new dir>

Packet files (CRLF text, DOS 8.3 names, no Microsoft file):
  TGSETUP.EXE  the installer, run at a DOS prompt: A:\\TGSETUP
  TGSETUP.LST  size and CRC-32 of every file, checked by TGSETUP
  TANDYGR.GR2  the grabber             TGCLIP.EXE  the Clipboard helper
  TGMODES.COM  test pictures in every graphics mode
  README.TXT
Writes PACKET.JSN (sizes, SHA-256) next to the files.
"""
import argparse
import binascii
import hashlib
import json
import shutil
import sys
from pathlib import Path

README = """TANDY GRABBER TEST PACKET - Clipboard and DOS programs for Windows XT
=====================================================================

Windows 3.0 real mode on a Tandy 1000 EX/HX with Windows XT (any of its
graphics display choices). Test candidate: emulator evidence only (86Box
Tandy 1000 HX), not yet run on real hardware.

INSTALL - at a plain DOS prompt, Windows not running:

  A:
  TGSETUP

(or TGSETUP D:\\WIN30 for Windows in another folder). TGSETUP checks this
packet's files, keeps your SYSTEM.INI and WIN.INI in C:\\WINDOWS\\TGBAK,
copies TANDYGR.GR2 and TGCLIP.EXE, selects the grabber in SYSTEM.INI and
starts TGCLIP from WIN.INI load=. Then start Windows as usual:

  C:\\WINXT\\WINXT

Nothing else changes: not the launcher, CONFIG.SYS or AUTOEXEC.BAT. Running
TGSETUP again updates the files. To undo it:

  C:\\WINDOWS\\TGBAK\\TGSETUP /REMOVE

If TGSETUP says a display mode change can still be undone, run
C:\\WINXT\\MODES first. MODES and Windows Setup select CGA.GR2 again when
they change the display: run TGSETUP again afterwards.

USE - Print Screen on a Tandy keyboard is SHIFT + PRINT.
  In Windows                copies the whole screen as a bitmap.
  In a DOS text program     copies the text.
  In a DOS graphics program copies the picture (CGA 320x200 4 colours and
  (full screen)             640x200 2 colours, Tandy 160x200 and 320x200 16
                            colours, 640x200 4 colours) in the colours shown.
Back in Windows, Paintbrush Edit > Paste pastes it. Paintbrush pastes only
what fits in its window: choose View > Zoom Out first to paste the whole
picture; for a 640-pixel picture set Options > Image Attributes to 640 x 200
pels and choose File > New first.

Switching away from a DOS graphics program (ALT+TAB) keeps its screen in a
temporary file in your TEMP folder while you are in Windows, so each DOS
program needs about 12 KB less memory than with CGA.GR2.

COLOURS - the Tandy palette registers cannot be read back. The grabber
follows what a program sets through the BIOS (INT 10h). A program that
programs the palette registers directly is copied, and restored after
ALT+TAB, in the colours of the last BIOS setting.

TEST PICTURES - TGMODES m p, m = 4 5 6 8 9 A (the BIOS mode), p = 0 (default
colours), 1 (other colours set through the BIOS), 2 (the same colours
written directly to the hardware). Any key ends it.
"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def crlf(s):
    return s.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grabber", type=Path, required=True)
    ap.add_argument("--apps", type=Path, required=True)
    ap.add_argument("--tools", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists():
        raise SystemExit(f"TGPACK: {a.out} exists")
    a.out.mkdir(parents=True)
    shutil.copyfile(a.grabber, a.out / "TANDYGR.GR2")
    for n in ("TGSETUP.EXE", "TGCLIP.EXE"):
        shutil.copyfile(a.apps / n, a.out / n)
    shutil.copyfile(a.tools / "TGMODES.COM", a.out / "TGMODES.COM")
    (a.out / "README.TXT").write_bytes(crlf(README))
    lst = "; TGSETUP.LST - name, size, CRC-32 (checked by TGSETUP.EXE)\n"
    for n in ("TANDYGR.GR2", "TGCLIP.EXE", "TGSETUP.EXE", "TGMODES.COM", "README.TXT"):
        b = (a.out / n).read_bytes()
        lst += f"{n} {len(b)} {binascii.crc32(b) & 0xFFFFFFFF:08X}\n"
    (a.out / "TGSETUP.LST").write_bytes(crlf(lst))
    total = sum(p.stat().st_size for p in a.out.iterdir())
    if total > 700 * 1024:
        raise SystemExit("TGPACK: packet does not fit a 720 KB floppy")
    rec = {"files": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
                     for p in sorted(a.out.iterdir())}, "bytes": total}
    (a.out / "PACKET.JSN").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
