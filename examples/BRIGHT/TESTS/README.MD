BRIGHT independent gameplay verification
========================================
Run from the vertical-slice root. No external libraries are required.

Build the C89 oracle against the same ENGINE.C used by the Windows build:
  cc -std=c89 -pedantic-errors -Wall -Wextra -Wconversion -x c \
     TESTS/ORACLE.C ENGINE.C -o TESTS/oracle

Gameplay (exit 0 on pass):
  ./TESTS/oracle

Engine prompt, receipt and label bounds (exit 1 if copy violates the bounds):
  ./TESTS/oracle --copy

Windows UI multiline body bounds (Python 3 standard library only):
  python3 TESTS/COPYUI.PY

Optional host memory/undefined-behavior instrumentation:
  cc -std=c89 -pedantic-errors -g -fsanitize=address,undefined \
     -fno-omit-frame-pointer -x c TESTS/ORACLE.C ENGINE.C \
     -o TESTS/oracle_sanitized
  ASAN_OPTIONS=detect_leaks=0 ./TESTS/oracle_sanitized

Leak detection is disabled because this executor runs under ptrace, which
LeakSanitizer does not support. AddressSanitizer and UndefinedBehaviorSanitizer
remain enabled. The engine does not allocate memory.

Coverage:
- Five-event table, choice counts, expected deltas, nonempty active labels/copy.
- All 108 nominal paths, with correct truncation at an early failure. Nominal
  suffixes after a failure count toward 108 but are never applied to the game.
- Every choice at all 512 combinations of metric boundary values
  0, 1, 15, 16, 49, 50, 99, 100 (6,656 cases).
- Continue from every event at those same metric combinations (2,560 cases).
- Independent oracle implements both clamp bounds, low-metric failure at <=15,
  final success iff every metric >=50, and receipt/next-event transitions.
- Receipt cannot apply a second choice; Continue cannot skip a playing event;
  terminal phases reject further actions; reset clears all fields.
- Negative/out-of-range choices, invalid choice-event indices, invalid phase.
- Requested success route 1,2,1,1,2 ends at 58/72/93.
- Requested failing route 2,3,2,3 stops after its third event at 96/10/92.
  Choice 4 is blocked because the game is already in FAILURE.

The gameplay oracle deliberately uses its own delta table and transition rules,
not events[] as its expected result. Engine copy is separately audited from the
actual compiled table. The UI audit examines standalone multiline C string
literals in BRIGHT.C; it does not emulate Windows font metrics or layout.

Scope/limits:
This is host-side C89 behavioral verification. It does not establish the Windows
3.0 executable's ABI, 8088 instruction compatibility, runtime GUI rendering,
actual device speed, or integration input behavior. Those require target build
and runtime validation. The public API is tested for legal metric values 0..100;
NULL GAME pointers or arbitrarily corrupted metric integers are not a contract.
