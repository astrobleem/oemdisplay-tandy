WINDOWS XT - ONE SUPPORT FOLDER / SIX DISPLAY CHOICES
Windows 3.0 real mode on Tandy EX/HX / 8088

EVERYTHING GOES IN C:\WINXT
From the public 720 KB image, run A: then CD \ then INSTALL outside Windows.
PREPXT verifies your own matching Windows/media files and prepares C:\WINXT.
Then run C: then CD \WINXT then INSTALL. The complete prepared folder stays on
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
C:\WINXT\BACKUP\B001 (or the next unused number), and pauses so you can record the backup path before Windows Setup.
It uses your existing Windows SETUP program, not a hand-edited display setting.

In Setup:
1. Choose Display, then Other display.
2. Enter C:\WINXT.
3. Choose one of the six modes listed below.
4. Accept the configuration. If prompted for the display disk again, enter
   the same source folder. INSTALL writes its actual path into OEMSETUP.INF;
   OEMBASE.INF preserves the original source INF. No second directory is needed.
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
Tandy video memory, and starts real-mode Windows. Never bypass a reservation/recovery error
by starting WIN directly. In one of the five TR5 graphics modes, a verified
TSSETUP installation activates the Windows XT desktop for that session; the
original shell selection is restored on exit. Without it, your existing
Windows shell starts. Experimental text mode uses the original shell,
normally Program Manager on a fresh installation; TSHELL is not qualified
for that experimental driver.

STARTUP AND ROLLBACK
The guarded launcher enables the short slow flag wave for TR53216/TANDY88
Color. Lettering and pane colors stay steady; a key skips the animation.
This runs before loading Windows. Mono/other modes retain static startup.
INSTALL privately combines your exact owned SYSTEM\WIN.CNF with the original
logo module. Installed WIN.COM stays untouched by the wave updater; normal
Windows Setup still owns its display installation. Wrong loader bytes,
changed starters or altered wrapper files refuse startup safely.

To disable only the wave at plain DOS:
  C:\WINXT\WAVEXT RESTORE C:\WINDOWS C:\WINXT
This restores both original starters, retaining inactive private stages.
Re-enable with APPLY using the same arguments. Never bypass a refusal.
Full pre-install rollback uses WINXT\BACKUP\B001\RESTORE YES (use the actual
number printed by INSTALL). It disables the wave first and byte-verifies
the original Windows files. Added inactive helpers remain for inspection.
Do not redistribute the completed folder; it contains your own loader/fonts.

SIX DISPLAY CHOICES
320x200, 16 colors  - TR53216.DRV, EGA fonts, TR5 graphics driver
640x200, 4 colors   - TR56404.DRV, CGA fonts, TR5 graphics driver
160x200, 16 colors  - TR51616.DRV, CGA fonts, TR5 graphics driver
320x200, 4 colors   - TR53204.DRV, CGA fonts, TR5 graphics driver
640x200, 2 colors   - TR56402.DRV, CGA fonts, TR5 graphics driver
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

FIRST-RUN UPDATE (2026-10-08)
Programs includes a Windows XT group with Matrix, Maze and Starfield /S
saver previews, About and the bundled Pinball v2. Missing optional apps are
hidden. TP.EXE and TANDI.EXE appear only if separately supplied at their
configured C:\WINXT paths; they are not bundled by this disk. Program Manager
groups remain read-only. Exit keeps Cancel as the initial/default button;
E selects Exit, Enter initially cancels, and Escape cancels.

EXISTING LONG FILENAMES IN RUN / BROWSE
Existing VFAT names are read-only labels; DOS 8.3 aliases still own navigation
and launch. Requires genuine DOS 6.22, Windows 3.0 real mode, and a fixed,
uncompressed FAT12/FAT16 drive with 512-byte sectors. Network, removable,
SUBST/JOIN/ASSIGN and compressed volumes fall back to DOS names. The view
limits each filtered listing to 128 rows and labels to 63 displayed characters
with ellipsis. It does not create, rename or write long filenames.

The source INF becomes installation-specific after INSTALL. The released
MANIFEST.SHA pins the original media; OEMBASE.INF retains that original.
Keep the source drive mounted through Setup. Never run the guarded installer
directly from a small/read-only floppy: PREPXT stages to a writable C:\WINXT.
