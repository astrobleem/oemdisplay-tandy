FLY SWAT 1.0 - Windows 3.0 / Tandy 1000 EX and HX
================================================

An original little mouse game: move the swatter and click the fly.
All graphics and code here are original; no Mario assets are used.

RUN
---
SWAT.EXE is the only runtime file. Keep it in its own folder.
Start Windows 3.0 normally (through your installed TANDY88 launcher when
using those display drivers). In Program Manager choose File, Run, then
enter the full path to SWAT.EXE. It is a Windows application, not a DOS game.

For the CompactFlash bundle, use the card's actual DOS drive letter:
  C:\TANDYLAB\FLYSWAT\SWAT.EXE
The drive called D: on the modern PC may be C: on the Tandy.
No installer, INI edits, custom DLL, sound driver, or extra memory needed.

PLAY
----
- Click in the play area to start, or click NEW.
- Move the little swatter with the normal Windows mouse.
- Click a fly: 10 points. An X flashes where you swat.
- Three hearts. An empty click or an escaped fly costs one heart.
- The fly flashes before escaping. Its movement speeds up gently.
- PAUSE/PLAY, P, or Space pauses/resumes.
- NEW, N, or R starts again. Space also restarts after game over.
- EXIT or Esc closes the game and returns to Windows.
- Switching away from fullscreen closes it and restores Windows.

FAST FULLSCREEN AND FALLBACK
----------------------------
On the five accepted TANDY88 display profiles, the game uses a fullscreen
fast renderer and its own mouse-swatter picture. It checks the driver name,
BIOS mode, real-mode state and display dimensions before enabling this path.
It checks foreground/visible-window ownership and exits when ownership is
lost. Windows' canonical display contents are restored on exit.

For other displays, or to force the slower windowed GDI fallback, run:
  SWAT.EXE /G
The fallback pauses when focus changes. It is much slower on the approximate
XT emulator profile; use normal fullscreen launch for the hardware test.

The game supports 160x200x16, 320x200x16, 320x200x4, 640x200x4 and 640x200x2.
One fly is active at a time. Graphics stay readable in monochrome.
Score stops at 59990. This first version is silent and does not touch PSG.
Normal play writes no files and changes no Windows or driver configuration.
It requests a 220 ms timer; slow delivery slows gameplay rather than jumping
forward. Emulator timing is not a calibrated physical 4.77 MHz measurement.
Please test it on the actual Tandy; physical hardware remains unverified.

BUILD AND TEST
--------------
python3 BUILD.PY --repo TOOLCHAIN_ROOT --dosbox DOSBOX --out NEW_DIR
Use your lawful Microsoft C6/Windows 3.0 toolchain and DOSBox-X.
See BUILDING.MD for source tools and TESTS.MD for bounded verification.
This directory adds the standalone source for the executable already shipped
in examples/TANDYLAB/FLYSWAT. Existing CF pack bytes are unchanged.

Development switches /T, /B, /R, /Q, /E, /W, /A, /O and /F write SWAT.LOG
(and some write SWAT.RAW), run diagnostics, and exit. Omit them for play.
/G is the ordinary windowed fallback. No Windows files, compiler, private
receipts, recordings or third-party artwork is included.
