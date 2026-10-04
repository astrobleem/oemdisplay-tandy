FLY SWAT 1.1 - CURSOR FIX VERIFICATION
=====================================

SWAT.EXE: 19901 bytes
SHA256: 850b65e0072ea6bdb68f2fb804f353eb76b093dc4946ab8a562cc30a69f1b0bb
Two independent Microsoft C 6 /G0 /Gw /AS /W3 /Ox builds match exactly.
The existing C4203 optimization notices for large diagnostic/entry functions
remain; no compiler errors. Imports remain Windows KERNEL, USER and GDI.

Scope
-----
Replaces the GDI stock crosshair with a per-instance Win3 CreateCursor
resource. Fixed black and white AND/XOR pixels are used, without inversion.
The same white head/handle and black halo are used in the native renderer.
Cursor bitmap rows are word-aligned. The client pointer is selected for a
stationary launch and HTCLIENT; nonclient handling stays with Windows.
Cursor resources are detached and freed on startup failure and normal exit.
The GDI path does not change ShowCursor's visibility count.

GAME.H and the exact detectFast function are byte-identical to the baseline.
No gameplay, score, hitbox, driver source/name gate or timer changes.
Unsupported/protected-mode displays skip raw-framebuffer cursor diagnostics.

Native checks
-------------
20 runs pass. Both windowed and direct-rendered paths pass in all five
formats: 160x200x16, 320x200x16, 320x200x4, 640x200x4, 640x200x2.
GDI fixtures use current trial-driver filenames. Direct-path test fixtures
use identical trial-driver bytes under accepted legacy names, solely to
exercise the unchanged gate. These are cloned emulator fixtures; no user
installation or driver bytes were changed. Raw private fixtures are not
published; the retained test counts here refer to those completed runs.

Assertions inspect native framebuffer pixels for the white core and black
halo during idle, swing and pause, on black and white backgrounds. GDI
checks actually reposition the system cursor using SetCursorPos, then send
WM_SETCURSOR; they are not merely WM_MOUSEMOVE state simulations. The old
cursor area is verified clean after movement. Nonclient pointer selection,
scoring, restart, exhaustion, resource cleanup and focus pause also pass.

The direct renderer additionally passes edge clipping, overlap and forced
Windows-shadow overwrite/recovery checks. Focus loss, Escape, Close, real
activation and full occlusion pass at 160 and 640x200x4, returning the
controlled baseline and current Windows display shadow exactly.

Host checks
-----------
Unchanged rules pass C89 ASan/UBSan with 2,000,000 sampled ticks. CURTEST.PY
compiles the exact native cursor function under C89 ASan/UBSan and checks
black/white backgrounds, off-screen clipping, all widths and dirty bounds.
A scoped reachable-instruction audit reports no post-8088 suspects. Its
unresolved indirect/imported-code paths remain excluded from this scoped
audit. AUDIT.PY reproduces the check against a build and matching MAP.

Approximate XT comparison
------------------------
DOSBox-X, normal 8086_prefetch core, 640 KB, no EMS/XMS/UMB, fixed 240 cycles.
This is not calibrated physical 4.77 MHz timing. Same 160-color fixture:
- Baseline: 39 actual timer intervals, 9228 ms (4.226 updates/s)
- Fixed:    39 actual timer intervals, 9117 ms (4.278 updates/s)
- Initial draw: 2087 ms baseline, 2087 ms fixed
- Paint totals: 2196 ms baseline, 4284 ms fixed
- Max measured paint: 55 ms baseline, 110 ms fixed
The richer cursor costs more painting work, but remains within the requested
220 ms tick budget in this sample. Do not interpret the small cadence
difference as a speed improvement. Both restore the current shadow exactly.

Limits
------
No screenshots or raw environment reports are included in this source delta.
Tests use native APIs and generated input; no manual external mouse pass or
physical Tandy test of this new build is claimed. No Windows media, driver,
compiler or private account material is included.

Publication reruns the period build, exact executable comparison, host rules
checks, CURTEST.PY and scoped ISA audit. The 20 native runs above are retained
qualification evidence, not a new full native regression during publication.
