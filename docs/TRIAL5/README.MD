# Trial 5: bounded multi-interval scanline refresh

Base source: astrobleem/oemdisplay-tandy commit
36e1b35b596585cc0dacabe9754e680744e2dd67.

## What changed

A private Windows 3.0 trace established that the stock Clock's two-pixel
rectangle border becomes one OS_SCANLINES Output call per row, with two
separate left/right edge intervals (count=3). Trial 4's row gate accepted
only count=2, so these calls refreshed the entire display for each row.

WIDESCAN.PY extends that gate to count=2..64 for OS_SCANLINES only. It
validates the complete 4*count far pointer span and every nonempty exclusive
X interval, plus the shared Y. The existing ROP2, background, pen/solid-brush
and alias checks still apply. Unsupported or uncertain cases use the exact
original synchronous full refresh. Thin polylines remain count=2 only.

The renderer still draws every original interval in its original order.
No rectangle is replaced with four fills. GDI retains responsibility for
wide-pen shapes, joins, odd/even widths, clipping and coordinate transforms.
Overlapping intervals and all ROP2 semantics are unchanged. This is a copy
bounds optimization, not a rasterization rewrite.

There is no deferred drawing, timer hook, marker suppression, extra cursor
state, interrupt masking or new memory buffer. The maximum validation loop
is 63 intervals. Existing marker80/81 full refresh, identity SRCCOPY full
resynchronization, 8088-safe copies, bounded cursor maintenance, row/column
conversion and reservation protections remain intact. Only EGA/TSOFT.ASM
changes in the staged driver sources; the five driver files grow 32 bytes.

## Reproduce

Apply this delta to the pinned base checkout, retaining the user's existing
authorized DDK, compiler and linker inputs. No OS, font, ROM, DDK or compiler
payload is supplied by this source delta.

    python3 src/tandysw/TST5SRC.PY
    python3 src/tandysw/TSTREP88.PY
    python3 src/tandysw/BUILD88.PY --dosbox <dosbox-x> --out <fresh-dir> --mode <profile>

Profiles: 160x200x16, 320x200x16, 320x200x4, 640x200x4, 640x200x2.
Compare driver SHA256 and size with BUILDS.JSN and inspect RESULT.json.
The new files use the separate TR5 runtime aliases listed in that manifest.
Do not replace historical accepted payloads or relax MAKEDISK pins.

For a separate exact Trial 4 comparison build, BLDTR4.PY is an unchanged
copy of the base BUILD88.PY in the same src/tandysw directory:

    python3 src/tandysw/BLDTR4.PY --dosbox <dosbox-x> --out <fresh-baseline> --mode <profile>

TST5SRC stages all five exact baseline pipelines, applies the narrow delta,
checks inverse scope and rejection of repeated/altered inputs. It does not
execute the renderer. The original TSTCHAIN source-manifest check expects
the old BUILD88 bytes, so use the new TST5SRC for this delta.

The actual staged validation gate can be executed under the 8088-compatible
DOSBox-X core using the 160-mode build:

    python3 src/tandysw/TSTWIDE.PY --build <160-build> --repo <checkout> --dosbox <dosbox-x> --out <fresh-test>

This runs 62 cases including count limits, ROP2 values, X/Y boundaries,
null/wrapping/aliased pointers, ignored scanline clip input and full register,
segment, flags and SP preservation. It tests the gate, not the whole renderer
or the Windows API. See VERIFY.TXT for completed runtime coverage.

## Limits

No physical Tandy timing or acceptance is claimed for these exact new bytes.
DOSBox-X cycle settings are uncalibrated host/emulator settings. Its 640x200
four-color model remains uncertain. Preserve the historically tried Trial 3
monochrome fallback separately; the new Trial 5 mono file is not that file.

The scalar pointer checks assume the caller supplies valid live stable
allocations, as the existing gate does. They do not prove allocation ownership.
