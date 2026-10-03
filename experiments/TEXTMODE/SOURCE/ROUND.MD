# Windows 3.0 bitmap roundtrip regression probes

These authored probes use the Windows 3.0 API, a 320x200 four-plane display,
and Microsoft C with explicit `/G0 /Gw /AS`. They do not call driver internals.
No original PROBE sources or frozen driver binaries are changed.

## Build

Mount the repository/toolchain as C: and the probe source directory as D:.
Run ROUND.BAT, ROUND2.BAT, or ROUND3.BAT from D:. The corresponding RSP files
link the small-model Windows C runtime and LIBW. Check BUILD.LOG, BUILD2.LOG,
and BUILD3.LOG for compiler/linker errors.

## Run

Copy the EXEs into an isolated Windows 3.0 guest. Keep the tested driver in
that guest's WINDOWS/SYSTEM directory. Use the normal 640 KB Tandy profile,
8086_prefetch, XMS/EMS/UMB disabled, and the RESERVE success gate before WIN /R.
Run WIN /R ROUND.EXE, ROUND2.EXE, or ROUND3.EXE. Logs and binary evidence go to
C:\. ROUND shows a completion dialog; ROUND2 and ROUND3 return after logging.
Do not overwrite an active emulator's driver or reuse a live guest directory.

A headless SDL=dummy launch is suitable for API and raw-framebuffer probes.
It does not establish interactive Paintbrush save/reopen behavior. Keep each
host log bounded to 1 MiB; do not apply process-wide file-size limits to SDL.

## Coverage

- ROUND: aligned 64x16 sixteen-color bars, GetObject stride/plane/depth metrics,
  raw GetBitmapBits, GetDIBits palette/data, a saved BMP, SetDIBitsToDevice,
  SetDIBits, CreateDIBitmap, and a 32 KiB raw B800 framebuffer dump
- ROUND2: asymmetric 37x11 pixels, odd width/word-aligned planar stride and
  DWORD-aligned DIB stride, complete RGB preservation, partial GetDIBits with
  first scan 3/count 5 and untouched output guard, and compression values 1, 2,
  0x100, 0x10000 rejected without changing the destination bitmap
- ROUND3: BI_RGB depths 1/4/8/24, with 407 pixels verified per depth through
  GetDIBits, SetDIBits, CreateDIBitmap, and direct DIB-to-screen conversion

ROUNDCHK.PY GUEST --out RESULT validates ROUND2 and renders its raw framebuffer.
ROUND3CK.PY GUEST --out RESULT validates all ROUND3 output formats and guards.
Python 3 and Pillow are required by ROUNDCHK.PY. Both checkers exit nonzero
when a required path fails; output JSON keeps each path's result distinct.
The expected mode 09 framebuffer is decoded as:
  offset=(y%4)*8192+(y//4)*160+x//2, even X in the high nibble.

## Baseline and first save-fix result

Frozen 04 SHA256:
191cc57cc538e15d3637a4dc21c4cddb078ff3452836476ae4776352a5ff5fdd
It produces correct 16-color source DDBs, but DIB output has a black/white
palette and all memory/direct DIB routes lose color. A stock CGA control is
naturally monochrome. Both stock and 04 return 0 for a null-data GetDIBits query.

First save-fix SHA256:
77c6dc58c06699ba825b03f9924fb5bcfd1c728020222ae026f197cb7cc79b64
All 1/4/8/24-bit memory DIB roundtrips pass. Odd width and partial Get preserve
RGB and guards, and all four invalid compression values return 0/no writes.
SetDIBitsToDevice still collapses 4/8/24-bit input to monochrome, so the full
regression remains failed until that separate screen path is fixed.

## Final screen-path and allocation checks

The final ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee
build also passes the formerly failing direct-screen paths. ROUND4 covers
56 cases: all four depths, negative and clipped destination coordinates,
source-X/source-Y cropping, partial bands, explicit DC clipping, and four
unsupported compression DWORDs at every depth. Every test compares all
32 KiB before/after framebuffer bytes and all 4096 source-buffer bytes.
See ORACLE.MD for the documented bottom-left DIB source-coordinate convention
and independent native stock-CGA control.

ROUND5 warms up eight calls, then repeats 64 direct-screen blits. All return
11 scans. Largest free block remains 318208 bytes and total free heap remains
328768 bytes at every 16-call checkpoint; before/after framebuffers match.
ROUNDGO.PY provides bounded headless execution and captures at most 1 MiB of
host diagnostics while draining excess output. It stops the disposable test
process only after a flushed COMPLETE marker, or reports a timeout.
