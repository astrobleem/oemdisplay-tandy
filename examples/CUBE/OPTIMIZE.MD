# Cube symmetry candidate

This unqualified source candidate follows the accepted cube at
`832daf29599c5a0a392a3f8135fa40206ae550af`. The accepted BIN files,
ACCEPT.JSN, native receipts and download packages retain their original bytes.
Historical TESTS.MD qualifies those accepted bytes, not this source delta.

CUBECORE.C still uses Q8 integer math, 16-bit int / 32-bit long conventions,
the 130-byte sine table, and four rotation products. Opposite corners share
scaled magnitudes, and opposite faces share signed lighting. Coordinate
scaling now uses six long multiply/divide expressions per frame instead of
16 (two x, four y). Lighting evaluates three dot products instead of six;
three signed /256 divisions and three /20 shade divisions replace six each.
These are source operation counts, not measured 8088 instruction counts.
Signed division order and ambient/clamping quantization are preserved.

No persistent data, allocation or initialization pass was added. Resize,
center changes, arbitrary phase skips and saver restarts recompute immediately.
The existing GDI bitmap, fill/dither/wire drawing and copy path are unchanged.
A full phase cache would add 28 KiB for the existing 16-bit projected geometry and
face state, would depend on scale (and projected coordinates on center), and
would need generated static data or startup/rebuild work. That is deferred in
favor of this smaller change for normal 640 KB real-mode Windows. Neither
approach removes GDI rendering cost. The existing 0.77s filled / 0.41s wire
second-frame medians suggest drawing remains material; those are historical
emulator observations, not a profile of this candidate or physical hardware.

## Numerical and visual-input equivalence

TESTCORE.C contains the frozen original frame algorithm and compares every
point coordinate, visibility flag and shade against it. All 512 phases and
every integer x scale 0..168 and y scale 0..96 pass (136,192 cases). The axes
are independent, so each is exhaustively varied with the other held at its
maximum. Positive/negative centers near the 16-bit limit are covered. Another
65,536 cases cover every native unsigned phase, plus a tiny resize case.
Existing winding, periodicity, lighting and canvas/copy-bound checks pass.
Identical geometry/lighting inputs to the unchanged renderer establish
numerical equivalence; a new native screenshot/scanout check remains pending.
The host uses wider int/long than MSC6. Tested coordinate intermediates fit
16-bit int, and all long products fit 32-bit long; sanitizer success alone is
not a substitute for native compilation.

The baseline and candidate RUNHOST.PY suites both pass all five groups:
geometry, 163 configuration checks, idle, Hold, and lifecycle. The candidate
geometry also passes GCC undefined-behavior sanitization with recovery disabled.
Receipts and the seven alternating benchmark samples are in EVIDENCE/OPT01.
CRLF is preserved; `git -c core.whitespace=cr-at-eol diff --check` passes.

## Performance evidence and reproduction

The GCC 14.2.0 -O2 modern-host microbenchmark runs two million calls per sample,
seven samples per version, alternating which runs first. It varies all phases,
consumes output through a volatile checksum and compiles the two algorithms in
separate translation units without LTO. Median CPU time was 0.084154 seconds
for baseline and 0.047712 for symmetry, about 43.3% less host CPU time.
This isolates geometry only; it does not measure Windows, GDI, target code size,
8088 cycles, native frame rate, or input responsiveness.

Run from the repository root into fresh output directories:

```text
python -B examples/CUBE/SOURCE/RUNHOST.PY --out NEW-HOST
python -B examples/CUBE/SOURCE/BENCH.PY --out NEW-BENCH
```

BENCH.PY reads the immutable original CUBECORE.C from local git history and
verifies its SHA-256 before building. No network or emulator is used.

## Remaining native qualification

Native build, 8088 ISA audit, screenshot/readback comparison, Windows timing,
and memory observations are pending. This environment has no MSC6/DDK inputs,
DOSBox-X or 86Box, and no coordinated shared emulator slot was acquired.
The action is pending due to missing tooling/coordination, not denied; no
emulator was launched or stopped and BOR's resources were not touched.
An approved separate native slot must measure geometry and total draw times
against the frozen baseline before claiming target speedup. Qualify changed
runtime bytes and update all affected acceptance/build/packet pins together;
existing strict package gates must continue rejecting stale native receipts.
Nothing was committed, pushed, published or merged by this work.
