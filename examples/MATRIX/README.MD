# Matrix for Windows 3.0 / Tandy 8088

The current executable supports both the original on-demand animation and
/S, the companion mode for Tandy Start 06's optional idle saver. Run without
arguments for on-demand use. TSHELL owns automatic idle timing and the global
input hook; Matrix has no resident hook or password lock.

See README.TXT for display behavior, controller contract, wake-input draining,
build commands and detailed limits. TESTS.MD summarizes the exact current
candidate's measured evidence. The current MATRIX.EXE is 14,157 bytes, SHA-256
0987936c3b80eb9fc5718f3022996514f6885adbdf83cd05128d01bc19de17c8.

MILESTONE.ZIP and the earlier MANIFEST.JSN/EVIDENCE files are preserved history,
not the current /S release or proof of its behavior. See HISTORY.TXT.
New /S and automatic-idle behavior still require physical Tandy testing.

From the repository root:

    python3 examples/MATRIX/SOURCE/RUNHOST.PY
    python3 examples/MATRIX/SOURCE/BUILD.PY --repo <owned-toolchain> --dosbox <dosbox-x> --out <new-directory>

No OS media, SDK, compiler, ROM or binary test payload is included. TESTSRC
contains source for the optional guard app; the only new binary here is the
owned production MATRIX.EXE. See ../TSHELL/UPDATE06.TXT for integrated upgrade.
