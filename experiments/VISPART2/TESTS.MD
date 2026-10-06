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

The profiled 320x200x16 display binary is the experimental TRIAL7 combined
build atop TRIAL6, not accepted stock TR5: TANDY88.DRV, 55,904 bytes,
SHA256 f922f12168de69ec2f8a761ce7fce2cbe2080b9e3fcfb06e3a3dac4faba6d502.
The actual profile guests were checked against that hash. It matches the
published TRIAL7 frozen manifest and already contains the earlier bounded
DIB refresh changes. Other visual-test modes used the same combined family.
This identifies the test fixture, not the user's installed driver. The app
kit neither supplies nor installs those driver binaries. DRIVER.JSN records
the exact identity and inspected generated-core provenance.

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
| First visible complete scene, matched diagnostic boundary | 1648 | 3240 |
| First visible scene, startup log writes suppressed | 1648 | 3240 |
| Legacy setup_ms field (different boundaries; not comparable) | 1648 | 2581 |
| Windowed frames in timed run | 8 | 8 |
| Measured work for eight steady frames, quiet profile | 9612 | 9612 |
| Saver startup | 329 | 110 |
| Saver elapsed, 60 ticks | 3570 | 3516 |
| Saver accumulated draw counter | 2910 | 3131 |
| Saver maximum draw counter | 55 | 110 |

Correction to the original report: its "first complete scene" label compared
different clock boundaries. The old setup_ms field stopped after the first
on-screen paint; the new field stops after preparing the off-screen bitmap,
before its final copy. The original 1648 versus 2581 ms figures are preserved
as legacy counters, not an end-to-end comparison. A matched creation-to-first-
completed-WM_PAINT probe measures 1648 versus 3240 ms. The new first copy
accounts for 659 ms beyond preparation. Suppressing startup diagnostic disk
logging in both builds produces the same visible-startup measurements.

The startup trade is therefore explicit: the new build finishes later while
yielding to input and showing a notice. The earlier 125 ms slice experiment's
3186 ms and the selected 55 ms experiment's 2581 ms were both preparation
counters, excluding final presentation. Setup requests 55 ms, then requests
the normal 125 ms animation interval. No steady-state speedup is claimed.
The original elapsed-run counters also begin at different first-copy points;
use the phase measurements below, not 10655 versus 10271 ms as an exact
steady-work comparison.
The saver still advances the same 244 columns/six complete views in its
measured run. End-to-end time is within one roughly 55 ms timer quantum;
draw-phase counters and their reported maximum increased, as shown above.
Do not interpret a single quantized phase maximum as a hardware guarantee.
If off-screen canvas allocation fails, the existing synchronous direct-draw
fallback is retained; cancellable sliced startup describes the buffered path.


## New Maze phase profile: why it is slow

Profiling uses the same 320-wide, 1500-cycle, 8088-compatible fixture, view
sequence and eight steady frames. Separate diagnostic builds bracket ray
casting, memory-DC filling and the final BitBlt with GetTickCount; results
accumulate in memory and print at completion. No ready executable is changed.
The quiet pair suppresses pre-existing startup CREATE/TIMER log writes.

| Eight steady frames, quiet profile (ms) | Baseline | Selected |
| --- | ---: | ---: |
| Ray calculation | 55 | 55 |
| Rectangle fills into memory DC | 4064 | 4119 |
| Bitmap-to-window copies | 5493 | 5438 |
| Sum of these measured phases | 9612 | 9612 |
| Rectangle-fill calls | 696 | 696 |
| Full-window copy calls | 8 | 8 |

The selected averages are about 7 ms ray calculation, 515 ms filling and
680 ms copying per frame. A logged repeat measured 110/4119/5383 ms across
eight frames; this one-tick redistribution is consistent with the roughly
55 ms measurement resolution. The robust conclusion is that drawing is
about 99% of measured work. The ordinary demo casts only 32 rays, each with
at most 24 map crossings; it uses integer tables/arithmetic, not floating
point. Adjacent identical wall spans are coalesced, but this view sequence
still makes 87 GDI fills and one full-window copy per frame. Reducing ray
count does not remove that copy and would also reduce horizontal detail.

The saver is a different renderer. It uses one ray per eight-pixel column:
20/40/80 columns across 160/320/640-wide displays. Recognized native drivers
render four columns per 55 ms timer message directly to video memory;
unrecognized-driver GDI fallback renders one column per message using three
small fills and one small copy. At 320 width, even zero rendering cost would
still require roughly 550 ms for a native sweep or 2200 ms for a GDI sweep.
These are nominal schedule limits; delivered Windows timers can be slower.

The actual native saver profile records 244 columns in 3516 ms, including
3131 ms of drawing. GDI fallback records 160 columns in 9393 ms, with 1647 ms
of drawing: its one-column-per-tick schedule is the main limit in that test.
Individual one-ray phases are below the 55 ms clock resolution; their logged
zero is not a claim of zero CPU cost. Native pixel-writing work and ordinary
GDI work are distinct and should not be conflated.

Exact diagnostic sources: CHECKS/MZPHASE (saver phase probes), MZLOG0/MZLOG1
(matched visible-frame boundary with the existing log behavior), and
MZQUIET0/MZQUIET1 (same comparison with startup log writes suppressed).
Corresponding MZVIS*, MZQUIET*, MZNPHASE and MZGPHASE logs/build records are
under EVIDENCE. All source and runtime files under SOURCE and RUN remain
byte-identical to the originally qualified kit.


## Copy path and feasible next investigations

Maze creates a device-dependent bitmap with CreateCompatibleBitmap, paints
into its memory DC and presents it with BitBlt(SRCCOPY). It does not call
SetDIBitsToDevice. The earlier TR6 DIB optimization changes SDIB88.ASM's DIB
bridge; that specific shortcut must not be assumed to accelerate this DDB
path, even though the tested TR7 driver includes it.

The actual staged TR7 TBitBlt wrapper maps a screen destination to the
canonical logical shadow, calls the DDK memory BitBlt engine, then converts
and flushes proven destination bounds using cursor-safe retained rows or
columns. Conservative full-refresh cases remain. The measured roughly
680 ms therefore covers this whole presentation operation, not merely a
single raw memory copy. It has not yet been split into engine versus
shadow-conversion/VRAM-flush time.

Possible follow-up tests, not optimizations implemented or promised here:

1. Instrument the memory BitBlt and retained-flush portions independently.
   Check source/destination alignment and clipping in the exact DDB workload
   before choosing a copy fast path. Preserve the canonical shadow and cursor
   contract rather than bypassing it.
2. Track previous wall heights/shades and benchmark changed spans or edge
   bands instead of copying the entire client every frame. The driver already
   honors bounded dirty rectangles; Maze currently requests the whole view.
   Expose/resize/repaint must still rebuild or present the complete view.
3. Compare fewer fill calls, such as background passes followed by wall spans,
   against the current up-to-three fills per span. That may reduce API setup
   while painting some pixels twice, so a speedup needs measurement.
4. Benchmark the existing direct-to-window GDI fallback against the memory
   canvas. It avoids the final copy but may incur many separate native
   flushes and visible partial painting/flicker. It is not raw VRAM drawing.

A guarded direct-VRAM path already exists for the full-screen saver.
It is not a safe windowed drop-in: clipping, overlapping windows, the cursor,
activation changes and canonical-shadow restoration still need protection.
No new drawing path, driver optimization or production code change is part
of this report correction.

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
