# Plantronics ColorPlus 320x200x16 driver (PCP3216): first build

Status: **PCP3216.DRV runs Windows 3.0 real mode on an emulated IBM PC/XT
with a Plantronics ColorPlus card in 86Box 6.0, and passes all 63 checks of
a scripted session: desktop redraws, overlapping windows moved with the
mouse, menus, dialogs, the cursor over all 16 colours, a 16-colour
Paintbrush image saved, closed, reopened and read back, exit to DOS and a
second launch (see "Windows 3.0 in 86Box" below). No driver defect was
found. It has not run on real ColorPlus-class hardware.** Nothing shipped
changes; this remains experimental.

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

`PCPTEST.PY` fails unless MASM reports exactly 0 severe errors, LINK reports
no error, the EXE exists, the emulator exits 0, the guest reports RUN=PASS
and VRAM.BIN is exactly 32,768 bytes; only then are bytes and pixels judged.
`BUILDPCP.PY` refuses a BUILD88 result that does not say PASS.

The cursor paths, the column and retained-cursor flushes and mode switching,
untested at the time of this build, have since run under Windows in 86Box
(next section).

## Windows 3.0 in 86Box (2026-10-11)

### Setup

| Item | Value |
| --- | --- |
| Emulator | 86Box 6.0 build 9001, official Linux AppImage, SHA-256 matches the release page (`pcp/P86ROMS.TXT`) |
| ROMs | 86Box ROM set tag v6.0 (commit `26761b5a`), private; hashes of the files loaded in `pcp/P86ROMS.TXT` |
| Machine | `ibmxt86`: IBM 5160 (1986 BIOS), 8088 at 4.77 MHz, 640KB, XT keyboard. The 1982 `ibmxt` model stops at 256KB, too little for Windows |
| Video | `gfxcard = plantronics`: 86Box "Plantronics Colorplus" (`src/video/vid_cga_colorplus.c`) |
| Disk | XTIDE (XT BIOS) with the workshop's PCjs PC DOS 3.20 + Windows 3.0 image (raw SHA-256 `f55fe24b...117561`, from `src/pcjr/PCJSIMG.PY`). The guest boots **IBM PC DOS 3.20 from that disk** |
| Mouse | Microsoft serial mouse on COM1, spoken byte-exactly by `src/pcp/PCPMOUSE.PY` through 86Box's Serial Passthrough (COM) on a host pty (see "Input") |
| Config | `pcp/P86CFG.TXT` |

Changes to the private copy of the install, made and logged by
`PCP86.PY prepare` (`pcp/P86PREP.JSN`): `display.drv=PCP3216.DRV`
(SHA-256 `67f8a3d7...c7c406`); CONFIG.SYS reduced to FILES/BUFFERS (HIMEM,
SMARTDRV and EGA.SYS need XMS or an EGA); `[keyboard] type=1` (XT keyboard);
WIN.INI `MouseSpeed=0` (no acceleration, so a test move of N mickeys is N
pixels); test tools in `C:\PCP`. The EGA fonts, grabber and group files of
the original install are unchanged. Windows media stayed in private
temporary folders; only frames, logs and the Paintbrush test image are here.

### The card is a ColorPlus

`src/pcp/PCPID.ASM` sets mode 04h and 3DDh = 10h, writes different bytes at
B800:0000 and B800:4000 and reads them back, then checks that with 3DDh = 0
the card aliases 4000h onto 0000h like a plain 16KB CGA. Only a card with
two separate 16KB planes switched by 3DDh passes (`pcp/P86NEG.JSN`):

| Run | Result |
| --- | --- |
| 86Box `plantronics`, at boot and after each Windows exit | `SPLIT=5A,33,A5,CC OFF_ALIAS=01 COLORPLUS=01` |
| 86Box IBM EGA, same machine and disk | `OFF_ALIAS=00 COLORPLUS=00` |
| DOSBox-X `machine=cga` and `tandy`; DOSBox 0.74 `tandy` | `SPLIT=A5,CC,A5,CC` (aliased) `COLORPLUS=00` |
| DOSBox 0.74 `machine=cga` | 32KB without aliasing: `OFF_ALIAS=00 COLORPLUS=00` |

The DOSBox runs use `JRRUN.PY --machine cga|tandy --cmd PCPID.COM --expect
PCPID=1`. Before Windows, `PCPSHOW` drew 16 bars that decode to exactly
colours 0-15 in IRGB order (64,000 pixels, 0 mismatches), which settles the
plane and bit order on this emulated card.

### Input

Keys reach 86Box through xdotool. The mouse could not: under Xvfb, 86Box 6.0
reads XTEST pointer input through XInput2 and mixes XI_Motion and
XI_RawMotion values (`src/qt/xinput2_mouse.cpp`), so injected motion arrives
wrong or not at all. `src/pcp/MSTEST.ASM`, a polling COM1 packet counter
that runs under DOS with no mouse driver and no Windows, showed zero motion
packets for absolute moves. The harness therefore connects COM1 to a host
pty and speaks the Microsoft protocol itself (`PCPMOUSE.PY`), answering
detection with `M` and sending 3-byte packets at 1200-baud byte timing.

- MSTEST under DOS received exactly what was sent:
  `B=000F P=0005 X=0046 Y=0032 BAD=0000` for moves of +100/+50/-30 and a
  click.
- Under Windows, with the pointer homed in the (0,0) corner, 40 packets of
  (+5,+3) at full 1200-baud rate put the arrow's hotspot exactly at
  (200,120), twice, and again with wider byte spacing (`pcp/P86DRIFT.JSN`).
  The driver's interrupt-time cursor redraw does not cost mouse bytes on a
  4.77 MHz 8088.
- Applications confine the cursor during drags, so the script re-homes the
  pointer before every click and drag instead of dead-reckoning.

### The session and its checks

`src/pcp/PCPWIN.PY` runs one scripted session (about 45 minutes at 4.77 MHz)
and saves 59 86Box screenshots. `SHOTDEC.PY` decodes each graphics capture to
exact 320x200 IRGB pixels and rejects any capture that does not decode
exactly; all 57 graphics frames matched their raw capture
(`pcp/P86RAW.JSN`). `src/pcp/PCPCHK.PY` then judges the frames and files read
back from the guest disk: **63 of 63 checks pass** (`pcp/P86CHK.JSN`).

| Area | What was checked | Result |
| --- | --- | --- |
| Colour bars | PCPSHOW, 16 bars, every pixel | PASS |
| Menus, dialogs | Program Manager File menu opened by keyboard and by a mouse click, Help > About opened and closed: each time the desktop returns to the reference frame exactly | PASS (0 pixels differ) |
| Overlapping windows | Notepad under Program Manager under Calculator; Calculator dragged +60,+40 by its title bar with the mouse; both closed: desktop identical to the reference | PASS |
| Paintbrush drawing | 16 Filled Box rectangles drawn with the mouse, one per colour picked from the palette: every pixel of each 27x53 box is its colour, the rest of the canvas untouched | PASS (16 boxes) |
| Arrow cursor over all colours | Arrow placed over each of the 16 palette colours: each frame equals the background with one identical black/white arrow composited in, nothing else changed; background restored exactly after moving away | PASS (16 colours) |
| Inverting cursor over all colours | Paintbrush's tool cursor over the centre of each box: every changed pixel is the box colour XOR 15, nothing outside the cursor changed, restored exactly | PASS (16 colours) |
| Save, close, reopen | TEST16.BMP saved, Paintbrush closed, reopened with the file: canvas identical; the saved 320x170 4-bit BMP equals the screen at all 30,988 visible canvas pixels | PASS |
| Exit to DOS | Exit Windows twice: PCPID afterwards reads BIOS mode 03h, 80 columns, ColorPlus still identified; text screen captured (`P86_09.PNG`) | PASS |
| Second launch | WIN /R again in the same boot: desktop identical to the first launch | PASS |

Screenshots straight from 86Box: `pcp/P86_01.PNG` bars, `_02` About (Windows
3.0, Real Mode, 337K free), `_03` File menu opened by mouse, `_04`
Calculator dragged, `_05` the 16 boxes, `_06` arrow over light gray, `_07`
inverted cursor over blue (shown yellow), `_08` reopened image, `_09` DOS
after exit, `_10` second launch. All 57 decoded frames: `pcp/FRAMES`, named in
`pcp/P86RAW.JSN`; the image Paintbrush saved: `pcp/TEST16.BMP`; step log: `pcp/P86RUN.JSN`.

### Findings

- **No PCP3216 defect found.** Nothing in the driver was changed.
- The saved BMP stores the driver's colour table, which this driver inherits
  unchanged from the DDK source behind TR5/TANDY88: light gray is recorded
  as RGB 128,128,128 and dark gray as 64,64,64. The check maps it exactly,
  but another program will show those two grays darker than the screen. It
  applies equally to the shipped Tandy drivers; not changed here.
- Windows 3.0 is slow on a 4.77 MHz XT: about two minutes to start, and
  Calculator's rounded buttons take tens of seconds to paint. The scripts
  wait for repainting; early runs that did not were harness failures, not
  driver faults (`P86RUN.JSN` records the final run only).
- Paintbrush fills a box up to, not including, the release point.

### Passed in 86Box / still needs real hardware

| Passed in 86Box 6.0 (emulated IBM XT + Plantronics ColorPlus) | Still needs real hardware |
| --- | --- |
| Driver loads; Windows 3.0 /R starts, runs, exits and restarts | A real ColorPlus and the clones (ATI Small Wonder, Paradise EGA 480, V6355 cards, ...), whose 3DDh handling may differ from 86Box's model |
| Plane split and bit order (PCPSHOW, PCPID) | Real monitor output: timing and colours on a real RGB display (86Box's snow emulation was on, its default; it applies to text modes) |
| Redraws, overlap, menus, dialogs, window drag by mouse | Real 8250 and mouse timing, other mice (bus, InPort) |
| Cursor drawing and restore over all 16 colours | A real XT keyboard path and XT BIOS variants |
| Paintbrush draw / save / close / reopen, file equals screen | PC DOS with real memory managers, TSRs, other DOS versions |
| Exit to DOS restores text mode 03h; second launch identical | A clean CGA-class install (CGA fonts and grabber instead of the EGA ones reused here), DOS boxes and grabber switching |
| Mouse delivery exact at 1200 baud at 4.77 MHz | Performance and responsiveness on real 8088 and V20 machines |

### Reproducing

    # tools: Xvfb, xdotool, mtools, Python 3 + Pillow, squashfs-tools; the
    # pinned DOS toolchain (tools/BUILDDEPS) and DOSBox-X for the DOS builds
    python3 src/pcp/BUILDPCP.PY ...                     # PCP3216.DRV (above)
    python3 src/pcp/PCPTEST.PY --show --deps <inputs> --dosbox <dosbox-x> --out <dir>
    python3 src/pcjr/BUILDCOM.PY --deps <inputs> --dosbox <dosbox-x> --out <dir> \
        --src src/pcp/PCPID.ASM --src src/pcp/MSTEST.ASM
    python3 src/pcjr/PCJSIMG.PY <PCDOS320-WIN300-EGA.json> <private.img>
    # 86Box: release AppImage + ROM set v6.0, both private (pcp/P86ROMS.TXT)
    Xvfb :79 -screen 0 1600x1200x24 &
    python3 src/pcp/PCP86.PY prepare --vm <new dir> --pristine <private.img> \
        --drv PCP3216.DRV --tools <dir with PCPID.COM PCPSHOW.EXE SHADOW.BIN MSTEST.COM> --mouse pty
    python3 src/pcp/PCPMOUSE.PY serve --vm <dir> &
    python3 src/pcp/PCP86.PY start --vm <dir> --box <86Box AppRun> --roms <rom dir>
    sleep 75   # XT POST and DOS boot
    python3 src/pcp/PCPWIN.PY --vm <dir> --box <AppRun> --roms <rom dir> \
        --menu-file 82,60 --calc-title 90,7
    python3 src/pcp/PCP86.PY stop --vm <dir>
    python3 src/pcp/PCPCHK.PY --vm <dir> --json CHECKS.JSN

Host tests, no emulator: `python3 src/pcp/HOSTTEST.PY` (SHOTDEC decodes
synthetic 86Box captures exactly and rejects distorted ones; mouse packets
round-trip through MSTEST's decoder for every value) and
`python3 src/pcjr/CHKTEST.PY`. Built tools: `pcp/PCPIDB.JSN`, `pcp/MSTESTB.JSN`
(pinned MASM 5.10, both rebuilt to the same hash).

## Next steps

1. **Real hardware.** Run `PCPID` and `PCPSHOW` (with `SHADOW.BIN`) on a
   ColorPlus-class card and photograph the bars; then Windows 3.0 /R with
   `display.drv=PCP3216.DRV` and the same session by hand.
2. **A clean CGA-class install** (CGA fonts and grabber), which also lets the
   86Box session test DOS boxes.
3. **Setup integration** under its own 8.3 names, with no change to the
   Tandy disk's existing choices. The Tandy launcher and RESERVE do not
   apply. Plain `WIN /R`.
4. **640x200x4 later**, possibly with the WINPCP author: same two-plane
   layout at 1bpp.

## Sources

- [86Box `src/video/vid_cga_colorplus.c`](https://github.com/86Box/86Box/blob/master/src/video/vid_cga_colorplus.c)
- [Plantronics ColorPlus notes (seasip.info)](https://www.seasip.info/VintagePC/plantronics.html)
- [WINPCP repository and hardware notes](https://github.com/cluehawk/WINPCP)
