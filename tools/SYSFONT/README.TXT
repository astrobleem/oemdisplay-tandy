GRAPHICS SYSTEM FONTS

CG1SYS (5 rows), CG2SYS (6 rows), XTCSYS (8 rows) and XTESYS (12 rows)
are Windows System faces for menus, titles and controls. They preserve
all existing advances, resource metadata and dialog metrics. XTCSYS also
preserves the approved nine-pixel M/W and I/J/C/E/S spacing.

BUILD.PY --out NEW-DIRECTORY builds the four font resources. The existing
FONTPACK producer can stage a driver folder with these System resources
using its drivers phase:
  python -B tools/FONTPACK/PREPARE.PY drivers --out NEW-WINXT
Use --packet EXISTING-HARDWARE.ZIP to stage another supported OEM folder.

Run the packet's normal pre-Windows video-memory guard when required.
From your existing Windows directory, run Windows SETUP. Choose Display,
Other, enter the staged folder, select the matching display and Complete
Changes. Give the same folder again if Setup asks for its driver disk.
Keep the extracted source separate from an installed C:\WINXT directory.
For Tandy EX/HX, extract under C:\SFONTS, then use the existing driver entry:
  CD \SFONTS\WINXT
  DISPWIN C: \WINDOWS
DISPWIN performs the normal reservation and grabber/panning preparation.
The legacy full-install STARTXT/FIXXT path manages its original font set;
use DISPWIN for this driver-only font installation. Other hardware keeps
its matching driver launcher/guard. PCjr JRSTART expects C:\JRPAN;
ColorPlus CPWIN expects C:\CPPAN; Video II T2WIN expects C:\T2EXP.
Extract those folders to their expected locations before using the launcher.
Do not ignore a reservation failure.
The existing OEM descriptor selects its matching System resources.
For generic CGA Setup, standard 320/640 select eight-row XTC; compact
choices select five-row CG1. The included six-row CG2 is for the existing
dedicated 320 profile, not every generic 320 choice. Selection is unchanged.
There is no added updater, version recognition, backup or rollback program.

ASCII drawings are revised; extended coverage and fallbacks stay as before.
Fixed/OEM fonts and TEXT80/TXT40 fixed-cell System fonts are unchanged.
Proportional UI rendering remains unsupported in TEXT80/TXT40. Their
presenters recognize eight-row glyphs with eight-pixel advances and show
one BIOS character per cell. Variable advances lose that text recognition
and become block approximations. TEXT80 25/C25/PAN/VGA and TXT40 therefore
keep XTTSYS and their existing Fixed/Terminal fonts. This candidate does
not make those hardware text modes proportional or change their ROM face.
Existing 160-pixel dialogs can still clip. Fonts do not fix hardware flicker.
Video II uses the revised XTC System face, but a matching SL/2 fixture is
still required for candidate cold-start qualification. EX/HX emulation
cannot qualify Video II. These are development candidates; physical
scanout remains unqualified.
