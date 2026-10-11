#!/usr/bin/env python3
"""Stage the proposed PCjr variant of the 320x200x16 driver sources.

Usage:
  python3 src/pcjr/JRPATCH.PY --out <new-dir>          stage V1JR.ASM, TCURJR.ASM
  python3 src/pcjr/JRPATCH.PY --check                  self-test only

Reads src/tandysw/V1.ASM and src/tandysw/TCURSOR.ASM from this checkout and
writes renamed copies with exactly three behavioral edits (docs/PCJR.MD):

  1. V1: new public word `video_seg` (default B800h) in the driver Data segment.
  2. V1 TEnable: after INT 10h mode 09h, on an IBM PCjr (F000:FFFE = FDh)
     set video_seg from the BIOS page-register copy at 40:8Ah:
     (CRT page & 6) * 400h. Non-PCjr machines keep B800h, so a Tandy run of
     the staged source is byte-for-byte the same drawing path.
  3. V1 FlushRows and both TCURSOR VRAM sites load ES from video_seg instead
     of the constant B800h. FlushRows reads it before DS moves to the shadow.

Every edit must match exactly once; otherwise nothing is written. The output
is SOURCE ONLY. It has not been assembled against the pinned DDK, linked,
or run under Windows; BUILD88 integration is a later step. CRLF is kept.
"""
import argparse
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "tandysw"

V1_EDITS = [
    ("data word",
     "old_mode db 3\r\n",
     "old_mode db 3\r\n"
     "public video_seg\r\n"
     "video_seg dw 0b800h          ; PCjr: physical page segment (JRPATCH)\r\n"),
    ("flush target",
     "    mov ax,seg shadow_bits\r\n"
     "    mov ds,ax\r\n"
     "    mov ax,0b800h\r\n"
     "    mov es,ax\r\n"
     "flush_row:\r\n",
     "    mov es,video_seg          ; read while DS is still the driver Data\r\n"
     "    mov ax,seg shadow_bits\r\n"
     "    mov ds,ax\r\n"
     "flush_row:\r\n"),
    ("enable page",
     "    mov ax,9\r\n"
     "    int 10h\r\n",
     "    mov ax,9\r\n"
     "    int 10h\r\n"
     "    ; PCjr only: B800h is a 16KB CPU window aliased at BC00h, so the\r\n"
     "    ; 32KB banked page must be written at its physical segment.\r\n"
     "    mov video_seg,0b800h\r\n"
     "    mov ax,0f000h\r\n"
     "    mov es,ax\r\n"
     "    cmp byte ptr es:[0fffeh],0fdh\r\n"
     "    jne enable_vseg_done\r\n"
     "    mov ax,40h\r\n"
     "    mov es,ax\r\n"
     "    mov al,es:[8ah]\r\n"
     "    and ax,0006h              ; CRT page; 32KB pages are even\r\n"
     "    mov cl,10\r\n"
     "    shl ax,cl                 ; 16KB page -> paragraphs\r\n"
     "    mov video_seg,ax\r\n"
     "enable_vseg_done:\r\n"),
]

TC_EDITS = [
    ("extern",
     "    externB enabled_flag\r\n",
     "    externB enabled_flag\r\n"
     "    externW video_seg\r\n"),
    ("vram sites",
     "    mov ax,0B800h\r\n"
     "    mov es,ax\r\n",
     "    mov es,video_seg\r\n"),
]


def apply(text, edits, expect_counts):
    for (name, old, new), want in zip(edits, expect_counts):
        n = text.count(old)
        if n != want:
            raise SystemExit(f"JRPATCH: edit '{name}' matched {n} times, expected {want}")
        text = text.replace(old, new)
    return text


def stage():
    v1 = (SRC / "V1.ASM").read_bytes().decode("latin-1")
    tc = (SRC / "TCURSOR.ASM").read_bytes().decode("latin-1")
    if "\r\n" not in v1 or "\r\n" not in tc:
        raise SystemExit("JRPATCH: sources are not CRLF; check out with .gitattributes")
    v1jr = apply(v1, V1_EDITS, [1, 1, 1])
    tcjr = apply(tc, TC_EDITS, [1, 2])
    header = ("; Staged by src/pcjr/JRPATCH.PY for the proposed TNDYJR PCjr driver.\r\n"
              "; Not assembled or runtime-tested. See docs/PCJR.MD.\r\n")
    return {"V1JR.ASM": (v1, header + v1jr), "TCURJR.ASM": (tc, header + tcjr)}


def check(staged):
    v1jr = staged["V1JR.ASM"][1]
    tcjr = staged["TCURJR.ASM"][1]
    assert "0b800h\r\n    mov es,ax" not in v1jr.lower()
    assert "0b800h" not in tcjr.lower()
    assert v1jr.count("video_seg") == 5, v1jr.count("video_seg")
    assert tcjr.count("mov es,video_seg") == 2
    # The read of video_seg must come before DS is switched to the shadow.
    i = v1jr.index("    mov es,video_seg")
    assert v1jr.index("    mov ds,ax\r\nflush_row:") > i
    # No new instructions beyond 8086 in the inserted text.
    for bad in ("push 0", "shl ax,10", "movzx", "pusha", ".286"):
        assert bad not in v1jr and bad not in tcjr, bad
    for _, new in staged.values():
        assert "\n" not in new.replace("\r\n", ""), "bare LF introduced"
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--diff", action="store_true", help="print unified diffs")
    a = ap.parse_args()
    staged = stage()
    check(staged)
    if a.diff:
        for name, (old, new) in staged.items():
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                fromfile="tandysw/" + ("V1.ASM" if name == "V1JR.ASM" else "TCURSOR.ASM"),
                tofile="pcjr/" + name))
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=False)
        for name, (_, new) in staged.items():
            (out / name).write_bytes(new.encode("latin-1"))
        print(f"JRPATCH: staged {', '.join(staged)} in {out}")
    if a.check or not (a.out or a.diff):
        print("JRPATCH: self-test PASS (source staging only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
