# Maze saver verification

Current MAZE.EXE: 23,215 bytes; SHA256
`c8dac5dd6c8b6c9c0c6fb8727dd56919e9c0fd5a71fa63b30c429f4be2c3598a`.
This source and runtime are the final compatible saver variant. The older
windowed example remains separately preserved in the parent directory.

## Recorded Windows 3.0 checks

- 16 repeated lifecycle cases on each of five canonical modes and five trial
  aliases: keyboard/mouse wake, task switch, close, cancellation, shutdown,
  shutdown cancellation, held/repeated input, capture theft and focus loss.
- Canonical raw restoration compared exact framebuffer bytes. Trial aliases
  compared sampled GDI pixels after repaint; the latter is not exhaustive.
- Actual SDL held Enter and held/repeated mouse input passed at 160 and 640
  mono. Input stayed shielded during a two-host-second hold and no input leak
  was observed after release.
- Ordinary windowed 160/640 tests completed with stable warmed-up free space.
- Scoped direct-control-flow audit: 6,341 instructions, no post-8088 suspects.
  Imported code and unresolved indirect continuations are excluded.

The final compatible renderer admits the canonical five driver names only
with mode/page/geometry checks. Other identities, including TR41616, TR43216,
TR43204, TR46404 and TR36402, use clipped GDI with no raw framebuffer writes.
The experimental GDI path is slow: an uncalibrated XT emulator preset measured
about 0.14 complete sweeps/sec at 160 and 0.05 at 640 mono. Maximum slices were
440 and 330 ms. Instrumented startup input acknowledgement took 14-16 host
seconds; subsequent held-input/release tests passed. These are emulator
observations, not physical Tandy timing or a claim of snappy wake response.

## Portable geometry checks

Run from this directory; uppercase .C requires `-x c` with GCC:

```
gcc -x c -std=c89 -O1 -g -fsanitize=address,undefined SOURCE/TESTHOST.C -lm -o /tmp/maze-base
ASAN_OPTIONS=detect_leaks=0 /tmp/maze-base
gcc -x c -std=c89 -O1 -g -fsanitize=address,undefined TESTS/GEOMTEST.C -lm -o /tmp/maze-geometry
ASAN_OPTIONS=detect_leaks=0 /tmp/maze-geometry
python3 TESTS/ADDRTEST.PY
```

The publication pass reran these successfully: 540,672 original rays,
2,365,440 extended rays, 30,000 movement steps each, and five-profile address
bounds. These mathematical checks do not establish Windows lifecycle safety.

## Period build and diagnostics

```
SDL_AUDIODRIVER=dummy python3 SOURCE/BUILD.PY --repo /absolute/toolchain --dosbox /absolute/dosbox-x --out /absolute/new-output
python3 SOURCE/AUDIT.PY /absolute/new-output/MAZE.EXE
```

The audit needs the adjacent MAP emitted by the build. Tools must be supplied
by their owner: Microsoft C 6, LINK4, Windows 3.0 headers and small-model
libraries. BUILD.BAT targets /G0 /Gw /AS /W3 /Od. No compiler, OS, ROM, guest
installation or display-driver binaries are included here.

Within an owned, disposable Windows 3.0 real-mode fixture, `/A` runs lifecycle
checks, `/I` observes external wake input, and `/B` benchmarks bounded slices.
These diagnostic modes replace MAZE.LOG beside the executable. Normal `/S`
starts the saver. SOURCE/RUNLAB.PY reproduces the older ordinary `/T` path
only; it does not replay the complete saver suite.

Physical hardware, calibrated timing, long-duration stress, low-memory fault
injection and exhaustive duplicate-launch races remain unverified.
