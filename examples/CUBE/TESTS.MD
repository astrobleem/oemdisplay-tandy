# Cube qualification

This is a local candidate with qualification still pending. No physical
adapter, composite output, Windows 3.1 or every-driver qualification is claimed.
Publication is not authorized. ACCEPT.JSN intentionally blocks release packaging.

The current 15,647-byte CUBE.EXE has SHA-256
`1de2326af2b6bc7e353f5e72d5bf7e8cb4aeac0d4e8437fd0851f7b761dd754d`.
It was compiled with MSC6/LINK4, `/G0 /Gw /AS /W3 /Oat` and NE target 3.0.
The candidate shell is 74,131 bytes; its paired TSINPUT.DLL is 6,301 bytes.
The native DOS installer uses Open Watcom `-bt=dos -0 -ms -os`.
No accepted display, font, mouse, keyboard, sound or core packet was replaced.

## Current binary observations

Two native UI attempts used the exact current Cube, shell, DLL and installer
on an IBM XT 8088 at 4.77 MHz, 640 KB, DOS 6.22, Windows 3.0 real mode,
and the accepted CGA100 driver with compact fonts (160x100x16 RGBI).
Both passed Cube settings persistence, preview launch, keyboard dismissal,
and return to settings. Style=1, Speed=3 and Size=3 were saved.

The first attempt saved the shell's Cube choice but left its delay at 300.
The second typed into the actual delay field, then timed out in the test
controller's cross-task edit readback, before Apply. These are failed tests;
no final idle-launch acceptance is claimed. The controller is being corrected
without changing the production Cube executable.

Direct CGA video-memory captures confirm both compact settings panels,
including their bottom buttons, fit inside 160x100. Every displayed cell
was verified as character DEh; its background/foreground attributes give
the left/right logical pixel. The decoder uses standard RGBI colors and
nearest-neighbor enlargement. Original headless captures are retained;
they have a vertical scanout offset that clips the lower image. Decoded
captures are evidence of logical layout, not calibrated physical aspect ratio.

Each attempt's final receipt proves its owned emulator stopped, the byte
lease was released and the emulator inventory was zero. No other run was stopped.

## Host and build checks

Host checks pass all 512 geometry phases, sine symmetry, face winding,
lighting range, sizing bounds and the reduced copy rectangle. Shell
transactions pass 163 checks, including Cube selection/path, disabling and
write-failure rollback. Original idle checks pass, and Hold checks cover
Cube's module/window wake exclusions. These are C89 host checks, not native
display or input qualification.

The scoped 8088 audit traces the NE entry and three exported Cube callbacks
through direct near control flow. It found no post-8088 suspects in 3,218
instructions. Indirect continuations/tables and imported Windows code are
excluded; this is not an exhaustive ISA or hardware proof.

## Earlier prototype evidence

A 15,615-byte prototype (`4c09c65813dec046961e7191ba8e3bd15bd9475718b08ae624038f62119cdd90`)
passed flat, dither and wireframe rendering at CGA160x100x16. Six runs each
drew 13 frames, covering keyboard wake, held mouse button/release, movement,
activation loss, Close and stolen capture. All six white source/screen
pixel reads matched; no input leaks or timer/capture/bitmap/DC/pen remnants
were reported. DOS install/undo/reinstall returned normally. That installer
preceded the current paired shell/DLL transaction; this is historical evidence.

The prototype's warm draw cost was about 0.77-0.82 seconds filled and
0.44-0.50 seconds wireframe in that emulator. These Windows tick observations
include GDI/cooperative scheduling and are not physical-machine benchmarks.
An older 14,479-byte prototype passed the same six cases at CGA640 mono.
Neither prototype establishes final-binary mode coverage.

## Pending acceptance

Final render/input QA at CGA low resolution, monochrome, Tandy color and
larger virtual dimensions/nonzero viewport remains pending, along with
real shell idle launch and paired installer undo/reinstall/unknown-file guards.
CUBECTL is developer-only: its default route exercises UI/idle; /Q runs
render/input QA and exits the private Windows fixture for DOS recovery tests.
It must never be installed or run in a Windows session containing user work.

Retained failed preparation attempts are not qualification: one FAT file-growth
failure incorrectly launched an incomplete fixture; its owned process was
stopped. Preparation now replaces entries and requires completed receipt/config
before launch. A stale-payload attempt was stopped before acceptance. Blank
transitional capture attempts were superseded by a QA frame hold and readback.
Private OS images, ROMs, toolchains and emulator executables are excluded.
