#!/usr/bin/env python3
"""Build TANDYGR.GR2, a Windows 3.0 real-mode grabber for the Tandy 1000.

  python3 src/tgrab/BUILDTG.PY --repo <display view> --dosbox <dosbox-x> --out <new dir>

Source: the Windows 3.0 DDK 286 CGA grabber (DDK\\286\\DISPLAY\\GRABBERS,
CGAHERC branch, -dCGA as its makefiles), from the pinned DDK view
(tools/BUILDDEPS). Nothing of the DDK is committed. Two builds are made in
DOSBox-X with the view's MASM 5.10, LINK and EXE2BIN:

  CONTROL.GR2   the unmodified DDK sources (control)
  TANDYGR.GR2   the same sources with the anchored edits in PATCHES

What the edits add for the Tandy 1000 (the retail CGA.GR2 knows only the
CGA modes 0-6, and indexes its mode table past its end for modes 8-0Ah):

  * The video mode, start address, cursor and mode-control bytes come from
    the BIOS data area (the DDK's own PGA path), not from the CGA light-pen
    regen measurement.
  * Modes 8 (160x200x16), 9 (320x200x16) and 0Ah (640x200x4) have their own
    InfoContext entries (Tandy layouts: 16 KB in two banks, 32 KB in four).
    Mode 7 and modes above 0Ah set fBadMode: SaveScreen refuses (Windows
    then does not switch away) and GetBlock grabs nothing.
  * The graphics save area is 32 KB (was 16 KB), so a DOS program in a
    32 KB mode is saved and restored exactly when the user switches away.
  * GetBlock re-reads the mode first, so a grab describes the current screen.

Windows 3.0 real-mode WINOLDAP copies a DOS screen to the Clipboard only
when GetInfo reports a text screen, so graphics screens are never grabbed
(docs/GRABBER.MD); text grabs work as with the DDK grabber.

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


def L(*lines):
    return "".join(x + "\r\n" for x in lines)


GRABBMP = L(
    "",
    ";TANDYGR: GrabBmp - full-screen grab of a 16-colour Tandy mode (8, 9).",
    ";  Windows 3.0 real-mode WINOLDAP puts only OEM text on the Clipboard,",
    ";  so the screen goes to a 4-bit BMP file (TEMP directory, else the root",
    ";  of the current drive) and WINOLDAP gets one text line:",
    ";  TANDYGR <path>.  TGCLIP.EXE turns that into a Clipboard bitmap.",
    ";  BMP colour index = Windows device index of the Tandy IRGB colour",
    ";  (bits 0 and 2 swapped), palette = the display driver's colour table.",
    ";  ENTRY es:di -> GrabRequest, ds = cs.  EXIT ax = record size, carry",
    ";  set if the file could not be written.  Called only from GetBlock,",
    ";  which WINOLDAP calls with DOS idle (it writes its own grab file next).",
    "tgPre\t\tdb\t'TANDYGR '",
    "tgPath\t\tdb\t80 dup (0)",
    "tgLen\t\tdw\t0\t\t\t;bytes of 'TANDYGR path',13,10",
    "tgTemp\t\tdb\t'TEMP='",
    "tgName\t\tdb\t'TANDYGR.BMP',0",
    "tgHandle\tdw\t0",
    "tgY\t\tdw\t0",
    "tgTblOk\t\tdb\t0",
    "tgTbl\t\tdb\t256 dup (0)",
    "tgRow\t\tdb\t160 dup (0)",
    "tgHdr\t\tdb\t'BM'",
    "tgFSize\t\tdd\t0",
    "\t\tdw\t0,0",
    "\t\tdd\t118",
    "\t\tdd\t40",
    "tgW\t\tdd\t0",
    "tgH\t\tdd\t0",
    "\t\tdw\t1,4",
    "\t\tdd\t0",
    "tgISize\t\tdd\t0",
    "\t\tdd\t0,0,16,16",
    "\t\tdb\t000h, 000h, 000h, 000h, 000h, 000h, 080h, 000h, 000h, 080h, 000h, 000h, 000h, 080h, 080h, 000h",
    "\t\tdb\t080h, 000h, 000h, 000h, 080h, 000h, 080h, 000h, 080h, 080h, 000h, 000h, 080h, 080h, 080h, 000h",
    "\t\tdb\t040h, 040h, 040h, 000h, 000h, 000h, 0FFh, 000h, 000h, 0FFh, 000h, 000h, 000h, 0FFh, 0FFh, 000h",
    "\t\tdb\t0FFh, 000h, 000h, 000h, 0FFh, 000h, 0FFh, 000h, 0FFh, 0FFh, 000h, 000h, 0FFh, 0FFh, 0FFh, 000h",
    "TGHDRLEN\tequ\t$ - tgHdr",
    "",
    ";tgPath = TEMP + '\\TANDYGR.BMP' (or d:\\TANDYGR.BMP); tgLen set",
    "tgBuildPath\tproc\tnear",
    "\t\tassume\tds:_TEXT",
    "\t\tpush\tes",
    "\t\tpush\tdi",
    "\t\tpush\tsi",
    "\t\tpush\tcx",
    "\t\tpush\tbx",
    "\t\tmov\tdi,offset tgPath",
    "\t\tmov\tah,62h\t\t\t;current PSP",
    "\t\tint\t21h",
    "\t\tmov\tes,bx",
    "\t\tmov\tbx,es:[2Ch]",
    "\t\tor\tbx,bx",
    "\t\tjz\ttgNoTemp",
    "\t\tmov\tes,bx",
    "\t\txor\tbx,bx",
    "tgEnv:",
    "\t\tcmp\tbyte ptr es:[bx],0",
    "\t\tje\ttgNoTemp",
    "\t\tmov\tsi,offset tgTemp",
    "\t\tmov\tcx,5",
    "tgCmp:",
    "\t\tmov\tal,es:[bx]",
    "\t\tcmp\tal,[si]",
    "\t\tjne\ttgSkip",
    "\t\tinc\tbx",
    "\t\tinc\tsi",
    "\t\tloop\ttgCmp",
    "\t\tmov\tcx,64",
    "tgCopy:",
    "\t\tmov\tal,es:[bx]",
    "\t\tor\tal,al",
    "\t\tjz\ttgSlash",
    "\t\tmov\t[di],al",
    "\t\tinc\tdi",
    "\t\tinc\tbx",
    "\t\tloop\ttgCopy",
    "\t\tjmp\tshort tgSlash",
    "tgSkip:",
    "\t\tcmp\tbyte ptr es:[bx],0",
    "\t\tje\ttgNext",
    "\t\tinc\tbx",
    "\t\tjmp\ttgSkip",
    "tgNext:",
    "\t\tinc\tbx",
    "\t\tjmp\ttgEnv",
    "tgNoTemp:",
    "\t\tmov\tah,19h\t\t\t;current drive",
    "\t\tint\t21h",
    "\t\tadd\tal,'A'",
    "\t\tmov\t[di],al",
    "\t\tmov\tbyte ptr [di+1],':'",
    "\t\tadd\tdi,2",
    "tgSlash:",
    "\t\tcmp\tdi,offset tgPath",
    "\t\tje\ttgAddSl",
    "\t\tcmp\tbyte ptr [di-1],'\\'",
    "\t\tje\ttgName0",
    "tgAddSl:",
    "\t\tmov\tbyte ptr [di],'\\'",
    "\t\tinc\tdi",
    "tgName0:",
    "\t\tmov\tsi,offset tgName",
    "tgName1:",
    "\t\tmov\tal,[si]",
    "\t\tmov\t[di],al",
    "\t\tinc\tsi",
    "\t\tinc\tdi",
    "\t\tor\tal,al",
    "\t\tjnz\ttgName1",
    "\t\tsub\tdi,offset tgPath + 1\t;path length",
    "\t\tadd\tdi,8 + 2\t\t;'TANDYGR ' and CR LF",
    "\t\tmov\t[tgLen],di",
    "\t\tpop\tbx",
    "\t\tpop\tcx",
    "\t\tpop\tsi",
    "\t\tpop\tdi",
    "\t\tpop\tes",
    "\t\tret",
    "tgBuildPath\tendp",
    "",
    "\t\tpublic\tGrabBmp",
    "GrabBmp\t\tproc\tnear",
    "\t\tassume\tds:_TEXT",
    "\t\tcld",
    "\t\tcall\ttgBuildPath",
    "\t\tmov\tax,es:[di]",
    "\t\tor\tax,es:[di][2]",
    "\t\tjnz\ttgGo",
    "\t\tmov\tax,[tgLen]\t\t;size query",
    "\t\tadd\tax,4 + 1",
    "\t\tclc",
    "\t\tret",
    "tgGo:",
    "\t\tpush\tes",
    "\t\tpush\tdi",
    "\t\tcmp\t[tgTblOk],0\t\t;nibble table: IRGB to Windows index",
    "\t\tjne\ttgTblDone",
    "\t\txor\tbx,bx",
    "tgTblLp:",
    "\t\tmov\tal,bl",
    "\t\tcall\ttgSwap",
    "\t\tmov\tah,al\t\t\t;low nibble done",
    "\t\tmov\tal,bl",
    "\t\tmov\tcl,4",
    "\t\tshr\tal,cl",
    "\t\tcall\ttgSwap",
    "\t\tshl\tal,cl",
    "\t\tor\tal,ah",
    "\t\tmov\ttgTbl[bx],al",
    "\t\tinc\tbx",
    "\t\tcmp\tbx,256",
    "\t\tjb\ttgTblLp",
    "\t\tmov\t[tgTblOk],1",
    "tgTblDone:",
    "\t\tmov\tax,[IC.icPixelsX]",
    "\t\tmov\tword ptr [tgW],ax",
    "\t\tmov\tax,[IC.icPixelsY]",
    "\t\tmov\tword ptr [tgH],ax",
    "\t\tmul\t[IC.icWidthBytes]",
    "\t\tmov\tword ptr [tgISize],ax",
    "\t\tmov\tword ptr [tgISize][2],dx",
    "\t\tadd\tax,TGHDRLEN",
    "\t\tadc\tdx,0",
    "\t\tmov\tword ptr [tgFSize],ax",
    "\t\tmov\tword ptr [tgFSize][2],dx",
    "\t\tmov\tdx,offset tgPath\t;create the file",
    "\t\txor\tcx,cx",
    "\t\tmov\tah,3Ch",
    "\t\tint\t21h",
    "\t\tjnc\ttgOpen",
    "\t\tjmp\ttgFail0",
    "tgOpen:",
    "\t\tmov\t[tgHandle],ax",
    "\t\tmov\tbx,ax",
    "\t\tmov\tdx,offset tgHdr",
    "\t\tmov\tcx,TGHDRLEN",
    "\t\tmov\tah,40h",
    "\t\tint\t21h",
    "\t\tjc\ttgFail",
    "\t\tmov\tax,[IC.icPixelsY]\t;rows bottom-up",
    "\t\tmov\t[tgY],ax",
    "tgRowLp:",
    "\t\tdec\t[tgY]",
    "\t\tmov\tbx,[tgY]",
    "\t\tpush\tds",
    "\t\tlds\tsi,[IC.iclpScr]",
    "\t\tassume\tds:nothing",
    "\t\txor\tsi,si",
    "\t\tcall\tComputeYBufPos",
    "\t\tpush\tcs",
    "\t\tpop\tes",
    "\t\tmov\tdi,offset tgRow",
    "\t\tmov\tcx,cs:[IC.icWidthBytes]",
    "\t\txor\tbh,bh",
    "tgXl:",
    "\t\tlodsb",
    "\t\tmov\tbl,al",
    "\t\tmov\tal,cs:tgTbl[bx]",
    "\t\tstosb",
    "\t\tloop\ttgXl",
    "\t\tpop\tds",
    "\t\tassume\tds:_TEXT",
    "\t\tmov\tbx,[tgHandle]",
    "\t\tmov\tdx,offset tgRow",
    "\t\tmov\tcx,[IC.icWidthBytes]",
    "\t\tmov\tah,40h",
    "\t\tint\t21h",
    "\t\tjc\ttgFail",
    "\t\tcmp\t[tgY],0",
    "\t\tjne\ttgRowLp",
    "\t\tmov\tbx,[tgHandle]",
    "\t\tmov\tah,3Eh",
    "\t\tint\t21h",
    "\t\tpop\tdi\t\t\t;the text record for WINOLDAP",
    "\t\tpop\tes",
    "\t\tles\tdi,es:[di][grlpData]",
    "\t\tmov\tax,GT_TEXT",
    "\t\tstosw",
    "\t\tmov\tax,[tgLen]",
    "\t\tadd\tax,4 + 1",
    "\t\tstosw",
    "\t\tmov\tsi,offset tgPre",
    "\t\tmov\tcx,[tgLen]",
    "\t\tsub\tcx,2",
    "\t\trep\tmovsb",
    "\t\tmov\tax,0A0Dh",
    "\t\tstosw",
    "\t\txor\tal,al",
    "\t\tstosb",
    "\t\tmov\tax,[tgLen]",
    "\t\tadd\tax,4 + 1",
    "\t\tclc",
    "\t\tret",
    "tgFail:",
    "\t\tmov\tbx,[tgHandle]",
    "\t\tmov\tah,3Eh",
    "\t\tint\t21h",
    "tgFail0:",
    "\t\tpop\tdi",
    "\t\tpop\tes",
    "\t\tstc",
    "\t\tret",
    "GrabBmp\t\tendp",
    "",
    ";al = IRGB nibble -> Windows device index (bits 0 and 2 swapped)",
    "tgSwap\t\tproc\tnear",
    "\t\tpush\tdx",
    "\t\tmov\tdl,al",
    "\t\tand\tdl,0Ah",
    "\t\ttest\tal,1",
    "\t\tjz\ttgS1",
    "\t\tor\tdl,4",
    "tgS1:",
    "\t\ttest\tal,4",
    "\t\tjz\ttgS2",
    "\t\tor\tdl,1",
    "tgS2:",
    "\t\tmov\tal,dl",
    "\t\tpop\tdx",
    "\t\tret",
    "tgSwap\t\tendp",
    "",
)

# (file, old, new, count): CRLF text, matched exactly.
PATCHES = [
    # 32 KB graphics save area (the 32 KB Tandy modes).
    ("CGAHERC/CGA/CGA.ASM", L("MAX_TOTGRPH\t=\t16*1024"),
     L("MAX_TOTGRPH\t=\t32*1024\t\t;TANDYGR: Tandy 32 KB modes"), 1),
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
    # SaveScreen refuses an unsupported mode (Windows then stays in it).
    ("CGAHERC/SRSCR.ASM", L("\t\textrn\tSetMode:near"),
     L("\t\textrn\tSetMode:near", "\t\textrn\tfBadMode:byte"), 1),
    ("CGAHERC/SRSCR.ASM",
     L("\t\tcall\tGetmode", "\t\tmov\t[DC.dcfSwitchGmt],FALSE"),
     L("\t\tcall\tGetmode",
       "\t\tcmp\t[fBadMode],TRUE\t\t;TANDYGR: unsupported mode",
       "\t\tjne\tssModeOk",
       "\t\tjmp\tssErr",
       "ssModeOk:",
       "\t\tmov\t[DC.dcfSwitchGmt],FALSE"), 1),
    # GetBlock: current mode first; no grab of an unsupported mode.
    ("BLOCK.ASM", L("\t\textrn\tGrabBits:near"),
     L("\t\textrn\tGrabBits:near", "\t\textrn\tGetMode:near", "\t\textrn\tfBadMode:byte"), 1),
    ("BLOCK.ASM",
     L("GetBlock\tproc\tnear", "\t\tassume\tds:_TEXT"),
     L("GetBlock\tproc\tnear", "\t\tassume\tds:_TEXT",
       "\t\tcall\tGetMode\t\t\t;TANDYGR: grab what is on screen now"), 1),
    ("BLOCK.ASM", L("gbGrph:"),
     L("gbGrph:", "\t\tcmp\t[fBadMode],0\t\t;TANDYGR: unsupported mode",
       "\t\tjne\tgbErrUs"), 1),
    # Graphics grabs of the 16-colour Tandy modes: GetInfo reports them as
    # grabbable (WINOLDAP only grabs when GetInfo returns 1) and GetBlock
    # writes a BMP plus a one-line text record (GrabBmp, TGCLIP.EXE).
    ("GETINFO.ASM", L("\t\tinc\tax\t\t\t\t;else show text", "giX:"),
     L("\t\tinc\tax\t\t\t\t;else show text", "giX:",
       "\t\tcmp\t[IC.icBitsPixel],4\t;TANDYGR: 16-colour modes 8, 9",
       "\t\tjne\tgiX2", "\t\tmov\tax,1", "giX2:"), 1),
    ("BLOCK.ASM", L("\t\textrn\tGrabBits:near"),
     L("\t\textrn\tGrabBits:near", "\t\textrn\tGrabBmp:near"), 1),
    ("BLOCK.ASM", L("\t\tjne\tgbErrUs"),
     L("\t\tjne\tgbErrUs",
       "\t\tcmp\t[IC.icBitsPixel],4\t;TANDYGR: 16-colour modes to a BMP",
       "\t\tjne\tgbGrphCga", "\t\tcall\tGrabBmp", "\t\tjc\tgbErrUs",
       "\t\tjmp\tgbExitGood", "gbGrphCga:"), 1),
    ("GRABBITS.ASM", L("\t\tsubttl\tGrabBits"), GRABBMP + L("\t\tsubttl\tGrabBits"), 1),
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


def batches():
    inc = r"-i.\ -i..\ -iR:\INC\ -v -dCGA"
    common = ["CD \\GRABBERS"] + [f"C:\\BIN\\MASM {inc} {f}; >> R:\\BUILD.LOG" for f in COMMON]
    branch = ["CD \\GRABBERS\\CGAHERC"] + [f"C:\\BIN\\MASM {inc} {f}.ASM,CGA\\; >> R:\\BUILD.LOG" for f in BRANCH]
    final = ["CD \\GRABBERS\\CGAHERC\\CGA",
             r"C:\BIN\MASM -i.\ -i..\ -i..\..\ -iR:\INC\ -v -dCGA CGA; >> R:\BUILD.LOG",
             r"C:\BIN\LINK @CGA.LNK >> R:\BUILD.LOG",
             r"C:\DDK\TOOLS\EXE2BIN CGA.2GR CGA.BIN >> R:\BUILD.LOG"]
    return ["@ECHO OFF\n" + "\n".join(b) + "\nCD \\\nEXIT\n" for b in (common, branch, final)]


def build(view, dosbox, d, patch):
    d.mkdir(parents=True)
    changed = stage(view, d, patch)
    for i, text in enumerate(batches(), 1):
        R.dos_text(d / f"BUILD{i}.BAT", text)
        R.run_dos(dosbox, view, d, f"BUILD{i}.BAT")
    log = (d / "BUILD.LOG").read_text(errors="replace")
    severe = re.findall(r"(\d+)\s+Severe\s+Errors", log)
    if len(severe) != len(COMMON) + len(BRANCH) + 1 or any(s != "0" for s in severe) or \
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
