# Rotating Cube screensaver

[Download CUBE.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CUBE.ZIP)
for Windows 3.0 real mode on an 8088 with normal 640 KB. It uses your installed
display driver; the kit includes the native DOS installer and all app files.

## Install from DOS

Expand the whole ZIP into a DOS folder and exit Windows completely. Run:

```text
CUBESET C:\WINDOWS
```

Use your actual full Windows directory. Cube is installed in `C:\WINXT`.
The recognized Windows XT Tandy Start receives a matching optional shell/input
update. The originals are kept as `TSHCUBE.BAK` and `TICUBE.BAK`; existing
saver choice, delay and other settings are retained. Select **System > Screen
saver > Cube > Apply** to enable automatic idle launch. **Options** opens its
settings. The delay accepts 10-3600 seconds.

For stock Windows 3.0 or an unrecognized Tandy Start, use:

```text
CUBESET /APPONLY C:\WINDOWS
```

This installs Cube alone and preserves the shell. Stock Windows 3.0 has no
3.1-style saver selector. No Python, driver gathering or manual INI edit is
needed for either installation route.

## Settings and wake

Inside Windows, run `C:\WINXT\CUBE.EXE /C`. Cycle Style, Speed and Cube size;
each speed and size has three choices. **Save** stores them and **Preview**
tries the current choices. Both panels fit the tested 160x100 compact display.
Run `C:\WINXT\CUBE.EXE /S` for a standalone saver.

- **Auto:** ordered dithering on monochrome displays, flat shading on color.
- **Flat:** solid face illumination mapped to the installed palette.
- **Dither:** ordered black/white patterns provide more light levels.
- **Wire:** all twelve cube edges. Small size or Wire reduces drawing work.

One new keyboard gesture, mouse movement or mouse button dismisses the saver.
Held wake gestures are drained. Task switching, lost focus/capture and shutdown
also dismiss it. It is not a password lock. Few-color palettes have fewer solid
shade levels; choose Dither for more visible intermediate illumination.

## Undo the optional shell update

Choose another saver, exit Windows and run:

```text
CUBESET /UNDO C:\WINDOWS
```

This restores the original shell/input pair and leaves Cube for standalone
use. Unknown changed files are preserved. Keep the backups if recovery reports
a problem, and resolve a pending transaction before restarting Windows.

## Qualification and source

Eight Windows 3.0 real-mode emulator fixtures cover CGA 160x100, 320x200 and
640x200 mono, Tandy 160x200 and 320x200 in sixteen colors, Tandy 640x200
in four colors, and two panning desktops.
All three drawing styles passed 624 QA frames and 48 matching white readbacks.
Settings, preview ownership, actual idle/wake and DOS installation/undo guards
passed separately. [Exact drivers, palettes, viewports and limits](../examples/CUBE/TESTS.MD)
remain the qualification scope. Physical hardware, composite output, unlisted
driver/font combinations, Windows 3.1 and injected installer faults are unqualified.

![Dithered Cube in decoded 160x100 CGA memory](../examples/CUBE/EVIDENCE/LOW02/STYLE2-VRAM.PNG)

This is a nearest-neighbor view of logical RGBI pixels, not a physical monitor
or calibrated pixel-aspect measurement.

[CUBESRC.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CUBESRC.ZIP)
contains first-party source, evidence and rebuild guidance. Native tools,
Windows media, installed guests and ROMs are excluded. The frozen producer is
`797b33a390cd63d7afd0da991e70edd407cc3d89`.
[CUBE.JSN](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CUBE.JSN)
and [CUBE.SHA](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CUBE.SHA)
pin the exact installer and source packets. The four core Windows XT assets
and their accepted runtime binaries are unchanged by this optional add-on.
