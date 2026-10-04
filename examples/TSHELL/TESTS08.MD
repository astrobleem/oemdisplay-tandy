TANDY START 08 - VERIFIED SCOPE
2026-10-04

FINAL BINARIES (SHA256)
TSHELL.EXE: 35,907 bytes, build04
2c7c0e23f89fe4d91800c55277c98d9a0d69dc81c86058ddee1fe1b71a82441e
SHELLSEL.EXE: 25,953 bytes, success-only FINISH revision
6aa652c9fc77e2e05944b46c055157e97b88a10b963135a4aecf5a01fa71c2fd
TSINPUT.DLL and MATRIX.EXE are byte-identical to the accepted 06 components:
cbb4a851a7f4489945e42c758bb2519415f85270dabe105781acfb056d0521f8
0987936c3b80eb9fc5718f3022996514f6885adbdf83cd05128d01bc19de17c8

START / MY COMPUTER
Ten final native Windows 3.0 real-mode cases pass in 160x200 16-color and
640x200 monochrome, 8086-prefetch, 640 KB, no XMS/EMS/UMB. Real SDL input opens
My Computer. File Manager launches once, reuses its existing window, restores
a minimized window, retains maximized geometry and activates an owned dialog.
Missing WINFILE.EXE shows a compact notice at both widths. Groups and
PROGMAN.INI remain unchanged, and launches preserve their working directory.

Clock/Calendar, Date/time Cancel, System/About, Start-menu saver inhibition,
Programs/Run/Browse arguments and working directories, startup companions,
shutdown veto and missing exit-helper smoke checks pass. All cases return to
DOS. The normal bar can still be covered by a maximized application; the QA
observer brings it forward for that specific geometry-preservation test.
File Manager keeps its original Windows 3.0 layout, which is cramped at 160.
No app-taskbar or always-on-top behavior is added.

SHUTDOWN ART AND FAILURE SAFETY
All 210 existing recovery assertions pass: interrupted selection/recovery,
nested interruptions, later unrelated INI edits, malformed inputs and failures.
Eleven presentation gates and 21 simulated BIOS mode/page/output cases pass.
The journal and transaction functions remain unchanged. Ordinary RECOVER is
plain; only FINISH can display the night screen after reread proof, sidecar
checks and verified journal deletion. No active journal means no success art.

The exact post-WIN batch replacement preserves every configured SET path and
every other byte. ERRORLEVEL is checked immediately after WIN /R. Nonzero
returns recover plainly; zero returns call FINISH. BATCH08.TXT is the precise
edit. No default replacement TSTART.BAT is supplied as a runtime file.

Genuine DOS 6.22 in 86Box Tandy 1000 HX, 8088 4.77 MHz, 640 KB, with no ANSI.SYS:
- 80- and 40-column artwork, mode/page handling, redirection without screen
  changes, absent/stale/corrupt/ambiguous inputs and read-only journal safety.
- Old SELECT/new RECOVER and new SELECT/old RECOVER preserve later edits.
- Actual TSTART -> WIN /R -> normal exit -> FINISH restores SYSTEM.INI exactly,
  clears the journal, draws in the returned BIOS mode 3/80 columns, and accepts
  a command typed at the DOS prompt.
- An application veto keeps Windows running with its active journal and
  selected shell. No DOS art appears; retry then restores and shows the art.
- A clearly labeled DOS WIN.COM stand-in returning 1 preserves its error text
  and recovers plainly. A zero-return stand-in making the journal read-only
  preserves recovery diagnostics and journal, with no safe-to-turn-off claim.
The last two are deterministic error-return fixtures, not claims that every
possible Windows startup failure was induced.

BUILD, SOURCE AND LIMITS
Both final executables have warning-free, byte-identical repeat period builds.
TSHELL uses MSC6 /G0 /Gw /AS; SHELLSEL uses DOS MSC6 /G0 /AS and LINK4.
The shell's scoped ISA audit covers 11,219 reachable instructions without
post-8088 suspects. Imports and unresolved indirect continuations are excluded;
it is not a formal proof. Final SHELLSEL runs on the emulated 8088 under DOS 6.22.

These are emulator tests. No physical Tandy, acoustic-quality or new display
performance claim is made. New screenshot files are actual emulator captures.
The final success-only FINISH revision supersedes preliminary renderer builds.

The source and portable checks for the 08 behavior are retained in this
repository; the current shell executable is identified separately in TESTS.MD.
These are the original 08 native results, not a rerun on any later shell.
