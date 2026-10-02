# Tandy 1000 EX/HX Windows 3.0 display driver

Target: **8086/8088 instructions, Windows 3.0 real mode, 320x200 pixels,
16 colors, normal 640KB shared conventional/video memory**.

The correction builds as `TANDY88.DRV`. The original V1 source and frozen
binary are preserved for comparison in [V1NOTES.md](V1NOTES.md); its old
386/emulator workaround does not meet this target. Use the build and run
commands below for the correction. The legacy `src/tandy16` build is unchanged.

## Current correctness checkpoint

Candidate05: 51,296 bytes

SHA256: `ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee`

Candidate05 fixes the candidate04 Paintbrush BMP save/reopen defect. Native
Paintbrush saved and reopened a 200x120 sixteen-color test image plus newly
entered cyan lettering; all 24,000 reopened canvas pixels match the saved BMP.
The earlier candidate04 screenshot remains a record of drawing, not proof
that its saving worked. See [DIB88.MD](DIB88.MD) and [ROUND.MD](ROUND.MD).

Verified in DOSBox-X 2026.08.31 SDL2, September 28 nightly, with the accepted
`8086_prefetch` CPU setting and normal 640KB Tandy memory:

- Windows 3.00 real-mode desktop, Paintbrush menus/text/save/reopen,
  Program Manager restore/maximize, clean Windows exit and relaunch
- Live Windows `GetSystemMetrics` and `GetDeviceCaps`: 320x200,
  BITSPIXEL=1, PLANES=4, NUMCOLORS=16; active BIOS mode 09h
- Native unscaled Paintbrush capture: exactly 320x200 pixels and all 16 Tandy
  RGBI colors; logical resolution is measured independently of host scaling
- Real8086 CPU semantics, including negative checks for later-CPU opcodes
- Strict 8086 assembly, complete linked-object accounting, generated-code
  review, and emitted-instruction audit
- 128 register/stack/FLAGS preservation cases and4,096 generated rotations
- 24 video-memory reservation checks on each of 8086 and8086_prefetch
- BI_RGB 1/4/8/24 bitmap conversion, odd-width partial-band roundtrips,
  56 direct-screen clipping/banding/rejection cases and no measured heap leak
- Full framebuffer comparison: all 64,000 coordinates, 32,000 visible bytes,
 768 unchanged padding bytes, all colors and packed-byte values

Candidate04 also passed mouse strokes with palette changes, window drag/resize,
Notepad editing, and all four cursor corners; these are retained historical
checks. Candidate05 repeated the live color/border/bank and 12-case SRCCOPY
probes, each matching all 64,000 pixels against an independent reference. See [STATUS88.TXT](STATUS88.TXT)
for exact limits and which checks were repeated on candidate05. Physical Tandy hardware and an explicit double-click case
have not been tested. This emulator is not a cycle-exact 8088 model.

## Build and reproduce tests

The automated harnesses were validated on Linux. Requirements: Python 3,
DOSBox-X, and this repository's existing BIN/LIB/DDK
inputs. Windows installation media is not needed for these builds/tests.
Each output path below must be new.

    python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/build
    python3 src/tandysw/TEST86.PY --dosbox /path/to/dosbox-x --out /new/cpu-tests
    python3 src/tandysw/RESERVE.PY --dosbox /path/to/dosbox-x --out /new/memory-tests --cpu 8086_prefetch
    python3 src/tandysw/TESTFB.PY --dosbox /path/to/dosbox-x --out /new/frame-tests

The build produces `TANDY88.DRV`, full MASM listings, logs, staged source and
`RESULT.json`. Runtime acceptance is separate from a successful build. The
memory tests also produce `RESERVE.COM` for installation. No tracked DDK files
are rewritten. Sources and batches retain DOS CRLF line endings.

DIB inputs are uncompressed BI_RGB; RLE is unsupported. See [DIB88.MD](DIB88.MD)
for screen-header, dimension and band limits.

Details: [AUDIT86.TXT](AUDIT86.TXT) explains every incompatible inherited
instruction, raw runtime-generated code, stack bounds and linked-library
closure. [RESERVE.MD](RESERVE.MD) describes the DOS memory reservation and its
supported layout/failure cases.

## Install in a separate Windows 3.0 guest copy

Keep a clean stock-CGA Windows 3.0 baseline. Do not include Windows media or
installed Windows files in public driver packages.

1. Copy the built `TANDY88.DRV` to `C:\WINDOWS\SYSTEM\TANDY88.DRV`
2. Copy the tested `RESERVE.COM` to `C:\RESERVE.COM`
3. Install `EGASYS.FON`, `EGAFIX.FON` and `EGAOEM.FON` from your own Windows 3.0
   media into `C:\WINDOWS\SYSTEM`
4. Set these existing `SYSTEM.INI` [boot] entries:

       display.drv=tandy88.drv
       fonts.fon=egasys.fon
       fixedfon.fon=egafix.fon
       oemfonts.fon=egaoem.fon

5. Retain the stock Microsoft mouse driver; use COM1 serial-mouse emulation
6. Start Windows with `WIN /R` only after `RESERVE` succeeds

The launcher validates the exact candidate/helper hashes, font presence and
INI selection; verifies CPU readback; and refuses to launch Windows if video
reservation fails:

    python3 src/tandysw/RUN88.PY /path/to/guest-drive-c /path/to/dosbox-x

Use `--prepare-only --config /new/TANDY88.CNF` to validate and inspect the
configuration without starting the emulator. It never overwrites an existing
configuration and discards host console diagnostics to prevent runaway logs.

`RESERVE.COM` is 1,512 bytes, SHA256:
`644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8`

The helper supports the tested 640KB physical Tandy layout: BIOS reports 624KB;
mode 09h uses physical 98000h-9FFFFh. DOS retains the exposed 16KB overlap with its
MCB at 97FFh, below video RAM. It leaves the BIOS size word unchanged, survives
Windows exit, and is idempotent until reboot. Unexpected/occupied memory fails
closed. This is not validation of every Tandy memory expansion or genuine
MS-DOS release.

## Exact emulator scope

The launcher uses:

    [dosbox]
    machine=tandy
    memsize=0
    memsizekb=640
    allow more than 640kb base memory=false
    [cpu]
    core=normal
    cputype=8086_prefetch
    cycles=fixed 20000
    fpu=false
    [dos]
    xms=false
    ems=false
    umb=false
    [serial]
    serial1=serialmouse
    [render]
    scaler=none
    doublescan=false
    aspect=false

**Do not use `cputype=8088`** in this DOSBox-X build: it is rejected and falls
back to auto. `8086_prefetch` is the accepted 8086 ISA core with the four-byte
8088 prefetch queue. The configuration name alone is not the evidence: CPU
semantic probes were run under this setting with a 386 comparison control.
The clock setting above is an emulator speed, not a claim of hardware timing.

Native captures exclude host-window scaling/decorations. Program Manager and
some application dialogs were designed for larger displays, so clipping or
scrollbars at 320x200 are possible. A Capture menu can deactivate the current
window and change its title-bar color.

## Performance

This correctness checkpoint still flushes the full shadow framebuffer after
many drawing calls. Each flush converts 8,000 planar groups / 64,000 pixels /
32,000 video bytes. At the test setting `cycles=fixed 20000`, 16 isolated full
conversions took 13 BIOS ticks, about 0.714 seconds total or 44.6 ms per flush.
The batch timer granularity is 54.9 ms. This excludes Windows, GDI and cursor
painting and is emulator throughput only. Large redraws remain slow.

Keep this frozen correctness baseline when testing future dirty-region or
query/no-flush optimizations, and rerun affected Windows interaction tests.
