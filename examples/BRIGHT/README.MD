THE BRIGHTER TOMORROW INITIATIVE
First playable slice - 2026-10-03
TOGETHER, WE MAKE TOMORROW BRIGHTER.

WHAT IS HERE
Five workplace notices, from failed coffee to an unauthorized shadow.
Three visible metrics, two or three choices, a receipt after every choice,
two endings, Restart and Exit. This is the requested compact first milestone;
it is deliberately shorter than the eventual 5-10 minute game.
The Initiative has always been benevolent.

RUN
Copy this BRIGHT folder wherever convenient. BRIGHT.EXE is standalone;
source and tests are not needed at runtime. From Program Manager,
File / Run: C:\BRIGHT\BRIGHT.EXE (adjust the drive/path if needed).
Or, from a correctly prepared DOS/Windows installation:
  C:\WINDOWS\WIN /R C:\BRIGHT\BRIGHT.EXE
Keep using the display driver's existing RESERVE-before-Windows procedure.
This application neither installs nor changes a driver or system file.

Click a choice, or press 1, 2 or 3. Tab and Shift+Tab select native buttons;
Space or Enter activates the focused button. Read the receipt, then Continue.
Alt+F4 or the system menu closes at any time. An ending offers Restart / Exit.
Holding a numeric key does not automatically play through several notices.

METRICS
Start: PRODUCTIVITY 60%, MORALE 60%, BRIGHTNESS 60%.
Values are clamped to 0..100. After a receipt, any value at 15 or below ends
participation. At the end of five notices, all three must be at least 50 for
success. Receipts pause progression so the changed metrics can be read.
Restart restores the initial values and first notice.

QUICK TEST ROUTES (SPOILERS)
Success: choices 1, 2, 1, 1, 2, with Continue after each: 58 / 72 / 93.
Early failure: choices 2, 3, 2: 96 / 10 / 92 after notice 3.
No fourth decision occurs in that route.

BUILD: EXISTING MICROSOFT C 6 / WINDOWS 3.0 TOOLS
No Microsoft compiler, library, headers, Windows media or display driver is
included. Use the existing period toolchain. There is no resource compiler
step and no external runtime DLL. The regular Win16 C startup/runtime links
statically from SLIBCEW.LIB; Windows imports come from LIBW.LIB.

Expected tool layout on C: in the build emulator:
  C:\BIN\CL.EXE (and its compiler passes)
  C:\BIN\LINK4.EXE (Microsoft segmented linker 5.01.17)
  C:\DDK\286\INC\WINDOWS.H
  C:\INCLUDE
  C:\LIB\SLIBCEW.LIB
  C:\LIB\LIBW.LIB
Mount a writable copy of this BRIGHT directory as D:, then run:
  D:
  SET PATH=C:\BIN
  SET INCLUDE=C:\DDK\286\INC;C:\INCLUDE
  SET LIB=C:\LIB
  CL /nologo /c /G0 /Gw /AS /W3 /Od BRIGHT.C ENGINE.C
  LINK4 /NOE /NOD @BRIGHT.RSP
The output is BRIGHT.EXE. /G0 requests 8086/8088 instructions; /Gw and /AS
select Windows code conventions and the small memory model.
BUILD.BAT runs those commands with a log and PASS/FAIL marker, then EXITs
its DOSBox session. All distributed source/build text uses CRLF and 8.3 names.

Optional host wrapper (Python 3 plus the existing DOSBox-X launcher):
  python3 BUILD.PY --dosbox /path/to/dosbox-x --repo /path/to/toolchain \
    --out /path/to/new-build-directory
--repo must contain BIN, LIB, INCLUDE and DDK/286/INC as above.
--out must be new. This copies source into the build directory, mounts the
existing toolchain, waits for the build result, and records its size/hash.
The packaged source was rebuilt this way and produced byte-identical output.

SIZE / MEMORY / CPU
BRIGHT.EXE: 8,271 bytes.
SHA256: f00c8b3efc31fc6d3073543cccea71cc3c48b1a662bff1193d632a07314fbdef
NE code segment: 5,012 bytes. Declared initialized/static data allocation:
2,176 bytes, plus a 4,096-byte stack and 1,024-byte local heap.
That is about 12 KiB of nominal code/data/stack/heap before loader, USER/GDI,
control and Windows overhead; it is NOT a measured total working-set figure.
The six-word game state is 12 bytes with the target's 16-bit int.

No floating point, explicit dynamic allocation, timers, animation, sound,
file saves, external assets, large bitmaps or nonstandard runtime is used.
The sun is ordinary monochrome GDI line art. Painting happens on normal
Windows invalidation and choices, not continuously. Buttons and fonts are
native Windows objects. The event table is compiled into the EXE.

TESTED ENVIRONMENT / DISPLAY
Minimum tested resolution: actual 160x200, 16 colors, in Windows 3.0 real
mode under DOSBox-X. Also tested 640x200, 2 colors, with accepted TRIAL2
bytes. Both use 640 KiB conventional guest RAM, XMS/EMS/UMB disabled, and
the driver's successful 16 KiB video-overlap reservation before Windows.
This is evidence for the expanded 640 KiB configuration; it does not claim
the unexpanded 256 KiB Tandy 1000 EX can run this Windows installation.
CPU emulation was 8086_prefetch, accelerated at fixed 200000 cycles, no FPU.
It establishes functional behavior, not physical 8088 performance or timing.
Physical Tandy performance remains unqualified.

The small-mode fixture used actual DOS Setup and the complete original
mode-specific support/font tuple, not only an INI edit. Its frozen driver
is an emulator test fixture, not a physically accepted small-mode release.
See TESTS.MD for exact driver hashes and evidence scope.

LOW-RESOLUTION TRADEOFFS
At 160 columns the title bar is shortened to BRIGHTER, while the full
three-line branding stays inside the client. Every prompt/receipt fits at
most 18 fixed-font columns and four lines. Full metric names and percentages
remain visible. Bar gauges appear only when there is spare horizontal space.
Native buttons are stacked vertically. The app has no menu bar, scrollbar,
resize border or modal message box consuming scarce client space.

The emulator presents non-square Tandy pixels with scaling; screenshots
are captured host surfaces, not a claim that the logical mode is 320 pixels
wide. Fonts and window metrics depend on correct driver Setup. Other display
modes/font tuples have not been certified. Native 160-column system menus
and Windows UI outside this app can still be cramped.
No app-blocking display corruption or hang was observed in the scoped tests.

VERIFICATION
See TESTS/README.MD for the independent deterministic C89 oracle and copy
audits, and TESTS.MD for recorded target GUI checks and limits.
AUDIT.PY plus BRIGHT.MAP performs a scoped objdump-based 8088 instruction
check. It inspected 1,850 reachable instructions with no post-8088 suspects.
It excludes imported Windows code, unresolved indirect CRT continuations and
unreachable bytes; it is not an exhaustive ISA or physical-hardware proof.

EXTENDING LATER
ENGINE.C owns the five-event table and consequences; ENGINE.H owns its
bounds/state; BRIGHT.C owns the Windows UI. Add events only after this slice
is reviewed, keeping the compact copy bounds and updating the independent
oracle's expected table. No further campaign, hidden metrics, sound or driver
changes are part of this milestone.

BRIGHTER TOMORROW THANKS YOU FOR YOUR PARTICIPATION.
