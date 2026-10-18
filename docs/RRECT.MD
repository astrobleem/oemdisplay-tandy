# Calculator's rounded keys: why they draw slowly, and a bounded-copy fix

**Summary.** In 86Box's Tandy 1000 HX (8088 at 7.16 MHz, 640 KB,
Windows 3.0 real mode, TR5 320x200x16 driver), one full repaint of
Windows 3.0 Calculator takes **92.5 s**. Almost none of that time is
spent drawing. Calculator draws its keys with `RoundRect`, which GDI
breaks into small driver Output calls. Of the 526 Output calls in one
repaint, 82 make TR5 copy its **whole** 32 KB shadow frame to video
memory (about 1.05 s each). The rest copy only the rows they touched.

The candidate driver changes only which rows are copied after each call;
nothing it draws changes. It handles two cases:

* GDI's begin/end markers (Output styles 80 and 81) copy nothing, because
  the renderer does not touch the shadow for them.
* Polylines with 3 to 1,024 points, all on screen, copy only the rows
  from their highest to their lowest point.

In matched runs, Calculator's repaint drops to **10.4 s (8.9x faster)**,
Reversi's from 13.6 s to 1.4 s and Paintbrush's from 36 s to 4.5 s.
**All 13 compared frames are byte-identical** to the unchanged driver's,
across all four 16 KB banks including the padding bytes. Three
deliberately broken versions of the candidate are each caught.

**Cost:** 96 bytes of driver code (`_TEXT` 3F42h to 3FA2h), no data and
no new resident component. Every TR5 profile grows by the same 96 bytes.

Branch `ai/roundrect-speed`. This is emulator evidence only. It changes
no release default, package, pin or accepted hash, and it has not been
tried on real hardware.

![Calculator repaint, unchanged vs candidate](rrect/TIMELINE.PNG)

*Real 86Box captures (Ctrl+F11, decoded exactly to 320x200 by SHOTDEC)
taken at fixed host times after Calculator's first timed repaint starts.
The unchanged driver still has not drawn the Back key at 95 s. The
candidate is finished at 14.7 s. In this run the hourglass cursor is over
the keypad, so both drivers are slower than in the timing runs below. The
final captures of the two drivers are pixel-identical, and so are those
of Reversi and Paintbrush ([SHOTS](rrect/SHOTS)).*

## 1. The drawing path, as traced

The traced calls (summarised in [TR_BASE.TXT](rrect/TR_BASE.TXT)) show
how GDI turns each call into driver Output calls.

`GetDeviceCaps` on TR5 reports CURVECAPS=0 and POLYGONALCAPS=8
(PC_SCANLINE only), so GDI simulates RoundRect and Ellipse itself rather
than passing them to the driver. Calculator imports RoundRect and
Rectangle. A test-only trace build of TR5 (`RRPATCH.patch_trace`)
records every TOutput call and returns the records through a private
escape. The trace showed:

| GDI call (in Calculator) | Driver Output calls | TR5 screen copy |
| --- | --- | --- |
| RoundRect, filled, with pen | style 80 (OS_BEGINNSCAN) | **whole frame** |
| | 1 one-interval OS_SCANLINES per fill row | that row |
| | style 81 (OS_ENDNSCAN) | **whole frame** |
| | 17-point OS_POLYLINE (the outline) | **whole frame** |
| Rectangle | 5-point OS_POLYLINE; the interior goes through BitBlt | **whole frame** |

TR5's renderer returns -1 for styles 80 and 81 without touching the
shadow. TR5's existing TOutput gate bounded only two kinds of call:
scanlines, and two-point polylines. Everything else took FlushShadow.
One Calculator repaint makes 526 Output calls:

* 444 single-row scanlines, which were already bounded;
* 27 style-80 and 27 style-81 markers;
* 28 polylines of 5, 23 or 25 points.

That makes **82 whole-frame copies**. GDI's own clipping (the
roundrect_clipped stage) only removes calls or shortens them, so it does
not change this picture.

## 2. Where the time goes

Ablation builds remove one part of the work at a time
([A_*](rrect), first probe version, Calculator repaint):

| Driver | Calculator repaint |
| --- | --- |
| unchanged TR5 | 98.98 s |
| trace build (records every call) | 99.09 s (+0.1%) |
| no copy to video memory at all (`noflush`, test-only, wrong output) | 6.32 s |
| no copy and no rendering (`nodraw`, test-only, wrong output) | 5.22 s |

So **93.6% of the repaint is copying the shadow to the screen**. About
1.1 s is TR5 rendering into the shadow, and about 5.2 s is Calculator,
USER, GDI's RoundRect simulation and the driver entry points. With 82
whole-frame copies at about 1.05 s each, the copies account for about
86 s; most of the remaining copy time is the row copies after the 444
scanlines.

## 3. The change

[RRPATCH.PY](../src/rrect/RRPATCH.PY) edits only the staged
`EGA/TSOFT.ASM` (TOutput); `patch_candidate` is about 40 lines of
8086 MASM. Each edit matches an exact anchor exactly once, and the build
refuses to run if the staged source differs. [RRBUILD.PY](../src/rrect/RRBUILD.PY)
runs `BUILD88.PY` unchanged, so BUILD88's instruction, REP-prefix and
link audits run on the patched listings. The `baseline` variant
reproduces the accepted TR5 driver hash `33f681b0…`
([TRIAL5/BUILDS.JSN](TRIAL5/BUILDS.JSN)).

* **Styles 80 and 81:** clear `dirty` and skip the copy. Before the
  change, the shadow already matched video memory before the call, and
  the renderer leaves it untouched for these styles. The return value
  is unchanged.
* **OS_POLYLINE with 3 to 1,024 points:** after the existing checks
  (point, mode, pen and clip structures lie within their segments,
  ROP2 1-16, background mode 1-2, a valid on-screen clip rectangle,
  pen style 4 or less), every point must satisfy x < 320 and y < 200 (an unsigned
  compare, which also rejects negatives). The copied rows are the lowest
  Y through the highest Y plus one, through the same FlushRetainRows
  path that two-point lines and scanlines already use. TR5 has no wide
  pens: GDI simulates them. A one-pixel polyline therefore never leaves
  its points' row range, and clipping only removes pixels.
* **Everything else is unchanged:** two-point lines, scanlines, other
  styles, any point off the screen, longer polylines, and anything the
  existing checks reject all fall back to the whole-frame copy exactly
  as before. Pens, brushes, raster operations, clipping and the cursor
  code are not touched. The renderer still does all the drawing.
* One existing `jmp short TOutput_bounded` became a near jump, because
  the inserted code is in its way.

**Code and memory cost (separate from timing).** Driver file: 54,896 to
54,992 bytes (+96). Link map: `_TEXT` 3F42h to 3FA2h (+96); `_DATA`
(382h), the 32,000-byte shadow and every other segment are unchanged.
No BIOS service, TSR or helper is added. The other four TR5 profiles
(640x200x4, 160x200x16, 320x200x4, 640x200x2) also build, each +96 bytes
([PROFILES.JSN](rrect/PROFILES.JSN)), but only 320x200x16 was run.

## 4. Matched A/B: exact pixels and timings

Both runs used the same private PC DOS 3.20 + Windows 3.0 image,
prepared the same way by `PCP86.PY prepare --target rrect`, with only
the driver differing. Both used 86Box 6.0 `tandy1000hx` with an 8088 at
7,159,092 Hz, 640 KB and XTIDE.

The probe [RRBENCH.C](../src/rrect/RRBENCH.C) runs as the Windows shell.
Each stage starts from a white screen with the cursor hidden. The probe
times each batch with GetTickCount (about 55 ms resolution), then saves
the 32 KB B800h frame.

[RRCMP.PY](../src/rrect/RRCMP.PY) passes only frames that are
byte-identical across all 32,768 bytes, including bank padding, and
only when both runs have the same stage names and API success counts.
Timings are reported but never compared
([C_CAND.TXT](rrect/C_CAND.TXT)).

| Stage | What it draws | Unchanged | Candidate | Frame |
| --- | --- | --- | --- | --- |
| roundrect_key | 20 Calculator-sized keys (26x15, r8, black pen, light grey) | 64.3 s | 4.8 s | equal |
| rectangle_key | 20 Rectangles, same size | 20.8 s | 2.0 s | equal |
| roundrect_large | 6 of 60x30, r12, white | 19.9 s | 2.5 s | equal |
| roundrect_hollow | NULL_BRUSH (outline only) | 20.9 s | 2.1 s | equal |
| roundrect_nopen | NULL_PEN (fill only), grey | 43.3 s | 2.5 s | equal |
| roundrect_xor | R2_XORPEN | 63.9 s | 4.4 s | equal |
| roundrect_overlap | 20 keys overlapping at 6,4 steps | 64.0 s | 4.4 s | equal |
| roundrect_clipped | clip region 40,30 to 280,170 | 51.1 s | 1.9 s | equal |
| ellipse_12 | 4 Ellipses (same GDI path) | 12.7 s | 0.8 s | equal |
| cursor_overlap | keys drawn under the visible arrow cursor, cursor then moved away | 71.1 s | 9.5 s | equal |
| calc | Calculator, full client repaint (x3) | 92.5 s | **10.4 s** | equal |
| reversi | Reversi, full client repaint (x3) | 13.6 s | 1.4 s | equal |
| pbrush | Paintbrush, full client repaint (x3) | 36.1-36.7 s | 4.5-5.2 s | equal |

Time from launch until the window was painted, in the same runs: Calculator 96.7 s to 14.4 s, Reversi
16.3 s to 4.1 s, Paintbrush 53.2 s to 22.1 s. Absolute times depend on
the screen state, such as where the cursor is: the first probe version
measured Calculator at 99.0 s, and the screenshot runs at 99.0 s and
14.7 s. Compare only runs made with the same probe.

A trace build of the candidate gives the same frames
([C_CANDTR.TXT](rrect/C_CANDTR.TXT)). It shows that every call in
the Calculator, Reversi and Paintbrush repaints is now either bounded or
copies nothing ([TR_CAND.TXT](rrect/TR_CAND.TXT)).

## 5. Fault injection: the checker notices broken candidates

Each broken variant is built and run exactly like the candidate.
Differences are counted against the unchanged driver
([C_M*.TXT](rrect), difference images in `rrect/D_*`).

| Broken variant | What it does wrong | Result |
| --- | --- | --- |
| mut-lastrow | polyline copy stops one row early | 11 of 13 stages differ (Calculator: 456 px) |
| mut-firstrow | polyline copy starts one row late | 11 of 13 stages differ (Calculator: 219 px) |
| mut-scanskip | scanline fills are never copied | roundrect_nopen differs (6,640 px) |

The stages that stay equal show what each stage can and cannot detect:

* **XOR stage.** A black pen in R2_XORPEN leaves pixels unchanged, so a
  stale outline row looks the same.
* **Shapes drawn with a pen.** The outline's bounded copy also covers
  the fill rows, so it hides a missing fill copy.

The NULL_PEN stage exists to catch that second case. The host tests in
[RRTEST.PY](../src/rrect/RRTEST.PY) cover the checker itself: one
changed pixel, a padding byte, a missing dump, a missing stage or a
different API result each fail, and a changed timing does not. They also
check the patch anchors (missing or repeated anchors are refused) and
that the committed comparisons say what this page says.
`.github/workflows/rrect.yml` runs them.

## 6. Reproducing

Commands and the pinned inputs they need are in each script's header.
The external inputs follow [BUILDDEPS](../tools/BUILDDEPS/README.MD): a
DDK/toolchain view, DOSBox-X, 86Box 6.0 with Tandy 1000 HX ROMs, and
your own Windows 3.0 and PC DOS media. None of these are in this
repository; nor are the drivers, frame dumps or disk images.
`src/rrect/RREVID.PY` collected this folder. Each `RRRUN.JSN` records
the SHA-256 of every frame dump and of the driver installed in that run.

```
python3 src/rrect/RRBUILD.PY --repo <view> --dosbox <dosbox-x> --out <dir> --mode 320x200x16 --variant candidate
python3 src/xtpan/PCP86.PY prepare --target rrect --vm <vm> --pristine <img> --drv <dir>/TANDY88.DRV --drv-sha <sha> --tools <dir>
python3 src/rrect/RRRUN.PY --vm <vm> --box <86Box> --roms <roms> --out <run> [--shots]
python3 src/rrect/RRCMP.PY <baseline run> <candidate run> --png <dir>
```

## 7. Limits and next step

* Emulator only; not run on a Tandy 1000 EX. 86Box has no EX, so the
  HX stands in.
* Only the 320x200x16 profile was run; the others were only built.
* No release default, package or pin changes; adopting the change would
  be a separate, deliberate TR5 update.
* What is left of the candidate's Calculator repaint is about 4 s of
  single-row copies after each fill scanline: 10.4 s with them, 6.3 s
  with no copies at all. These could be merged into one bounded copy at
  OS_ENDNSCAN. That is not implemented here; it would need its own
  exactness evidence.
