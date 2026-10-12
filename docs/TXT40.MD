# TXT40: Windows 3.0 in CGA 40x25 colour text, for a TV (experimental)

Status: **TXT40.DRV runs Windows 3.0 real mode on an emulated IBM PC/XT
(8088, 4.77 MHz) with an IBM CGA card in 86Box 6.0, with the whole screen
in BIOS 40x25 colour text. A scripted session passes @@CHECKS@@ checks: menus, a
message box, a dialog, Notepad typing, a window move, the mouse cursor,
exit to DOS and an identical second launch. The same session also ran on
86Box's composite (TV) output. It has not run on real hardware or a real
TV.** Nothing shipped changes: `TXTMODE.DRV` in the WINXT package and its
release are untouched; this is a new driver under a new name.

## Who it is for

A CGA card's composite output was made for a TV. On a TV, 640x200
graphics are unreadable and 320x200 smears into colour fringes; 40-column
text is what a TV shows well, which is why CGA has a 40-column mode.
Windows 3.0 never offered it. TXT40 does: every 8x8 block of a normal
320x200 16-colour Windows screen becomes one character cell, with a
foreground and a background colour (blink is turned off, so all 16
background colours work).

## How it works

TXT40 is the accepted TR5 renderer for 320x200x16 (the Tandy profile built
by `src/tandysw/BUILD88.PY`), unchanged, plus a new presenter. Windows
draws into TR5's private shadow as before. Where TR5 would convert the
shadow to Tandy video memory, TXT40 turns each dirty 8x8 block into a text
cell at B800h:

- **Text is shown as text.** When Windows draws a string on the screen in
  an 8x8 raster font, the driver records a *hint* for each 8-pixel glyph:
  its exact position, its 8 bitmap rows and the CP437 code to show (ANSI is
  mapped to CP437; OEM fonts pass through). A hint is shown only while the
  pixels still hold exactly that glyph in two colours, so text that is
  overpainted, scrolled away or partly covered falls back to the
  approximation instead of lying. Text is shown in its own colours, at the
  cell holding the glyph's centre, so text that is not aligned to the
  8-pixel grid (most of it is not) still lands in one cell per character.
  If that strict check fails, a second check of rows 1-6 only lets a
  focused button's label through its dotted focus rectangle.
- **Everything else is approximated:** blank cells, full and half blocks,
  light and medium shades, and single-line box drawing for frames, menus
  and window borders, in the cell's two most common colours.
- **Menus and dialogs that close** restore their pixels; each cell keeps
  its two newest hints, so the text that was under a menu comes back as
  text. **Window moves and scrolling** (screen-to-screen copies) move the
  hints with the pixels.
- **The mouse cursor** is the cell under the hot spot, with its attribute
  XOR 77h. The hardware cursor is hidden.
- **Mode:** BIOS mode 01h, then port 3D8h = 08h and BIOS 40:65h = 08h
  (blink off). Leaving Windows restores the previous mode as TR5 does.

The presenter does real work per cell, which is the cost of this driver on
an 8088 (see "Speed").

### Fonts

Text is only recognized in 8-pixel-high fonts whose glyphs are 8 pixels
wide: the repository's first-party 8x8 XT fonts (`XTTSYS.FON`,
`XTCFIX.FON`, `XTCOEM.FON`, as in the WINXT package). Windows 3.0 dialogs
ask for the proportional "Helv" font; with Helv installed, dialog text is
proportional and shows only as approximation. The TV setup therefore
comments out every `[fonts]` entry in WIN.INI, so the font mapper can only
pick the 8x8 System and Terminal fonts. Dialogs then use the 8x8 System
font (readable, but wider, so wide dialogs are cut off at the right edge
of a 320-pixel screen, as they already are at 320x200).

## The specification and its tests (no emulator needed for the spec)

`src/txt40/T40MODEL.PY` is the specification of the presenter in Python:
hint bookkeeping, glyph verification, the approximation, which cells a
flush rewrites, and how hints follow screen-to-screen copies.
`src/txt40/T40PRES.ASM` (8086, MASM 5.1) is the driver's presenter, and
the driver build inserts it verbatim.

- `T40TEST.PY` assembles the same `T40PRES.ASM` into a DOS program and
  runs it under DOSBox-X (8086 prefetch core) on @@FLUSHES@@ flushes: seeded
  synthetic screens (rectangles, lines, dither, text at every alignment and
  at the screen edges, opaque, transparent and underlined, every pixel
  density, every box junction, focus rectangles, overpainting, moves, and
  single-pixel nicks next to glyphs), plus decoded reference screenshots
  when given. Every text buffer must equal the model's, byte for byte,
  and every full flush must equal the model's from-scratch answer. The
  scenes must also flush every pixel they change, as the driver does.
  Result: `txt40/T40TEST.JSN` (PASS).
- `T40MUT.PY` makes @@MUTANTS@@ one-line changes to `T40PRES.ASM` (thresholds,
  tie-breaks, edges, margins, the stale and touch rules, slot handling, the
  second check, the blit order) and requires `T40TEST.PY` to fail on every
  one. Result: `txt40/T40MUT.JSN` (@@MUTANTS@@/@@MUTANTS@@ caught). Changes that make the
  presenter re-verify more cells are not listed: with every pixel change
  flushed they cannot change the result.

## Building

`src/txt40/BUILDT40.PY` runs the view's own `src/tandysw/BUILD88.PY` for
profile 320x200x16 unchanged, except that after BUILD88 has staged and
ported every source, `T40PATCH.PY` edits the staged `TSOFT.ASM`,
`TCURSOR.ASM` and `TSOFT.DEF` (each edit must match an exact count).
BUILD88's instruction, REP-prefix and link audits then run on the patched
listings. The edits:

- Enable: mode 01h, blink off, hardware cursor hidden, text and hints
  cleared. Disable: unchanged.
- The four flush routines become one text-cell flush; the cursor-retaining
  variants become plain flushes.
- StrBlt/ExtTextOut on the screen record hints (8x8 raster fonts, no
  justification or character extra). Text flushes are bounded by the text
  rows and the clip/opaque rectangle columns, using screen-clamped copies
  of those rectangles, because a window wider than the screen otherwise
  forces a full-screen flush (cheap for TR5, seconds here).
- Screen-to-screen SRCCOPY BitBlt moves the hints wholly inside the source.
- New segment `_T40` (34KB hint table and presenter state).
- Cursor: the cell cursor above.

Result: `txt40/T40BUILD.JSN`, TXT40.DRV @@DRVBYTES@@ bytes, SHA-256
`@@DRVSHA@@`. `src/txt40/T40ID.ASM` (built with
`src/pcjr/BUILDCOM.PY`, `txt40/T40IDB.JSN`) checks for a colour CGA-class
text adapter and reports the BIOS mode, for use at the DOS prompt before
and after Windows.

## Windows 3.0 in 86Box (@@DATE@@)

### Setup

Same emulator, ROM set, machine, disk image and serial mouse as the
Plantronics work ([PCP.MD](PCP.MD), "Setup"; `pcp/P86ROMS.TXT`), with
`gfxcard = cga` (86Box "IBM CGA", snow emulation on, its default) instead
of the ColorPlus. `PCP86.PY prepare --target txt40 --fonts
distributions/WINXT --grid 1 --only-8x8` installs `display.drv=TXT40.DRV`,
the three 8x8 fonts (hashes checked), `GridGranularity=1` and the empty
`[fonts]` list, plus the usual XT changes (`txt40/T40PREP.JSN`). `--tv`
selects 86Box's composite output (`display_type = 1`).

Screens are read back from 86Box screenshots: `SHOTDEC.PY` decodes them to
exact 320x200 pixels (any off-palette sample fails), then
`src/txt40/T40SHOT.PY` reads every cell against the CGA character ROM's
8x8 font (86Box `roms/video/mda/mda.rom` at offset 1800h, SHA-256 of the
ROM file in `pcp/P86ROMS.TXT`; not in this repository) and reports the
printable characters. Composite captures cannot be decoded; they are
pictures only.

### The session and its checks

`src/txt40/T40WIN.PY` drives Windows through xdotool and the serial mouse.
Before each check it waits until two captures in a row are identical and
the expected text is on screen. Result: `txt40/T40WIN.JSN`, decoded
screens as text in `txt40/*.TXT`.

| Step | Check | Result |
| --- | --- | --- |
@@TABLE@@

### Speed

`T40TEST.PY --bench` builds the presenter into a DOS program that times
flushes of a desktop-like screen (wallpaper bars, a window, a menu bar,
15 lines of text) with the BIOS clock. Run on the emulated 4.77 MHz 8088
(`txt40/T40BENCH.JSN`), its text output equals the DOSBox-X run:

| Flush | Time on the emulated XT |
| --- | --- |
@@SPEED@@

During the session, typing the 22 characters of the Notepad line took
about @@TYPING@@ s until all of them were on screen. That is slow but usable, and much
slower than TR5 on the same machine, which only copies bytes.

### On a TV (composite)

@@TV@@

### Passed in 86Box / still needs real hardware

| Passed in 86Box 6.0 (emulated IBM XT + IBM CGA) | Still needs real hardware |
| --- | --- |
| Driver loads; Windows 3.0 /R starts, runs, exits to DOS (mode 03h, 80 columns restored) and restarts identically | A real IBM CGA and clones, whose handling of 3D8h bit 5 (blink) and 40-column timing may differ; PCjr and Tandy video are not CGA and are not targets |
| Text recognized in menus, a message box (focused OK), the Run dialog, Notepad, the exit dialog | A real TV over composite (and RF modulators): legibility of 40-column text, colours, overscan cutting off the edge cells |
| Menus close back to the identical screen; a moved window keeps its text | Real 8088 and V20 speed; CGA snow does not apply to 40-column text, but needs a look |
| Mouse cursor is exactly the hot-spot cell, XOR 77h | Other mice, keyboards, BIOS variants, DOS versions |
| Presenter equals the specification on @@FLUSHES@@ flushes; @@MUTANTS@@ mutants caught | A clean CGA install (CGA grabber and fonts instead of the EGA ones reused here), DOS boxes |

### Limits

- Pictures, icons and anything that is not 8x8 text become blocks and
  shades: recognizable shapes at best.
- Text in other fonts (proportional, larger, vector) is approximated.
  The empty `[fonts]` setup avoids that in Windows' own dialogs, not in
  applications that ask for specific fonts.
- Text drawn into memory bitmaps and copied to the screen (some
  applications, disabled "grey" text via GrayString) carries no hint.
- At 320x200, many windows and dialogs are wider than the screen.
- A full-screen redraw takes seconds on a 4.77 MHz 8088.

### Reproducing

    # tools: Xvfb, xdotool, mtools, Python 3 + Pillow; the pinned DOS
    # toolchain (tools/BUILDDEPS) and DOSBox-X for the DOS builds
    python3 src/txt40/T40MODEL.PY --check
    python3 src/txt40/T40PATCH.PY --check
    python3 src/txt40/T40TEST.PY --deps <inputs> --dosbox <dosbox-x> --out <dir> --scenes 12
    python3 src/txt40/T40MUT.PY --deps <inputs> --dosbox <dosbox-x> --out <dir>
    python3 src/txt40/BUILDT40.PY --repo <DEPS.PY display view> --dosbox <dosbox-x> --out <dir>
    python3 src/pcjr/BUILDCOM.PY --deps <inputs> --dosbox <dosbox-x> --out <dir> \
        --src src/txt40/T40ID.ASM --src src/pcp/MSTEST.ASM
    # 86Box, ROMs and the disk image as in PCP.MD; CGA font from mda.rom:
    python3 -c "d=open('<roms>/video/mda/mda.rom','rb').read(); open('CGA8.BIN','wb').write(d[0x1800:0x2000])"
    python3 src/pcp/PCP86.PY prepare --vm <new dir> --pristine <private.img> --target txt40 \
        --drv TXT40.DRV --drv-sha <sha256> --tools <dir with T40ID.COM MSTEST.COM> \
        --mouse pty --fonts distributions/WINXT --grid 1 --only-8x8 [--tv]
    python3 src/pcp/PCPMOUSE.PY serve --vm <dir> &
    python3 src/pcp/PCP86.PY start --vm <dir> --box <86Box AppRun> --roms <rom dir>
    sleep 75   # XT POST and DOS boot
    python3 src/txt40/T40WIN.PY --vm <dir> --font CGA8.BIN [--tv]
    python3 src/pcp/PCP86.PY stop --vm <dir>
    # speed: copy <bench dir>/T40TEST.EXE and OPS.BIN to C:\T40, run T40TEST
    # there, copy TIME.BIN back (BIOS ticks per BENCH entry in T40TEST.PY)
    python3 src/txt40/T40TEST.PY --deps <inputs> --dosbox <dosbox-x> --out <bench dir> --bench

## Files

| File | Purpose |
| --- | --- |
| `src/txt40/T40MODEL.PY` | Specification of the presenter; previews from reference frames |
| `src/txt40/T40PRES.ASM`, `T40DATA.ASM` | The presenter and its state, inserted verbatim into the driver and the test program |
| `src/txt40/T40TEST.PY`, `T40MUT.PY` | Presenter against the specification under DOSBox-X; mutation check; XT bench |
| `src/txt40/T40PATCH.PY`, `BUILDT40.PY` | Driver edits and build on BUILD88 |
| `src/txt40/T40ID.ASM` | DOS check for a colour text adapter and the BIOS mode |
| `src/txt40/T40SHOT.PY`, `T40WIN.PY` | Screenshot to text; the scripted 86Box session |
| `src/txt40/FNTREAD.PY` | 8x8 glyphs from a .FON (tests and previews) |
| `src/pcp/PCP86.PY` | Shared 86Box harness: `--target txt40`, `--fonts`, `--grid`, `--only-8x8`, `--tv` |
| `docs/txt40/` | Evidence named above |

## Next steps

1. **Real hardware and a real TV.** `T40ID` at the DOS prompt, then
   Windows with `display.drv=TXT40.DRV` and the 8x8 fonts, on a CGA card's
   composite output.
2. **Speed.** Full-screen redraws are the slow case; caching each cell's
   last inputs would skip unchanged cells.
3. **Setup integration** under its own 8.3 names, without changing the
   WINXT package's existing choices.
