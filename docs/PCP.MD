# Plantronics ColorPlus 320x200x16 driver (PCP3216): first build

Status: **PCP3216.DRV builds through the pinned BUILD88 pipeline, its audits
pass, and its pixel-conversion code has executed correctly under DOSBox-X's
8086 core. It has not run under Windows and has not touched a real or
emulated ColorPlus card.** Nothing shipped changes.

## Target hardware

Plantronics ColorPlus and its clones: ATI Graphics Solution / Small Wonder,
Paradise EGA 480 in CGA mode (Amstrad PC1640), Yamaha V6355-based cards,
Twinhead CT-6190G, VTech VTCL 27-0739-01 cards, some Tandy add-in cards.
These are ordinary 8-bit CGA-class cards, so this driver is for **any XT**
with one, not only Tandys. [WINPCP](https://github.com/cluehawk/WINPCP)
targets the same cards' 640x200x4 mode; this targets 320x200x16, so the two
do not overlap.

## Hardware model

From 86Box `vid_cga_colorplus.c`, the seasip.info ColorPlus notes and the
WINPCP notes, which agree:

- INT 10h mode 04h, then port 3DDh = 10h. Port 3DDh = 0 before leaving.
- 32KB on the card at B800h. Plane 0 at offset 0000h, plane 1 at 4000h.
- Each plane is CGA 2bpp: even rows at +0000h, odd rows at +2000h,
  80 bytes per row, leftmost pixel in bits 7-6.
- Plane 0 field = (R << 1) | G; plane 1 field = (B << 1) | I. The 16 colors
  are fixed IRGB, the same order the TR5 driver already uses.

## How the driver changes

The TR5 renderer draws everything into a private four-plane shadow (DDK
order red, green, blue, intensity) and only converts to video memory when
flushing. So one shadow byte column (8 pixels) becomes two bytes in each
Plantronics plane:

    plane 0 word = spread(R) << 1 | spread(G)
    plane 1 word = spread(B) << 1 | spread(I)

`spread()` moves bit k to bit 2k, done with a 512-byte lookup table in the
code segment. That replaces the Tandy nibble packing.

`PCPPATCH.PY` applies these edits to BUILD88's fully staged sources, each
with an exact match count:

| Area | Change |
| --- | --- |
| Four flush routines | CGA two-bank row address (80-byte rows) instead of Tandy four-bank (160); 2 bytes per column instead of 4; `pp_byte` replaces the nibble loop |
| Cursor retention | physical columns are one 80-byte plane row (was 160); column scale x2 (was x4) |
| `TEnable` / `TDisable` | mode 04h + 3DDh = 10h; 3DDh = 0 before restoring the old mode |
| `TCURSOR` | CGA row math; save/restore both planes (buffer 544 -> 576 bytes); per-pixel AND/XOR applied to the 2-bit field in both planes |

The cursor needs no color decoding. Its AND mask forces color 0, and its XOR
mask flips all four color bits. Both are bitwise, and every color bit lives
in exactly one plane field. So clearing or flipping the pixel's two-bit field
in both planes gives exactly the same result as on the Tandy.

No memory reservation is needed. The video RAM is on the card, so there is
no RESERVE or JRGUARD step.

## Evidence

**Build.** `BUILDPCP.PY` runs the view's unchanged BUILD88 for 320x200x16
and applies the edits between staging and the first assembly. BUILD88's
instruction, REP-prefix and link audits run on the patched listings and pass.

    PCP3216.DRV  54,832 bytes
    SHA256 67f8a3d77574f8f78d2751f68b9c303fc59fcacd93325b9aa4aaf10288c7c406

Two builds gave the same hash. Same toolchain and emulator as the PCjr build
(DOSBox-X 2024.03.01 package, MASM 5.10/LINK from the pinned inputs); that
pipeline reproduces the accepted TR5 320x200x16 hash exactly. Reports:
`pcp/PCPRES.JSN`, `pcp/PCPBUILD.JSN`.

**Conversion code executed.** `PCPTEST.PY` generates a DOS program from the
*same text* the driver build inserts (macros, table and row-address block),
assembles it with the pinned MASM 5.10 and LINK inside DOSBox-X (8086
prefetch core), and converts a seeded random full-frame shadow plus edge
patterns into a RAM buffer. DOSBox-X has no ColorPlus card, so the output
goes to RAM, not B800h.

| Check | Result |
| --- | --- |
| 32,768 output bytes vs host model | 0 mismatches |
| 64,000 pixels decoded with 86Box's ColorPlus rules vs the colors the TR5 Tandy flush shows | 0 mismatches |
| Mutation: planes 0 and 1 swapped in `pp_byte` | FAIL as expected: 14,996 bytes, 32,140 pixels |

Reports: `pcp/PCPTEST.JSN`, `pcp/MUTANT.JSN`.

**Not yet tested:** the cursor paths, the column and retained-cursor flushes
at runtime, mode switching, and everything under Windows.

## Next steps

1. **On-screen check before Windows.** `python3 src/pcp/PCPTEST.PY --show
   ...` builds `PCPSHOW.EXE`: mode 04h, 3DDh = 10h, then the same conversion
   draws 16 vertical bars in color order 0-15 (black, blue, green, cyan, red,
   magenta, brown, light gray, dark gray, then the bright versions). Run it
   with `SHADOW.BIN` beside it on a ColorPlus-class card or 86Box with the
   ColorPlus video card; any key returns to text. A photo settles plane and
   bit order on real hardware.
2. **Windows 3.0 real mode** in 86Box (8088 XT machine, Plantronics ColorPlus
   card, owned Windows media) with `display.drv=PCP3216.DRV`: desktop, cursor
   edges, Paintbrush, Solitaire, exit to DOS, restart.
3. **Setup integration** under its own 8.3 names, with no change to the
   Tandy disk's existing choices. The Tandy launcher and RESERVE do not
   apply. Plain `WIN /R`.
4. **640x200x4 later**, possibly with the WINPCP author: same two-plane
   layout at 1bpp.

## Sources

- [86Box `src/video/vid_cga_colorplus.c`](https://github.com/86Box/86Box/blob/master/src/video/vid_cga_colorplus.c)
- [Plantronics ColorPlus notes (seasip.info)](https://www.seasip.info/VintagePC/plantronics.html)
- [WINPCP repository and hardware notes](https://github.com/cluehawk/WINPCP)
