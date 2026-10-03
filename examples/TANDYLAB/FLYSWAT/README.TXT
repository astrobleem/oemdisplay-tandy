FLY SWAT - REAL-HARDWARE TEST BUILD
===================================
Run inside Windows 3.0 using Program Manager / File / Run:
  C:\TANDYLAB\FLYSWAT\SWAT.EXE
C: is an example of the Tandy DOS drive; it may differ from the PC's D:.
Use your normal accepted TANDY88/RESERVE startup for custom display modes.
SWAT.EXE is the only runtime file. No DLL, asset, sound driver or INI change.

Click the play area or NEW to begin. Move the swatter with the mouse.
Click the fly for 10 points. Empty clicks and escapes cost a heart (three
hearts). P/Space or PAUSE pauses. N/R or NEW restarts. EXIT/Esc returns to
Windows. Switching away from fullscreen closes the game and restores Windows.

Normal launch uses fast fullscreen on the five accepted Tandy display modes.
It checks real mode, driver identity, BIOS mode, dimensions and ownership.
For other displays it uses a much slower windowed GDI fallback. /G explicitly
forces that fallback, which pauses on focus loss. Prefer normal launch on
an accepted Tandy mode for the hardware pass. First verify basic display
and mouse behavior with About/Cookie, then play this with no unsaved work.

One fly at a time; silent; normal play writes no files. Approximate-XT
emulation measured 4.33 updates/sec at 160x200 and 4.28 at 640x200x4.
These are emulator measurements, not calibrated physical Tandy timing.
Thirty native mode/exit/focus/occlusion tests and long live-shadow restore
checks passed. Physical hardware and external manual mouse input remain
unverified. Verify desktop and mouse restoration when exiting on hardware.

Do not use diagnostic switches for play. See DOCS\SWAT.TXT in the pack
for the original detailed notes. No automatic startup or idle hook is used.
