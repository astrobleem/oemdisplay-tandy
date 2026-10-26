# Windows XT display installation

Use [WINXT.ZIP and the ordinary Windows Setup route](../DRIVERS.MD), or the
[full desktop installer](../DESKTOP.MD). Both use the same expanded driver folder.

<details>
<summary>Historical standalone XRSYNC installation record</summary>

# XRSYNC: DOS-native display installation

**[Download XRSYNC.EXE](https://github.com/astrobleem/oemdisplay-tandy/releases/download/xrsync-dos-2026-10-24/XRSYNC.EXE)**

Put this file on the Tandy and exit Windows. On the DOS computer, run:

```bat
XRSYNC C:\WINDOWS
```

Use your actual installed Windows 3.0 directory. The packet includes its grabber, fonts and artwork, prepares `C:\XR155`, reserves video memory
and opens normal Windows Setup. No Python, modern computer, conversion or
unpacking step is needed. It can be started from another drive.

In Setup choose **Display / Other**, enter **C:\XR155**, select
**Tandy XR1 640x256 synchronous Output**, then **Complete Changes**. Keep the
existing keyboard and mouse choices. Select **No Changes** for DOS configuration.

Start every session from plain DOS with:

```bat
C:\XR155\RUNSYNC.BAT
```

RUNSYNC verifies the installed display/fonts, reserves video memory and starts
Windows from the directory you supplied. In Windows, run
`C:\XR155\XYCTL.EXE` for viewport panning and presentation controls.

Requires an original Tandy 1000 EX/HX, normal 640 KB, DOS 3.20+ and an existing
English Windows 3.0 real-mode installation.

[ZIP alternative](https://github.com/astrobleem/oemdisplay-tandy/releases/download/xrsync-dos-2026-10-24/XRSYNC.ZIP):
extract on the DOS computer and run `XSETUP C:\WINDOWS` in that folder.
The EXE download includes the same payload and needs no ZIP utility.

The rendering driver is unchanged. [Graphics results](../RRSYNC.MD) and
[native installation results](../QUAL/DOSINST/XRSYNC.JSN) record emulator
qualification; there is no new physical-hardware claim. The download contains
the supplied grabber and all display support files. An installed Windows 3.0
system remains required.

</details>
