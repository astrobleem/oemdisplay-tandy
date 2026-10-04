# Tandy Start 10

Optional Windows 3.0 real-mode shell for 8086/8088 Tandy machines. Version 10
adds Start / System / Screen saver: Matrix, Maze, Starfield or None, delay,
Apply and unsaved Preview. Starfield Options offers three speeds and
16/32/64 stars. Earlier Start, date/time, My Computer and DOS FINISH features
remain. These visual effects are not password locks.

## Current files and history

TSHELL.EXE is 48,547 bytes. Current Maze saver is at
[../MAZE/SAVER10](../MAZE/SAVER10/README.MD); current Starfield is at
[../STARFLD](../STARFLD/README.MD). Matrix, TSINPUT.DLL, DOS/SHELLSEL.EXE and
the DOS batch block remain unchanged. TESTS.MD records all exact identities.

MILESTONE.ZIP, MANIFEST.JSON, UPDATE09.MF and earlier EVIDENCE/TESTS06/08/09
files retain their original historical scope. They do not identify current
10 runtime files. No OS, SDK, compiler, ROM or test-control binary is added.

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
    python3 examples/TSHELL/TESTS/CONFIG/RUN.PY
    python3 examples/TSHELL/DOS/TESTSEL.PY
    python3 examples/TSHELL/DOS/TESTNITE.PY

Build the DOS selector separately using DOS/BUILD.BAT with the
owned C:\BIN, C:\INCLUDE and C:\LIB layout. It uses /G0 /AS and DOS SLIBCE,
without Windows startup/runtime. See DOS/README.TXT for full first-install
and interruption-recovery details.

## Settings, upgrade and input safety

USING THE SETTINGS
- Choose a saver and an idle delay in seconds. 300 means five minutes.
  The supported range is 10 to 3600 seconds.
- Apply saves the choices and updates the primary shell immediately.
- Preview tries the selected saver without saving. A key or mouse gesture
  dismisses it and returns to the settings window. Held wake input is drained
  before the underlying app receives input.
- Starfield / Options chooses speed 1 (slow), 2 (normal), or 3 (fast), and
  16, 32, or 64 stars. Press OK, then Apply in the main settings window to
  save. Preview can try the new options before Apply.
- Cancel, Escape, or closing either dialog discards that dialog's unapplied
  choices. An earlier explicit Apply remains saved.
- None disables the automatic idle saver. The normal default is Matrix with
  a five-minute delay if that is already configured. An unconfigured shell
  starts with automatic saving disabled until you choose and Apply.
- A secondary bar launched from Program Manager saves for the next primary
  shell startup. It can Preview, but does not install another idle observer.

UPGRADE FROM INSTALLED 08 OR 09
Exit Windows. Preserve unused backup copies of the existing files first.
Stage this folder's TSHELL.EXE, ../MAZE/SAVER10/MAZE.EXE and
../STARFLD/STARFLD.EXE in C:\TSUPD10 on the DOS machine, then copy:

COPY C:\TSUPD10\TSHELL.EXE C:\WINDOWS\TSHELL.EXE
COPY C:\TSUPD10\MAZE.EXE C:\TSTART\MAZE.EXE
COPY C:\TSUPD10\STARFLD.EXE C:\TSTART\STARFLD.EXE

Use your existing working TSTART command. No INI or batch edit is needed for
this upgrade. Open Start / System / Screen saver to choose the saver.
If your existing setup uses different paths, keep that arrangement and
replace the copies it already uses. Custom saver program paths are preserved.
The original on-demand Maze elsewhere is not replaced by these instructions.

FROM INSTALLED 05, 06 OR 07
Keep the existing launcher, RESERVE helper, recovery files, sound companions,
and all working path settings. Back up each destination before replacement.
Copy TSHELL.EXE and TSINPUT.DLL to C:\WINDOWS. Copy MATRIX.EXE, MAZE.EXE and
STARFLD.EXE to C:\TSTART. Then use the new settings dialog; manual INI editing
is unnecessary for the default paths. Existing Sounds/Startup settings stay.

For the retained moon-and-stars DOS shutdown screen, also copy SHELLSEL.EXE
over the helper your launcher uses and follow DOS/BATCH08.TXT's exact post-WIN
block edit once. Preserve every configured SET/path line. Do not overwrite
your whole working batch file. If that edit was already applied for 08/09,
leave it alone. No default replacement TSTART.BAT is supplied here.

SPEED AND DISPLAY NOTES
Maze keeps its ordinary windowed demo when launched without /S. Its saver
uses the known canonical drivers' native path, and a safe clipped GDI path
for trial aliases and other compatible 160/320/640 by 200 displays. A driver
replacement is not required. The fallback paints progressively and can be
very slow on an 8088. Matrix remains a good choice if Maze is too slow.

Starfield draws through GDI on every driver. 16 stars is the lightest choice;
64 gives more stars but slower per-star updates. The default is speed 2 and
32 stars. Emulator verification does not establish physical Tandy speed.
These savers are visual effects, not password locks.

IDLE AND INPUT SAFETY
Only the selected primary TSHELL owns the global input observer. Input in
other Windows apps resets the delay. Menus, modal dialogs, held input,
capture, system-modal activity, startup sounds, known sound apps, and pending
shutdown suppress automatic launch. An already running saver program blocks
duplicates. DOS/scheduling interruptions require fresh input and a new idle
interval. A completely untouched boot waits for its first input gesture.
The components consume their wake gesture, restore focus only while still
owning activation, and yield control between bounded rendering slices.

ADVANCED PATHS (OPTIONAL)
The existing Windows-directory TSHELL.INI is retained. Default program paths:
[ScreenSaver]
Program=C:\TSTART\MATRIX.EXE
MazeProgram=C:\TSTART\MAZE.EXE
StarProgram=C:\TSTART\STARFLD.EXE

The chooser saves Enabled, IdleSeconds, and Choice. Choice is Matrix, Maze,
or Starfield; None writes Enabled=0 while retaining Choice. Starfield Options
save Speed and Stars under [Starfield]. The chooser leaves custom paths and
unrelated INI keys intact, checks readback, and reports failed saves.
Full DOS 8.3 paths without spaces are required. An unusually long StarProgram
may fit idle launch but be refused for Preview when its option arguments
would exceed the launcher's 126-character command limit.


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


