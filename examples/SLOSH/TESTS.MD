# Slosh acceptance record

## Sealed build

SLOSH.EXE is 6,015 bytes, SHA256
f4bce83252d25d14d80d9d5459562a95b723eaf683c87d350c5bb8b1a49827f4.
Two independent builds produced identical bytes. Microsoft C compiled cleanly
with /G0 /Gw /AS /W3 /Od and LINK4; no warnings in the sealed build.
EVIDENCE/RESULT.JSON and BUILD.LOG contain the result.

Only examples/SLOSH is added in an isolated worktree. No display driver,
launcher, memory-reservation helper, Cookie, About or sound files changed.
No GitHub push, publication or installation into a user's machine was done.

## Native runtime environment

DOSBox-X 2026.08.31; machine=tandy; core=normal;
cputype=8086_prefetch (the emulator's four-byte 8088-compatible prefetch core);
fpu=false; memsize=0; memsizekb=640; no EMS, XMS or UMB. Each runtime fixture
used an existing accepted Windows 3.0 real-mode installation and RESERVE.
GUI runs used fixed 20000 cycles. This is an emulator configuration, NOT a
measured 4.77 MHz Tandy or a physical-hardware performance calibration.
No Windows media or third-party toolchain is included in this archive.

The sealed, uninstrumented EXE was launched and visually inspected in:
- 320x200x16 (baseline): native frame/title and blue lower water body
- 160x200x16: complete native frame/title and water; real mouse move and close
- 320x200x4: complete frame/title and dark water on a light client
- 640x200x2: complete frame/title, black water on white
- 640x200x4: complete frame/title, dark water on white

Each mode's FINAL.PNG is an unretouched native screenshot of the sealed EXE.
The 160 test also has MOVED.PNG, MOTION.PNG and NATIVE.AVI. MOTION.PNG is an
unaltered decoded frame from that native AVI. The 160 window requested 112px,
but Windows expanded it to 128px, leaving 32px horizontal travel. 160x200 is the
minimum verified usable display; smaller displays are unsupported/untested.
The original narrow-mode mouse recording is the actual ready EXE, without any
logging or diagnostic overlay. It moves left, raises the right side, rebounds,
and visibly returns to a flat surface. The 14-second MP4 preview is its first
14 seconds at original speed, with audio omitted and no crop/resize/overlays.

Native captures use non-square pixel conventions: logical160x200 is captured
as 320x200 by doubling columns; logical640x200 is captured as 640x400 by doubling
rows. The baseline and320x200x4 captures are 320x200.

## Default Windows move-loop investigation

EVIDENCE/DEFAULT contains a QA-only version routing titlebar mouse-down through
DefWindowProc and recording messages in a fixed RAM array, flushed only on
close. A real captured-serial-mouse drag ran from 407598 to 410344 milliseconds:
2,746 ms inside the default move call, zero timer events during it, and one
WM_MOVE at the end (x=64 to x=124). Merely watching WM_MOVE would therefore give
release-only motion. TRACE.JSON and SLPROBE.BIN preserve the events.

Production titlebar movement instead uses SetCapture plus the ordinary message
pump. Both WM_TIMER and captured WM_MOUSEMOVE share a 55 ms minimum interval;
release takes one final position sample. Input messages cannot indefinitely
starve live updates, and a pending timer cannot double-step immediately after
an input-driven step. Physics is calculated before the MoveWindow repaint.
The standard system-menu/keyboard Move command still uses Windows' outline
move; it is not claimed as live mouse dragging.

## Final live-drag evidence

EVIDENCE/LIVE/TRACE.C is the final source with only bounded in-memory event
logging added; its WATER.H is byte-identical to production. Its displayed UI
and simulation are unchanged. Events 3/4/5 delimit down, up arrival and final
release completion. Event 1 means a step with the capture flag set, and can
include the final up-handler sample; use the delimiters to distinguish them.

Final recorded trials:
- Short right drag: x=64 to x=128. Release sample left=-50 Q4, right=+50 Q4.
  It rebounded through the opposite sign and reached exact zero at 86946 ms.
  The button was held only 55 ms; the nonzero movement sample was on release.
- Left drag: x=128 to x=0. Two nonzero steps occurred BEFORE button-up:
  x=98 with left=+50 Q4/right=-50 Q4, then x=0 with +141 Q4/-141 Q4.
  It continued after release, crossed through the opposite sign and reached
  exact zero at 152911 ms. Thus this recording proves actual live response while
  held, as well as post-release oscillation and damping.

NATIVE.AVI is the full original baseline native recording, including pauses.
TRACE.JSON and SLTRACE.BIN retain the bounded 512-record trace. There is no
invented motion, scripted injection into the production window, or composited
water. Real GUI mouse dragging supplied the motion. EARLY preserves an earlier
native two-direction trial before the final paint/input refinements.

## Numerical and source checks

EVIDENCE/UNIT contains an exact WATER.H snapshot, HOST.C, NATIVE.C and logs.
The host test ran 100,000 bounded forcing steps with undefined-behavior checking,
checking direction, rebound, bounds and eventual settling. The /G0 Win16 test
ran inside real-mode Windows: both directions, rebound, exact-zero settling,
and 4,000 bounded forcing steps all passed. Native test log is fixed 64 bytes,
so its explanatory final word is truncated; PASS is complete.

The source audit checked 16-bit bounds, restoring/coupling/damping signs,
clipped/coalesced fill coverage, pending invalidation accumulation, shared
input/timer throttling and idempotent brush cleanup. Failed window creation,
WM_DESTROY, cancellation and lost capture have bounded cleanup paths. It does
not claim that allocation failure was forced in the native GUI.

To rebuild the numerical native harness, copy the demo build inputs into a
scratch directory, replace SLOSH.C with UNIT/NATIVE.C and WATER.H with its
UNIT snapshot, then use BUILD.PY with --repo pointing to the existing full
repository. Run that EXE in a separate accepted Windows fixture; it writes
C:\SLOSHUT.LOG and exits. The host test builds with a C89 compiler, for example:

    cc -x c -std=c89 -Wall -Wextra -fsanitize=undefined HOST.C -o host-test

## Performance and limits

The requested update rate is about 18 Hz, not a delivered-frame-rate claim.
GDI repaint and cooperative scheduling visibly delay/step motion in this
emulator. Large moves expose/repaint the desktop and can be especially slow.
The final baseline trace settled in about 20.7 s for the short right trial and
44.8 s for the stronger left trial, reflecting delayed/coalesced work; these
are observations of these emulator runs, not predictions for hardware.
The sealed 160 recording showed a raised right edge, a reverse tilt, then flat
water by about10 seconds. No physical Tandy 1000 EX/HX test or performance claim
is made. This is a small functional demonstration, not a smooth-fluid or
calibrated timing benchmark. The 32 px narrow-mode travel and coarse pixel
heights limit how much motion can be demonstrated in 160x200.

The model is 1D and approximate; it has no pressure solver, splashes, objects,
sound, menus, settings, framebuffer or per-pixel simulation. Height clamps
bound extreme motion. Painting uses at most 40 coalesced air/water column pairs,
usually fewer; a flat body needs one water fill and then no physics repaint
until an integer-pixel surface height changes. No driver or IRQ/PIT changes.
