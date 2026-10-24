WINDOWS XT - START HERE

Already have Windows 3.0 real mode on a Tandy EX/HX with 640 KB?
Download the current XRSYNC display update:
https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-xrsync-2026-10-24/XRSYNC.ZIP
Follow its automatic preparation and Windows Setup guide:
https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/RELEASES/XRSYNC.MD
Start that profile with C:\XR155\RUNSYNC.BAT.

For a complete Windows XT desktop install from matching Windows 3.0 media,
use the rc.8 installer:
https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINXT-XR1.ZIP

Extract it on a modern computer and prepare with Python 3.8+ and matching
English Windows 3.0 media:
  python PREPARE.PY --windows-media C:\WIN30SRC --mode fresh --out C:\XR1NEW
For an existing Windows installation, use --mode update and a new output
folder. Transfer the prepared DOS-CROOT contents to DOS C:\, keeping your
DOS boot files and configuration. From plain DOS run C:\SETUPXT.
Start Windows every time with C:\STARTXT.

Setup choices and repair:
https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/RELEASES/RC8.MD
Other machines (PCjr, PC1512, ColorPlus, Video II, Yamaha, text mode):
https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/PLATFORM.MD

EARLIER PACKAGES
Historical TANDY88 disk instructions and fixed-mode details:
https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/OEMDISK.MD
