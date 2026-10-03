STARTQA - focused CDSTART native test harness
===========================================
These five first-party source/build files are the exact source used for the
accepted CDSTART helper tests. Historical filenames TSHELL.C/EXE are retained;
this is a disposable test harness, not the optional Start-bar application.
Build with BUILD.PY --repo <owned-toolchain-repo> --dosbox <dosbox-x> --out <new-output>.
The existing L4046 module/output-name warning is retained. A fresh publication
rebuild exactly matched the tested 7,331-byte executable (SHA256 below).

Use only an owned disposable guest. Copy the resulting TSHELL.EXE as
C:\STARTQA.EXE. Prepare the C: or D: layout and missing-file fixtures described
in ../TESTS.TXT, then start C:\STARTQA.EXE C (or D) inside the guarded Windows
real-mode guest. The harness writes C:\STARTQA.LOG, drives the demo's Save,
Read and Cancel operations, creates a scratch round-trip file and calls
ExitWindows when finished. It is not a normal application or card shortcut.
Do not run it with unsaved work or against a real installation.

The preserved STARTC/STARTD/CHILDC/CHILDD logs in the parent folder are the
native test evidence. Publication performed an exact rebuild, not a new
native test run. Native script scaffolding tied to temporary host paths is
omitted; reproduce with the documented owned-guest procedure.

Harness SHA256: 5a7b3377c0119e25362c277d3845f90812c2f715ff15012f0fe57949a75b3e93
