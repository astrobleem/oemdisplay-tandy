# Five selectable original-Tandy display modes

This driver set targets **Windows 3.0 real mode on the original 8088-based
Tandy 1000 EX/HX with normal 640 KB memory**. It uses no 386, expanded-memory,
EMS/XMS or UMB workaround. The default candidate05 driver is unchanged; four
new binaries expose additional modes through Windows Setup's **Other display**
menu. Mode selection is an installation choice followed by restarting Windows,
not an INI tweak or a live desktop resolution switch.

## Status

**Rendering, reproducible builds and five-mode native OEM emulator acceptance
passed (October 2, 2026).** The four new profiles passed 374
Windows GDI cases comparing 33,024,000 pixels. All five fresh driver rebuilds
matched byte for byte, and each build's 27 linked objects passed the instruction
and linkage audits. These results establish the tested emulator behavior, not
physical hardware or cycle-exact 8088 performance.

Native Windows Setup has now selected all five profiles sequentially, then
returned from the default to 640x200 four-color. Five independent clones of
these Setup-produced installations passed **466 GDI cases / 38,912,000 pixels**
without SYSTEM.INI edits. Exact selected drivers/fonts were checked, original
CONFIG.SYS remained unchanged, and the custom splash is embedded. These are
additional installation checks; the four-new-profile rendering total above
remains 374 cases / 33,024,000 pixels.
[Native Setup and installed-runtime evidence](modes/oem/RESULT.JSON).

**Final native acceptance passed:** a fresh emulator process booted with only
the installed C: drive, reopened the saved Paintbrush bitmap, and returned
cleanly to Program Manager. [Cold/reopen evidence](modes/oem/COLD.JSON).
The final rebuilt ZIP passed verification and byte-identical repeat packaging.

![Windows Setup's five original-Tandy choices](modes/oem/CHOICES.PNG)

## Select a mode

| Setup profile | File | BIOS | Actual display colors | Fonts / tuple |
| --- | --- | --- | --- | --- |
| 320x200x16, default | `TANDY88.DRV` | 09h | Tandy sixteen-color palette | EGA / `133,96,72` |
| 640x200x4 | `TNDY6404.DRV` | 0Ah | Black, red, green, white | CGA / `200,96,48` |
| 160x200x16 | `TNDY160.DRV` | 08h | Tandy sixteen-color palette | CGA / `200,96,48` |
| 320x200x4 | `TNDY3204.DRV` | 04h | Black, cyan, magenta, white | CGA / `200,96,48` |
| 640x200x2 | `TNDY6402.DRV` | 06h | Black, white | CGA / `200,96,48` |

**640x200x4 is the recommended starting choice for usable desktop width.** The
sixteen-color default remains useful when color range matters more than width.
The 160- and 320-pixel modes can clip application and Setup dialogs, requiring
keyboard navigation. Every profile retains a 200-pixel logical height.

On the original EX/HX, **BIOS 0Ah is 640x200 with four colors**. There is no
640x200 sixteen-color claim here. The current four-color hardware palette is
RGBI `[0,12,10,15]`; its Windows color contract is black/red/green/white. The
320x200 four-color palette is `[0,11,13,15]` (black/cyan/magenta/white). Hardware
RGBI captures can show the monitor/emulator's bright-color RGB values; those
need not equal the logical RGB values exported into a BMP.

### Install or switch through Windows Setup

Start with a working stock-CGA Windows 3.0 installation and a backup. The OEM
disk supplies its display dependencies; it is not a complete Windows installer.

1. Extract `TANDY88.ZIP` and copy the contents of `DISK1` to a 360 KB disk or
   DOS-accessible directory
2. Exit Windows and run `INSTALL` from that disk at the DOS prompt. It installs
   the shared reservation helper and launcher in `C:\TANDY88`
3. Run `C:\TANDY88\TANDY88 SETUP`, choose **Other display**, provide the OEM
   disk path, and select the required mode. Use the same disk path if Setup
   asks for `TNDYLOGO.RLE`
4. Let Setup install the selected driver, matching fonts and custom splash.
   Start Windows with `C:\TANDY88\TANDY88` on every boot
5. To change modes later, exit Windows, repeat the guarded Setup step, choose
   the new profile and restart through the same launcher

Setup owns the display/font entries and rebuilds `WIN.COM`; normal installation
never asks users to edit SYSTEM.INI or copy a driver directly into Windows.
Keep the installed DOS helper when upgrading an earlier TANDY88 disk. Simply
copying a splash image does not rebuild the startup executable.

For fresh Windows installations, stock CGA first and then the OEM display-change
flow avoids the cramped graphical Setup phase. Do not start a graphical phase
without a successful reservation. The [full OEM contract](OEMDISK.MD) and
[distribution instructions](../README.TXT) explain the fail-closed launcher.

## Memory and driver contract

All profiles retain the shared software renderer's **four logical DDB planes**:
`BITSPIXEL=1`, `PLANES=4`. `NUMCOLORS` is the actual display count: 16, 4 or 2.
The planes describe the internal device-dependent bitmap representation; they
do not add physical colors. Reduced-color drivers quantize RGB input to their
mode palette and interpret raw DDB aliases according to that palette. A four-
plane compatible bitmap in the monochrome mode still displays only two colors.

| Profile | Logical shadow bytes | Hardware VRAM bytes | Visible hardware bytes |
| --- | ---: | ---: | ---: |
| 320x200x16 | 32,000 | 32,768 | 32,000 |
| 640x200x4 | 64,000 | 32,768 | 32,000 |
| 160x200x16 | 16,000 | 16,384 | 16,000 |
| 320x200x4 | 32,000 | 16,384 | 16,000 |
| 640x200x2 | 64,000 | 16,384 | 16,000 |

The 16K/32K/64K shadow shorthand means exactly 16,000/32,000/64,000 bytes here.
The 64,000-byte shadow stays below the 65,536-byte segment limit. Hardware VRAM
is banked differently from that shadow; checks cover visible pixels and padding
rather than assuming these representations have identical sizes.

The accepted `RESERVE.COM` and permanent launcher are unchanged. On the tested
640 KB layout, the BIOS reports 624 KB; the helper protects the extra 16 KB
video overlap exposed to DOS. That conservative reservation is shared across
**all five modes**, even when a mode's hardware buffer uses only 16 KB. It does
not allocate the logical shadow and is not a memory-expansion workaround.
Unexpected layouts, a busy video region and linked UMB arrangements fail closed.
Never bypass failure by launching WIN directly. See
[RESERVE.MD](../src/tandysw/RESERVE.MD).

### Fonts and custom splash

The unchanged default retains `EGASYS.FON`, `EGAFIX.FON`, `EGAOEM.FON` and the
resource/Setup tuple `133,96,72`. The new profiles use the eight-pixel
`CGASYS.FON`, `CGAFIX.FON`, `CGAOEM.FON` fonts and tuple `200,96,48`, including
96x48 logical DPI. This is an intentional low-resolution font choice.

The three CGA fonts are the only new Windows dependencies. The original five
Windows support files (three EGA fonts, `CGA.GR2`, `CGALOGO.LGO`) are unchanged.
All profiles retain the same pinned first-party `TNDYLOGO.RLE` image and stock
loader. Setup builds the custom splash into WIN.COM normally. The custom-splash
work merged from main is preserved; [SPLASH.MD](SPLASH.MD) remains its source
and runtime record.

## Binary identities

These are the exact package inputs, reproduced by the fresh builds in
[REBUILD.JSON](modes/REBUILD.JSON). The mode-specific build records remain in
`modes/160`, `modes/3204`, `modes/6404rg` and `modes/6402`.

| Driver | Bytes | SHA256 |
| --- | ---: | --- |
| `TANDY88.DRV` | 51,296 | `ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee` |
| `TNDY6404.DRV` | 50,832 | `5ab225f6e93d53f39d092b8db81fd0129a0fe473cf30eef880ddaeaaa0a8d306` |
| `TNDY160.DRV` | 51,296 | `124a07c38c13922a4cbd58452d39108755f632abe01e4dd17780c32140d2aedd` |
| `TNDY3204.DRV` | 50,848 | `c90526efb90f4434e8aa567d439e9cdf7f81c096968a362806a992052a81e9e9` |
| `TNDY6402.DRV` | 50,704 | `b0c95515462ba27ce208963dd94957019995e3e6085d147771ef037b39967652` |

The shared reservation SHA256 remains
`644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8`.
The custom image SHA256 remains
`e7a9c043ce3b9f9c78f7ff38bc68d211a0da32462e036abb7135f0602194f083`.
See [BUILDING.MD](../BUILDING.MD) for the eight Windows dependency pins and
per-profile build commands. The legacy root `TNDY16.DRV` is not a package input.

## Verification

[RESULT.JSON](modes/RESULT.JSON) summarizes the four new Windows rendering
runs; the unchanged default keeps its candidate05 evidence in
[STATUS88.TXT](../src/tandysw/STATUS88.TXT) and [DIB88.MD](../src/tandysw/DIB88.MD).

| Current new profile | Windows GDI cases | Pixels compared | Independent report |
| --- | ---: | ---: | --- |
| 160x200x16 | 92 | 2,944,000 | [160/GDI.JSON](modes/160/GDI.JSON) |
| 320x200x4 | 94 | 6,016,000 | [3204/GDI.JSON](modes/3204/GDI.JSON) |
| 640x200x4 | 94 | 12,032,000 | [6404rg/GDI.JSON](modes/6404rg/GDI.JSON) |
| 640x200x2 | 94 | 12,032,000 | [6402/GDI.JSON](modes/6402/GDI.JSON) |
| Total | 374 | 33,024,000 | All passed |

The Windows probe exercises full-width/edge rendering, pixel colors, compatible
DDBs, DIB imports and actual exports/readback, text, cursor restoration and
reduced-color raw aliases. `MODECHK.PY` decodes captured physical VRAM and
compares independently generated expected pixels; it does not use BIOS pixel
reads as the Windows oracle. Text glyph shape is compared to a memory-DDB
reference, while color and placement have independent checks. Its six-profile
self-test includes the earlier cyan/magenta 640x200 variant for historical data;
there are still only five current Setup choices.

[REBUILD.JSON](modes/REBUILD.JSON) also records the byte-identical builds,
27-object audits, unchanged baseline CPU/framebuffer checks, mode staging,
layout/cursor guards, color-contract tests and fail-closed command-line checks.
The mathematical color and Boolean-ROP checks are not additional Windows
runtime coverage. BIOS mode-0Ah raw write/padding checks pass, but the emulator's
raw BIOS pixel-read defect remains: 96,000 of 128,000 reads mismatch. This does
not contradict the independent Windows GDI passes.

### Native applications

![Native 640x200 four-color Solitaire, scan-doubled to 640x400](modes/6404rg/SOLITAIR.PNG)

The current [Solitaire capture record](modes/6404rg/CAPTURE.JSON) verifies all
seven columns, distinct red/black suits and a green table. The PNG is an
unmodified native 640x400 capture of logical 640x200, with duplicated rows.
This verifies startup/layout/color, not full-game playability.

Native Paintbrush **Save As** produced a 320x64, 4-bpp BMP with all four colors;
all **20,480 pixels** match exactly. [PAINT.JSON](modes/PAINT.JSON) records its
identities and comparison. A fresh C-only restart of the OEM-installed guest and native reopening of
that saved bitmap passed; see [COLD.JSON](modes/oem/COLD.JSON). The default candidate05's separately verified
24,000-pixel save/reopen result remains in [DIB88.MD](../src/tandysw/DIB88.MD).

### Packaging and native installation

The package passed **71 host checks and 26 DOS launcher checks**. Repeated
complete builds, compressed/expanded media and toolkit staging were identical.
[PACKAGE.JSON](modes/PACKAGE.JSON) and [DOS.JSON](modes/DOS.JSON) retain the exact
payload/guard checks. The final measured package uses **326,656 of 368,640 bytes**,
including FAT12 allocation rounding and overhead, leaving **41,984 bytes free**.
This is the final rebuilt ZIP measurement, including final packaged-text edits.

The installer tests use executable sentinels; native Windows Setup acceptance
is separate. [The native Setup result](modes/oem/RESULT.JSON) records the five
installed profiles and their 466-case / 38,912,000-pixel GDI checks. Its per-mode
`GDI.JSON`, `BOOT.JSON` and `RUN.JSON` records are in `modes/oem/6404`, `160`,
`3204`, `6402` and `baseline`. See the completed cold/reopen evidence above and
[OEMDISK.MD](OEMDISK.MD) for the actual installation checkpoint and historical
completed single-mode flows.

### Reproduce the checks

Build each profile with `BUILD88.PY --mode` as documented in
[BUILDING.MD](../BUILDING.MD). Use a new output directory for every build/run.
For oracle self-tests and packaging controls:

```sh
python3 src/tandysw/MODECHK.PY --selftest
python3 oemdisk/TESTDISK.PY
python3 oemdisk/TESTDOS.PY --dosbox /path/to/dosbox-x --out /new/dos-checks
python3 MAKEDISK.PY --verify TANDY88.ZIP
```

`MODECHK.PY` documents how to build MODETEST.EXE and run it in an isolated
own-media Windows 3.0 guest after RESERVE. For captured current 640x200
four-color output, for example:

```sh
python3 src/tandysw/MODECHK.PY /isolated/guest --profile 640x200x4 --out /new/GDI.JSON
```

Use the correct profile and phase mask for the recorded run; the 160x200
sixteen-color run uses `--phases 15`, while reduced-color alias coverage adds
phase 16. A decoder/self-test does not execute the driver or install Windows.

Tests use DOSBox-X 2026.08.31 SDL2 (September 28 nightly), `machine=tandy`,
`core=normal`, `cputype=8086_prefetch`, 640 KB and no EMS/XMS/UMB. In this build,
`8086_prefetch` enforces the ISA with a four-byte 8088 prefetch queue; CPU
semantic probes validate that behavior. **Do not use `cputype=8088`: it is
rejected and falls back to auto.** Build-tool memory configuration is not a
runtime compatibility claim; the actual driver guests use normal 640 KB.

## Limits and preserved history

- Physical EX/HX hardware and cycle-exact bus/CPU timing have not been tested
- Windows 3.0 real mode is the target; Windows 3.1 and standard/enhanced modes
  are outside acceptance
- `GetDIBits` with a NULL bits buffer is unsupported. Actual non-NULL exports
  and imports/readback are tested
- Current Windows runtime probes cover solid brushes, SRCCOPY and SRCINVERT,
  not every hatch/pattern brush or all 256 raster operations
- DIB limits still include RLE, top-down images and extended headers; consult
  the exact acceptance/rejection contract in DIB88.MD
- Reduced palettes deliberately quantize colors. Monochrome and CGA fonts do
  not promise sixteen-color fidelity or wider application compatibility
- Raw VRAM verifies pixel indices, not monitor RGB calibration. Native captures
  and BIOS palette programming provide separate palette evidence
- Full-screen software redraws can be slow. Emulator cycle settings do not
  establish real 8088 performance
- Native Windows host packaging-wrapper execution, genuine MS-DOS variants,
  broader memory layouts and exhaustive application behavior remain unverified

The original DOS-mode feasibility work stays in [ALTMODES.MD](ALTMODES.MD).
The `modes/6404/` cyan/magenta Windows checkpoint is experimental and historical;
it is not the current red/green driver in `modes/6404rg/`. Candidate05, original
OEM and custom-splash evidence are retained rather than rewritten to imply
that those older tests exercised the new modes.
