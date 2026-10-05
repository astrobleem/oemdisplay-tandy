# Starfield: optional Arwing flight test build

Experimental Windows 3.0 real-mode / 8086-8088 saver. Plain Starfield remains
selected unless you enable Arwing. This is a private test build; physical
Tandy joystick operation and animation speed are not yet qualified.

## Try it

Close Windows and back up the existing STARFLD.EXE and TSHELL.EXE before
replacing each file at its existing configured location. Current WindowsXT
usually keeps TSHELL.EXE in C:\WINDOWS and STARFLD.EXE in C:\WINXT; older
setups may keep the saver in C:\TSTART. Keep your existing guarded WindowsXT
launcher, display setup, TSINPUT.DLL and INIs. This package has no card installer.

In TSHELL, open System > Screen saver, choose Starfield, then Options.
Check Arwing. OK stages the choice, Preview tries it, and Apply saves it.
Options Cancel keeps the previous staged choices; the outer Cancel discards
unapplied changes. Existing speed and star-density choices are retained.

Standalone preview: C:\WINXT\STARFLD.EXE /S /R1
Plain preview: C:\WINXT\STARFLD.EXE /S /R0

Without a calibrated joystick, the ship follows a gentle automatic path.
Any ordinary keyboard or mouse activity dismisses the saver. Escape works.
Joystick motion steers the ship without dismissing it; either joystick
button fires. Holding a button repeats at a bounded rate. At most four
laser bolts exist at once. There is no audio or sound-driver ownership.

## Joystick calibration

From Program Manager File > Run, or TSHELL Run, launch:

    C:\WINXT\STARFLD.EXE /J

Use your configured StarProgram path if it differs. Select Right or Left
with Port (P). Move the stick to all edges, release it to center, then click
Center (C). Click Save (S) while it remains centered. Reset (R) starts over;
Escape cancels. The window fits 160x200.

Both axes need a measured range around the explicitly selected center.
Missing, zero-at-first-sample and timed-out signals cannot enable steering
or fire. Unplugging a stick returns to automatic flight when the next
bounded poll rejects the signal. Old lasers finish their bounded lifetime.
No center is guessed when the saver starts. Uncalibrated flight does no
joystick I/O. Calibration uses the existing EXJOY 512-sample 0201h capture
routine; it performs one write and exactly 512 reads without disabling
interrupts. The saver requests at most one burst per 250 ms, with no catch-up
loop. Calibration is local to this machine and timing environment: repeat
it after changing machine/emulator speed. Physical hardware remains untested.

## Options and drawing

Speed 1/2/3 is slow/normal/fast; density is 16/32/64 stars. Default 2/32 is
retained. New Arwing defaults to 0 (off). The new saved value must be exactly
1 to enable it. Optional Windows-directory TSHELL.INI keys are:

    [Starfield]
    Speed=2
    Stars=32
    Arwing=0

Calibration stores one validated JoyCal string in this section. Use /J
rather than editing its timing numbers. Existing unrelated keys remain.

Whole-token preview overrides: /V1..3, /N16|32|64, /R0|1. Later valid
whole tokens win; invalid overrides leave the saved/default value intact.
For example: STARFLD.EXE /S /V3 /N16 /R1. Preview does not write settings.

Three original pre-baked banked poses are selected at runtime. Their widths
are 16,32,64 pixels on the 160,320,640 modes, with a common 26-pixel height.
White structure remains readable in monochrome; color modes add an accent.
The ship uses tiny masked GDI bitmaps. Small damaged areas are reconstructed
from the current stars/lasers and ship mask, avoiding stale save-under data.
There are no runtime ship polygons, floating-point math, framebuffer writes,
display-mode switches, global input hooks or Windows multimedia dependency.

Initial black clearing is bounded to 16 rows per timer. Plain mode still
updates one star per timer. Flight mode gives every third timer slice to
the ship/lasers while leaving the other slices for stars. The 55ms timer and
165 ms flight interval are requests, not frame-rate promises. There is no
busy-wait catch-up. Four fixed laser slots and a three-flight-slice cooldown
bound held-button work. GDI owns desktop restoration when the popup closes.

## Build, source and evidence

Use licensed period tools:

    python3 SOURCE/STARFLD/SOURCE/BUILD.PY --repo <toolchain-root> --dosbox <dosbox-x> --out <new-directory>

Microsoft C 6 /G0 /Gw /AS /W3 /Od, MASM 5.10 and LINK4. The current executable
is identified in EVIDENCE/BUILD.JSN. TESTS.MD distinguishes exact-runtime
emulator checks, injected input, sampled restoration and hardware limits.
Run python3 SOURCE/STARFLD/TESTS/RUNHOST.PY for portable model/joystick tests.

SOURCE/STARFLD/SOURCE/ARTBUILD.PY contains original geometric sprite artwork and generates
SHIPART.H once on a modern host using Pillow. The ship does not rasterize
polygons during saver animation. No Nintendo ROM/game assets are included.
See NOTICE.TXT and SOURCE/STARFLD/SOURCE/JOYLIC.TXT.

Diagnostic /A runs lifecycle cases, /O foreign-cursor handoffs, /I observes
external input, and /B benchmarks. Add /R1 for flight. Test-only /D1 injects
steering/button/disconnection states. /D2 also reads the documented Tandy
fixture's B800 memory to compare incremental output with a full redraw and
save SCENEn.BIN evidence. That read-only oracle is not renderer input and
must not be generalized to arbitrary GDI drivers. These diagnostic paths
write STARFLD.LOG; ordinary /S writes no log and does not use the oracle.
