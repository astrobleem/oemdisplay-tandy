# Edge-panning desktop for Windows XT (experimental): investigation

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
- *Keys* `KeyMods`+`KeyDown`/`KeyUp`/`KeyTop` (default Ctrl+Alt+PgDn,
  PgUp, Home), polled with GetAsyncKeyState including taps between
  ticks.
- *FollowActive:* a newly activated window not wholly visible is brought
  into view (Windows centres dialogs on the 400-row desktop, so they
  otherwise appear straddling the viewport edge). After a key or follow
  pan the pointer is moved into the viewport if it was left outside.
- Each pan is logged with its duration when `LogFile` is set.

WIN.INI `[XTPan]` settings and defaults: `Enabled=1`, `Step=50`,
`Dwell=400`, `Edge=3`, `KeyMods=3` (1 Ctrl, 2 Alt, 4 Shift),
`KeyDown=34` (VK_NEXT), `KeyUp=33` (VK_PRIOR), `KeyTop=36` (VK_HOME),
`FollowActive=1`, `LogFile=` (none).

**Turning it off.** `[XTPan] Enabled=0` stops the helper (the desktop
stays 320x400, viewport at the top). To remove the experiment, set
`display.drv=TR53216.DRV` in SYSTEM.INI again (the shipped Windows XT
driver) and remove `XTPAN.EXE` from `load=`; the helper also exits by
itself under any other display driver.
