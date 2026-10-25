# Tandy fixed-resolution display profiles

**[Download WINXT720.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/WINXT720.ZIP)**

For Tandy 1000 EX/HX, 640 KB, DOS 3.3+ and an installed Windows 3.0 in real
mode. The profiles are 320x200x16, 640x200x4, 160x200x16, 320x200x4 and
640x200x2. At 160 pixels, many standard dialogs are cramped.

1. Extract the ZIP and use its WINXT720.IMG as a 720 KB data floppy. Boot
   your normal DOS system; the image is not bootable.
2. Exit Windows. With the disk in A:, select `A:`, `CD \`, then run `INSTALL`.
   It uses the bundled grabber and fonts to prepare `C:\WINXT`; no separate
   support-media folder is needed.
3. After successful preparation, select `C:`, `CD \WINXT`, then `INSTALL`.
   In Windows Setup choose Display / Other, enter `C:\WINXT`, choose your
   graphics profile and Complete Changes. Keep DOS configuration unchanged.
4. Start Windows every time with `C:\WINXT\WINXT` so its memory guard runs.

To select another fixed-resolution profile, exit Windows and run
`C:\WINXT\MODES`. These are hardware display choices, not software versions.
