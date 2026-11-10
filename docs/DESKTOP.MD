# Install the full Windows XT desktop

[Download WXTF1107.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WXTF1107.ZIP).
For display drivers without changing your desktop or input drivers, use the
[driver-only guide](DRIVERS.MD) instead.

## Before you start

The full desktop requires:

- An original **Tandy 1000 EX/HX with 640 KB RAM**, running **DOS 3.3 or later**.
- Your own supported **English Windows 3.0 real-mode installation or original
  Setup media**. Setup checks the Windows metadata and loader it needs;
  incompatible or missing files cause it to stop.
- A writable C: drive. This installer uses **C:\WINDOWS** for Windows and
  **C:\WINXT** for its support files. Supplying another folder to `SETUP UPDATE`
  does not change those destinations. Use the driver-only route for Windows
  in a different directory.
- A compatible **COM1/IRQ4 serial mouse** if you want mouse input. Full Setup
  selects the supplied `WHEEL.DRV`, Tandy keyboard driver and sound driver.
  It does not preserve another Windows mouse driver. PS/2, USB and PicoMEM
  mouse input are not supported by this serial driver. The full launcher
  checks these selections, so changing the mouse afterward is not a supported
  way to retain the full configuration.

Back up an existing Windows installation first. If you use the separate
UISET compact-controls add-on, run `UISET C:\WINDOWS OFF` for each enabled
display mode before updating its driver. This pack does not include UISET.

**Fresh-install limitation:** preparation and finishing/update checks passed
in the recorded emulator tests, but the latest original Windows Setup attempt
stalled during hardware detection, before copying files. A complete clean
installation is not verified. The instructions below describe the intended
fresh route; they are not a claim that it passed end to end.

## 1. Extract the download

Extract the ZIP with its folders intact, for example into `C:\INSTALL`.
Keep `SETUP.EXE`, `README.TXT` and the expanded `WINXT` folder together.
The drivers, apps, fonts, grabber and artwork are ready to use; no compiler,
Python, manual INI edits or separate driver-support downloads are needed.

![DOS directory listing showing SETUP.EXE, README.TXT and the WINXT directory](SETUP/FILES.PNG)

*The screenshot uses C:\INSTALL. Use your extraction folder in the commands
below. Keep the complete source folder while installing.*

## 2. Choose a display for existing Windows

If your current Windows installation already uses the Tandy display mode you
want, keep it and go to step 3. If it still uses stock CGA or another display,
select the Tandy driver first. **UPDATE preserves the selected display; it
will not automatically select sixteen-color graphics.**

Exit Windows, change to the extracted `WINXT` folder and run:

```bat
C:
CD \INSTALL\WINXT
DISPLAY
```

In Windows Setup choose **Display > Other**, enter `C:\INSTALL\WINXT`,
and select **Tandy EX/HX 320x200 16 colors (no panning)**. Choose **Complete
Changes**, giving the same folder if Setup asks for the driver disk. Leave
the other Setup choices alone. [Illustrated walkthrough](DRIVERS.MD).

You can select one of the other fixed modes instead. The **HPXY 640x256**
choice supplies a larger desktop that you scroll through a 320x200 view.
It is optional, not a requirement for the full desktop.

## 3. Install or update the desktop

From plain DOS, change to the extracted folder containing `SETUP.EXE`:

```bat
C:
CD \INSTALL
SETUP UPDATE C:\WINDOWS
```

![SETUP UPDATE C:\WINDOWS typed at the DOS prompt in the extracted folder](SETUP/COMMAND.PNG)

This adds or updates Tandy Start, apps and support files, selects the bundled
keyboard/mouse/sound drivers, and keeps the display you selected. It starts
Windows when its checks succeed. If a check stops it, read the actual error;
do not bypass it by running Windows directly.

### If Windows is not installed yet

Read the fresh-install limitation above first. Allow about 30 MB for source,
installation and temporary files. Insert your first original Windows Setup
disk and, from the extracted folder, run:

```bat
SETUP FRESH A:\
```

Insert later disks when prompted. A complete original Windows Setup folder
can be supplied instead of A:. During Windows Setup choose **Computer:
Tandy 1000 EX/HX (WindowsXT)**. That preset selects fixed **320x200 sixteen
colors**, the Tandy keyboard and COM1 serial mouse. Keep the installation
location `C:\WINDOWS` and follow Setup's prompts. The Computer entry is a
Setup preset, not a replacement for Windows' original `SYSTEM.DRV`.
The installer then attempts
the same finishing steps used for an update.

## 4. Start Windows and choose options

Use **`C:\STARTXT`** from DOS for every later session. Tandy video shares
system RAM; the launcher reserves video memory and checks the installed files
before Windows starts. Never skip it to get past a reservation or file error.

If you already ran UPDATE while stock CGA was selected and want sixteen
colors, exit Windows, run `C:\MODEXT /320`, then `C:\STARTXT`.
`C:\MODEXT /XR1` selects the optional larger scrolling desktop instead.
For the other fixed profiles, use the [Display > Other route](DRIVERS.MD).

![Windows XT running with viewport controls open and the Start bar visible](SETUP/DESKTOP.PNG)

*This capture shows the optional scrolling desktop with its view moved down
to the Start bar. It is not the default fixed 320x200 display.*

On the scrolling desktop, **Ctrl+Alt+arrows** move the view and
**Ctrl+Alt+Home** returns home. **Ctrl+Alt+S** or `PAN /SETTINGS` opens its
settings. [Panning guide](PANNING.MD).

Choose **System > Screen saver** for Cube, Starfield, Matrix or Ovals.
New settings use a five-minute idle delay; updates preserve existing settings.

## Repair an existing installation

Exit Windows and run `C:\FIXXT` from plain DOS to repair the current full
desktop installation. When it succeeds, run `C:\STARTXT`. If repair stops,
keep its temporary files and read the stated error before trying again.

## Optional fonts

Display installation selects its required System, Fixed and Terminal fonts.
For additional application fonts, open **Control Panel > Fonts > Add** and
browse to `C:\WINXT\FONTS`. Choose any of the six XT Tandy fonts you want.
The three compact Helv fonts can affect existing applications' font choices,
so leave them unselected if you want to keep your current Helv fonts.
[Font guide](FONTS/README.MD).

[Screenshot details](SETUP/CAPTURES.MD).
