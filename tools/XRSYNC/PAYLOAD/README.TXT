XRSYNC - WINDOWS 3.0 DISPLAY INSTALLER

Tandy 1000 EX/HX, normal 640 KB, DOS 3.20+, English Windows 3.0 real mode.
The desktop is 640x256 through a 320x200, sixteen-colour viewport.

INSTALL ON THE DOS COMPUTER
Put XRSYNC.EXE on the DOS computer and exit Windows. Run:
  XRSYNC C:\WINDOWS
Use your actual installed Windows directory.

The packet includes the grabber, fonts, artwork, driver and helpers. It
prepares C:\XR155, reserves video memory and opens Windows Setup. It needs no Python,
modern computer, compiler or unpacker. It works from another current drive.

In Setup choose Display / Other and enter C:\XR155. Select:
  Tandy XR1 640x256 synchronous Output
Choose Complete Changes. Keep your keyboard and mouse choices. Choose
No Changes when Setup asks about DOS configuration.

Start every Windows session from plain DOS with:
  C:\XR155\RUNSYNC.BAT
It checks the installed display/fonts, reserves video memory and starts
WIN /R from your Windows directory. In Windows run C:\XR155\XYCTL.EXE
for viewport panning and presentation controls.

ZIP alternative: extract XRSYNC.ZIP on the DOS computer and run
  XSETUP C:\WINDOWS
from that folder. The EXE download does not require ZIP extraction.

Current guide: docs/RELEASES/XRSYNC.MD at the source commit in RELEASE.JSON.
Test results: docs/QUAL/DOSINST/XRSYNC.JSN and docs/RRSYNC.MD.
See NOTICE.TXT, OWATCOM.TXT and the font/artwork notices. Your installed
Windows 3.0 system is required; no separate support-file collection is needed.
