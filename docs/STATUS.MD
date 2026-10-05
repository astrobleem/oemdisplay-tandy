# Display development status and evidence

This page separates development builds, historical packages, emulator evidence
and physical observations. The public README is a feature showcase; it does
not imply that every listed app, mode or recent update is hardware-qualified.

## Driver and package identities

The current TR5 drawing pipeline extends the bounded Output-row gate to
validated multi-interval OS_SCANLINES calls. It preserves the original renderer
and full-refresh fallback for uncertain cases. See the
[TR5 source and build guide](TRIAL5/README.MD), [binary identities](TRIAL5/BUILDS.JSN)
and [paired verification](TRIAL5/VERIFY.TXT).

The [unified own-media installation](../distributions/WINXT/README.MD) offers five
TR5 graphics choices and a separately labeled experimental hardware-text choice.
It shares C:\WINXT with TSTART companions. Microsoft support files are supplied
from the user's licensed media and verified during host assembly; they are not
included in the public overlay. Installation, mode switching and rollback have
their own [qualified scope](UNIFIED/README.md).

Historical TANDY88.ZIP binaries and exact MAKEDISK pins remain unchanged. The
physically tried TRIAL 3 monochrome fallback differs from the new TR5 monochrome
bytes. The previous [TRIAL4 guide](TRIAL4/README.MD) remains historical evidence.
A successful development rebuild does not change an old accepted package.

Unknown drawing bounds retain full refresh. Cursor overlap uses synchronous
hide/restore, and identity screen copies retain full resynchronization. No
general deferred conversion or asynchronous GDI flush is claimed.

## Current shell and Windows XT additions

Tandy Start 14 includes the 11 friendly-name browser, the narrow-desktop System
menu repair, 12 single Exit item with Shift-to-skip-chime, 13 reduced Browse
redraws and 14 guarded Hold-to-Start support. Source and matching runtimes are
published together. Friendly-name lookup is read-only; launches retain DOS
aliases and unsupported metadata falls back to short names.

Current runtime SHA-256 identities:
- TSHELL.EXE, 68,451 bytes:
  `4577182c8ba80f3604867710c44403f61c7e684f01cdc4d45e1e6dc92ef74689`.
- TSINPUT.DLL, 6,281 bytes:
  `d14dde571906bdd27a95030f11647333016eb34864afd22c08c5d2cf80660a80`.

See [cumulative changes and verification](../examples/TSHELL/TESTS14.MD),
[upgrade instructions](../examples/TSHELL/README.MD) and the separate
[fresh installation](../examples/TSHELL/FRESH14/README.TXT). Replace both
matching shell and helper when upgrading; preserve configured INI/batch files.
The saver binaries and historical accepted display-package pins are unchanged.

[Keyboard candidate](../src/tandyk3/README.md) includes first-party patches,
probes and a guarded installer, alongside the DDK-derived runtime with its
attribution/rights notice. Seventeen physical raw press/release pairs matched;
Windows translation, modifier behavior and Hold-to-Start are not physically
qualified. Hold-to-Start defaults to the supported real-mode Tandy ROM and
actually loaded compatible driver. It is not a general Scroll Lock override.

The [splash-only updater](../examples/WXTSPL/README.TXT) preserves display
components and unrelated settings. [Hill wallpaper](../examples/HILLS/README.TXT)
uses normal Windows desktop handling with measured bitmap-memory cost.
[XTEyes](../examples/XTEYES/README.TXT) is an original bounded GDI pointer toy.
Each component records its native emulator coverage and physical limits.

Physical reports confirm friendly-name browsing and all three selectable savers,
with Maze slow. The later Browse redraw changes and new Hold behavior have no
instrumented physical acceptance. Emulator cycle presets are not physical MHz.

## Retained Tandy Start 10 snapshot

The following documents the earlier 10 delivery. Its hashes, upgrade recipe
and test evidence are historical; use the current guides above for 14.

Tandy Start 10 source and matching first-party runtimes are included in this
branch. Start / System / Screen saver offers None, Matrix, Maze and Starfield,
a 10..3600-second delay, Apply and unsaved Preview. Starfield Options selects
speed 1/2/3 and 16/32/64 stars. Cancel discards unapplied choices. Only the
primary shell updates automatic idle immediately; a secondary bar saves for
the next primary startup and can Preview without installing another hook.

Maze keeps the native path for canonical drivers and uses clipped GDI on
trial aliases/other supported identities. It remains very slow. Starfield
uses GDI on every driver; 16 stars is lightest. Neither is a password lock.

The 09 Start placement fix, 08 My Computer/FINISH and 07 date/time editor
remain. My Computer opens or restores File Manager directly from Start.

The date/time editor validates calendar dates (1980–2099) and 24-hour times.
Apply changes only edited values. Reload, Cancel, Escape and closing without
Apply do not set the clock. Native controls fit the 160-pixel desktop.

After a zero Windows return, SHELLSEL FINISH verifies shell restoration and
journal deletion before drawing the moon/stars farewell using BIOS text colors.
No ANSI.SYS, key wait or power-off is required. Nonzero Windows returns, manual
RECOVER, missing journals and failed restoration retain plain diagnostics.

From installed 08/09, exit Windows, back up and replace TSHELL.EXE, then
copy the current MAZE.EXE and STARFLD.EXE to the configured saver directory
(normally C:\TSTART). Keep your INI and batch. Earlier installations also need
the preserved input observer/Matrix and, for the DOS artwork, the exact
[BATCH08.TXT](../examples/TSHELL/DOS/BATCH08.TXT) helper upgrade.
See the [component guide](../examples/TSHELL/README.MD); never overwrite a
configured launcher or bypass the shared-memory reservation.

[Version 10 verification](../examples/TSHELL/TESTS.MD) separates fifteen
integrated cases using TSHELL 05/Maze 12/Starfield 08 from three fresh targeted
runs after the final Starfield 10 cursor correction. Earlier 06/08/09 evidence
remains historical. No full old suite or physical acceptance is claimed anew.

Version 10 SHA-256 identities:
- TSHELL.EXE, 48,547 bytes:
  `d87142ac16b615dc1a696976478db2596030b3d4b61e445eb48f2f84aa893cfa`.
- MAZE.EXE, 23,215 bytes:
  `c8dac5dd6c8b6c9c0c6fb8727dd56919e9c0fd5a71fa63b30c429f4be2c3598a`.
- STARFLD.EXE, 16,783 bytes:
  `e06c9d80f977e1bda1db2d13be8af5f7d8b6f00285daa4f0e0159af00211b8d0`.
Matrix, TSINPUT, SHELLSEL and the post-WIN block remain unchanged.

Programs import is read-only; Program Manager remains the group editor.
Maximized apps can cover the bar. An application taskbar is only proposed,
not implemented. The global idle saver is not a lock, and cooperative
Windows cannot guarantee progress while another task blocks.

## Physical hardware reports and remaining limits

Recent reports come from a genuine 8088 Tandy 1000 EX with DOS 6.22 and Windows
3.0 real mode. They are user observations, not calibrated benchmarks or a
complete compatibility matrix:

| Area | Reported status |
| --- | --- |
| TRIAL 3 640x200x2 | Substantially faster; the applications tried were usable. Exact final Output-row monochrome bytes are a separate development build. |
| Later 320x200x16 trial | Paintbrush and TSHELL loaded and worked; still slow. |
| Low-resolution 16-color | Operation reported working; exact mode unconfirmed. Broad app/lifecycle coverage remains open. |
| 320x200x4 | Operation reported working, with red hearts mapping to black. |
| 640x200x4 | Physical behavior unconfirmed; emulator success cannot settle the hardware-model uncertainty. |
| Shell and automatic saver | Automatic screensaver operation was reported working on the user's Tandy on 2026-10-04; the exact runtime hash was not read back. Every control, idle-hook edge case and later build still needs separate acceptance. |
| Joystick input | Physical stick/port behavior remains unverified. |

The [experimental verification record](TRIAL4/VERIFY.TXT) scopes the
driver observations. Historical documentation can correctly say that its
older checkpoint lacked hardware testing; that does not describe every later
trial. Reports without post-install hash readback do not certify exact binaries.

Windows 3.0 real mode and normal 640 KB shared memory are the target. Windows
3.1, standard/enhanced modes, PCjr, other memory layouts and an unexpanded
256 KB EX are outside acceptance. Bitmap/ROP coverage is bounded; large redraws
can remain slow. Emulator cycle settings do not establish physical 8088 speed.

## Install, build and verify

For the **current public WINXT kit**, use the
[unified own-media installation guide](../distributions/WINXT/README.MD)
and [full installation and rollback instructions](../distributions/WINXT/README.TXT).
It combines five TR5 graphics choices, experimental text and optional Tandy
Start 14 in one support folder. The [TR5 guide](TRIAL5/README.MD) covers
source builds and scoped driver verification. Preserve the separately tried
TRIAL 3 monochrome fallback; it is not the new TR5 monochrome binary.

For **historical OEM package reproduction**, start with backed-up stock-CGA
Windows 3.0, extract [TANDY88.ZIP](../TANDY88.ZIP), run `INSTALL` from `DISK1`,
then `C:\TANDY88\TANDY88 SETUP`. Select Display > Other display and the profile.
Launch through `C:\TANDY88\TANDY88` on every boot. Never bypass a failed memory
reservation with a direct `WIN` command. [Full installation instructions](../README.TXT).

Developer builds use Python 3 to orchestrate DOSBox-X and the existing licensed
period assembler/linker/DDK inputs. Every output directory must be new:

```sh
python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/build --mode 320x200x16
```

Inspect `RESULT.json` and the [development binary identities](TRIAL5/BUILDS.JSN).
The existing package pins deliberately reject unaccepted new builds. Do not
replace them simply because compilation succeeds. See [BUILDING.MD](../BUILDING.MD),
[mode evidence](MODES.MD), [OEM evidence](OEMDISK.MD) and
[source provenance](../src/tandysw/PROVENANCE.md) for reproduction and limits.

Runtime evidence uses normal 640 KB, no XMS/EMS/UMB workaround and enforced
8086/8088 semantics. The documented DOSBox-X build uses `8086_prefetch`;
`cputype=8088` is rejected there and falls back to auto. Runtime checks,
hardware acceptance, packaging checks and GitHub CI are separate results.

Contributions and hardware testing are welcome. Include the driver/app hash,
machine, DOS/Windows versions, reproduction steps and whether a result came
from hardware or emulation. Preserve existing third-party notices and publish
only appropriate project source/assets, not full OS installations or toolchains.


## Input diagnostic development

[Draft PR 80](https://github.com/astrobleem/oemdisplay-tandy/pull/80) supplies
the bounded DOS WHEEL diagnostic, source, build instructions and tests. Raw
Genius serial-wheel data has been detected on hardware. This does not provide
a Windows scrolling bridge, general mouse-driver support or broad hardware
qualification. Review its own consent, capture and restoration instructions.

## Screenshot provenance

[Capture sources and SHA-256 identities](SHOTS/README.MD) distinguish historical
frames from current functionality. All showcase PNGs are byte-identical copies
of existing emulator evidence, not new runtime tests or physical photographs.
Screenshots do not prove timing, audio or full application behavior. Source
revisions and exact per-asset paths are recorded there.
