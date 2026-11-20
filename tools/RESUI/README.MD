# Resolution-aware Windows UI checkpoint

This feature branch starts the all-profile UI correction. It does not declare
all graphics adapters, text presenters or released packages finished. PPCUI's
separate PPC512 six-row tester and every accepted graphics module remain intact.

The ordinary CGA `320` argument now selects **CGA32C.DRV + CG1SYS.FON**.
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

## Findings and verified 320 slice

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

Next: carry viewport-based System/chrome choices through each graphics
producer, preserve guards/palettes/timing and explicit fixed-font roles,
verify representative low/wide/panning families, and check every package's
selected System/font/OEM mapping. Legacy installed-package upgrade, full
fresh-media production acceptance and non-CGA runtime coverage remain open.

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
