# CGA graphics for Windows 3.0

**[Download CGA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/CGA.ZIP)**

Windows on IBM CGA, including **160x100 with 16 colors**, compact fonts and
small controls. You need installed Windows 3.0 real mode, DOS 3.3+ and 640 KB.

[![Paintbrush showing a sixteen-color twilight landscape on CGA](CGA/PAINT100X.PNG)](CGA/PAINT100.PNG)

*Windows 3.0 Paintbrush at 160x100, enlarged 4x. The picture itself uses all
16 RGBI colors, verified pixel for pixel against the opened BMP.
[Original 160x100 image](CGA/PAINT100.PNG) Â· [Palette view](CGA/PAINTPLX.PNG) Â·
[Try the picture](CGA/COVE16.BMP).
Captured from native IBM XT/CGA emulation; not a real-hardware photograph.*

## 1. Extract the download

Keep root `SETUP.EXE`, `README.TXT` and the expanded `CGA` folder together.
This is a drivers-only packet for existing Windows; fonts and support files
are included. Use its root SETUP to install the compact dialog fonts too.

## 2. Choose a mode

Exit Windows. From the extracted folder in DOS, run:

```bat
SETUP C:\WINDOWS 100
```

Use your actual Windows path. Replace `100` to choose another mode:

| Choice | Resolution and colors |
| --- | --- |
| `PAN` | 320x200 desktop in 16 colors, viewed through a movable 160x100 screen |
| `100` | 160x100, 16 RGBI colors, smallest fonts and controls |
| `320` | 320x200, black / bright cyan / magenta / white |
| `640` | 640x200, black and white |

Wait for Setup's success message; a 4.77 MHz 8088 takes several minutes.

## 3. Start Windows

Change to your Windows directory and run `WIN /R`.

[![Notepad File Open with compact fonts and controls at 160x100](CGA/OPEN100X.PNG)](CGA/OPEN100.PNG)

*Notepad File Open at 160x100, enlarged 4x.
[Original image](CGA/OPEN100.PNG).*

In mode `100`, **Ctrl+Alt+arrows** moves the window workspace;
**Ctrl+Alt+Home** returns home and **Ctrl+Alt+End** exposes the active window's
bottom/right. File Manager's maximize and File Open commands help on this
short screen. Extended characters currently use fallback boxes.

[![File Manager directory view at 160x100](CGA/FILE100X.PNG)](CGA/FILE100.PNG)

*File Manager at 160x100, enlarged 4x; this frame uses five colors.
[Original image](CGA/FILE100.PNG).*

## A larger desktop on the same CGA screen

Choose `SETUP C:\WINDOWS PAN` in DOS, then start `WIN /R`. Setup installs
and starts the viewport helper automatically. Windows gets a 320x200 desktop;
the physical screen still shows 160x100 pixels in 16 colors.

**Ctrl+Alt+arrows** moves the view, **Ctrl+Alt+Home** returns to the top left,
and **Ctrl+Alt+End** shows the active window's bottom/right. Moving the pointer
to an edge scrolls after a short dwell. New windows and controls reached with
Tab are brought into view. Commands sent while Windows is loading an app are
retained in a bounded queue and applied afterward.

**Ctrl+Alt+S** opens Panning settings; `PAN /SETTINGS` from Run is the common entry.
Change Step, Dwell, Follow active window or Pan at screen edge, then Apply.
Apply saves in WIN.INI; Cancel discards un-applied edits. Step rounds to a
multiple of 8 across: entering 20 gives 24. Home moves the view without
changing the settings.

The compact dialog now shares its layout and input handling with the other
panning helpers. See [current shared settings and controls](PANNING.MD).

![Paintbrush in the panning desktop](CGA/PANPAINT.PNG)

*Paintbrush on the same 160x100 viewport of the larger desktop.
[Another part of the picture](CGA/PANPAL.PNG). These are emulator captures.*

## Other modes and undo

Exit Windows and rerun SETUP with `100`, `PAN`, `320` or `640` to change mode. To undo:

```bat
SETUP UNDO C:\WINDOWS
```

| 320x200, four colors | 640x200, monochrome |
| --- | --- |
| [![Notepad File Open in CGA four-color mode](CGA/OPEN320X.PNG)](CGA/OPEN320.PNG) | [![Notepad File Open in CGA monochrome mode](CGA/OPEN640X.PNG)](CGA/OPEN640.PNG) |

*[Original 320x200 image](CGA/OPEN320.PNG) Â·
[Original 640x200 image](CGA/OPEN640.PNG). The 320 frame uses three of its
four available colors; the 640 frame uses both.*

These modes were tested in IBM CGA emulation. Physical cards, clone CRTCs,
composite, PCjr/Tandy and EGA/VGA remain separate targets.
[Image sources and capture details](CGA/CAPTURES.MD) Â·
[Text instructions and recovery](../downloads/experimental/CGA/README.TXT).

The compact settings use the same implementation as the other current panning
helpers. `PAN /SETTINGS` is the common entry; see [Panning](PANNING.MD)
for controls, supported approaches and current native screenshots.
