# Windows XT

Windows XT brings color graphics, a compact Start-menu desktop, games and
utilities to Windows 3.0 on the Tandy 1000 EX/HX.

| Startup | Desktop | Shutdown |
| --- | --- | --- |
| <img src="docs/PROMO/XTWAVE.GIF" alt="Windows XT slow flag wave startup" width="260"> | <img src="examples/HILLS/HILL320.PNG" alt="Windows XT green hill desktop" width="260"> | <img src="docs/PROMO/XTEXIT.PNG" alt="Windows XT moon and stars after shutdown" width="260"> |

[User manual](docs/USERMAN.MD) · [Downloads and installation](#get-started)

## Before and Windows XT

| Before: Windows 3.0, four colors | Windows XT: sixteen colors |
| --- | --- |
| <img src="docs/PROMO/BF2030.PNG" alt="Program Manager from Chad's older four-color Windows 3.0 video" width="390"> | <img src="docs/PROMO/PBRUSH16.PNG" alt="Windows XT Paintbrush with a colorful hill canvas and all sixteen palette colors" width="390"> |

From [Chad's earlier video](https://www.youtube.com/watch?v=yNisFBDLXos&t=1230s).
Paintbrush in 320x200, with all 16 palette colors. Different modes; appearance comparison. [Capture details](docs/PROMO/SHOWCASE.MD#earlier-windows-30-video).

## Features

- Five graphics modes, including 320x200 in 16 colors.
- Tandy Start: Programs, My Computer, Run/Browse and a clock.
- Long filename browsing for existing names on supported DOS 6.22 FAT volumes.
- Games, screen savers, green hill wallpaper and optional
  [Tandy sound](https://github.com/astrobleem/oemsound-tandy).
- Original MIT-licensed bitmap fonts and static logo.
- DOS display-mode menu with undo and interrupted-switch recovery.
- Faster guarded startup and normal installation with zero SHA verification.
- Short animated startup and a moon-and-stars shutdown screen.

Experimental software. Requires your own Windows 3.0 installation, DOS 3.3+
and a supported Tandy 1000 EX/HX with 640 KB RAM.

## Apps

| [Buddy Holly · Tandy sound](https://github.com/astrobleem/oemsound-tandy) | [Maze preview](examples/MAZE/GAME/README.MD) | [Tandinator](examples/TANDINAT/README.MD) |
| --- | --- | --- |
| <a href="https://github.com/astrobleem/oemsound-tandy"><img src="https://raw.githubusercontent.com/astrobleem/oemsound-tandy/5411fe5f9c2cccdbe09900a779ebda382a407a74/docs/SHOTS/BUDCAP04.GIF" alt="Genuine Buddy Holly animated capture from the Tandy sound companion" width="260"></a> | <img src="docs/PROMO/XTMAZE.PNG" alt="New Maze game in Windows XT" width="260"> | <img src="examples/TANDINAT/SHOTS/320x200x16.PNG" alt="Canonical Tandinator v0.2 character guessing game" width="260"> |

Buddy Holly is a silent GIF; click it for the sound companion.
Maze is a separate preview; the disk image includes the older saver.
[Pinball](examples/PINBALL/README.MD), [Cookie Clicker](examples/COOKIE/README.MD)
and more are in the user manual.
[Capture details](docs/PROMO/SHOWCASE.MD).

## Get started

**[Download Windows XT 0.1.0-rc.6](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/v0.1.0-rc.6)**
— [720 KB disk ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.6/WINXT720.ZIP)
or [disk image](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.6/WINXT720.IMG).

Back up Windows, then follow the [installation guide](tools/FLASHDISK/README.MD).
Use the guarded `C:\WINXT\WINXT` launcher after installation.

The [short animated startup](examples/WXTSPL/WAVE/README.MD) is enabled by
the guarded installer in Color mode; other modes retain static startup.
The [original fonts](docs/FONTS/README.MD) are included. Windows and the CGA.GR2
non-font support file still come from your own installation/media.
[Optional experimental downloads](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experiments-2026-10-07)
have their own installation guides.

## Other video hardware: experimental drivers

These are separate experimental driver packets for cloned Windows 3.0 installs.
Back up the complete installation and follow the machine's recovery guide.
Physical hardware and fresh Windows Setup integration remain unqualified.

| Machine/card | Mode and download | Status and guide |
| --- | --- | --- |
| [Amstrad PC1512](https://github.com/astrobleem/windows-3-amstrad-pc1512) | [PC1512.DRV, 640x200x16](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PC1512.ZIP) | Emulator rendering evidence; one cursor-state case remains unresolved. [Install/recover](experiments/DISPLAY3/PC1512.TXT) |
| [IBM PCjr](https://github.com/astrobleem/windows-3-pcjr) | [TNDYJR.DRV, 320x200x16](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PCJR.ZIP) | Emulator-tested; guard required before every start. Real PCjr expanded-memory reservation remains unqualified. [Install/recover](experiments/DISPLAY3/PCJR.TXT) |
| [IBM XT + Plantronics ColorPlus](https://github.com/astrobleem/windows-3-plantronics) | [PCP3216.DRV, 320x200x16](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PCP3216.ZIP) | Emulator rendering evidence; requires the ColorPlus card and its dedicated VRAM. [Install/recover](experiments/DISPLAY3/PCP3216.TXT) |

[Experimental release, source and checksums](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experimental-displays-2026-10-12)
and [qualification scope](experiments/DISPLAY3/README.MD). Tandy EX/HX users
should continue with Windows XT rc.6 above. This release includes no TXT40
or TGA-II driver and no Windows, DOS, font/grabber, ROM or compiler files.

PCjr [PR #138](https://github.com/astrobleem/oemdisplay-tandy/pull/138) merged at [613137d](https://github.com/astrobleem/oemdisplay-tandy/commit/613137d0029817b42e141a11685182d867da911d) after 40 host tests. It adds a clean-install [screenshot](https://github.com/astrobleem/oemdisplay-tandy/blob/613137d0029817b42e141a11685182d867da911d/docs/pcjr/INSTALL/DESKTOP.PNG) and [26/26 session record](https://github.com/astrobleem/oemdisplay-tandy/blob/613137d0029817b42e141a11685182d867da911d/docs/pcjr/INSTALL/SESSION.JSN); both [post-merge install checks](https://github.com/astrobleem/oemdisplay-tandy/actions/runs/39078997906) and [disk build](https://github.com/astrobleem/oemdisplay-tandy/actions/runs/39078997999) passed. The merge did not publish a new PCJR.ZIP.

## Display modes

| Resolution | Colors |
| --- | ---: |
| **320x200** | **16 — default** |
| 640x200 | 2 |
| 640x200 | 4 |
| 320x200 | 4 |
| 160x200 | 16 |

**Tandy Video II 640x200x16: experimental SL/2 family only ([front door](https://github.com/astrobleem/windows-3-tandy-video-ii)).**
[Download TNDYV2.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-video-ii-2026-10-14-r2/TNDYV2.ZIP)
and read the [release notes and qualification](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experimental-video-ii-2026-10-14-r2)
and [Setup, owned-file staging and recovery guide](docs/tga2/INSTALL.TXT).
Windows rendering evidence covers the emulated SL/2 only. Physical hardware,
other SL/TL/RL models and Windows 3.1 remain unqualified; EX/HX must not use
this driver. Run T2RESV successfully before Setup and every Windows start.

[TEXT80 and compact C25](docs/TEXT80.MD) ([front door](https://github.com/astrobleem/text-mode-windows)) are merged experimental text-mode
driver profiles with emulator evidence. C25 passed 54/54 in 86Box 6.0 build
9001 on an emulated IBM XT/CGA (8088, 4.77 MHz); see the [Notepad capture](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/1dc95619dde79663d0e1d9e1c7d251b00978b7ed/docs/text80/RUN_c3/c80w3/notepad.png)
and [tested commit 1dc9561](https://github.com/astrobleem/oemdisplay-tandy/commit/1dc95619dde79663d0e1d9e1c7d251b00978b7ed). No current TEXT80/C25 binary
package has been released; the older rc.6 TXTMODE feasibility driver is historical.
Olivetti PC1/Yamaha has no public driver package, source packet, or machine-specific
emulator capture/qualification record ([front door](https://github.com/astrobleem/windows-3-olivetti-pc1)); no download is available, and hardware
support remains unqualified.

The physical HPAN R3 run is accepted; no public package or evidence bundle
is published. The combined HPXY candidate remains private and emulator-tested;
physical XY qualification is pending and no public download is available.

For mode details, the text-mode experiment, app guides, long filename
requirements and recovery, see the [user manual](docs/USERMAN.MD).
[Development status](docs/STATUS.MD) · [Build guide](BUILDING.MD)

## Screen savers

| [Starfield](experiments/VISPART2/README.MD) | [Matrix](experiments/VISPART1/README.MD) |
| --- | --- |
| <img src="docs/SHOTS/STARS10.PNG" alt="Native Starfield screen saver capture" width="390"> | <img src="docs/SHOTS/MATRIX.PNG" alt="Native Matrix screen saver with green trails" width="390"> |
