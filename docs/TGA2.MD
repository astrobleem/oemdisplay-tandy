# Tandy Graphics II / ETGA 640x200x16: groundwork

Status: **mapping probe and plan only. No driver, no shipped change.** The
README's "in development" line for SL/TL/RL stays accurate. EX/HX BIOS 0Ah
remains four colors and is unaffected ([ALTMODES.MD](ALTMODES.MD)).

## What is known, and how well

Radio Shack advertised a 640x200 16-color mode for later SL/TL-class
machines; the RL ships with Video II. No Tandy technical reference for those
models was found in this session, so the programming model below comes from
two independent emulator sources that agree with each other:

| Item | 86Box `vid_tandy.c` (SL2, implemented) | DOSBox-X `int10_modes.cpp` (entry commented out) |
| --- | --- | --- |
| Enable | video array register 5 bit 0 | not modeled |
| CPU window | A0000h, 64KB (32KB B8000h window otherwise) | A0000h, 64KB page |
| Rows | one scan line per CRTC row (8-bit row counter on SL2 only) | 200 rows, vertical total 256 |
| Row stride | 80 CRTC characters x 4 bytes = 320 bytes, linear | 80 columns |
| Pixels | packed 4bpp, high nibble first, palette via array regs 10h-1Fh | `M_TANDY16` |
| Physical RAM | 64KB half of the 128KB video area, chosen by 3DFh bit 2 | - |

So the working hypothesis is a **linear, unbanked 64,000-byte framebuffer at
A000:0000** - different from every EX/HX mode. It is consistent with 86Box
widening the CRTC row counter to 8 bits only for the SL2 (200 one-line rows
do not fit in 7 bits). It is still a hypothesis until a real SL/TL/RL or an
86Box SL2 run with owner-supplied BIOS ROMs confirms it.

The decisive unknown is **where those 64KB physically live**. On EX/HX the
32KB mode 09h page sits at the top of 640KB and needs a 16KB reservation.
If Video II's 64KB page is also carved from the top of conventional memory,
a Windows driver needs a much larger protected region than RESERVE handles.

## T2PROBE (src/tga2)

`T2PROBE.ASM` answers the physical-location question without writing through
an unknown window:

1. Shrinks itself, allocates the largest free DOS block, and stamps every
   paragraph of that block with its own segment and a tag.
2. Only on a machine with the Tandy signature (F000:FFFE = FFh and
   FC00:0000 = 21h): sets BIOS mode 09h, then applies the hypothesis: array
   register 5 = 1 (index to 3DAh, data to 3DEh) and CRTC R4=FFh, R5=06h,
   R6=C8h, R7=E0h, R9=00h, keeping the horizontal timing from mode 09h.
   Anything else gets a report and no register writes.
3. Scans A000:0000-FFFF read-only for the tags. Each tag found names the
   physical paragraph behind that window offset.
4. Writes a linear 640x200x16 pattern and dumps the window (`T2VRAM.BIN`)
   **only if all 4,096 window paragraphs were found by tag, with one constant
   offset, so the entire 64KB window is proven to be the probe's own block.**
   A partial, inconsistent or out-of-block mapping writes nothing. `/W`
   holds the pattern on screen for a photo.
5. Clears register 5, restores the BIOS mode and frees its block.
   Exit 0 = pattern written and dumped, 2 = report only, 1 = setup failure.

Review fix (2026-10-10): the first version also accepted window paragraphs
it had not found by tag, as long as the computed address fell above the DOS
arena, so it could write 64KB after verifying only part of the mapping. That
allowance is gone. If the window turns out to live above the arena (likely,
by analogy with EX/HX), the probe reports the mapping and writes nothing;
a write test there needs a separate, explicitly reserved design.

`T2CHECK.PY` verifies a dump byte-for-byte and can render an illustrative
decode. It exits 0 only for a verified pattern whose report proves the
mapping safe (`SAFE_TO_WRITE=01`, `PATTERN_RAN=01`, `MAPPED_PARAS=1000`,
`MAP_INCONSISTENT=00`); a correct-looking image under any other report is a
FAIL. It exits 2 ("not tested") when there is no dump, and with
`--expect-unmapped` it checks a negative control. `src/pcjr/CHKTEST.PY`
covers these cases on the host.
`T2PROBE.TXT` also records INT 15h C0h model/submodel/revision and a read of
port 65h, to find a reliable SL/TL/RL detection signature later.

**Negative controls only so far** (EX/HX-class emulation, which has no Video
II): DOSBox-X and DOSBox `machine=tandy` both report zero mapped paragraphs,
`SAFE_TO_WRITE=00`, no pattern write and exit 2; `T2CHECK --expect-unmapped`
passes on both (`tga2/*T2CHK.JSN`). INT 15h C0h returned model FFh, submodel
0Ah, revision 10h on both. Built with the pinned MASM 5.10 / LINK / EXE2BIN
(`src/pcjr/BUILDCOM.PY`), `T2PROBE.COM` SHA256
`c844192ef549c0f52d359ff3a1005e104ca1ca0b990cb6b7275d70a25ba4acaa`.
The positive path (mapping found, pattern written) has **not** executed
anywhere yet.

## Driver plan once the probe has run on Video II

1. **Mode set.** Prefer whatever the SL/TL BIOS actually does. If it has no
   INT 10h mode for this, the probe's register sequence becomes the driver's
   mode set after hardware confirmation.
2. **Reservation.** Generalize the RESERVE approach to the measured 64KB
   region, or require a configuration that keeps it outside DOS, with a
   separate fail-closed helper. No assumption about SL/TL memory size.
3. **Renderer.** The DDK four-plane shadow at 640 pixels is 64,000 bytes
   (ALTMODES.MD already flags the segment-size review). Because the target is
   linear packed 4bpp, the flush becomes a simpler plane-to-nibble conversion
   with no bank arithmetic. 16 real colors means NUMCOLORS=16 honestly.
4. **Cursor.** TCURSOR's bank math becomes linear with a 320-byte stride and
   640-pixel clipping.
5. **Fonts/metrics.** 640x200 shares the 8-pixel CGA-class font and tuple
   decisions already made for the 640x200 profiles.
6. **Name and scope.** Separate 8.3 driver name (proposed `TNDYV2.DRV`),
   own hashes and Setup entry, detection that refuses EX/HX.

## What would help most

- One run of `T2PROBE /W` on a real SL, TL or RL from a fresh boot: the
  report file, its exit code, and a photo of the screen if it drew.
- Or an 86Box SL2 machine with the owner's own BIOS ROM images, using the
  same command. ROMs are not supplied by this repository.

## Sources

- [86Box `src/video/vid_tandy.c` and `src/machine/m_tandy.c` (SL2 video and machine)](https://github.com/86Box/86Box/blob/master/src/video/vid_tandy.c)
- [DOSBox-X BIOS mode table, commented 640x200x16 Tandy entry](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/int10_modes.cpp)
- [Tandy Graphics Adapter (Wikipedia): SL/TL/RL enhanced mode, Video I/II](https://en.wikipedia.org/wiki/Tandy_Graphics_Adapter)
- [Radio Shack RSC-20 Computer Catalog (1989), 1000 SL graphics](https://colorcomputerarchive.com/coco/Documents/Catalogs/Radio%20Shack/RSC-20%20Computer%20Catalog%20%281989%29%28Radio%20Shack%29.pdf)
