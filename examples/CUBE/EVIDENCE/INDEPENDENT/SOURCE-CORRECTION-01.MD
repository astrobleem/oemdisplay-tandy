# Independent Cube correction review

Baseline: `0346d47af8025e9b854bfcf9af9e3061cb679e86`. Reviewed state: uncommitted, pinned by the changed-file hashes in `CORRECTION-01.json`.

The production correction resolves **CUBE-SRC-1**. `WM_DESTROY` leaves the already-visible settings dialog alone; `stop()` retains the guarded explicit restoration. Standalone/shutdown quit and developer QA completion remain intact. No residual production-source finding was found in this two-file diff.

The controller now checks normal preview return and retained external activation/focus after a second preview. Its sensitivity still needs a negative-control run: `CUBECTL.C:36` calls `SetFocus(w)` immediately after `SetActiveWindow(w)`, which could mask a synchronous activation steal during the first call. The [Win3.0 SDK reference](https://www.pcjs.org/documents/books/mspl13/win/w3sdkr1/) specifies that SetFocus also activates its target. Require the new test to fail against the frozen pre-fix EXE; revise the observer if it passes. This is a test gap, not an additional demonstrated production defect.

Both changed files retain CRLF and existing Win3.0/C89 callback conventions. No native build or emulator was run, and old native receipts do not qualify the corrected runtime. No source was edited by the reviewer.

- `CUBE.C`: `8974196ce2f099ca9cae39bd043f9c90077562d13aa686e1d8afe9d2cb571a69`
- `CUBECTL.C`: `11a9b7f90c9b1fc170a8d22881a42c3a936a4e3568fb64c6cdaedf8827bf5514`
