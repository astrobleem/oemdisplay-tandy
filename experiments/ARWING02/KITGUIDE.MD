# Arwing Starfield v0.2: horizon lasers

Optional Windows 3.0 real-mode / 8086-8088 test build. This corrects the
v0.1 laser direction: shots launch from alternating bank-aligned wing tips,
converge on the starfield's vanishing point at the middle of the screen,
shrink as they recede, and disappear there. They no longer travel to the
top edge. No enemies, scoring, audio or other gameplay was added.

The four-bolt cap, firing cooldown, ship movement, automatic flight,
calibration, settings and plain Starfield default are preserved. The same
TSHELL.EXE from v0.1 is included unchanged for convenience.

## Read-only preview first

Place RUN/STARFLD.EXE in a separate test directory and run it through your
existing guarded WindowsXT setup, for example:

    C:\ARWING02\STARFLD.EXE /S /R1

This preview does not write settings. Keyboard or mouse activity dismisses
it; Escape works. With no valid calibrated joystick, the ship flies itself.
Either joystick button fires; holding it repeats at a bounded rate.
The included GIF is an actual emulator recording with injected joystick
input. Physical Tandy joystick operation and speed remain untested.

## Settings are shared across directories

A separate executable directory does NOT isolate TSHELL.INI. Calibration
(/J) and the TSHELL Apply button write the Windows-directory TSHELL.INI.
Back up that INI before trying either. Do not install synthetic calibration
from a test fixture. The ordinary /S /R1 preview is read-only.

For an existing v0.1 installation, exit Windows, back up its STARFLD.EXE,
and replace only that executable at its configured location. TSHELL.EXE,
TSINPUT.DLL, INIs, guarded launcher, drivers and fonts need no replacement.
For an older installation, back up both active app executables and INI,
then use the matching RUN pair at the existing configured paths. Current
WindowsXT commonly uses C:\WINDOWS\TSHELL.EXE and C:\WINXT\STARFLD.EXE;
older/custom installations can use other paths. No installer is included.

In TSHELL: System > Screen saver > Starfield > Options > Arwing. OK stages
it, Preview tries it, and Apply saves it. Keep existing speed/density.
To calibrate when hardware is available, run the configured STARFLD.EXE /J,
select the port, sweep all edges, release to center, then Center and Save.
Escape cancels. Calibration format and UI are unchanged from v0.1.

## How the correction works

Each bolt keeps its original muzzle position. A bounded integer depth table
projects it toward (screen width/2,100), matching the stars. The ship may be
above or below that point; the ray always converges to it. Length and
thickness diminish. At most four slots and seventeen age states are used.

Each short bolt uses a sixteen-byte 8x8 mask. Adjacent equal rows become
tiny solid GDI patches, avoiding slow Windows line/bitmap conversion paths.
Dirty rectangles cover the previous/current projected endpoints and width,
then stars, bolts and the ship mask are restored in order. The ship's three
pre-baked poses remain unchanged. No runtime ship polygons or floating point.

## Source and qualification

TESTS.MD and EVIDENCE hold the exact new-build qualifications. The v0.1 ZIP
is preserved separately for comparison; its previous tests are not silently
relabelled as v0.2 results. Host tests are under SOURCE/STARFLD/TESTS.
Build with licensed period tools using SOURCE/STARFLD/SOURCE/BUILD.PY.

Original geometric fan art, code rights and Nintendo non-affiliation are
explained in NOTICE.TXT. No ROM, extracted game artwork, Windows files,
compiler, driver or font binaries are included. This experimental candidate
is not physical hardware acceptance and does not authorize automatic merge.
