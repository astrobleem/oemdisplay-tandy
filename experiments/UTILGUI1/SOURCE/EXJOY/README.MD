EXJOY UTILUI01 trial - Tandy 1000 EX joystick tester
Windows 3.0 real mode / 8088 target. Label polish based on the 2026-10-04 baseline.

QUICK START
1. Extract EXJOY.EXE into its own folder, for example C:\EXJOY.
2. Start your existing Windows 3.0 real-mode setup normally.
3. File > Run: C:\EXJOY\EXJOY.EXE
No installer, added driver, Windows settings change, or reboot is needed.
Nothing in this directory should replace files in WINDOWS or your display setup.

This is an initial physical-hardware trial. The EX's electrical interface
is documented, but actual joystick behavior on your computer is NOT tested.
Do not run this hardware build on an unrelated PC. Protected-mode Windows
is deliberately rejected. The emulator tests use Windows 3.0 real mode,
not a physical DOS 6.22 boot.

WHAT YOU SEE
R and L show two X/Y raw pulse counts and both buttons.
- A number is a sampling-loop count, not milliseconds or a calibrated angle.
- TMO means the bit never went low within the bounded capture.
- timing seen means a high-to-low edge was observed.
- zero / unknown means at least one axis was already low at the first read.
- Presence stays uncertain. Neither numbers nor a timeout prove attachment.
A one-button stick may naturally leave its second button up.
Check both on-screen groups by moving just one stick and pressing one
button at a time; see HWREF.MD for the physical port-label caveat.

CONTROLS
Pause / Run button or P: stop / resume sampling.
Range / Live button: switch between live readings and captured ranges.
Tab then Space: operate either button from the keyboard.
C: store the current center for axes that have a timed pulse.
R: reset measured ranges AND centers. Ranges start growing again immediately.
Esc or Q: close. The normal Windows system-menu Close works too.
Minimizing suppresses sampling; restoring resumes it unless paused.

OPTIONAL CALIBRATION
Put the sticks in their intended center position. Press R, then C.
Move slowly through the full range and corners. Open Range to inspect each
axis's observed minimum, maximum and C(center). C--- means no valid center;
--- ranges mean no measured value. Calibration is session-only and never
writes an INI file. Center n/4 axes reports exactly how many axes supplied a timed
pulse. The shared source also provides an optional 0..100 normalization
function for later software, requiring measured endpoints around center.

LIMITS / SAFETY
The app requests samples every 250 ms (nominal 4 Hz); busy Windows can make
that slower. Display updates are throttled separately. It is a diagnostic,
not a precision logger. Interrupts remain enabled, so raw counts may jitter
or be shortened by an interrupt during capture. Keep CPU speed unchanged
while comparing raw counts/calibrating. There is no smoothing hiding noise.

Each sample writes only the documented trigger port and reads a fixed
512-byte burst. It never spins until a joystick responds, disables
interrupts, changes BIOS/PIT/PIC settings, or installs a driver. The finite
instruction budget is not a hard wall-clock guarantee during interrupts.
Normal runs do not write files. Calibration and samples vanish at exit.

OPTIONAL DEMO
EXJOY.EXE /demo displays synthetic moving readings, labelled Demo (or Paused while stopped). It
performs no joystick I/O and is useful for inspecting the interface.

DEVELOPER-ONLY SWITCHES
/test and /porttest are automated QA modes, not normal user controls.
They create C:\EXJOY.LOG and AUTOMATICALLY EXIT WINDOWS after about eight
seconds. Do not use them in a working Windows session with unsaved work.
The regular app and /demo only close their own window.

BUILD AND TESTS
---------------
python3 BUILD.PY --repo TOOLCHAIN_ROOT --dosbox DOSBOX --out NEW_DIR
Supply lawful C6/MASM/LINK4 and Win3.0 headers/libraries. Source and first-party
EXJOY.EXE are included; no OS/toolchain/ROM or private receipts are included.
Read ../../EVIDENCE and BUILD.MD for verification and untested hardware boundaries.
Original source and documentation: MIT (LICENSE.TXT).
