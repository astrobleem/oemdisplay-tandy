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
| Install or update the current XR1 desktop, panning and wheel input | **rc.8:** [installer ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINXT-XR1.ZIP) · [prepare, install and recover](docs/RELEASES/RC8.MD) |
| Converted Minesweeper app and About shim | **rc.8:** [Minesweeper ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINMINE30.ZIP), including its installation guide |

Supply the matching Windows 3.0 media; **all required project components are
included**. Use Python on a modern computer to prepare the files, then run
`C:\SETUPXT` from plain DOS. Back up Windows first; start afterward with
`C:\STARTXT`. Public downloads contain no Windows or DOS installation media. Keep prepared
own-media folders private. [Earlier packages](docs/RELEASES/RC8.MD#verification-and-notices) remain available.

## More color, compact controls

| Before: Windows 3.0, four colors | Windows XT: sixteen colors |
| --- | --- |
| <img src="docs/PROMO/BF2030.PNG" alt="Four-color Windows from the earlier Tandy video" width="390"> | <img src="docs/PROMO/PBRUSH16.PNG" alt="Windows XT Paintbrush with a colorful hill and sixteen-color palette" width="390"> |

- Tandy Start: Programs, My Computer, Run/Browse and a clock.
- Original XT Pixels bitmap fonts and compact controls.
- Read existing long filenames on compatible DOS 6.22 FAT volumes.
- A DOS display-mode menu with undo and interrupted-switch recovery.
- Optional Hold-to-Start with the [compatible keyboard driver](src/tandyk3/README.md).

XR1 shows a **640x256 logical desktop through a 320x200, sixteen-color view**.
Keyboard panning brings off-screen windows and controls into reach.
[XR1 controls and installation](docs/RELEASES/RC8.MD#what-is-current) ·
[Original fonts](docs/FONTS/README.MD)

The earlier five fixed profiles, including 640x200 and 160x200, remain separate
downloads. [Mode details](docs/MODES.MD).

## More room to play

The current XR1 package includes panning and the combined drawing improvements.
The captures below retain their original, separately documented test scope.

| More room for windows | A board beyond the screen |
| --- | --- |
| <img src="docs/pan/DEMO.GIF" alt="Emulator demonstration of vertical software panning" width="390"> | <img src="docs/pan/MINE/REVEAL.PNG" alt="Converted Minesweeper demonstration in the emulator's larger desktop" width="390"> |

Use Ctrl+Alt+arrows to pan and Ctrl+Alt+Home to return home. XYCTL's menu or
Ctrl+Alt+H switches between software and hardware presentation.
[Download Minesweeper and its shim](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINMINE30.ZIP) ·
[Capture notes](docs/pan/MINE/CAPTURE.MD).

<img src="docs/rrect/TIMELINE.PNG" alt="Matched emulator captures comparing the original and optimized Calculator repaint" width="640">

One Calculator repaint fell from **92.5 to 10.4 seconds** in a matched emulator
experiment. That comparison has its own [drawing test scope](docs/RRECT.MD).

## Games, savers and sound

| [Maze preview](examples/MAZE/GAME/README.MD) | [Tandinator](examples/TANDINAT/README.MD) | [Tandy Winamp](https://github.com/astrobleem/oemsound-tandy/releases/tag/tandy-winamp-ux3.20261018) |
| --- | --- | --- |
| <img src="docs/PROMO/XTMAZE.PNG" alt="Windows XT Maze preview" width="260"> | <img src="examples/TANDINAT/SHOTS/320x200x16.PNG" alt="Tandinator character-guessing game" width="260"> | <img src="https://raw.githubusercontent.com/astrobleem/oemsound-tandy/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/docs/SHOTS/WAMPUI3.PNG" alt="Tandy Winamp companion with a scrolling playlist" width="260"> |

Try [Pinball](examples/PINBALL/README.MD), [Cookie Clicker](examples/COOKIE/README.MD),
[Starfield](experiments/VISPART2/README.MD) and [Matrix](experiments/VISPART1/README.MD).
XR1 includes the current Maze game/saver, Pinball, Starfield and Matrix.

The separate [Tandy sound companion](https://github.com/astrobleem/oemsound-tandy)
includes Winamp's playlist player, PSG music and Beats/Fiddle tools.
[Download Winamp UX3](https://github.com/astrobleem/oemsound-tandy/releases/download/tandy-winamp-ux3.20261018/TWUX3.ZIP) ·
[App and sound details](docs/SHOWCASE.MD#apps-input-and-sound)

## Compatibility and source

Experimental software: earlier HPXY panning was accepted on a real EX; the
current XR1 package and new first-party wheel driver are emulator-qualified.
That does not certify every mode or app. Windows 3.1 is not supported.
[Hardware and capture scope](docs/SHOWCASE.MD#panning-on-real-tandy-hardware)

Other machines use [separate driver packages](docs/PLATFORM.MD), including
Video II, PC1512, PCjr, Plantronics, Yamaha and text-mode experiments.

The original wheel/font kit is MIT-licensed; adapted drivers and other
components retain their own [notices](tools/XR1PACK/NOTICE.TXT).
[Provenance](tools/XR1PACK/PROVENANCE.JSN) ·
[Build guide](BUILDING.MD) · [Development notes](docs/STATUS.MD) ·
[Canonical source](https://github.com/astrobleem/oemdisplay-tandy)
