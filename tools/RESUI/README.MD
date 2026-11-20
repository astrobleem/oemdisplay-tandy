# Resolution-aware Windows UI checkpoint

This feature branch starts the all-profile UI correction. It does not declare
all graphics adapters, text presenters or released packages finished. PPCUI's
separate PPC512 six-row tester and every accepted graphics module remain intact.

The current CGA `320` argument selects **CGA32C.DRV + UI6SYS.FON**.
The six-row follow-up below supersedes the first five-row visual baseline.
`320C` remains an exact alias, including the interactive menu's ordinary
320 choice. `320L` explicitly opts into the former large-control native
profile. The ordinary OEM 320 entry and its 320C alias select the same compact
resource/font group; the old large OEM choice is explicitly opt-in. No new
intermediate 320 UI, mode, renderer or installer is introduced.

The driver-only System-font producer uses this source OEM descriptor too;
otherwise rebuilding SFCGA from the historical full archive would resurrect
the wrong default. Historical full archives themselves are still unchanged.

## Authoritative scope

`tools/CURRENT/PRODUCTS.JSN` and `docs/DOWNLOADS.MD` select consumer products.
`tools/SYSFONT/PACK.PY:PACKETS` names eight graphics OEM source packets.
Their actual embedded OEMSETUP.INF choices take precedence over old staging
copies: for example shipping JR/ColorPlus panning is 640x400, despite an
older ColorPlus staging descriptor still saying 320x400. `AUDIT.PY` prints
the archive choices, actual System advances and OEM geometry to the console;
it emits no manifest. Source/build and text-mode definitions are below.

| Family | Shipping/default and retained profiles | Source/build entry |
| --- | --- | --- |
| Tandy EX/HX | 320x200x16; 640x200x4; 320x200x4; 160x200x16; 640x200x2; HPXY 640x256 desktop / 320x200 view | MODEPROF/BUILD88; FONTPACK and XROEM; HPXY resources |
| CGA | 160x100x16; 320x200 desktop / 160x100 view; 320x200x4 large/compact; 640x200 mono large/compact | STAGECGA, CMPRSC, CGASET, PACKCGA; PAN/CGASTAGE; FRESHPK's fresh 640 entry |
| PCjr | fixed 320x200x16; 640x400 desktop / 320x200 view | pcjr/BUILDJR, BUILDCOM, INSTALL/JRPACK; UPAN |
| ColorPlus | fixed 320x200x16; 640x400 desktop / 320x200 view | pcp/BUILDPCP; SPPACK; UPAN |
| PC1512 | 640x200x16 | pc1512/BUILD15; P15PACK |
| Video II SL/2 | 640x200x16 | tga2/T2BUILD, T2PACK; actual SL/2 fixture still needed |
| Olivetti PC1 | 160x200x16, B000 window | experiments/YAMAHA; Yamaha packet recipe |
| Standalone Yamaha | 160x200x16, B800 window | experiments/YAMAHA; emulator-only qualification |
| TEXT80 | C25 and 25: 640x200 / 80x25; PAN: 640x400 desktop / 640x200 view; VGA: 640x400 / 80x50 | text80/BUILDT80, T80UI, T80TALL; text80 native selector |
| TXT40 retained build | 320x200 / 40x25 | txt40/BUILDT40, T40PRES; BUILDT80's t40 variant; not a separate current catalog ZIP |

Panning UI must follow the physical viewport and pixel shape, rather than
assuming that a 640-wide logical desktop gives a 640-wide visible screen.
Fixed/Terminal/application faces deliberately requesting monospace are
separate roles from the UI System face.

## First checkpoint: five-row 320 slice (superseded visually)

The graphics System faces already have genuinely different advances: CG1
has `i=2/W=4`, CG2 `2/6`, corrected XTC `4/9`, XTE `4/14`. This does not make
all existing controls suitable for their resolution. Standard fixed modules
mostly retain 27x14 caption buttons, 18x11 vertical and 23x9 horizontal
arrows, and 11/23 thumb configuration, including narrow 160-wide modules.
HPXY already has a different 16x8 / 12x8 resource baseline. CGA compact
uses 8x6 caption buttons and 6x6 arrows/thumbs. TEXT80's selected XTTSYS is
actually fixed width (`i=W=8`); T80CMP changes cell-aligned chrome, not that.
Raw full archives sometimes carry older XTC resources (W=14); current
System-font OEM producers overlay the corrected W=9 resource. Neither
font resource flags nor archive names are sufficient runtime evidence.

The old native `320` route was also inconsistent with old OEM Setup: the
native selector chose six-row CG2, while OEM's large 320 group chose XTC.
Both kept the large OEM controls. That is the original 320 path relevant
to Alex's report, not an already-selected compact 320C.

Actual Windows 3.0 real-mode results, CGA, DOSBox-X 8086-prefetch, normal
640 KB, no EMS/XMS/UMB, original Windows Paintbrush loaded from private media:

| Runtime measurement | Old native 320 | New 320 and 320C |
| --- | ---: | ---: |
| System `GetTextExtent("i") / ("W")` | 2 / 6 | **2 / 4** |
| System height / dialog base units | 6 / 4x6 | 5 / 3x5 |
| Menu / caption height | 14 / 16 | 6 / 8 |
| Caption button | 27x14 | 8x6 |
| Vertical scrollbar width / horizontal height | 18 / 9 | 6 / 6 |
| Vertical / horizontal thumb | 11 / 23 | 6 / 6 |
| Paintbrush Open pushbutton height | 12 | 10 |
| Maximized Paintbrush client height | 170 | 186 |

Both native arguments selected identical driver/font files and produced
identical measured UI geometry. Fixed and Terminal each measured `i=W=4`.
The ordinary OEM default selected the same compact driver/System and
measured System `2/4`, caption 8, menu 6 and 6-pixel scrollbars. Existing
application-font registrations can give a dialog different geometry between
installation routes; OEM Setup preserves them. Paintbrush Open's important
buttons and the small Save-style dialog fit in all tested routes. All
completed clean DOS return. These are focused checks, not physical hardware
or every application/font/legacy-install upgrade qualification.

## Text cells remain an open requirement

The TXT40/TEXT80 presenter converts a logical pixel shadow into character
cells using ROM glyph matching and glyph hints (T40PRES). The cell is eight
logical pixels wide; changing System advances alone can make GDI report
proportional widths while the physical presenter loses/merges the glyphs.
That would not meet the requirement. CGA has no writable character generator
for arbitrary per-cell pixels. EGA/VGA font RAM could support an explicitly
bounded glyph-cache renderer, but at the existing 8x8 cell geometry its finite glyph bank does not guarantee
arbitrary exact pixel tiles across the whole screen. A different graphics
mode is a different backend and cannot silently be called the same text mode.
No universal exact same-mode pixel fallback has been implemented here. These
profiles are neither completed nor exempt; their defaults remain unchanged.

## Reproduce and continue

`python tools/RESUI/AUDIT.PY` audits all current packet inputs.
`python tools/RESUI/BUILD320.PY NEW_PRIVATE_DIRECTORY` stages the existing
installer source and payload without standalone generated audit manifests.
Use the existing MSC6 DOS workflow to compile native-src/SETUP.C, /G0 /AS,
with a 4096-byte stack. The existing installer integrity/transaction code is
retained; this adds no installer/version/checksum mechanism. Private staging
contains existing licensed support inputs and is not a publication archive.
CHECK.C/DEF provide the original Win16 geometry/Paintbrush probe. Screenshots
are native logical Windows pixels; physical sampling/readability is untested.

The follow-up below carries selection through all eight ordinary graphics OEM
producers. Full fresh-media acceptance and legacy installed-package upgrades
remain open; current released archives remain unchanged.

Native settled Paintbrush comparison: [old 320](../../docs/RESUI/OLD320.PNG)
and [new ordinary 320](../../docs/RESUI/NEW320.PNG).

## Release/front-door handoff

The separate windows-3-cga README's Choose a display mode section directs
users to plain 320 and lists 100/PAN/320/640. Its Download CGA.ZIP link points
to oemdisplay-tandy's windows-xt release, whose archive is unchanged here.
That existing download still selects the old large native 320 path. Before
announcing the fix as shipped, rebuild and qualify the bundled DOS launcher,
CGA OEM folder and SFCGA OEM folder together. Their source defaults and
instructions are now aligned. The other repository was only read, not edited;
its 320C alias/320L explanation and release-facing wording remain follow-up.

## Six-row caption and graphics-family follow-up

Chad found the first five-row title hard to read. UI6.PY now builds a
separate original six-row System face with one spacing column, wider m/w,
and hand-tuned counters/stems. Neither released CG1/CG2 bytes nor PPCUI
change. The native Paintbrush title exactly matches UI6's 82-pixel glyph
sequence at (115,0): this verifies the caption uses the selected System
strike, beyond merely measuring its proportional flag. Native screenshot
pixels are binary black/white; the supplied crop had 13 grayscale levels
in its title area. Resampling contributes distortion, but the crowded
five-row design also needed work; integer enlargement does not repair it.
The user's attachment is not included in this repository.

| Current compact 320 measurement | Result |
| --- | ---: |
| System height / isolated i,W | 6 / 2,6 |
| Dialog base units | 4x6 |
| Caption / caption button | 8 / 8x6 |
| Menu | 7 (one pixel above first checkpoint) |
| Scrollbars / thumbs | 6 |
| Paintbrush client height | 185 (first checkpoint 186) |
| Paintbrush Open buttons | all fit, 12 high, right edge 283 |

Both rebuilt native `320` and `320C` installations/cold starts completed;
settled menu, Paintbrush and Open captures are byte-identical between them.
Save-style dialog, actual Paintbrush Open, closure and DOS return passed.
Ordinary Windows Setup Display > Other also committed CGA32C + UI6 and
completed a cold-start check. These are source candidates,
not an update to the released CGA download.

[Previous native title at 4x](../../docs/RESUI/PREV4X.PNG),
[current title at 4x](../../docs/RESUI/READ4X.PNG), and
[current full native Paintbrush](../../docs/RESUI/READ320.PNG).
Integer scaling uses nearest-neighbor; no generated artwork or user image.

GRAPHICS.PY is shared by FONTPACK's eight ordinary graphics OEM stages and
PACKCGA's existing native serializer. It selects by physical viewport:

| Physical width | System | Chrome / companions |
| --- | --- | --- |
| 160 | existing CG1, five rows, i/W 2/4 | 8x6 caption buttons, 6x6 arrows/thumbs; existing 4x6 Fixed/Terminal |
| 320 | new UI6, six rows, i/W 2/6 | same compact chrome; existing 4x6 Fixed/Terminal |
| 640 | corrected XTC, eight rows, i/W 4/9 | existing HPXY 16x8 buttons, 12x8 arrows, 8/12 thumbs; original 8-pixel fixed faces |

HPXY retains its accepted driver bytes and existing compact chrome because
FIXXT DISPLAY validates that identity; its OEM System/companion selection
changes. Explicit CGA320L and 640C choices are retained. CGA100 and its
160x100-view pan keep their established compact path. The private PPCUI and
nonblanking PPC512 variants are not inputs to this producer.

The resource transplant checks all original file-backed segments and fixups,
unbacked data contracts, target aspect/color configuration and palette.
Only OEM bitmaps, UI geometry and default variable-face descriptors change.
Fixed/Terminal **bytes and monospace behavior** remain exact, but low-viewport
OEM selections now use the project's existing 4x6 companions. This matters:
on fixed 160x200 the same small dialog shrank from 218 to 114 pixels wide;
its overflow disappeared. Blindly preserving the old eight-pixel selection
would preserve oversized controls despite a proportional System face.

CHECKPKG.PY checks every one of the 21 staged OEM display entries for real
variable System advances, complete System/Fixed/Terminal groups, exact fixed
font bytes and resource-only driver reconstruction. All eight archive builds
and exact rebuild verification passed. No standalone records are emitted.
Use SYSFONT/PACK.PY --out NEW_PRIVATE_DIRECTORY, then CHECKPKG.PY DIRECTORY.
BUILD320.PY produces the normal native candidate source/payload; compile it
with the existing C6 workflow. Private support inputs are not distributable.

Representative Windows 3.0 real-mode / 8086-prefetch runs used normal 640 KB,
no EMS/XMS/UMB, and the existing lease/watchdog. In addition to both native
320 aliases, wide CGA640 measured System 4/9, menu 9, caption 10, 16x8 caption
buttons and 12x8 scrollbars; Paintbrush Open and DOS return passed.
PCjr JRPAN measured a 640x400 desktop / 320x200 view, System 2/6, caption 8,
menu 7 and six-pixel scrollbars. Its unchanged JRGUARD passed; panning to
(320,200) and restoring to (0,0) succeeded. Fixed Tandy160's unchanged RESERVE
reserved 16 KB and its compact System measured 2/4; Windows returned to DOS.

There are real remaining limits. Fixed 160x200 Paintbrush Open still places
buttons through x=173 on a 160-wide screen, even though the small dialog now
fits. Do not call that profile a complete application-layout pass or shrink
all text indiscriminately to hide it. Panning dialogs are measured against
the logical desktop; their full bounds may require moving the viewport.
The ordinary OEM consumer install paths outside CGA and full fresh-media/
legacy-upgrade acceptance have not been rerun. The dedicated FRESH640 media
producer and full/fixed WINXT producers are not repackaged by this checkpoint.
Video II still needs an actual matching SL/2 fixture. No physical adapter,
scanout timing, snow/flicker or hardware readability qualification is claimed.

A faithful universal proportional TEXT80/TXT40 backend is not supplied.
CGA's ROM text glyphs cannot express arbitrary pixel tiles. Even writable
EGA/VGA text fonts offer a finite simultaneous glyph bank and only two
colors per character cell; arbitrary Windows pixels can exceed both limits.
A cache would have to approximate, reject drawing after startup, or change
modes. None is a transparent faithful same-mode fallback. Existing text
mode defaults remain untouched, not completed or exempt. Next action is
an explicit separate backend/design decision: a bounded writable-font trial
with honest rendering limits, or an explicitly selected graphics backend;
never silently promote a proportional flag on the current cell presenter.
