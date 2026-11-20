GRAPHICS SYSTEM FONTS

CG1SYS (5 rows), CG2SYS (6 rows), XTCSYS (8 rows) and XTESYS (12 rows)
are Windows System faces for menus, titles and controls. They preserve
each resource's advances and metadata; changing the selected face can change
the resulting UI metrics. XTCSYS also
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
The source CGA descriptor now makes ordinary 320 and 320C select the same
proportional six-row UI6 System and compact controls, matching the native
installer. Generic 640 and the explicit large OEM choice retain eight-row
XTC; the native legacy 320L choice retains six-row CG2. Published CGA/SFCGA
downloads still have their prior selection until rebuilt and released.
See tools/RESUI/README.MD for the measured feature-branch checkpoint.
There is no added updater, version recognition, backup or rollback program.

ASCII drawings are revised; extended coverage and fallbacks stay as before.
Fixed/OEM font bytes and TEXT80/TXT40 fonts are unchanged. Low-viewport
graphics OEM choices select existing 4x6 Fixed/Terminal companions so
Windows 3.0 dialog templates also scale; these remain deliberate monospace.
The feature branch uses CG1 at 160 pixels, separate original UI6 at 320
pixels and corrected XTC at 640 pixels, with viewport-appropriate OEM chrome.
Only resources change: rendering, aspect, palette and memory guards stay
exact. HPXY retains its accepted driver identity and existing compact chrome.
Proportional UI rendering remains unsupported in TEXT80/TXT40. Their
presenters recognize eight-row glyphs with eight-pixel advances and show
one BIOS character per cell. Variable advances lose that text recognition
and become block approximations. TEXT80 25/C25/PAN/VGA and TXT40 currently
keep XTTSYS and their existing Fixed/Terminal fonts. Their System/UI is an
open requirement, not completed or exempt. No exact same-mode pixel fallback
is implemented here; their defaults remain unchanged.
Existing 160-pixel dialogs can still clip. Fonts do not fix hardware flicker.
Video II uses the revised XTC System face, but a matching SL/2 fixture is
still required for candidate cold-start qualification. EX/HX emulation
cannot qualify Video II. These are development candidates; physical
scanout remains unqualified.
