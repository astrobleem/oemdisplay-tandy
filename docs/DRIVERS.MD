# Windows XT: drivers through Windows Setup

[Download WINXT.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WINXT.ZIP) and extract it. The same download
offers the [full desktop installation](DESKTOP.MD) and a complete driver source
in its expanded `WINXT` folder. Drivers only do not require the custom `SETUP.EXE`.

Use installed Windows 3.0 real mode on an original Tandy 1000 EX/HX with
normal 640 KB and DOS 3.20+. Fonts, grabber and startup artwork are included.

1. Exit Windows. At the DOS prompt, change to the extracted `WINXT` folder
   and run `DISPLAY`. For example: `C:`, `CD \ALT\WINXT`, then `DISPLAY`.
2. In Windows Setup choose **Display / Other** and enter that folder's full
   path. If Setup asks for the Windows XT driver disk, enter the same path.
3. Select **Tandy EX/HX HPXY 640x256 hardware pan**, then **Complete Changes**.
   Keep your keyboard, mouse and DOS configuration choices unchanged.
4. For every Windows session, change to that `WINXT` folder and run `DISPWIN`.
   In Windows, run `XYCTL.EXE` from that folder for viewport controls.

`DISPLAY` and `DISPWIN` reserve shared video memory automatically and stop
if reservation fails. They use Windows in `C:\WINDOWS`; for another directory,
pass its drive and path, such as `DISPLAY D: \WIN30` and `DISPWIN D: \WIN30`.

Ctrl+Alt+arrows pan the 320x200 view over the 640x256 desktop;
Ctrl+Alt+Home returns home. XYCTL or Ctrl+Alt+H switches software/hardware
presentation. Exit Windows before changing display drivers through Setup.

[Other hardware](PLATFORM.MD) uses its matching packet. [Native installation
evidence](../tools/XROEM/NATIVE.JSN) records the alternate-folder Setup and launch test.
