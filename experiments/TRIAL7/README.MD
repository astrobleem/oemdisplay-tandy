# TRIAL7: experimental border, text and DIB test build

**Public experimental draft, 2026-10-05. Not a replacement for accepted TR5.**
The selected combined TRIAL7 build includes the retained TRIAL6 bounded DIB
refresh plus fail-closed border/thin-line and short raster-label refresh.
The shipped drivers and rollback helper are the exact emulator-qualified
bytes; no physical Tandy timing, CF reliability or power-loss claim is made.

## Download and use

- [TRIAL7.ZIP](TRIAL7.ZIP): exact 20-file optional runtime/rollback kit.
- [Runtime instructions](RUNTIME/README.TXT): read before copying or applying.
- [Full source and qualification evidence](SOURCEQA.ZIP).
- [Performance and limitations](EVIDENCE/REPORT.TXT).
- [Package safety tests](EVIDENCE/PACKAGE-REPORT.TXT).

Use the existing working **default-layout TR5 WindowsXT installation** at
`C:\WINXT`, with Windows at `C:\WINDOWS`. This is a one-shot overlay for one
already active mode. It is not an OEM disk, a fresh installation or a
mode-switching tool. Exact helper and driver identities are required.
If TR6 is installed, restore it through its original DIBTR6 kit and saved
backup first. TRIAL7 intentionally refuses TR6 as an installed baseline.

Keep an independent storage backup and a plain-DOS boot route. Exit Windows
completely. Unpack the whole kit to `C:\TRIAL7`; follow its APPLY and RESTORE
instructions with the current mode code and explicit YES. Start Windows
only through the existing guarded `C:\WINXT\WINXT` launcher. Never bypass a
failed identity, reservation or recovery check. Retain the kit, original
saved backup and marker even after successful restore.

Original TR5 binaries, stable packages, launcher/source defaults, fonts and
configuration are unchanged by this publication. The helper changes only
the selected active driver after saving and verifying its installed bytes.
Restore uses that saved copy, not a shipped substitute. Physical disk or
filesystem failure remains outside its guarantee.

## Qualified scope

- All five selected mode binaries have strict emitted 8086 instruction,
  multi-prefix REP and linked-object audits, with no unsupported findings.
- 1,800 border/text differential GDI cases and 580 DIB regression cases
  passed across five modes. Direct-line checks cover 14,144,000 pixels.
- Native Notepad/Paintbrush sequences passed in ten fresh guest sessions.
  Of 360 paired frames, 346 were byte-exact; fourteen differ only in a
  documented native Notepad caret. No differences are silently masked.
- Rollback QA: 143 host cases, 76 DOS cases and three SHA-256 known answers.
- This publication rechecked all 15 variant/mode build identities/audits,
  30 text-transform checks, 75,000 bound geometries, 143 helper host cases,
  archive manifests and the frozen runtime hashes. The existing DOS and
  Windows evidence is retained; it was not represented as a new hardware run.

Fixed-cycle DOSBox-X timings are workload measurements, not calibrated
8088 timings or whole-application speedups. Narrow UI clipping, unsupported
font/ROP cases, long soaks and real hardware remain separate concerns.
640x200x4 means four colors, black/red/green/white. DOSBox-X qualification
does not establish original EX/HX mode 0Ah behavior. Normal 640 KB and the
existing video-memory reservation remain required; no EMS/XMS/UMB shortcut.

## Source and reproduction

The six [source overlay files](SOURCE/src/tandysw) are intentionally isolated
from the accepted repository build defaults. Apply them to a separate exact
checkout of source baseline `1eac04fdc571f73037b502ecf1f085028271866e`, copying
`SOURCE/src/tandysw/*` into that checkout's `src/tandysw/`. Use the baseline's
authorized original DDK/compiler inputs, not a changed working tree.

Then use `python3 src/tandysw/BUILD88.PY --dosbox <dosbox-x> --out <fresh-path>
--mode <profile> --trial7 combined`. The supported profiles are 160x200x16,
320x200x16, 320x200x4, 640x200x4 and 640x200x2. The default trial selection
in this overlay is combined. `BLDTR5.PY` and `BLDTR6.PY` preserve historical
builders. Every transform fails closed on changed prerequisite hashes.

SOURCEQA.ZIP includes full checked source, scripts, logs, results, raw
framebuffer captures and selected screenshots. Some historical harnesses
record the original build workspace paths; adapt those paths and supply
your own licensed fixture before reproducing emulator tests. Do not treat
the source archive as a standalone Windows or toolchain distribution.

Run `python3 experiments/TRIAL7/TESTPUB.PY` from the repository root to
verify both original archives, every internal evidence hash, all runtime
manifest entries, five selected driver identities and isolated source.

## Provenance and historical labels

The archives are immutable copies of the completed 2026-10-05 test artifacts.
Their original descriptions say "private" or "not published" because that
was their status at build time; this directory is their public draft
publication record. SHA256.JSN records their exact identities. Neither
archive contains Microsoft OS/media, fonts, compiler/DDK binaries, a guest
installation, user documents or credentials. Existing first-party source
permissions and [third-party provenance](../../src/tandysw/PROVENANCE.md)
remain applicable. No new license or redistribution right for existing
third-party inputs is asserted.
