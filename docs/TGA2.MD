# Tandy Video II 640x200x16 (TNDYV2.DRV): first build, emulator-tested

**[Download TNDYV2.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/TGA2/TNDYV2.ZIP)** and follow the
[short install guide](tga2/INSTALL.TXT). Fonts, grabber and startup logo are
included. [Support integration test](tga2/SUPPORT.MD).

The remaining sections preserve the development and test record.

Status: **Windows 3.0 runs TNDYV2.DRV in 640x200 with 16 colours on 86Box's
Tandy 1000 SL/2, and the scripted session passes 88 of 88 checks
(2026-10-14).** The experimental driver-only prerelease is available; nothing
has run on a physical machine. The intended selector is restricted to the
SL/2 family, and the rendering evidence covers the emulated SL/2 only. EX/HX
have no Video II; this driver must not be used there (see "Limits" below).

The original `experimental-video-ii-2026-10-14` ZIP has no OEMSETUP.INF or
Video II Setup selector. The separate selector source `src/tga2/OEMSETUP.INF`
uses **EXPERIMENTAL TANDY SL/2 FAMILY ONLY 640x200x16**: 46 characters, within
the pinned Windows 3.0 OEM sample's 47-character description limit. It does
not add other models; the target remains Windows 3.0 real mode. The revised
packet must contain this exact INF and matching qualification/checksums;
the published original ZIP is retained. See [Setup, owned-file staging and recovery](tga2/INSTALL.TXT).
The existing EX/HX rc.6 OEM disk and its bound documentation are unchanged.

The 86Box machine needs the owner's own SL/2 BIOS ROM images. They are kept
private and are not in this repository; only their SHA-256 values are
recorded (`tga2/SL2ROMS.TXT`).

## What the SL/2 does (measured in 86Box)

| Item | Result | Evidence |
| --- | --- | --- |
| BIOS modes | INT 10h accepts 00h-0Ah only; no 640x200x16 BIOS mode | `tga2/T2MODES.TXT` (T2MODES.COM) |
| Memory | BIOS reports 624K; DOS arena ends at 9C00h | `tga2/T2PROBE_SL2.TXT` |
| Video II page | A0000h window = physical 90000h-9FFFFh (top 64K of 640K); 90000h-9BFFFh is ordinary DOS memory | T2PROBE found 0800h of its own tagged paragraphs at window offset 0, block at 9000h; 9800h-9BFFh were wiped by the mode-09 clear |
| Identification | INT 15h C0h: model FFh, submodel 00h, revision 13h (EX/HX-class DOSBox: 0Ah/10h) | `tga2/T2PROBE_SL2.TXT` |
| Pixel format | linear, 320 bytes per row, packed 4 bits, high nibble = left pixel, colour = palette register 10h+nibble | T2SHOW: 128,000 of 128,000 pixels exact (`tga2/T2SHOW.JSN`, `tga2/T2SHOW.PNG`) |

**Enable** (the driver's text, also used by T2SHOW): BIOS mode 0Ah; palette
registers 10h-1Fh = 0-15 (nibble = IRGB); border (array register 2) = 0;
CRTC R4=FFh, R5=06h, R6=C8h, R7=E0h, R9=00h, R12=R13=0; array register 5 = 1
(index to 3DAh, data to 3DEh); clear A000:0000, 64,000 bytes.
**Disable:** array register 5 = 0, then the BIOS mode that was set before.

## T2RESV.COM: keeping the page from DOS

Because 90000h-9BFFFh is free DOS memory, Windows would load over the
screen. `T2RESV.COM` is `RESERVE.COM` (src/tandysw, unchanged and still the
shipped helper) generated with only the range and texts changed, by exact
counted substitutions (`src/tga2/T2RESV.PY`): it keeps 0C00h paragraphs at
9000h (MCB 8FFFh) as one owned DOS block. Every RESERVE check stays: Tandy
signature, BIOS 624K, text mode 3, DOS 3+, the real arena ending at 9C00h,
last-fit allocation verified to the paragraph, no MCB edits, fail closed.
23 of 23 checks pass in DOSBox-X (`tga2/T2RESV.JSN`; normal, repeat,
three allocation strategies, occupied top, occupied exact range, RESERVE's
own 16K block already present, short arena, wrong BIOS size, wrong mode,
expanded memory, CGA, DOS 2.11, and the T2SHOW gate cases below).
T2RESV.COM is 1,502 bytes, SHA-256 `ff478b95...0360`.

The test probe `T2RESVT.ASM` is generated from `RESERVET.ASM` the same way.
Review fix (2026-10-14): its count of the resident's open handles still
looked for RESERVE's block (97FFh, 400h paragraphs), so for T2RESV the count
was never taken and "resident closes inherited handles" passed without
checking anything. It now looks at 8FFFh/0C00h, and RESERVE's mode-09 alias
probe (`P`), which is about physical 9800h only, is removed from T2RESVT
and fails if called; the generator rejects any leftover 97FFh, 9800h or
400h. A liveness check keeps it honest: a foreign resident at exactly
9000h/0C00h (T2RESVT `T`, a TSR that keeps its handles) must be seen with
open handles.

**T2SHOW's reservation gate.** T2SHOW's enable text clears 64,000 bytes at
physical 90000h, which without T2RESV can belong to DOS or another program.
Review fix (2026-10-14): before touching any video register or memory it now
requires the last DOS block to be MCB 8FFFh, 0C00h paragraphs, owned by a PSP
whose resident record at 103h is T2RESV's (`TNDYV2R1`, 9000h, 0C00h);
otherwise it exits 3 and draws nothing (`/G` stops after the check, for the
DOS tests). The harness checks the record offset in T2RESV's listing, and
T2TEST refuses to generate T2SHOW if any of four markers (`@MODE@`,
`fill_row:`, `int 10h`, `0a000h`) comes before the gate. Gate cases: no
reservation, a foreign block at exactly 9000h/0C00h, RESERVE's 16K block,
a short arena (all exit 3), and behind T2RESV (exit 0). These tests compare
five arena metadata fields before and after: `last_mcb`, `last_owner`,
`last_size`, `arena_end`, and `bda_kb`. They do not trace all RAM or video
register writes.

Both fixes have failure tests (`T2RESV.PY --mutate`, `tga2/T2RMUT.JSN`):
`stale_handles` puts the old 97FFh/400h comparison back and `no_gate`
removes the gate; each run passes only if exactly the targeted checks fail,
and both are caught. The host acceptance now compares the exact failure set
and rejects duplicate reports. `T2RTEST.PY` covers expected-only, missing,
extra, empty, duplicate and reordered failure lists, and checks the saved
DOS failure lists under the corrected rule; it does not rerun the guest.
On the 86Box SL/2 the gated T2SHOW (SHA-256
`155a5ea2...570d`) still draws all 128,000 pixels exactly behind T2RESV
(`tga2/T2SHOW2.JSN`, `tga2/T2SHOW2.PNG`). The Windows session below ran
before the gate existed, with T2SHOW `09cdb59e...7809`, after T2RESV.

The cost is memory: Windows 3.0 reports 176K free in real mode, against
242K on the PC1512 run.

## How TNDYV2.DRV is built

`src/tga2/T2BUILD.PY` is `BUILD15.PY` (the PC1512 pipeline) with
`T2PATCH.PY` in place of P15PATCH's staged edits: BUILD88's 640x200x4 profile,
the sixteen-colour sections restored from the 320x200x16 stage, then:

- **Flush (TSOFT):** each shadow byte (eight pixels in four planes R, G, B, I
  at +0/+80/+160/+240) becomes four VRAM bytes through a 1KB table in the code
  segment (`t2_row`); rows are linear at A000h with a 320-byte stride.
  `T2PATCH.PY --check` proves the conversion against a model of 86Box's
  decode for every colour, and a plane-order error is caught.
- **Pointer (TCURSOR):** linear 320-byte rows, two pixels per byte, AND/XOR
  per nibble. The pointer is composited in a RAM copy of the saved bytes and
  written back row by row with `REP MOVSB` (as the PC1512 build does).
- GDI reports 16 colours; the retain-footprint checks use VRAM bytes.

TNDYV2.DRV: 55,552 bytes, SHA-256 `6a8d97b0...4c43`; a second build gave the
same hash (`tga2/T2RES.JSN`). BUILD88's audits pass on the patched listings.

## Windows 3.0 on the 86Box SL/2 (2026-10-14)

Setup: 86Box 6.0, machine `tandy1000sl2`, 8086 at 8 MHz, 640K, internal
video, XTIDE disk with the verified Windows 3.0 image used for the other
86Box runs, serial mouse on COM1 through `PCPMOUSE.PY` (one mickey = one
pixel). AUTOEXEC runs T2RESV; Windows starts with `WIN /R`.
Configuration: `tga2/P86CFG.TXT`, `tga2/P86PREP.JSN`.

The session is the PC1512 script (`PCPWIN.PY --width 640 --target tga2`):
colour bars before Windows (T2SHOW), menus by keyboard and mouse, About,
the 16-bar wallpaper with the arrow over every bar, mouse drift, Program
Manager minimize/restore, Notepad and Calculator overlapping, dragging,
Paintbrush with 16 filled boxes drawn by mouse, the arrow over all 16
palette colours, the crosshair over every box, Save As, close and reopen,
exit to DOS, second launch, exit again. 46 minutes of emulated time.

| Check (PCPCHK) | Result |
| --- | --- |
| All checks | **PASS, 88 of 88**, none skipped (`tga2/P86CHK.JSN`) |
| Arrow glyph | equals the driver's own `NORMAL.CUR` as Windows shows it on 200 lines |
| Palette arrows | 16 of 16 on the first attempt (`tga2/P86LAND.JSN`) |
| Saved BMP | equals the screen; reopened canvas identical |
| After each exit | T2RESV reports "already installed", which it says only after checking text mode 3, the Tandy BIOS and the intact reservation |
| Checker mutations | PCPMUT: clean frames pass, all 8 injected faults caught |
| Evidence index | PCPEVID: PASS, 97 frame ids, 10 retained raw captures re-decoded exactly |

**Against the PC1512 reference run** (same script, same Windows image),
91 of the 95 frames that both runs have are pixel-identical. The four that
differ: `about` (the free-memory figure, 176K vs 242K); `arrow_12_t1` (a
PC1512 miss attempt); `calc_over_pm_notepad` and `saveas_dlg`, both caught
before the application had finished repainting (the Run dialog not yet
erased; the Save As dialog body not yet drawn after 12 seconds). PCPCHK does
not judge those two frames, and the frames after them match. The SL/2 is
slower to repaint: the flush writes four times as many VRAM bytes, and with
less free memory Windows reloads more code from disk.

### What the first runs showed, and what changed

The first session stopped at the palette arrows: the left palette cells
showed Paintbrush's crosshair, or an arrow with its bottom rows missing, or
no pointer at all. Every frame before that point already matched the PC1512
run exactly. Two causes were found:

1. **The capture hotkey reached the guest.** PCP86 captured with 86Box's
   Ctrl+F11. The Tandy keyboard has an F11 key, and Paintbrush reacted to
   the keystroke by changing the pointer shape while the capture was being
   taken. A direct test: over colours 0, 15 and 7 the pointer was the
   crosshair until the first Ctrl+F11, and the arrow after it. For `tga2`
   only, PCP86 now clicks 86Box's own toolbar "Take screenshot" button (the
   same 86Box capture, no guest input; decodes exactly), and PCPWIN moves
   the pointer one pixel right and back before each palette and crosshair
   capture, so Paintbrush sets the shape from a mouse message instead of a
   keystroke. The ColorPlus and PC1512 procedures are unchanged.
2. **The pointer was drawn pixel by pixel in VRAM**, slow enough to be seen
   half-drawn. It is now composited off-screen and copied row by row.

With both, the next complete run is the one above.

## Limits

- **Not tested on real hardware.** Everything above is 86Box's model of the
  SL/2 with real SL/2 BIOS ROMs. The register sequence, the physical page
  location and the timing are 86Box's; a real SL, TL or RL may differ.
- **No hardware detection in the driver.** TNDYV2.DRV programs Video II
  registers when Windows enables it. T2RESV refuses non-Tandy machines, other
  memory sizes and anything not in text mode 3, but it cannot tell an EX/HX
  (also 640K, BIOS 624K) from an SL. A detection signature (the INT 15h C0h
  values above are one candidate) needs real SL/TL/RL readings first.
- **640K machines only.** On the SL/2 the video area is the top 128K of
  RAM, so the page moves with memory size; T2RESV fails closed unless the
  BIOS reports 624K and the arena ends at 9C00h.
- Windows 3.0 real mode only, like the other 8088-class drivers.

## What to test on a real SL/2

In this order, from a fresh boot, with nothing else loaded:

Physical SL/2 testing is still needed. Other SL/TL/RL models are not qualified
by the SL/2 selector or the emulator results.

1. `T2PROBE /W`: send `T2PROBE.TXT`, the exit code, and a photo if it drew.
   This confirms or refutes the page location.
2. `T2MODES`: send `T2MODES.TXT`.
3. `T2RESV` then `T2SHOW` (it refuses to draw without T2RESV): a photo of the screen. Sixteen vertical bars, black
   on the left to white on the right, are the expected result.
4. Only if 3 looks right: `display.drv=TNDYV2.DRV` in SYSTEM.INI (keep a copy
   of the old line), `T2RESV`, `WIN /R`.

## Reproducing

    # tools: Xvfb, xdotool, mtools, Python 3 + Pillow;
    # the pinned DOS toolchain and display view (tools/BUILDDEPS); DOSBox-X
    python3 src/tga2/T2BUILD.PY --repo <display view> --dosbox <dosbox-x> --out <dir>
    python3 src/tga2/T2PATCH.PY --check
    python3 -B src/tga2/T2RTEST.PY           # host acceptance regression
    python3 src/tga2/T2RESV.PY --repo <display view> --dosbox <dosbox-x> --out <new dir>
    python3 src/tga2/T2RESV.PY ... --out <new dir> --mutate stale_handles   # must be CAUGHT
    python3 src/tga2/T2RESV.PY ... --out <new dir> --mutate no_gate         # must be CAUGHT
    python3 src/tga2/T2TEST.PY --out <gen>          # T2SHOW.ASM
    python3 src/pcjr/BUILDCOM.PY --deps <inputs> --dosbox <dosbox-x> --out <bin> \
        --src <gen>/T2SHOW.ASM --src src/pcp/MSTEST.ASM
    # 86Box 6.0 with the owner's SL/2 ROMs (hashes: tga2/SL2ROMS.TXT), private
    Xvfb :79 -screen 0 1600x1200x24 &
    python3 src/pcp/PCP86.PY prepare --target tga2 --vm <new dir> --pristine <private.img> \
        --drv <dir>/TNDYV2.DRV --drv-sha 6a8d97b0...4c43 --tools <T2RESV, T2SHOW, MSTEST> --mouse pty
    python3 src/pcp/PCPMOUSE.PY serve --vm <vm> &
    python3 src/pcp/PCP86.PY start --vm <vm> --box <86Box AppRun> --roms <rom dir>
    sleep 80
    python3 src/pcp/PCPWIN.PY --vm <vm> --box <AppRun> --roms <rom dir> --width 640 --target tga2
    python3 src/pcp/PCP86.PY stop --vm <vm>
    python3 src/pcp/PCPCHK.PY --vm <vm> --width 640 --target tga2 \
        --cursor <dir>/B640/resources/NORMAL.CUR --json CHECKS.JSN
    python3 src/pcp/PCPMUT.PY --evidence docs/tga2 --width 640 --target tga2
    python3 src/pcp/PCPEVID.PY --evidence docs/tga2 --width 640

Frames: `tga2/FRAMES/Fnn.PNG` are the exact 640x200 decodes (index = IRGB),
indexed by `tga2/P86RAW.JSN`; `tga2/T2W_nn.PNG` are 86Box captures kept raw.

## Background: groundwork (2026-10-10)

Before ROM images were available, the programming model came from 86Box's
`vid_tandy.c` and DOSBox-X's commented-out mode entry, and T2PROBE was
written to find the physical page without writing through an unknown window.
On the SL/2 it found the page (above) and, as designed, wrote nothing
(`SAFE_TO_WRITE=00`: the window is not inside the probe's own block).

### T2PROBE (src/tga2)

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

## Sources

- [86Box `src/video/vid_tandy.c` and `src/machine/m_tandy.c` (SL2 video and machine)](https://github.com/86Box/86Box/blob/master/src/video/vid_tandy.c)
- [DOSBox-X BIOS mode table, commented 640x200x16 Tandy entry](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/int10_modes.cpp)
- [Tandy Graphics Adapter (Wikipedia): SL/TL/RL enhanced mode, Video I/II](https://en.wikipedia.org/wiki/Tandy_Graphics_Adapter)
- [Radio Shack RSC-20 Computer Catalog (1989), 1000 SL graphics](https://colorcomputerarchive.com/coco/Documents/Catalogs/Radio%20Shack/RSC-20%20Computer%20Catalog%20%281989%29%28Radio%20Shack%29.pdf)
