OPTIONAL DISPLAY TOOLKIT - NOT AN INSTALL-READY DISK
====================================================
Leave this folder alone until your own Windows 3.0 installation works.
T88TOOLS.ZIP is the existing verified support-free toolkit: five accepted
first-party display drivers, RESERVE.COM, custom splash, Setup metadata,
DOS helper templates and the unchanged portable STAGE.PY validator.
No proprietary Windows support files are included here.

On the MODERN PC, extract T88TOOLS.ZIP into a NEW work folder. Its DISK1
is incomplete: do not run INSTALL yet. Its original README describes the
COMPLETED OEM disk, which only exists after successful staging below.

Supply your own matching Windows 3.0 files in one PC directory:
  EGASYS.FON EGAFIX.FON EGAOEM.FON
  CGASYS.FON CGAFIX.FON CGAOEM.FON CGA.GR2 CGALOGO.LGO
STAGE.PY validates exact accepted SHA256 values, file structure and the
first-party payload. Missing/ambiguous/wrong files fail before output.
The validator is intentionally strict; do not remove its hash checks.
Python 3.8+ is a MODERN PC staging dependency, not a Tandy runtime dependency.

Example after opening a PC command prompt in the extracted toolkit:
  py STAGE.PY --windows-files C:\WIN30SRC --out C:\T88OEM --windows-dir C:\WINDOWS

C:\WIN30SRC = your PC source folder; C:\T88OEM = NEW PC output folder.
The --windows-dir argument is the FUTURE TANDY DOS Windows path, not the
PC's card-reader drive letter. Replace C:\WINDOWS if your installation
uses another path. The accepted permanent DOS helper is C:\TANDY88.
Stage only into a new folder on the PC, then inspect the success report.
The script never edits installed Windows, existing folders or boot files.
It does not write the CF unless you explicitly choose a CF output path;
use the PC-local example instead. If Python isn't already available,
you can defer this optional work; it is not needed to copy the app pack.

After staging succeeds, manually copy the completed OEM folder to a NEW
folder on the card (for example D:\T88OEM on the PC), safely eject, then
use its README from DOS on the Tandy. Back up Windows and keep DOS recovery.
Recommended accepted sequence: stock-CGA Windows first; exit completely to
DOS; completed-disk INSTALL; C:\TANDY88\TANDY88 SETUP; Windows Setup's
Display / Other choice. Begin with 640x200 four-color for desktop width.
Setup installs matching fonts/driver and rebuilds WIN.COM. Do not manually
edit SYSTEM.INI to install display drivers. Use the guarded TANDY88 launcher
for every custom-driver Windows start, including later boots.

Modes: 320x200x16 (original), 640x200x4 (black/red/green/white),
160x200x16, 320x200x4 (black/cyan/magenta/white), 640x200x2.
Original EX/HX BIOS 0Ah is FOUR colors, never 640x200x16.

Requirements/limits: original EX/HX, normal 640 KB shared-memory layout,
BIOS/DOS reporting the accepted 624 KB arena, Windows 3.0 real mode and
DOS 3.0+. No XMS/EMS/UMB or expanded-base-memory workaround. RESERVE fails
closed for unsupported layouts; never bypass it. Native five-mode Setup
and rendering were tested in emulation, not on physical hardware.

Rollback: exit Windows to DOS; restore your known-good Windows backup or
use ordinary Windows Setup with your own appropriate media. Reboot releases
the reservation. Do not delete a helper that the active custom setup needs.
