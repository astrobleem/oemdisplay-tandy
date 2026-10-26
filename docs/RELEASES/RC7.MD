# Windows XT v0.1.0-rc.7 - qualified R1 components and overlay

This release publishes the redistributable subset of the completed Oct19 R1
work. It does not publish Microsoft's Windows files or the complete private
installer. The earlier rc.6 release and experimental downloads are preserved.

## Downloads and prerequisites

- [First-party wheel/font source and runtime kit](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/WINXT-FIRST-PARTY-R1.zip).
- [R1 overlay and local assembly utility](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/WINXT-REDISTRIBUTABLE-OVERLAY-R1.zip).
- [Start here](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/START-HERE.TXT),
  [qualification](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/QUALIFY.JSON),
  [release identities](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/RELEASE.JSON) and
  [checksums](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/SHA256SUMS).

The overlay is **not a standalone installer, Windows distribution or bootable
disk**. Its nine destination files are copies of four unique MIT binaries:
WHEEL.DRV, XTCFIX.FON, XTCOEM.FON and XTCSYS.FON. It requires 370 separately
supplied exact local files. Windows 3.0 licensed media alone is insufficient:
the complete XR1 assembly also requires the separately held display/keyboard,
shell, bridge and other project helpers. Their private use does not establish
redistribution rights, so those executables are absent from these downloads.

Extract the overlay and use its host-only ASSEMBLE-LOCAL.py with the existing
local private R1 DOS-CROOT and a new output directory. It verifies all inputs
before creating output and checks all 379 completed files. Copy the assembled
contents using the user's normal backup/media procedure; preserve DOS boot
files and MBR. This publication task does not copy anything to CF. From plain
DOS use `C:\SETUPXT`; fresh installs use C:\WINDOWS, existing installs update.
Choose the first Tandy 1000 EX/HX Computer entry, HPXY 640x256, PC/XT keyboard,
COM1 wheel and No Changes for DOS configuration. Start with `C:\STARTXT`.
Repair/verify with `C:\FIXXT` and `C:\FIXXT /VERIFY`; select XR1 from plain DOS
with `C:\MODEXT /XR1`. Follow START-HERE for transaction recovery and limits.
The component kit alone does not install the private bridge or add scrolling
without a separately supplied compatible wheel client.

## Included improvements

The newly authored first-party Windows 3.0 real-mode driver supports original
8086/8088 COM1/IRQ4 serial input at 1200 baud 7N1, two buttons and the optional
signed wheel nibble. It retains API version 0100h/ordinals 10-12 and adds the
timestamped ordinal 13. Explicit DS addressing corrects the linked NE data
access issue found by actual Windows API tests. Matching assembly, decoder,
format checks, font generator and MIT notices are included. The provenance
record explicitly makes **no clean-room claim**; no DDK implementation,
Microsoft runtime object or SDK import library is linked into this driver.

The qualified private R1 assembly combines XR1 640x256 logical space with a
320x200 viewport, focused helper keyboard panning/home, hardware extremes and
wheel scrolling. The private fixed/preloaded bridge's bounded recovery policy
accepts known packet ages up to 18 BIOS ticks after a stable Windows-only gap.
This is an ingestion-age limit, **not a response-time guarantee**. The bridge
executable itself is not supplied by this public subset.

## Verification and remaining limits

The final Oct19 R1 emulator run used the unchanged original 8088 core at
7,159,092 Hz, 640 KB and the Tandy HX surrogate: four calibrated wheel checks,
eight exact 320x200 active-viewport frames, two clean DOS returns and exact
UART/IRQ/BDA/PIC restoration. Fresh and update install tests passed. Actual
Windows timestamp API checks and a separate controlled recovery test passed;
wheel targets used normal pre-input timer warm-up, not a product readiness
acknowledgment. Earlier intermittent Notepad loss was not definitively
attributed; the timestamp change has its own host and native evidence.
The full native record in QUALIFY.JSON retains exact run IDs and limits.

**Earlier physical acceptance is separate.** The owner's earlier HPXY R1 run
on a real Tandy 1000 EX accepted panning/drawing, with 54 pans (53 hardware),
no ERROR records, software/home cleanup and Windows exit 0. It does not
qualify the final combined R1 package, this new first-party WHEEL.DRV, other
machines/profiles or Windows 3.1. No new physical run is claimed for rc.7.
The partial HPAN R3 physical record is a different 640x200 candidate.

Publication checks bind the existing ZIPs to visible sources, notices and
all manifest bytes. New local host reproduction/checks and exact-commit CI
are release verification, not new guest or hardware testing. Physical serial
mouse behavior with the new driver, final-package hardware coverage,
protected mode, Windows 3.1 and alternate profiles remain unqualified.
No optional PR155/PR158, new feature, floppy/cloud work or RAVE work is added.
