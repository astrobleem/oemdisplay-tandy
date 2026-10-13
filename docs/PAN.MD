# Edge-panning desktop for Windows XT (experimental): investigation

**Summary.** XTPAN.DRV gives Windows 3.0 a 320x400 desktop on the Tandy
1000 EX/HX's 320x200 16-colour screen, panned vertically in 50-row steps
by a small helper (edge dwell, keys, following new windows exactly). In
86Box's Tandy 1000 HX (the EX's sibling; 86Box has no EX) the current
scripted session passes all 33 of its checks: every viewport position
shows the exact logical rows, the pointer's exact shape is drawn where it
clicks, a window that fits is shown whole, and a 275-row dialog's bottom
button, a menu below row 200, overlapping windows, a window dragged across
the boundary, a text selection across it, ScrollWindow copies, repeated
panning and exit/relaunch all work. Costs: **40,416 bytes** of Windows'
free memory (32,320 driver, 8,096 helper; 15% of the 268,448 bytes the
unchanged driver leaves), **about 1.05 s per pan** on the emulated
7.16 MHz 8088. Ordinary drawing costs at most 0.7% more with the
helper off (+0.7% for fills, none for text or scrolling) and 0.6-1.3%
more with it running (fills +1.3%). **Real hardware (2026-10-13): Chad
reports that panning works on his Tandy 1000 EX** (details in section 8).
Recommendation in section 8.

Branch `ai/xt-pan`, separate from every release line. Target: Tandy 1000
EX (8088, 640KB, Windows 3.0 real mode), driver profile 320x200x16
(TANDY88.DRV). Goal: present Windows with a 320x400 logical desktop, show
a 320x200 viewport, pan vertically so that windows and dialog buttons
below row 200 can be reached.

This file starts as the design analysis and grows with the evidence.

## 1. What has to change, and what does not

Sources read: the TR5 renderer as staged by `src/tandysw/BUILD88.PY`
(TSOFT.ASM, TCURSOR.ASM, the DDK renderer modules it links), and the
Windows 3.0 DDK adaptation guide (PCjs mirror of w3ddkadp: GDIINFO,
Enable, the cursor functions, Control/Escape).

**Logical resolution (GDIINFO).** GDI and USER learn the screen size only
from GDIINFO (`dpHorzRes`, `dpVertRes`, sizes in mm and the mapping-mode
extents) and the PDEVICE BITMAP returned by Enable. USER clips the cursor
and windows to that size, and computes window positions, menu placement,
dialog centring and mouse hit testing in it. So these change to 400 rows:
`dpVertRes`, `dpVertSize` (doubled, keeping the pixel aspect), the
MM_LO/HIMETRIC/ENGLISH extents, and `bmHeight` and the per-plane size of
both BITMAP descriptors. Changing GDIINFO alone is not enough: every
drawing path must be able to write 400 rows.

**Drawing and clipping.** TR5 never draws to video memory. Every DDK
renderer module draws into the private four-plane shadow through the
device BITMAP (`bmHeight`, `bmWidthBytes`, `bmWidthPlanes`), and GDI clips
to the device size. A 400-row shadow is 400 x 4 x 40 = 64,000 bytes, still
one real-mode segment and still a "small" bitmap (under 64KB), the same
size the 640-wide profiles already use. Constants that must follow:
`SCREEN_HEIGHT` (TSOFT; used by the flushes, TBitBlt, TOutput, TPixel,
the text bounds, and exported to SCANLR), the shadow size, and one
hard-coded 200 in `SDIB88.ASM` (DIB-to-screen clip). Off-screen drawing
therefore lands in the shadow like any other drawing and survives; nothing
needs repainting when it is revealed.

**Pixel reads and screen-to-screen copies** read the shadow (GetPixel,
BitBlt from the screen, ScrollWindow, SaveScreenBitmap substitutes) and
so work in logical coordinates with no change. The identity SRCCOPY that
DOS-box return uses still forces a full flush.

**Presentation (flush).** Only here do logical rows meet the screen. Each
of TR5's four flush routines clamps its row range to the viewport
`[top, top+200)`, converts those shadow rows, and writes them to video
rows `row - top`. Rows outside the viewport are skipped (they are already
correct in the shadow).

**Cursor.** USER passes MoveCursor logical coordinates (0..399). TCURSOR
draws in video memory, so it subtracts `top` when it computes the cursor
origin; its clipping to 200 physical rows is unchanged. A cursor outside
the viewport is simply not drawn.

**Mouse hit testing** needs no change: USER does it in logical
coordinates, and the mouse driver reports motion, not screen positions.
Clicks during and after a pan go to whatever is at the logical cursor
position, which is where the drawn cursor is whenever it is visible.

**Panning itself** is a full-viewport flush (200 rows converted). That is
too long for the mouse interrupt (MoveCursor runs at interrupt time) and
for the timer path (CheckCursor). So the interrupt path only records the
cursor position, as now. Panning runs in task time, in the driver's
Control (Escape) entry, called by a small helper application on a
timer: it applies the edge dwell rule (cursor in the top or bottom edge
band for a configurable time) and the keyboard alternative (polled with
GetAsyncKeyState), then calls the driver to pan by a fixed step.

## 2. Hardware-assisted alternatives (Tandy 1000 EX/HX)

The EX/HX video gate array shows a 32KB window of system RAM (CRT page
register 3DFh, 16KB units) through a 6845 CRTC whose 320x200x16 rows are
interleaved in four 8KB banks (row & 3). Two hardware routes exist:

- **CRTC start address.** The start address moves the display in whole
  character rows (4 scan lines here) and wraps inside each 8KB bank, so
  video memory can act as a 200-line ring: a pan of k lines converts only
  the k newly revealed lines. It still needs the full 64,000-byte shadow
  (video memory holds only 200 lines), so it saves time, not memory. It
  also depends on the exact wrap behaviour of the gate array, which
  emulators may not reproduce and which was not verified on real
  hardware. Not used for this prototype; noted as a later speed-up.
- **CRT page flip** between two 32KB pages (64KB of video RAM) gives an
  instant pan, but only in 200-line steps (a dialog straddling row 200
  stays split), and costs another 32KB of conventional memory, since
  Tandy video RAM is system RAM. Rejected.

No VGA-style pixel panning or programmable scan-line pitch is assumed;
the Tandy has neither.

## 3. Memory

Tandy video RAM is the top of system RAM: with mode 09h, 32KB of the
640KB is video (the BIOS keeps 16KB, RESERVE.COM protects the other
16KB), so DOS starts with at most 608KB. The software approach adds
32,000 bytes to the driver's fixed data (64,000-byte shadow instead of
32,000); video RAM stays 32KB. Measured figures follow in section 5.

Link maps of the two builds (`TSOFT.MAP`): the shadow segment `_SHADOW`
grows from 7D00h (32,000) to FA00h (64,000) bytes; code grows by 308
bytes (`_TEXT` +234 for the viewport clipping and `pan_set`, `_BLUEMOON`
+74 for the escape); `_DATA` by 2 bytes (`pan_top`). The driver is
PRELOAD FIXED, so all of it is taken from conventional memory for the
whole session: **+32,310 bytes**.

## 4. The prototype as built

Branch `ai/xt-pan`. Nothing in any release changes.

| File | Purpose |
| --- | --- |
| `src/xtpan/PANPATCH.PY`, `BUILDPAN.PY` | The driver edits (section 1) and their build on BUILD88's 320x200x16 profile, which reproduces the shipped `TR53216.DRV` byte for byte without the edits |
| `src/xtpan/XTPAN.C` | The panning helper (a Windows application, task time only) |
| `src/xtpan/PANTEST.C` | Test fixture: exact test pattern, tall dialog, overlapping windows, drag, menu, edit selection, benchmarks; logs what Windows reports |
| `src/xtpan/BUILDAPP.PY` | Builds both applications with the pinned compiler (`/G0 /Gw /AS`, LINK4) |
| `src/xtpan/PANCHK.PY` | Checks a capture of the test pattern pixel by pixel against the viewport top |
| `src/xtpan/XPWIN.PY` | The scripted 86Box session |
| `src/xtpan/EMULOCK.PY` | Runs every emulator job under the shared lock (non-blocking, refuses if another emulator runs, bounded) |
| `src/xtpan/PCP86.PY` etc. | Copies of the 86Box harness (`PROVENANCE.TXT`), with Tandy 1000 HX targets |

**Driver (XTPAN.DRV).** GDI and USER see a 320x400 screen. All drawing
goes to the 64,000-byte shadow as before; flushes present only the rows
inside the viewport; the cursor is drawn at its logical row minus the
viewport top. The viewport moves only through the Control escape 5850h
(input: new top, or FFFFh to query; output: top, 200, 400), which
converts the 200 visible rows in task time.

**Helper (XTPAN.EXE)**, started by WIN.INI `load=`, runs a 55 ms timer:

- *Edge dwell:* the pointer rests in the bottom (top) `Edge` rows of the
  viewport for `Dwell` ms: one `Step` down (up). A pass through the
  band shorter than the dwell does nothing.
- *Pointer outside the viewport* (USER lets the pointer go anywhere in
  the 400 rows, so a fast move can leave the viewport): pan at once, in
  whole steps, to show it. The drawn pointer and the click target are
  never apart.
- *Keys* `KeyMods`+`KeyDown`/`KeyUp`/`KeyTop` (default Alt+PgDn,
  Alt+PgUp, Alt+F9, NumLock off; see section 7 for why not Ctrl+Alt or
  Shift), polled with GetAsyncKeyState, including taps between ticks; a
  modifier seen within the last 250 ms counts as held.
- *FollowActive:* a newly activated window not wholly visible is brought
  into view (Windows centres dialogs on the 400-row desktop, so they
  otherwise appear straddling the viewport edge). The move is exact, not
  in Steps: the smallest change of top that shows the whole window, or
  its top row if it is taller than 200 rows (`FollowTop` in XTPAN.C). The
  helper re-reads the viewport top from the driver first, in case another
  program panned. After a key or follow pan the pointer is moved into
  the viewport if it was left outside.
- Each pan is logged with its duration when `LogFile` is set.

WIN.INI `[XTPan]` settings and defaults: `Enabled=1`, `Step=50`,
`Dwell=400`, `Edge=3`, `KeyMods=2` (1 Ctrl, 2 Alt, 4 Shift),
`KeyDown=34` (VK_NEXT), `KeyUp=33` (VK_PRIOR), `KeyTop=120` (VK_F9),
`FollowActive=1`, `LogFile=` (none).

**Turning it off.** `[XTPan] Enabled=0` stops the helper (the desktop
stays 320x400, viewport at the top). To remove the experiment, set
`display.drv=TR53216.DRV` in SYSTEM.INI again (the shipped Windows XT
driver) and remove `XTPAN.EXE` from `load=`; the helper also exits by
itself under any other display driver.

## 5. Evidence (86Box Tandy 1000 HX)

Current run: `pan/FIT` (`XPWIN.JSN`: 33 checks, 0 failures), made after
review with the exact-fit follow and the exact pointer check below; the
guest's own logs `PANTEST.LOG` and `XTPAN.LOG`, the lock record and every
capture, decoded to exact pixels, are kept with it. The previous run,
`pan/FINAL` (43/43), used the older helper and the weaker pointer check;
it is kept, and its 12 pattern captures were re-checked against the
exact arrow afterwards (`pan/FINAL/CURSOR.JSN`, 12/12; see section 7).
Demonstration: `pan/DEMO.GIF` (frames from the baseline and `FINAL`).
Builds: `pan/BUILD.JSN` (XTPAN.DRV, SHA-256 `4367985b...c60a97`, the
same driver in both runs), `pan/BUILD300.JSN`, `pan/APPS.JSN` (the
applications of `FIT`; `pan/FINAL/APPS.JSN` those of `FINAL`).

Emulator, ROMs, machine settings and guest changes: `pan/EMU.TXT`. The
session (`src/xtpan/XPWIN.PY`) drives Windows with xdotool keys and the
byte-exact serial mouse, and checks what Windows reports (log lines the
fixture and the helper write on the guest disk, read while it runs) and
exact pixels (`PANCHK.PY`: the capture decoded to 320x200 IRGB pixels;
every video row must equal the logical row `top + row` of the test
pattern, whose 8-row bands are all distinct, with one consistent colour
mapping). The pointer is part of the expected frame, not a skipped box:
the session reads the driver file from the guest disk, takes its
OCR_NORMAL arrow (32x32 resource) and the cursor compression factors in
its OEM configuration resource (1 horizontal, 2 vertical: USER hands
the driver a 32x16 cursor, each row the AND of two resource rows), and
composites it as TCURSOR.ASM draws it (AND bit 0 gives black, then XOR
bit 1 inverts the IRGB nibble) with its hot spot at the logged pointer
position minus the viewport top. Every pixel of the frame must match.
`CURCHK.PY` re-checks a kept run the same way and proves the check can
fail: the arrow one pixel left, right, up or down, no arrow, and one mask
bit flipped must each mismatch (the flipped bit by exactly one pixel).

| What | Check | `FIT` run |
| --- | --- | --- |
| Presentation | The test pattern, drawn once over all 400 rows, is exact at viewport tops 0, 50, 150, 200 and after relaunch | PASS |
| Pointer | The driver's 32x16 arrow, exact in every pixel, with its hot spot at the logged position minus the viewport top, in all 12 pattern captures (including clipped at the bottom edge) | PASS |
| Keys | Alt+PgDn x4 = four 50-row pans; Alt+PgUp, Alt+F9 back to 150 and 0 | PASS |
| Edge dwell | A brief touch of the bottom edge does not pan; resting there pans one step | PASS |
| Pointer outside | A fast move to row 330 shows it at once | PASS |
| Hit testing | Clicks at (20,160), (300,345), (150,300) are reported there, inside the viewport | PASS |
| Screen copies | ScrollWindow x3 of the 400-row pattern, then viewed at tops 0 and 200 | PASS |
| Repeated panning | 10 alternating pans, then exact pixels | PASS |
| Tall dialog | A 275-row DialogBoxIndirect dialog; its Bottom button (rows 259-277) clicked after panning | PASS |
| Exact follow | A bordered 190-row window at rows 30-220 shown from top 0: the helper pans 0 to 20 (logged), and all 190 rows, border included, are on screen at video rows 10-199 | PASS |
| Overlap | Two windows across row 200: clicks reach the window on top at each point | PASS |
| Drag | Caption dragged from row 146 to 296: window ends exactly 150 rows lower; the viewport followed during the drag | PASS |
| Menu | A menu bar at row ~250: its fourth item clicked, command 204 received | PASS |
| Selection | Drag-select in an edit control from line 2 (row 131) to line 18 (row 291) | PASS |
| Exit and relaunch | Windows exits to DOS and restarts; pattern exact again | PASS |

The same tall dialog on the unchanged driver (`pan/BASE/XPWIN.JSN`,
picture `pan/BASE/BEFORE.PNG`): Windows moves it to row 0 and its Bottom button lies at
rows 238-256, below the 200-row screen; only the keyboard (Tab, Space)
reaches it.

## 6. Measurements

Same machine, same disk, same fixture (`pan/BASE`, `pan/NOHELP`,
`pan/FINAL`); free memory is GetFreeSpace(0) as the first test
application starts; times are sums over many operations
with the 55 ms BIOS tick. The helper measured is the `FINAL` build; the
`FIT` build differs only when the active window changes (the exact-fit
arithmetic and one driver query), and the benchmark was not repeated with
it. Its pans took the same time (79 pans in `pan/FIT/XTPAN.LOG`, average
1044 ms).

| | TR53216.DRV (shipped) | XTPAN.DRV, helper off | XTPAN.DRV + XTPAN.EXE |
| --- | --- | --- | --- |
| Windows free memory | 268,448 | 236,128 (-32,320) | 228,032 (-40,416) |
| 400 rectangle fills | 8,404 ms | 8,459 ms (+0.7%) | 8,513 ms (+1.3%) |
| 200 TextOut lines | 17,850 ms | 17,850 ms (0) | 17,961 ms (+0.6%) |
| 50 ScrollWindow | 39,711 ms | 39,711 ms (0) | 39,985 ms (+0.7%) |

The driver's cost matches its link map (+32,310 bytes: 32,000 shadow,
308 code, 2 data). The helper costs 8,096 bytes (its code, data, 4 KB
stack and a 1 KB heap); its 55 ms timer explains the small slowdown in
the last column (fills +1.3%, text +0.6%, scrolling +0.7%). With the
helper off, text and scrolling cost exactly what they cost on the shipped
driver and fills 0.7% more (one 55 ms tick in 400 fills, at the
resolution of the measurement): only rows inside the viewport are
converted, as before.

**Pan latency:** 40 pans alternating 0 and 200: 42,182 ms, **1,055 ms
each**; alternating 0 and 50: 42,951 ms, 1,074 ms each; the 65 pans the
helper made in the final run averaged 1,042 ms (`pan/FINAL/XTPAN.LOG`). A pan is
one conversion of the 200 visible rows by the unchanged TR5 code, the
same work as one full-screen flush of the shipped driver, so its cost
does not depend on the step. The mouse interrupt path is unchanged
except for one subtraction (the cursor origin); no pan, redraw or
allocation happens in it or in the timer interrupt.

**Conventional memory on a 640 KB EX/HX:** 32 KB of the 640 KB is video
RAM (the BIOS keeps 16 KB, RESERVE.COM the other 16 KB) with either
driver. Inside Windows the experiment takes 40,416 of the 268,448 free
bytes (15%), leaving 228,032.

**A smaller virtual height** is a build option (`BUILDPAN.PY --rows`, a
multiple of 4 from 204 to 408). `--rows 300` builds and links with a
48,000-byte shadow (+16,000 bytes instead of +32,000; link map in
`pan/BUILD300.JSN`); it was not run in the emulator. 300 rows hold the
275-row test dialog.

## 7. Failures on the way (kept)

Every failed run is kept under `pan/` with its logs, lock record and
captures. None was a driver fault:

- run 1 (`pan/RUN1`): the session counted a file's trailing newline as a
  line and missed every new log line; aborted.
- run 2 (`pan/RUN2`): Ctrl+Alt+PgDn, then the default pan key, is 86Box's
  fullscreen hotkey: the emulator took one key press and resized its
  window. The default keys became Alt+Shift.
- run 3 (`pan/RUN3`, 36/43): the fixture passed near strings to
  wsprintf's `%s` (garbled log lines); the session's dead-reckoned
  pointer went stale after the helper moved the pointer into view;
  Alt+Shift+Home never registered (with Shift, a NumLock-off keypad key
  can arrive as a digit on XT/Tandy keyboards): the default "top" key
  became Alt+Shift+F9.
- baseline 1 and 2: Escape did not close the fixture's dialog; the
  benchmark's text crossed row 200, where the shipped driver (rightly)
  flushes the whole screen, which made it look twice as slow. The bench
  now stays inside 200 rows for both drivers.
- run 4 (`pan/RUN4`, 41/43) and run 5 (`pan/RUN5`, 40/43): Alt+Shift+PgDn
  and PgUp were sometimes not seen (2 of 23 quick taps; 4 of 10 presses
  held for 150 ms). The helper's raw key log (`LogKeys=1`, `pan/KEYDIAG`)
  showed why: with Shift held, PgUp/PgDn arrive wrapped in transient
  "Shift up" codes (the scheme enhanced keyboards use around the grey
  navigation keys), and Windows 3.0's XT keyboard driver takes them
  literally, so Shift reads as released while PgDn is down. On a real
  EX/HX keyboard PgUp/PgDn are keypad keys, which Shift turns into
  digits. Shift is the wrong modifier either way: the default keys are
  now Alt+PgDn, Alt+PgUp and Alt+F9, and a modifier seen within the last
  250 ms counts. Keys still need NumLock off (Alt with a keypad digit is
  Windows' Alt+number character entry).

Found in review after `FINAL` (both fixed and re-run as `pan/FIT`):

- FollowActive moved in whole 50-row Steps, down until the bottom showed,
  then up until the top showed. A 190-row window at rows 30-220 seen from
  top 0 went to 50, then back to 0, and stayed cut off although it fits.
  It now uses the exact smallest move (`FollowTop`), tested on the host
  for every top and every window position (`HOSTPAN.PY`, 16,120,200
  cases, compiled from XTPAN.C itself) and in the emulator.
- The pointer check excluded a 16x20 box at the pointer from the pattern
  check and then only required that the box differed somewhere. One wrong
  pixel would have passed it. It now checks the actual arrow, as above.
  Doing so showed that the arrow on screen is 32x16, not the 32x32
  resource: USER compresses it by the driver's own factors. The rule
  for combining two rows into one (AND, for both masks) was identified
  by comparing one capture (`FINAL/PTOP0`) with the resource. It is one
  fixed rule, and the other 23 pattern captures of `FINAL` and `FIT`
  match it exactly.

## 8. Recommendation

The architecture works and is contained: GDI and USER only need the
larger screen in GDIINFO; drawing, clipping, pixel reads and screen
copies already go through the shadow; only presentation and the cursor
origin know about the viewport; panning happens in task time through an
escape. Nothing needed a kernel or USER change.

- **Keep it an opt-in experiment**, not part of the release. It is worth
  offering to EX/HX users who keep hitting dialogs that do not fit, with
  the costs stated: 40 KB of Windows memory and about a second per pan
  step on a 7.16 MHz machine.
- **Prefer the 300-row build** if wider testing shows 300 rows are enough
  for the dialogs people meet (half the memory cost); keep 400 rows for
  the largest dialogs.
- **Pan speed** is the weak point. Two routes, both future work: (1) the
  CRTC start address in a ring of video memory, so a 50-row step converts
  only the 50 new rows (about a quarter of the time); this needs the
  gate array's address wrap within each 8 KB bank confirmed on real
  hardware first; (2) a table-driven nibble conversion, which would speed
  every flush, not only pans, but touches the shared TR5 path and needs
  its own qualification.
- **Do not** add hardware page flipping (another 32 KB of system RAM,
  200-row steps only) or VGA-style assumptions.
- Real hardware: on 2026-10-13 Chad (the maintainer) reported that the
  panning test worked on his real Tandy 1000 EX. That is the first run
  outside 86Box, and on the machine the work targets (86Box has no EX
  model). It is his report, not a scripted capture: no pan times,
  free-memory figures or screenshots from the EX are recorded here yet.
  Still to record from real hardware: pan time per step, the WINXT
  keyboard keys (Alt+PgDn / Alt+PgUp / Alt+F9) on the EX keyboard, and an
  HX run.

## 9. Reproducing

All inputs are explicit and pinned (`tools/BUILDDEPS/README.MD`); nothing
is fetched. Windows media, ROMs and Microsoft fonts stay private.

1. Driver (DOSBox-X, pinned MASM/DDK view):
   `python3 src/xtpan/BUILDPAN.PY --repo <deps view> --dosbox <dosbox-x> --out <fresh dir>`
   gives `XTPAN.DRV` and `PANRES.JSON` (`--rows 300` gives `XTPAN300.DRV`).
   Without the edits the same profile rebuilds `TR53216.DRV`
   (sha256 `33f681b0...`) byte for byte; `python3 src/xtpan/PANPATCH.PY --check`
   verifies every edit anchor matches exactly once.
2. Applications: `python3 src/xtpan/BUILDAPP.PY --repo <deps view> --dosbox <dosbox-x> --out <fresh dir>`
   gives `XTPAN.EXE` and `PANTEST.EXE`.
3. VM (settings in `pan/EMU.TXT`): put `XTPAN.DRV` (or `TR53216.DRV`),
   `XTPAN.EXE`, `PANTEST.EXE`, `RESERVE.COM` and `MSTEST.COM` in one folder, then
   `python3 src/xtpan/PCP86.PY prepare --target xtpan --vm <new dir> --pristine <disk image> --drv <XTPAN.DRV> --tools <folder>`
   (`--target xtbase --drv TR53216.DRV` for the unchanged baseline).
4. Session, under the shared emulator lock (Xvfb on `:79`):
   `python3 src/xtpan/EMULOCK.PY --lock <shared lock> --seconds 5400 --status <vm>/LOCK.JSN --purpose xtpan -- <script>`
   where the script starts `PCPMOUSE.PY serve --vm <vm>` (with
   `PCPMOUSE_BYTE_MS=7.5`), `PCP86.PY start --box <86Box AppRun> --roms <roms> --vm <vm>`,
   waits 80 s for the DOS prompt, runs `XPWIN.PY --vm <vm>` (add `--base`
   for the baseline, `--measure` for memory and drawing only), then
   `PCP86.PY stop --vm <vm>`. Results land in `<vm>/XPWIN.JSN`.
5. A single capture: `python3 src/xtpan/PANCHK.PY <capture> --top <T> [--off <O>] --drv <XTPAN.DRV> --cursor <X>,<VY>`;
   a whole kept run with negative controls: `python3 src/xtpan/CURCHK.PY --run docs/pan/FIT --drv <XTPAN.DRV>`.
   Host tests (no emulator): `python3 src/xtpan/HOSTPAN.PY [--drv <XTPAN.DRV>]` and `python3 src/xtpan/HOSTTEST.PY`.
6. Demonstration: `python3 src/xtpan/DEMO.PY --out pan/DEMO.GIF --frame <png> "<caption>" ...`
   (the frames used are listed in the commit that added `pan/DEMO.GIF`).
