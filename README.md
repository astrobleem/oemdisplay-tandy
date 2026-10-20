# Windows XT

**A colorful little Windows desktop for an 8088 Tandy.**

Windows XT brings color graphics, a compact Start-menu desktop, games and
utilities to Windows 3.0 on the original Tandy 1000 EX/HX.

| Startup | Desktop | Shutdown |
| --- | --- | --- |
| <img src="docs/PROMO/XTWAVE.GIF" alt="Windows XT animated startup" width="260"> | <img src="examples/HILLS/HILL320.PNG" alt="Tandy Start with optional green hill wallpaper" width="260"> | <img src="docs/PROMO/XTEXIT.PNG" alt="Windows XT moon-and-stars shutdown screen" width="260"> |

[Get started](#get-started) · [User manual](docs/USERMAN.MD) ·
[More screenshots and capture notes](docs/SHOWCASE.MD)

## Get started

Requires **Windows 3.0 real mode, DOS 3.3+ and 640 KB RAM** on an EX/HX.

| What you want | Download and guide |
| --- | --- |
| Install the Windows XT desktop and graphics modes | **rc.6:** [720 KB ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.6/WINXT720.ZIP) · [disk image](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.6/WINXT720.IMG) · [install and recover](docs/USERMAN.MD#install-windows-xt) |
| The newer wheel driver and fonts, with source and MIT notices | **rc.7:** [first-party kit](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/WINXT-FIRST-PARTY-R1.zip) |
| Update an existing matching local R1 setup | **rc.7:** [R1 overlay](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/WINXT-REDISTRIBUTABLE-OVERLAY-R1.zip) · [prerequisites and instructions](docs/RELEASES/RC7.MD) |

The R1 overlay is **not a standalone installer**. It needs the matching local
Windows files and separately supplied project components; Windows media alone
is insufficient. The wheel kit also needs a compatible wheel client to scroll.

Back up Windows before installing. For rc.6, follow the guide and use the
guarded `C:\WINXT\WINXT` launcher afterward. Public downloads contain no
Microsoft Windows or DOS media; keep assembled own-media folders private.

## More color, compact controls

| Before: Windows 3.0, four colors | Windows XT: sixteen colors |
| --- | --- |
| <img src="docs/PROMO/BF2030.PNG" alt="Four-color Windows from the earlier Tandy video" width="390"> | <img src="docs/PROMO/PBRUSH16.PNG" alt="Windows XT Paintbrush with a colorful hill and sixteen-color palette" width="390"> |

- Tandy Start: Programs, My Computer, Run/Browse and a clock.
- Original XT Pixels bitmap fonts and compact controls.
- Read existing long filenames on compatible DOS 6.22 FAT volumes.
- A DOS display-mode menu with undo and interrupted-switch recovery.
- Optional Hold-to-Start with the [compatible keyboard driver](src/tandyk3/README.md).

| Graphics mode | Colors |
| --- | ---: |
| **320×200** | **16 — default** |
| 640×200 | 2 or 4 |
| 320×200 | 4 |
| 160×200 | 16 |

These are five profiles; narrow modes can clip wide Windows dialogs.
[Mode details](docs/MODES.MD) · [Original fonts](docs/FONTS/README.MD)

## Experiments in motion

These separate experiments have their own setup and are not in the rc.6 installer.

| More room for windows | A board beyond the screen |
| --- | --- |
| <img src="docs/pan/DEMO.GIF" alt="Emulator demonstration of vertical software panning" width="390"> | <img src="docs/pan/MINE/REVEAL.PNG" alt="Converted Minesweeper demonstration in the emulator's larger desktop" width="390"> |

Panning brings off-screen windows and buttons into view. See the
[software-panning guide](docs/PAN.MD) and [hardware-panning packages](downloads/experimental/hpan-hpxy/README.md).
The converted Minesweeper app and shim shown here are not distributed.

<img src="docs/rrect/TIMELINE.PNG" alt="Matched emulator captures comparing the original and optimized Calculator repaint" width="640">

One experimental Calculator repaint fell from **92.5 to 10.4 seconds** in a
matched emulator run. [Drawing work and exact test scope](docs/RRECT.MD).

## Games, savers and sound

| [Maze preview](examples/MAZE/GAME/README.MD) | [Tandinator](examples/TANDINAT/README.MD) | [Tandy Winamp](https://github.com/astrobleem/oemsound-tandy/releases/tag/tandy-winamp-ux3.20261018) |
| --- | --- | --- |
| <img src="docs/PROMO/XTMAZE.PNG" alt="Windows XT Maze preview" width="260"> | <img src="examples/TANDINAT/SHOTS/320x200x16.PNG" alt="Tandinator character-guessing game" width="260"> | <img src="https://raw.githubusercontent.com/astrobleem/oemsound-tandy/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/docs/SHOTS/WAMPUI3.PNG" alt="Tandy Winamp companion with a scrolling playlist" width="260"> |

Try [Pinball](examples/PINBALL/README.MD), [Cookie Clicker](examples/COOKIE/README.MD),
[Starfield](experiments/VISPART2/README.MD) and [Matrix](experiments/VISPART1/README.MD).
Maze is a separate game preview; the installer retains the older saver.

The separate [Tandy sound companion](https://github.com/astrobleem/oemsound-tandy)
includes Winamp's playlist player, PSG music and Beats/Fiddle tools.
[Download Winamp UX3](https://github.com/astrobleem/oemsound-tandy/releases/download/tandy-winamp-ux3.20261018/TWUX3.ZIP) ·
[App and sound details](docs/SHOWCASE.MD#apps-input-and-sound)

## Compatibility and source

Experimental software: earlier HPXY panning was accepted on a real EX, but the
final R1 package and new first-party wheel driver remain emulator-qualified.
That does not certify every mode or app. Windows 3.1 is not supported.
[Hardware and capture scope](docs/SHOWCASE.MD#panning-on-real-tandy-hardware)

Other machines use [separate driver packages](docs/PLATFORM.MD), including
Video II, PC1512, PCjr, Plantronics, Yamaha and text-mode experiments.

The original wheel/font kit is MIT-licensed; other components retain their
own notices. [Provenance](tools/WINR1/KIT/mouse/PROVENANCE.md) ·
[Build guide](BUILDING.MD) · [Development notes](docs/STATUS.MD) ·
[Canonical source](https://github.com/astrobleem/oemdisplay-tandy)
