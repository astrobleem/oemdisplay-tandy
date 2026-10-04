FLY SWAT 1.0 - VERIFICATION
==========================

Sealed native build
-------------------
SWAT.EXE is 16989 bytes, SHA-256:
6f65c56dd17a5667e16b583638d8e02a0a8b937234357b09457ca60ee965a60b
Two independent Microsoft C 6 /G0 /Gw /AS /W3 /Ox + LINK4 builds are byte-identical.
The compiler reports C4203 notices for the large diagnostic/entry functions,
which skip global optimization; there are no build errors. The rendering
functions remain optimized. The actual imports are only KERNEL, GDI and USER.
A direct-control-flow NE disassembly audit found no post-8088 instruction
suspects in its reachable scope. Imported Windows routines, unresolved indirect continuations and unreachable bytes are outside the scoped audit.

Rules and input
---------------
The exact shared GAME.H passed GCC C89 with AddressSanitizer/UndefinedBehavior-
Sanitizer, including hit/miss, pause, game-over, restart, score cap and 2000000
sampled game ticks. Native Windows tests route synthetic left-click, key,
focus and timer messages through the actual window procedure. They verify
start, scoring, lost hearts, pause/input blocking, restart, escape exhaustion,
swatter clipping/overlap, animated paints and resource cleanup.
These are synthetic native-message tests, not a manual physical-mouse pass.

Fast rendering and restoration
------------------------------
The default fast renderer is enabled only for the five accepted driver/name,
BIOS-mode, real-mode, page-zero, resolution and color tuples. It uses original
monochrome art in each hardware packing layout. The Windows cursor is hidden
with a balanced visibility count; a small drawn swatter follows WM_MOUSEMOVE.

Ownership loss blocks further framebuffer writes immediately. Focus change,
activation loss, cancel mode and an occluding top-level window queue a close;
the main message loop also finalizes pending closes if message posting fails.
The screen DC is acquired before rendering, and allocation failure fails closed.
Exit forces the display driver's current canonical shadow back to VRAM and
restores the Windows cursor. It never copies a stale desktop snapshot over
another application's current drawing.

All five native profiles passed each of these controlled runs:
- /T: gameplay/input/paint, forced shadow overwrite and repair, then EXIT click
- /Q: focus-loss close request
- /E: Escape
- /W: Close
- /A: real activation of another full-screen window
- /O: a nonactivating full-screen occluding window

All 30 runs returned the controlled baseline with zero changed framebuffer
bytes, and a second independent Windows-shadow flush changed zero bytes.
The long real-timer runs separately verify current-shadow restoration. During
those runs Windows creates a blue active-task caption strip at the bottom of
the desktop, so the prelaunch screenshot is no longer an exact oracle. Before
and after snapshots are retained; the game does not draw that blue strip.

A forced windowed /F regression also passed at 160x200. /G is the user-facing
fallback switch, and /F is diagnostic only. Earlier unchanged GDI drawing was
tested in all five modes, but it is too slow for preferred hardware play.

Performance
-----------
See the measured table below. The slow preset is DOSBox-X 2026.08.31,
machine=tandy, 640 KB conventional RAM, core=normal, cputype=8086_prefetch,
fpu=false, no EMS/XMS/UMB, fixed 240 cycles. It is NOT a calibrated physical
4.77 MHz Tandy timing model. These are guest GetTickCount measurements.
The 40 timer-driven runs use actual WM_TIMER dispatch, not synthetic timer
sends. Reported update rate uses the 39 measured intervals after the first
paint, so it excludes initial setup and the initial repair repaint.

Measured final native timer delivery:
160: first draw 2.087 s; 39 intervals 9.008 s; 4.329 updates/s; restore 2.142 s.
6404: first draw 4.174 s; 39 intervals 9.118 s; 4.277 updates/s; restore 0.549 s.
The 160 mode is 160x200x16; 6404 is 640x200x4.
The logged paint totals/maxima include an initial repair repaint; they are
not steady-frame latency statistics. The timer interval measurement above
starts after that first paint.

PUBLICATION CHECKS AND LIMITS
-----------------------------
The source is rebuilt fresh, compared with the sealed 16989-byte executable,
and checked by the host gameplay sanitizer suite and scoped ISA auditor.
The native results above are retained bounded emulator observations, not a
new manual-input or all-app regression. Physical hardware, external mouse
and keyboard play, and calibrated speed remain untested.
This is the original silent, single-fly game without saved high scores.
No desktop/driver/install settings or existing TANDYLAB pack are changed.
