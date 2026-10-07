# Tandy Pinball test record (version 2, 2026-10-07)

## Build

`PINBALL.EXE` is 15,487 bytes, SHA-256
`ad1a725bf47669e2491f2d0d45e8c28bca095a8c1fe07095de2e958da219f15c`.
Two builds with Microsoft C 6 `/G0 /Gw /AS /W3 /Od` and LINK4 in DOSBox-X
matched byte for byte, with no compiler warnings
(`EVIDENCE/V2/BUILD.JSON`, `REBUILD.JSON`, `BUILD.LOG`).

## Physics and rules (TEST.C)

Host (gcc, C89, `-Wall -Wextra`, ASan + UBSan): **PASS**, no warnings.
Native (MSC 6, run in Windows 3.0 real mode on the emulated Tandy):
**PASS**. Both print replay checksum `155063374`
(`EVIDENCE/V2/HOST.LOG`, `NATIVE.LOG`).

Checked:

- Space starts a game; three balls
- Full plunge reaches the top arc and leaves the lane; a tap falls back to
  the plunger without losing a ball
- A held flipper cradles the ball near the pivot; releasing and flipping
  sends it up-field
- Tip hits are faster than pivot hits
- A resting flipper gives no kick
- Bumper and slingshot kicks and scores
- Lanes light; three lit raise the multiplier and reset; flipper buttons
  rotate lit lanes
- Drop targets drop, the full bank scores and resets
- Ball save works once per ball, then drains count
- Three drains end the game and keep the high score
- A ball falling back into the lane can be plunged again
- Random play never leaves the table, never exceeds the speed cap, and
  never sits still off a held flipper (2,000,000 ticks host, 20,000
  native)
- The same inputs give the same result

## Tuning runs (host)

Average ball life over 400 balls with ball save:

| Play style | Ball life | Outlane share of drains |
| --- | --- | --- |
| Never flipping | ~4 s | almost none (balls go down the middle) |
| Random button mashing | ~16 s | ~40% |
| Bot flipping on time every time | ~33 s | ~65% |

Bugs found and fixed while tuning:

- Ball save re-armed on every plunge
- A ball moving sideways could slip through the slanted lane gate into the
  plunger lane and never be launched again
- A ball draining at the right edge could be mistaken for a lane ball
- A ball could balance forever on a post tip or in a notch at a flipper
  pivot. The guides now step down onto the flippers, and a ball still for
  about 2 s off a held flipper gets a small nudge.

## In Windows

Tested in DOSBox-X built from source (2026.10.01), `machine=tandy`, 8086
prefetch core, 640 KB, no XMS/EMS/UMB, fixed 20,000 cycles. Windows 3.0
was installed fresh from the original disks, with Windows XT drivers
installed through Setup.

- All five graphics modes (160x200x16, 320x200x16, 320x200x4, 640x200x4,
  640x200x2): the table draws at the right shape, the panel fits, and A/L
  raise the flippers.
- 320x200x16: plunge, full ball cycle, ball save, lane lights, multiplier
  to X3, game over, high score kept, and a new game started.
- A 45-second random-key session left no XOR residue on screen.
- `EVIDENCE/V2/GAMEPLAY.MP4` is a 45-second recording of one game
  (4x nearest-neighbor, 4:3). `GAMEPLAY.MKV` is the unscaled capture.

The PSG path ran in the emulator (the Tandy signature check passed and the
panel offers S SOUND), but sound output was not listened to. Physical Tandy
hardware has not been tested.
