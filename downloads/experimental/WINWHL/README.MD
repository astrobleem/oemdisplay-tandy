# Wheel input for Windows XT

**Current EX/HX installation:** [download Windows XT](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WINXT.ZIP) and follow the
[Windows XT install guide](../../../docs/RELEASES/RC8.MD). It includes the first-party
WHEEL.DRV, bridge and paired client; no separate driver hunt is needed.

## Historical bridge-only R1 packet

[Download WHEELR1.ZIP](WHEELR1.ZIP) · [SHA-256](SHA256.TXT) · [source, build and qualification](../../../tools/WHEEL/WIN16/README.TXT)

This source-inclusive repository ZIP is an optional Windows 3.0 real-mode
wheel bridge for 8086/8088 systems. It is a repository download, not a GitHub
Release asset, installer, or part of Windows XT RC6.

## Required driver

`WHEELR1.ZIP` supplies the bridge and paired TP client, not `WHEEL.DRV`. The
active Windows `MOUSE` module must already use a working `WHEEL.DRV` that
exports API 1.0. The current XR1 package above supplies that driver. This
older bridge-only packet cannot add wheel scrolling by itself.
The steps below begin after the driver is already configured.

## Quick use

The target system must already have a working `WHEEL.DRV` configured in the
Windows `MOUSE` module and exposing the wheel API 1.0. The package does not
include, install, replace, or modify that driver. Extract `WXTWHL.EXE` and the
paired `TP.EXE` to a directory, close the old TP, then use Program Manager's
**File → Run** to launch the full path to `WXTWHL.EXE`. Use `/STOP` with the
same path to stop it. No `SYSTEM.INI` or startup entries are changed. Full
details are in the package's `README.TXT`.

## Scope and evidence

The bridge sends one vertical line/item per detent to standard vertical bars,
ordinary multiline edits, basic list boxes and cooperating clients. Horizontal
bars, combos, single-line edits, page/speed/Shift-wheel and arbitrary custom
controls are excluded. The paired TP is required for clean shared ownership;
an unmodified TP causes the bridge to pause reading the driver.

The R1 emulator test used synthetic input under Windows 3.0 real mode on an
emulated 8086 with 640 KB and passed 57 native assertions; the host mock suite
passed 27 checks. The owner later reported use on a real Tandy 1000 EX in
Program Manager, File Manager and Notepad. That is owner-reported use, not a
scripted physical acceptance record. Windows 3.1 is not supported. No
Write-specific adapter or additional driver is included.

The ZIP contains both runtime binaries, the exact bridge and paired-client
sources, a host mock harness, hashes and scoped qualification notes. It does
not contain Windows or DOS media, ROMs, WHEEL.DRV, compiler/SDK/DDK files or
private test fixtures. Recreate the ZIP from the pinned public inputs with
`python3 tools/WHEEL/WIN16/PACKAGE.PY`; verify it with `--verify`.
