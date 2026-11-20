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

## Accepted unchanged text modes

Chad accepted the fixed-cell limitation and removed text backend redesign
from this assignment. TEXT80/TXT40 and their defaults remain untouched.
All real graphics modes remain in scope. No SVGA/VESA work is included.

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

TEXT80/TXT40 stay unchanged by Chad's explicit acceptance. Their renderer
redesign is no longer planned work. Fixed 160-pixel application-dialog
clipping remains a separate graphics limitation, not a reason to shrink
all text. Video II and physical hardware qualification remain separate.

## Production package checkpoint

The exact live WXTF1107.ZIP was downloaded read-only and equals the current
FONTPACK/BIN/WINXT.ZIP byte for byte (1,201,728 bytes; root SETUP.EXE 95,716,
FIXXT.EXE 53,814). Its actual graphics are fixed TANDY88/TNDY160/TNDY3204/
TNDY6402/TNDY6404 plus HPXY. Its fixed-new-install, explicit HPXY and update
preservation behavior already exists. No #217 generator was imported.

The original CGA and full Tandy inputs contain a byte-identical original
Windows CGA.GR2. New candidates exclude it. Ordinary OEM descriptors use
original Windows Disk 3 via the standard `3:CGA.GR2` field. OWNMEDIA.PY also
removes obsolete presence/copy lines from existing convenience scripts.
Native CGA keeps its current checked copy/cleanup contract: it obtains the
owner's installed SYSTEM\CGA.GR2 (or existing CGAGRAB alias) and creates its
private alias locally. No new guest checksum or version machinery is added.
The new compiler input headers serve the existing launchers; no standalone
source, checksum, provenance or testing records are produced.

Actual production-route evidence:

- SFCGA: ordinary Windows Setup, Other, normal 320 entry selected CGA32C,
  UI6 and existing 4x6 companions. Boot uses the owner's CGA.GR2. Cold start,
  Paintbrush, Open buttons and clean DOS return passed; System i/W = 2/6.
- SFTANDY: ordinary Setup selected fixed TANDY88, UI6 and 4x6 companions.
  The unchanged DISPWIN executed reservation, grabber and PAN preparation,
  started real-mode Windows, and returned to DOS. Important Open buttons fit.
- The same SFTANDY source then selected explicit HPXY through ordinary Setup.
  DISPWIN passed again. System i/W = 2/6; logical 640x256 / physical 320x200;
  panning to (320,56) and restoration to (0,0) passed. HPXY driver identity
  and the launcher/guard binaries remain unchanged.
- Rebuilt native CGA normal 320 installed with no grabber in its source ZIP,
  copied only the owner's known original, cold-started and returned to DOS.
  Its existing UNDO restored original boot selections, removed its owned
  grabber alias and preserved the original SYSTEM\CGA.GR2 byte for byte.
- The rebuilt fresh launcher passed its real /CHECK against original media
  and the new closed kit. Actual original fresh Setup recognized the OEM
  choice and copied the exact revised CGA640, XTC fonts and owner's CGA.GR2.
  Complete fresh Setup / first ordinary cold start is NOT yet accepted;
  bounded automation stalled across alternating project/Microsoft disk paths.
  These attempts are not passes or a diagnosed display-driver failure.

Release URLs retain this prefix:
https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/

| Asset names at that prefix | Current candidate status |
| --- | --- |
| SFCGA.ZIP | Independently ordinary-install/cold-start qualified in emulation |
| SFTANDY.ZIP | Independently ordinary-install/guarded-start qualified for fixed 320 and explicit HPXY in emulation |
| CGA.ZIP, CGASRC.ZIP | Project-only paired candidates built; native normal/restore and fresh input/OEM-copy checks pass; fresh completion still held |
| WXTF1107.ZIP | Full desktop replacement blocked by existing compiled preparation/finisher bindings, not interchangeable with SFTANDY |
| SFPCJR.ZIP, SFPCP.ZIP; JRPAN.ZIP, CPPAN.ZIP, PAN.ZIP | Existing universal panning updater binding blocks revised resource-derived drivers |
| SF1512.ZIP; PC1512.ZIP | Matching driver base confirmed; metadata/shared-wide-UI checks only for new candidates; ordinary install not independently repeated |
| SFTGA2.ZIP, SFPC1.ZIP, SFYAMA.ZIP; TNDYV2.ZIP, PC1.ZIP, YAMAHA.ZIP | OEM candidates machine-checked; independent adapter install/start not repeated; Video II still has no matching SL/2 fixture |
| WINXT720.ZIP | Separate FAT12 data-image producer and installer; not rebuilt or qualified here |
| TANDYLAB.ZIP | Curated optional display subtree depends on the full/core producer; app collection not rewritten here |
| WINXT.ZIP, WINXTSRC.ZIP, WINXT.JSN, WINXT.SHA; WXT61107.ZIP | Preserved historical/core download identities, not a substitute for current WXTF1107 |

PC1512's live/local ZIP drift is INSTALL.TXT only; the display binary agrees
exactly. No unrelated app asset was modified, including MINESET/COOKSET.
TEXT80/TXT40 and SVGA/VESA remain outside this work.

The production blockers were observed, not inferred only from metadata:

1. Overlaying graphics candidates into a private copy of the actual full
   WXTF1107 packet makes ordinary SETUP UPDATE /PREP stop before changes:
   first `Required regular file is missing: ...\CGA.GR2`. Supplying the
   owner's original only inside that private fixture progresses to
   `File larger than release pin: ...\OEMSETUP.INF`. Windows selections
   remain untouched. Its finisher also still declares the former fixed
   driver sizes and XTESYS/XTC profile font matrix; UI6/CG1 companions are
   not wired into its full fresh/update ownership contract. Next work must
   adapt the existing full producer's OS-input rule, payload bindings and
   font selection, then qualify real UPDATE/FRESH and MODEXT transitions.
   It must preserve guards and custom data, not introduce another updater.
2. The unchanged PCjr PANINST executed with the candidate driver says
   `STOP: Panning driver source damaged`. The source PANSETUP.C validates
   its compiled current/old driver identities, and its launcher is shared
   with ColorPlus and standalone PAN. The current contract cannot merely
   be ignored or replaced by an unchecked copy. Existing transition/binding
   handling needs a separate controlled update and qualification.
3. The current catalog's closed CGAFRESH/core acceptance still describes
   the former archives; no historical receipt or source pin was relaxed.

SYSFONT/PACK.ready is a host-only fail-closed publication check for the
observed unchanged panning-launcher mismatch. Automatic eight-asset upload
now stops before any release mutation. It does not add guest validation.
The earlier main-push workflow publishes all eight SF assets, so use only
explicit independently qualified replacements until the blockers close.

Final ZIP audits compared every entry with the owner's original Windows
media: no exact original OS file remains. No OS disk, compiler/DDK, private
guest tree, or unrequested JSN/JSON/SHA/SUM file is included. Original project
and DDK-derived project components retain their existing component notices;
this is not a claim that the project drivers contain no adapted DDK code.
All final runtime/font/OEM/launcher bytes in the qualified SFCGA/SFTANDY ZIPs
match the actually installed candidates; differences are instructional text.
Normal 640 KB / 8086-prefetch emulator evidence is not physical hardware,
scanout, flicker, bus timing or complete application qualification.
