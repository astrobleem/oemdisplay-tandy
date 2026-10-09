# Windows 3.0 idle input observer

TSINPUT.DLL supplies the global input observation used by the primary TSHELL.
It is a fixed-code/single-data Win16 DLL, built for 8086 with no CRT or local
heap. TSHELL loads it from its own Windows directory and owns installation,
periodic readiness queries and removal. A secondary TSHELL bar never installs
it. Exports are IdleInstall, IdleRemove, IdleGeneration, IdleReady, IdleRecord
and resident WEP. The final DLL is one level above this source directory.

IdleRecord uses the documented WH_JOURNALRECORD hook and chains prior hooks.
It records only activity generations, held input and raw mouse position;
no typed content is saved. No file I/O, yielding, UI or DOS time calls happen
inside the hook. The owner task calls the documented DOS INT 21h/AH=2Ch clock
service and compares elapsed time to GetTickCount, detecting Windows tick
suspension in a DOS task. Polling gaps, modal transitions, midnight and clock
changes conservatively reset readiness and require fresh input release.

Ordinary polls do not consume GetAsyncKeyState low bits. Initial installation
and exceptional resynchronization take physical baselines outside the hook;
these baseline calls do clear the API's shared pressed-since-last-call bits.
Input observed after installation is required before first launch. The shell
supplies idle timing, startup/audio/menu/dialog guards and launch cancellation.

Build from the repository root with an owned toolchain and DOSBox-X:

    python3 examples/TSHELL/IDLE/BUILD.PY --toolchain <toolchain-root> --dosbox <dosbox-x> --out <new-directory>

BUILD.BAT expects C:\BIN, C:\DDK\286\INC, C:\INCLUDE and C:\LIB. It builds
TSINPUT.DLL and IDLEPROB.EXE. IDLEPROB is an optional observation test app, not
a required runtime companion; its binary is not distributed here.

tests/HOSTTEST.C includes ../TSINPUT.C, which selects tests/WINSTUB.H only for
host tests. The source is checked through ../TESTS/RUNHOST.PY; tests/VERIFY.PY
checks the actual DLL NE layout. See ../TESTS.MD for final native results and
physical-hardware limitations. No Windows, SDK or compiler files are included.

The lowercase tests suite also checks the current Hold exports and supplies
HOLDTEST.C. The earlier uppercase idle-only suite is preserved unchanged at
[the pre-cleanup DEV snapshot](https://github.com/astrobleem/oemdisplay-tandy/tree/96ce6971a1757f3c77094322ed82741791c79646/examples/TSHELL/IDLE/TESTS).
