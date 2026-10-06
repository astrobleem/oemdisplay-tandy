# Supplementary ordinary-display capture check

6 October 2026. All seven APPUI01 production executable hashes are unchanged.
The original ZIP, original immediate dumps, runtime pins and 41-run/2,663-check
qualification record are retained unchanged.

## Capture caveat

The original PNGs are diagnostic B800 memory samples, often collected directly
after a synchronous cross-task `UpdateWindow`. They are not standalone proof
that the ordinary visible display has completed every queued repaint. Related
utility-observer testing found incomplete immediate samples while recorded
ordinary display content was complete. Its precise low-level cause was not
established; it is not being labelled a general driver or APPUI01 defect.

This additional APPUI01 run records the ordinary **320x200x4** display and
retains immediate samples alongside it. The video was reviewed across all
seven apps: captions, readings, instructions, path controls and the successful
Paintbrush handoff are visible. All 41 normal-use observer checks passed.
The included About memory-page sample and later video frame both show complete
content and their RGB pixels match. This is one bounded checkpoint against a
later frame, not synchronized observation or an exhaustive visual proof.
No missing-field APPUI01 regression was established.

## Exact evidence

- [APP3204.AVI](APP3204.AVI) is the untouched DOSBox-X recording, 320x200,
  approximately 14.819 seconds. It uses the emulator's lossless recording codec.
- [RESULT.JSN](RESULT.JSN) records the video, observer and seven runtime hashes,
  configuration, selected frame indexes/timestamps and comparison limits.
- Individual app PNGs are exact decoded video frames, with no repainting or
  overlays. [CONTACT.PNG](CONTACT.PNG) labels them outside the captured pixels.
- ABOUTRAW.RAW and ABOUTRAW.PNG preserve one immediate memory sample and its
  decoded form. The earlier sealed archive still contains the original dumps'
  derived images and their qualification.
- RESULT.LOG retains the observer checks. Its source/build inputs are here;
  only final Windows shutdown was added to finalize the recording cleanly.
  No application source or runtime was rebuilt for this follow-up.

The owned prepared guest used Windows 3.0 real mode, 640 KB, 8086_prefetch,
FPU off, no EMS/XMS/UMB, and uncalibrated 25,000 cycles. Capture was started with
DOSBox-X `DX-CAPTURE /V`, then stopped after normal Windows exit. Supply your own
licensed tools/guest to reproduce; neither is included. This is functional
emulator/display evidence, not physical Tandy speed, calibrated timing or
manual physical-input qualification. Other profiles retain their stated scope.

Run `python3 TESTVID.PY` to verify evidence and unchanged runtime pins.
With FFmpeg and Pillow installed, `python3 TESTVID.PY --decode` also extracts
and compares all seven selected frames against the untouched recording.
