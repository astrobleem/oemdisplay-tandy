# Tandinator animation, sound and usability trial

Optional standalone TANDI07 / 0.3.4. This does not replace canonical
`examples/TANDINAT`, the accepted OEM disk, drivers or earlier experiments.

## Changes

- Ten exact expression crops from the supplied sprite sheet: idle blink,
  thinking, talking reveal and happy/winking victory; native pixels preserved.
- Short optional PSG reveal, wrong-guess and victory cues. F3 toggles sound;
  known competing sound users take priority. No PIT/IRQ changes.
- Held-key and double-click guards; Escape closes help/diagnostics first.
- F2 clearly identifies diagnostics and warns before exposing candidate names.
- After rejecting a guess at question 25, choose Continue guessing, Restart
  or Exit. Every remaining candidate stays reachable; no guess cap.
- Bad-DAT screen gives repair instructions and Exit, rather than dead replay.
- Installer copies EXE, DAT, roster and README and refuses existing files.

The 256-character / 130-question DAT, inference engine and loader are exactly
TANDI05's reviewed versions. The art/sound implementation matches the frozen
TANDI06 trial. This pass does not claim improved factual accuracy, add learning,
undo, a roster browser or session statistics. Escape outside overlays still
exits. Normal engine calculation remains synchronous between animation frames.

## Verification

Run `python3 TESTPUB.PY` for exact archive, source/evidence, screenshot and
platform-exclusion pins. `TANDI07.ZIP` contains the runtime, complete source,
original sprite sheets, recipes, tests and captured evidence. Extract it and
run from `TANDI07/SOURCE`:

    python3 tests/QTEST06.PY
    python3 tests/CURTEST.PY
    python3 tests/ARTTEST.PY --require-runtime --runtime-tag=-use07b
    python3 tests/UITEST.PY --runtime-tag=-use07b
    python3 tests/ANIMTEST.PY
    python3 tests/UIGUARD.PY
    python3 tests/HOSTTEST.PY

Python/Pillow/NumPy and GCC are modern-host test dependencies, never Tandy
runtime requirements. Captured evidence is not a fresh emulator run.

For the original C6 build, mount the owned toolchain root as C: and SOURCE/src
as D:, then run BUILD.BAT. It uses /G0 /Gw /AS, the supplied response file and
four C modules. WndProc remains exported. Inspect BUILD.LOG/BUILD.OK/TANDI.MAP;
run tools/AUDIT.PY on the resulting executable. Native EMUTEST.PY is a private
fixture example requiring owned Windows/compiler/emulator files and matching
TRIAL7 drivers. Adapt its fixture paths; retain its shared lock and bounded
60-second acquisition plus per-process timeout. No proprietary platform files
are distributed. SOURCE.DIF shows relevant changes from published TANDI05;
the ZIP is self-contained and does not require an unpublished intermediate.

Fresh final tests passed in Windows 3.0 real mode at 320x200x16, 640x200x2 and
640x200x4, plus an actual corrupted-DAT launch. 36 host UI checks, 59 sound
scenarios and exact original-pixel animation checks passed. All three native
runs verified four-file installation and refusal to overwrite an installed
sentinel. Details, precise hashes and limits are in QA07.TXT and EVIDENCE.

These use 640 KB, 8086_prefetch, no XMS/EMS/UMB/FPU and uncalibrated 25,000 cycles.
No physical Tandy or human accuracy study was performed. Known-writer sound
arbitration cannot detect arbitrary programs writing directly to the PSG.
