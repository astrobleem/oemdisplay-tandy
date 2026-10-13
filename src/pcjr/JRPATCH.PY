#!/usr/bin/env python3
"""PCjr edits for the 320x200x16 driver (proposed TNDYJR, docs/PCJR.MD).

Usage:
  python3 src/pcjr/JRPATCH.PY --check            self-test on this checkout
  python3 src/pcjr/JRPATCH.PY --diff             review against src/tandysw
  python3 src/pcjr/JRPATCH.PY --out <new-dir>    write V1JR.ASM, TCURJR.ASM

BUILDJR.PY applies the same edits to the fully staged BUILD88 sources
(EGA/TSOFT.ASM and EGA/TCURSOR.ASM) after every TR5 port step, which is the
path that produces a driver. Edits:

  1. A public word `video_seg` (default B800h) in the driver Data segment.
  2. TEnable, after INT 10h mode 09h: on an IBM PCjr (F000:FFFE = FDh) only,
     video_seg = (40:8Ah & 6) * 400h, the physical 32KB page. Elsewhere it
     stays B800h, so a Tandy takes exactly today's drawing path.
  3. Every VRAM site loads ES from video_seg through an explicit `seg`
     fixup and ES override, the same `seg` idiom the renderer already uses
     for shadow_bits, so it does not depend on DS at that point. AX is
     clobbered exactly as the original `mov ax,0B800h` did.

Every edit must match the expected number of times or nothing is written.
"""
import argparse
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "tandysw"

DATA_OLD = "old_mode db 3\r\n"
DATA_NEW = ("old_mode db 3\r\n"
            "public video_seg\r\n"
            "video_seg dw 0b800h          ; PCjr physical page segment (JRPATCH)\r\n")

ENABLE_OLD = "    mov ax,9\r\n    int 10h\r\n"
ENABLE_NEW = ("    mov ax,9\r\n"
              "    int 10h\r\n"
              "    ; PCjr only: B800h is a 16KB CPU window repeated at BC00h, so the\r\n"
              "    ; 32KB banked page must be addressed at its physical segment.\r\n"
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
              "enable_vseg_done:\r\n")

VRAM_LOAD = ("    mov ax,seg video_seg      ; PCjr: physical page (JRPATCH)\r\n"
             "    mov es,ax\r\n"
             "    mov es,es:video_seg\r\n")

TC_EXTERN_OLD = "    externB enabled_flag\r\n"
TC_EXTERN_NEW = "    externB enabled_flag\r\n    externW video_seg\r\n"


def replace_n(text, old, new, want, name):
    n = text.count(old)
    if n != want:
        raise SystemExit(f"JRPATCH: '{name}' matched {n} times, expected {want}")
    return text.replace(old, new)


def patch_v1(text, vram_sites):
    text = replace_n(text, DATA_OLD, DATA_NEW, 1, "data word")
    text = replace_n(text, ENABLE_OLD, ENABLE_NEW, 1, "enable page")
    for upper in (False, True):
        old = "    mov ax,0B800h\r\n    mov es,ax\r\n" if upper else "    mov ax,0b800h\r\n    mov es,ax\r\n"
        want = vram_sites if not upper else 0
        text = replace_n(text, old, VRAM_LOAD, want, "renderer VRAM sites")
    if "0b800h\r\n    mov es" in text.lower():
        raise SystemExit("JRPATCH: an unpatched renderer VRAM site remains")
    return text


def patch_tc(text):
    text = replace_n(text, TC_EXTERN_OLD, TC_EXTERN_NEW, 1, "cursor extern")
    text = replace_n(text, "    mov ax,0B800h\r\n    mov es,ax\r\n", VRAM_LOAD, 2, "cursor VRAM sites")
    if "0b800h" in text.lower():
        raise SystemExit("JRPATCH: an unpatched cursor VRAM site remains")
    return text


def patch_staged(ega_dir, vram_sites=4):
    """Patch BUILD88-staged EGA/TSOFT.ASM and EGA/TCURSOR.ASM in place."""
    ega = Path(ega_dir)
    out = {}
    for name, fn in (("TSOFT.ASM", lambda t: patch_v1(t, vram_sites)), ("TCURSOR.ASM", patch_tc)):
        p = ega / name
        old = p.read_bytes().decode("latin-1")
        new = fn(old)
        check_text(new)
        p.write_bytes(new.encode("latin-1"))
        out[name] = (old, new)
    return out


def check_text(new):
    assert "\n" not in new.replace("\r\n", ""), "bare LF introduced"
    for bad in ("movzx", "pusha", "push 0", ".286", "shl ax,10"):
        assert bad not in new.lower(), bad


def stage_raw():
    v1 = (SRC / "V1.ASM").read_bytes().decode("latin-1")
    tc = (SRC / "TCURSOR.ASM").read_bytes().decode("latin-1")
    if "\r\n" not in v1 or "\r\n" not in tc:
        raise SystemExit("JRPATCH: sources are not CRLF")
    header = ("; Staged by src/pcjr/JRPATCH.PY for the proposed TNDYJR PCjr driver.\r\n"
              "; Review copy; BUILDJR.PY patches the fully staged sources instead.\r\n")
    staged = {"V1JR.ASM": (v1, header + patch_v1(v1, 1)),
              "TCURJR.ASM": (tc, header + patch_tc(tc))}
    for _, new in staged.values():
        check_text(new)
    v1jr = staged["V1JR.ASM"][1]
    i = v1jr.index("int 10h\r\n    ; PCjr only")
    assert v1jr.index("enable_vseg_done:\r\n") > i
    assert v1jr.count("mov es,es:video_seg") == 1
    assert staged["TCURJR.ASM"][1].count("mov es,es:video_seg") == 2
    return staged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()
    staged = stage_raw()
    if a.diff:
        for name, (old, new) in staged.items():
            src = "V1.ASM" if name == "V1JR.ASM" else "TCURSOR.ASM"
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                fromfile="tandysw/" + src, tofile="pcjr/" + name))
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=False)
        for name, (_, new) in staged.items():
            (out / name).write_bytes(new.encode("latin-1"))
        print(f"JRPATCH: wrote {', '.join(staged)} in {out}")
    if a.check or not (a.out or a.diff):
        print("JRPATCH: self-test PASS (source edits only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
