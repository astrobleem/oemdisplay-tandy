# Tandy Start 09

Optional Windows 3.0 real-mode shell for 8086/8088 Tandy machines. Programs
reads existing Program Manager groups; Run/Browse, startup sound selection
and normal or silent exit remain available. Version 07 added a compact
date/time editor. Version 08 added My Computer directly under Start and
success-only DOS moon/stars artwork. Version 09 corrects popup placement
so Start opens directly above its bar.

The optional Matrix idle saver observes input across Windows applications.
It is not a password lock. Saver selection is configured through TSHELL.INI;
there is no graphical screensaver chooser in this version.

## Current files and history

TSHELL.EXE is the current 35,907-byte shell. DOS/SHELLSEL.EXE is the unchanged
25,953-byte success-only FINISH helper from 08. TSINPUT.DLL remains 3,082 bytes
and ../MATRIX/MATRIX.EXE remains 14,157 bytes, both unchanged from 06. Exact
SHA-256 identities and measured limits are in TESTS.MD.

Historical MILESTONE.ZIP, MANIFEST.JSON and pre-06 EVIDENCE remain unchanged;
they do not describe current runtime files. TESTS06.MD and TESTS08.MD retain
earlier qualification without claiming it was rerun on 09. No OS, SDK,
compiler, ROM, donor-media or test-control binaries are added.

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
    python3 examples/TSHELL/TESTS/DATE/RUN.PY
    python3 examples/TSHELL/DOS/TESTSEL.PY
    python3 examples/TSHELL/DOS/TESTNITE.PY

Build the DOS selector separately using DOS/BUILD.BAT with the
owned C:\BIN, C:\INCLUDE and C:\LIB layout. It uses /G0 /AS and DOS SLIBCE,
without Windows startup/runtime. See DOS/README.TXT for full first-install
and interruption-recovery details.

## Upgrade an existing installation

Exit Windows completely and preserve unused backup copies before replacing
files. Keep all installed TSHELL.INI choices, custom paths, display drivers,
RESERVE.COM and sound companions.

- From 08: replace only TSHELL.EXE in the actual Windows directory.
- From 06/07: replace TSHELL.EXE and SHELLSEL.EXE, then apply the exact
  post-WIN block in DOS/BATCH08.TXT. Install the new helper first. Preserve
  every SET path and all other batch bytes; do not overwrite a configured
  TSTART.BAT with the source template. No INI change is required.
- From 05 or earlier: first follow UPDATE06.TXT for TSINPUT.DLL, the Matrix
  /S companion and optional ADDON.INI keys, preserving existing settings,
  then apply the 06/07 steps above. Use the current TSHELL.EXE throughout.

About This Tandy, Clock/Calendar and File Manager must already be installed
separately. My Computer opens WINFILE.EXE or restores/activates its existing
window; it does not bundle or rewrite File Manager. A missing app produces
a compact notice. Program Manager remains the group editor.

The right-click clock editor validates 1980..2099 dates and 24-hour times.
Apply changes only edited fields. Cancel, Escape and closing without Apply
do not set the clock. Reload reads the current values. Failed or unverifiable
partial changes require Reload before another Apply; no silent rollback is
attempted. Double-click still opens Clock, with Calendar as fallback.

Use the existing working TSTART command with its configured reservation path.
A fresh installation must configure DOS batch paths against its accepted
RESERVE.COM; C:\TANDY88\RESERVE.COM is only a template default. Never bypass a
failed reservation. Manual SHELLSEL SELECT is not the complete procedure.

TSTART recovers interrupted selection, reserves video memory, selects TSHELL,
runs WIN /R, then restores the original shell. Immediate nonzero ERRORLEVEL
uses plain RECOVER. A zero return uses FINISH, which draws its farewell only
after reread verification and journal cleanup. It leaves a usable DOS prompt;
it does not power off or require ANSI.SYS. All error/recovery paths stay plain.

After interruption, run RECOVER before starting Windows; retain journal and
backup sidecars on conflict. Never copy TSHELL.BAK over a current SYSTEM.INI.
See DOS/README.TXT for installation and conservative recovery details.

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

