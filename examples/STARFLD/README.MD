# Starfield for Windows 3.0

A GDI flying-star saver for Windows 3.0 real mode and the 8086/8088 target.
Copy STARFLD.EXE to the configured saver directory, normally C:\TSTART.
Choose Starfield in [TSHELL settings](../TSHELL/README.MD), or run
C:\TSTART\STARFLD.EXE /S. Without /S, it is a fullscreen preview that closes
on input. It does not install a driver, global idle hook or password lock.

## Options

Speed 1/2/3 means slow/normal/fast; density is 16/32/64 stars. Default 2/32 is
used for missing/invalid saved options. Sixteen stars is the lightest choice.
The chooser stages Options until Apply; Preview can try unsaved choices.

Optional Windows-directory TSHELL.INI keys:

    [Starfield]
    Speed=2
    Stars=32

Unsaved command-line preview: STARFLD.EXE /S /V3 /N16. Only valid whole
tokens override saved values, and later valid overrides win.

## Drawing and input

Uses GDI on every driver, with no raw framebuffer/BIOS writes, display-mode
changes, filename-based native admission or startup hashing. Initial black
clear is bounded to 16 scanlines per timer; later slices update one star with
at most two 1x1/2x2 PatBlt patches. Each returns to the Windows message queue.
The 55ms timer request is not a frame-rate guarantee. Driver load and density
affect animation; physical Tandy smoothness remains unmeasured.

/S consumes the wake gesture and drains held/repeated input. Focus, capture,
task-switch, cancellation and shutdown paths end the saver. Final build 10
preserves a new owner's cursor during handoff and deselects its own blank
cursor before destruction. It uses Win3.0 SetCursor, not Win3.1 GetCursor.
Restoration checks are sampled where documented, not universal byte proofs.

## Build and verification

From this directory, with licensed period tools:

    python3 SOURCE/BUILD.PY --repo <toolchain-root> --dosbox <dosbox-x> --out <new-directory>

Build uses Microsoft C6 /G0 /Gw /AS and segmented LINK4. Windows, compiler
and ROM files are not supplied. [TESTS.MD](TESTS.MD) identifies the exact
final runtime and distinguishes historical rendering/options tests from
current cursor and integration reruns.

/A, /I, /B and /O are isolated diagnostic modes, writing STARFLD.LOG beside
the executable. Normal /S does not create a log. The test-only bios=0 field
is unused by the GDI renderer. New controls and performance still require
physical hardware acceptance.
