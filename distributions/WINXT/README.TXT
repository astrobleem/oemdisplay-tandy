WINDOWS XT - ONE SUPPORT FOLDER / SIX DISPLAY CHOICES
Windows 3.0 real mode on Tandy EX/HX / 8088

EVERYTHING GOES IN C:\WINXT
Unzip on your modern computer. Copy the one WINXT folder to C:\WINXT on
your DOS drive. That folder holds all display sources, helpers, shell
companions and settings templates. Backups are created INSIDE WINXT\BACKUP.
There is no separate TDISPLAY, TANDY88 or TSTART support directory to create.
Windows keeps its normal operating-system and active driver files in WINDOWS.

FRESH INSTALL
Start at a plain DOS prompt, outside Windows. Install Windows 3.0 normally
first; the combined default path is C:\WINDOWS.

  C:
  CD \WINXT
  INSTALL

INSTALL verifies the source, preserves an original-file snapshot under
C:\WINXT\BACKUP\B001 (or the next unused number), and opens Windows Setup.
It uses your existing Windows SETUP program, not a hand-edited display setting.

In Setup:
1. Choose Display, then Other display.
2. Enter C:\WINXT.
3. Choose one of the six modes listed below.
4. Accept the configuration. If prompted for the display disk again, enter
   the SAME C:\WINXT. No second source directory is needed.
5. Accept Complete Changes. If asked about CONFIG.SYS, choose option 3:
   Setup can make NO changes for you.

For the included Windows XT desktop shell, also run once from DOS:

  C:\WINXT\TSSETUP

TSSETUP verifies and installs TSHELL.EXE, TSINPUT.DLL and TSHELL.INI in
WINDOWS. It refuses existing shell files rather than overwriting your old
configuration. Optional-shell backups stay in WINXT\BACKUP\SHELL14.
This optional step changes no permanent shell selection during installation.

ONE COMMAND TO START
At a fresh DOS prompt:

  C:\WINXT\WINXT

The launcher recovers any interrupted temporary shell selection, reserves
Tandy video memory, and uses WIN /R. Never bypass a reservation/recovery error
by starting WIN directly. In one of the five TR5 graphics modes, a verified
TSSETUP installation activates the Windows XT desktop for that session; the
original shell selection is restored on exit. Without it, your existing
Windows shell starts. Experimental text mode uses the original shell,
normally Program Manager on a fresh installation; TSHELL is not qualified
for that experimental driver.

SIX DISPLAY CHOICES
320x200, 16 colors  - TR53216.DRV, EGA fonts, TR5 Clock optimization
640x200, 4 colors   - TR56404.DRV, CGA fonts, TR5 Clock optimization
160x200, 16 colors  - TR51616.DRV, CGA fonts, TR5 Clock optimization
320x200, 4 colors   - TR53204.DRV, CGA fonts, TR5 Clock optimization
640x200, 2 colors   - TR56402.DRV, CGA fonts, TR5 Clock optimization
80x25 hardware text - TXTMODE.DRV, EXPERIMENTAL, known character corruption

The text choice is available through the same Setup list, not another folder.
Read TEXTMODE.TXT before choosing it. It is the existing feasibility driver,
not a stable replacement or a TR5-optimized driver. Setup selects its separate
TXTSYS.FON fixed-cell font; original graphics fonts remain unchanged.

CHANGE DISPLAY MODE
Exit Windows completely, then run:

  C:\WINXT\WINXT SETUP

Select Display -> Other, use C:\WINXT again, and choose your mode. Reboot
and use C:\WINXT\WINXT. This uses ordinary DOS Setup, not a live in-Windows
hardware mode switch. Switching back to a qualified graphics mode restores
its graphics fonts and enables the verified optional-shell launch path again.

RECOVER YOUR ORIGINAL WINDOWS CONFIGURATION
From plain DOS, use the backup path printed by INSTALL. For example:

  C:\WINXT\BACKUP\B001\RESTORE YES

Your actual numbered path is recorded in C:\WINXT\BACKUP.TXT. Restoration
checks its saved inputs and byte-verifies every restored file. It restores
original INIs, WIN.COM and saved Windows resources, and disables automatic
optional-shell dispatch by preserving its ready marker as SHREADY.OFF.
New driver/shell files are left in place but are no longer selected by the
restored configuration. The guarded WINXT launcher still reserves memory.
Do not remove your backup until the restored system works on your hardware.
A failed or interrupted restore must be resolved before Windows is started.
Boot files absent before installation are not deleted if Setup created them.

KNOWN LIMITS
- Stock Clock digital digits are invisible in the 320x200 four-color CGA
  palette, on both old Trial4 and TR5. Use analog there, or another mode.
- Stock Program Manager may retain old 640-pixel window positions on narrower
  screens. Alt+Space, X maximizes the active window.
- Paintbrush's unsaved-close prompt is wider than 160 pixels. Its N keyboard
  shortcut still discards an unsaved drawing; wider modes fit more stock UI.
- Matrix/Maze use their safe GDI path under new driver identities; this may
  be slower than an explicitly recognized direct-framebuffer mode.
- Experimental text has visible character/geometry damage. Full DOS-app
  grabber switching is unverified. See TEXTMODE.TXT.
- Tests include genuine guest DOS and Windows, not physical Tandy timing.

ABOUT THIS PACKAGE
The five graphics drivers include the bounded scanline-flush correction that
removes Clock's slow thick-border painting in the tested emulator. Stock
CLOCK.EXE is unchanged. See TESTS.TXT for exact coverage and qualifications.
The moon startup art is installed by Windows Setup with the Windows-owned
loader preserved. No replacement Windows/DOS installation is included.

This complete package contains your licensed Microsoft fonts, grabber and
logo loader, plus privately derived TXTSYS.FON. Do not mirror or redistribute
those support files publicly. Public source staging requires your own media.
Host build/source/evidence archives are separate; none is needed on the CF.
See SHELL14.TXT and HOLD14.TXT for shell/keyboard navigation details.

ADVANCED / EXISTING INSTALLATIONS
The display installer supports another Windows path, e.g. INSTALL D:\WIN30,
and writable 8.3 source paths. The integrated optional shell is specifically
C:\WINXT plus C:\WINDOWS. DOS 3.3+ is required; no long filenames or spaces.
Existing generated helpers or partial installs are refused safely. To change
modes use WINXT SETUP, not INSTALL again. Older root support folders are not
deleted automatically; this package's fresh layout needs only C:\WINXT.
