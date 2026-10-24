WINDOWS XT - START HERE

For a Tandy 1000 EX/HX with 640 KB, DOS 3.3+ and Windows 3.0 real mode,
download the current XR1 installer:
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
