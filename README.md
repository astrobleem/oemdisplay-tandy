# Windows XT

**A colorful little Windows desktop for an 8088 Tandy.**

Windows XT brings five graphics modes, a compact Start-menu shell, games and
utilities to **Windows 3.0 real mode on the original Tandy 1000 EX/HX with
640 KB RAM**. This repository, OEMDisplay-Tandy, contains the display drivers,
desktop additions and their source and test evidence.

[Get started](#get-started) · [Display modes](#display-modes) ·
[The desktop](#tandy-start--tshell) · [Apps](#games-and-utilities) ·
[Performance](#performance-and-verification) ·
[Sound companion](https://github.com/astrobleem/oemsound-tandy)

![16 COLORS. WOW! Windows 3.0 on a Tandy 1000 EX, with a real Paintbrush capture inside a promotional computer scene](docs/PROMO/16WOW.WEBP)

*Project artwork, not a hardware photograph or official Tandy/Microsoft
packaging. The monitor uses an [actual emulator capture](docs/tandy-dib-roundtrip.png).
[Artwork details](docs/PROMO/README.MD).*

The startup picture is **Windows XT** in every current display profile.
The retired Tandy picture is not an installation option. Historical OEM
artifacts remain intact for provenance and recovery. For an older installation,
the [splash-only updater](examples/WXTSPL/README.TXT) preserves the existing
loader prefix and original backup; applying it is an explicit DOS command.

## At a glance

- **Five graphics modes:** 160 or 320 pixels wide in sixteen colors,
  320 pixels in four colors, or a 640-pixel desktop in two or four colors.
- **Tandy Start 14:** Programs, My Computer, Run/Browse, a clock, screen
  savers, optional sounds and guarded Hold-to-Start support.
- **One support folder:** `C:\WINXT`, with native Windows Setup, matching
  fonts, a guarded launcher and numbered recovery backups.
- **Small native apps:** Cookie Clicker, Fly Swat, Pinball, XTEyes, GIF
  conversion for Paintbrush and more.
- **An experimental sixth mode:** real 80×25 hardware text, with known
  character corruption. Choose a graphics mode for ordinary use.

**Status:** experimental software with emulator tests and limited reports
from a physical Tandy 1000 EX. Hardware reports do not certify every current
binary or app. See the [mode table](#display-modes) and
[detailed status](docs/STATUS.MD).

## Get started

### Choose the right package

| What you want | Start here |
| --- | --- |
| GoTek, emulator or 720 KB floppy | [Windows XT disk image](tools/FLASHDISK/README.MD): current TR5 drivers, optional desktop and a DOS helper that gathers your own Windows files. No Python needed to install. |
| Copy directly to CF/hard disk | [One-folder WINXT source and staging guide](distributions/WINXT/README.MD): the same current runtime, with optional host-side staging. |
| Games and utilities to try on an existing setup | [TANDYLAB test pack](examples/TANDYLAB/README.MD): a separate, versioned app collection. Check individual component guides for newer work. |

### 1. Mount the 720 KB disk and prepare Windows XT

Start with a **backed-up, working Windows 3.0 installation** on DOS 3.3 or
later. Download `WINXT720.IMG` (or the same image inside `WINXT720.ZIP`)
using the [disk download/build guide](tools/FLASHDISK/README.MD). Select it in
your GoTek or mount it as a **720 KB floppy** in your emulator. Boot your
existing DOS system first: this is an installation data disk, not a boot disk.
No 1.44 MB controller support or Python is needed on the Tandy.

At a plain DOS prompt, outside Windows:

```bat
A:
CD \
INSTALL
```

The DOS helper gathers and verifies matching support files from your own
`C:\WINDOWS` and `SYSTEM` folder. If some files are missing, it lists them
and stops; supply a directory copied from your own Windows 3.0 media with
`INSTALL D:\WIN30SRC` (use your actual path). Original compressed files are
accepted. After validation and your confirmation, it prepares a new
`C:\WINXT` without changing Windows or overwriting an existing WINXT folder.

The public image excludes Microsoft support files and fonts; the completed
own-media folder contains your private copies. **Do not redistribute it.**
For direct CF transfer or advanced host-side staging, use the
[one-folder guide](distributions/WINXT/README.MD).

### 2. Install through Windows Setup

Exit Windows completely. At the DOS prompt:

```bat
C:
CD \WINXT
INSTALL
```

In Setup, select **Display → Other display**, enter **`C:\WINXT`**, choose
a mode and accept **Complete Changes**. If asked for the display disk again,
use the same folder. If Setup offers to alter CONFIG.SYS, choose **option 3:
make no changes**.

For the optional Tandy Start desktop, run once from DOS:

```bat
C:\WINXT\TSSETUP
```

This fresh-install step refuses to overwrite existing shell files. For an
existing Tandy Start installation, follow the
[upgrade guide](examples/TSHELL/README.MD) and preserve your settings.

### 3. Start Windows

At a fresh DOS prompt, use:

```bat
C:\WINXT\WINXT
```

**Always use this guarded launcher, including for lower-color modes and
Setup. Never bypass a video-memory reservation or recovery error by running
WIN directly.** It starts Windows in real mode. A verified optional-shell
installation uses Tandy Start for that graphics session and restores the
original shell on exit; experimental text keeps the original Windows shell.

### Change modes or roll back

Exit Windows and run `C:\WINXT\WINXT SETUP`. Select **Other display** and
`C:\WINXT` again, choose the new mode, then reboot and use the guarded
launcher. Use Setup rather than editing SYSTEM.INI by hand.

To restore the pre-installation configuration, use the backup path printed
by INSTALL and recorded in `C:\WINXT\BACKUP.TXT`. For example, from DOS:

```bat
C:\WINXT\BACKUP\B001\RESTORE YES
```

`B001` is an example; use your actual numbered backup. Restoration verifies
the saved files and disables automatic optional-shell dispatch. New files
may remain on disk but are no longer selected. Keep the backup until the
restored system works; resolve any restore failure before starting Windows.

[Full installation and recovery guide](distributions/WINXT/README.TXT) ·
[Installation, six-mode switching and rollback evidence](docs/UNIFIED/README.md)

## Display modes

All five graphics profiles have 200 logical rows. These are the driver
identities in the current public WINXT kit:

| Mode | Palette / purpose | Driver | Physical Tandy status |
| --- | --- | --- | --- |
| **320×200, 16 colors** | Full Tandy palette; default profile | `TR53216.DRV` | Paintbrush and TSHELL worked on a later trial; still slow |
| **640×200, 2 colors** | Wide black-and-white desktop | `TR56402.DRV` | Earlier TRIAL 3 reported substantially faster and usable |
| **160×200, 16 colors** | Smallest desktop; full Tandy palette | `TR51616.DRV` | Low-resolution report did not identify the exact mode |
| **320×200, 4 colors** | Black, cyan, magenta, white | `TR53204.DRV` | Operation reported; red hearts mapped to black |
| **640×200, 4 colors** | Black, red, green, white | `TR56404.DRV` | Unconfirmed; emulator hardware model remains uncertain |
| **80×25 hardware text** | BIOS mode 03h; 640×200 logical GDI surface | `TXTMODE.DRV` | Lab-only; physical behavior and speed untested |

The physical observations above concern earlier trials, with no final-file
hash readback. **They are not acceptance of the exact TR5 files in this
table.** The known-working TRIAL 3 monochrome fallback is a different binary;
keep it separately. [Hardware reports and scope](docs/STATUS.MD).

Original EX/HX 640×200 Tandy graphics has **four colors, not sixteen**.
Narrow modes can clip stock Windows dialogs. In 320×200 four-color mode,
stock Clock's digital digits are invisible; use analog Clock or another mode.

<details>
<summary>See the six Setup choices and the text-mode caveat</summary>

![The five TR5 graphics choices and explicitly experimental text choice in native Windows Setup](docs/UNIFIED/SHOTS/SETUP6.PNG)

Actual Windows 3.0 Setup in the emulator. The experimental text driver runs
unchanged Program Manager and Notepad in real hardware character cells, but
window movement, clipping, caret inversion and bitmap restore can corrupt
characters. It is not ready for everyday use. TSHELL is not qualified for
this driver; switching back to graphics restores the appropriate fonts and
optional-shell path.

[Text-mode experiment](experiments/TEXTMODE/README.MD) ·
[Known failures and measurements](experiments/TEXTMODE/EVIDENCE/RESULT.JSON) ·
[Runtime text-mode notes](distributions/WINXT/TEXTMODE.TXT)

</details>

## Tandy Start / TSHELL

Tandy Start 14 adds a compact Start menu and clock bar while keeping
Program Manager as the editor for your program groups.

- **My Computer and Programs:** open or restore File Manager; browse existing
  Program Manager groups with paging, saved arguments and working directories.
- **Run / Browse:** launch from the program's folder, with read-only friendly
  names from validated FAT/VFAT metadata. Launches still use DOS aliases;
  unsupported metadata falls back to short names.
- **Clock and System:** right-click the clock to adjust date/time; double-click
  to open Clock or Calendar. About This Tandy shows system, display and memory
  pages. The compact controls fit the 160-pixel desktop.
- **Screen savers:** None, Matrix, Maze or Starfield; 10–3600-second idle delay,
  unsaved Preview, and Starfield speed/star-count options. Maze can be very slow.
- **Sounds and exit:** optional Tandy or XP-note startup phrase and pre-exit
  chime. Hold Shift while selecting Exit to skip the chime. Application save
  prompts remain active; successful return to DOS can show moon-and-stars art.
- **Hold-to-Start:** optional original-Tandy Hold key support through the
  compatible keyboard driver and TSINPUT helper. The default is guarded by
  the supported real-mode ROM and loaded driver profile.

| Tandy Start 14: Hold opens Start over another app | Green hill wallpaper with Tandy Start 13 |
| --- | --- |
| ![Tandy Start 14 Hold-to-Start emulator capture](examples/TSHELL/SHOTS/HOLD640.PNG) | ![Native sixteen-color hill wallpaper emulator capture with Tandy Start 13](examples/HILLS/HILL320.PNG) |

Actual emulator captures, with doubled rows and, for the hill scene, columns.
The wallpaper image retains its version 13 identity. Physical Hold behavior
and the later Browse redraw improvements remain unverified. Friendly-name
browsing and all three savers have hardware reports, with Maze slow.

Maximized apps can cover the bar; there is no application taskbar. The idle
saver is not a password lock. See the
[launch, upgrade and recovery guide](examples/TSHELL/README.MD) and
[version 14 changes and test scope](examples/TSHELL/TESTS14.MD).

### Optional desktop additions

| Addition | What it provides |
| --- | --- |
| [Original keyboard support](src/tandyk3/README.md) | Compatible real-mode driver, diagnostics, guarded install and rollback. Seventeen raw key press/release pairs matched hardware; Windows translation and Hold still need physical verification. |
| [Windows XT splash updater](examples/WXTSPL/README.TXT) | CHECK, APPLY and RESTORE for a recognized startup file, preserving display drivers, fonts and INI settings. |
| [Green hill wallpaper](examples/HILLS/README.TXT) | Native RGBI landscapes for 160×200 and 320×200 sixteen-color modes, using about 16 KB / 32 KB of bitmap memory. Turn wallpaper off before switching to monochrome. |
| [XTEyes](examples/XTEYES/README.TXT) | A small native GDI window whose eyes follow the pointer, with integer geometry and bounded redraws. Physical responsiveness is unmeasured. |

These standalone additions are opt-in; the main installer does not activate
them all automatically.

## Games and utilities

| App | What to try |
| --- | --- |
| [TANDINATOR v0.2](examples/TANDINAT/README.MD) | Experimental full-screen character oracle with native sprite art, 128 curated characters and bounded mouse-following eyes. 320/640-pixel displays; hardware testing remains open. |
| [Cookie Clicker](examples/COOKIE/README.MD) | Click or press Space, buy cookies-per-second upgrades, save and load. Fits 160×200. |
| [Fly Swat 1.1](examples/SWAT/README.MD) | Mouse-controlled fly hunting with score, three hearts, pause and restart; fullscreen and windowed paths, plus `/G` fallback. |
| [Pinball](examples/PINBALL/README.MD) | Two flippers, three bumpers and three balls; Space launches, Z/Left and / or Right flip, P pauses. |
| [Matrix](examples/MATRIX/README.MD) | Fullscreen character rain, on demand or as the shell's idle companion. |
| [Maze](examples/MAZE/SAVER10/README.MD) | Experimental raycasting saver and windowed demo. Trial aliases use clipped GDI; approximate-XT settings can be very slow. |
| [Starfield](examples/STARFLD/README.MD) | GDI flying stars, three speeds and 16/32/64-star settings. Sixteen stars is the lightest option. |
| [Slosh](examples/SLOSH/README.MD) | Drag the title bar and watch a tiny water surface rebound and settle. |
| [Brighter Tomorrow](examples/BRIGHT/README.MD) | A compact choices-and-consequences game with workplace notices, receipts and two endings. |
| [GIFLOAD](examples/GIFLOAD/README.TXT) | Convert supported static GIFs to new palette-mapped BMPs for Paintbrush. It does not add formats to Paintbrush itself. |
| [COMMDLG demo](examples/COMMDLG/README.TXT) | Bounded app-local Open/Save dialogs for Windows 3.0; use the pack's CDSTART launcher. |
| [FileDrop demo](examples/FILEDROP/README.TXT) | Drag one or two path names between demo apps. It transfers names, not file contents. |
| [About This Tandy](examples/TABOUT/README.MD) | System, display and memory pages with refresh; exact hardware-model detection remains deferred. |
| [EXJOY](examples/EXJOY/README.MD) | Raw joystick axes/buttons, range display and session-only center calibration. Physical input remains unverified. |
| [DOS WHEEL diagnostic](tools/WHEEL/README.TXT) | Bounded mouse-wheel/API and serial diagnostics. Raw Genius data was detected; no Windows scrolling bridge is implemented. |

| Cookie Clicker · 320×200×16 | Pinball · logical 640×200×4 |
| --- | --- |
| ![Cookie Clicker native emulator capture](docs/SHOTS/COOKIE.PNG) | ![Pinball native emulator capture, with doubled rows](docs/SHOTS/PINBALL.PNG) |

These are retained emulator captures, not physical performance measurements.
[Screenshot sources and exact scope](docs/SHOTS/README.MD).

The [TANDYLAB catalog](examples/TANDYLAB/CATALOG.TXT) describes the separate
test pack and paired runtime files. Stock Windows apps shown in project
captures, such as Paintbrush and File Manager, come from your own Windows
installation.

### Add some Tandy sound

The companion **[OEMSound-Tandy](https://github.com/astrobleem/oemsound-tandy)**
project has Mini MIDI, Mini Piano, Beats Lab, Automatic Mouth, PSGPLAY and
startup/exit chimes. It uses the Tandy's three square-wave voices and noise
voice. Follow each app's guide: app-local MIDIMAP is not a system MIDI device
or General MIDI synthesizer, and only one PSG producer should run at a time.

## Performance and verification

The graphics drivers keep an 8086/8088-safe drawing path and reserve shared
video memory before Windows starts. Proven drawing cases refresh bounded
regions; uncertain bounds fall back to the original synchronous full-screen
copy. Palette conversion, compatible bitmaps and bounded BI_RGB support
include Paintbrush save/reopen checks.

**The public TR5 change targets repeated Clock-border copies.** It expands
the validated multi-interval scanline refresh gate while preserving the
original renderer, raster rules and cursor protections. Stock CLOCK.EXE is
unchanged.

| Measured operation | TRIAL 4 | TRIAL 5 |
| --- | ---: | ---: |
| Two-pixel rectangle, 121×72 client, 160×200×16 | 1,318 ms | 55 ms |

About **24× faster for that measured operation**, in exclusive paired
DOSBox-X runs at fixed 25,000 cycles. The guest timer resolves roughly
55 ms; these cycle settings are uncalibrated and **do not predict physical
8088 speed or an overall Windows speedup**.

The five-mode paired rectangle suite compared **6,560 cases** with zero
framebuffer differences against TRIAL 4. Coverage included pen widths, all
16 ROP2 values, clipping, coordinate transforms and cursor corners. This is
bounded regression evidence, not complete GDI or hardware qualification.

[TR5 design and reproduction](docs/TRIAL5/README.MD) ·
[Exact binaries](docs/TRIAL5/BUILDS.JSN) ·
[Timings, regression coverage and limits](docs/TRIAL5/VERIFY.TXT)

### Optional TRIAL7 test build

The [TRIAL7 experimental overlay](experiments/TRIAL7/README.MD) publishes the
qualified border/text candidate with the retained TR6 DIB optimization,
source, emulator evidence and a one-shot saved-backup rollback kit. It needs
the exact default-layout TR5 installation and changes only its already
active mode. Restore any TR6 overlay first. Stable packages and build
defaults remain unchanged; physical 8088 timing and EX/HX 640x200 four-color
behavior still need hardware testing.

### What still needs testing

- Exact current binaries on physical EX/HX hardware, especially 640×200
  four-color behavior; the emulator's model remains uncertain.
- Text-mode character/geometry corruption and DOS-app/grabber switching.
- Physical Windows keyboard translation, Hold-to-Start and joystick input.
- Broader app compatibility, long-running use and calibrated hardware timing.

Windows 3.1, standard/enhanced mode, PCjr, other memory layouts and an
unexpanded 256 KB EX are outside the current acceptance scope. Large redraws
can still be slow. [Complete development status](docs/STATUS.MD).

## Build, explore and contribute

- [Build guide](BUILDING.MD): host tooling and historical package reproduction.
- [Current TR5 driver guide](docs/TRIAL5/README.MD): source pipeline, profile
  names, audits and exact build identities.
- [Mode contracts](docs/MODES.MD): palettes, fonts, memory and retained evidence.
- [Unified installation evidence](docs/UNIFIED/README.md): staging, Setup,
  six-mode lifecycle checks and verified rollback.
- [Source provenance](src/tandysw/PROVENANCE.md): third-party inputs and notices.

Preserve the historical binaries and package pins when experimenting.
A successful rebuild does not make a new driver hardware-qualified.

Hardware reports are especially useful. Include the machine and RAM, DOS
and Windows versions, display mode, driver/app version or SHA-256, exact
steps and expected versus actual behavior. Say whether the result came from
hardware or an emulator, and keep a known-working rollback available.
Preserve component licenses and third-party notices; repository inclusion
does not grant new rights to Windows, DDK material or fonts.

<details>
<summary>Windows XT concept box and project artwork</summary>

<a href="docs/PROMO/WINXTBOX.WEBP"><img src="docs/PROMO/WINXTBOX.WEBP" alt="Windows XT concept box for the Tandy Windows 3.0 TShell and Extensions Plus Pack" width="360"></a>

Promotional concept art, not official packaging or a physical product.
[Original artwork and image identities](docs/PROMO/README.MD).

</details>
