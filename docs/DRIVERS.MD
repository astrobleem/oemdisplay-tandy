# Windows XT: drivers through Windows Setup

[Download the Windows XT pack](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WXTF1107.ZIP) and extract it. The same download
offers the [full desktop installation](DESKTOP.MD) and a complete driver source
in its expanded `WINXT` folder. Drivers only do not require the custom `SETUP.EXE`.

Use installed Windows 3.0 real mode on an original Tandy 1000 EX/HX with
normal 640 KB and DOS 3.20+. Its installed Windows Setup files must be
available. Fonts, grabber and static startup artwork are included. This
route keeps your existing shell, keyboard, mouse and sound selections when
you change only Display. It also installs the matching DOS clipboard and
panning support. It does not install the full desktop or its animated startup.

Back up Windows first. If the separate UISET compact-controls add-on is
enabled, restore it with `UISET C:\WINDOWS OFF` for each enabled display
mode before updating that driver. Substitute your actual Windows directory,
for example `UISET D:\WIN30 OFF`, when it is installed elsewhere.

## 1. Start Windows Setup

Exit Windows. At the DOS prompt, change to the extracted `WINXT` folder and
run `DISPLAY`. This example extracted the download into `C:\ALT`:

```bat
C:
CD \ALT\WINXT
DISPLAY
```

## 2. Choose Display, then Other

Use the arrow keys to highlight **Display** and press Enter. In the display
list, move down to **Other** and press Enter.

![Windows Setup display list with Other selected](SETUP/OTHER.PNG)

*Other lets Windows Setup read the driver from your extracted folder.*

## 3. Point to the expanded folder

Enter the full path to the folder containing `OEMSETUP.INF`, then press Enter.
For this example it is `C:\ALT\WINXT`, rather than `C:\ALT`.

![Windows Setup source prompt containing C:\ALT\WINXT](SETUP/FOLDER.PNG)

*Use your own extraction path. If Setup later asks for the Windows XT driver
disk, enter this same path again.*

## 4. Select the driver and finish

Select a fixed Tandy profile: **320x200 sixteen colors**, **640x200 four colors**,
**320x200 four colors**, **160x200 sixteen colors** or **640x200 monochrome**.
Choose **Tandy EX/HX 320x200 16 colors (no panning)** for a full-screen
sixteen-color desktop. The optional **Tandy EX/HX HPXY 640x256 hardware pan**
gives you a larger desktop viewed through a 320x200 window that you scroll.
At 160 pixels wide, many ordinary Windows dialogs do not fit.
Press Enter, then choose **Complete Changes** on System Information.
Keep your keyboard, mouse and DOS configuration choices unchanged.

![System Information showing the Tandy EX/HX HPXY display and Complete Changes selected](SETUP/SELECTED.PNG)

*The older screenshot illustrates HPXY. Check the Display line before accepting. Setup copies the included fonts,
grabber and startup artwork along with the driver.*

If HPXY was already selected, Windows Setup can retain its existing driver
bytes. After Setup returns, `DISPLAY` checks the selected HPXY driver and
asks before replacing only `SYSTEM\HPXY.DRV` from this folder. Type **Y**
to accept; Enter, **N** or end of input leaves it unchanged. The prompt can
also appear after canceling Setup while HPXY remains selected. No replacement
is offered when another display is selected.

The HPXY replacement step changes only that display-driver file, not the
shell, keyboard, mouse, sound or INI settings. After Windows Setup returns,
`DISPLAY` separately installs the matching grabber, clipboard and panning
support for the selected Tandy display, including their startup entries.
This driver-only route supports DOS 3.20; the full desktop installer still
requires DOS 3.3+.

## 5. Launch Windows

For every session, return to the expanded `WINXT` folder and run `DISPWIN`.
For the example above:

```bat
C:
CD \ALT\WINXT
DISPWIN
```

In Windows, run `PAN /SETTINGS` for viewport controls. The normal launcher
installs it automatically.

Tandy video shares system RAM. `DISPLAY` and `DISPWIN` reserve the required
video memory automatically so Windows cannot allocate it to programs. They
stop if reservation fails; do not bypass them by launching Setup or Windows
directly. They use Windows in `C:\WINDOWS`; for another directory,
pass its drive and path, such as `DISPLAY D: \WIN30` and `DISPWIN D: \WIN30`.

With HPXY, Ctrl+Alt+arrows pan the 320x200 view over the 640x256 desktop;
Ctrl+Alt+Home returns home. Use PAN /SETTINGS to choose Software or Hardware,
or Ctrl+Alt+H to switch presentation. Exit Windows before changing display
drivers through Setup.

[Other hardware](PLATFORM.MD) uses its matching packet. [Native installation
evidence](../tools/XROEM/NATIVE.JSN) records the alternate-folder Setup and launch test.

The included `WINXT\DISPLAY.TXT` has the same instructions without images.
The five-driver update passed native installed-runtime tests; the original
Windows Setup wizard was not rerun for this update.
[Screenshot details](SETUP/CAPTURES.MD).
