XRSYNC - DOS-NATIVE WINDOWS 3.0 DISPLAY INSTALLER

Tandy 1000 EX/HX, 8088, normal 640 KB RAM, DOS 3.20 or later.
Requires an existing English Windows 3.0 real-mode installation.

INSTALL ON THE DOS COMPUTER
Download XRSYNC.EXE and put it anywhere on the DOS computer. Exit Windows.
Run it with your installed Windows directory, for example:

  XRSYNC C:\WINDOWS

It gathers the existing Windows support file automatically, prepares the
complete OEM disk in C:\XR155, reserves video memory and opens Windows Setup.
No Python, compiler, modern computer or separate unpacker is needed.
It works when started from another drive. Use your actual Windows path.

In Setup choose Display / Other, enter C:\XR155, select
  Tandy XR1 640x256 synchronous Output
then Complete Changes. Keep your keyboard and mouse selections. Select
No Changes when Setup asks about DOS configuration.

Start each Windows session from plain DOS with:
  C:\XR155\RUNSYNC.BAT

RUNSYNC checks the installed display and fonts, reserves video memory and
starts WIN /R from the Windows directory used during installation.
In Windows, run C:\XR155\XYCTL.EXE for viewport and presentation controls.

XRSYNC.ZIP is the same driver disk for users with a DOS ZIP utility. Extract
it on the target computer and run XSETUP C:\WINDOWS from the extracted folder.
The complete XRSYNC.EXE download does not require extraction.

Existing differing C:\XR155 files are refused rather than overwritten.
Missing or wrong Windows support is reported before creating the OEM disk.
Use Windows Setup to choose the previous display if you want to switch back.
After selecting XRSYNC, use RUNSYNC; STARTXT/FIXXT belongs to the original
HPXY profile. No manual SYSTEM.INI or launcher-pin changes are needed.

This installs the synchronous Output display update, not the full rc.8 shell.
Its 60,800-byte driver is unchanged from the qualified graphics release.
The logical desktop is 640x256 through a 320x200, sixteen-colour viewport.

QUALIFICATION AND NOTICES
DOS 3.20 / 8088 emulator: native staging from another drive, missing-input
refusal, normal Windows Setup and a cold RUNSYNC cursor/panning probe.
Existing per-call pixel, marker, cursor, panning and RLE results are retained
in docs/RRSYNC.MD. Exact native installer results are in
 docs/QUAL/DOSINST/XRSYNC.JSN
at the source commit in RELEASE.JSON. No new physical test is claimed.

The download excludes Windows/DOS files, disk images and proprietary tools.
Your installed Windows CGA.GR2 is gathered locally and remains private.
See NOTICE.TXT, OWATCOM.TXT and the font/artwork notices.
