TANDYLAB - COMPACTFLASH HARDWARE TEST PACK
========================================
Prepared 2026-10-03 for Windows 3.0 real mode on a Tandy 1000 EX/8088.
The included apps have prior native-emulator acceptance. Physical hardware
is still untested. This is a first hardware-test pack, not a compatibility
or speed guarantee. Your Windows installation and DOS boot files are yours.

ON YOUR MODERN WINDOWS PC
-------------------------
1. Confirm D: really is the CompactFlash card. Back up its current contents
   to a separate PC disk before changing anything. For boot-sector/partition
   recovery, a full card image is stronger than a file-only copy.
2. Extract TANDYLAB.ZIP on the PC. Copy its TANDYLAB folder to D:\, giving:
       D:\TANDYLAB\README.TXT
       D:\TANDYLAB\ABOUT\TABOUT.EXE
   Do not create D:\TANDYLAB\TANDYLAB by accident. If a TANDYLAB folder
   already exists, preserve it first instead of merging/overwriting blindly.
3. Finish your own DOS/Windows 3.0 setup as planned. This ZIP contains no
   Windows media, system DLLs/fonts, SDK/DDK/compiler or disk image.
   It has no main installer, automatic startup, shell or INI replacement.
4. Safely eject the card in Windows before removing it. Power the Tandy
   off before inserting/removing its card or adapter.

ON THE TANDY
-------------
D: is the PC card-reader letter, not necessarily its DOS letter on the Tandy.
At DOS, locate TANDYLAB with DIR on the actual card drive. The commands in
CATALOG.TXT use C: only as an EXAMPLE. Substitute the Tandy's actual drive.

These EXEs run INSIDE Windows 3.0, not at a DOS prompt or on modern Windows.
Use your normal working Windows startup procedure. If you installed one of
the custom Tandy display drivers, always use its accepted TANDY88 launcher
so RESERVE.COM succeeds first. Never bypass a reservation error with WIN.
Ordinary stock-CGA Windows installation does not use the custom driver yet.

In Program Manager choose File, Run, and type an application's full path.
Start with ABOUT\TABOUT.EXE, then COOKIE\COOKIE.EXE. Keep one test app open
at a time for the initial hardware pass. Follow CHECK.TXT in order.

WHAT IS HERE
-------------
ABOUT, COOKIE, SLOSH, PINBALL: small visual/control tests.
SHELL: optional Tandy Start bar with Run/Browse, as a normal application.
PSG, MOUTH, CHIMES: sound demos; never overlap PSG-producing programs.
BEATS: experimental sequencer with its exact app-local MIDIMAP.DRV.
GIF: GIF-to-BMP helper and a known 96x64 sample GIF.
DROP: two-app path-only drag/drop proof; read its special README first.
MATRIX: on-demand rain saver. It is not installed as an idle saver.
FLYSWAT: final silent fly-swatter game; normal launch uses fast fullscreen
  on accepted Tandy modes. Test after basic display/mouse checks.
EXPER: optional COMMDLG demo (use CDSTART) and slow windowed maze.
  Leave these for later. CDSTART fixes Windows 3.0 private-DLL lookup.
DRIVERS: optional support-free display toolkit; NOT an install-ready disk.
DOCS: preserved upstream detailed notes. Their historical C:\ paths and
source/evidence references describe the standalone source packages. Use
this pack's CATALOG, CHECK and folder README files for the copy/run layout.

SAFETY / LIMITS
---------------
- Preserve SYSTEM.INI, WIN.INI, CONFIG.SYS, AUTOEXEC.BAT and the working
  display/boot setup. Do not copy app DLLs/DRVs into WINDOWS or SYSTEM.
- No SOUND.DRV/TSOUND.DRV install is needed for the included sound demos.
  Standard Windows SOUND support must already be installed by Windows.
- Test sound quietly, one program at a time. Stop/close it before the next.
  Frozen cooperative Windows can delay cleanup; physical timing is untested.
- TEXIT /preview only plays audio. TEXIT without /preview asks first and
  then attempts a normal Windows exit. It is not tied to TSHELL shutdown.
- Avoid undocumented/test switches. Some diagnostics can exit Windows.
- Cookie Save replaces its own COOKIE.SAV. GIF conversion creates a new BMP.
  Other file-writing caveats are listed in CATALOG and the folder notes.
- Back up any saves/results before removing or replacing this folder.

The experimental hardware TEXTMODE driver is deliberately not in this pack:
it needs transformed copies of owned fonts and has known character/redraw
corruption. Keep that separate lab proof away from the fresh Windows setup.

MANIFEST.SHA lists SHA-256 hashes for the delivered files except itself.
SOURCES.TXT identifies source projects/standalone source archives.

FLY-SWATTER GAME INCLUDED
-------------------------
FLYSWAT\SWAT.EXE is the final 16,989-byte hardware-test build. Normal launch
is fast fullscreen on accepted Tandy modes; /G selects a much slower GDI
fallback. EXIT/Esc or switching away restores Windows. It is silent and
needs no additional files or startup changes. Read FLYSWAT\README.TXT.
