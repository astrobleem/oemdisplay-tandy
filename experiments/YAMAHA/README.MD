# Yamaha V6355D and Olivetti PC1 display drivers

Choose the profile for your hardware. Both use Windows 3.0 real mode,
640 KB and a 160x200, 16-color desktop. They have no automatic detection
and are not interchangeable:

- **Olivetti Prodest PC1, B000h:** [download PC1-B000-CANDIDATE03.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP).
  This uses `PC1YAMA.DRV`.
- **Standalone Yamaha V6355D, B800h emulator profile:** [download YAMAHA-B800-CANDIDATE03.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP).
  This uses `YAM160.DRV`.

## Install

1. Extract your chosen ZIP to a DOS folder, for example `C:\YAMAHA`.
2. Copy matching **CGA.GR2** and **CGALOGO.LGO** from your Windows 3.0
   installation or media into that folder. They may be in `C:\WINDOWS\SYSTEM`
   or `C:\WINDOWS`. These required support files are not included, and there
   is no staging helper for these packets.
3. Exit Windows completely. From plain DOS, select your Windows drive,
   change to its directory and run `SETUP`. Choose **Display / Other**,
   enter `C:\YAMAHA`, and select the label matching the ZIP:
   **EXPERIMENTAL Olivetti PC1 160x200x16** or
   **EXPERIMENTAL Yamaha B800 EMULATOR ONLY**. Complete Changes.
4. From your Windows directory, start with `WIN /R`. Use ordinary Windows
   startup; the Tandy launcher and RESERVE helper are for different hardware.

To change back, exit to plain DOS and use Windows Setup to select your
previous display.

## Known limits and technical details

PC1/B000 has build and host checks only; Windows runtime and Setup remain
untested. B800 has a separate 86Box Windows screenshot and DOSBox-X API/VRAM
tests. The reduced public B800 packet has not been tested end to end through
Setup. Neither profile has physical PC1 or RGB/SCART qualification. At 160
pixels, some dialogs clip.

[B800 screenshot](https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/yamaha/YAMAHA03.JPG) ·
[Detailed test scope](https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/yamaha/QUALIFICATION.MD) ·
[Source and evidence archive](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-CANDIDATE03-SOURCE-EVIDENCE.ZIP).
Component notices remain in each packet.
