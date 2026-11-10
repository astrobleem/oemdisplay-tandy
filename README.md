# Windows XT

**A colorful little Windows desktop for an 8088 Tandy.**

Windows XT brings color graphics, a compact Start-menu desktop, games and
utilities to Windows 3.0 real mode on the original Tandy 1000 EX/HX.

**[Watch the Windows XT overview video](https://youtu.be/A1i9R6zSxHY)**

| Startup | Desktop | Shutdown |
| --- | --- | --- |
| <img src="docs/PROMO/XTWAVE.GIF" alt="Windows XT animated startup" width="260"> | <img src="examples/HILLS/HILL320.PNG" alt="Tandy Start with optional green hill wallpaper" width="260"> | <img src="docs/PROMO/XTEXIT.PNG" alt="Windows XT moon-and-stars shutdown screen" width="260"> |

[Get started](#get-started) · [Other machines](#other-machines) ·
[All downloads](docs/DOWNLOADS.MD) · [Screenshots and capture notes](docs/SHOWCASE.MD)

## Get started

**[Download the Windows XT pack: WXTF1107.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WXTF1107.ZIP)**

For an **original Tandy 1000 EX/HX with normal 640 KB and Windows 3.0 real mode**.
You supply DOS and Windows. Extract the ZIP with folders intact; keep
`SETUP.EXE`, `README.TXT` and the expanded `WINXT` folder together.

- **Full desktop, DOS 3.3+:** exit Windows and run `SETUP UPDATE C:\WINDOWS`.
  For a new Windows installation, use `SETUP FRESH A:\` with your original
  Windows media. Use `C:\STARTXT` for every later session.
  [Full installation](docs/DESKTOP.MD).
- **Drivers only, existing Windows and DOS 3.20+:** run `DISPLAY` from the
  expanded `WINXT` folder. In Windows Setup choose **Display > Other**, enter
  that folder's full path and select a display. Use `DISPWIN` from the same
  folder for every later session. [Driver installation](docs/DRIVERS.MD).

Fonts, grabber, startup artwork and memory guards are included. No Python,
manual INI edits or separate support-file collection is needed.

New full installations default to **fixed 320x200, sixteen colors, without
panning**. Updates preserve the installed display and panning choice. The
same pack includes all five optimized fixed profiles:
**320x200x16, 640x200x4, 320x200x4, 160x200x16 and 640x200 monochrome**.
Choose another profile or optional HPXY through Windows Setup.

**Before updating:** if you use the separate UISET compact-controls add-on,
run `UISET C:\WINDOWS OFF` for each enabled display mode first. That add-on
is not included in this pack. [Update instructions](docs/DESKTOP.MD).

The latest pack passed emulator preparation, update and finishing checks.
A complete clean Windows installation remains unqualified: the latest original
Setup attempt stalled during hardware detection before file copying.
[Release notes and limits](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/windows-xt).

## What's included

| Before: Windows 3.0, four colors | Windows XT: sixteen colors |
| --- | --- |
| <img src="docs/PROMO/BF2030.PNG" alt="Four-color Windows from the earlier Tandy video" width="390"> | <img src="docs/PROMO/PBRUSH16.PNG" alt="Windows XT Paintbrush with a colorful hill and sixteen-color palette" width="390"> |

- **Tandy Start:** existing Program Manager groups, My Computer, Run/Browse,
  a clock and screen-saver settings.
- **Faster drawing:** optimized fixed drivers, plus HPXY bitmap and panning
  improvements. Performance results are emulator measurements, not hardware
  timings. [Fixed-driver changes](https://github.com/astrobleem/oemdisplay-tandy/pull/218) ·
  [HPXY results](docs/QUAL/HPDIB).
- **Keyboard and mouse:** the Tandy keyboard driver and optional Hold-to-Start,
  plus a serial wheel-mouse driver and Windows scrolling support.
  [Input details and scope](docs/USERMAN.MD#keyboard-mouse-and-joystick).
- **DOS clipboard:** Shift+Print copies DOS text or graphics into Windows.
  [Supported modes and palette limits](docs/GRABBER.MD).
- **Long-name browsing:** Run/Browse can display existing long filenames on
  supported DOS 6.22 FAT12/FAT16 volumes, then launch through their DOS aliases.
  It does not add system-wide long-filename support.
  [Requirements](distributions/WINXT/NAMES11.TXT).
- **Pinball, four screen savers, original bitmap fonts, startup and shutdown
  artwork**, plus a DOS display-mode menu with undo and interrupted-switch recovery.

## One panning application

**PAN** detects the installed display and selects its backend automatically.
It is included in the Windows XT, CGA, PCjr and ColorPlus packets. The separate
**[PAN.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/PAN.ZIP)**
updates an existing supported display installation.

- **Tandy HPXY:** a 640x256 desktop through a 320x200, sixteen-color view,
  with Software or Hardware presentation.
- **PCjr and ColorPlus:** a 640x400 software desktop through a 320x200,
  sixteen-color view, panning on both axes. Fixed 320x200 is also available.
- **CGA 160x100 panning profile:** a 320x200 desktop through a 160x100 view.
- **Supported fixed displays:** an optional workspace that moves windows
  while keeping the fixed framebuffer.

Press **Ctrl+Alt+S** or run `PAN /SETTINGS`. **Ctrl+Alt+arrows** move,
**Ctrl+Alt+Home** returns home and **Ctrl+Alt+End** brings the active window
into view. `PAN OFF` disables panning; `PAN` enables it again.
[Installation, controls and memory requirements](docs/PANNING.MD).

## Fonts

The compatible narrow **M/W System font** preserves Windows 3.0 dialog spacing.
It updates recognized XTCSYS fonts used by HPXY and the four XTC fixed modes;
fresh fixed 320x200 sixteen-color installations retain their XTE fonts.
Custom font choices and application-font registrations are preserved.

Six optional fonts provide **XT Tandy I**, **XT Tandy II** and **XT Tandy 2K**
in 8-row and 12-row forms. Full Setup puts them in `C:\WINXT\FONTS`;
add the ones you want through **Control Panel > Fonts > Add**.
Three compact **Helv** fonts are also included. Leave those unselected if you
want to keep your present Helv installation. [Font guide](docs/FONTS/README.MD).

## Games, savers and sound

Choose **Cube, Starfield, Matrix or Ovals** in **System > Screen saver**.
New installations use a five-minute idle delay; updates preserve your settings.
[Cube](docs/CUBE.MD) offers Flat, Dither and Wire styles and a standalone installer.
Ovals cycles through five animated scenes. Maze is a separate game/experiment,
not a saver in the current pack.

| [Maze preview](examples/MAZE/GAME/README.MD) | [Tandinator](examples/TANDINAT/README.MD) | [Tandy Winamp](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/TWXT2.ZIP) |
| --- | --- | --- |
| <img src="docs/PROMO/XTMAZE.PNG" alt="Windows XT Maze preview" width="260"> | <img src="examples/TANDINAT/SHOTS/320x200x16.PNG" alt="Tandinator character-guessing game" width="260"> | <img src="https://raw.githubusercontent.com/astrobleem/oemsound-tandy/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/docs/SHOTS/WAMPUI3.PNG" alt="Tandy Winamp companion with a scrolling playlist" width="260"> |

[Pinball](examples/PINBALL/README.MD) comes with the desktop. Add
[Cookie Clicker](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/COOKSET.ZIP),
[converted Minesweeper](tools/CURRENT/GUIDES/MINESET.TXT) or the
[TANDYLAB app collection](examples/TANDYLAB/README.MD) separately.
The [green hill wallpaper](examples/HILLS/README.TXT) shown above is optional.

The separate [Tandy sound companion](https://github.com/astrobleem/oemsound-tandy)
provides **Tandy Winamp**, PSG music and **Tandy Beats Lab/Fiddle** tools.
[App and sound downloads](docs/DOWNLOADS.MD).

## Other machines

Use the packet for your adapter; the EX/HX desktop pack is not a universal driver.

- **IBM CGA RGBI:** fixed/panning 160x100 in sixteen colors, standard or compact
  320x200 four-color and 640x200 monochrome. The kit also supports fresh Windows
  Setup with its 640x200 driver. [CGA installation](docs/CGA.MD).
- **IBM PCjr and Plantronics ColorPlus:** fixed or two-axis software-panning
  desktops. [Install guide](docs/SOFTPAN/RELEASE.MD).
- **Tandy SL/2 Video II, Amstrad PC1512, Olivetti PC1, standalone Yamaha and
  text-mode profiles:** [hardware choices and limits](docs/PLATFORM.MD).

[All hardware downloads](docs/DOWNLOADS.MD). Physical CGA/composite output,
PCjr and ColorPlus remain unqualified; consult each guide for its tested scope.

## Compatibility and source

Experimental software for **Windows 3.0 real mode**, not Windows 3.1. The
current pack is emulator-tested; earlier HPXY R1 panning was accepted on a real
Tandy 1000 EX. That does not qualify the current combined pack or every mode
and app. Narrow displays can still clip standard Windows dialogs.
[Hardware and capture scope](docs/SHOWCASE.MD#panning-on-real-tandy-hardware).

The original wheel/font kit is MIT-licensed; adapted drivers and other
components retain their own [notices](tools/XR1PACK/NOTICE.TXT).
[Build guide](BUILDING.MD) · [Development notes](docs/STATUS.MD) ·
[Canonical source](https://github.com/astrobleem/oemdisplay-tandy).

For separate source-only DOS and portable C89 Tandy components, see
[libtandy](https://github.com/astrobleem/libtandy). This Windows display driver
does not depend on that library.
