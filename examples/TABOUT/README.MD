# About This Tandy

A tiny native Windows 3.0 system-information app for the Tandy display-driver
project. Inspired by the compact machine summary in
https://github.com/astrobleem/dosfetch . This is original Windows code; none of
DOSfetch's direct hardware, timing, BIOS, IRQ or emulator-detection routines
are imported.

## Run

Copy TABOUT.EXE to the Windows machine. Start Windows 3.0 in real mode using
the project's normal TANDY88 launcher; keep its RESERVE protection. In Program
Manager, choose File > Run and enter the path, for example C:\TABOUT.EXE.
Do not run this Windows EXE directly at a DOS prompt.

The app opens maximized. The minimum verified screen is 160x200. All five
accepted profiles work: 160x200x16, 320x200x4, 320x200x16, 640x200x2,
and 640x200x4. It uses native Windows buttons, GDI text and the stock fixed
system font, with a 148-pixel-wide information area centered on larger screens.
There are no settings, installation changes, file writes, timers, or sound.

- Sys / S: Windows version, Windows execution mode, CPU family, model status.
- Disp / D: GDI resolution, physical color count, logical DDB planes and bits.
- Mem / M: free Windows global-heap memory in KiB.
- Refresh / R: resample all values; memory is a snapshot, not a live meter.
- Left / Right: previous / next page, wrapping around.
- Tab / Shift-Tab: move native button focus. Space activates the focused button.
- Escape or the system menu's Close: exit.

## What the numbers mean

GetVersion supplies the Windows version. GetWinFlags supplies Windows mode
and CPU-family flags. It cannot distinguish an 8088 from an 8086, an exact CPU
model or clock rate. On this target, the honest family label is 8086/8088.
The machine model is deliberately unknown; the program does not assume that
the active Tandy display driver proves a particular motherboard or EX/HX model.

GetDeviceCaps(HORZRES/VERTRES) supplies the active GDI dimensions. NUMCOLORS
supplies the physical color count reported by the display driver. All five
project drivers use four logical DDB planes at one bit per plane, including
2- and 4-color outputs. Do not multiply logical planes to infer physical colors.

GetFreeSpace(0) supplies free Windows global-heap bytes. Displayed KiB are
truncated to whole units of 1,024 bytes. This is neither installed RAM nor DOS
free conventional memory, and it is not the largest contiguous allocation.
The value varies with the active driver, Windows, loaded applications and
allocations; Refresh updates it. No Windows 3.1 resource-percentage API is used.

## Build

Use the full repository's existing Microsoft C and Win16 toolchain. No compiler
or Microsoft Windows media is included in this standalone example package.
From the repository root on a host with Python 3 and DOSBox-X:

    python3 examples/TABOUT/BUILD.PY --dosbox <path-to-dosbox-x> --out <new-dir>

The output directory must not exist. The builder copies only this example's
inputs, mounts the existing toolchain read/write as C and the output as D,
runs BUILD.BAT, and records BUILD.LOG and RESULT.JSON. It does not modify or
rebuild the display driver. Compiler flags are /G0 /Gw /AS /W3 /Od, explicitly
8086 code generation, Windows prologues and small model. LINK4 creates the
segmented Windows executable using SLIBCEW.LIB and LIBW.LIB.

For a DOS build with the same toolchain mounted at C, copy TABOUT.C, TABOUT.DEF,
TABOUT.RSP and BUILD.BAT to the build directory and run BUILD.BAT.

## Contents and limits

TABOUT.C is the complete app. BUILD.BAT / BUILD.PY / TABOUT.DEF / TABOUT.RSP
rebuild it. TABOUT.EXE is ready to copy. TESTS.MD and EVIDENCE contain emulator
acceptance, source hashes, native harness source, logs and raw screenshots.

Physical Tandy hardware remains untested. Emulator cycles were accelerated;
this makes no performance or clock-rate claim. Screens smaller than160x200,
other fonts or a window manually shrunk below the compact layout can clip.
Maximize it again. Values on other drivers depend on those drivers' accuracy.
Later CPU families are reported only as far as these Windows 3.0 flags allow.

Raw DOSBox-X screenshots reflect non-square pixels: logical160x200 captures
are320x200 (doubled columns), logical640x200 captures are640x400 (doubled rows),
and logical320x200 captures are320x200. Images are unretouched.
