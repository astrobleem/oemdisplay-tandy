# Yamaha V6355D and Olivetti PC1 display drivers

Choose the profile for your hardware. Both use Windows 3.0 real mode,
640 KB and a 160x200, 16-color desktop:

- **Olivetti Prodest PC1, B000h:** [download PC1.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/PC1.ZIP).
  This uses `PC1YAMA.DRV`.
- **Standalone Yamaha V6355D, B800h:** [download YAMAHA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/YAMAHA.ZIP).
  This uses `YAM160.DRV` for the standalone emulator profile.

These are different memory apertures, with no automatic detection. Physical
PC1 and RGB/SCART output remain unqualified. Some dialogs clip at 160 pixels.

## Install

1. Extract your chosen packet to `C:\YAMAHA`. The fonts, grabber and startup
   logo are included. No separate Windows support-file collection is needed.
2. Exit Windows to plain DOS. From your Windows directory, run `SETUP`.
   Choose **Display / Other**, enter `C:\YAMAHA`, and select the matching label:
   **EXPERIMENTAL Olivetti PC1 160x200x16** or
   **EXPERIMENTAL Yamaha B800 EMULATOR ONLY**. Choose **Complete Changes**.
3. From your Windows directory, start with `WIN /R`. These adapters use
   ordinary Windows startup; they do not need Tandy's RESERVE launcher.

To select another display, exit Windows and run Setup from DOS.
[Technical support and test record](https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/yamaha/SUPPORT.MD).
Component notices are included in each packet.
