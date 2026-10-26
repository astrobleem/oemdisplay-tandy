# Panning settings

Use the settings offered by your installed display. Each helper runs one
available approach at a time.

| Display | Available approach | Open settings inside Windows |
| --- | --- | --- |
| Windows XT HPXY | Software or hardware viewport, as reported by the driver | XY overview: **Options / Panning settings** |
| PCjr or ColorPlus 320x400 | Software viewport over the larger display bitmap | Run the packet's **PANCFG SETTINGS** |
| Fixed 320x200 or 640x200 | Window workspace: move application windows around a 2048x2048 workspace | Run **XTPAN /SETTINGS** or the packet's **PANCFG SETTINGS** |

Apply saves the available settings; Cancel discards edits. Reopening settings
uses the running helper. The window fits the 320x200 screen.

The window workspace uses no larger display bitmap. Move to an edge to pan,
or use Ctrl+Alt+arrows. **Home** brings windows back into reach. Closing the
helper, using **PANCFG OFF**, or leaving Windows normally also recovers them,
including the saved positions of minimized and maximized windows. It tracks
up to 24 application windows; if that limit is reached, close windows or use
Home before panning again.

For PCjr and ColorPlus, select the included fixed driver through the packet's
INSTALL if you want the window workspace. Select the 320x400 driver for its
software framebuffer viewport instead. Keep using JRSTART or CPWIN as directed
by the [installation guide](SOFTPAN/RELEASE.MD). Windows XT installation and
its HPXY viewport remain in the [desktop guide](DESKTOP.MD).

These are Windows 3.0 real-mode emulator results. The window workspace moves
windows through USER; it does not modify USER.EXE or add hardware panning.
