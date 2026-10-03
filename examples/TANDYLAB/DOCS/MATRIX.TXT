MATRIX: ON-DEMAND DIGITAL RAIN FOR WINDOWS 3.0 / TANDY 8088

Run MATRIX.EXE from Program Manager's File > Run, or add an ordinary
Program Manager item pointing to MATRIX.EXE. Start Windows using the
existing accepted TANDY88 launcher. No setup or driver replacement.

Press any key, click a mouse button, or move the pointer more than two
pixels to leave. Alt-Tab, Close and Windows shutdown also dismiss it.
There is no password lock. This is an ON-DEMAND fullscreen saver: it
DOES NOT start automatically after idle time, install a resident helper,
edit WIN.INI, or register a Windows 3.1 .SCR module. Automatic Windows 3.0
idle activation would need a separately tested input-hook DLL.

DISPLAY
- 160x200x16 and 320x200x16: dark/bright green trails, white leading glyphs.
- 640x200x4: green trails with sparse dim tail pixels and white heads.
- 320x200x4: cyan trails, matching that mode's existing physical palette.
- 640x200x2: white heads and patterned monochrome fading.
All glyphs are original simple 8x8 symbols. No movie images are included.

DRAWING AND SAFETY
The five accepted graphics drivers flush their entire shadow bitmap for
visible GDI drawing. MATRIX instead writes changed 8x8 graphics cells
straight into their known B800 framebuffer layout. This is GRAPHICS rain,
not the experimental text-mode driver. No video mode/palette or driver
is changed. The fast path requires real mode, an exact known loaded
module basename, BIOS mode, page zero, width, height and color tuple.
Mode/page, foreground ownership and overlapping windows are rechecked
before drawing. Unknown matching-size displays use a slower GDI fallback;
/G explicitly selects that fallback. Height other than 200 or width outside 160..640 is rejected.

The cursor is hidden only while active, with one balanced ShowCursor
call on exit. Drawing is timer-driven and yields to Windows. Deactivation,
any overlapping higher window, input or shutdown stops framebuffer writes.
An app-local cell grid handles sparse updates and repaint recovery. A
16-occupied-cell check detects full shadow flushes; it is not an exhaustive
per-pixel integrity check against arbitrary background video writers.
On exit a same-pixel GDI copy flushes the driver's current canonical shadow
back to the display, then the fullscreen window is destroyed normally.
It never restores an old desktop snapshot over a different app's updates.
The canonical flush can make exit take longer than ordinary rain updates.

BOUNDARIES
No allocations, hooks or GDI objects are created on each animation tick.
The grid is bounded at 80 columns by 25 rows; the dirty queue holds at
most four cells per column. Direct drawing touches visible bytes only,
never unused bank padding. Normal direct rendering allocates no full-screen
bitmap. The optional GDI path creates one reusable compatible bitmap.
The QA-only path allocates 32KB to compare desktop restoration.

BUILD
Use the existing owned Microsoft C 6 and Windows SDK toolchain from the
Tandy project. Tools and Windows files are not included in this package.
python3 SOURCE/BUILD.PY --repo <project> --dosbox <dosbox-x> --out <new-dir>
Compiler flags: /G0 /Gw /AS /W3 /Ox, with WINVER 0x0300. No floating point.
BUILD.BAT is also provided for the mounted C: toolchain, D: build layout.

REPRODUCIBLE CHECKS
/T: 60 timer updates, performance/memory log beside EXE, then exits.
/C: same benchmark plus native framebuffer at update 40, MATRIX.RAW.
/Q: message-driven input/restoration/repaint/overlap tests, then exits.
/F: 60-update benchmark of the forced GDI fallback.
These diagnostic switches replace MATRIX.LOG; /C and /Q also replace
MATRIX.RAW and RESTORE.RAW respectively, beside a writable EXE copy.
Diagnostic logs measure emulated GetTickCount, in coarse clock ticks.
A zero draw time at accelerated settings means below clock resolution.

SOURCE/RUNLAB.PY makes a fresh clone of an already installed owned guest,
with 640KB, 8086_prefetch, FPU/XMS/EMS/UMB disabled, and no source-install
changes. Select --preset accelerated (200000 cycles) or approx-xt (240).
Use --mode T, C, Q or F and a fresh output path.

Host test:
cc -x c -std=c89 -O2 -fsanitize=undefined,address SOURCE/TESTHOST.C -o test
ASAN_OPTIONS=detect_leaks=0 ./test
LeakSanitizer is disabled because this execution sandbox cannot run it.
The test itself uses fixed arrays and no dynamic allocations.

SOURCE/VERIFY.PY checks completed C/Q/XT/F runs against one release hash,
the host rendering oracle and the restoration log assertions.

SOURCE/AUDIT.PY runs a scoped objdump i8086 control-flow audit from the
NE entry and exported callbacks. Indirect continuations and imported
Windows code are excluded; it is not exhaustive ISA certification.
SOURCE/DECODE.PY converts actual B800 captures into PNG images, requiring
Pillow on the host. It does not invent or retouch screen pixels.

See RESULTS.TXT for measurements and exact verification limits.
