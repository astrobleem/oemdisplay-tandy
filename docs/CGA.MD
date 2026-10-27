# Install the CGA driver for Windows 3.0

**[Download CGA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CGA.ZIP)**

This installs the CGA display driver, matching fonts, grabber and helpers into
an **existing Windows 3.0 installation**. You need **DOS 3.3 or later, 640 KB RAM,
Windows 3.0 real mode, and IBM CGA with RGBI output**. Windows and DOS are not
included; Windows 3.1 is unsupported. If Windows is not installed yet, install
it from your own disks first and confirm that `WIN /R` starts.

The examples use **`C:\WINDOWS`** for Windows and **`C:\CGAKIT`** for the extracted
download. Substitute your actual drives and directories.

## 1. Exit Windows and extract the package

If Windows is running, use Program Manager's **File → Exit Windows** and
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
DIR CGA
```

You should now have this layout:

```text
C:\CGAKIT\SETUP.EXE
C:\CGAKIT\README.TXT
C:\CGAKIT\CGA\CGA100.DRV
C:\CGAKIT\CGA\CGAPAN.DRV
C:\CGAKIT\CGA\...the other supplied files...
```

Keep the complete `CGA` folder beside the package's root `SETUP.EXE`.
You do not need Python, a modern-PC preparation step or separately collected
fonts and support files.

[![DOS directory listing showing SETUP.EXE, README.TXT and the CGA folder](CGA/INSTALL/FILES2X.PNG)](CGA/INSTALL/FILES.PNG)

*The extracted package in `C:\CGAKIT`, captured from the DOS guest.*

## 2. Choose a mode

Choose **one** command from this table. `100` is the small fixed desktop;
`PAN` gives applications such as Paintbrush more room.

| Run from `C:\CGAKIT` | Result |
| --- | --- |
| `SETUP C:\WINDOWS 100` | Fixed 160×100 desktop, 16 RGBI colors, compact fonts and controls |
| `SETUP C:\WINDOWS PAN` | 320×200 desktop in 16 colors, seen through a movable 160×100 view |
| `SETUP C:\WINDOWS 320` | Fixed 320×200: black, bright cyan, magenta and white |
| `SETUP C:\WINDOWS 640` | Fixed 640×200: black and white |

## 3. Install the selected driver

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

## 4. Start Windows in real mode

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

## 5. Reach windows and controls

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
`100`, `PAN`, `320` or `640`. To remove this packet's changes:

```bat
C:
CD \CGAKIT
SETUP UNDO C:\WINDOWS
```

Keep the package for mode changes and undo. `UNDO` preserves unrelated later
INI edits. The separate `RESTORE` recovery command replaces whole saved INIs
and loses later edits; use the included `README.TXT` for that recovery path.

## If Setup stops

| Message or symptom | What to check |
| --- | --- |
| `Exit Windows completely before running SETUP` | Exit Windows itself, including any Windows DOS session, then retry from plain DOS. |
| `Existing Windows directory and SYSTEM folder required` | Use the directory containing your installed `WIN.COM` and `SYSTEM` folder. |
| Missing or damaged packet file | Re-extract the complete ZIP with directories preserved; keep `CGA` beside root `SETUP.EXE`. |
| Different, changed or incomplete installed files | Keep the recovery files and follow the package's `README.TXT`; do not delete the journals or overwrite individual drivers. |

The [current text instructions](../tools/PAN/GUIDES/CGA.TXT) match the package.
Testing uses IBM XT/CGA emulation with normal 640 KB; physical cards, clone
CRTCs and composite output remain unqualified. PCjr, Tandy and EGA/VGA are
separate targets.

The DOS screenshots use the preceding public package. The current download
retains the same layout, mode commands and success message; file sizes and
helper-copy lines differ. The current settings entry is `PAN /SETTINGS`.
[Original captures and exact version scope](CGA/INSTALL/CAPTURES.MD).

[Sixteen-color Paintbrush and capture details](CGA/CAPTURES.MD) ·
[Current release and checksums](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/windows-xt) ·
[CGA front door](https://github.com/astrobleem/windows-3-cga)
