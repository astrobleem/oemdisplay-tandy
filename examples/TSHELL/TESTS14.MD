# TSTART11 through TSTART14 verification

Current TSHELL.EXE: 68,451 bytes, SHA256
4577182c8ba80f3604867710c44403f61c7e684f01cdc4d45e1e6dc92ef74689.
Current TSINPUT.DLL: 6,281 bytes, SHA256
d14dde571906bdd27a95030f11647333016eb34864afd22c08c5d2cf80660a80.

Both final period-toolchain rebuilds were byte-identical. Scoped executable
instruction audits found no post-8088 suspects in 22,368 shell and 1,772 DLL
instructions. They exclude imported OS code and untraced indirect/far paths.

## Version 11: friendly names and hotfixes

The pure bounded FAT/VFAT core passed 6,211 cases under host sanitizers and in a
DOS 8086 build. Genuine DOS 6.22 FAT12/FAT16 tests covered legacy and packet INT25
reads, a sector above 65535, and 1,000 success plus 1,000 error calls with balanced
stack handling. Windows real-mode timer-driven reads passed. Native Run/Browse
covered valid names, unsupported characters, corrupt entries, nested short paths,
arguments and working directories, 128/129-row boundaries, budget failures,
cancellation, reopening and unsupported-drive fallback. Synthetic mirror-FAT
corruption tests establish parser rejection; DOS repaired one native test mirror,
so that native attempt is not claimed as a corruption proof.

The 160-pixel System fix was verified through real menu input. Genuine DOS 6.22
reproduced the original date readback issue at the last tick of a second. The
corrected time readback passed 63/63 target values; 11,565,431 fake-clock checks
and three mutations verified the narrow hundredths tolerance and refusal of
larger/date-only mismatches. It does not accelerate stock Clock drawing.

## Version 12: Shift exit

Seven final native Win3 real-mode cases at 160/640 pixels covered mouse and
keyboard Shift selection, normal confirmation, Cancel/retry, app veto, no late
Shift change to an already captured choice, real TEXIT /go, and stock Notepad
unsaved-document prompts. Both normal and silent paths returned to DOS. The
old separate silent menu row was removed. These runs used the version 12 binary;
its exit implementation remains unchanged in 14.

## Version 13: fewer Browse paints

Four exact-production genuine DOS 6.22 runs covered 160/640 pixels on 16/64MB
FAT16, 18 steps each, including fixed FAT12 and removable-drive fallback. A
controlled instrumentation pair on the same fixture reduced a 15-row directory
from 28 to 5 WM_PAINT and 26 to 4 WM_ERASEBKGND messages. Both retained 18 raw
reads and identical list mutations. The 128-row, 129-row and budget-failure read
counts remained 102, 0 and 527. Instrumentation timing excluded final presentation
and does not establish physical or end-to-visible speed. Twenty-six ASan/UBSan
bridge groups and 22 mutation checks passed. The 26 groups were rerun for 14.

## Version 14: Hold and exact final scope

The final DLL passed 28 native named cases and 238 host callbacks / 19 post
attempts, plus the original 30-callback idle suite. Tests cover hook chaining,
negative codes, repeated gestures, modifier changes, token freshness, stale input,
ownership, callback reentry, failed unhook retention and unload behavior. Eighteen
source-extracted shell fault groups and 18 final default-gate cases passed.

The final shell passed six host-mounted real-mode gate cases: loaded compatible
keyboard default on, stock default off, explicit stock opt-in, explicit compatible
opt-out, and both live INI-name changes without changing the actual loaded driver.
Final genuine DOS 6.22 runs at 160/640 pixels covered release-to-open, focus return,
no duplicate Hold, typing and Shift exit to DOS.

The immediately preceding shell build03, with the exact final DLL, additionally
passed ten host fixtures and 31 primary checkpoints per width. Coverage included
covered bars, System menus, modifiers, Run/Browse/date dialogs, saver Preview and
idle wake, idle reconfiguration, shutdown veto, normal and Shift exit, Program
Manager launch, held secondary-bar close/restart and interruption races. Final04
changes only the conservative loaded-keyboard default gate. These broader runs
are historical build03 evidence, not a claim that every case was rerun on04.

Native probes confirm that PM_NOREMOVE can still expose the original event and
GetKeyState(VK_SCROLL) still reports its toggle state. No global keyboard-state
rewrite is attempted. Physical raw Hold scan 46/C6 is known, but Windows virtual
key, menu and chord behavior on the physical machine remain pending.

## Screenshots and limits

SHOTS/HOLD160.PNG and HOLD640.PNG are actual final14 genuine DOS 6.22 Windows 3.0
/R SDL captures, logical 160x200 and 640x200, each output at 640x400. They use
TR41616/TR36402 and the compatible keyboard in disposable fixtures, showing Start
over a covering QA window. They are not reconstructed UI.

No OS images, compiler/SDK libraries, private logs or physical performance/audio
claims are included. Host stubs establish bounded logic, not the real far-pointer
ABI. Native tests cover that ABI within their named fixtures. Arbitrary third-party
modal/hook implementations and forced native detach failures are not exhaustive.
Fresh-kit installation evidence is recorded separately under FRESH14/FULLTEST.TXT.
