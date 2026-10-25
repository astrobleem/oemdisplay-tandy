# PC1512 Output optimisation (host-tested, not native-qualified)

Source and host tests only. No PC1512.DRV was built or run for this change,
no accepted pin or package is touched, and nothing here measures PC1512
speed. Tandy measurements do not transfer to the four-plane adapter.

## What changes

`src/pc1512/BUILD15.PY` now calls `P15OUT.patch_staged_output` once, right
after `P15.patch_staged` and before the first assembly, so BUILD88's
instruction, REP-prefix and link audits run on the result. It edits only the
`TOutput` gate of the staged `EGA/TSOFT.ASM`:

1. `src/rrect/RRPATCH.patch_candidate` (PR151), reused unchanged:
   `OS_BEGINNSCAN`/`OS_ENDNSCAN` skip the copy and cursor work; polylines of
   3..1024 points are bounded to their rows.
2. The synchronous X half of `experiments/XYRRECT/XRBATCH.PY` (PR155
   follow-up): the gate also collects the validated X extent, rounds it
   outward to eight-pixel columns (`first>>3`, `(last+7)>>3`) and presents
   through the stage's existing `FlushRetainColumns`, preserving AX..DX.

On PC1512 one logical column is one byte in each of the four planes (80-byte
plane rows), and P15PATCH already removed the Tandy doubling, so no scaling
is added. XR1's viewport, packed-pixel, dual-band and XY cursor edits are not
used; the stage's own cursor retention is untouched. Every Output call still
presents before returning (no pending rows, no marker-owned state). Calls the
gate rejects keep the existing `FlushShadow` fallback.

Each anchor must match the stated number of times or nothing is written; a
stage that already has either change is refused, so nothing applies twice.

## Host results

    python3 src/pc1512/P15PATCH.PY --check           PASS (unchanged model)
    python3 -B src/pc1512/P15OTEST.PY              27 tests OK
    python3 src/pc1512/P15OUT.PY --check --stage <staged EGA dir>

`P15OUT.FIX` is `TOutput` from the real post-P15PATCH stage (main 316f21b,
BUILD88 view, no emulator); the tests assert it is patchable, every anchor
matches once and refuses when missing/duplicated, the validation order, the
unchanged fallback, register preservation and no XR1/Tandy-only text. A
plane-aware model (P15PATCH's flush/decoder) checks that the rounded region
equals a full flush for random polylines and scanlines, including x=0, x=639
and 632..640, with negative controls that fail when rounding is dropped.
The model is not the assembled code: it does not prove the driver runs.

## Native handoff (dot)

Changed build inputs: `src/pc1512/BUILD15.PY` (one import, one call, one
docstring line), new `src/pc1512/P15OUT.PY`. `P15OUT.FIX`, `P15OTEST.PY`
and this note are host-only. P15RES.JSON's `staged_patched_sha256` for
TSOFT.ASM will change; BUILD88, RRPATCH, XRBATCH and the other adapters are
unchanged. PC1512.DRV bytes will differ from any currently pinned build.

Expected `P15RES.JSON` `staged_patched_sha256` (host dry run of the real
BUILD15 on a BUILD88 view of main 316f21b, stopped before any emulator
launch; compare to confirm the native build assembled the reviewed text):

    TSOFT.ASM   09736072f813770b3d2d24625d326be85bd7a43203e05c97ce0eb9616ad70def
    TCURSOR.ASM 4ded456320df4280c8bd8f074bbe5143325d8099dd3323a44f70d9e3f1beb775

(TSOFT.ASM without this change: 30b2c183...ab0; TCURSOR.ASM is unchanged.)
Versus the pre-change stage only EGA/TSOFT.ASM differs (TSOFT.DEF differs
only in the existing BUILD15 description swap).

Acceptance, on the same inputs with and without this change:

1. Build via BUILD15; BUILD88 audits and the link audit pass.
2. Calculator and Reversi redraw correctly; no stale rows or edge columns,
   including objects touching column 0 and the right edge.
3. Plane-aware output identical to the unpatched driver: compare the four
   hardware planes (3DEh read select 0..3, rows interleaved at +0000h/+2000h,
   80 bytes per row), not one flat buffer.
4. Drawing is visible immediately after each Output call returns (no wait
   for an END marker or next call).
5. Cursor moves over and is restored after drawing; 3DDh=0Fh and 3DEh=0
   afterwards.
6. Only then, matched timing, never a figure borrowed from Tandy.

Capture adaptation: `src/rrect/RRBENCH.C` dumps the flat B800h 32 KB
(`0xb8000000`, 0x8000 bytes). PC1512 has four 16 KB planes behind that
window, selected by 3DEh for reads, so that dump sees one plane at most and
is not valid evidence. The idle/visibility probes (RRBENCH.C reading
`[at] & 15` at B800h) also assume packed 4-bit pixels; on PC1512 that byte is
eight pixels of the plane 3DEh selects, so "immediate visibility" needs its
own plane-aware probe. The capture needs a capture that reads each plane through
3DEh (restoring 3DEh=0) and writes 64,000 bytes, and RRCMP's frame size
expectations adapted to match. Not done here.

Reuse and watch-points: Output now calls `FlushRetainColumns`, which the
stage already runs from TBitBlt (its copy loop is the `p15_row` version).
TBitBlt keeps a `FlushRetainRows` fast path for full-width spans; this patch
always uses Columns, as XRBATCH does, so check full-width fills first if
timing disappoints.

Overlap: PR #183 edits `docs/PC1512.MD` and the PC1512 package; this branch
touches neither. Follow with a pointer in PC1512.MD after #183 merges.
