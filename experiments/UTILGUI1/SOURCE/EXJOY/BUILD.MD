BUILDING EXJOY
The binary was built using existing Microsoft C 6.00A, MASM 5.10, and
Segmented Executable Linker 5.01.17 tools. Tools, Windows, and SDK libraries
are not included. Use your licensed period toolchain.

DOS build layout:
C:\BIN      CL.EXE, compiler passes, MASM.EXE, LINK4.EXE
C:\INCLUDE  C runtime headers
C:\DDK\286\INC  Windows headers
C:\LIB      SLIBCEW.LIB, LIBW.LIB
D:\         all files from SOURCE

Run D:\BUILD.BAT inside a disposable DOS environment. It selects /G0 /Gw
/AS /W3 /Od, assembles 8086 instructions, and creates EXJOY.EXE and EXJOY.MAP.
The output log must end in PASS. Do not replace your working Windows files.

Optional Linux orchestration (DOSBox-X must already be installed):
python3 BUILD.PY --dosbox /path/to/dosbox-x --repo /period/toolchain --out /new/build-directory
The output directory must not already exist. The repository is only used
as the toolchain source; outputs go to the separate D: directory.

Independent modern-host logic tests:
cc -std=c89 -pedantic -Wall -Wextra -Werror -fsanitize=address,undefined -g -x c HOSTTEST.C -x c JOYCORE.C -o hosttest
ASAN_OPTIONS=detect_leaks=0 ./hosttest
LeakSanitizer was unavailable under the sandbox's tracing; ASan/UBSan were
used with leak detection disabled. No dynamic allocation is used by core.

python3 CAPTEST.PY /new/build-directory/EXJOY.EXE
python3 AUDIT.PY /new/build-directory/EXJOY.EXE
CAPTEST executes the exact capture bytes in a small explicit instruction
model with simulated I/O. It is not a general emulator or hardware test.
AUDIT follows direct control flow from entry/public code symbols, excluding
the Microsoft runtime's __wflags data word. It lists indirect boundaries;
imported Windows routines are outside the audit.

Native UI test harness, using YOUR OWN expendable Windows guest copy:
python3 TESTWIN.PY --guest /existing/fixture --out /new/test-directory --build /new/build-directory --dosbox /path/to/dosbox-x --capture
The harness clones its fixture, never edits the original, starts win /r,
uses /test, and verifies EXJOY.LOG plus the return-to-DOS marker. It expects
the existing fixture's C:\TANDY88\RESERVE helper and configured display.
For a bounded I/O no-device-path check add --arg /porttest. Joystick
emulation is disabled in the supplied harness. No forced interrupts or
emulated joystick motion are injected. Never aim the harness at a mounted
physical CF card or use its QA switches in a valuable Windows session.

REUSABLE READER
JOYCAP.ASM: near C-callable fixed port capture into a 512-byte buffer.
JOYCORE.C/H: decode, range tracking, manual center, optional normalization.
The raw buffer must be a valid near pointer in the caller's DS (small-model
application). Never call the reader from a timer interrupt or IRQ handler.
Use a normal application message/timer callback at low cadence. Do not
reinterpret a timeout or a valid pulse as reliable physical presence.
