# Arwing v0.2 qualification

Final STARFLD.EXE: 33231 bytes, SHA256
de1af104b4b79f77217a7c6edc5ed5981fa22013359c58cab8f2b8939d743887
TSHELL.EXE is unchanged from v0.1:
703383a6944c9c22a0533f15d2e2ff7794edfd57ed0ebced125eca67129a7403

Only STARFLD.C, STFLY.C and STFLY.H changed in production source. Ship art,
joystick capture/calibration, settings format and the TSHELL binary/source
are unchanged. The source and notices are included; the old kit remains
available separately, identified in BASELINE.TXT.

## Exact final runtime

Windows 3.0 real mode, normal 640 KB, enforced 8086_prefetch, FPU/EMS/XMS/UMB
off. Existing reserve helper and owned fixtures, cloned for each run.

- Five modes: 320x200x16, 640x200x4, 640x200x2, 160x200x16, 320x200x4.
- /D3 exercised all four ship corners and three banks under held fire, at
  density 64. 200 full-scene memory comparisons matched incremental output.
  Five are initial-clear checkpoints; 195 have active flight. Old/new bolt
  bounds, masks and overlap with stars/ship were included in reconstruction.
- Four normal-flight /D2 scene checks also matched. This sequence includes
  steering extrema, held buttons, disconnect/reconnect and bounded firing.
- 32 repeated lifecycle cases at 160 and 640 mono passed, with sampled desktop
  differences zero, capture released, no observed leaks and stable warm
  memory. Includes Escape/keyboard, mouse, focus, activation, cancel, close,
  shutdown and repeated reentry.
- 15 foreign-cursor handoffs across all five modes passed, preserving another
  owner's cursor on activation, focus or capture loss.
- Two actual SDL held-input reruns passed: Return at 640 mono and mouse button
  at 160. Both drained while held, did not exit early, released capture, had
  no observed input leak and zero sampled desktop differences after exit.
- Shot count never exceeded four. No frame catch-up loop or new input hook.

/D3 directly supplies diagnostic flight controls; its injection is distinct
from the electrical joystick decoder tests. /D2 captures are read-only B800
fixture oracles, not renderer input or general-driver assumptions. The
comparison covers sampled checkpoints, not every possible frame. Runners
stop DOSBox after QUIT clean while Program Manager remains open. No user
installation or card was written.

## Model, raster and ISA

Host C89/ASan/UBSan tests passed 261795 checked flight slices, 57783 births,
56944 retirements and 96 injected sequences. They cover all widths/corners,
all banks, both exact wing muzzles, fixed firing origins, convergence without
overshoot, nonincreasing length/thickness, finite near-horizon retirement,
tight bounds, cooldown/cap, disconnect/restart and counter wrapping.

4802 independent raster cases compare the exact production drawBolt body
with an independent major-axis Bresenham reference. Every pixel matches,
all writes stay within 8x8, and each bolt uses at most seven coalesced solid
patches. RUNHOST.PY checks that its copied raster body matches production.
The unchanged joystick suites again passed 81813 + 90060 checks. LeakSanitizer
is disabled under the host's ptrace. No old native calibration/settings
result is relabelled as a v0.2 rerun; those components are byte-identical.

Microsoft C 6 /G0 /Gw /AS /W3 /Od and MASM 5.10 compile without warnings.
The scoped direct-control-flow audit covers 9013 reachable instructions with
no post-8088 suspects. It excludes imported OS code, unresolved indirect
continuations and unreachable bytes; this is not a formal ISA proof.

## Fair timing comparison

The v0.1 report's 165ms maximum was AUTOFLIGHT WITH AN ABSENT JOYSTICK, not an
active-firing measurement. It cannot be compared with firing stress figures.

The paired diagnostic fixtures use exactly the same 1500-cycle preset,
320x200x16 scene, stationary centered ship, 77 flight updates, 151 star updates,
10 shot births and four-slot cap. Fire is held for 10 of each 36 flight steps;
all four bolts retire before the next volley. Both variants force the same
every-third-timer flight schedule ONLY in this timing fixture. Rendering and
movement code is unchanged; the trajectory/lifetime difference is the
intentional feature under comparison. These fixture EXEs are not included.
The exact input/schedule overrides and build identities are recorded in
EVIDENCE/PAIRINPT.JSN, PERFOLD.JSN and PERFNEW.JSN.

| Matched workload | v0.1 straight bolts | v0.2 perspective bolts |
| --- | ---: | ---: |
| Total elapsed | 16972ms | 17741ms |
| Cumulative render | 7366ms | 8295ms |
| Maximum render slice | 220ms | 275ms |

Matched elapsed overhead is about 4.53%. Do not interpret these as
physical 8088 speed or a guaranteed frame rate. Windows clock granularity is
about 55ms; zero samples mean less than a sampled tick, not zero work.

Separate final-runtime moving/held-fire stress at 1500 cycles measured:
- 320: maximum slice 550ms; 240 timer messages in39491ms.
- 640c: maximum slice 385ms; 240 timer messages in30044ms.
- 640m: maximum slice 385ms; 240 timer messages in 29824ms.

That stress workload is different from the stationary paired comparison.
It can visibly pause animation in this slow preset. The discarded generic
Windows line prototype peaked at 1099ms in 320 color; the selected local-mask
renderer avoids that path. The GIF uses the qualified 25000-cycle emulator
fixture, with injected controls; it is not a physical-hardware speed claim.
The v0.1 fallback remains intact. Long endurance, low-memory fault injection
and physical Tandy/joystick acceptance remain open.
