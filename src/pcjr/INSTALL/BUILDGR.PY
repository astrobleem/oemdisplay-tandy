#!/usr/bin/env python3
"""Build JRGRAB.GR2, the PCjr-safe Windows 3.0 real-mode screen grabber.

  python3 src/pcjr/INSTALL/BUILDGR.PY --repo <display view> --dosbox <dosbox-x> --out <new dir>

The source is the Windows 3.0 DDK's 286 CGA grabber (DDK\\286\\DISPLAY\\GRABBERS,
CGAHERC branch, built with -dCGA exactly as its makefiles do), from the
pinned DDK view (tools/BUILDDEPS). Nothing of the DDK is committed. Two
builds are made in DOSBox-X with the view's MASM 5.10, LINK and EXE2BIN:

  CONTROL\\CGA.GR2   the unmodified DDK sources (a control; its hash is
                    recorded, and is compared with --retail if given)
  JRGRAB.GR2        the same sources with the anchored edits below

Why: the retail Windows 3.0 CGA.GR2 finds the video mode by firing the
6845 light-pen latch (ports 3DBh/3DCh) and matching the measured regen
length against CGA tables. On DOSBox-X's PCjr this misidentifies text mode
3 and RestoreScreen brings a switched-away DOS program back in a 4-colour
graphics mode (docs/PCJR.MD). Separately, GetMode indexes a 7-entry table
(modes 0-6) with the BIOS mode byte, so the PCjr-only modes 8, 9 and 0Ah
read past it and SaveScreen/RestoreScreen copy to and from a garbage far
pointer. The edits, each matched an exact number of times:

  1. CGA.ASM DevInit: on a PCjr (F000:FFFE = FDh) set fPCjr.
  2. CGA.ASM GetModeDev: on a PCjr skip the light-pen measurement and take
     the mode, start, cursor and mode-control bytes from the BIOS data area
     (the path the DDK already uses for the PGA).
  3. GSMODE.ASM GetMode: a BIOS mode above 6 sets fBadMode and uses the
     mode-6 InfoContext (B800h, 16 KB, graphics: no block operations) so no
     pointer leaves the 16 KB B800h window.
  4. SRSCR.ASM SaveScreen: with fBadMode, refuse (beep, carry): Windows
     then does not switch away from that DOS program.
  5. GRABSCR.ASM GrabScreen: with fBadMode, grab nothing.

On anything but a PCjr, edits 1-2 change nothing; 3-5 only affect modes
above 6, which this CGA grabber never supported. Exit 0 on success.
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
ROOT = HERE.parents[2]
R = importlib.machinery.SourceFileLoader("reserve_harness", str(ROOT / "src" / "tandysw" / "RESERVE.PY")).load_module()

COMMON = ["BLOCK", "EDGRAB", "ENTRY", "GETINFO", "GRABBITS", "GRABSCR", "INOUT", "INQUIRE", "OEM", "PROMPT", "RCOLOR"]
BRANCH = ["BEPAINT", "BLOCKDEV", "EDSAVE", "GSMODE", "SETSWAP", "SRSCR"]

# (file, old, new, count): CRLF text, matched exactly.
PATCHES = [
    ("CGAHERC/CGA/CGA.ASM",
     "fPGA\t\tdb\tFALSE\r\n",
     "fPGA\t\tdb\tFALSE\r\nfPCjr\t\tdb\tFALSE\t\t;JRGRAB: IBM PCjr (F000:FFFE = FDh)\r\n", 1),
    ("CGAHERC/CGA/CGA.ASM",
     "diNoPga:\r\n\t\tpop\tes\r\n",
     "diNoPga:\r\n"
     "\t\tmov\tax,0F000h\t\t;JRGRAB: a PCjr has no usable\r\n"
     "\t\tmov\tes,ax\t\t\t;  light-pen mode measurement\r\n"
     "\t\tcmp\tbyte ptr es:[0FFFEh],0FDh\r\n"
     "\t\tjne\tdiNotJr\r\n"
     "\t\tmov\t[fPCjr],TRUE\r\n"
     "diNotJr:\r\n"
     "\t\tpop\tes\r\n", 1),
    ("CGAHERC/CGA/CGA.ASM",
     "\t\tcmp\t[fPGA],TRUE\r\n\t\tje\tgmdNotRogue\r\n",
     "\t\tcmp\t[fPGA],TRUE\r\n\t\tje\tgmdNotRogue\r\n"
     "\t\tcmp\t[fPCjr],TRUE\t\t;JRGRAB: PCjr, trust the BIOS\r\n"
     "\t\tje\tgmdNotRogue\r\n", 1),
    ("CGAHERC/GSMODE.ASM",
     "\t\tpublic\tGetMode\r\n",
     "\t\tpublic\tGetMode\r\n\t\tpublic\tfBadMode\r\n", 1),
    ("CGAHERC/GSMODE.ASM",
     "\t\tmov\tsi,offset IT\r\n\t\tmov\tdi,offset IC\r\n\t\tmov\tal,[DC.dcScrMode]\r\n",
     "\t\tmov\tsi,offset IT\r\n\t\tmov\tdi,offset IC\r\n\t\tmov\tal,[DC.dcScrMode]\r\n"
     "\t\tmov\t[fBadMode],FALSE\t;JRGRAB: modes above 6 (PCjr 8-0Ah)\r\n"
     "\t\tcmp\tal,6\t\t\t;  have no table entry: use the\r\n"
     "\t\tjbe\tgmModeOk\t\t;  16 KB graphics entry and refuse\r\n"
     "\t\tmov\t[fBadMode],TRUE\t\t;  save and grab\r\n"
     "\t\tmov\tal,6\r\n"
     "gmModeOk:\r\n", 1),
    ("CGAHERC/GSMODE.ASM",
     "\t\tsubttl\tGetmode\r\n",
     "fBadMode\tdb\t0\t\t\t;JRGRAB: set by GetMode\r\n\r\n\t\tsubttl\tGetmode\r\n", 1),
    ("CGAHERC/SRSCR.ASM",
     "\t\textrn\tGetMode:near\r\n",
     "\t\textrn\tGetMode:near\r\n\t\textrn\tfBadMode:byte\r\n", 1),
    ("CGAHERC/SRSCR.ASM",
     "\t\tcall\tGetmode\r\n\t\tmov\t[DC.dcfSwitchGmt],FALSE\r\n",
     "\t\tcall\tGetmode\r\n"
     "\t\tcmp\t[fBadMode],TRUE\t\t;JRGRAB: unsupported mode\r\n"
     "\t\tjne\tssModeOk\r\n"
     "\t\tjmp\tssErr\r\n"
     "ssModeOk:\r\n"
     "\t\tmov\t[DC.dcfSwitchGmt],FALSE\r\n", 1),
    ("GRABSCR.ASM",
     "\t\textrn\tGetMode:near\r\n",
     "\t\textrn\tGetMode:near\r\n\t\textrn\tfBadMode:byte\r\n", 1),
    ("GRABSCR.ASM",
     "\t\tcall\tGetMode \t\t\t;get display state\r\n",
     "\t\tcall\tGetMode \t\t\t;get display state\r\n"
     "\t\tcmp\tcs:[fBadMode],0\t\t;JRGRAB: unsupported mode\r\n"
     "\t\tje\tgsModeOk\r\n"
     "\t\tjmp\tgsX\r\n"
     "gsModeOk:\r\n", 1),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stage(view, dest, patch):
    src = view / "DDK" / "286" / "DISPLAY" / "GRABBERS"
    shutil.copytree(src, dest / "GRABBERS")
    (dest / "INC").mkdir()
    shutil.copyfile(view / "DDK" / "286" / "INC" / "GRABBER.INC", dest / "INC" / "GRABBER.INC")
    # The view stores LF text; DOS tools get CRLF (same bytes otherwise).
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
                raise SystemExit(f"BUILDGR: {rel}: anchor matched {n} times, expected {want}: {old[:40]!r}")
            text = text.replace(old, new)
            p.write_bytes(text.encode("latin-1"))
            changed[rel] = sha(text.encode("latin-1"))
    return changed


def batches():
    """Three short DOS sessions (the shared runner allows 60 s each)."""
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
        raise SystemExit(f"BUILDGR: assembly/link failed; see {d / 'BUILD.LOG'}")
    out = d / "GRABBERS" / "CGAHERC" / "CGA" / "CGA.BIN"
    if not out.exists():
        raise SystemExit("BUILDGR: no CGA.BIN produced")
    return out.read_bytes(), changed


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True, help="display view with BIN and DDK (tools/BUILDDEPS)")
    ap.add_argument("--dosbox", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--retail", type=Path, help="optional: the retail Windows 3.0 CGA.GR2 (expanded) for comparison")
    a = ap.parse_args(argv)
    out = a.out.resolve()
    if out.exists():
        raise SystemExit(f"BUILDGR: {out} exists")
    view = a.repo.resolve()
    control, _ = build(view, a.dosbox, out / "CONTROL", patch=False)
    jr, changed = build(view, a.dosbox, out / "PATCHED", patch=True)
    (out / "CONTROL.GR2").write_bytes(control)
    (out / "JRGRAB.GR2").write_bytes(jr)
    res = {"jrgrab": {"file": "JRGRAB.GR2", "bytes": len(jr), "sha256": sha(jr)},
           "control": {"file": "CONTROL.GR2", "bytes": len(control), "sha256": sha(control),
                       "what": "unmodified DDK 286 CGA grabber, same build"},
           "patched_sources_sha256": changed,
           "edits": len(PATCHES)}
    if a.retail:
        retail = a.retail.read_bytes()
        res["retail_cga_gr2"] = {"bytes": len(retail), "sha256": sha(retail),
                                 "equals_control": retail == control}
    (out / "RESULT.JSON").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
