# Windows XT desktop bundle

**[Download WINXT-XR1.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINXT-XR1.ZIP)**

For an original Tandy 1000 EX/HX with 640 KB, DOS 3.3+ and Windows 3.0 real
mode. This bundle supplies Tandy Start, the HPXY panning profile, COM1 wheel
input, fonts and apps. It is the complete desktop product; the standalone
display packet is listed separately in [current downloads](DOWNLOADS.MD).

## Install

1. On a modern computer, extract the ZIP. From that folder, run Python 3.8+
   with your matching English Windows 3.0 media collected in `C:\WIN30SRC`:

   ```text
   python PREPARE.PY --windows-media C:\WIN30SRC --mode fresh --out C:\XR1NEW
   ```

   Choose a new output folder. Expanded files and original mode-A SZDD files
   are accepted. The preparer checks the supported media set automatically;
   if it refuses, read its message before continuing. Supply matching Windows 3.0 media, including its Setup files. Allow about 20 MB on the DOS drive
   for a fresh source/install and temporary files.
2. Transfer the prepared **DOS-CROOT contents** to DOS `C:\`, preserving your
   DOS boot files and configuration. Exit Windows completely and run:

   ```bat
   C:\SETUPXT
   ```

   Fresh Setup uses `C:\WINDOWS`: choose the first **Tandy 1000 EX/HX**
   Computer entry, **HPXY 640x256**, **PC/XT keyboard**, **COM1 wheel mouse**
   and **No Changes** for DOS configuration.
3. Start Windows with this command on every launch, including after reboot:

   ```bat
   C:\STARTXT
   ```

Windows and DOS media are supplied by you. The prepared folder contains
Windows files; the public ZIP contains the project components and preparer.

## Repair

From plain DOS, run `C:\FIXXT`. `C:\FIXXT /VERIFY` adds a full file comparison.
The included README.TXT covers interrupted installation and recovery.

## Optional Minesweeper

[Download MINESET.EXE](https://github.com/astrobleem/oemdisplay-tandy/releases/download/native-apps-2026-10-25/MINESET.EXE) and run
`MINESET` from DOS. In your normal guarded Windows desktop, choose Run and
enter `C:\MINETST\MINERUN.EXE`. The bundled About helper stays beside the app.
[Installation details](../tools/MINEAPP/INSTALL.TXT) cover another app folder.
SETUPXT does not install this separate app.
