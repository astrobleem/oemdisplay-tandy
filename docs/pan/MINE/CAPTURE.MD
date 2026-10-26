# Minesweeper panning captures

These are real emulator captures from the converted Minesweeper build.
The [rc.8 app/shim download](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINMINE30.ZIP)
includes installation instructions, notices and the exact tested binary hashes.
This page preserves the original capture scope.

- Emulator: 86Box native headless build.
- Machine: Tandy 1000 HX, 8088 at 7.159090 MHz, 640 KB conventional memory.
- OS: Windows 3.0 real mode (`WIN /R`); no EMS or XMS.
- Display: 320×200×16 viewport over a 640×256 logical desktop. The PNGs are
  labeled **Cropped emulator capture** and show the verified 640×200 active
  guest viewport at its original pixel scale.
- Test case: MNSN2 passed with four snapshots, zero viewport/display pixel
  mismatches, intact reservation canary, clean DOS return, and the owned
  emulator stopped with its lease released.
- Tested software: the capture used the private combined HPXY XR1 PR151 + E1
  runtime. The public PR151 component is linked at
  [commit fc7b09b](https://github.com/astrobleem/oemdisplay-tandy/commit/fc7b09bdbe7e37dc9d562bdb746cf435b0628ba0).
  This component link does not identify the full capture build. The capture
  predates rc.8, whose current combined-runtime pins and installer tests are
  recorded separately in [the release guide](../../RELEASES/RC8.MD).
- Hardware: the combined XR1 PR151 + E1 runtime shown here was not physically
  tested. The separate HPXY R1 physical acceptance described in the
  [panning package guide](../../../downloads/experimental/hpan-hpxy/README.md)
  does not qualify this private combination or Minesweeper.

`REVEAL.PNG` shows the board at viewport origin (0,0). `PAN16040.PNG` shows
the viewport after a planned large jump to (160,40). That move used a full
viewport copy with hardware enabled and actual CRTC start 840; it is not an
incremental staged pan and was not a retrace fault. See `CROP.JSON` for the
source and lossless-crop hashes and exact exclusive crop rectangle.

The revealed-board frame follows a left click. No claim is made about the
right-button gesture in the panned frame. No executable, shim, Windows files,
disk image, or ROM is part of this evidence.
