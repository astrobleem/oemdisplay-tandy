WINDOWS XT WHEEL BRIDGE R1 - EXPERIMENTAL
=========================================

This optional Windows 3.0 real-mode program reads wheel packets from an
already installed WHEEL.DRV and sends vertical line-scroll input to selected
Windows controls. It is for 8086/8088 systems.

REQUIREMENTS
------------
- Windows 3.0 real mode.
- An existing MOUSE module exposing WHEEL.DRV API 1.0, with the wheel driver
  already configured and working. WHEEL.DRV is not included.
- The existing DOS/Windows mouse configuration. This bridge does not install
  or replace a driver, edit SYSTEM.INI, add startup entries, or change the
  pointer/button path.

QUICK START
-----------
1. Extract RUNTIME\WXTWHL.EXE and RUNTIME\TP.EXE to a directory of your choice.
   Keep your existing TP.EXE separately.
2. Close the existing TP before launching the paired TP.EXE.
3. In Program Manager, choose File / Run and launch the full path to
   WXTWHL.EXE. It runs without a visible window.
4. Move focus into a supported document/list and turn the wheel.
5. To stop the bridge, use File / Run on the same path followed by /STOP.
   The paired TP resumes reading the driver after the bridge stops. Windows
   exit also shuts down the bridge.

SUPPORTED INPUT
----------------
Vertical line scrolling is provided for standard vertical scroll bars,
ordinary multiline edits, basic single-column list boxes and explicitly
cooperating wheel clients. One line/item is sent per detent. The paired TP
uses the cooperating-client interface.

Combos, single-line edits, horizontal or square scroll bars, multicolumn or
variable-height owner-draw lists, page/speed/Shift-wheel actions, and arbitrary
custom application scrolling are outside this version's scope. Focus selects
the recipient; moving the pointer alone does not. An unmodified TP is detected
and the bridge pauses its driver reads to prevent competing consumers.

QUALIFICATION
-------------
R1 was built as BLD08 with Microsoft C 6.0 /G0 /Gw /AS /W3 /Od and LINK4.
The pinned emulator session used Windows 3.0 WIN /R, an emulated 8086, 640 KB,
and no EMS/XMS/UMB. Its synthetic-input native run passed 57 assertions and
the TP /TEST regression; the host mock suite passed 27 checks. These checks do
not substitute for physical wheel input or timing qualification.

The owner later reported scrolling working in Program Manager, File Manager
and Notepad on a real Tandy 1000 EX. That is owner-reported use, separate from
the emulator suite; this package does not claim a scripted physical acceptance
run. Windows 3.1 is not supported. No Write-specific adapter is included.

BUILD AND SOURCE
----------------
SOURCE contains the R1 bridge and paired TP client. HOST contains the mock
test harness; run `python3 HOST/RUNHOST.PY` with a C89-compatible GCC on PATH.
EVIDENCE\QUAL.TXT records the exact tested binary hashes and test scope.
Rebuilding the Win16 binaries requires an external Microsoft C 6.0 / LINK4
and Windows 3.0 SDK/DDK environment. No compiler, SDK/DDK, Windows files,
ROMs, or driver are bundled.

The ZIP and download are experimental repository files, not a Windows XT
release asset or installer. See the online guide for hashes and limitations:
https://github.com/astrobleem/oemdisplay-tandy/blob/main/downloads/experimental/WINWHL/README.MD
