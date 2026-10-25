#!/usr/bin/env python3
"""PC1512 Output optimisations: marker skip, bounded polylines, narrow flush.

Usage:
  python3 src/pc1512/P15OUT.PY --check [--stage <staged EGA dir>]

Adapts two proven Tandy changes to the staged PC1512 EGA/TSOFT.ASM, after
P15PATCH.patch_staged and before the first assembly (BUILD15.PY):

1. src/rrect/RRPATCH.patch_candidate (PR151), applied unchanged: GDI's
   OS_BEGINNSCAN/OS_ENDNSCAN markers skip the copy and the cursor work, and
   3..1024-point polylines are bounded to the rows between their points.
2. The synchronous X half of experiments/XYRRECT/XRBATCH.PY (PR155
   follow-up): TOutput also collects the validated X extent, rounds it
   outward to eight-pixel logical byte columns and presents through the
   stage's existing FlushRetainColumns. Every Output call still presents
   before it returns; there is no pending state and no marker-owned state.

PC1512 specifics: a logical byte column is one byte in each of the four
planes (80 bytes per plane row), so FlushRetainColumns needs no further
scaling (P15PATCH already removed the Tandy doubling). None of XR1's
viewport, packed-pixel or dual-band edits are used, and the cursor
implementation is the stage's own. Cases the gate rejects keep the
existing fallback (FlushShadow). Every anchor must match exactly the stated
number of times or nothing is written; a stage that already carries either
change is refused rather than patched twice.
"""
import argparse
import importlib.machinery
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RR = importlib.machinery.SourceFileLoader(
    "p15out_rrpatch", str(HERE.parent / "rrect" / "RRPATCH.PY")).load_module()

SCREEN_W_BYTES = 80
SCREEN_WIDTH = 640


def _crlf(s):
    return s.replace("\n", "\r\n")


# (name, old, new); each applies exactly once to the post-candidate stage.
X_EDITS = (
    ("Output X locals",
     "    localW lastrow\ncBegin\n    mov dirty,0\n    mov outrows,0\n",
     "    localW lastrow\n    localW firstcol\n    localW lastcol\ncBegin\n"
     "    mov dirty,0\n    mov outrows,0\n"),
    ("scan X initialization",
     "    mov cx,count\n    dec cx\nTOutput_scan_interval:\n",
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
    ("Output preserve X registers",
     "    ; Preserve the actual renderer result and all post-render GPRs.\n"
     "    push ax\n    push bx\n",
     "    ; Preserve the actual renderer result and all post-render GPRs.\n"
     "    push ax\n    push bx\n    push cx\n    push dx\n"),
    ("synchronous narrow presentation",
     "    mov ax,firstrow\n    mov bx,lastrow\n    call FlushRetainRows\n"
     "    jmp short TOutput_flushed\n",
     "    mov ax,firstrow\n    mov bx,lastrow\n    mov cx,firstcol\n"
     "    mov dx,lastcol\n    add dx,7\n    shr cx,1\n    shr cx,1\n"
     "    shr cx,1\n    shr dx,1\n    shr dx,1\n    shr dx,1\n"
     "    call FlushRetainColumns\n    jmp short TOutput_flushed\n"),
    ("Output restore X registers",
     "TOutput_flushed:\n    pop bx\n    pop ax\n",
     "TOutput_flushed:\n    pop dx\n    pop cx\n    pop bx\n    pop ax\n"),
)


def patch_output(t):
    """Return TSOFT.ASM text with the PR151 gate and narrow presentation."""
    for marker in ("TOutput_marker", "firstcol", "TOutput_two_point"):
        if marker in t:
            raise SystemExit("P15OUT: stage already carries '%s'" % marker)
    t = RR.patch_candidate(t)
    for name, old, new in X_EDITS:
        t = RR.replace_n(t, _crlf(old), _crlf(new), 1, name)
    if "\n" in t.replace("\r\n", ""):
        raise SystemExit("P15OUT: refusing bare LF")
    if "call FlushRetainColumns" not in t or "call FlushShadow" not in t:
        raise SystemExit("P15OUT: presentation or fallback call missing")
    return t


def patch_staged_output(ega_dir):
    """Edit EGA/TSOFT.ASM in place; return its new text."""
    p = Path(ega_dir) / "TSOFT.ASM"
    new = patch_output(p.read_bytes().decode("latin-1"))
    p.write_bytes(new.encode("latin-1"))
    return new


# --- host model of the gate's X/Y bounds and the flush rounding -------------

def flush_columns(first_x, last_x_excl):
    """The patched epilogue: eight-pixel columns, rounded outward."""
    return first_x >> 3, (last_x_excl + 7) >> 3


def scan_bounds(y, intervals):
    """OS_SCANLINES: one Y and exclusive-X intervals, all validated."""
    if not 0 <= y < 200:
        return None
    xs0, xs1 = 640, 0
    for left, right in intervals:
        if not (left < right <= 640):
            return None
        xs0, xs1 = min(xs0, left), max(xs1, right)
    return y, y + 1, xs0, xs1


def polyline_bounds(points):
    """OS_POLYLINE, 2..1024 points, all on the screen."""
    if not 2 <= len(points) <= 1024:
        return None
    if any(not (0 <= x < 640 and 0 <= y < 200) for x, y in points):
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
        print("P15OUT: staged TSOFT.ASM accepts the patch (%d -> %d bytes)"
              % (len(text), len(out)))
    else:
        print("P15OUT: no --stage given; run P15OUTTEST.PY for the host tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
