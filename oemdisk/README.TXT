TANDY88 - Windows 3.0 real-mode OEM display disk
==============================================

TANDY88.ZIP is ready to use. Extract it and copy the CONTENTS of DISK1
to a floppy or DOS-accessible folder. No Python, font collection, or
media-staging step is needed to install this downloaded driver disk.

The package contains five selectable display drivers, RESERVE.COM, DOS
helpers, OEMSETUP.INF, the custom TNDYLOGO.RLE startup image, and eight
required Windows support files: EGASYS.FON, EGAFIX.FON, EGAOEM.FON,
CGASYS.FON, CGAFIX.FON, CGAOEM.FON, CGA.GR2 and CGALOGO.LGO. It does not
include Windows itself. You still need a working Windows 3.0 installation.
All five choices and their support files fit one standard 360 KB floppy.

QUICK INSTALL
-------------
1. Back up Windows, then exit completely to DOS. Do not use a Windows
   DOS box. For a new machine, install Windows 3.0 with stock CGA first.
   The normal downloaded disk expects Windows in C:\WINDOWS.
2. Change to the completed disk directory. For a floppy, type A: and
   then INSTALL. It installs the DOS helper into C:\TANDY88, outside
   Windows, after successfully reserving video memory. It does not
   start Windows or Setup automatically.
3. Run C:\TANDY88\TANDY88 SETUP. In Windows Setup, choose Display,
   Other display (Requires disk from OEM), and the path to this disk,
   such as A:\. The first choice, Tandy EX/HX 320x200 16 colors (8088 c05),
   is the unchanged default. Select it or one of the other modes below.
4. Let Windows Setup install the driver/support files and update its
   settings. If asked for TNDYLOGO.RLE or a font, supply the same OEM disk
   path. Setup installs the selected driver and its matching system fonts.
   Do not manually edit SYSTEM.INI or copy drivers into Windows yourself.
5. Every time you start Windows, including after a reboot, run:

     C:\TANDY88\TANDY88

   This safely checks RESERVE and then starts WIN.COM /R. After the
   installation finishes, the removable OEM disk is no longer needed.

SELECTABLE DISPLAY MODES
------------------------
Windows Setup presents these five choices in this order:

  320x200 16 colors (8088 c05)  TANDY88.DRV   Original default, EGA fonts
  640x200  4 colors (8088)      TNDY6404.DRV  Black, green, red, white
  160x200 16 colors (8088)      TNDY160.DRV   Very narrow desktop
  320x200  4 colors (8088)      TNDY3204.DRV  Four-color desktop
  640x200  2 colors (8088)      TNDY6402.DRV  Black-and-white desktop

The original choice keeps its EGA fonts and 133,96,72 font resolution.
All four additional modes use 8-pixel CGA system, fixed, and terminal
fonts with 200,96,48 font resolution. These are display modes for the
same Tandy EX/HX hardware; choosing a CGA-style mode does not make the
package a generic CGA or PCjr driver.

To switch, exit Windows completely, run C:\TANDY88\TANDY88 SETUP, and
repeat Display / Other with this disk and the desired choice. Each mode
has a unique driver filename, so Setup can replace the active selection.
Keep this disk available when switching. Some standard Windows dialogs
clip at 320 pixels; 160x200 is especially cramped and is not recommended
for normal desktop work. Wider modes provide more horizontal room.

CUSTOM TANDY STARTUP SCREEN
--------------------------
The disk includes a crisp monochrome Tandy startup screen. Windows Setup
installs it automatically and rebuilds WIN.COM; no separate patching is
needed. Its 640x200 two-color startup mode changes to the desktop mode
you selected as Windows loads.

Already using the previous TANDY88 disk? Keep its installed DOS helper,
exit Windows, and run C:\TANDY88\TANDY88 SETUP with this new disk via the
same Display / Other procedure. The unique TNDYLOGO.RLE filename avoids
Windows Setup reusing its cached stock CGALOGO.RLE. Do not just copy the
image into WINDOWS\SYSTEM; Setup must rebuild WIN.COM.

WHAT RESERVE.COM DOES
--------------------
Tandy mode 09 uses 32 KB at the top of shared RAM. In the supported
640 KB layout, the BIOS already keeps the upper 16 KB away from DOS,
but the lower 16 KB remains available to ordinary DOS allocations.
RESERVE.COM claims that remaining 16 KB through the DOS allocator,
with valid DOS memory-block ownership, before Windows uses it as video
memory. The same conservative reservation is used for all five display
choices, including modes that need only 16 KB. It does not add RAM or
change the BIOS memory-size value.

The same helper may run again in the same boot: it verifies its existing
reservation and succeeds without reserving it twice. Reboot removes the
reservation. A different resident build or an unsupported/occupied memory
layout fails. The launcher checks for the helper and a successful return
before either Windows or Setup can start. Do not bypass an error with
WIN, and replace any direct WIN command in your own startup procedure
with the guarded launcher. There is no unload command.

TARGET AND LIMITS
-----------------
- Windows 3.0 REAL MODE, 8086/8088, original Tandy 1000 EX/HX modes above
- Normal 640 KB shared-memory layout: BIOS reports 624 KB and the DOS
  arena ends at 9C00h; BIOS text mode 3 before RESERVE
- DOS 3.0 or later with the helper's required allocation functions
- No expanded-base-memory, XMS/EMS/UMB, PCjr, Windows 3.1, or protected-
  mode support is claimed by this installation package

Emulator testing does not establish physical EX/HX hardware compatibility
or cycle-accurate 8088 timing. Genuine MS-DOS variants remain a separate
hardware/DOS acceptance check.

Fresh initial Windows Setup has also been exercised with reservation
before its graphical phase. Some original Setup dialogs are wider than
320 pixels and clip text/buttons at this resolution. The recommended
stock-CGA-first, then OEM driver-change route avoids that cramped phase.
Do not begin an arbitrary initial graphical Setup before RESERVE succeeds.

TROUBLESHOOTING
---------------
- Missing support file or LOCAL.TXT: extract the complete TANDY88.ZIP
  again. T88TOOLS.ZIP, when provided, is an incomplete developer toolkit.
- C:\TANDY88 already exists: INSTALL preserves it. Use the installed
  launcher, or reboot and review/remove the old helper directory yourself
  before reinstalling. Check the directory before deleting anything.
- Copy error: a partial helper directory may remain. Correct the storage
  problem and incomplete installation before using that directory.
- Reservation failure: confirm the supported Tandy/640 KB layout, text
  mode 3, and free video overlap. Reboot if another helper build was
  resident. Do not change the BIOS memory-size word to force it through.
- Windows is not in C:\WINDOWS: obtain a package built for its actual
  absolute DOS path. Developers can use --windows-dir as described below.
- Reverting: use your Windows backup or ordinary Windows Setup with the
  appropriate media. Reboot to release the reservation.

DEVELOPER REBUILDS ONLY
-----------------------
Normal installation needs no Python. Developers rebuilding this ZIP use
Python 3.8+ on a modern host and the exact accepted Windows support files:

  MAKEDISK.BAT --windows-files C:\WIN30SRC --out C:\RELEASE\TANDY88.ZIP

MAKEDISK.PY is the portable backend. Add --local-out C:\OEMDISK to write
an extracted disk too, or --windows-dir D:\WIN30 for a different guest
Windows path. Output paths must be new. Original Windows 3.0 SZDD mode-A
inputs or the accepted expanded files are supported. All fifteen binary
inputs (five drivers, helper, splash, eight support files) are SHA256-pinned;
stale or unaccepted files are rejected. Both completion paths reject a
disk that exceeds standard 360 KB FAT12 space, including cluster rounding.

Verify a rebuilt complete archive with MAKEDISK.PY --verify TANDY88.ZIP.
For the support-free toolkit, use --verify-toolkit T88TOOLS.ZIP. Both
checks reject unexpected members and stale source or manifest contents.

An explicit --toolkit-only produces the separate T88TOOLS.ZIP for
optional developer staging with STAGE.PY. It is not the normal download.
See BUILDING.MD and docs/OEMDISK.MD in the source repository for commands,
verification, provenance and acceptance details. Preserve existing source
and upstream notices; this package makes no new project-wide license claim.
