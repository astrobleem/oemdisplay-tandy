# Canonical HPXY local integration

This candidate updates the normal expanded WINXT package and keeps the
HPXY.DRV filename. There is no additional consumer product or download.
The preserved private TNDY2816 packet is a historical comparison only.
No push, PR, merge, release or physical-hardware write is authorized here.

## Package and installation

The normal producer remains tools/DOSINST/RCPUB.PY. Its qualified runtime
override now includes tools/DOSINST/BIN/HPXY.DRV; generated SETPINS/SETFILES
and native SETUP match that driver and the updated FIXXT. Frozen older
payloads and qualification records remain unchanged.

Consumers retain the existing full SETUP UPDATE/FRESH route or, on an
installed Windows system, DISPLAY -> Windows Setup Other -> DISPWIN.
DISPLAY invokes the same included FIXXT to launch native Windows Setup.
Afterward it checks the selected bare HPXY.DRV name. If old bytes remain,
it offers an explicit-Y refresh of SYSTEM\HPXY.DRV only. Default, EOF,
Escape and N leave it unchanged. This prompt also covers canceled Setup
with HPXY already selected; a returned Setup status grants no permission.

The route rejects a conflicting root HPXY shadow, unrelated journals,
ambiguous recovery, changed source and damaged staged bytes. It validates
the complete source and closed staged file against the compiled size/CRC
before renaming. DOS 3.20 uses checked close/readback; the DOS 3.3 commit
requirement remains in the existing full-install route.

Native testing exposed both actual upgrade details: Windows Setup retained
the old same-basename driver, and a completed selection returned nonzero.
FIXXT now logs the raw status and rejects only negative launch failure before
examining selection/consent. The initial failed run preserved the old driver.

The staged ZIP has 60 members. Exactly six differ from the accepted baseline:
SETUP.EXE, README.TXT, WINXT/HPXY.DRV, WINXT/FIXXT.EXE, WINXT/DISPLAY.BAT and
WINXT/DISPLAY.TXT. The other 54 members are byte-identical. In particular,
the ordinary descriptor, XYCTL, fonts, grabber, logos and sound are unchanged.

## Driver behavior and cost

The 2,816-byte preflight budget admits larger disjoint exposed strips without
overflowing scratch or overwriting old visible addresses before blanking.
It admits pure X24, pure Y16 and X16/Y8 diagonal requests. Larger requests
retain the safe 32,000-byte full conversion. Pure Y4 writes only old-offscreen
storage, so that path omits blanking; failure explicitly blanks before full
software recovery. Existing helper steps remain X8/Y4. Common retrace
scheduling and the 640x256 desktop / 320x200 viewport remain unchanged.

The driver is 61,856 bytes, SHA-256
c86a243c9e724401de3fa40d2c304bb6e336c6f8ad5df241c2e4ff1911d297a9.
The controlled current-source baseline is 60,400 bytes; the older accepted
packet driver is 56,704 bytes and remains preserved separately. The strip
change adds 86 code bytes and 1,376 scratch bytes relative to the controlled
source baseline, not relative to the older packet binary.

Gross NE segment minimum allocations total 126,883 bytes. The existing
project ceiling is 127,531, leaving 648 bytes. This allocation budget is not
remaining conventional DOS RAM. The focused Windows A/B probe measured
1,472 additional allocated bytes, 154,592 free warm bytes and a 149,280-byte
largest free block, unchanged after its movement sequence.

## Evidence and limits

The driver source/build and four matched Windows suites are sealed in
tools/DOSINST/HPXY.JSN and docs/QUAL/HPXY/WINDOWS.ZIP. They cover 152 exact
framebuffer/cursor comparisons (4,864,000 packed bytes), both directions,
diagonals, bank wrap, edges, GDI drawing, cursor restoration, fault recovery
and normal DOS return. Independent code/address review found no remaining
core issue. MODEL.C separately checked 96,196 moves / 3,078,272,000 bytes;
host models do not execute the hardware.

The configured 86Box HX surrogate runs an 8088 at 7,159,092 Hz with 640 KB,
reporting 624 KB after the normal reservation. In the focused Windows A/B
tests, X24, Y16 and X16/Y8 fell from approximately 1,208 ms to 165 ms, with
some high-origin diagonals taking 220 ms. Far fallback stays around 1,208 ms.
GetTickCount measures the complete Escape call at roughly 55 ms resolution;
these are not blackout measurements or physical EX timings. Earlier DOSBox
PIT results are a separate emulator model and are not combined with them.

The canonical installer passes 30 focused C89 host transaction cases and
the existing FIXXT regression. Independent installer/package review found
and resolved native C89 declaration order and a missing full-finisher gate.
It also reviewed the nonzero Setup-status correction and reran the final
30-case suite. C6 and normal native SETUP builds pass.

The canonical DOS 3.20 DISPLAY/Other/same-name refresh/DISPWIN run passes,
including exact final bytes, Paintbrush repaint and a 165 ms total Escape
for (0,0)->(16,8), four framebuffer comparisons and clean DOS return. It
waited 469.3 seconds for the shared lease and ran for 242.2 seconds. Setup's
observed return was 1; the visible Y prompt was answered only after recording
the old installed driver. Unrelated sound, keyboard, mouse, SYSTEM driver,
stock shell/application binaries and the original alternate source are preserved.

The native full UPDATE preparation passes all 83 exact outputs and the full
INSTALL/CPSET/CHECK finisher, including installed HPXY and unchanged XYCTL
identities. A second installed Windows boot runs the actual XYCTL menu steps
right/down/left/up, verifying X8/Y4 movement and 800/640-byte mode-1 work.
All eight frames and clean DOS return pass. That boot waited 397.1 seconds
for the lease and ran for 199.6 seconds. These waits are host resource
coordination, not driver movement or blackout measurements.

Native fresh preparation also passes all 370 byte-exact outputs. The current
fresh/update receipts freeze the tested archive, SETUP, FIXXT and HPXY
identities; collection refuses to restamp older evidence. The two Windows
application runs independently pass 12 frames / 384,000 packed bytes. These
add to the earlier controlled A/B qualification, rather than replacing it.
All owned emulator children stopped and their shared leases released.

The run directories and final receipts are under the sibling
tandy-pan-integration directory. Final package gates and catalog checks are
recorded in CANON-STATUS.JSN. The failed redirected-log harness run and the
blocked no-child lease attempts remain preserved locally as failed receipts.

Remaining physical limits include optical blank intervals, actual EX
scanout/timing, natural retrace timeout and deliberately exhausted memory.
