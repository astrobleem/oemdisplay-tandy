# Windows XT

[Download WINXT.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WINXT.ZIP).
Extract it on the DOS computer. It contains `SETUP.EXE`, `README.TXT` and
an expanded `WINXT` folder with the drivers, apps, fonts, grabber and logos.
Keep those extracted files together; the ZIP is no longer needed.

The target is an original Tandy 1000 EX/HX with normal 640 KB and Windows 3.0
real mode. Original Windows and DOS are required. Installation runs on the
DOS computer itself.

For the complete desktop, exit Windows and run:

```bat
SETUP UPDATE C:\WINDOWS
```

For a new Windows installation, insert the first original Setup disk and run:

```bat
SETUP FRESH A:\
```

The installer gathers Windows files automatically, runs Setup as needed,
installs Tandy Start and the apps, and starts the desktop. Use `C:\STARTXT`
on every later launch. The full installer requires DOS 3.3 or later.

For drivers only, use the same expanded folder as an ordinary Windows Setup
source. The included `WINXT\DISPLAY.TXT` describes the guarded Setup and
launch entries; this path leaves the desktop and bundled apps uninstalled.
It does not require running the custom `SETUP.EXE`.

The display supplies a 640x256 desktop with a 320x200 hardware viewport.
Run XYCTL for viewport controls. 
