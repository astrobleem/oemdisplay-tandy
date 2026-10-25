# Setup screenshot notes

These pictures illustrate the current expanded
[WINXT.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WINXT.ZIP),
648,375 bytes, SHA-256
`dac91c866628f71d14d6fa52a930339fac5bf07546e79a43f03e6f3ead5b49e8`.
They are direct emulator framebuffer captures of DOS and Windows 3.0 on
a Tandy 1000 HX profile, taken on 25 October 2026.

The guide images remove unused screen borders and use two-times nearest-neighbour
enlargement for readable text. No screen text, choices or file listings were
drawn or replaced. Original captures are linked below.

| Guide image | What it shows | Original |
| --- | --- | --- |
| Extracted files | The published ZIP's `SETUP.EXE`, `README.TXT` and `WINXT` directory in `C:\INSTALL` | [FILES.PNG](RAW/FILES.PNG) |
| DOS command | `SETUP UPDATE C:\WINDOWS`, immediately before Enter | [COMMAND.PNG](RAW/COMMAND.PNG) |
| Installed desktop | The whole active viewport after panning down to show Start; the viewport-control window remains open, partly above the view | [DESKTOP.PNG](RAW/DESKTOP.PNG) |
| Other | Stock Windows Setup's display list | [OTHER.PNG](RAW/OTHER.PNG) |
| Source folder | The same expanded files at `C:\ALT\WINXT`; custom SETUP was not run for this path | [FOLDER.PNG](RAW/FOLDER.PNG) |
| Complete Changes | HPXY selected in the [qualified alternate-folder installation](../../tools/XROEM/NATIVE.JSN) of the same ZIP | [SELECTED.PNG](RAW/SELECTED.PNG) |

The full-install example uses an existing Windows installation and the UPDATE
path. The separate FRESH command in the guide is text, not a claim that its
disk prompts appear in these UPDATE screenshots. Windows Setup's keyboard,
mouse and other existing settings can differ from those pictured.

The [installation qualification](../QUAL/DOSINST/EXPAND.JSN) remains the
functional test record. These documentation captures change no installer,
driver, app or support-file bytes. The download's text-mode `README.TXT` and
`WINXT\DISPLAY.TXT` remain usable without the pictures.
