# Windows XT demos and capture notes

The front page shows what Windows XT looks like. This page keeps the detailed
capture provenance, measured comparisons and package distinctions together.
The pictures below are emulator captures; separately described physical
acceptance is not a claim that a screenshot came from hardware.

For downloads and installation use the [front page](../README.md#get-started).
Final R1/new wheel-driver qualification is in the [rc.7 notes](RELEASES/RC7.MD);
the older installer's record is [rc.6 qualification](QUAL/RC6.MD).

## Startup, desktop and colors

The front page's startup, hill desktop, moon-and-stars shutdown and before/after
color comparison retain the original visual tour. The four-color picture comes
from [the owner's earlier video](https://www.youtube.com/watch?v=yNisFBDLXos&t=1230s).
It and the sixteen-color Paintbrush picture compare appearance in different
modes, not performance. See the [original showcase/capture notes](PROMO/SHOWCASE.MD)
and [color comparison record](PROMO/SHOWCASE.MD#earlier-windows-30-video).

<img src="../examples/HILLS/HILL320.PNG" alt="Actual Windows 3.0 desktop with Tandy Start in the 320x200x16 Tandy mode" width="640">

*DOSBox-X guest capture · Windows 3.0 real mode · Tandy 320×200×16 logical mode, displayed doubled. The hill wallpaper is optional and separate from RC6. [Capture provenance](PROMO/SHOWCASE.MD) · [capture commit 43cf098](https://github.com/astrobleem/oemdisplay-tandy/commit/43cf0984f1d3da389231c55cdd82d8757074836a).*

## A desktop taller than its screen

<img src="pan/DEMO.GIF" alt="Existing 86Box captures showing Windows XT's vertical software-panning experiment" width="640">

*86Box 6.0 · Tandy 1000 HX, 8088 at 7.16 MHz · Windows 3.0 real mode · 320×200×16 viewport over a 320×400 logical desktop. Existing captured frames; the [33/33 session record](pan/FIT/XPWIN.JSN) is preserved at [test commit 6d48868](https://github.com/astrobleem/oemdisplay-tandy/commit/6d48868aa62fa5b7cf5d6ed8946dd7984582ace7).*

The XTPAN prototype makes lower windows and buttons reachable without changing the 320×200 display. Keyboard pans, edge dwell, cursor rendering and mouse hit-testing were checked; one 275-row dialog's bottom button was clicked after panning. This is software viewport panning, not CRTC hardware scrolling, and it is not in RC6. A Tandy 1000 EX owner reports XTPAN works on real hardware, but no scripted physical test of this software-panning prototype is recorded. The separate HPXY hardware-pan results below do not qualify XTPAN. See the [full investigation](PAN.MD).

A converted Minesweeper demonstration shows one board extending below the 200-row viewport. The app conversion is specific to this application; the private executable and shim are not distributed.

<img src="pan/MINE/REVEAL.PNG" alt="Revealed Minesweeper board in Windows 3.0 real mode on the emulated Tandy 1000 HX" width="640">

*Cropped emulator capture · 86Box native headless · emulated Tandy 1000 HX, 8088 at 7.159090 MHz, 640 KB · Windows 3.0 real mode · 320×200×16 viewport over 640×256 logical space. The MNSN2 emulator run passed four snapshots with zero viewport/display mismatches. It used the private combined HPXY XR1 PR151 + E1 runtime; that combination has no public tested commit or hardware qualification. [Capture/test provenance](pan/MINE/CAPTURE.MD) · [public PR151 component commit fc7b09b](https://github.com/astrobleem/oemdisplay-tandy/commit/fc7b09bdbe7e37dc9d562bdb746cf435b0628ba0).*

<img src="pan/MINE/PAN16040.PNG" alt="Minesweeper viewport after a large jump to origin 160,40 in Windows 3.0 real mode" width="640">

*Cropped emulator capture · same 86Box/Tandy 1000 HX setup · viewport origin (160,40). This large jump used a planned full viewport copy with hardware enabled and CRTC start 840; it is not an incremental staged pan or a retrace fault. The combined runtime remains physically untested. See the [separate HPXY R1 hardware acceptance](#panning-on-real-tandy-hardware) and [capture record](pan/MINE/CAPTURE.MD).*

## Panning on real Tandy hardware

Panning keeps a 320×200 display while bringing the rest of a larger Windows desktop into view. HPXY R1 has been tested and accepted on the owner's real Tandy 1000 EX: Windows 3.0 real mode, stock-CGA profile, 7.16 MHz 8088, 640 KB. The scoped run recorded 54 pans, including 53 hardware operations, no ERROR records, return to software presentation at (0,0), and Windows exit code 0. That acceptance applies to this HPXY R1 configuration; it does not qualify other machines, display profiles or Windows 3.1. The rc.7 R1 overlay documents integration with separately supplied local XR1 dependencies; it does not bundle the private panning driver/helper or qualify the new first-party wheel driver on hardware. RC6 remains unchanged and does not include panning.

| HPAN R3 | HPXY R1 |
| --- | --- |
| <img src="../downloads/experimental/hpan-hpxy/HPAN-R3-86Box-FRAME314.png" alt="Original 86Box capture: emulated Tandy 1000 HX, Windows 3 real mode, 320×200×16 viewport over 640×200" width="360"> | <img src="../downloads/experimental/hpan-hpxy/HPXY-R1-86Box-FRAME514.png" alt="Original 86Box capture: emulated Tandy 1000 HX, Windows 3.0 real mode, 320×200×16 viewport over 640×256" width="360"> |
| 86Box · Tandy 1000 HX · Windows 3 real mode · 320×200×16 display over 640×200 logical space. [Download HPAN R3 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/7c119ac1ee5428fa1a3a3c37e49d340c0f363150/downloads/experimental/hpan-hpxy/HPAN-R3-PHYSICAL-ACCEPTANCE.zip). Its separate physical record is a short 0→104→0 run; it is not the accepted HPXY R1 hardware result. | 86Box · Tandy 1000 HX · Windows 3.0 real mode · 320×200×16 display over 640×256 logical space. [Download HPXY R1 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/7c119ac1ee5428fa1a3a3c37e49d340c0f363150/downloads/experimental/hpan-hpxy/HPXY-R1-EXPERIMENTAL.zip). The bundled frame is emulator evidence; the physical EX acceptance above is separate. |

The ZIPs are repository downloads, not GitHub Release assets or installers. The [package guide, installation and rollback instructions](../downloads/experimental/hpan-hpxy/README.md) lists each binary hash and its original emulator evidence. The private E1 + PR #151 combination remains a separate development build; this HPXY R1 physical acceptance does not certify it, and the complete private combined runtime is not included in the rc.7 component/overlay downloads.


## Same Calculator, less waiting

<img src="rrect/TIMELINE.PNG" alt="Actual 86Box comparison frames from unchanged and bounded-copy Calculator repaint runs" width="640">

*86Box 6.0 · Tandy 1000 HX, 8088 at 7.16 MHz · Windows 3.0 real mode · TR5 320×200×16. This is a fixed-time screenshot sequence: the unchanged driver still lacks the Back key at 95 seconds; the candidate is complete at 14.7 seconds.*

In a separate matched timing run, one Calculator repaint fell from **92.5 to 10.4 seconds**; all 13 compared frames were byte-identical. The bounded-copy change merged in [PR #151](https://github.com/astrobleem/oemdisplay-tandy/pull/151) at [commit fc7b09b](https://github.com/astrobleem/oemdisplay-tandy/commit/fc7b09bdbe7e37dc9d562bdb746cf435b0628ba0). It is emulator-only, tested only in 320×200×16, and is not in the RC6 download. The compact Start is already in RC6. PR #151's renderer optimization and panning have not shipped as a combined runtime or been tested on physical hardware; the new E1 edge cadence is also physically untested. The rc.7 downloads provide a redistributable component subset, not that complete private runtime. See the [full test record](RRECT.MD) and [evidence commit](https://github.com/astrobleem/oemdisplay-tandy/commit/3ece9ee38ecce27c726aa9c73c815632b28589c9).

## Readable text and compact controls

<img src="FONTS/SHOTS/WIN320.PNG" alt="Genuine native-size Windows 3.0 Tandy 320x200 text and menu capture" width="480">

*Genuine Windows 3.0 Tandy-emulator capture · native 320×200×16 · unscaled. The capture record does not name a specific emulator model; see [screenshot provenance](FONTS/SHOTS/README.TXT) and [capture commit b07a4ca](https://github.com/astrobleem/oemdisplay-tandy/commit/b07a4cad7b0e646e71402ff420d958093c2bc768).*

RC6 supplies original XT Pixels System, Fixed and OEM fonts with the inspected Windows metrics intact. At 320 pixels, text and common controls remain readable alongside Tandy Start; at 160 pixels some menus wrap and wide dialogs still clip. See the [font qualification](FONTS/README.MD) and [font evidence](QUAL/FONTSR10.JSON). The taller-desktop experiment above is separate work for windows that do not fit.

## Apps, input and sound

The vertical-pan test keeps cursor shape and click targets aligned as the view moves; its keyboard shortcuts and edge-dwell controls are listed in [PAN.MD](PAN.MD). Small Windows apps provide more examples: [Tandy Maze](../examples/MAZE/GAME/README.MD), [Tandinator](../examples/TANDINAT/README.MD), [Pinball](../examples/PINBALL/README.MD), [Starfield](../experiments/VISPART2/README.MD) and [Matrix](../experiments/VISPART1/README.MD).

Owner-reported input highlights include mouse-wheel scrolling in Program Manager, File Manager and Notepad on a real Tandy 1000 EX, plus Hold opening Tandy Start. The public Windows 3.0 R1 download is a bridge-only [source-inclusive experimental package](../downloads/experimental/WINWHL/README.MD) with a [direct ZIP download](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/WINWHL/WHEELR1.ZIP). It requires a separately obtained, already configured WHEEL.DRV API 1.0; this ZIP does not include or install that driver, and the historical bridge ZIP supplies no driver. The [rc.7 first-party kit](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.7/WINXT-FIRST-PARTY-R1.zip) now supplies a separately licensed, source-inclusive WHEEL.DRV; its final qualification is emulator-only. A user still needs a compatible separately supplied wheel client and configuration; the kit alone does not install the complete scrolling system. The owner's hardware report is separate from the package's synthetic-input emulator checks and does not establish a fresh-install path. This package is not part of RC6 and does not support Windows 3.1. The public [WHEEL.EXE DOS diagnostic](../tools/WHEEL/WHEEL.EXE) and its [instructions](../tools/WHEEL/README.TXT) check mouse/serial data; they do not add Windows scrolling. RC6 ships the shell-side `TSINPUT.DLL` and Hold guide/screenshots; the compatible [TNDYK3 keyboard test candidate](../src/tandyk3/README.md) is separate.

<img src="https://raw.githubusercontent.com/astrobleem/oemsound-tandy/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/docs/SHOTS/WAMPUI3.PNG" alt="Tandy Winamp UX3 showing a seven-entry scrolling playlist in a Windows 3.0 emulator capture" width="480">

*Unmodified emulator capture · emulated Tandy 1000 HX, 8088 at 4.772728 MHz, 640 KB, stock CGA · Windows 3.0 real mode. The published capture record does not name the emulator product. [Capture provenance and image hash](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/docs/SHOTS/WINAMP3.MD) · [tested UI record](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/experimental/WINAMP30/VALIDATION-UI.MD) · [source commit 824ae10](https://github.com/astrobleem/oemsound-tandy/commit/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476). The app's separate physical acceptance is on a real Tandy 1000 EX, 7.16 MHz 8088; see the [scoped acceptance record](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/experimental/WINAMP30/EVIDENCE/PHYSICAL.JSON).*

**[Download Tandy Winamp UX3](https://github.com/astrobleem/oemsound-tandy/releases/download/tandy-winamp-ux3.20261018/TWUX3.ZIP)** · [Release notes and checksum](https://github.com/astrobleem/oemsound-tandy/releases/tag/tandy-winamp-ux3.20261018) · [Install guide](https://github.com/astrobleem/oemsound-tandy/blob/824ae10e1d79d1bd2d09f4a37447f58dd9cc9476/experimental/WINAMP30/INSTALL.TXT)

Tandy Winamp UX3 browses and adds music, manages a scrollable 32-entry playlist, and plays MIDI, supported VGM/VGZ and PSG-adapted MOD. On the real EX, the user accepted Browse/Add, Remove and scrolling past four songs; music also continued while they used Program Manager. Its separate HX emulator suite passed 396 native UI checks and 88 audio/event regression checks. This app update is separate from the Windows XT RC6 package.

The Tandy sound companion also offers [PSGSTART and BEATSTART](https://github.com/astrobleem/oemsound-tandy/releases/tag/sound-v0.1.0-preview.20261007); the optional [MML3 kit](https://github.com/astrobleem/oemsound-tandy/releases/tag/sound-exp-v0.1.0-pit.20261007) adds Fiddle/Beats authoring and a fifth square-wave speaker voice.
[libwintandy](https://github.com/astrobleem/libwintandy/tree/24ff4f932c0d4d4e2a18a3c49b0ea0a8ff90e71f) publishes shared 8086 Windows 3.0 helpers and a source-inclusive [VGM/VGZ and bounded MOD format-preview package](https://github.com/astrobleem/libwintandy/blob/24ff4f932c0d4d4e2a18a3c49b0ea0a8ff90e71f/examples/FORMATS30/LibWinTandy-Win30-Formats-Gzip-Fix-Preview-20261017.zip). This is an opt-in preview, not a stable release or general-purpose emulator: VGM/VGZ accepts a defined Tandy SN76496 command subset, while MOD becomes a square-wave PSG arrangement without sampled timbres. See the [format limits and test record](https://github.com/astrobleem/libwintandy/blob/24ff4f932c0d4d4e2a18a3c49b0ea0a8ff90e71f/examples/FORMATS30/README.md).


## Screen savers

| Starfield | Matrix |
| --- | --- |
| <img src="SHOTS/STARS10.PNG" alt="Saved native Starfield capture" width="390"> | <img src="SHOTS/MATRIX.PNG" alt="Saved native Matrix capture" width="390"> |

The [showcase record](PROMO/SHOWCASE.MD) describes these saved captures.

[Back to Windows XT](../README.md) · [Other machine packages and captures](PLATFORM.MD)
