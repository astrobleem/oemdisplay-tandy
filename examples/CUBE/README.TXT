WINDOWS XT ROTATING CUBE - LOCAL REVIEW CANDIDATE

Windows 3.0 real mode, 8086/8088, normal 640 KB.
Requires an installed working display driver and Windows. Not Windows 3.1.

INSTALL FROM REAL DOS, WITH WINDOWS FULLY CLOSED

Expand this whole kit into a DOS folder. Run:
  CUBESET C:\WINDOWS
Use the actual full Windows directory if different. Cube goes in C:\WINXT.
The current Windows XT Tandy Start is recognized by exact file identity.
Its replacement adds Cube to System > Screen saver. TSHCUBE.BAK preserves
the old shell. Existing saver choice, idle delay and other settings remain.
Select Cube and Apply to enable it. Options opens the Cube settings panel.
The delay remains 10-3600 seconds; 300 means five minutes.

For stock Windows 3.0, or an unrecognized Tandy Start, use:
  CUBESET /APPONLY C:\WINDOWS
This installs only the standalone app. Stock Windows 3.0 has no built-in
3.1-style .SCR selector; automatic idle launch is provided by Tandy Start.
No Python, driver files, OS media conversion or manual INI edits are needed.

USE INSIDE WINDOWS

  C:\WINXT\CUBE.EXE /C       Settings
  C:\WINXT\CUBE.EXE /S       Screen saver / preview
Running CUBE without arguments also opens settings. Select each button to
cycle Style, Speed and Cube size. Save stores the choices; Preview tries
the current choices. X or Escape closes settings. Unsaved choices are not
written. Save uses CUBE.INI in the active Windows directory.

Styles: Auto, Flat, Dither and Wire. Auto uses ordered black/white dithering
on monochrome displays and flat illumination on color displays. Flat maps
grays to the installed palette, so few-color modes have fewer light levels.
Wire shows all twelve edges. Speed and size each have three choices.
Drawing speed depends on the display driver; filled modes can be visibly
slow on a 4.77 MHz 8088. Small size or Wire reduces work.

One new keyboard gesture, mouse movement or mouse button wakes the saver.
Held wake gestures are drained before focus returns. Task switching, lost
focus/capture and Windows shutdown also dismiss it. This is not a lock.
Windows XT panning drivers with the XY query keep the cube centered in the
current visible viewport. Other displays use their reported screen size.

UNDO THE OPTIONAL SHELL UPDATE FROM DOS

Choose another saver before undoing. Exit Windows, then run:
  CUBESET /UNDO C:\WINDOWS
This restores the exact original Tandy Start from TSHCUBE.BAK. Cube and its
settings remain for standalone use. Do not discard the backup if a copy or
rename fails; /UNDO can recover when TSHELL.EXE is temporarily absent.

This candidate supports the project dimensions through GDI, without raw
framebuffer assumptions. TESTS.MD records the actual native mode coverage.
It does not certify every adapter, physical hardware, composite output or
all palette/driver combinations. No OS media, driver, compiler or emulator
is included. Do not publish this local candidate without approval.
