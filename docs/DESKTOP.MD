# Windows XT: native DOS installation

**[Download WINXTDOS.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8-dos.1/WINXTDOS.ZIP)**

Extract `WINXT.EXE` and put it on the DOS computer. Extraction works on DOS
or another computer; the included executable is ready to run.

Run this on the Tandy from plain DOS. It gathers Windows files automatically,
prepares the installer, reserves video memory and starts installation.
No Python, modern computer, conversion or manual file collection is required.

For an existing English Windows 3.0 installation at `C:\WINDOWS`:

```bat
WINXT UPDATE C:\WINDOWS
```

For new Windows, insert the first original English Windows 3.0 Setup disk:

```bat
WINXT FRESH A:\
```

Use its actual drive letter. The preparer asks for each next disk and gathers
the files itself. A complete existing Setup directory is also accepted:
`WINXT FRESH C:\WIN30SRC`. Expanded files and mode-A SZDD compression work
on the DOS computer. Allow about 30 MB for fresh source, installation and
temporary files. Windows is installed in `C:\WINDOWS`.

In fresh Setup, press Enter at Welcome and directory. At System Information,
choose Computer and select the first **Tandy 1000 EX/HX (WindowsXT)** entry.
Confirm **HPXY 640x256** and **PC/XT keyboard**; keep Setup's mouse choice.
Complete the remaining Windows Setup screens and choose **No Changes** for
DOS configuration. The finisher installs the COM1 wheel mouse and current
desktop automatically. Update preserves unrelated INI entries and shell customization.

Start every later session from plain DOS with **`C:\STARTXT`**.
Repair uses `C:\FIXXT`; `C:\FIXXT /VERIFY` adds full file comparison. If
interrupted, rerun `C:\SETUPXT` for the existing recovery/resume path.

The separately named `WINXT.ZIP` is the raw native-preparer kit.

Requires an original Tandy 1000 EX/HX, normal 640 KB, DOS 3.3+ and Windows
3.0 real mode. You supply Windows and DOS; their files are absent from the
download. The gathered Windows files remain private on the DOS computer.
For the separate synchronous display update, see [XRSYNC](RELEASES/XRSYNC.MD).

## What is current

XR1 provides a 640x256 logical desktop through a 320x200, sixteen-colour
viewport, Tandy Start, panning, COM1/IRQ4 mouse and optional wheel input.
XYCTL starts in Software mode; its menu or Ctrl+Alt+H enables Hardware.
Ctrl+Alt+arrows pan and Ctrl+Alt+Home returns home. Windows 3.1 is unsupported.

The desktop installs one shared SOUND driver for Windows alerts, legacy sound
calls, PIT instruments and Winamp. Current clients acquire and release the
same driver; no per-app driver replacement is needed.

[Current optional apps](DOWNLOADS.MD) have separate packets and install guides.

The display and keyboard drivers, fonts and artwork are preserved. The native
preparer has [fresh/update results](QUAL/DOSINST/RC8.JSN), separate from
[earlier runtime qualification](QUAL/XR1/INSTALL.JSN). No new physical
hardware test is claimed. NOTICE.TXT and the individual component notices
retain the Microsoft-derived driver notices and original project licenses.

## Optional Minesweeper

[Download MINESET.EXE](https://github.com/astrobleem/oemdisplay-tandy/releases/download/native-apps-2026-10-25/MINESET.EXE) and run
`MINESET` from DOS. In your normal guarded Windows desktop, choose Run and
enter `C:\MINETST\MINERUN.EXE`. The bundled About helper stays beside the app.
[Installation details](../tools/MINEAPP/INSTALL.TXT) cover another app folder.
SETUPXT does not install this separate app.
