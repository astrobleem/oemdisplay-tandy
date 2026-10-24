#!/usr/bin/env python3
"""Build TANDYGR.GR2, a Windows 3.0 real-mode grabber for the Tandy 1000.

  python3 src/tgrab/BUILDTG.PY --repo <display view> --dosbox <dosbox-x> --out <new dir>

Source: the Windows 3.0 DDK 286 CGA grabber (DDK\\286\\DISPLAY\\GRABBERS,
CGAHERC branch, -dCGA as its makefiles), from the pinned DDK view
(tools/BUILDDEPS). Nothing of the DDK is committed. Two builds are made in
DOSBox-X with the view's MASM 5.10, LINK and EXE2BIN:

  CONTROL.GR2   the unmodified DDK sources (control)
  TANDYGR.GR2   the same sources with the anchored edits in PATCHES and
                our own modules in OWN

What the edits and our modules (TGTANDY, TGSRSCR, TGBMP) add for the
Tandy 1000 (the retail CGA.GR2 knows only the CGA modes 0-6, and indexes
its mode table past its end for modes 8-0Ah):

  * The video mode, start address, cursor and mode-control bytes come from
    the BIOS data area (the DDK's own PGA path), not from the CGA light-pen
    regen measurement.
  * Modes 8 (160x200x16), 9 (320x200x16) and 0Ah (640x200x4) have their own
    InfoContext entries (Tandy layouts: 16 KB in two banks, 32 KB in four).
    Mode 7 and modes above 0Ah set fBadMode: SaveScreen refuses (Windows
    then does not switch away) and GetBlock grabs nothing.
  * Switching away: text screens stay in the save area; graphics screens
    (16 or 32 KB) go to a temporary file, so every session's save area is
    the text size (MAX_CDSIZE + 4 KB) instead of 16 KB (CGA.GR2) or 32 KB.
  * Palette: an INT 10h hook inside the DOS session keeps a copy of the
    palette registers the BIOS loads (the registers are write-only); it is
    restored after switching back and used for grabs.
  * Print Screen in any graphics mode (4, 5, 6, 8, 9, 0Ah): GetInfo reports
    the screen grabbable and GetBlock writes it as a 4-bit BMP in the
    colours shown, plus a one-line text record for WINOLDAP that
    TGCLIP.EXE turns into a Clipboard bitmap.
  * GetBlock re-reads the mode first, so a grab describes the current screen.

Exit 0 on success. RESULT.JSON records both hashes and the patched sources.
"""
import argparse
import hashlib
import importlib.machinery
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
R = importlib.machinery.SourceFileLoader("reserve_harness", str(ROOT / "src" / "tandysw" / "RESERVE.PY")).load_module()

COMMON = ["BLOCK", "EDGRAB", "ENTRY", "GETINFO", "GRABBITS", "GRABSCR", "INOUT", "INQUIRE", "OEM", "PROMPT", "RCOLOR"]
BRANCH = ["BEPAINT", "BLOCKDEV", "EDSAVE", "GSMODE", "SETSWAP", "SRSCR"]
REPLACED = ["SETSWAP", "SRSCR", "EDSAVE"]  # by TGSRSCR in the patched build


def L(*lines):
    return "".join(x + "\r\n" for x in lines)


# Our own modules (MIT, in this directory), assembled in the CGAHERC branch
# directory with the DDK's includes:
#   TGTANDY  InitScreen, INT 10h palette shadow, pixel -> colour map
#   TGSRSCR  SaveScreen/RestoreScreen (graphics screens in a temporary file),
#            SetSwapDrive
#   TGBMP    GrabBmp: Print Screen of a graphics mode to a 4-bit BMP
OWN = ["TGTANDY", "TGSRSCR", "TGBMP"]


# (file, old, new, count): CRLF text, matched exactly.
PATCHES = [
    # The save area: contexts, palette shadow and file name, plus 4 KB for a
    # text screen or the graphics file buffer (TGSRSCR.ASM); graphics
    # screens go to a file, so text and graphics need the same size.
    ("CGAHERC/CGA/CGA.ASM", L("MAX_CDSIZE2\t=\t(SIZE HpBiosData)"),
     L("MAX_CDSIZE2\t=\t(SIZE HpBiosData) + 98\t;TANDYGR: palette shadow, file name"), 1),
    ("CGAHERC/CGA/CGA.ASM", L("SaveGrphSize\tdw\tMAX_CDSIZE + MAX_TOTGRPH"),
     L("SaveGrphSize\tdw\tMAX_CDSIZE + MAX_TOTTEXT\t;TANDYGR: graphics in a file"), 1),
    # InitScreen is TGTANDY's (it hooks INT 10h in the DOS session).
    ("CGAHERC/CGA/CGA.ASM", L("\t\tpublic\tInitScreen"), L(";TANDYGR: InitScreen is in TGTANDY.ASM"), 1),
    ("CGAHERC/CGA/CGA.ASM", L("InitScreen\tproc\tfar"), L("DdkInitScr\tproc\tfar\t\t;TANDYGR: unused"), 1),
    ("CGAHERC/CGA/CGA.ASM", L("InitScreen\tendp"), L("DdkInitScr\tendp"), 1),
    # Trust the BIOS data area for the mode (no light-pen measurement).
    ("CGAHERC/CGA/CGA.ASM", L("\t\tcmp\t[fPGA],TRUE", "\t\tje\tgmdNotRogue"),
     L("\t\tjmp\tgmdNotRogue\t\t;TANDYGR: the Tandy BIOS mode is reliable",
       "\t\tcmp\t[fPGA],TRUE", "\t\tje\tgmdNotRogue"), 1),
    # Mode table entries for the Tandy modes.
    ("CGAHERC/GSMODE.ASM",
     L("IT6\t\tInfoContext\t<DI_CGA,ST_GRPH,2400,1800,80,25,32,32,640,200,080,1,1,1,1,0B8000000h,04000h>"),
     L("IT6\t\tInfoContext\t<DI_CGA,ST_GRPH,2400,1800,80,25,32,32,640,200,080,1,1,1,1,0B8000000h,04000h>",
       ";TANDYGR: 7 is never used (fBadMode); 8 = 160x200x16, 9 = 320x200x16,",
       ";  0Ah = 640x200x4 (Tandy 1000 layouts)",
       "IT7\t\tInfoContext\t<DI_CGA,ST_GRPH,2400,1800,80,25,32,32,640,200,080,1,1,1,1,0B8000000h,04000h>",
       "IT8\t\tInfoContext\t<DI_CGA,ST_GRPH,2400,1800,20,25,08,32,160,200,080,4,1,1,1,0B8000000h,04000h>",
       "IT9\t\tInfoContext\t<DI_CGA,ST_GRPH,2400,1800,40,25,16,32,320,200,160,4,1,2,3,0B8000000h,08000h>",
       "ITA\t\tInfoContext\t<DI_CGA,ST_GRPH,2400,1800,80,25,32,32,640,200,160,2,1,2,3,0B8000000h,08000h>"), 1),
    ("CGAHERC/GSMODE.ASM", L("\t\tpublic\tGetMode"), L("\t\tpublic\tGetMode", "\t\tpublic\tfBadMode"), 1),
    ("CGAHERC/GSMODE.ASM",
     L("\t\tmov\tsi,offset IT", "\t\tmov\tdi,offset IC", "\t\tmov\tal,[DC.dcScrMode]"),
     L("\t\tmov\tsi,offset IT", "\t\tmov\tdi,offset IC", "\t\tmov\tal,[DC.dcScrMode]",
       "\t\tmov\t[fBadMode],FALSE\t;TANDYGR: 7 and above 0Ah unsupported",
       "\t\tcmp\tal,7",
       "\t\tje\tgmBadMode",
       "\t\tcmp\tal,0Ah",
       "\t\tjbe\tgmModeOk",
       "gmBadMode:",
       "\t\tmov\t[fBadMode],TRUE",
       "\t\tmov\tal,6",
       "gmModeOk:"), 1),
    ("CGAHERC/GSMODE.ASM", L("\t\tsubttl\tGetmode"),
     L("fBadMode\tdb\t0\t\t\t;TANDYGR: set by GetMode", "", "\t\tsubttl\tGetmode"), 1),
    # GetBlock: current mode first; no grab of an unsupported mode.
    ("BLOCK.ASM", L("\t\textrn\tGrabBits:near"),
     L("\t\textrn\tGrabBits:near", "\t\textrn\tGetMode:near", "\t\textrn\tfBadMode:byte",
       "\t\textrn\tGrabBmp:near"), 1),
    ("BLOCK.ASM",
     L("GetBlock\tproc\tnear", "\t\tassume\tds:_TEXT"),
     L("GetBlock\tproc\tnear", "\t\tassume\tds:_TEXT",
       "\t\tcall\tGetMode\t\t\t;TANDYGR: grab what is on screen now"), 1),
    # Every graphics mode: GetInfo reports it grabbable (WINOLDAP only grabs
    # when GetInfo returns 1) and GetBlock writes a BMP plus a one-line text
    # record (TGBMP.ASM, TGCLIP.EXE).
    ("BLOCK.ASM", L("gbGrph:"),
     L("gbGrph:", "\t\tcmp\t[fBadMode],0\t\t;TANDYGR: unsupported mode",
       "\t\tjne\tgbErrUs",
       "\t\tcall\tGrabBmp\t\t\t;TANDYGR: graphics to a BMP",
       "\t\tjc\tgbErrUs", "\t\tjmp\tgbExitGood"), 1),
    ("GETINFO.ASM", L("\t\tpublic\tGetInfo"),
     L("\t\tpublic\tGetInfo", "\t\textrn\tfBadMode:byte"), 1),
    ("GETINFO.ASM", L("\t\tinc\tax\t\t\t\t;else show text", "giX:"),
     L("\t\tinc\tax\t\t\t\t;else show text", "giX:",
       "\t\tcmp\t[fBadMode],0\t\t;TANDYGR: graphics modes too",
       "\t\tjne\tgiX2", "\t\tmov\tax,1", "giX2:"), 1),
    ("GRABBITS.ASM", L("\t\tpublic\tGrabBits"),
     L("\t\tpublic\tGrabBits", "\t\tpublic\tComputeYBufPos\t;TANDYGR: TGBMP.ASM"), 1),
    # Link our modules instead of the DDK's SetSwapDrive and Save/Restore.
    ("CGAHERC/CGA/CGA.LNK", L("      setswap.obj       +", "      srscr.obj         +"),
     L("      tgsrscr.obj       +", "      tgtandy.obj       +", "      tgbmp.obj         +"), 1),
    ("CGAHERC/CGA/CGA.LNK", L("      edsave.obj        +"), "", 1),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stage(view, dest, patch):
    src = view / "DDK" / "286" / "DISPLAY" / "GRABBERS"
    shutil.copytree(src, dest / "GRABBERS")
    (dest / "INC").mkdir()
    shutil.copyfile(view / "DDK" / "286" / "INC" / "GRABBER.INC", dest / "INC" / "GRABBER.INC")
    for p in list(dest.rglob("*")):
        if p.is_file() and p.suffix.upper() in (".ASM", ".INC", ".LNK"):
            raw = p.read_bytes()
            p.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    changed = {}
    if patch:
        for name in OWN:
            raw = (HERE / f"{name}.ASM").read_bytes()
            (dest / "GRABBERS" / "CGAHERC" / f"{name}.ASM").write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            changed[f"CGAHERC/{name}.ASM"] = sha((dest / "GRABBERS" / "CGAHERC" / f"{name}.ASM").read_bytes())
        for rel, old, new, want in PATCHES:
            p = dest / "GRABBERS" / rel
            text = p.read_bytes().decode("latin-1")
            n = text.count(old)
            if n != want:
                raise SystemExit(f"BUILDTG: {rel}: anchor matched {n} times, expected {want}: {old[:50]!r}")
            text = text.replace(old, new)
            p.write_bytes(text.encode("latin-1"))
            changed[rel] = sha(text.encode("latin-1"))
    return changed


def branch_modules(patch):
    return [f for f in BRANCH if f not in REPLACED] + OWN if patch else BRANCH


def batches(patch):
    inc = r"-i.\ -i..\ -iR:\INC\ -v -dCGA"
    common = ["CD \\GRABBERS"] + [f"C:\\BIN\\MASM {inc} {f}; >> R:\\BUILD.LOG" for f in COMMON]
    branch = ["CD \\GRABBERS\\CGAHERC"] + [f"C:\\BIN\\MASM {inc} {f}.ASM,CGA\\; >> R:\\BUILD.LOG" for f in branch_modules(patch)]
    final = ["CD \\GRABBERS\\CGAHERC\\CGA",
             r"C:\BIN\MASM -i.\ -i..\ -i..\..\ -iR:\INC\ -v -dCGA CGA; >> R:\BUILD.LOG",
             r"C:\BIN\LINK @CGA.LNK >> R:\BUILD.LOG",
             r"C:\DDK\TOOLS\EXE2BIN CGA.2GR CGA.BIN >> R:\BUILD.LOG"]
    return ["@ECHO OFF\n" + "\n".join(b) + "\nCD \\\nEXIT\n" for b in (common, branch, final)]


def build(view, dosbox, d, patch):
    d.mkdir(parents=True)
    changed = stage(view, d, patch)
    for i, text in enumerate(batches(patch), 1):
        R.dos_text(d / f"BUILD{i}.BAT", text)
        R.run_dos(dosbox, view, d, f"BUILD{i}.BAT")
    log = (d / "BUILD.LOG").read_text(errors="replace")
    severe = re.findall(r"(\d+)\s+Severe\s+Errors", log)
    if len(severe) != len(COMMON) + len(branch_modules(patch)) + 1 or any(s != "0" for s in severe) or \
            re.search(r"error [AL]\d+|fatal|cannot", log, re.I):
        raise SystemExit(f"BUILDTG: assembly/link failed; see {d / 'BUILD.LOG'}")
    out = d / "GRABBERS" / "CGAHERC" / "CGA" / "CGA.BIN"
    if not out.exists():
        raise SystemExit("BUILDTG: no CGA.BIN produced")
    return out.read_bytes(), changed


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True, help="display view with BIN and DDK (tools/BUILDDEPS)")
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--retail", type=Path, help="optional: retail Windows 3.0 CGA.GR2 (expanded) for comparison")
    a = ap.parse_args(argv)
    out = a.out.resolve()
    if out.exists():
        raise SystemExit(f"BUILDTG: {out} exists")
    view = a.repo.resolve()
    control, _ = build(view, a.dosbox, out / "CONTROL", patch=False)
    tg, changed = build(view, a.dosbox, out / "PATCHED", patch=True)
    (out / "CONTROL.GR2").write_bytes(control)
    (out / "TANDYGR.GR2").write_bytes(tg)
    res = {"tandygr": {"file": "TANDYGR.GR2", "bytes": len(tg), "sha256": sha(tg)},
           "control": {"file": "CONTROL.GR2", "bytes": len(control), "sha256": sha(control),
                       "what": "unmodified DDK 286 CGA grabber, same build"},
           "patched_sources_sha256": changed, "edits": len(PATCHES)}
    if a.retail:
        retail = a.retail.read_bytes()
        res["retail_cga_gr2"] = {"bytes": len(retail), "sha256": sha(retail), "equals_control": retail == control}
    (out / "RESULT.JSON").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
