#!/usr/bin/env python3
"""Make the TANDYGR test packet: an OEM display disk folder for Windows Setup.

  python3 src/tgrab/TGPACK.PY --grabber <TANDYGR.GR2 from BUILDTG.PY>
      --tools <dir with TGPAT.COM> --out <new dir>

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

README = """TANDYGR TEST PACKET - Windows XT 320x200x16 with a Tandy grabber
=================================================================

Test candidate for Windows 3.0 real mode on a Tandy 1000 EX/HX. Emulator
evidence only (86Box Tandy 1000 HX); not yet run on real hardware.

What changes: the screen grabber. The display driver (TR53216.DRV), fonts,
logo and RESERVE.COM are the shipped Windows XT files, byte for byte.
TANDYGR.GR2 replaces CGA.GR2 for this one Setup choice. It saves and
restores DOS programs in the Tandy modes 8, 9 and 0Ah when you switch
away from them (CGA.GR2 cannot), and reads the mode from the BIOS.

Install (on an existing Windows XT 320x200x16 installation):
  1. Start Windows XT as usual (C:\\WINXT\\WINXT, which runs RESERVE).
  2. Main group > Windows Setup > Options > Change System Settings.
  3. Display: choose "Other display (Requires disk from OEM)", enter the
     folder or drive holding this packet, choose
     "Tandy EX/HX 320x200 16 colors, Tandy grabber (TEST)", OK.
  4. Restart Windows with C:\\WINXT\\WINXT.
To go back, choose "Tandy EX/HX 320x200 16 colors" from the Windows XT disk
the same way.

Clipboard on a Tandy keyboard: Print Screen is SHIFT + PRINT.
  * In Windows: SHIFT+PRINT copies the whole screen to the Clipboard as a
    320x200 16-colour bitmap; Paintbrush Edit > Paste pastes it.
  * In a full-screen DOS program: Windows 3.0 real mode copies TEXT
    screens only. A graphics screen (for example TGPAT's mode 9) is not
    copied. See the limitations in the pull request / docs/GRABBER.MD.

Checks:
  * TGIMG.BMP: 64x40 picture with all 16 colours. Open it in Paintbrush,
    select it with the Pick tool, Edit > Copy, File > New, Edit > Paste,
    save, reopen: the same 64x40 picture in the same colours.
  * TGPAT.COM: run it from File > Run. It shows the same picture in BIOS
    mode 9. Press ALT+TAB to go to Windows and ALT+TAB again to return:
    the picture must come back unchanged. Press SPACE to end it.
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
    shutil.copyfile(a.tools / "TGPAT.COM", a.out / "TGPAT.COM")
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
