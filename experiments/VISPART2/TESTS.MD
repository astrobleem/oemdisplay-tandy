# Qualification and measured trade-offs

## Selected sources and environment

Base: astrobleem/oemdisplay-tandy main c6ee4b0, including the merged ARWING02
kit. The ready executables are the rebuilt Maze ordinary+saver entrypoint
and Arwing02-compatible Starfield. Existing accepted packages are retained.

Native tests used DOSBox-X, machine=tandy, normal core with 8086_prefetch,
640 KB conventional RAM, no FPU, EMS, XMS or UMB, Windows 3.0 /R and the
existing RESERVE helper. The CPU and later-opcode probes retained their
8088-compatible expected signatures. Native app/scene checks used 25,000
cycles; the deliberately slow paired measurements used 1500 cycles.
Those settings are not a calibrated physical EX/HX timing claim.

Microsoft C /G0 /Gw /AS /W3 /Od and LINK4 builds pass. Maze retains an existing
signed/unsigned warning in the diagnostic tick-limit comparison; its positive
limits are unchanged. Scoped entry/export/symbol-reachable ISA audits find
no post-8088 instructions in the checked application code. External Windows
routines and unresolved indirect paths are outside that audit.

## Maze

- 540,672 host ray comparisons pass against the independent reference, with
  maximum wall-height error of one pixel. 30,000 movement steps stay bounded.
- 2,000 poses prove eight four-ray setup slices equal a complete cast.
- Forced initial timer-failure tests execute the actual C WM_CREATE branches:
  one error is reported, creation returns -1, and no endless startup notice
  is left. Successful creation requests the bounded 55 ms setup timer.
- Final 640-wide native and forced-GDI startup controllers each pass Close,
  Escape and resize-then-Escape scenarios. Ordinary windows are found within
  439-550 ms and are gone within 824-934 ms of launch in the slow fixture;
  saver cases are gone within 549-714 ms. Every case releases capture.
- Final 160-wide saver lifecycle suite passes all 16 cases: keyboard, mouse,
  activation/focus loss, close, Cancel, shutdown, cancelled shutdown, repaint,
  covering window, held/double-click input, synthetic input and capture theft.
  Desktop comparisons are exact and warm free memory remains stable.
- Actual native 320-color framebuffer at timer tick 40 matches the baseline
  in all 32,000 visible bytes; unused bank padding is excluded.

Slow paired measurements, milliseconds:

| Measurement | Baseline | Selected |
| --- | ---: | ---: |
| Windowed first complete scene | 1648 | 2581 |
| Windowed frames in timed run | 8 | 8 |
| Windowed timed-run elapsed | 10655 | 10271 |
| Saver startup | 329 | 110 |
| Saver elapsed, 60 ticks | 3570 | 3516 |
| Saver accumulated draw counter | 2910 | 3131 |
| Saver maximum draw counter | 55 | 110 |

The windowed startup trade is explicit: it finishes later while yielding to
input and showing a notice. The initial 125 ms slice trial took 3186 ms;
using 55 ms only during setup reduces that to 2581 ms, then restores the
normal 125 ms animation interval. No steady-state speedup is claimed.
The saver still advances the same 244 columns/six complete views in its
measured run. End-to-end time is within one roughly 55 ms timer quantum;
draw-phase counters and their reported maximum increased, as shown above.
Do not interpret a single quantized phase maximum as a hardware guarantee.
If off-screen canvas allocation fails, the existing synchronous direct-draw
fallback is retained; cancellable sliced startup describes the buffered path.

## Plain Starfield

- 5,000 actual-C overlapping-star fixtures pass exact full-scene comparison.
  The baseline eraser damages 2,332 of those deliberately overlapping scenes.
- The diagnostic plain-scene oracle passes 40 snapshots in each of 160-,
  320- and 640-wide native displays: 120 checks, zero differing framebuffer
  bytes. It uses the same plain rendering path as the selected executable.
  TRIALS/PLAINQA.C enables the existing diagnostic oracle for plain mode;
  its unrelated Arwing batching branch is not selected for RUN/STARFLD.EXE.
- A 64-star, 240-tick slow run is unchanged at 14226 ms elapsed, 1373 ms
  accumulated drawing and 110 ms maximum. No speed, density or timer change
  is included.

## Arwing02

Selected change: skip a bolt's old damage box only when it is completely
contained in the old ship box already repaired. The exact original ship
mask/body/accent blits, bolt raster, projection and layer order remain.

- 3,600 dense-star moving/held-fire cases compare actual old/new C renderers
  and full reconstruction: identical scene pixels at all three ship widths,
  corners, banks and overlapping live bolts.
- Selected executable: 40 native corner/bank/held-fire reconstruction checks
  at each of 160x200x16, 320x200x16 and 640x200x2; all 120 checks match exactly.
- Selected 640-wide lifecycle suite: all 16 cases pass with unchanged desktop
  samples, released capture and stable warm free memory. This GDI fallback
  restoration check samples an eight-pixel grid, not every framebuffer byte.
- Existing host model/raster/joystick checks also pass: 261,795 flight slices,
  4,802 raster cases, 81,813 bounded-capture checks and 90,060 joystick cases.
  These are synthetic checks, not physical joystick qualification.

The fixed-input pair has exactly 77 flight updates, 151 star updates, 23 shot
births, a four-slot maximum and 642 bolt patches in both builds. Steering and
fire are indexed by flight step, not by changing wall-clock speed.

| Fixed trace, milliseconds | Baseline | Containment guard |
| --- | ---: | ---: |
| Elapsed | 32790 | 32022 |
| Damage-repair phase total | 7029 | 6369 |
| Accumulated draw counter | 24660 | 24329 |
| Maximum draw counter | 385 | 385 |

That is a 2.3% elapsed reduction and 9.4% repair-phase reduction. The ordinary
wall-clock moving-fire stress reads 39491 -> 37404 ms elapsed, but both retain
a 550 ms maximum. That secondary trace is not used as the fixed-workload
proof because input polling is time based. The worst stall is not solved.

A broader all-boxes/one-star-pass rewrite was pixel-correct but gave no
meaningful benefit: its moving run remained 39491 ms with a 550 ms maximum.
It is omitted from ready code; BATCH.C and its measurements are retained as
a rejected trial rather than silently promoted.

## Slosh: tested, omitted

The restrained cyan surface edge was enabled only for more-than-four-color
GDI, leaving low-color modes unchanged. A matched synthetic stress trace
paints 40 distinct surface samples for 81 paints in each build. It measures
painting cost, not normal water physics or physical Tandy speed.

| Slosh stress, milliseconds | Baseline | One-pixel edge |
| --- | ---: | ---: |
| Accumulated paint counter | 91834 | 96887 |
| Maximum paint counter | 1154 | 1264 |

The 5.5% cumulative cost and higher maximum fail the negligible-cost condition.
No new Slosh executable is included. TRIALS/SLOSH0 and SLOSH1 contain the
exact diagnostic source/build files; their synthetic height sequence is not
an application replacement. SL0.PNG and SL1.PNG are actual trial frames.

## Reproduce and interpret the evidence

TESTHOST.PY runs the portable host checks with Python 3/GCC. Native QA sources
are included under CHECKS; use an owned cloned Windows fixture with existing
approved support files. Diagnostic executable/controller names and paths are
fixed to that clone. Production builds use SOURCE/*/SOURCE/BUILD.PY and the
licensed toolchain supplied through --repo; use a fresh --out directory.

For the two fixed Arwing comparisons, overlay TRIALS/PROF0.C (baseline) or
PROF2.C (selected guard) onto a separate copy of Starfield's source. PROF1.C
and BATCH.C are the rejected broad rewrite. PLAINQA.C is a diagnostic-only
plain-mode reconstruction build. None belongs in normal RUN.

Application logs are authoritative. A few early exploratory harness results
captured their JSON just before the final QUIT line was flushed; the complete
.LOG files are preserved too. The initial ordinary Maze harness waited for a
marker that this app does not emit and reached its harness timeout after the
benchmark had completed; the final selected ordinary run detects its proper
completion record. These are disclosed harness differences, not hidden app
hangs. Later controller and lifecycle runs use their explicit clean markers.

Native screenshots and decoded framebuffer images were inspected. No OS,
compiler, driver, font, complete guest image or captured memory padding is
redistributed. Physical hardware and native Windows-host wrappers remain
unverified. The isolated kit does not alter install defaults or accepted pins.
