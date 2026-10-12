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
