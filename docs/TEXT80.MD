# TEXT80: Windows 3.0 in 80-column text mode (experimental)

Branch `ai/text80` (TXT40 + XTPAN merged in), draft PR. Nothing here
changes a released driver, an installer default, a package, a pin or a
release hash. A rebuild is not runtime acceptance: everything below was
run in emulators, none of it on real hardware yet.

@@VERDICT@@

## 1. Profiles

| Profile | Driver | Text on screen | Glyph cell | Windows sees | Pixel aspect GDI is told | Adapters | Minimum hardware |
|---|---|---|---|---|---|---|---|
| TXT40 (existing, fixed here) | `TXT40.DRV` | 40x25 | 8x8 | 320x200 | as TR5 320x200 | CGA-compatible colour | 8088, CGA, 640 KB |
| **TEXT80 25** | `TEXT80.DRV` | 80x25 | 8x8 (BIOS font of the card: 8x8 CGA, 8x9 Tandy, 8x14 EGA, 8x16 VGA) | 640x200 | 96x48 (the CGA resolution resources) | CGA, Tandy 1000/PCjr-class, EGA, VGA in their colour 80x25 mode | 8088, any of those, 640 KB |
| **TEXT80 PAN** | `T80PAN.DRV` + `XTPAN.EXE` | 80x25 window over 80x50 logical rows | as above | 640x400 | 96x48 | as above | 8088, 640 KB (130 KB more Windows memory than 25) |
| **TEXT80 VGA** | `T80VGA.DRV` | 80x50 | 8x8 (INT 10h AX=1112h ROM font, 400 scan lines) | 640x400 | 96x48 | VGA only (checked) | 8088 with an 8-bit VGA card, 640 KB |

Physical text cells versus logical pixels: Windows always draws 8x8
logical pixels per text cell. How tall a cell looks is the adapter's
business (8x9 on a Tandy 1000 HX in 80 columns, 8x16 on VGA 80x25). The
logical pixel aspect told to GDI is the CGA resolution set's 96x48, so the
system font and the added 8x8 faces are chosen; circles drawn by programs
are taller than wide on every profile.

Capability checks in Enable (no assumptions):
- 25 and PAN: BIOS mode 03h; CGA-compatible mode register 3D8h = 09h
  (blink off) and BIOS 40:65h; on EGA/VGA (INT 10h AH=12h BL=10h answers)
  blink off with INT 10h AX=1003h. The Tandy 1000 EX/HX and PCjr-class
  video run 80x25 colour through the BIOS like a CGA. Real IBM CGA shows
  snow in 80 columns when video memory is written during the display (the
  presenter writes only the cells that change; it does not wait for
  retrace).
- VGA: INT 10h AX=1A00h must return AL=1Ah and display combination 7 or 8
  (VGA mono/colour), checked before the mode is touched; then mode 03h,
  INT 10h AX=1112h (8x8 font), and the BIOS must report 50 rows (40:84h =
  49), else mode 03h is restored, the shadow freed and Enable returns 0.
  UEFI machines without a legacy video BIOS cannot run real-mode Windows
  3.0 anyway; VGA text through a CSM is the same INT 10h path and has not
  been tried.

## 2. Where Notepad's 3-second keystroke went (TXT40), and the fixes

All figures: 86Box 6.0 b9001, IBM XT (`ibmxt86`), 8088 at 4.77 MHz,
IBM CGA (snow on), 640 KB, XTIDE, `time_sync=disabled`; PC DOS 3.20 and
Windows 3.0 started with `WIN /R`. `TPROF.EXE` (first-party, built here)
types into a visible edit control with `WM_CHAR` messages and times each
character from the message to the end of the paint (`GetCurrentTime`,
55 ms resolution, so per-character figures are averages over 30).

**Correction.** Until commit b3870c0, `TPROF TYPE` created its window
hidden (`CW_USEDEFAULT` for x with y = 0 means `SW_HIDE`), so the early
TYPE numbers in `docs/text80/PROF1` and `STOCK0` (1464 ms, later 110 ms
per character) measured drawing that never reached the screen. Every
number below is from the visible window.

Where the time went in stock TXT40 (profiling build, `PROF1`/`BASEPROF1`,
ExtTextOut trace and per-flush timers in `T80PROF.PY`):
1. Each keystroke in an edit control or Notepad causes an opaque
   ExtTextOut of the line, the caret twice, and an opaque-only
   ExtTextOut. The text flush's rectangle was the union of the clip and
   opaque rectangles: in Notepad that is the whole client area, about
   170 cells per keystroke at ~3 ms of glyph matching each (2.6 s).
2. Every flush also re-verified and re-wrote one cell of margin around
   every dirty cell whether or not anything there changed.
3. Dialog labels asked for bold Helv; with only a normal-weight 8x8 Helv,
   GDI drew each label twice one pixel apart (simulated bold), so no
   glyph matched and labels came out as block approximations.

Fixes (each specified in `T40MODEL.PY` first, property-checked, then
assembled and checked against the model in DOSBox-X by `T40TEST.PY`):
- text flush rows come from the text bounds, columns from the text's own
  extent (x to the end `t40_text` walked, +1 for simulated bold), widened
  only by a filled opaque rectangle and always intersected with the clip;
- tight output range: a flush writes the dirty cells, the cells whose
  shown state actually changed in its verify pass (or were stale) and
  their neighbours, nothing else (a cell's text depends only on its own
  pixels and the hints shown in its 3x3 neighbourhood);
- snapshot-diff flushes for rectangles GDI cannot bound;
- whole-cell copies: a screen-to-screen BitBlt by a whole number of
  cells (Notepad scrolling, windows moved on the 8-pixel grid) moves the
  interior cells' text, hints and state instead of matching them again;
  hint moves visit only cells that can hold a moved hint;
- `T80HELV.FON` bold and variable pitch (section 7).

Typing, `TPROF TYPE 30`, ms per character, visible edit control:

| Driver | Build | ms/char | Change |
|---|---|---|---|
| Stock TXT40 (`fb9622ab`) | release | **3,166** | baseline |
| TXT40 with this branch's fixes | release-style | **286** | 11x faster |
| TEXT80 25 | release-style | **245** | |
| TEXT80 PAN | release-style | 265 | |
| TEXT80 25 on a Tandy 1000 HX (7.16 MHz) | release-style | 152 | |
| TXT40 fixed | profiling | 370 | |
| TEXT80 25 | profiling | 328 | |

TEXT80 25 per character (profiling build, readings 16 onwards): Windows
and the edit control 138 ms, rendering into the shadow 27 ms, flushes
162 ms (verify 21, glyph matching 47, cell writes 38, compares 27, caret
and the rest 29), 13.8 cells written. The remaining cost is spread out;
no single step dominates any more.

Scrolling (`TPROF LINES 30`: a line typed, Enter, the edit control scrolls
by one line; ms per line once it scrolls):

| Driver | Build | ms/line |
|---|---|---|
| TXT40 fixed (40x25), b6 | release-style | 3,266 |
| TEXT80 25 before whole-cell copies (b5) | profiling | 6,400 |
| TEXT80 25 with whole-cell copies (b6) | release-style / profiling | 3,466 / 5,284 |
| TEXT80 25, hint moves bounded (b7, final) | release-style / profiling | **2,686** / 4,115 |
| TEXT80 PAN (b7, final) | release-style | 2,792 |
| TEXT80 25 on a Tandy 1000 HX, 7.16 MHz (b7) | release-style | 1,657 |

A scroll still costs about 2.7 s per line on a 4.77 MHz 8088. Per
scrolled line (profiling build b7): Notepad and GDI 0.44 s, drawing and
the BitBlt in the shadow 0.46 s (1.63 s before hint moves were bounded),
flushes 3.2 s. The largest flush is the scrolled area itself, 1.6 s:
Notepad's lines sit 3 pixels below the cell grid (y = 67), so of the 10
cell rows the top three and bottom three (the partly copied row, its
neighbour and the extra layer) are matched again and only the middle is
moved; the new line costs another 0.5 s. The edit control also redraws
about twenty fully clipped lines; each costs under 1 ms.

## 3. Memory

| Profile | Driver data segments | Shadow | Free (GetFreeSpace before Notepad) |
|---|---|---|---|
| Stock TXT40 | `_T40` 18,621 | 32,000 static | 263,264 |
| TXT40 fixed | as above | 32,000 static | 268,224 |
| TEXT80 25 | `_T40` 28,621 | 64,000 static | 207,776 |
| TEXT80 PAN | `_T40` 48,621 + `_T80L` 8,000 | 129,536 GlobalAlloc | 105,440 (b7 session, with `XTPAN.EXE` running; 122,240 in b6) |
| TEXT80 VGA (DOSBox-X) | as PAN, without `_T80L` | 129,536 GlobalAlloc | 121,792 |

The 640x400 shadow is 4 bits per pixel, 128,000 bytes: more than a
segment. T80TALL makes it a huge block of two 200-row bands of 64,000
bytes each (+ 1,536 bytes of fill so the second band starts on a segment
boundary): `bmSegmentIndex` = `__NEXTSEG`, `bmScanSegment` = 200,
`bmFillBytes` = 1,536, so GDI's own bitmap code walks the bands, and the
presenter addresses rows through `t40_rowes` (band 0 / band 1 selector).

Enable asks `GlobalAlloc(GMEM_FIXED, 129536)` once per Enable/Disable
pair, locks it and clears both bands. On failure it returns 0 before
touching the screen mode, and Windows 3.0 quietly returns to DOS; the DOS prompt is usable and T80OFF restores
the previous driver. Disable frees the block. Fault injection
(`t80panfail`: the same driver asking for 7FA00h bytes) proved this in
86Box: Windows refused to start, the DOS prompt wrote a file, T80OFF
rolled back and Windows started with the previous driver
(`docs/text80/ALLOCFAIL`). Leaving Windows and starting it again (every
session does it) gives a desktop identical cell for cell.

## 4. Panning (PAN profile)

T80PAN.DRV reuses the XTPAN design unchanged: a 640x400 desktop, a
25-row window onto it, and the same task-time helper `XTPAN.EXE` (from
PR #132, unmodified) that watches the active window and keys Alt+PgDn /
Alt+PgUp / F9 and asks the driver for a new top with escape 5850h. The
pan itself runs only from that escape, at task time, never in the mouse
interrupt; the pointer interrupt only records where the pointer is.

Cell alignment: a text screen can only start at a whole text row, so the
driver rounds the requested top: when moving down it rounds **up** to a
multiple of 8, when moving up it rounds **down**, which never pushes the
window's far edge out of view. `T80PANT.PY` checks this over every window
position, height and starting top on the 400-row desktop:
- the review regression: a 190-row window at rows 30..220 seen from top
  0 gets top 20 from XTPAN's rule and **24** from the text driver, and
  rows 30..219 are all shown;
- every window up to 193 rows tall ends wholly visible from every
  starting top (the rounding costs up to 7 rows of the 200);
- 194..200-row windows can lose up to 7 rows at some positions
  (counted, documented, not a failure);
- negative controls (round to nearest, always down, always up) fail.

A pan copies 25 rows of 80 cells (4,000 bytes) from the logical text
buffer into video memory. `XTPAN.LOG` timestamps put every pan at 0-55 ms
(below `GetCurrentTime`'s resolution) on the 4.77 MHz XT, against about
1.05 s per pan for the XTPAN graphics desktop on the Tandy 1000 HX
(docs/PAN.MD), because text mode moves 4,000 bytes instead of re-drawing
a 16 KB graphics page. Off-screen drawing goes into the shadow and the
logical text buffer and appears exactly when panned to.

Final PAN session (b7, 86Box XT/CGA, 23/23): Alt+PgDn moves to top 56
and screen rows 0-17 are exactly rows 7-24 seen before; Alt+PgUp
restores every cell; repeated Alt+PgDn continues row for row and stops
at top 200; the pointer below row 200 is exactly one cell; Alt+F9 goes
home; the Run dialog is shown whole after a follow pan; a line typed
into Notepad while scrolled out of view appears, exact, when panned to;
21 helper pans logged at 0 or 55 ms each; relaunch identical; T80OFF
removes `XTPAN.EXE` from `load=` again and the previous driver starts.

## 5. VGA 80x50

T80VGA.DRV shows the whole 640x400 desktop at once as 80x50 text with
the VGA ROM's 8x8 font (no panning, same presenter and shadow as PAN).

**What is not measured:** the VGA ROM image needed for an 86Box VGA
machine was not available here (fetching it from the 86Box ROM set was
refused by this environment's policy, and no copy is in the repository),
so VGA ran only in DOSBox-X 2024.03.01 (`machine=vgaonly`, `cputype=8086`,
`core=normal`, `cycles=max`, 640 KB, serial mouse on COM1, the same PC DOS
3.20 + Windows 3.0 disk booted with `imgmount` + `boot`). DOSBox-X does
not time an 8088, so the VGA results are functional only; expect the
same per-cell costs as TEXT80 PAN on real hardware. The mode-set and
detection code is the same INT 10h path a real VGA BIOS answers.
Final VGA session (b7, 34/34): the BIOS reports 80 columns and 50 rows;
desktop, File menu (every cell restored on close), Run dialog, the
pointer as one exact cell, Notepad typing and its colours, selection,
scrolling, overlapping windows, relaunch identical, T80OFF and the
previous driver starting again. The TYPE/LINES times it records (2 and
18 ms) are DOSBox-X at full host speed and mean nothing for an 8088.

## 6. Tests and evidence

Three layers, each with deliberately broken cases that must fail.

**Presenter against its specification** (`src/txt40`, DOSBox-X runs the
real assembled presenter in a DOS harness, no Windows):
- `T40MODEL.PY` is the executable specification. Its own property checks
  (300 overlapping glyphs at any alignment; 60 unaligned rectangles and
  120 aligned copies moved by whole cells) keep every cell equal to the
  ideal text; negative controls (a broken neighbour rule, no extra ring
  layer) fail them.
- `T40TEST.PY` replays random scenes, explicit regressions and pans
  through the assembled presenter and compares every flush and every
  video-memory dump (`VIDEO.BIN`) with the model, at 40x25, 80x25,
  80x25 with the glyph dictionary limited to 64, 80x50 banded, and
  80x25 panned over 80x50. Explicit regressions with exact expected
  cells: same-position overwrite of a hint, second hint slot restored,
  stale hint after partial overpaint and partial flush, diff flushes
  (half rows, mismatched rows), overlapping BitBlt, hint windows touched
  only at their first/last column, aligned copies (attributes copied,
  flush wider than the destination), pans. Exit codes separate "a
  difference was found" (1) from build/tool (3) and harness (4) failures.
- `T40MUT.PY` assembles each mutant and runs T40TEST on it. A mutant
  counts as caught only when a completed comparison failed; a mutant
  that fails to assemble or run is "invalid" and fails the whole check;
  the unmutated presenter must pass and an unassemblable control must
  come back invalid. One mutant was removed as equivalent (attribute
  change on a kept hint; reasoning in the file). @@B7MUT@@

**Pan rule**: `T80PANT.PY` (section 4).

**Windows in 86Box** (`T80WIN.PY`; screens are read exactly: `T80SNAP.EXE`
copies the 80-column text buffer, attributes, pointer position and BIOS
mode to `C:\T80\SNAPS.BIN` whenever Scroll Lock is pressed, so every check
is on exact cells, not on pictures). The 80x25 session checks: T80ON's
INI edits; desktop text; the pointer is exactly one cell (attribute XOR
77h) at its hot spot, at two positions; File menu text and every cell
restored on close; Run dialog; Notepad typing (exact text and colours of
the typed line); selection by mouse drag and its removal; Edit menu;
scrolling 30 lines; dragging a window by whole cells; overlapping
windows brought to front and back; the save-changes dialog; exit and
relaunch identical cell for cell; T80OFF and Windows starting again with
the previous driver; typing and scrolling speed; free memory. The PAN
session adds keyed and helper pans, repeated pans to the bottom and
back, a dialog off-screen, the pointer below row 200; the VGA session
runs the same checks at 80x50.

Results (b6 builds unless stated):

| Session | Machine | Result |
|---|---|---|
| TEXT80 25 | 86Box XT/CGA | **b7: 50/50**. b6: 49/1 (the overlap check looked for the wrong title; fixed) |
| TEXT80 PAN | 86Box XT/CGA | **b7: 23/23**. b6 stopped after 10 passes on a harness limit (pointer moves past row 199; fixed) |
| TEXT80 VGA | DOSBox-X vgaonly | **b7: 34/34**. b4: 31/4 (all four were wrong expectations in the checks; fixed) |
| Allocation failure (`t80panfail`) | 86Box XT/CGA | Windows does not start; DOS prompt works; T80OFF rollback; Windows starts with the previous driver |
| TEXT80 25 on Tandy 1000 HX | 86Box `tandy1000hx`, 8088 7.16 MHz, internal video, 640 KB | **b7: 49 pass, 1 fail**: after T80OFF, Windows starts with the HX's previous driver (TR53216, a 320x200 graphics mode; the BIOS check passes), but the text-buffer reader cannot see a graphics desktop, so the 'Program Manager' wait fails: a harness limit. 80x25 typing 152 ms/character, scrolling 1,657 ms/line, 173,120 bytes free. b6: never started (the backslash key, section 9) |

Evidence: `docs/text80/<run>/<vm>/` holds each session's `T80WIN.JSN`,
`session.log`, `SNAPS.BIN`, the decoded text of every screen (`*.txt`),
86Box/DOSBox-X configuration, lock records and captures. No disk images,
ROMs or Windows files are included.

## 7. Installing and removing (DOS)

From the folder holding the TEXT80 files, at the DOS prompt (never inside
Windows):

    T80ON [windows folder] [25 | PAN | VGA]      (defaults C:\WINDOWS and 25)
    T80OFF [windows folder]

`T80ON` copies the driver and the 8x8 fonts into the Windows SYSTEM
folder (and, for PAN, `XTPAN.EXE` into the Windows folder), then
`T80SET ON` saves `SYSTEM.INI` and `WIN.INI` byte for byte as
`SYSTEM.T80` and `WIN.T80` and edits the live files:
- `SYSTEM.INI [boot]`: `display.drv=` the chosen driver;
  `fonts.fon=XTTSYS.FON`, `fixedfon.fon=XTCFIX.FON`,
  `oemfonts.fon=XTCOEM.FON` (the first-party 8x8 fonts);
- `WIN.INI [windows] load=`: for PAN, `XTPAN.EXE` is appended; every
  existing entry stays (checked in 86Box with `T80SNAP.EXE` and, on the
  Tandy HX disk, `XTPAN.EXE` already on the line);
- `WIN.INI [fonts]`: two lines are **added**, none removed or commented
  out: `Helv 8x8 (TEXT80)=T80HELV.FON` and
  `Courier 8x8 (TEXT80)=T80COUR.FON`.

`T80ON` refuses if `SYSTEM.T80` already exists. `T80OFF` copies both
backups back over the live files and deletes them, so Windows starts
exactly as before (checked in every 86Box session, including after the
forced allocation failure). The copied driver and fonts stay in SYSTEM,
unused. Everything works from the DOS prompt, so a display driver that
cannot start Windows cannot lock you out.

Why the two added faces: Windows 3.0 dialogs ask for bold "Helv 8"; the
installed `HELVB.FON` strikes are 10 pixels tall and proportional, which
cannot be shown as text cells. `T80HELV.FON` is the 8x8 system-font strike
renamed "Helv", offered as **bold** and **variable pitch** (all glyphs 8
pixels wide): with a normal-weight face GDI simulated bold by drawing each
label twice one pixel apart, and a fixed-pitch face lost to `HELVB.FON`
on the pitch penalty (both seen in 86Box with the ExtTextOut trace before
they were fixed). TXT40's earlier test disks commented out the whole
`[fonts]` list instead; TEXT80 never does.

Application limits: text shows as text only in 8-pixel-high faces (the
system, OEM and fixed fonts and the two added faces). A program that asks
for a bigger face (Write, Paintbrush text, Help titles, Tms Rmn, Helv 10
and up) gets an EGA-resolution strike that is drawn into the shadow
correctly but shown as block and shade approximations. Graphics
(Paintbrush, icons, wallpaper) are always approximations. Help, Write and
Cardfile were not tried.

## 8. Building

Inputs as for TXT40 and XTPAN (`tools/BUILDDEPS/README.MD`: the
commit-pinned DDK/toolchain view; DOSBox-X supplied separately; nothing
is fetched). From the repository root, each variant into a fresh folder:

    python3 src/text80/BUILDT80.PY --repo <display view> --dosbox <dosbox-x> --out <dir> --variant t80
    (variants: t40 t40prof t80 t80prof t80pan t80panprof t80vga t80vgaprof t80panfail)
    python3 src/text80/BUILDAPP.PY --repo <deps> --dosbox <dosbox-x> --out <dir> --app TPROF --app T80SNAP --dos-app T80SET
    python3 src/text80/T80FONT.PY --out <dir>          (T80HELV.FON, T80COUR.FON from the first-party 8x8 font)

Each build runs BUILD88's instruction (8086/8088 only), REP-prefix and
link audits on the edited listings. Host checks:

    python3 src/txt40/T40MODEL.PY
    python3 src/txt40/T40TEST.PY --deps <deps> --dosbox <dosbox-x> --out <dir> --cols 80 [--rows 50 [--vrows 25]] [--glimit 64]
    python3 src/txt40/T40MUT.PY  --deps <deps> --dosbox <dosbox-x> --out <dir> --cols 80 [--rows 50 --vrows 25]
    python3 src/text80/T80PANT.PY

The 86Box sessions need a private PC DOS 3.20 + Windows 3.0 disk image and
86Box ROMs (not in the repository): `T80PREP.PY` prepares a copy of the
image, then `T80WIN.PY --vm <dir> [--profile pan|vga|allocfail]
[--emulator dosbox]` runs a session under `EMULOCK.PY`. Released drivers,
packages, release workflows, pins and hashes are untouched.

## 9. Limits and open questions

- **Scrolling is slow**: about 2.7 s per scrolled line in an edit
  control on a 4.77 MHz 8088 (typing is ~0.25 s per character); see
  section 2 for where it goes. Next steps, in order of payoff: drop hints
  whose pixels a copy overwrote, which makes the extra ring layer
  unnecessary (about a third of the 1.6 s area flush); then a
  text-native scroll that moves video text without matching the edge
  rows again.
- Windows 3.0 wants 640 KB; the Tandy 1000 EX needs its memory expansion.
- Only 8-pixel-high faces become text; anything larger is drawn as block
  approximations (section 7). Graphics are always approximations.
- IBM CGA snows in 80 columns; nothing waits for retrace.
- PAN: windows taller than 193 rows can lose up to 7 rows at some
  positions (cell rounding); pans are whole text rows.
- PAN/VGA use 130 KB more Windows memory than 80x25 (105-122 KB free in a
  640 KB machine before Notepad).
- VGA 80x50 is functional evidence only (DOSBox-X); no speed figure.
- The Tandy 1000 BIOS reads the backslash key's scan code from 86Box as
  Left arrow at the DOS prompt, so the HX session types batch names
  (`GOT80`, `ONPAN`); a real Tandy keyboard does not have this problem.
- `T80ON.BAT`/`T80OFF.BAT` start with `@ECHO OFF`, which PC DOS before
  3.3 does not know: there they print their lines as they run (harmless,
  seen on the PC DOS 3.20 test disk).
- Not tried: Write, Cardfile, Help, Paintbrush, Terminal, EGA cards, real
  PCjr.

## 10. What to test on real hardware

Chad, on the Tandy 1000 EX (and any XT-class CGA or VGA machine you
have), from the DOS prompt in the TEXT80 folder:

1. `T80ON` then `WIN`. Check the desktop and Program Manager are readable
   80-column text, the pointer is one inverted cell, File menu opens and
   closes cleanly.
2. Open Notepad, type a sentence at normal speed: does every letter
   appear, roughly a quarter second each? Type past the bottom to scroll
   and note the seconds per line. Drag-select a word; open the Edit menu.
3. Drag Notepad by its title; overlap it with Program Manager and click
   between them; close Notepad with unsaved text (the save dialog).
4. Exit Windows, run `WIN` again, then `T80OFF` and `WIN`: your previous
   driver must come back, `WIN.INI` `load=` and `[fonts]` as before.
5. PAN: `T80ON C:\WINDOWS PAN`, `WIN`. Alt+PgDn / Alt+PgUp / F9 and
   activating a window low on the desktop should pan almost instantly;
   compare with the XTPAN graphics desktop you already tried.
6. VGA machine only: `T80ON C:\WINDOWS VGA`: 80x50 small text; on a
   non-VGA card Windows must simply return to DOS (then `T80OFF`).
7. Tell me: snow on a real CGA, how the 8x9 Tandy font looks, timings
   from 2, and anything that stays garbled.
