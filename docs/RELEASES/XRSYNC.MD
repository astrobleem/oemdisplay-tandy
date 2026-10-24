# XRSYNC: current XR1 display update

**[Download XRSYNC.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-xrsync-2026-10-24/XRSYNC.ZIP)**

This installs the synchronous drawing update: a 640x256 Windows desktop
viewed through a 320x200, 16-color screen. Use an original Tandy 1000 EX/HX
with normal 640 KB and an existing Windows 3.0 real-mode installation at
`C:\WINDOWS`. For a complete new Windows XT desktop installation from your
Windows media, use the [rc.8 installer](RC8.MD) first.

## Prepare and install

1. Extract the ZIP on a modern computer. From that folder, run Python 3,
   pointing at your installed Windows 3.0 folder as seen by that computer:

   ```text
   python PREPARE.PY --windows C:\OWNW30\WINDOWS --out C:\XR155
   ```

   Use your actual host paths and a new output folder. A merged source-media
   folder is also accepted. Preparation finds and checks the required support
   file automatically; no manual file collection is needed.
2. Copy the entire prepared folder to **`C:\XR155` in DOS**. Exit Windows.
   From plain DOS, run:

   ```bat
   C:\XR155\RESERVE.COM
   ```

   Continue only after success, then run `C:\WINDOWS\SETUP`. Choose
   **Display / Other**, enter **`C:\XR155`**, select
   **Tandy XR1 640x256 synchronous Output**, and complete Setup. Keep the
   existing keyboard and mouse choices.
3. Start Windows with this command every time:

   ```bat
   C:\XR155\RUNSYNC.BAT
   ```

   RUNSYNC checks the video reservation before `WIN /R`. In Windows, use
   Program Manager's **File / Run** to start **`C:\XR155\XYCTL.EXE`** for
   viewport panning and software/hardware presentation controls.

After selecting XRSYNC, use RUNSYNC rather than the rc.8 STARTXT/FIXXT path,
which belongs to the original HPXY profile. No manual INI or launcher-pin
changes are needed. To return to the previous display, exit Windows, run
RESERVE successfully and select that display through DOS Windows Setup.

## Details

This is a display update, not a full Windows installation or a replacement
for the rc.8 shell installer. Windows 3.1 is unsupported. Large redraws can
still take time on an 8088. [Drawing and installation results](../RRSYNC.MD)
record the emulator scope; there is no new physical-hardware qualification.
