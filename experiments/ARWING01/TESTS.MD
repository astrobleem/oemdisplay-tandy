# Arwing flight test build: verified scope

Final STARFLD.EXE: 31599 bytes, SHA256
2ff451a01c55c1a87ed29d8b24f57ed2d1f0c0885bcf227c9f0008196965aeeb
Matching TSHELL.EXE: 68979 bytes, SHA256
703383a6944c9c22a0533f15d2e2ff7794edfd57ed0ebced125eca67129a7403

These are the exact tested private candidates. Neither has been published.
The base was main 62f46b2404233f02f548d314ed05fd505bca1fa5.
The earlier plain build10 report is preserved separately in TESTS10.MD.

## Exact-runtime emulator checks

All runs use Windows 3.0 real mode, 640 KB conventional memory, DOSBox-X
8086_prefetch, no FPU, EMS, XMS or UMB. The existing RESERVE helper precedes
Windows. The original fixture is cloned and never edited. Five installed
trial-driver modes passed: 320x200x16, 640x200x4, 640x200x2, 160x200x16,
320x200x4. No physical Tandy or joystick was available.

- Twenty scene checkpoints across five modes, plus four 64-star/fast mono
  stress checkpoints, matched independent full-scene reconstruction exactly.
  Each compares the incremental scene's captured B800 memory with a complete
  redraw of current stars, lasers and the ship. This is checkpoint coverage,
  not a proof of every possible pixel at every moment.
- Scripted extreme steering, held-button fire, disconnect and reconnect ran
  in all five modes. The laser pool never exceeded four; disconnect stopped
  firing and selected automatic flight. These are injected control values.
- 48 repeated lifecycle cases (16 each at 160, 320 color and 640 mono) passed
  sampled desktop restoration, capture release, focus/task-switch/cancel,
  close/shutdown paths and repeated entry. Warm free-space values stayed
  constant across all 16 passes within each run.
- Six foreign-cursor handoffs (focus, capture, activation at 160 and 640 mono)
  preserved the new owner's cursor.
- Four actual SDL held-input cases (Return and mouse button at 160/640 mono)
  verified draining while held, no early exit, release, no observed input
  leak, capture release and zero sampled desktop differences. SDLIN.C is
  the external event injector; these are more than posted Win16 messages.
- Native TSHELL control-message suites at 160 and 640 mono verified layout,
  legacy default-off, staged OK, Options Cancel, outer Cancel, preview both
  ways, Apply and reopen. A test proxy records exact preview arguments then
  launches the final STARFLD.EXE. Requests were /S /V3 /N16 /R1 and
  /S /V1 /N64 /R0. Neither preview changed saved options. This is a narrow
  secondary-bar settings rerun, not a new claim about every TSHELL feature.
- Saved 1/64/Arwing, invalid-key fallback 2/32/plain, strict new Arwing parsing
  and later-valid whole-token override order passed on the exact runtime.
- The distributable SOURCE/STARFLD/TESTS/TESTWIN.PY reproduced a full mono scene run with
  the final executable. Benchmark/lifecycle runners stop DOSBox after the
  app logs QUIT clean because Program Manager stays open. Native shell and
  calibration harnesses explicitly exit Windows and return to DOS.

## Joystick calibration and pure models

The unchanged final STJOY.C passed two native 160x200 calibration runs with
35 checks each:window/text/control bounds, early Center rejection, explicit
range/center, disconnection before Save, first INI creation/readback, reopen,
port switch/Escape preserving saved values, and no polling after close.
The native harness substitutes synthetic electrical bursts for joy_capture;
physical electrical compatibility and calibration accuracy remain untested.
Protected-mode port rejection is source/build checked, not a protected-mode
runtime certification. Missing calibration performs no hardware I/O.

Portable C89 tests passed 81813 joystick-module checks, 90060 decoder checks
and 60330 model slices across 160/320/640. ASan/UBSan passed; LeakSanitizer is
disabled under this host's ptrace. These cover limits, exact deadzone,
selected axes/buttons, early/timeout/absence, clamp/shot lifecycle/reentry.
TSHELL configuration passed 218 transaction/rollback/preview checks and its
unchanged date suite passed 306822 checks. The broader legacy RUNHOST suite
still stops at an existing IDLE/HOSTTEST link failure from missing WinAPI
stubs; it is not claimed as a full aggregate pass.

## Performance and memory

Paired 1500-cycle runs are an uncalibrated slow emulator preset. All use
speed 2/stars 32, with valid stored calibration and joysticktype=none for the
Arwing half, exercising the actual bounded absent-port capture path.
Milliseconds are Windows GetTickCount's approximately 55 ms resolution;
a zero means below a sampled tick, not zero work. Render time includes
startup clearing but excludes the isolated full-scene oracle.

| Mode | Plain max slice | Arwing max slice | Arwing 60-tick elapsed | Additional live sprite resources |
| --- | ---: | ---: | ---: | ---: |
| 320 | 110ms | 165ms | 4504ms | 1440 bytes |
| 640c | 55ms | 165ms | 4284ms | 2720 bytes |
| 640m | 0ms | 165ms | 4174ms | 2720 bytes |
| 160 | 55ms | 165ms | 4394ms | 1280 bytes |

The resource delta compares off/on in the same new executable; it is not the
entire feature's code/data footprint. Free space was unchanged from warm-up
to stop in each pair. Arwing performed 16 bounded flight updates in each
60-tick run; plain mode updated 48 stars, flight mode 32, after initial clear.
No real-port sample was accepted without a joystick. The requested 55 ms
Windows timer and 165 ms flight cadence are not guaranteed frame rates.
Physical 8088 speed, long-duration endurance and forced low-memory faults
are still untested.

## Build and ISA scope

Final source bytes match BUILD04 inputs. C 6 /G0 /Gw /AS /W3 /Od and MASM 5.10
compile without warnings; LINK4 produces a Win16 NE. ARTBUILD.PY regenerates
SHIPART.H byte-for-byte. The scoped direct-control-flow audit checks 8437
reachable instructions with no post-8088 suspects. It excludes imported OS
code, unresolved indirect continuations and unreachable bytes, so it is not
formal whole-program ISA certification. Actual 8086_prefetch runs complement
it. No physical machine, Windows license, toolchain, ROM or driver is in the
private ZIP. Original fan-art and source licensing are in NOTICE.TXT.
