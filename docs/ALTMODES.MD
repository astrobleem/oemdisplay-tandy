# Alternate Tandy graphics modes: bounded experiment

Tested 2026-10-02 against the repository at `f80b3f85e1b655f63331102e435d436946e6213b`.
The distributed `TANDY88.DRV` remains candidate05, 320 x 200 with 16 colors.
No driver, OEM package, installation or shared GUI state was changed by this experiment.

## Answer

**640 x 200 with four colors is a real EX/HX-class hardware mode (BIOS 0Ah).**
It doubles horizontal resolution relative to the current driver, with the same
200 vertical pixels. The four displayed colors are selected from the 16-color
hardware palette. It requires a different Windows rendering backend; there is
no working candidate05 INI switch for it.

The first-generation hardware mode menu is:

| BIOS | Pixels | Colors | Video storage | This experiment |
| --- | --- | --- | --- | --- |
| 04h | 320 x 200 | 4 | 16KB | BIOS writes, reads and raw layout pass |
| 06h | 640 x 200 | 2 | 16KB | BIOS writes, reads and raw layout pass; stock CGA Windows metrics pass |
| 08h | 160 x 200 | 16 | 16KB | BIOS writes, reads and raw layout pass |
| 09h | 320 x 200 | 16 | 32KB | BIOS writes, reads and raw layout pass; existing candidate05 target |
| 0Ah | 640 x 200 | 4 | 32KB | Mode and raw BIOS writes pass; emulator BIOS reads fail |

Do not infer 640 x 200 x 16 support for EX/HX from old repository profiles.
Radio Shack advertised that enhanced mode on later SL/TL-class systems; it is
not in the HX technical manual's hardware mode list. DOSBox-X's `machine=tandy`
BIOS table used here accepts modes through 0Ah and has its 640 x 200 x 16 entry
commented out. This experiment did not test enhanced Tandy Video II hardware.

## Evidence and limits

Full results are in [altmodes/RESULT.JSON](altmodes/RESULT.JSON).
The authored test assembles with MASM `.8086`, and runs separate SDL-dummy boots
using `core=normal`, `cputype=8086_prefetch`, `memsize=0`, `memsizekb=640`, expanded
base memory disabled, and no XMS/EMS/UMB. CPU setting is recorded and accepted by
the emulator. This is the existing DOSBox-X 2026.08.31 SDL2 September 28 nightly;
it is not a cycle-exact 8088 or a physical Tandy test.

For every mode the test:

1. Checks that all live code/data/stack is below segment 9800h, the owned DOS
   block ends at 9C00h, and the BIOS reports 624KB
2. Enters the requested mode and checks BIOS mode/column readback
3. Loads host-generated raw pixels, then reads every coordinate using INT 10h
   AH=0Dh into a separate file
4. Writes every coordinate using INT 10h AH=0Ch, dumps all video bytes and
   compares against an independent host layout, including untouched padding
5. Verifies physical shared-RAM aliasing, unchanged DOS MCB, unchanged BIOS
   memory size and successful return to text mode 03h

Mode 0Ah wrote all 128,000 coordinates correctly: zero mismatches across all
32,768 raw bytes, including 768 padding bytes. It uses this layout:

    base = (y & 3) * 8192 + (y >> 2) * 160 + (x >> 3) * 2
    pixel bit 0 = (VRAM[base]     >> (7 - (x & 7))) & 1
    pixel bit 1 = (VRAM[base + 1] >> (7 - (x & 7))) & 1

This is byte-interleaved two-plane storage, not the ordinary packed-2bpp CGA
layout and not the packed-4bpp layout of mode 09h.

**Emulator caveat:** INT 10h AH=0Dh returned 96,000 wrong pixels out of 128,000
in mode 0Ah. All returned values exactly match the wrong 16KB CGA read formula.
DOSBox-X's official `INT10_GetPixel` source uses that formula unconditionally
for `M_CGA4`; its `INT10_PutPixel` correctly contains the 32KB special case.
Therefore this is a demonstrated emulator BIOS readback defect, not evidence
that genuine Tandy hardware lacks four-color high resolution. It also does
not establish a Windows GetPixel defect: a shadow-backed Windows driver would
normally read its own bitmap. No external issue was filed or emulator patched.

The suite deliberately reports `PARTIAL: mode0A BIOS readback bug` and exits 2
when the defect is reproduced. Modes 04h/06h/08h/09h had zero read and write
mismatches. A failed read is not waived into an overall PASS.

The headless suite's `DECODED.PNG` files are **raw-VRAM previews with stated
illustrative colors**, not native emulator screenshots. They are separate from
the later native captures below. No four-color Windows desktop, GDI, fonts,
cursor or BMP save/reopen claim is made.

## Native screenshots

After the bounded tests, a separate screenshot pass captured the running
emulator through DOSBox-X's native raw-PNG action (F12 + Ctrl + P). No capture
was resized, cropped or recolored. The exact files, hashes, color counts and
CPU/mode metadata are in [CAPTURES.JSON](altmodes/CAPTURES.JSON).

| Screen | Logical resolution | Native PNG | Visible colors | Scope |
| --- | --- | --- | --- | --- |
| [Stock CGA Windows](altmodes/CGAWIN.PNG) | 640 x 200 | 640 x 400 | 2 | Windows 3.0 Program Manager, Microsoft CGA driver |
| [High-resolution four-color test](altmodes/MODE0A.PNG) | 640 x 200 | 640 x 400 | 4 | DOS-only BIOS 0Ah |
| [Medium-resolution four-color test](altmodes/MODE04.PNG) | 320 x 200 | 320 x 200 | 4 | DOS-only BIOS 04h |
| [Low-resolution sixteen-color test](altmodes/MODE08.PNG) | 160 x 200 | 320 x 200 | 16 | DOS-only BIOS 08h |

DOSBox-X duplicated every adjacent pair of rows in the two 640-pixel captures,
and every adjacent pair of columns in the 160-pixel capture. This was verified
pixel-for-pixel; capture dimensions do not change the logical BIOS mode.
The existing [candidate05 Paintbrush capture](tandy-dib-roundtrip.png) supplies
the implemented 320 x 200 x 16 Windows view at its native 320 x 200 dimensions.

DOS screens show a BIOS-rendered mode/resolution label, color bars, a one-pixel
diagonal pattern and a checker pattern. The 0Ah capture uses the
BIOS default black/blue/green/cyan palette. Its earlier BIOS pixel-read defect
still applies; a screenshot is not evidence that the read function is fixed.
The stock-CGA GUI session reran the live metrics probe before its final capture:
[CGA-GUI.LOG](altmodes/CGA-GUI.LOG). All capture guests were isolated copies and
exited cleanly, leaving the installer and current driver unchanged.

## Stock CGA Windows control

A disposable copy of the existing user-supplied Windows 3.0 CGA installation
booted headlessly with the same enforced CPU and normal-memory profile. The
existing authored `PROBE.EXE` was used as the temporary shell and Windows
returned to DOS cleanly. [CGAWIN.LOG](altmodes/CGAWIN.LOG) records:

    SM_CXSCREEN=640  SM_CYSCREEN=200
    HORZRES=640      VERTRES=200
    BITSPIXEL=1      PLANES=1      NUMCOLORS=2
    BIOS_MODE_DECIMAL=6           COMPLETE=1

The guest retained `display.drv=cga.drv`, `fonts.fon=cgasys.fon`,
`fixedfon.fon=cgafix.fon` and `oemfonts.fon=cgaoem.fon`. It used `WIN /R`.
This verifies mode/metrics and clean exit, not a new interactive regression
suite. Windows media and installed Windows files are not included in evidence.

## Actual port scope

The old `src/ENABLE.C` has a mode-selection sketch marked `future`, incomplete
exports and a comment saying its shadow flush still needs implementation.
`src/tandy16/TGAVID.ASM` also contains placeholder plane offsets. Neither is the
candidate05 renderer. Merely selecting their mode or changing AX=9 to AX=0Ah
would give incorrect display memory and GDI behavior.

A genuine separate four-color Windows driver requires coordinated changes in
at least these six areas:

1. `V1.ASM`: width/stride, shadow and physical BITMAP descriptors, GDIINFO,
   advertised colors/planes, BIOS selection, color tables and `FlushShadow`
2. `TCURSOR.ASM`: 640-pixel clipping plus two-plane byte addressing and
   save/restore/AND/XOR operations; the current cursor edits packed nibbles
3. DDK color and bitmap engine: `DISPLAY.INC` fixes `NUMBER_PLANES=4`;
   `COLORS`, `COLORINF`, `ROBJECT`, `CBLT`, text and scan operations use that
   representation. Existing conditional paths generally distinguish three
   from four planes; changing the constant to two is not a supported port
4. DIB roundtrip: `SDIB88.ASM` clips at x=320; `PORTDIB.PY` injects 16-color
   palette data; `BMC_ETI`/`BMC_ITE` and bitmap realization must agree with the
   new palette and device representation
5. Resources/fonts: separate `TSOFT.DEF`, metrics/color resources and suitable
   low-resolution 80-column fonts, then actual GDI text measurement checks
6. Build, launcher and reservation validation: a separately named binary,
   pinned staged-source audits and its own hashes/configuration. The 32KB
   hardware span matches 09h, but the reservation helper must still be tested
   with the new mode and Windows lifecycle

A retained four-plane logical shadow would grow from 32,000 to 64,000 bytes at
640 pixels and require consistent color quantization/readback and segment-size
review. It must not advertise 16 real display colors or quietly truncate them.
A true two-plane 32,000-byte shadow avoids that growth but needs the broader
DDK engine conversion above. Neither route is a small configuration experiment.

Before publishing support, rerun the 8088 instruction/generated-code audit,
full-frame tests, palette/Pixel/GetPixel, clipped and overlapping ROPs,
text/font metrics, all cursor edges, paint/save/reopen and Windows exit/restart.
**No renderer rewrite or experimental Windows driver binary was started.**

## Reproduce

Python 3, Pillow and the existing repository MASM/LINK tools are required.
No Windows installation or additional OS media is needed for the mode test.
Choose a new output directory:

    python3 src/tandysw/TESTMODE.PY --dosbox /path/to/dosbox-x --out /new/mode-tests

Expect exit 2 on the tested DOSBox-X build because of the recorded 0Ah read bug.
Keep `RESULT.JSON`, `MODETEST.ASM`, `MODETEST.LST`, `MODETEST.EXE`, per-mode
`RUN.CONF`, `CPU.TXT`, `HOST.LOG`, `META.BIN`, `INPUT.BIN`, `READS.BIN`,
`WRITE.BIN` and `DECODED.PNG` together. `RESULT.TXT=PASS` in a guest folder means
the guest completed safely; the host JSON contains the actual pixel verdict.

Standalone probe EXE SHA256:
`7ae387e67bb862445d57cb5de9f5987b3d541b625236326b3fe322872d208d6b`

Unchanged candidate05 driver SHA256:
`ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee`

## Primary sources

- [Tandy 1000 HX Technical Reference Manual, Graphics Mode and 4 Color High Resolution sections](https://manualzz.com/doc/57483083/tandy-1000-hx-technical-reference-manual)
- [Radio Shack RSC-20 Computer Catalog (1989), Tandy 1000 SL graphics specifications](https://colorcomputerarchive.com/coco/Documents/Catalogs/Radio%20Shack/RSC-20%20Computer%20Catalog%20%281989%29%28Radio%20Shack%29.pdf)
- [DOSBox-X BIOS mode table and mode validation](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/int10_modes.cpp)
- [DOSBox-X BIOS pixel write/read implementation](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/int10_put_pixel.cpp)

Manual and catalog mirrors host the original vendor documents. The live source
links describe code reviewed on 2026-10-02; emulator runtime results above are
independent evidence for the locally tested build.
