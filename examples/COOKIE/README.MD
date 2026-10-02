# Tandy Cookie Clicker Benchmark

A tiny native Windows 3.0 usability test for the Tandy 1000 display driver.
The window caption is shortened to **Cookie** so it fits 160 pixels.

## Run the ready EXE

1. Copy `COOKIE.EXE` to a writable DOS directory, for example `C:\COOKIE`.
2. Start your existing accepted Tandy Windows installation through its
   `C:\TANDY88\TANDY88` launcher. Keep its reservation helper and mode intact.
3. In Program Manager choose File > Run and enter `C:\COOKIE\COOKIE.EXE`.
   The app opens maximized; it needs no installation, DLL, COMMDLG, or data file.

Click inside the cookie (a GDI ellipse with five chips), or press Space, to add
one cookie. The native **Buy +1 CPS (10)** button costs ten cookies and adds one
cookie per second. Press U as a keyboard alternative. The button stays readable
and enabled even when unaffordable; a click then says **Need 10 cookies**.
This deliberately avoids invisible gray disabled text in 2/4-color modes.

Native menus: **Game > New, Save, Load, Exit** and **Help > About**. Alt+G / Alt+H
and the underlined menu letters work. About has a native OK control and supports
Enter, Escape, and its system Close command. New resets the current session.
Exit does not save automatically. Save explicitly overwrites `COOKIE.SAV`
beside the EXE; Load validates it before replacing the current state.

The count is capped at 999,999 and CPS at 999. No offline income or elapsed-time
catch-up is attempted: one delivered 1,000 ms Windows timer tick adds the current
CPS. Windows timers can be delayed/coalesced by other work; this is a UI exercise,
not a calibrated performance or real-time benchmark. Save is a fixed 12-byte,
versioned little-endian record with checksum. Invalid, truncated, extended,
out-of-range, or unreadable saves leave the live game unchanged. The simple
in-place save is not crash-atomic; a failed write may require starting a new save.

## Minimum usable display and tested modes

**160x200 is the minimum verified usable screen resolution.** The complete
maximized app, native menus, buy control, count/CPS, instructions, and About/OK
fit without horizontal scrolling. Smaller resolutions are not supported or
tested. Resizing a window below its intended compact dimensions can clip it;
maximize it again. The app also runs at 320x200x4, 320x200x16, 640x200x2, and
640x200x4. See `TESTS.MD` and `EVIDENCE` for actual results and screenshots.

The 2/4-color cookie fill is intentionally palette-dependent: white in CGA
cyan/magenta and monochrome, red in the black/red/green/white profile, yellow in
16-color profiles. Its black outline/chips remain visible. The 640 modes have
non-square displayed pixels; native raw captures double rows to 640x400, while
the actual logical resolution remains 640x200. The 160 capture doubles columns
to 320x200. No screenshot has been repainted or cosmetically corrected.

## Rebuild with the existing project toolchain

From the repository root on the host:

    python3 examples/COOKIE/BUILD.PY --dosbox /path/to/dosbox-x --out /new/build

The build uses the existing `BIN`, `DDK/286/INC`, `INCLUDE`, and `LIB` tree. If
using this standalone source ZIP, pass `--repo /path/to/full/tandy/repository`.
Python 3 is a host build convenience only; it is not a guest runtime dependency.
The compile is Microsoft C small model, `/G0 /Gw /AS`, with LINK4, SLIBCEW and
LIBW. There are no 286/386 code-generation or modern-runtime dependencies.
Tool compilation may use 16 MB; all runtime acceptance uses normal 640 KB,
Windows real mode, the 8086/8088 prefetch core, no EMS/XMS/UMB, and no FPU.

Alternatively in DOSBox, mount the repository as C and a writable copy of the
four source/build files as D; run D:\BUILD.BAT. It writes BUILD.LOG and COOKIE.EXE.
The toolchain and full Windows media are intentionally not included here.

## Scope

Only this independent `examples/COOKIE` demo is added. No display driver,
launcher, reservation helper, media package, or unrelated application changed.
The benchmark exercises windows, mouse/keyboard input, a native button,
GDI/text, timer/repaint, menus, a modal dialog, and fixed-file I/O.
