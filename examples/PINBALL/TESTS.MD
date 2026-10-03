# Tiny Pinball verification

## Sealed native build

PINBALL.EXE is 8,655 bytes, SHA256
0cf3a9b69d7d2f461d32626a6cbd60d100fac2e00fee5664cadfe24af1981298.
Two independent C6 /G0 /Gw /AS /W3 /Od and LINK4 builds matched byte for byte,
with no compiler warnings. EVIDENCE/BUILD.JSON, REBUILD.JSON and BUILD.LOG
record the builds. Only the new examples/PINBALL app is in scope; no driver,
launcher, sound, shell or other application code is changed.

## Integer physics

- Shared TEST.C host regression passes 2,000,000 ticks under C89, AddressSanitizer
  and UndefinedBehaviorSanitizer (leak detection disabled in this sandbox).
- Native Microsoft C 6 / 8086 build passes 20,000 stress ticks in Windows 3.0
  real mode, plus launch height, natural drain, bumper score, both flipper kicks
  and returns, walls, three-ball exhaustion, score cap and deterministic replay.
- Independent host review adds 45,000,000 input-schedule ticks, including
  200 reproducible random seeds. FUZZ.C and logs are included. This is sampled
  stress coverage, not proof of every possible ball trajectory.
- An exact axis-aligned bumper/ceiling trap was found and fixed with a small
  deterministic sideways impulse. Its regression leaves the lane in 27 ticks.
- REVIEW.TXT documents the earlier source review. Its physics header hash still
  matches the final game; the subsequent rendering cache is covered by the
  native key/paint tests below, rather than that earlier source review.

## Native message and paint checks

EVIDENCE/UICHECK.C is a QA-only app variant. It routes Z, slash, arrow aliases,
Space, P and focus-loss messages through the actual window procedure. It checks
flipper rise/return, independently held aliases, launch, paused position and
focus-loss release. It also verifies cache allocation and performs 60 explicit
physics/timer-message + UpdateWindow iterations. This is an in-process native
integration test, separate from actual external-keyboard GUI play.

All five accepted display profiles pass on the final build. Earlier cached-build
300-iteration diagnostic results (BENCH.LOG) are listed below; final 60-iteration
reruns are in KEYPAINT.LOG:
- 160x200x16: client 154x181, font 8px; 300-step paint batch 31637ms
- 320x200x16: client 154x181, font 10px; batch 61241ms
- 320x200x4: client 154x181, font 8px; batch 24113ms
- 640x200x2: client 152x181, font 8px; batch 3186ms
- 640x200x4: client 152x181, font 8px; batch 8294ms

Times are GetTickCount measurements within this particular emulator diagnostic,
not live delivered FPS or physical Tandy timings. Other emulator workloads were
active, so these are not controlled hardware benchmarks or mode rankings.
The uncached 160 comparison did not finish within its 150-second host timeout.
That and visibly incremental full redraws motivated the static bitmap cache.

## Actual GUI verification

The sealed EXE was launched and visually inspected in all five profiles.
EVIDENCE/<MODE>/FINAL.PNG contains unretouched native screenshots. The whole
table, score, ball count and keyboard hint fit. 160x200 is the minimum verified
usable display; narrower/smaller displays are not supported or tested.

At 160, actual external Space launched the ball; Z and slash were held
individually and together. Native capture shows the moving square ball,
flippers rising and returning, bumper contacts and score increasing to 80.
P paused, displayed its resume hint and resumed with another P.
An earlier uncached run visibly drained from three balls to two. The final
manual drain capture and normal-close check were not completed: that combined
GUI action was denied, so it was not retried and the emulator was left open.
Final native physics/message tests separately cover drain and exhaustion.
Do not treat the final manual drain/close check as passed.

EVIDENCE/160/NATIVE.AVI is the untouched emulator-native recording.
The separately delivered MP4 transcodes all 16.94 seconds without cropping,
resizing, overlays, cuts or speed changes. Playback uses the captured frame
rate; this is not a wall-clock or physical-hardware performance benchmark.
The video shows stepped movement and some repaint flicker; this is an early
playable proof of concept, not a smooth arcade game.

Native capture conventions: 160x200 doubles columns to 320x200; 640x200 modes
double rows to 640x400. The 320 modes are captured as 320x200. Screenshots and
video preserve these native capture dimensions, not square-pixel corrections.

## Cache fault paths

The final renderer received a separate source review. CACHEREV.TXT records it.
CACHETST.C uses the exact rendering functions in a host stub harness; six
asserted cases cover DC/bitmap creation failures, bitmap-selection failure,
initial cache-clear failure, restore BitBlt failure, and repeated cache/free
lifecycle. These are host fault injections, not native GDI failure injection.
Native final all-mode tests verify the normal allocation and painting path.

## Runtime limits

DOSBox-X 2026.08.31, machine=tandy, core=normal, cputype=8086_prefetch,
fpu=false, memsize=0, memsizekb=640, no EMS/XMS/UMB, fixed 20000 cycles.
This core is the emulator's four-byte 8088-compatible prefetch configuration;
its cycle setting is not calibrated to a physical 4.77 MHz machine.

The 55ms timer request does not guarantee 18 FPS. Rendering can remain visibly
stepped, particularly in the 16-color modes. Four fixed substeps per delivered
message mean slow paints slow the game rather than cause catch-up tunneling.
The bitmap cache uses roughly 14.5 KB of GDI bitmap storage at 154x181/four planes.
A failed cache allocation falls back to much slower direct GDI.

Physical Tandy EX/HX hardware has not been tested. No sound dependencies,
Windows media, Microsoft toolchains or third-party assets are included.
No GitHub publication or installation on the user's computer was performed.
