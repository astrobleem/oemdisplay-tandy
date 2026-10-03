TANDY MAZE: NATIVE WINDOWS 3.0 RAYCASTING PROOF

A small native windowed raycaster for Windows 3.0 real mode and an
8086/8088 instruction target. 32 integer rays, 12x12 map, automatic walk.
No game engine, textures, floating-point runtime, sound or helper DLL.

Run MAZE.EXE after starting Windows through the accepted TANDY88 launcher.
Space pauses/resumes. Escape or Close exits. Resizing is supported; a
minimized window does no ray work. These paths are implemented; manual
keyboard/mouse and interrupted resize testing remain unverified.

Status and evidence
- Final application is 8,463 bytes, built with Microsoft C 6 /G0 /Gw /AS.
- All five existing Tandy display profiles passed native 10-second runs:
  160x200x16, 320x200x4, 640x200x2, 640x200x4 and baseline 320x200x16.
- Accelerated emulation produced about 6 frames/second, limited in part by
  Windows timer granularity. Every run reported no timer or buffer failure
  and no change in free memory after the warm-up point. This is a bounded
  memory check, not a general leak proof or a physical-speed claim.
- Host oracle: 540,672 rays, maximum projected height difference 1 pixel;
  30,000 movement steps and geometry bounds passed under undefined-behavior
  sanitization. The independent host oracle uses floating point only in
  test code, never in the Windows application.
- EVIDENCE/MAZE.PNG is decoded from actual native B800 framebuffer bytes.
  The final buffered renderer was pixel-identical to the earlier native
  full-repaint capture at the same frame. It is not an illustration/mockup.

8088-speed warning and screensaver decision
The installed DOSBox-X preset describes approximately 240 cycles as
"8088 XT 4.77MHz". It is not calibrated physical Tandy timing. With that
preset, first window paint took 87.441 seconds. The ordinary 10-second
cold-start benchmark then reached its first timer too late and completed
zero animation frames; that result is NOT a steady-state FPS measurement.
A separate diagnostic started timing at the first timer and measured one
animation frame: 6.316 seconds total, 6.096 seconds inside painting.
Its geometry and buffer-paint code are identical to the release application.
This single-frame result is not an average steady-state FPS measurement.

The current GDI rendering path does not meet the screensaver performance
gate. No idle helper or screensaver has been installed or bundled. A faster
presentation path is needed before that follow-on is justified. Physical
Tandy timing remains untested.

Architecture
- Fixed-point Q8 positions and a 256-entry signed sine table.
- Each DDA ray advances at most 24 grid boundaries; integer projection.
- One compatible memory DC and bitmap reused until resize, then released.
- The scene is drawn offscreen and transferred with one final BitBlt,
  avoiding repeated display flushes from individual wall fills.
- Stock brushes are borrowed; no per-frame GDI object allocations.
- Cooperative GetMessage/SetTimer loop; no busy waiting or hardware writes
  in normal drawing. The optional capture mode only reads Tandy VRAM.

Build and reproduce
Place SOURCE under examples/MAZE in a copy of the original project, or pass
--repo explicitly to BUILD.PY. Use the existing owned Microsoft toolchain
and original project's headers/libraries; none are bundled here.
python3 SOURCE/BUILD.PY --repo <project> --dosbox <dosbox-x> --out <new-build>

MAZE.EXE /T writes a 10-second measurement to MAZE.LOG beside a writable EXE
copy, replacing that log, and exits. Its clock starts after the first paint;
other startup painting can delay the first timer, as the XT cold test shows.
MAZE.EXE /C captures the actual Tandy B800 aperture at frame 30 to C:\MAZE.RAW
and exits. The raw bytes require the active display profile's decoder.

SOURCE/RUNLAB.PY clones an already installed owned guest profile and runs /T
with normal core, 8086_prefetch, 640KB base memory, FPU/XMS/EMS/UMB disabled.
The template must already contain WINDOWS/WIN.COM and TANDY88/RESERVE.COM.
It never changes the source installation or its display selection.
Use --preset accelerated or --preset approx-xt and a fresh --out directory.

PERF contains the single-frame diagnostic source and its MAZE.EXE. It is a
measurement variant, not the release application. Its /T exits after one
complete animation frame and reports separate frame and paint times.

Verification limits
No physical EX/HX run, calibrated cycle-accurate hardware result, broad
manual pause/resize/minimize/close test, low-memory stress, long-duration
leak test or screen-saver integration is claimed. Existing drivers and the
accepted normal launcher are unchanged. No Windows media is included.
