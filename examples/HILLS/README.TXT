WINDOWS XT - GREEN HILL DESKTOP
Original pixel landscape. 4 October 2026.
Windows 3.0 real mode, Tandy 16-color modes.

This is ordinary Windows desktop wallpaper. It starts with Windows behind
Tandy Start. It is not the boot splash. No new resident program, timer,
shell code, driver, or startup application is installed.

INSTALL (OPT IN)
1. Exit Windows. Extract HILLS under C:\WINXT and keep it there.
   Create the WINXT directory first if it does not already exist.
2. Make a NEW backup of C:\WINDOWS\WIN.INI. Never overwrite an older backup.
   Example, ONLY if C:\WINXT\HILLS\WINBAK.INI does not already exist:
     COPY C:\WINDOWS\WIN.INI C:\WINXT\HILLS\WINBAK.INI
3. Open your existing WIN.INI in DOS EDIT or Notepad. Find [desktop].
   Change only Wallpaper and TileWallpaper in that EXISTING section.
   Do not replace the entire INI file or add duplicate sections/keys.

   For 160 x 200, 16 colors:
     Wallpaper=C:\WINXT\HILLS\HILL160.BMP
     TileWallpaper=0

   For 320 x 200, 16 colors:
     Wallpaper=C:\WINXT\HILLS\HILL320.BMP
     TileWallpaper=0

   Alternatively use Windows Control Panel > Desktop > Wallpaper, enter
   the full matching BMP pathname and choose Center, then OK.
4. Restart Windows with your usual TSTART command.

Choose the file matching your CURRENT color mode. Windows 3.0 does not
stretch it. These are full-screen, precomputed 4-bit Windows BMPs, with
native RGBI colors and standard padded rows, not a conversion at startup.
HILL160.BMP = 16,118 bytes. HILL320.BMP = 32,118 bytes.
The lower 22 desktop pixels naturally sit behind the Start bar.

RESTORE / DISABLE
Exit Windows. Compare [desktop] in C:\WINXT\HILLS\WINBAK.INI with your current
WIN.INI. Restore only the previous Wallpaper and TileWallpaper values.
If a key was absent in the backup, remove that key from the current file.
Keep all other current settings, including changes made since installation.
Restart Windows. Do not copy the whole backup over newer INI settings.
For a plain desktop, Control Panel > Desktop > Wallpaper > (None) also works.

MODE CHANGES
Before selecting the 640-pixel monochrome driver, turn wallpaper off or
restore the earlier settings. This pack is intentionally color-only; no
monochrome conversion, low-memory auto-switching, or automatic mode change
is installed. Use the plain desktop if the extra bitmap memory matters.

The existing moon boot splash, drivers, shell executable, sound and saver
settings are untouched. Physical hardware acceptance is not claimed.
Native emulator results and limits are in TESTS.TXT.

REBUILD ART
Run python3 BUILDART.PY on a modern host with Pillow installed. It writes
verified BMPs and enlarged artwork previews under assets/; no Python is
needed on the Tandy. HILL160.PNG and HILL320.PNG beside this guide are
actual Windows emulator captures; their doubled axes are display scaling.
