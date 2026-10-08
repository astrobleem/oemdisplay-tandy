# Tandy Start 14

Optional Windows 3.0 real-mode shell for 8086/8088 Tandy machines. Start imports
existing Program Manager groups, opens File Manager through My Computer, and
provides Run/Browse, About this Tandy, date/time controls and three screen savers.
The DOS launcher reserves display memory, selects the shell temporarily, then
restores the original shell on return. Its successful exit screen uses BIOS text
output and does not need ANSI.SYS.

## Current release

TSHELL.EXE is 68,451 bytes; TSINPUT.DLL is 6,281 bytes. Copy both when upgrading.
Version 14 adds optional Hold-to-Start. It retains version 13's reduced Browse
repainting, version 12's single Exit item with Shift-to-skip-chime, and version
11's validated read-only friendly names and 160-pixel System/date-time fixes.
[TESTS14.MD](TESTS14.MD) records exact identities and the scope of each test run.
Older MILESTONE, UPDATE and TESTS artifacts retain their original historical scope.

Current saver companions are [Matrix](../MATRIX/README.MD),
[Maze](../MAZE/SAVER10/README.MD) and [Starfield](../STARFLD/README.MD).
Their runtime, the DOS selector and sound companions are unchanged by 14.
Windows, fonts, ROMs, compilers and SDK libraries are not included.

## Install or upgrade

A complete fresh kit is documented in FRESH14/README.TXT. Its TSSETUP.BAT targets
C:\WINDOWS and keeps companions under the common C:\WINXT folder. It refuses an existing shell and
preserves both original Windows INIs. It does not install or select display,
keyboard or sound drivers. Do not use its fresh TSHELL.INI to overwrite an
existing setup.

For an installed version 10 or later, exit Windows and keep unused backup copies
of C:\WINDOWS\TSHELL.EXE and TSINPUT.DLL. Copy the current two files there,
then use your existing working TSTART launcher. Keep its path configuration,
INI files, recovery helper, RESERVE helper and companions. If Windows is in
another location, replace the active copies there. The DLL belongs beside the
Windows-directory shell. No INI replacement is needed.

For older installations, first supply the three current saver companions and
the current selector. Follow DOS/BATCH08.TXT for the narrow success-only FINISH
batch update, preserving configured paths. The complete fresh kit is a simpler
starting point for a new Windows installation.

The first-run Windows XT runtime in distributions/WINXT adds a bounded
[Programs] group from the Windows-directory TSHELL.INI. Existing executables
only are shown; full DOS paths and arguments are retained. The fresh disk
configures Matrix/Maze/Starfield /S, About and bundled Pinball v2. Existing
Program Manager groups remain read-only. Enter/Escape cancel the Exit dialog;
E selects Exit. The standalone 14 runtime/manifest and FRESH14 packet remain
historical; use the current disk for the matching first-run build.
See [first-run qualification](../../docs/FIRSTRUN.MD).

## Start and clock

My Computer opens or restores File Manager. Programs reads original Win3.0 PMCC
groups registered in PROGMAN.INI, Group1 through Group40, stopping at a gap.
Group files are read-only. Program Manager remains the editor; save it and reopen
Programs to refresh. Item arguments and executable working directories remain.
The group reader bounds occupied items, slots and command lengths and refuses
unsupported Windows 3.1 extension tags or ambiguous paths.

System offers About this Tandy and Screen saver settings. At 160 pixels it opens
a separate small menu so mouse selection works; wider modes use native cascades.
Double-click the bar clock to open Clock or Calendar. Right-click the clock to
adjust the DOS date/time explicitly. Apply validates and rereads the result;
Cancel does not change it. The sub-tick DOS rounding correction does not change
stock Clock's drawing speed.

## Long filename browsing

Start > Run > Browse displays **existing long filenames**, including spaces,
by reading names already stored as VFAT entries on supported fixed local
FAT12/FAT16 volumes with 512-byte sectors under genuine DOS 6.22 and Windows
3.0 real mode. The shell installer's DOS 3.3+ minimum does not qualify raw reads
on those older DOS versions. FAT32 and emulator host-folder mounts are outside
this verified volume domain. It uses bounded
one-sector reads between message-loop turns and never writes filesystem metadata.
DOS enumeration remains authoritative. Navigation and launch always use the
existing short alias, shown separately; arguments and working directories remain.
It does not create or rename long names, change other programs' file dialogs, or
invent aliases. Type short DOS paths in Run.

Listings above 128 filtered rows, unsupported non-ASCII names, corrupt or
ambiguous entries, exhausted limits, memory/read errors and unsupported drives
retain short names. Validated names above 63 display characters use an ellipsis.
Network, removable, SUBST, JOIN and resident ASSIGN paths are refused. A detected
Microsoft DriveSpace service disables raw reading; other compression products are
outside the verified domain. A stale long entry can survive a legacy DOS edit,
so identify the file by its visible short alias. Cancel remains available during
reading. Version 13 batches list updates to reduce repeated painting.

## Screen savers

Start > System > Screen saver chooses Matrix, Maze, Starfield or None. Delay is
10 to 3600 seconds; 300 means five minutes. Apply saves and updates the primary
shell. Preview tries unsaved choices. Cancel discards unapplied edits. Starfield
Options chooses speed 1/2/3 and 16/32/64 stars. These are visual effects, not locks.

Only the primary shell owns idle observation. Input in other apps resets the
interval. Menus, modal dialogs, capture, held input, startup/audio activity and
shutdown suppress idle launch. Untouched boot waits for the first input gesture.
DOS or scheduling interruptions require fresh input and another interval. A
secondary bar can Preview and saves choices for the next primary startup.
The savers drain held wake gestures and restore focus only while they still own
activation. Maze's safe GDI fallback can be very slow on an 8088.

The existing Windows-directory TSHELL.INI is preserved. The retained base
configuration uses C:\TSTART\MATRIX.EXE, MAZE.EXE and STARFLD.EXE; the fresh
WINXT configuration points these companions to C:\WINXT instead. Paths use Program,
MazeProgram and StarProgram under [ScreenSaver]. Choice, Enabled and IdleSeconds
are saved there; Speed and Stars live under [Starfield]. Full DOS 8.3 paths are
required. An unconfigured shell leaves idle saving disabled until Apply.

## Sounds and exit

[Sounds] selects XP, TANDY or NONE startup and optional ExitChime. Only the actual
selected shell runs the startup sequence. Supported WIN.INI load/run entries are
bounded space-separated executable/PIF names. Duplicate chimes are suppressed;
the selected sound finishes before other startup apps. Opening Program Manager
later does not replay the sequence.

Exit Windows is the single exit item. Hold Shift while selecting it to skip the
chime; the choice is captured before confirmation. Confirmation and unsaved-file
prompts still apply. TEXIT /go plays before Windows queries other apps, so an app
can veto shutdown after the sound. Known PSG conflicts are refused; unknown sound
writers and non-yielding tasks cannot be guaranteed. The Tandy chime apps use PSG
directly and do not require installation of a Windows sound driver.

After a crash or reset, run SHELLSEL RECOVER with the full SYSTEM.INI path before
starting Windows. TSTART does this automatically. Keep journal sidecars until
recovery succeeds. The selector changes only the shell entry, preserving current
display and keyboard settings. Never restore a stale whole INI over new drivers.

## Hold-to-Start

Press and release plain Hold to open Start over another app. Escape restores its
prior focus. Repeats and a second Hold while Start is open do not select an item.
Shift/Ctrl/Alt combinations keep their original behavior; Ctrl+Hold is not remapped.
Standard modal dialogs, savers and shutdown take priority. Waking a saver with Hold
does not immediately open Start.

Automatic enabling requires the supported real-mode Tandy ROM profile and an
actually loaded TNDYK3.DRV keyboard driver. That separately supplied compatible
kit has its own guarded installer/rollback. With the stock driver the Start button
works normally. [Keyboard] HoldStart=0 disables the shortcut. Explicit 1 opts into
another driver within the supported profile, but generic modifier changes can
produce mismatched make/break virtual keys. Prefer the compatible driver.

Ordinary removed/dispatched Hold messages are consumed. Programs peeking without
removing input or polling Scroll Lock state can still observe it. Stale gestures
are discarded. Custom modal loops cannot always be identified. Hooks post work to
the shell instead of displaying UI in callbacks; unsuccessful detach retains inert
code rather than freeing an active hook. Physical Windows Hold behavior remains
pending; emulator testing is not a physical performance claim.

## Build and portable checks

Use your licensed MSC6/Windows 3.0 tools. The helpers do not download them:

    python3 examples/TSHELL/BUILD.PY --repo TOOLCHAIN --dosbox DOSBOX --out NEWDIR
    python3 examples/TSHELL/IDLE/BUILD.PY --toolchain TOOLCHAIN --dosbox DOSBOX --out OTHERDIR

The shell uses /G0 /Gw /AS /W3 /Od and LINK4, then marks the resource-free NE target
for Windows 3.0. The fixed DLL has no CRT or local heap. Its build also creates
optional IDLEPROB and HOLDPROB test apps; neither is installed.
From IDLE, compile tests/HOSTTEST.C and tests/HOLDTEST.C with a C89 host compiler,
then run them. VERIFY.PY checks the real NE DLL segment/import/export contract.
Retained TESTS/RUNHOST.PY, TESTS/DATE/RUN.PY, TESTS/CONFIG/RUN.PY and DOS selector
checks cover their documented scopes. Additional exact-source Browse/parser tests
are supplied with the release source archive. Native DOS/Windows fixtures are
private licensed inputs and are not redistributed.
