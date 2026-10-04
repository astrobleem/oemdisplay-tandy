# Display development status and evidence

This page separates development builds, historical packages, emulator evidence
and physical observations. The public README is a feature showcase; it does
not imply that every listed app, mode or recent update is hardware-qualified.

## Driver and package identities

The current drawing pipeline includes the 8088 copy correction and bounded
Output-row refresh. Historical TANDY88.ZIP binaries and exact packaging pins
remain unchanged and predate that correction. The physically tried TRIAL 3
monochrome fallback differs from the final Output-row monochrome build.
Use the [trial guide](TRIAL4/README.MD), [binary identities](TRIAL4/BUILDS.JSN)
and [measured verification scope](TRIAL4/VERIFY.TXT). A successful build does
not update the accepted package or justify relaxing its pins.

Unknown drawing bounds retain full refresh. Cursor overlap uses synchronous
hide/restore, and identity screen copies retain full resynchronization. No
general deferred conversion or asynchronous GDI flush is claimed.

## Shell update status

Tandy Start 09 source and matching runtime files are included in this branch.
It adds corrected Start-menu placement to version 08, which includes version
07's right-click clock date/time editor and **My Computer directly under Start**.
My Computer launches or restores File Manager; there is no extra submenu.

The date/time editor validates calendar dates (1980–2099) and 24-hour times.
Apply changes only edited values. Reload, Cancel, Escape and closing without
Apply do not set the clock. Native controls fit the 160-pixel desktop.

After a zero Windows return, SHELLSEL FINISH verifies shell restoration and
journal deletion before drawing the moon/stars farewell using BIOS text colors.
No ANSI.SYS, key wait or power-off is required. Nonzero Windows returns, manual
RECOVER, missing journals and failed restoration retain plain diagnostics.

For an installed 08, exit Windows and replace only TSHELL.EXE after backing
it up. For 06/07, also replace SHELLSEL.EXE and apply the exact
[BATCH08.TXT](../examples/TSHELL/DOS/BATCH08.TXT) post-Windows block.
Preserve every custom SET path and all other launcher content. The two EXEs
alone are not the full 06/07 upgrade. TSINPUT.DLL and MATRIX.EXE are unchanged
from 06; no INI change is required for an installed 06/07/08. The
[component guide](../examples/TSHELL/README.MD) covers older installations.

[Current verification](../examples/TSHELL/TESTS.MD) identifies the exact 09
checks, separately from [retained 08 evidence](../examples/TSHELL/TESTS08.MD).
The 08 suite included ten native Windows cases, 210 recovery assertions and
genuine DOS 6.22 emulator exit/veto/error/failure checks. Error-return and
read-only-journal failures used clearly labeled WIN.COM stand-ins, not every
possible Windows failure. Earlier tests are not relabeled as 09 reruns.
No exact-binary physical acceptance of 09 is claimed.

TSHELL 09 build01 is 35,907 bytes, SHA-256
`ad3c8394b3391939f19e2a1cf282d89701fe46397a4ce5c4c7a312f37c6babe6`.
Unchanged 08 SHELLSEL (success-only FINISH) is 25,953 bytes, SHA-256
`6aa652c9fc77e2e05944b46c055157e97b88a10b963135a4aecf5a01fa71c2fd`.

Programs import is read-only; Program Manager remains the group editor.
Maximized apps can cover the bar. An application taskbar is only proposed,
not implemented. The global Matrix idle saver is not a lock, and cooperative
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

For **current trial drivers**, use [TRIAL4's guide](TRIAL4/README.MD),
preserve the known-working monochrome fallback and follow its exact overlay
and rollback contract. Trial overlays are not complete OEM disks.

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

Inspect `RESULT.json` and the [development binary identities](TRIAL4/BUILDS.JSN).
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
