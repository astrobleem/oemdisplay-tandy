#!/usr/bin/env python3
"""ColorPlus Output optimisations: marker skip, bounded polylines, narrow flush.

Usage:
  python3 src/pcp/CPPOUT.PY --check [--stage <staged EGA dir>]

Brings the Output optimisations of the PC1512 driver (src/pc1512/P15OUT.PY,
PR184) to the fixed 320x200x16 Plantronics ColorPlus driver. It edits only
TOutput in the staged EGA/TSOFT.ASM, after PCPPATCH.patch_staged and before
the first assembly (BUILDPCP.PY):

1. src/rrect/RRPATCH.patch_candidate (PR151), applied unchanged: GDI's
   OS_BEGINNSCAN/OS_ENDNSCAN markers skip the copy and the cursor work, and
   3..1024-point polylines are bounded to the rows between their points.
2. The synchronous X half of the XYRRECT batch work: TOutput also collects
   the validated X extent, rounds it outward to eight-pixel logical byte
   columns and presents through the stage's existing FlushRetainColumns.
   Full-width work ([0,SCREEN_WIDTH)) keeps FlushRetainRows. Every Output
   call still presents before it returns: no pending state, no marker-owned
   state, no change to the renderer call, its return value or registers.

ColorPlus specifics. The shadow keeps four 40-byte planes per row (R,G,B,I;
SCREEN_W_BYTES is 40, SCREEN_WIDTH 320). VRAM has two plane images, 16 KB
each, at B800:0000 and B800:4000, each laid out as CGA even/odd banks of
80-byte rows. One logical eight-pixel column becomes TWO bytes in each
hardware plane. FlushRetainColumns takes logical byte columns and the stage
already scales them (PCPPATCH: its cursor lease uses shl cx,1/shl dx,1 and
the VRAM offset uses shl ax,1), so this patch passes x>>3 and (right+7)>>3
and never scales again. Nothing here selects planes by port: the PC1512's
port-selected plane scheme does not exist on this card.

The staged TOutput is byte-identical before and after PCPPATCH and to the
PC1512 stage (CPPOUT.FIX), so the same textual edits apply; the symbols
SCREEN_WIDTH/SCREEN_HEIGHT take the ColorPlus values at assembly. This file
carries its own copy of the edits and does not load P15OUT.PY. Every anchor
must match exactly the stated number of times or nothing is written; a stage
that already carries either change is refused rather than patched twice.
"""
import argparse
import importlib.machinery
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RR = importlib.machinery.SourceFileLoader(
    "cppout_rrpatch", str(HERE.parent / "rrect" / "RRPATCH.PY")).load_module()

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 200
SCREEN_W_BYTES = 40
SCAN_MAX = 64            # OS_SCANLINES: count points = 1 Y + count-1 intervals
POLY_MAX = RR.RR_POLY_MAX


def _crlf(s):
    return s.replace("\n", "\r\n")


# (name, old, new); each applies exactly once to the post-candidate stage.
# The two "register contract" entries have old == new on purpose: they only
# prove that the push/pop frame the narrow flush relies on is present.
X_EDITS = (
    ("Output X locals",
     "    localW lastrow\ncBegin\n    mov dirty,0\n    mov outrows,0\n",
     "    localW lastrow\n    localW firstcol\n    localW lastcol\ncBegin\n"
     "    mov dirty,0\n    mov outrows,0\n"),
    ("scan X initialization",
     "    mov cx,count\n    dec cx\nTOutput_scan_interval:\n",
     "    ; Points/mode spans and Y are already validated. For count=2,\n"
     "    ; the exact [0,SCREEN_WIDTH) interval proves both X predicates.\n"
     "    cmp count,2\n    jne TOutput_scan_collect\n"
     "    cmp word ptr es:[di+4],0\n    jne TOutput_scan_collect\n"
     "    cmp word ptr es:[di+6],SCREEN_WIDTH\n    jne TOutput_scan_collect\n"
     "    mov outrows,2\n    jmp TOutput_render\nTOutput_scan_collect:\n"
     "    mov firstcol,SCREEN_WIDTH\n    mov lastcol,0\n    mov cx,count\n"
     "    dec cx\nTOutput_scan_interval:\n"),
    ("scan X bounds",
     "    cmp dx,SCREEN_WIDTH\n    or_require jbe,TOutput_render\n"
     "    loop TOutput_scan_interval\n",
     "    cmp dx,SCREEN_WIDTH\n    or_require jbe,TOutput_render\n"
     "    cmp bx,firstcol\n    jae TOutput_scan_min\n    mov firstcol,bx\n"
     "TOutput_scan_min:\n    cmp dx,lastcol\n    jbe TOutput_scan_max\n"
     "    mov lastcol,dx\nTOutput_scan_max:\n    loop TOutput_scan_interval\n"),
    ("polyline X initialization",
     "    mov cx,count\n    mov ax,7fffh\n    xor bx,bx\nTOutput_poly_point:\n",
     "    mov firstcol,SCREEN_WIDTH\n    mov lastcol,0\n    mov cx,count\n"
     "    mov ax,7fffh\n    xor bx,bx\nTOutput_poly_point:\n"),
    ("polyline X bounds",
     "TOutput_poly_point:\n    mov dx,es:[di]\n    cmp dx,SCREEN_WIDTH\n"
     "    or_require jb,TOutput_render\n",
     "TOutput_poly_point:\n    mov dx,es:[di]\n    cmp dx,SCREEN_WIDTH\n"
     "    or_require jb,TOutput_render\n"
     "    cmp dx,firstcol\n    jae TOutput_poly_xmin\n    mov firstcol,dx\n"
     "TOutput_poly_xmin:\n    inc dx\n    cmp dx,lastcol\n"
     "    jbe TOutput_poly_xmax\n    mov lastcol,dx\nTOutput_poly_xmax:\n"),
    ("two-point X bounds",
     "TOutput_line_ordered:\n    mov firstrow,ax\n",
     "TOutput_line_ordered:\n    cmp cx,dx\n    jbe TOutput_x_ordered\n"
     "    xchg cx,dx\nTOutput_x_ordered:\n    mov firstcol,cx\n    inc dx\n"
     "    mov lastcol,dx\n    mov firstrow,ax\n"),
    ("Output result register contract",
     "    ; Preserve the actual renderer result and all post-render GPRs.\n"
     "    push ax\n    push bx\n",
     "    ; Preserve the actual renderer result and all post-render GPRs.\n"
     "    push ax\n    push bx\n"),
    ("synchronous rows or narrow presentation",
     "    mov ax,firstrow\n    mov bx,lastrow\n    call FlushRetainRows\n"
     "    jmp short TOutput_flushed\n",
     "    mov ax,firstrow\n    mov bx,lastrow\n"
     "    cmp outrows,2\n    je TOutput_rows\n"
     "    cmp firstcol,0\n    jne TOutput_columns\n"
     "    cmp lastcol,SCREEN_WIDTH\n    je TOutput_rows\n"
     "TOutput_columns:\n    push cx\n    push dx\n    mov cx,firstcol\n"
     "    mov dx,lastcol\n    add dx,7\n    shr cx,1\n    shr cx,1\n"
     "    shr cx,1\n    shr dx,1\n    shr dx,1\n    shr dx,1\n"
     "    call FlushRetainColumns\n    pop dx\n    pop cx\n"
     "    jmp short TOutput_flushed\nTOutput_rows:\n"
     "    call FlushRetainRows\n    jmp short TOutput_flushed\n"),
    ("Output return register contract",
     "TOutput_flushed:\n    pop bx\n    pop ax\n",
     "TOutput_flushed:\n    pop bx\n    pop ax\n"),
)


def patch_output(t):
    """Return TSOFT.ASM text with the PR151 gate and narrow presentation."""
    for marker in ("TOutput_marker", "firstcol", "TOutput_two_point"):
        if marker in t:
            raise SystemExit("CPPOUT: stage already carries '%s'" % marker)
    t = RR.patch_candidate(t)
    for name, old, new in X_EDITS:
        t = RR.replace_n(t, _crlf(old), _crlf(new), 1, name)
    if "\n" in t.replace("\r\n", ""):
        raise SystemExit("CPPOUT: refusing bare LF")
    if "call FlushRetainColumns" not in t or "call FlushShadow" not in t:
        raise SystemExit("CPPOUT: presentation or fallback call missing")
    return t


def patch_staged(ega_dir):
    """Edit EGA/TSOFT.ASM in place; return its new text.

    Nothing is written unless every anchor matched exactly as required."""
    p = Path(ega_dir) / "TSOFT.ASM"
    new = patch_output(p.read_bytes().decode("latin-1"))
    p.write_bytes(new.encode("latin-1"))
    return new


# --- host model of the gate's X/Y bounds and the flush rounding -------------

def flush_columns(first_x, last_x_excl):
    """The patched epilogue: eight-pixel logical columns, rounded outward.

    These are the values handed to FlushRetainColumns; the stage doubles
    them to ColorPlus plane bytes itself."""
    return first_x >> 3, (last_x_excl + 7) >> 3


def scan_bounds(y, intervals):
    """OS_SCANLINES: one Y and exclusive-X intervals, all validated.

    The driver call carries count = 1 + len(intervals) points, 2..SCAN_MAX."""
    if not 2 <= 1 + len(intervals) <= SCAN_MAX:
        return None
    if not 0 <= y < SCREEN_HEIGHT:
        return None
    xs0, xs1 = SCREEN_WIDTH, 0
    for left, right in intervals:
        if not (left < right <= SCREEN_WIDTH):
            return None
        xs0, xs1 = min(xs0, left), max(xs1, right)
    return y, y + 1, xs0, xs1


def polyline_bounds(points):
    """OS_POLYLINE, 2..POLY_MAX points, all on the screen."""
    if not 2 <= len(points) <= POLY_MAX:
        return None
    if any(not (0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT)
           for x, y in points):
        return None
    if len(points) == 2 and points[0] == points[1]:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(ys), max(ys) + 1, min(xs), max(xs) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--stage", type=Path,
                    help="staged EGA dir (a copy is patched in memory only)")
    a = ap.parse_args()
    if a.stage:
        text = (a.stage / "TSOFT.ASM").read_bytes().decode("latin-1")
        out = patch_output(text)
        print("CPPOUT: staged TSOFT.ASM accepts the patch (%d -> %d bytes)"
              % (len(text), len(out)))
    else:
        print("CPPOUT: no --stage given; run CPPOTEST.PY for the host tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
