# Experimental Maze saver

Current TSHELL10-compatible Maze, with ordinary windowed behavior retained.
Launch MAZE.EXE normally for the windowed demo (Space pauses; Escape/Close
exits), or MAZE.EXE /S for the fullscreen saver. Copy this variant to the
configured saver directory, normally C:\TSTART; do not overwrite a separate
on-demand installation unintentionally. Select it through
[TSHELL settings](../../TSHELL/README.MD). It installs no idle hook itself.

## Compatibility and performance

Canonical TNDY160/TANDY88/TNDY3204/TNDY6404/TNDY6402 names retain native
presentation, with real-mode/BIOS-page/geometry checks. Other identities,
including the tested trial aliases, use clipped GDI. Supported geometry is
160, 320 or 640 by 200. No driver replacement, raw alias-layout guess or
startup file hashing is required.

Native slices draw four eight-pixel columns; GDI fallback draws one. It
yields between slices, but the fallback can be very slow. Short uncalibrated
XT-preset measurements were about 0.14 fps at 160 and 0.05 fps at 640. Those
are emulator observations, not physical Tandy speed. Input acknowledgement
in instrumented startup tests could take 14.2..16.2 host seconds. This is an
experimental visual effect, not a responsive-performance guarantee.

/S drains held/repeated wake input before closing. Ownership/focus/capture
loss, cancellation and shutdown stop drawing. Normal wake restores valid
prior focus; lost ownership does not deliberately steal it back. It is not
a password lock. Native presentation resynchronizes the current driver
shadow. GDI close relies on ordinary invalidation/repainting; a recorded
raw restore_ms=0 is not complete GDI repaint timing.

## Build and test

From this directory, with licensed period tools:

    python3 SOURCE/BUILD.PY --repo <toolchain-root> --dosbox <dosbox-x> --out <new-directory>

The MSC6 /G0 /Gw /AS build links with segmented LINK4. Supply your own
Windows/DOS/toolchain; none is included. See [TESTS.MD](TESTS.MD) for exact
runtime hash, native coverage and portable test commands. Diagnostic /A,
/I, /B, /T and /C modes write local MAZE.LOG and belong only in disposable
test sessions. Normal /S is the saver path.

The older parent-directory windowed source, executable, PROOF.ZIP and
measurements remain unchanged historical artifacts. This variant has its
own source/runtime identity and does not rewrite those pins.

Physical testing, calibrated timing, long-duration leak stress, low-memory
fault injection and exhaustive ordinary window interruption remain open.
GDI restoration evidence samples pixels; it is not a full-byte screen proof.
