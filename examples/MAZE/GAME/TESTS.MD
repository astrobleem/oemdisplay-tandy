# Tandy Maze test record (2026-10-08)

## Build

`MAZE.EXE` is 28,013 bytes, SHA-256
`9905abccd267dd229502fad2d7e57375f51c34b2c445fc52ea754508407de389`.
Two builds with Microsoft C 6
`/G0 /Gw /Gs /AS /W3 /Oit` and LINK4 in DOSBox-X matched byte for byte,
with no compiler warnings (`BUILD.JSON`, `REBUILD.JSON`, `BUILD.LOG`).

## Rules and renderer (TEST.C)

Host (gcc, C89, `-Wall -Wextra`, ASan + UBSan): **PASS**, no warnings.
Native (MSC 6, run in Windows 3.0 real mode on the emulated Tandy):
**PASS**. Both print replay checksum `669354881` (`EVIDENCE/HOST.LOG`,
`NATIVE.LOG`). The 8088 build fills spans with inline assembly and the
host with C, so a matching checksum means the two paths and 16-bit
arithmetic agree on every byte of 200 rendered frames.

Checked, levels 1-13, 300 seeds each on the host (3 natively):

- Every maze is perfect: all cells open, n*n-1 passages, all connected
- Exactly one exit, in the outer wall, beside a boundary cell
- Par is reachable: walking the shortest path with the real controls
  takes exactly par moves
- The autopilot (screen saver) reaches the exit in every maze
- Bumping a wall does not move or count; turns do not count; stepping
  back keeps the facing
- Renderer at ten view sizes (16x16 to 400x200), 300 positions each, in
  16-colour and mono palettes: no write outside the buffer (ASan), the
  status rows untouched by the view, and nothing drawn right of the view
  in each row's padding

Two deliberate mutations were caught: par off by one, and spans allowed
9 pixels past the view (found only after the bounds test was given a
real palette; it had been running with an all-black shade table).

## In Windows

DOSBox-X built from source, `machine=tandy`, 8086 prefetch core, 640 KB,
no XMS/EMS/UMB, Windows 3.0 with WINXT TR5 drivers.

- All five modes (160x200x16, 320x200x16, 320x200x4, 640x200x4,
  640x200x2): play, turning, map, pause, demo and the level-complete
  screen (`EVIDENCE/<mode>.PNG`, final EXE)
- Fast path in all five modes (`gdi=0`); the GDI fallback (`/G`, `/F`)
  in 320x200x16 and 640x200x2 (`FALLBACK.PNG`: 640x200x2, final EXE;
  plain shading without the calibrated dithers)
- Saver lifecycle self-test `/A`, 16 cases (key, mouse, move, task
  switch, close, cancel mode, shutdown and cancelled shutdown, repaint
  disruption, overlap, held mouse, synthetic input, capture theft, focus
  loss): all restore the desktop, return focus and capture, and quit
  clean, with free memory unchanged across runs, in 320x200x16 and
  640x200x2 (`QA320.LOG`, `QA640.LOG`, final EXE)
- TSHELL idle launch with Maze selected (10 s delay): the saver walks,
  starts a new maze at the exit and wakes to the desktop on a key, in
  320x200x16 and 640x200x2 (`SAVER.PNG`, build 01e8fd34; the saver path
  is identical in the final EXE). It refuses to start while the game is
  open, as before.
- Timing at 360 cycles in all five modes and the fallback:
  `XTBENCH.TXT`; real-time clip at that speed: `XTSPEED.MP4`;
  B-roll at an unthrottled emulator speed: `GAMEPLAY.MP4` (silent)

## Sound

The emulated PSG output was recorded (DOSBox-X DX-CAPTURE) and measured,
not listened to (`SOUND.PNG`, `SOUND.TXT`). Bumps play near 100 Hz for
140-160 ms, the exit arpeggio 523-659-784-1047 Hz ending on a 300 ms
note, the level jingle 392 then 523 Hz, steps and turns as short noise
clicks. The first recording showed notes stretched to seconds or clipped
to milliseconds, because Windows merges timer messages while a frame is
drawing; notes are now timed by the clock and start after the frame.

## Not tested

- Physical Tandy hardware; the 360-cycle setting is DOSBox-X's own scale,
  not a calibrated 7.16 MHz measurement
- Listening to the sound effects
- Drivers other than the five TR5 modes (the fallback exists for them)
- Long sessions, low-memory fault injection
