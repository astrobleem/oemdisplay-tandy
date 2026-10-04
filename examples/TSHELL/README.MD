# Tandy Start 06

Optional Windows 3.0 real-mode shell for 8086/8088 Tandy machines. Programs
reads existing Program Manager groups; Run/Browse, startup sound selection
and normal or silent exit remain available. Version 06 adds Start / System /
About This Tandy, clock-area double-click launching Clock (or Calendar), and
an optional Matrix idle saver observing input across Windows applications.
The saver is not a password lock. New features still need physical testing.

## Current files and history

TSHELL.EXE is the current 29,555-byte shell; TSINPUT.DLL is its 3,082-byte
input observer. The current 14,157-byte Matrix /S companion is at
../MATRIX/MATRIX.EXE. Exact SHA-256 values and measured limits are in TESTS.MD.
The historical MILESTONE.ZIP, earlier MANIFEST.JSON and existing EVIDENCE
files describe older builds. They are retained as history, not as the source
of the current executables. See HISTORY.TXT. No OS, SDK, compiler, ROM,
donor-media or test-control binaries are supplied by this update.

## Build and portable checks

Use an existing licensed Microsoft C 6.0 and Windows 3.0 toolchain:

    python3 examples/TSHELL/BUILD.PY --repo <toolchain-root> --dosbox <dosbox-x> --out <new-build-directory>
    python3 examples/TSHELL/IDLE/BUILD.PY --toolchain <toolchain-root> --dosbox <dosbox-x> --out <another-new-directory>
    python3 examples/MATRIX/SOURCE/BUILD.PY --repo <toolchain-root> --dosbox <dosbox-x> --out <another-new-directory>

The shell uses /G0 /Gw /AS /W3 /Od and segmented LINK4, then marks the
resource-free NE module for Windows 3.0. The DLL uses /G0 /Gsw /ASw /Zp /W3
/Od, a fixed 8086 assembly entry point, no CRT, and no local heap. Its build
also creates the optional IDLEPROB test app; that app is not installed.
Build helpers do not download the compiler, SDK or emulator.

Run portable host checks with Python 3 and GCC:

    python3 examples/TSHELL/TESTS/RUNHOST.PY

Build the unchanged DOS selector separately using DOS/BUILD.BAT with the
owned C:\BIN, C:\INCLUDE and C:\LIB layout. It uses /G0 /AS and DOS SLIBCE,
without Windows startup/runtime. See DOS/README.TXT for full first-install
and interruption-recovery details.

## Upgrade an existing installation

Exit Windows completely before copying files. Preserve TSHELL.EXE,
TSHELL.INI, TSINPUT.DLL and the target MATRIX.EXE in unused backup names.
Copy TSHELL.EXE and TSINPUT.DLL to the actual Windows directory, and copy
the current Matrix /S variant to C:\TSTART\MATRIX.EXE. Adapt paths to the
installation. Keep any separate on-demand Matrix installation unchanged.

Merge the keys from ADDON.INI into the existing TSHELL.INI, preserving
Sounds and Startup settings. Never replace an installed TSHELL.INI with
ADDON.INI. The TSHELL.INI in this source folder remains the base example;
missing ScreenSaver settings mean disabled. Use UPDATE06.TXT for copy-by-copy
upgrade instructions. About This Tandy and Clock/Calendar must already be
installed separately; Apps/System selects the About executable path.

Use the existing working TSTART command and preserve its configuration and
reservation path. This upgrade does not replace TSTART.BAT, RECOVER.BAT, SHELLSEL.EXE,
RESERVE.COM or sound companions. A fresh installation must configure DOS
batch paths against its existing accepted RESERVE.COM. C:\TANDY88\RESERVE.COM
in the source batch is only a configurable default. Never bypass a failed
reservation. Manual SHELLSEL SELECT is not the complete launch procedure.

TSTART recovers prior interrupted selection, reserves video memory, selects
TSHELL, runs WIN /R, then restores the original shell after any return.
After interruption, run RECOVER before starting Windows; retain journal and
backup sidecars on conflict. Never copy TSHELL.BAK over a current SYSTEM.INI.

## Optional idle saver

Enable it through ADDON.INI. IdleSeconds accepts 10..3600; 300 is five minutes.
TSHELL supplies /S to the configured Matrix executable. Only the selected
TSHELL shell installs the global observer; an ordinary secondary bar does not.
A completely untouched boot waits until the observer sees genuine input.
After DOS suspension or exceptional resynchronization, complete a new key or
button gesture, then a full idle interval. Menus, dialogs, held input,
capture, startup helpers and known audio tools defer automatic launch.

The fixed-code WH_JOURNALRECORD hook only records activity and held state in
memory and chains the prior hook. It performs no I/O, yields or UI work.
The owner task compares DOS INT 21h/AH=2Ch time with GetTickCount to detect
suspended Windows time. Ordinary polls do not call GetAsyncKeyState; initial
and exceptional physical baselines do clear that API's shared low bits.

Matrix /S drains the wake gesture until release while it owns focus/capture,
then restores the prior app. Forced deactivation/shutdown releases ownership
without stealing it back. Cooperative Windows cannot guarantee progress if
another task never yields, or swallow input after focus/capture is lost.

## Programs and startup

Programs reads original Win3.0 PMCC groups registered in PROGMAN.INI Group1
through Group40, stopping at a gap as Program Manager does. Limits are 50
occupied items, 64 allocated slots and 126-character command lines. Invalid
files and Windows 3.1 extension tags are refused. No group file is written.
Use Program Manager to edit groups; save it and reopen Programs to refresh.
Saved arguments and executable working directories are retained. Full DOS
paths or bare executable names are supported; ambiguous relative/space paths
are refused. Run/Browse retains the original direct-command behavior.

TSHELL.INI selects XP, TANDY or NONE startup sound and optional exit sound.
The actual selected shell alone processes startup. Supported WIN.INI load/run
entries are bounded space-separated executable/PIF filenames, without custom
argument syntax. Duplicate startup chime entries are suppressed, helpers
finish before other startup apps launch, and unsafe entries are reported.
Opening Program Manager later does not replay the selected startup sequence.

TEXIT /go plays before Windows asks other apps to save/exit. A veto leaves
Windows open, possibly after the sound played. Silent exit remains available.
Known PSG ownership conflicts cause refusal; unknown writers and non-yielding
tasks cannot be guaranteed. The bar is not an Explorer replacement: maximized
apps can cover it, and Alt+Tab returns to it. No desktop icons or task tray.

See TESTS.MD for measured evidence and limits.
