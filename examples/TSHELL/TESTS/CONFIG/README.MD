# Screensaver configuration core tests

Run python3 examples/TSHELL/TESTS/CONFIG/RUN.PY from the repository root.
Requires Python 3 and GCC. Compiles the production SCFGCORE.C as strict C89
with warnings as errors, ASan and UBSan. Leak inspection is disabled.

143 assertions cover parsing, defaults, allowed choices/options, custom paths,
None, conflicts, write/read failures, rollback and command-length limits.
The test uses fake configuration I/O; it does not mutate the installed INI.
Native Win3.0 profile handling and dialog behavior are qualified separately
in ../../TESTS.MD.
