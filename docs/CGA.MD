# Install the CGA driver for Windows 3.0

**[Download CGA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CGA.ZIP)**

This supplies the CGA display driver, matching fonts, grabber and helpers for
**fresh or existing Windows 3.0 installations**. You need **DOS 3.3 or later, 640 KB RAM,
Windows 3.0 real mode, and IBM CGA with RGBI output**. Windows and DOS are not
included; Windows 3.1 is unsupported. Fresh Setup starts with the project's
fixed 640x200 monochrome profile. The mode choices below remain available
after Windows is installed.

The examples keep the extracted CGA kit, original Windows media and installed
Windows in separate directories. Substitute your actual drives and directories.

## Extract the package

If Windows is running, use Program Manager's **File / Exit Windows** and
confirm the exit. Run the following commands at the plain DOS prompt.

Transfer `CGA.ZIP` to the DOS computer using your usual floppy, disk or network
transfer. Use a DOS ZIP extractor that preserves folders. For example, with
PKUNZIP available and the archive on `A:`:

```bat
C:
MD \CGAKIT
CD \CGAKIT
PKUNZIP -D A:\CGA.ZIP
DIR
DIR FRESH640
DIR CGA
```

The current archive includes these files and folders:

```text
C:\CGAKIT\FRESH.EXE
C:\CGAKIT\FRESH.TXT
C:\CGAKIT\README.TXT
C:\CGAKIT\FRESH640\OEMSETUP.INF
C:\CGAKIT\FRESH640\CGA640.DRV
C:\CGAKIT\FRESH640\...the supplied fresh-Setup support files...
C:\CGAKIT\SETUP.EXE
C:\CGAKIT\CGAOLD.TXT
C:\CGAKIT\CGA\...the supplied existing-Windows drivers and support files...
```

Keep both complete folders beside `FRESH.EXE` and the kit's `SETUP.EXE`.
No Python, modern-PC preparation, manual INI edits or separate font/support
gathering is needed. `README.TXT` and `FRESH.TXT` contain the same fresh-install
instructions; `CGAOLD.TXT` retains the existing-Windows installer instructions.

## Fresh Windows installation

Use these paths for the example below:

| Purpose | Example path | Contents or use |
| --- | --- | --- |
| Extracted CGA kit | `C:\CGAKIT` | This download, including `FRESH.EXE` |
| Original Windows media | `C:\W30SRC` | Unchanged original Windows files, including Microsoft's `SETUP.EXE` and `SETUP.INF` |
| Display driver folder | `C:\CGAKIT\FRESH640` | The bundled driver and its support files |
| Windows destination | `C:\WINDOWS` | New installation directory chosen inside Microsoft Setup |

With unchanged original English retail Windows 3.0 media already collected in
`C:\W30SRC`, run:

```bat
C:
CD \CGAKIT
FRESH C:\W30SRC
```

**The argument `C:\W30SRC` tells FRESH where to read the Windows media.** The
display driver folder comes from the location of `FRESH.EXE`. With the kit
extracted in `C:\CGAKIT`, the launcher prints this exact line:

```text
Display driver path: C:\CGAKIT\FRESH640
```

Write down that complete path before pressing Enter to start original
Microsoft Setup. If you extracted the kit elsewhere, use the complete path
printed for your kit instead.

1. Choose the new Windows destination, normally `C:\WINDOWS`.
2. At **System Information**, choose **Display**, scroll down to **Other**
   (the last choice), and press Enter.
3. At the manufacturer's driver-disk prompt, enter **`C:\CGAKIT\FRESH640`**.
4. Select **Windows XT IBM CGA 640x200 mono**, then **No Changes** to accept
   the hardware list. Complete original Setup.
5. Start the installed Windows from `C:\WINDOWS` with `WIN /R`.

During copying, answer each disk request using the disk name:

| Setup asks for | Enter this path in the example |
| --- | --- |
| Manufacturer's display-driver disk, or **Windows XT CGA fresh Setup** | `C:\CGAKIT\FRESH640` |
| **Microsoft Windows 3.0 Disk #1**, or another original Windows disk | `C:\W30SRC` |

**Setup may prefill the previous disk's path. Replace it when the requested
disk changes.** For example, a request for **Windows XT CGA fresh Setup** may
still show `C:\W30SRC`; replace it with `C:\CGAKIT\FRESH640`. A subsequent
Microsoft Windows disk request may still show the driver path; replace it
with `C:\W30SRC`.

For original floppy media instead of a collected directory, insert the first
Windows Setup disk and run `FRESH A:\` from `C:\CGAKIT`. The display driver
path is still **`C:\CGAKIT\FRESH640`**. For Microsoft file requests, insert the
requested original Windows disk and use `A:\`. You can verify inputs without
starting Setup with `FRESH /CHECK C:\W30SRC` (or `FRESH /CHECK A:\`).

The driver, matching fonts and grabber are used during graphical Setup.
Fresh Setup currently offers one fixed 640x200 monochrome profile. To choose
another mode afterward, exit Windows and follow the existing-Windows route
below. [Fresh Setup scope and native evidence](CGA-FRESH.MD) record the tested
media-directory route, 640 KB IBM XT/CGA fixture and physical-hardware limits.
Other Setup versions are refused. Developer launcher rebuild inputs are in
[CGASRC.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CGASRC.ZIP).

## Choose a mode in an existing Windows installation

Run `SETUP C:\WINDOWS` to choose from a menu, or use one direct command
from this table. Standard and compact text sizes are listed side by side.
Press Enter at the menu to cancel without changes. `PAN` gives applications
such as Paintbrush a larger desktop through a movable view.

| Run from `C:\CGAKIT` | Result |
| --- | --- |
| `SETUP C:\WINDOWS 100` | Fixed 160×100 desktop, 16 RGBI colors, compact fonts and controls |
| `SETUP C:\WINDOWS PAN` | 320×200 desktop in 16 colors, seen through a movable 160×100 view |
| `SETUP C:\WINDOWS 320` | Standard UI; fixed 320×200: black, bright cyan, magenta and white |
| `SETUP C:\WINDOWS 320C` | Same four colors; compact UI and controls, 4×6 fixed text |
| `SETUP C:\WINDOWS 640` | Standard UI; fixed 640×200: black and white |
| `SETUP C:\WINDOWS 640C` | Same monochrome resolution; compact UI and controls, 4×6 fixed text |

The compact choices use 3×5 UI text and six-row controls to leave more
room. Standard choices keep larger UI text. Let your eyes decide: `320` and
`640` retain their existing defaults, and dropping the `C` restores that
resolution's standard fonts and controls. Both styles include their fonts.

[![Standard and compact UI at 320x200 and 640x200](CGA/COMPACT.PNG)](CGA/COMPACT.PNG)

*Actual Windows 3.0 emulation captures of both styles, displayed at 4:3 with
nearest-neighbor pixels. The compact views use the real smaller fonts and
OEM resources; only the presentation of the captures is enlarged.*

## Install the selected driver

For the fixed 160×100 desktop, type:

```bat
C:
CD \CGAKIT
SETUP C:\WINDOWS 100
```

Use the `SETUP.EXE` supplied in this download. It copies the driver and support
files and selects them in the Windows configuration automatically. There is
no separate Windows Setup selection or manual INI edit for this route.

Wait for checking and copying to finish; a 4.77 MHz 8088 takes several minutes.
Continue only after the installer reports:

```text
SETUP: selected CGA mode and fonts installed. Start Windows with WIN /R.
```

If it reports an error, stop and use the checks below before starting Windows.

[![Actual DOS installer output selecting CGA100.DRV and reporting successful installation](CGA/INSTALL/SETUP2X.PNG)](CGA/INSTALL/SETUP.PNG)

*Successful installation of mode `100`. Your chosen mode appears in the
`display.drv` line.*

## Start Windows in real mode

Change to the Windows drive and directory, then launch Windows:

```bat
C:
CD \WINDOWS
WIN /R
```

Use those same launch commands for later sessions. A new installation starts
PAN automatically. A previous OFF choice is preserved; run `PAN` inside Windows
to enable it again.

[![DOS prompt after changing to C:\WINDOWS and issuing WIN /R](CGA/INSTALL/START2X.PNG)](CGA/INSTALL/START.PNG)

*Starting Windows in real mode. `PAUSE` and the error-level check visible in
these captures belong to the recording harness; you do not need to type them.*

![Program Manager using the fixed 160×100 CGA desktop](CGA/DESK100X.PNG)

*Program Manager at 160×100, enlarged 4× from an existing Windows emulator
capture. This illustrates the installed display; capture provenance is in
[CGA image sources](CGA/CAPTURES.MD).*

## Reach windows and controls

- In `PAN`, **Ctrl+Alt+arrows** moves the viewport over the larger desktop.
  **Ctrl+Alt+Home** returns to the top left; **Ctrl+Alt+End** shows the active
  window's bottom/right. Edge scrolling and window following are available.
- In fixed `100`, those commands move windows and active client contents to
  expose hidden controls; the framebuffer remains 160×100.
- **Ctrl+Alt+S**, or `PAN /SETTINGS` from Windows Run, opens the matching
  settings. Apply saves changes; Cancel discards unapplied edits.

See [Panning settings and controls](PANNING.MD). Fixed `320` and `640` can opt
into a window workspace through `PAN`. Compact 160×100 fonts currently
show fallback boxes for extended characters.

## Change mode or undo

Exit Windows, return to `C:\CGAKIT`, and rerun the chosen Setup command with
`100`, `PAN`, `320`, `320C`, `640` or `640C`. To remove this packet's changes:

```bat
C:
CD \CGAKIT
SETUP UNDO C:\WINDOWS
```

Keep the package for mode changes and undo. `UNDO` preserves unrelated later
INI edits. The separate `RESTORE` recovery command replaces whole saved INIs
and loses later edits; use the included `CGAOLD.TXT` for that recovery path.

## If Setup stops

| Message or symptom | What to check |
| --- | --- |
| `Exit Windows completely before running SETUP` | Exit Windows itself, including any Windows DOS session, then retry from plain DOS. |
| `Existing Windows directory and SYSTEM folder required` | Use the directory containing your installed `WIN.COM` and `SYSTEM` folder. |
| Missing or damaged packet file | Re-extract the complete ZIP with directories preserved; keep `CGA` beside root `SETUP.EXE`. |
| Different, changed or incomplete installed files | Keep the recovery files and follow the package's `CGAOLD.TXT`; do not delete the journals or overwrite individual drivers. |

The [fresh text instructions](../src/cga/FRESH.TXT) become the package's
`README.TXT` and `FRESH.TXT`. The [existing-Windows text instructions](../tools/PAN/GUIDES/CGA.TXT)
cover the separate `SETUP` route.
Testing uses IBM XT/CGA emulation with normal 640 KB; physical cards, clone
CRTCs and composite output remain unqualified. PCjr, Tandy and EGA/VGA are
separate targets.

The DOS installer and launch screenshots above show the historical
existing-Windows route. They predate the fresh-install launcher and compact
choices; file sizes and helper-copy lines differ. The old directory-listing
capture is retained in the capture record, but does not show the current
archive's added `FRESH.EXE` and `FRESH640` folder. Use the current extraction
layout above. The current settings entry is `PAN /SETTINGS`.
[Original captures and exact version scope](CGA/INSTALL/CAPTURES.MD).

[Sixteen-color Paintbrush and capture details](CGA/CAPTURES.MD) ·
[Current release and checksums](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/windows-xt) ·
[CGA front door](https://github.com/astrobleem/windows-3-cga)
