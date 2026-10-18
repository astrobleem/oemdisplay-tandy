# Windows XT

**Windows 3.0 real mode for the Tandy 1000 EX/HX (640 KB).** Windows XT adds five Tandy graphics modes, original bitmap fonts and a compact Start desktop to an 8088 that would otherwise be left in CGA.

[Download 720 KB ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.6/WINXT720.ZIP) · [Disk image](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.6/WINXT720.IMG) · [Release notes and checksums](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/v0.1.0-rc.6) · [Install and recover](docs/USERMAN.MD#install-windows-xt) · [User manual](docs/USERMAN.MD)

<img src="examples/HILLS/HILL320.PNG" alt="Actual Windows 3.0 desktop with Tandy Start in the 320x200x16 Tandy mode" width="640">

*DOSBox-X guest capture · Windows 3.0 real mode · Tandy 320×200×16 logical mode, displayed doubled. The hill wallpaper is optional and separate from RC6. [Capture provenance](docs/PROMO/SHOWCASE.MD#desktop) · [capture commit 43cf098](https://github.com/astrobleem/oemdisplay-tandy/commit/43cf0984f1d3da389231c55cdd82d8757074836a).*

## Current package: 0.1.0-rc.6 preview

Install into your own Windows 3.0 real-mode setup on a Tandy 1000 EX/HX with DOS 3.3+ and 640 KB. Windows/DOS media and the non-font support files remain user-supplied. Follow the [install, mode-change and recovery guide](docs/USERMAN.MD#install-windows-xt); after installation, start Windows with the guarded C:\WINXT\WINXT launcher.

RC6 includes the compact Tandy Start menu, Programs and Run/Browse controls, clock, shell-side `TSINPUT.DLL`, the Hold shortcut guide and 160/640-pixel screenshots, original MIT-licensed bitmap fonts, guarded mode switching with undo/recovery, and support for existing long names on compatible DOS 6.22 FAT volumes. Hold-to-Start is opt-in and needs the separate compatible `TNDYK3.DRV`; the ordinary Start button remains available with the stock keyboard. See [Hold instructions](distributions/WINXT/HOLD14.TXT), [160-pixel capture](distributions/WINXT/HOLD160.PNG), [640-pixel capture](distributions/WINXT/HOLD640.PNG), the [separate keyboard test candidate](src/tandyk3/README.md), and the [RC6 manifest](distributions/WINXT/MANIFEST.SHA). The exact release qualification and its emulator/host scope are in [RC6 qualification](docs/QUAL/RC6.MD); it is not a blanket physical-hardware certification.

| RC6 Tandy display mode | Colors |
| --- | ---: |
| 320×200 | 16 (default) |
| 640×200 | 4 |
| 160×200 | 16 |
| 320×200 | 4 |
| 640×200 | 2 |

## A desktop taller than its screen

<img src="docs/pan/DEMO.GIF" alt="Existing 86Box captures showing Windows XT's vertical software-panning experiment" width="640">

*86Box 6.0 · Tandy 1000 HX, 8088 at 7.16 MHz · Windows 3.0 real mode · 320×200×16 viewport over a 320×400 logical desktop. Existing captured frames; the [33/33 session record](docs/pan/FIT/XPWIN.JSN) is preserved at [test commit 6d48868](https://github.com/astrobleem/oemdisplay-tandy/commit/6d48868aa62fa5b7cf5d6ed8946dd7984582ace7).*

The XTPAN prototype makes lower windows and buttons reachable without changing the 320×200 display. Keyboard pans, edge dwell, cursor rendering and mouse hit-testing were checked; one 275-row dialog's bottom button was clicked after panning. This is software viewport panning, not CRTC hardware scrolling, and it is not in RC6. A Tandy 1000 EX owner reports XTPAN works on real hardware, but no scripted physical test of this software-panning prototype is recorded. The separate HPXY hardware-pan results below do not qualify XTPAN. See the [full investigation](docs/PAN.MD).

A separate Windows Minesweeper demonstration used one owner-supplied executable adapted for Windows 3.0 real mode on an 8088; panning lets a board extend below the visible 200 rows. This is an app-specific conversion, not a general x86 emulator. The executable and a verified Minesweeper screenshot are not in this public repository, so no Minesweeper download or image is shown. The panning test above verifies the driver behavior, not that app binary.

## Panning on real Tandy hardware

Panning keeps a 320×200 display while bringing the rest of a larger Windows desktop into view. HPXY R1 has been tested and accepted on the owner's real Tandy 1000 EX: Windows 3.0 real mode, stock-CGA profile, 7.16 MHz 8088, 640 KB. The scoped run recorded 54 pans, including 53 hardware operations, no ERROR records, return to software presentation at (0,0), and Windows exit code 0. That acceptance applies to this HPXY R1 configuration; it does not qualify other machines, display profiles or Windows 3.1. The next RC is planned to include this accepted panning feature; RC6 remains unchanged and does not include it.

| HPAN R3 | HPXY R1 |
| --- | --- |
| <img src="downloads/experimental/hpan-hpxy/HPAN-R3-86Box-FRAME314.png" alt="Original 86Box capture: emulated Tandy 1000 HX, Windows 3 real mode, 320×200×16 viewport over 640×200" width="360"> | <img src="downloads/experimental/hpan-hpxy/HPXY-R1-86Box-FRAME514.png" alt="Original 86Box capture: emulated Tandy 1000 HX, Windows 3.0 real mode, 320×200×16 viewport over 640×256" width="360"> |
| 86Box · Tandy 1000 HX · Windows 3 real mode · 320×200×16 display over 640×200 logical space. [Download HPAN R3 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/7c119ac1ee5428fa1a3a3c37e49d340c0f363150/downloads/experimental/hpan-hpxy/HPAN-R3-PHYSICAL-ACCEPTANCE.zip). Its separate physical record is a short 0→104→0 run; it is not the accepted HPXY R1 hardware result. | 86Box · Tandy 1000 HX · Windows 3.0 real mode · 320×200×16 display over 640×256 logical space. [Download HPXY R1 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/7c119ac1ee5428fa1a3a3c37e49d340c0f363150/downloads/experimental/hpan-hpxy/HPXY-R1-EXPERIMENTAL.zip). The bundled frame is emulator evidence; the physical EX acceptance above is separate. |

The ZIPs are repository downloads, not GitHub Release assets or installers. The [package guide, installation and rollback instructions](downloads/experimental/hpan-hpxy/README.md) lists each binary hash and its original emulator evidence. The private E1 + PR #151 combination remains a separate development build; this HPXY R1 physical acceptance does not certify it, and no combined public release is available.


## Same Calculator, less waiting

<img src="docs/rrect/TIMELINE.PNG" alt="Actual 86Box comparison frames from unchanged and bounded-copy Calculator repaint runs" width="640">

*86Box 6.0 · Tandy 1000 HX, 8088 at 7.16 MHz · Windows 3.0 real mode · TR5 320×200×16. This is a fixed-time screenshot sequence: the unchanged driver still lacks the Back key at 95 seconds; the candidate is complete at 14.7 seconds.*

In a separate matched timing run, one Calculator repaint fell from **92.5 to 10.4 seconds**; all 13 compared frames were byte-identical. The bounded-copy change merged in [PR #151](https://github.com/astrobleem/oemdisplay-tandy/pull/151) at [commit fc7b09b](https://github.com/astrobleem/oemdisplay-tandy/commit/fc7b09bdbe7e37dc9d562bdb746cf435b0628ba0). It is emulator-only, tested only in 320×200×16, and is not in the RC6 download. The compact Start is already in RC6. PR #151's renderer optimization and panning have not shipped as a combined runtime or been tested on physical hardware; the new E1 edge cadence is also physically untested. No combined package is released. See the [full test record](docs/RRECT.MD) and [evidence commit](https://github.com/astrobleem/oemdisplay-tandy/commit/3ece9ee38ecce27c726aa9c73c815632b28589c9).

## Readable text and compact controls

<img src="docs/FONTS/SHOTS/WIN320.PNG" alt="Genuine native-size Windows 3.0 Tandy 320x200 text and menu capture" width="480">

*Genuine Windows 3.0 Tandy-emulator capture · native 320×200×16 · unscaled. The capture record does not name a specific emulator model; see [screenshot provenance](docs/FONTS/SHOTS/README.TXT) and [capture commit b07a4ca](https://github.com/astrobleem/oemdisplay-tandy/commit/b07a4cad7b0e646e71402ff420d958093c2bc768).*

RC6 supplies original XT Pixels System, Fixed and OEM fonts with the inspected Windows metrics intact. At 320 pixels, text and common controls remain readable alongside Tandy Start; at 160 pixels some menus wrap and wide dialogs still clip. See the [font qualification](docs/FONTS/README.MD) and [font evidence](docs/QUAL/FONTSR10.JSON). The taller-desktop experiment above is separate work for windows that do not fit.

## Apps, input and sound

The vertical-pan test keeps cursor shape and click targets aligned as the view moves; its keyboard shortcuts and edge-dwell controls are listed in [PAN.MD](docs/PAN.MD). Small Windows apps provide more examples: [Tandy Maze](examples/MAZE/GAME/README.MD), [Tandinator](examples/TANDINAT/README.MD), [Pinball](examples/PINBALL/README.MD), [Starfield](experiments/VISPART2/README.MD) and [Matrix](experiments/VISPART1/README.MD).

On the real Tandy 1000 EX, the mouse wheel scrolls in Program Manager, File Manager and Notepad; Hold opens Tandy Start. The Windows wheel extension remains private and has no public download yet. The public [WHEEL.EXE DOS diagnostic](tools/WHEEL/WHEEL.EXE) and its [instructions](tools/WHEEL/README.TXT) check mouse/API and serial data; they do not install Windows scrolling. RC6 includes the shell-side `TSINPUT.DLL` and Hold guide/screenshots; the compatible [TNDYK3 keyboard test candidate](src/tandyk3/README.md) supplies a separate keyboard path.

<img src="https://raw.githubusercontent.com/astrobleem/oemsound-tandy/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/docs/SHOTS/WAMPUI3.PNG" alt="Tandy Winamp UX3 showing a seven-entry scrolling playlist in a Windows 3.0 emulator capture" width="480">

*Unmodified emulator capture · emulated Tandy 1000 HX, 8088 at 4.772728 MHz, 640 KB, stock CGA · Windows 3.0 real mode. The published capture record does not name the emulator product. [Capture provenance and image hash](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/docs/SHOTS/WINAMP3.MD) · [tested UI record](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/experimental/WINAMP30/VALIDATION-UI.MD) · [source commit 824ae10](https://github.com/astrobleem/oemsound-tandy/commit/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476). The app's separate physical acceptance is on a real Tandy 1000 EX, 7.16 MHz 8088; see the [scoped acceptance record](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/experimental/WINAMP30/EVIDENCE/PHYSICAL.JSON).*

**[Download Tandy Winamp UX3](https://github.com/astrobleem/oemsound-tandy/releases/download/tandy-winamp-ux3.20261018/TWUX3.ZIP)** · [Release notes and checksum](https://github.com/astrobleem/oemsound-tandy/releases/tag/tandy-winamp-ux3.20261018) · [Install guide](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/experimental/WINAMP30/INSTALL.TXT)

Tandy Winamp UX3 browses and adds music, manages a scrollable 32-entry playlist, and plays MIDI, supported VGM/VGZ and PSG-adapted MOD. On the real EX, the user accepted Browse/Add, Remove and scrolling past four songs; music also continued while they used Program Manager. Its separate HX emulator suite passed 396 native UI checks and 88 audio/event regression checks. This app update is separate from the Windows XT RC6 package.

The Tandy sound companion also offers [PSGSTART and BEATSTART](https://github.com/astrobleem/oemsound-tandy/releases/tag/sound-v0.1.0-preview.20261007); the optional [MML3 kit](https://github.com/astrobleem/oemsound-tandy/releases/tag/sound-exp-v0.1.0-pit.20261007) adds Fiddle/Beats authoring and a fifth square-wave speaker voice.
[libwintandy](https://github.com/astrobleem/libwintandy/tree/24ff4f932c0d4d4e2a18a3c49b0ea0a8ff90e71f) publishes shared 8086 Windows 3.0 helpers and a source-inclusive [VGM/VGZ and bounded MOD format-preview package](https://github.com/astrobleem/libwintandy/blob/24ff4f932c0d4d4e2a18a3c49b0ea0a8ff90e71f/examples/FORMATS30/LibWinTandy-Win30-Formats-Gzip-Fix-Preview-20261017.zip). This is an opt-in preview, not a stable release or general-purpose emulator: VGM/VGZ accepts a defined Tandy SN76496 command subset, while MOD becomes a square-wave PSG arrangement without sampled timbres. See the [format limits and test record](https://github.com/astrobleem/libwintandy/blob/24ff4f932c0d4d4e2a18a3c49b0ea0a8ff90e71f/examples/FORMATS30/README.md).

## Other machine-specific video packages

<details>
<summary>Experimental driver and download matrix</summary>

These packages have separate install paths and qualification limits. A result for one card or computer does not qualify another.

| Target | Public download | Evidence, status and guide |
| --- | --- | --- |
| Tandy Video II, emulated SL/2 family | [TNDYV2.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-video-ii-2026-10-14-r2/TNDYV2.ZIP) | Experimental; Windows rendering is for the SL/2 emulator profile only. Other SL/TL/RL models and physical hardware are unqualified. EX/HX must not use it. Run T2RESV before Setup and every Windows start; see [install/recovery](docs/tga2/INSTALL.TXT) and the [qualification](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experimental-video-ii-2026-10-14-r2). |
| Amstrad PC1512 | [PC1512.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PC1512.ZIP) · [front door](https://github.com/astrobleem/windows-3-amstrad-pc1512) | Experimental emulator evidence; one cursor-state case remains unresolved. [Install/recover](experiments/DISPLAY3/PC1512.TXT). |
| IBM PCjr | [PCJRSET.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/PCJR/PCJRSET.ZIP) · [front door](https://github.com/astrobleem/windows-3-pcjr) | 320×200×16 Setup packet; clean and existing-install Setup tested in DOSBox-X. This is a repository-file download, not a GitHub Release asset. [Install/recover](downloads/experimental/PCJR/README.MD). |
| IBM XT + Plantronics ColorPlus | [PCP3216.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PCP3216.ZIP) · [front door](https://github.com/astrobleem/windows-3-plantronics) | Experimental emulator rendering; requires the ColorPlus card and its dedicated VRAM. [Install/recover](experiments/DISPLAY3/PCP3216.TXT). |
| Olivetti Prodest PC1 / Yamaha V6355D | [PC1/B000 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP) · [Yamaha B800 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP) · [front door](https://github.com/astrobleem/windows-3-olivetti-pc1) | Experimental repository files, not release assets. PC1/B000 has build and host checks only; no emulator, Setup or physical-PC1 test. The separate B800 screenshot is an 86Box IBM XT profile, not a PC1. [Corrected evidence](docs/yamaha/QUALIFICATION.MD) · [guide](experiments/YAMAHA/README.MD). |
| 80-column TEXT80 | [TEXT80.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/TEXT80/TEXT80.ZIP) · [front door](https://github.com/astrobleem/text-mode-windows) | Experimental text modes and compact C25; C25's recorded Windows binary passed 54/54 checks in 86Box XT/CGA. Other rebuilds have newer host audits, not fresh Windows GUI runs. [Install, rollback and exact scope](downloads/experimental/TEXT80/README.MD). |

### PCjr clean-install evidence

<a href="https://github.com/astrobleem/oemdisplay-tandy/blob/613137d0029817b42e141a11685182d867da911d/docs/pcjr/INSTALL/DESKTOP.PNG"><img src="docs/pcjr/INSTALL/DESKTOP.PNG" alt="Actual clean-install Windows 3.0 desktop on the emulated IBM PCjr at 320x200x16" width="480"></a>

*DOSBox-X · IBM PCjr · Windows 3.0 real mode · 320×200×16. PR #138 merged at [commit 613137d](https://github.com/astrobleem/oemdisplay-tandy/commit/613137d0029817b42e141a11685182d867da911d) after 40 host tests; the [26/26 clean-install session report](docs/pcjr/INSTALL/SESSION.JSN) pins source commit [9ae4408](https://github.com/astrobleem/oemdisplay-tandy/commit/9ae44084127fe5d2f0c57ee1e1842d1ee1885573). The screenshot and PCJRSET.ZIP are repository evidence/downloads, not new release assets.*

<img src="docs/yamaha/YAMAHA03.JPG" alt="Original 86Box screenshot of Windows 3.0 on an emulated IBM XT with a standalone Yamaha V6355D B800 profile at 160x200x16" width="480">

*86Box · IBM XT (1986), 8088 at 4.77 MHz · Windows 3.0 real mode · 160×200×16 B800 profile. This proves only the pictured emulator profile, not an Olivetti PC1 or physical hardware. [Qualification and source evidence](docs/yamaha/QUALIFICATION.MD).*

</details>

[Canonical development repository](https://github.com/astrobleem/oemdisplay-tandy) · [graphics modes](docs/MODES.MD) · [user manual and recovery](docs/USERMAN.MD) · [build guide](BUILDING.MD) · [screenshot provenance](docs/PROMO/SHOWCASE.MD).
