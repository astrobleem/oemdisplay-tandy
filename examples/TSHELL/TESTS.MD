TANDY START 10 - VERIFIED SCOPE
2026-10-04

FINAL RUNTIME SHA256
TSHELL.EXE 48547 bytes
d87142ac16b615dc1a696976478db2596030b3d4b61e445eb48f2f84aa893cfa
MAZE.EXE 23215 bytes
c8dac5dd6c8b6c9c0c6fb8727dd56919e9c0fd5a71fa63b30c429f4be2c3598a
STARFLD.EXE 16783 bytes
e06c9d80f977e1bda1db2d13be8af5f7d8b6f00285daa4f0e0159af00211b8d0
MATRIX.EXE 14157 bytes
0987936c3b80eb9fc5718f3022996514f6885adbdf83cd05128d01bc19de17c8
TSINPUT.DLL 3082 bytes
cbb4a851a7f4489945e42c758bb2519415f85270dabe105781acfb056d0521f8
SHELLSEL.EXE 25953 bytes
6aa652c9fc77e2e05944b46c055157e97b88a10b963135a4aecf5a01fa71c2fd

CURRENT SHELL AND SETTINGS
TSHELL build 05 has warning-free, byte-identical MSC6 /G0 /Gw /AS repeat
builds. Scoped direct-control-flow audit covers 15,090 instructions with no
post-8088 suspects. Imported OS code and unresolved indirect continuations
are excluded; this is not a formal proof. Configuration core passes 143
strict-C89/ASAN/UBSAN host assertions; native profile probes additionally
verify absent/empty/literal-sentinel keys and correct far-NULL deletion.
Run TESTS/CONFIG/RUN.PY with Python3 and GCC to repeat
the portable checks; uppercase period .C files are explicitly compiled as C.

15 native integrated scenarios pass at 160x200 and 640x200 in Windows 3.0
real mode, 8086_prefetch, 640 KB, no XMS/EMS/UMB. They cover:
- Four-choice UI and Starfield Options fit; Cancel/Escape/close preserve
  unapplied INI contents; Apply updates primary idle immediately.
- Delay bounds 10/3600, focused Space/Enter, edit Enter without a write,
  and cancellation when a held Preview loses focus.
- All three Preview paths, held wake gestures, focus/CWD restoration,
  Matrix/Maze switching, Starfield saved/unsaved options, and None/unhook.
- Options Cancel, Options OK then main Cancel, defaults 2/32, saved 3/64 and
  saved 1/16, custom executable paths and unrelated INI keys retained.
- Other-app input, modal/menu/audio/capture/shutdown-confirmation holds.
- Readonly, missing executable and absent-INI behavior; secondary bars
  save for next primary startup and Preview without installing the hook.
- Maze Preview/idle on actual TR41616/TR36402 trial-driver fixtures.
- Real ExitWindows veto by a separate app with nested Options open; both
  dialogs/config survive, idle recovers, and allowed exit with Maze active
  returns cleanly to DOS. All 15 cases return to DOS.

Those 15 cases used final TSHELL 05/Maze 12 plus Starfield 08. Final Starfield 10
then corrected cursor handoff only. Its 160/640 settings/Preview/idle cases
and secondary Preview case were rerun successfully with the final runtime;
the three supplemental cases explicitly record the new component hash.
Rendering and option semantics did not change in that cursor correction.

COMPONENT QUALIFICATION
Maze 12: 16 native lifecycle cases on each of five canonical and five trial
profiles, plus actual held-input/no-leak tests. Canonical drivers retain the
native path; all other identities use clipped GDI, without raw layout
guesses or startup hashing. Ordinary windowed mode is preserved.

Starfield 10: the preceding08 five-trial-mode/options/lifecycle suite is
retained as historical evidence. The final cursor fix has six native
foreign-cursor handoffs (focus/capture/activation at 160/640), four real
held-input checks and two stable-memory animation checks. Current input,
focus and sampled restoration tests pass. GetCursor, a Windows 3.1 API, is
not imported; supported Win 3.0 SetCursor handles the ownership check.
Restoration evidence uses sampled pixels where documented, not an
exhaustive byte comparison for every GDI scenario.

Matrix/TSINPUT and the DOS SHELLSEL helper/batch block are byte-identical to
the accepted earlier components. The genuine DOS 6.22 success, veto, recovery
and error-path evidence from 08 is retained; it was not fully rerun for 10.
The Start-menu placement correction from 09 remains in the current source.

METHOD AND LIMITS
Actual SDL key/button input drove the unchanged production executables;
an independent Win16 observer records windows, control geometry, focus,
capture, modules, input generations, CWD and DOS clock values. Isolated
emulator fixtures are functional tests, not new Windows Setup tests.
No host/physical clock change or CF installation was part of those tests.

Maze GDI fallback is intentionally slow: short, uncalibrated XT-preset
measurements were about 0.14 fps at 160 and 0.05 fps at 640. Starfield updates
one star per slice; 16 stars is the lightest choice. These are not physical
Tandy performance guarantees. Acoustic quality was not requalified. Explicit Preview release checks use
GetAsyncKeyState physical state and therefore clear that API's shared
pressed-since-last-call bits; ordinary idle polling remains unchanged.

Screenshots are actual emulator surfaces, losslessly converted to PNG.
Source/evidence folders label older and current component hashes clearly.
No guest OS, ROM, compiler library, guest image or control executable is
included. Physical-machine acceptance of these new controls remains pending.

PUBLICATION SCOPE
Earlier TESTS06.MD, TESTS08.MD and TESTS09.TXT remain historical. Current
source and runtimes are included here; no new GitHub CI pass is implied.
Runtime and source identities are recorded in UPDATE10.MF.

FRESH PUBLICATION SUPPORT CHECKS
The current overlay passes all 143 configuration-core assertions under
ASan/UBSan, 306,822 date-core checks, the existing group/startup/saver/idle
host suite and fixed-DLL contract, 210 selector recovery assertions and
11 FINISH presentation gates/21 BIOS simulations. Component Maze geometry
and address checks were also rerun; see its TESTS.MD. These portable checks
do not substitute for native UI or physical testing.
